"""Analyze a saved cold/warm raw pair without inventing missing startup coverage."""
import argparse
import json
import logging
import numpy as np
import pandas as pd
import campaign as c
import crash_monitor as cm


def main():
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args()
    source=c.BASE/a.label;session=json.loads((source/'summary.json').read_text())
    if session['status']!='CAPTURED; OFFLINE ANALYSIS AND OPERATOR ATTESTATION PENDING':raise RuntimeError('Pair not fully captured')
    frozen=json.loads((c.BASE/'hashes/initial_artifacts.json').read_text())
    if not all(c.sha(c.ROOT/k)==v for k,v in frozen.items()):raise RuntimeError('Frozen artifacts changed')
    cfg=cm.load_config(c.BASE/'frozen/deploy/config.yaml')
    records={};checks={};configs=[]
    for phase in ['cold','warm']:
        out=source/phase;s=json.loads((out/'summary.json').read_text());raw=pd.read_csv(out/'raw.csv',float_precision='round_trip')
        before,during,after=[json.loads((out/f'registers_{name}.json').read_text()) for name in ['before','during','restored']];configs.append(during)
        checks[phase+'_full_duration']=s['elapsed_s']>=600 and s['exception'] is None and s['cleanup_error'] is None
        checks[phase+'_raw_rows']=len(raw)==s['samples'] and np.array_equal(raw.sample_idx,np.arange(len(raw)))
        checks[phase+'_time_order']=bool(np.all(np.diff(raw.t_monotonic)>0))
        checks[phase+'_restored']=before==after
        arr=raw[['ax_raw','ay_raw','az_raw','gx_raw','gy_raw','gz_raw']].to_numpy()*np.array([9.80665/16384]*3+[1/131]*3)
        scorer=cm.WindowScorer(cfg,cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz'),cm.CausalGravityFilter(.3,50))
        guard=cm.SampleStreamGuard(cfg['sensor']['timing_guard'],.02,logging.getLogger('cold_warm'))
        outputs=[]
        for index,(t,sample) in enumerate(zip(raw.t_monotonic,arr)):
            gap,dt=guard.observe(t)
            if gap:
                scorer.clear()
                if dt>=guard.long_gap_reset_s:scorer.gravity_filter.reset()
            scorer.append(sample);r=scorer.try_score()
            if r is not None:outputs.append([index,t,r['crash_prob'],r['recon_error']])
        pd.DataFrame(outputs,columns=['sample_idx','t_monotonic','crash_prob','recon_error']).to_csv(out/'offline_scores.csv',index=False)
        scores=np.asarray(outputs).reshape(-1,4)
        records[phase]={'first_sample_uptime_s':float(raw.t_monotonic.iloc[0]),'last_sample_uptime_s':float(raw.t_monotonic.iloc[-1]),'n_samples':len(raw),'n_scored_windows':len(scores),
                        'axes':{axis:{'mean':float(arr[:,i].mean()),'std':float(arr[:,i].std())} for i,axis in enumerate(['ax','ay','az','gx','gy','gz'])},
                        'sensor_temperature_raw_mean':float(raw.temperature_raw.mean()),
                        'score_distributions':{name:{str(q):float(np.percentile(scores[:,i],q)) for q in [0,50,95,99,100]} for name,i in [('classifier',2),('reconstruction',3)]},
                        'raw_sha256':c.sha(out/'raw.csv')}
    checks['same_configuration']=configs[0]==configs[1]
    checks['warm_after_one_hour']=records['warm']['first_sample_uptime_s']>=3600
    result={'checks':checks,'phases':records,'missing_startup_seconds':min(600,records['cold']['first_sample_uptime_s']),
            'warm_minus_cold_axis_mean':{axis:records['warm']['axes'][axis]['mean']-records['cold']['axes'][axis]['mean'] for axis in records['cold']['axes']},
            'scope':'I2 early/warm comparison only. Nonzero startup delay cannot supply literal first-ten-minute coverage. Scores are offline replay, not online latency measurements. Power removal, stationarity and unchanged orientation require operator confirmation.'}
    c.finish([],'Earlier-start cold/warm comparison','VERIFIED COMPARISON; STARTUP COVERAGE AND ATTESTATION QUALIFICATIONS' if all(checks.values()) else 'FAIL',result,source/'analysis')
    if not all(checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
