"""Sequential queue: result must be committed to last_results before next task.

No concurrent experiment execution. Exceptions stop the queue for investigation.
"""
import argparse
import json
import subprocess
import sys
import time
import campaign as c

TASKS=[('model_analysis.py',x) for x in ['L1','L2','L3','L4','L5','L6','L7','L8','L9']]
TASKS += [('provenance.py',x) for x in ['M1','M2','M3','M4','Q1','Q2','N2']]
TASKS += [('stream_analysis.py',x) for x in ['E1','E2','E3','F1','F2','H2']]

def main():
    p=argparse.ArgumentParser();p.add_argument('--start',default='L1');p.add_argument('--only');args=p.parse_args()
    tasks=[t for t in TASKS if t[1]==args.only] if args.only else TASKS[next(i for i,t in enumerate(TASKS) if t[1]==args.start):]
    for script,item in tasks:
        out=c.BASE/'execution_logs';out.mkdir(exist_ok=True)
        path=out/(item+'_'+str(time.time_ns())+'.log')
        cmd=[sys.executable,str(c.BASE/'scripts'/script),item]
        print('START',item,str(path),flush=True)
        start=time.monotonic()
        with path.open('w') as log:
            rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
        if rc:
            c.finish([item],item+' execution attempt','ERROR — NOT A RESULT',{'command':cmd,'returncode':rc,'elapsed_s':time.monotonic()-start,'execution_log':str(path.relative_to(c.ROOT))},out/('failed_'+item+'_'+str(time.time_ns())))
            raise SystemExit(rc)
        statuses=json.loads((c.BASE/'metadata/checklist.json').read_text())
        state=next(t['status'] for t in statuses if t['id']==item)
        print('DOCUMENTED',item,state,'elapsed_s',round(time.monotonic()-start,2),flush=True)
        if not state.startswith('COMPLETE'):
            raise SystemExit('Incomplete result requires review before next experiment: '+item)

if __name__=='__main__':main()
