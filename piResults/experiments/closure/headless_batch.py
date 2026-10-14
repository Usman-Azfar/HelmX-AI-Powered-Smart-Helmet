"""Run the matched headless conditions from a separate console after IDE exit.

Use --plan to inspect commands. This script never stops desktop/remote services.
"""
import argparse
import csv
import datetime
import json
import os
import subprocess
import sys
import time
import campaign as c
from headless_gate import interactive

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--smoke-test', action='store_true',
                        help='60 seconds per condition with desktop allowed; not headless evidence')
    args = parser.parse_args()
    seconds = 60 if args.smoke_test else 1200
    scope = 'smoke' if args.smoke_test else 'headless'
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    labels = [f'{scope}_{stamp}/normal', f'{scope}_{stamp}/fifo']
    commands = [['taskset','-c','3',sys.executable,str(c.BASE/'scripts/live.py'),
                 '--seconds',str(seconds),'--label',label] +
                ([] if args.smoke_test else ['--require-headless']) for label in labels]
    commands[1] = ['chrt','-f','10'] + commands[1]
    if args.plan:
        print(json.dumps({'commands':commands, 'total_capture_minutes':seconds*2/60,
                          'scope':'Same core 3, normal versus FIFO priority 10; no alarm or SMS.'},indent=2))
        return
    if os.geteuid() != 0:
        raise RuntimeError('Run with sudo from a separate console for SCHED_FIFO privileges.')
    if not args.smoke_test and interactive():
        raise RuntimeError('Close desktop, VNC, IDE and agent first: '+repr(interactive()))
    for service in ['helmx-crash-monitor.service','helmx-research-boot-capture.service']:
        if c.command(['systemctl','is-active',service]).get('stdout','').strip() != 'inactive':
            raise RuntimeError('Competing service is not inactive: '+service)
    initial = json.loads((c.BASE/'hashes/initial_artifacts.json').read_text())
    if not all(c.sha(c.ROOT/p)==h for p,h in initial.items()):
        raise RuntimeError('Frozen artifact mismatch')
    batch = c.BASE / f'{scope}_{stamp}'
    batch.mkdir(exist_ok=False)
    c.save(batch/'plan.json', {'commands':commands,'core':3,'duration_each_s':seconds,
                             'smoke_test':args.smoke_test,
                             'operator_condition':'Keep helmet untouched on same surface and in same orientation for both runs.'})
    for index, (label, command) in enumerate(zip(labels, commands)):
        print(f'Starting condition {index+1}/2: {label}; {seconds} seconds.', flush=True)
        ownership = c.command(['fuser','/dev/i2c-1'])
        if ownership.get('returncode') != 1 or ownership.get('stdout','').strip():
            raise RuntimeError('Sensor ownership could not be confirmed free: '+repr(ownership))
        observations = []
        next_progress = time.monotonic() + 60
        with (batch/f'condition_{index}.log').open('w') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            try:
                while process.poll() is None:
                    observations.append({'monotonic':time.monotonic(),'interactive':interactive()})
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        pass
                    if process.poll() is None and time.monotonic() >= next_progress:
                        print(f'Condition {index+1}/2 still recording; log: {batch}/condition_{index}.log', flush=True)
                        next_progress = time.monotonic() + 60
            except BaseException:
                process.terminate()
                process.wait(timeout=30)
                raise
        out = c.BASE/label
        checks = {'exit_success':process.returncode==0}
        if not args.smoke_test:
            checks['no_interactive_process_observed'] = not any(x['interactive'] for x in observations)
        if (out/'summary.json').exists():
            summary=json.loads((out/'summary.json').read_text())
            meta=json.loads((out/'metadata.json').read_text())
            checks.update(full_duration=summary['elapsed_s']>=seconds,
                          no_exception=summary['exception'] is None,
                          samples_recorded=summary['n_samples']>0,
                          windows_scored=summary['n_windows']>0,
                          correct_affinity=meta['affinity']==[3],
                          correct_scheduler=meta['scheduler']==(0 if index==0 else 1),
                          correct_priority=meta['priority']==(0 if index==0 else 10))
            for filename, key in [('raw_sensor.csv','n_samples'),('window_scores.csv','n_windows')]:
                checks[key+'_rows_match'] = False
                if (out/filename).exists():
                    with (out/filename).open() as source:
                        checks[key+'_rows_match']=sum(1 for _ in csv.reader(source))-1==summary[key]
            before=json.loads((out/'registers_before.json').read_text())
            after=json.loads((out/'registers_restored.json').read_text()) if (out/'registers_restored.json').exists() else {}
            config_regs=['SMPLRT_DIV','CONFIG','GYRO_CONFIG','ACCEL_CONFIG','ACCEL_CONFIG2',
                         'FIFO_EN','USER_CTRL','INT_PIN_CFG','INT_ENABLE','PWR_MGMT_1','PWR_MGMT_2']
            checks['configuration_restored']=all(before[k]==after.get(k) for k in config_regs)
        else:
            checks['summary_exists']=False
        c.finish([], 'Headless batch condition verification',
                 ('SMOKE TEST PASSED; NOT HEADLESS EVIDENCE' if args.smoke_test else
                  'CAPTURED; OPERATOR STATIONARITY AND RAW REVIEW PENDING') if all(checks.values()) else 'FAILED',
                 {'label':label,'checks':checks,'process_observations':observations,
                  'limitation':'Process observations every ten seconds cannot exclude shorter interactive activity. Headless checklist closure also requires raw/replay/resource review and operator stationarity confirmation.'},
                 batch/f'verification_{index}')
        if not all(checks.values()):
            print((batch/f'condition_{index}.log').read_text()[-8000:], file=sys.stderr)
            raise RuntimeError('Condition failed; result recorded; next experiment not started.')
        print(f'Condition {index+1}/2 finished and documented.', flush=True)
    print('Both captures documented. Restore services you stopped and return for review.')

if __name__ == '__main__':
    main()
