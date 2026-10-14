"""Sequential, reversible hardware measurements; never sends SMS.

No formal headless or human-motion claims are made by this unattended runner.
"""
import argparse
import json
import subprocess
import signal
import sys
import time
from pathlib import Path
import campaign as c

def run(script,args,label):
    out=c.BASE/'execution_logs';out.mkdir(exist_ok=True)
    log=out/(label.replace('/','_')+'_'+str(time.time_ns())+'.log')
    cmd=[sys.executable,str(c.BASE/'scripts'/script),*args]
    print('START',label,'log',log,flush=True)
    with log.open('w') as f:
        proc=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT)
        try:rc=proc.wait()
        except BaseException:
            proc.terminate()
            try:proc.wait(timeout=30)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            raise
    if rc:raise RuntimeError(f'{label} exited {rc}; see {log}')
    s=json.loads((c.BASE/label/'summary.json').read_text())
    if s.get('exception'):raise RuntimeError(f'{label} failed: '+s['exception'])
    if s.get('stationary_physical_plausibility_gate') is False:
        raise RuntimeError(f'{label} failed the physical plausibility gate; result retained, next trial not started')
    print('DOCUMENTED',label,flush=True)
    return s

def baseline_gate(a,b):
    values=[]
    for axis in ['ax','ay','az','gx','gy','gz']:
        p=a['physical'][axis];f=b['physical'][axis]
        values.append({'axis':axis,'mean_difference_fifo_minus_polling':f['mean']-p['mean'],
                       'std_ratio_fifo_over_polling':f['std']/p['std'] if p['std'] else None,
                       'rms_difference':f['rms']-p['rms'],'polling_min':p['min'],'polling_max':p['max'],
                       'fifo_min':f['min'],'fifo_max':f['max']})
    ok=all(abs(v['mean_difference_fifo_minus_polling']) < (.3 if v['axis'][0]=='a' else 2.) for v in values)
    ok=ok and a['stationary_physical_plausibility_gate'] and b['stationary_physical_plausibility_gate']
    return values,bool(ok)

def equivalence():
    out=c.BASE/'04_polling_fifo_equivalence';out.mkdir(exist_ok=False)
    prereg={'mean_axis_tolerances':{'acceleration_ms2':.3,'gyro_deg_s':2},
            'other_gate':'Both physical sanity checks pass, no rail hits, no I2C error, no FIFO overflow.',
            'purpose':'Conservative engineering plausibility/equivalence gate, NOT a formal statistical equivalence test.',
            'configuration':'Both modes use CONFIG=4, ACCEL_CONFIG2=4, SMPLRT_DIV=19, +/-2g and +/-250 dps. Different from original unfiltered deployment.',
            'conditions':'Unattended in existing physical placement; physical assembly/mounting not independently confirmed.'}
    c.save(out/'predeclared_gate.json',prereg)
    a=run('hardware.py',['capture','--mode','polling','--filtered','--seconds','600','--label','04_polling_fifo_equivalence/polling'],'04_polling_fifo_equivalence/polling')
    b=run('hardware.py',['capture','--mode','fifo','--filtered','--seconds','600','--label','04_polling_fifo_equivalence/fifo'],'04_polling_fifo_equivalence/fifo')
    vals,passed=baseline_gate(a,b)
    result={'axis_comparison':vals,'gate_passed':passed,'predeclared_gate':prereg,
            'polling_rate_hz':a['achieved_samples_per_s'],'fifo_rate_hz':b['achieved_samples_per_s'],
            'polling_magnitudes':{'accel':a['accel_magnitude'],'gyro':a['gyro_magnitude']},
            'fifo_magnitudes':{'accel':b['accel_magnitude'],'gyro':b['gyro_magnitude']}}
    c.finish(['B3'],'Matched filtered polling/FIFO raw comparison','COMPLETE (UNATTENDED)' if passed else 'FAIL — DO NOT RUN B4',result,out)

def aba():
    gate=json.loads((c.BASE/'04_polling_fifo_equivalence/summary.json').read_text())
    if not gate['gate_passed']:raise RuntimeError('B3 must pass before B4')
    out=c.BASE/'05_corrected_aba';out.mkdir(exist_ok=False)
    c.save(out/'predeclared_conditions.json',{'order':['A1_polling','B_fifo','A2_polling'],'duration_s_each':1200,
        'fixed_config':'Filtered 50-Hz low-range configuration for ALL arms; does not reproduce original unfiltered polling.',
        'timing':'Host observed read-completion times, no artificial reconstruction of sensor timestamps. Batch duplicate timestamps retained.',
        'policy':'Frozen model/thresholds/60ms guard/3 consecutive positives/60s cooldown. Record events; no GPIO/countdown block/SMS.'})
    results={};governors={str(p):p.read_text().strip() for p in Path('/sys/devices/system/cpu/cpufreq').glob('policy*/scaling_governor')}
    c.save(out/'governors_before.json',governors)
    try:
        for path in governors:
            r=subprocess.run(['sudo','-n','tee',path],input='performance\n',text=True,capture_output=True)
            if r.returncode:raise RuntimeError('Cannot fix CPU governor: '+r.stderr)
            if Path(path).read_text().strip()!='performance':raise RuntimeError('Governor readback mismatch')
        for name,mode in [('A1_polling','polling'),('B_fifo','fifo'),('A2_polling','polling')]:
            label='05_corrected_aba/'+name
            results[name]=run('live.py',['--mode',mode,'--filtered','--seconds','1200','--label',label],label)
    finally:
        restored={}
        for path,value in governors.items():
            rr=subprocess.run(['sudo','-n','tee',path],input=value+'\n',text=True,capture_output=True)
            restored[path]={'returncode':rr.returncode,'readback':Path(path).read_text().strip(),'original':value}
        c.save(out/'governors_restored.json',restored)
    c.finish(['B4'],'Corrected filtered A–B–A','COMPLETE (CONFIGURATION QUALIFIED)',results,out)

def high_range():
    # C1 is evidenced by actual readback in the first diagnostic capture.
    run('hardware.py',['capture','--mode','polling','--filtered','--high-range','--seconds','10','--label','06_high_range_register_check','--ids','C1'],'06_high_range_register_check')
    run('hardware.py',['capture','--mode','polling','--filtered','--high-range','--seconds','600','--label','06_high_range_stationary','--ids','C2'],'06_high_range_stationary')
    run('live.py',['--filtered','--high-range','--seconds','1200','--label','08_high_range_20min','--ids','C4'],'08_high_range_20min')

if __name__=='__main__':
    def stop(signum,frame):raise InterruptedError('User/process termination requested')
    signal.signal(signal.SIGTERM,stop)
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['equivalence','aba','high-range','thermal']);args=p.parse_args()
    service=c.command(['systemctl','is-active','helmx-crash-monitor.service'])
    if service.get('stdout','').strip()=='active':raise RuntimeError('Live crash monitor active: cannot share sensor during research captures')
    if args.phase=='equivalence':equivalence()
    elif args.phase=='aba':aba()
    elif args.phase=='high-range':high_range()
    else:run('live.py',['--seconds','10800','--label','thermal_3h','--ids','I1'],'thermal_3h')
