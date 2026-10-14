"""Armed, one-boot identity/baseline capture; never shuts down or sends SMS."""
import argparse
import fcntl
import json
import subprocess
import sys
from pathlib import Path
import campaign as c

STATE=c.BASE/'metadata/boot_capture_arm.json'

def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()

def eligible(state,current):
    return state.get('armed') is True and state['armed_boot_id']!=current

def run_script(script,args,log):
    with log.open('w') as f:
        proc=subprocess.run([sys.executable,str(c.BASE/'scripts'/script),*args],stdout=f,stderr=subprocess.STDOUT)
    if proc.returncode:
        raise RuntimeError(f'{script} failed ({proc.returncode}); see {log}')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['arm','run','status'])
    parser.add_argument('--boot',type=int,choices=[1,2,3,4])
    a=parser.parse_args()
    if a.action=='status':
        print(STATE.read_text() if STATE.exists() else 'Not armed')
        return
    if a.action=='arm':
        if a.boot is None:raise ValueError('--boot is required')
        if (c.BASE/'01_identity_three_boots'/f'boot{a.boot}').exists():
            raise RuntimeError('Boot capture already exists; do not overwrite')
        state={'armed':True,'boot':a.boot,'armed_boot_id':boot_id(),
               'baseline_seconds':600 if a.boot in [1,4] else 300,
               'power_removal_attested':False,
               'rule':'Run once on a different OS boot; physical power removal must be attested afterward.'}
        c.save(STATE,state)
        c.finish([],f'Prepare boot {a.boot} automatic identity and stationary capture',
                 'PREPARED; NOT AN EXPERIMENT RESULT',state,c.BASE/'boot_capture_preparation'/f'boot{a.boot}')
        return
    lock=(c.BASE/'metadata/boot_capture.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=json.loads(STATE.read_text()) if STATE.exists() else {}
    if not eligible(state,boot_id()):
        print('Not armed for this boot; no device accessed')
        return
    state.update(armed=False,started_boot_id=boot_id(),start_uptime_s=float(Path('/proc/uptime').read_text().split()[0]))
    c.save(STATE,state)  # Consume before touching hardware; failed trials never silently retry.
    out=c.BASE/'boot_capture_execution'/f'boot{state["boot"]}'
    out.mkdir(parents=True,exist_ok=False)
    c.save(out/'metadata.json',c.metadata())
    result={'arm':state,'error':None,'baseline':None}
    try:
        frozen=json.loads((c.BASE/'hashes/initial_artifacts.json').read_text())
        if not all(c.sha(c.ROOT/name)==digest for name,digest in frozen.items()):
            raise RuntimeError('Frozen artifacts changed')
        service=c.command(['systemctl','is-active','helmx-crash-monitor.service'])
        if service.get('stdout','').strip() not in {'inactive','unknown'}:
            raise RuntimeError('Cannot establish that crash monitor is inactive')
        openers=c.command(['fuser','/dev/i2c-1'])
        if openers.get('returncode')!=1 or openers.get('stdout','').strip():
            raise RuntimeError('I2C is already open or exclusive access cannot be checked')
        run_script('identity_boot.py',['--boot',str(state['boot']),'--await-power-attestation'],out/'identity_execution.log')
        label=f'boot_repeatability/boot{state["boot"]}_stationary'
        result['baseline_start_requested_uptime_s']=float(Path('/proc/uptime').read_text().split()[0])
        run_script('live.py',['--seconds',str(state['baseline_seconds']),'--label',label],out/'baseline_execution.log')
        summary=json.loads((c.BASE/label/'summary.json').read_text())
        result['baseline']=label
        if summary['exception'] or summary['elapsed_s']<state['baseline_seconds']:
            raise RuntimeError('Incomplete stationary capture; retained as failure')
        import csv
        with (c.BASE/label/'raw_sensor.csv').open() as f:
            result['first_sample_uptime_s']=float(next(csv.DictReader(f))['t_monotonic'])
        result['limitation']='Boot-to-first-sample delay is reported, not hidden. Stationarity and power removal need operator attestation. H1 still requires motion on each boot. I2 still requires the >=60-minute warm comparison.'
    except Exception as error:
        result['error']=repr(error)
    c.finish([],f'Boot {state["boot"]} automatic capture',
             'CAPTURED; OPERATOR ATTESTATION AND MOTION PENDING' if result['error'] is None else 'FAIL; SEE ERROR',result,out)
    if result['error']:raise SystemExit(1)

if __name__=='__main__':main()
