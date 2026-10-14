"""New analyses of explicitly identified historical sensor recordings."""
import argparse
import copy
import csv
import json
import logging
import math
import numpy as np
import campaign as c
import crash_monitor as cm

HIST=c.ROOT/'piResults/results/final-validation'
INPUTS=[HIST/'final_aba_acquisition_test/A1_polling/raw_sensor.csv',HIST/'clipping/motion_session_raw.csv',HIST/'clipping/motion_session_raw_part2.csv']

def load(path):
    import pandas as pd
    d=pd.read_csv(path)
    # Unclean shutdown can leave zero-filled or incomplete trailing rows.
    cols=['t_monotonic','ax_ms2','ay_ms2','az_ms2','gx_dps','gy_dps','gz_dps']
    before=len(d);d=d.dropna(subset=cols);d=d[d.t_monotonic>0]
    if np.any(np.diff(d.t_monotonic)<=0):raise ValueError('Non-monotonic retained sensor timestamps')
    return d.t_monotonic.to_numpy(),d[cols[1:]].to_numpy(),before-len(d)

def stats(dt):
    ms=np.asarray(dt)*1000
    bins=[0,10,15,25,30,40,60,100,float('inf')];counts=np.histogram(ms,bins)[0]
    return {'n':len(ms),'mean_ms':float(ms.mean()),'median_ms':float(np.median(ms)),'std_ms':float(ms.std()),
            'rms_error_from_20ms':float(np.sqrt(np.mean((ms-20)**2))),
            **{'p'+str(p)+'_ms':float(np.percentile(ms,p)) for p in [90,95,99,99.9]},'max_ms':float(ms.max()),
            'histogram_edges_ms':[0,10,15,25,30,40,60,100,'inf'],'counts_left_closed_right_open':counts.tolist(),
            'deviation_counts':{str(t):int(sum(abs(ms-20)>t)) for t in [2,5,8]}}

def source(path,removed=0):
    return {'file':str(path.relative_to(c.ROOT)),'sha256':c.sha(path),'origin':'HISTORICAL recording; fresh analysis, not a fresh hardware trial','invalid_rows_removed':removed}

def timing():
    results=[]
    for path in INPUTS:
        ts,x,removed=load(path);results.append({**source(path,removed),**stats(np.diff(ts))})
    for path in sorted((HIST/'scheduler_repeats').glob('*_dt.csv')):
        dt=np.loadtxt(path,delimiter=',',skiprows=1)/1000
        results.append({**source(path),**stats(dt)})
    c.finish(['E1'],'Complete observed-dt distributions','COMPLETE (HISTORICAL INPUTS)',{'recordings':results,'note':'No FIFO synthetic timestamps used. Explicit interval-bin convention prevents boundary ambiguity.'},c.BASE/'stream_E1')

class Adaptive(cm.CausalGravityFilter):
    def set_dt(self,dt):self.alpha=math.exp(-2*math.pi*.3*max(dt,0))

def replay(ts,x,threshold=.06,adaptive=False,repair=None):
    cfg=cm.load_config(c.BASE/'frozen/deploy/config.yaml');cfg=copy.deepcopy(cfg);cfg['sensor']['timing_guard']['max_dt_s']=threshold
    model=cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz')
    f=Adaptive(.3,50) if adaptive else cm.CausalGravityFilter(.3,50)
    scorer=cm.WindowScorer(cfg,model,f);guard=cm.SampleStreamGuard(cfg['sensor']['timing_guard'],.02,logging.getLogger('quiet'))
    th=cm.load_model_thresholds(cfg);policy=cm.TriggerPolicy(*th,3,60)
    rows=[];inserted=0;run=0;runs=[];last=None;prev=None
    def feed(t,v,idx,synthetic):
        nonlocal run,last
        gap,dt=guard.observe(t)
        if gap:
            runs.append(run);run=0;scorer.clear();guard.record_window_invalidated()
            if dt>=1:f.reset()
        run+=1
        if adaptive:f.set_dt(.02 if dt is None else dt)
        scorer.append(v);res=scorer.try_score();last=t
        if res is not None:
            guard.record_window_scored();positive,fired=policy.update(res['crash_prob'],res['recon_error'],now=t-ts[0])
            rows.append({'sample_index':idx,'timestamp':float(t),'synthetic_end':synthetic,'probability':res['crash_prob'],'reconstruction':res['recon_error'],'positive':positive,'triggered':fired})
    for i,(t,v) in enumerate(zip(ts,x)):
        dt=t-ts[i-1] if i else .02
        isolated=i>=2 and ts[i-1]-ts[i-2]<=.03 and (i+1==len(ts) or ts[i+1]-t<=.03)
        if repair and .03<dt<=.06 and isolated:
            # Exactly one midpoint sample, not a variable-density resampling.
            vv=(x[i-1]+v)/2 if repair=='linear' else x[i-1]
            feed((ts[i-1]+t)/2,vv,i-.5,True);inserted+=1
        feed(t,v,i,False)
    runs.append(run);snap=guard.snapshot();n=len(x)+inserted;nom=max(0,1+(len(x)-60)//15)
    opportunity=sum(max(0,r-90+1) for r in runs)/max(1,n-90+1)
    summary={'scored':len(rows),'nominal_received_sample_positions':nom,'nominal_elapsed_time_positions':max(0,1+int(((ts[-1]-ts[0])*50-59)//15)),
             'invalidations':snap['windows_invalidated'],'V_T_scored_over_scored_plus_resets':len(rows)/max(1,len(rows)+snap['windows_invalidated']),
             'C_D_received_sample_denominator':len(rows)/nom if nom else None,'inserted_samples':inserted,
             'p_valid_90_sample_position':opportunity,'confirmed_alert_events':sum(r['triggered'] for r in rows),
             'trigger_timestamps':[r['timestamp'] for r in rows if r['triggered']],
             'guard_threshold_s':threshold,'run_lengths_samples':runs}
    return rows,summary

def compare_rows(a,b):
    aa={r['sample_index']:r for r in a if not r['synthetic_end']};bb={r['sample_index']:r for r in b if not r['synthetic_end']}
    common=sorted(aa.keys()&bb.keys())
    return {'matched_end_sample_windows':len(common),'reference_only':len(aa.keys()-bb.keys()),'transformed_only':len(bb.keys()-aa.keys()),
            'classifier_mae':float(np.mean([abs(aa[i]['probability']-bb[i]['probability']) for i in common])) if common else None,
            'reconstruction_mae':float(np.mean([abs(aa[i]['reconstruction']-bb[i]['reconstruction']) for i in common])) if common else None,
            'or_flips':sum(aa[i]['positive']!=bb[i]['positive'] for i in common),
            'or_agreement':float(np.mean([aa[i]['positive']==bb[i]['positive'] for i in common])) if common else None,
            'caveat':'Only common window end indices compared. Interpolation may change sample contents and scheduling; unmatched windows are not silently treated as agreeing. No crash labels exist for these physical captures.'}

def stream(which):
    out=c.BASE/('stream_'+which);out.mkdir(exist_ok=True);c.save(out/'metadata.json',c.metadata());results=[]
    for ix,path in enumerate(INPUTS):
        ts,x,removed=load(path);base,bs=replay(ts,x,.06 if which in ['E2','E3'] else .03)
        c.save(out/f'{ix}_reference_windows.json',base)
        row={**source(path,removed),'reference':bs}
        if which=='E2':
            jitter=[];cp=[];rr=[]
            for r in base:
                i=int(r['sample_index']);local=np.diff(ts[max(0,i-59):i+1])
                jitter.append(float(np.sqrt(np.mean((local-.02)**2))));cp.append(r['probability']);rr.append(r['reconstruction'])
            def corr(a,b):return float(np.corrcoef(a,b)[0,1]) if np.std(a)>0 and np.std(b)>0 else None
            row.update(dt=stats(np.diff(ts)),window_jitter_correlation={'classifier':corr(jitter,cp),'reconstruction':corr(jitter,rr)},
                       caveat='Pearson correlation is descriptive, overlapping windows are dependent. Null means constant score/jitter; no inferential p-value asserted.')
        else:
            variants=[('adaptive_alpha',.06,True,None)] if which=='E3' else ([('linear_one_sample',.03,False,'linear'),('hold_one_sample',.03,False,'hold')] if which=='F1' else [(str(ms)+'ms',ms/1000,False,None) for ms in [25,30,35,40,60]])
            row['variants']={}
            for name,threshold,adaptive,repair in variants:
                rows,summary=replay(ts,x,threshold,adaptive,repair);c.save(out/f'{ix}_{name}_windows.json',rows)
                row['variants'][name]={'summary':summary,'fidelity':compare_rows(base,rows)}
        results.append(row)
    c.finish([which],which+' sensor-stream analysis','COMPLETE (HISTORICAL INPUTS)',{'recordings':results,
             'policy_versions':'60 ms is frozen current deployment; 30 ms historical policy is explicit reference for F1/F2.',
             'class_specific_fidelity':'Not estimable for unlabeled physical recordings; no invented crash-class metric.'},out)

def pause():
    path=INPUTS[1];ts,x,removed=load(path);x=x[:300]
    out=c.BASE/'stream_H2';out.mkdir(exist_ok=True);cfg=cm.load_config(c.BASE/'frozen/deploy/config.yaml')
    model=cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz');results={}
    for mode in ['continuous','unexpected_2s_gap','known_cancel_pause']:
        f=cm.CausalGravityFilter(.3,50);scorer=cm.WindowScorer(cfg,model,f);guard=cm.SampleStreamGuard(cfg['sensor']['timing_guard'],.02,logging.getLogger('pause'))
        scores=[];samples=[];offset=0
        for i,v in enumerate(x):
            if i==150 and mode!='continuous':
                offset=2 if mode=='unexpected_2s_gap' else 30
                if mode=='known_cancel_pause':scorer.clear();guard.reset_baseline()
            gap,dt=guard.observe(i*.02+offset)
            if gap:
                scorer.clear()
                if dt>=1:f.reset()
            scorer.append(v)
            if 150<=i<270:samples.append({'sample':i,'filtered':list(scorer.buffer[-1]),'gravity_state':f.gravity.tolist()})
            r=scorer.try_score()
            if r is not None:scores.append({'sample':i,'probability':r['crash_prob'],'reconstruction':r['recon_error']})
        c.save(out/(mode+'_first120.json'),samples);results[mode]=scores
    c.finish(['H2'],'Pause/reset replay','COMPLETE (SOFTWARE REPLAY)',{'source':source(path,removed),'scores':results,
             'behavior':'Unexpected >=1 s gap resets EMA; known countdown cancellation pause clears window and resets guard baseline but preserves EMA, matching main(). These tests characterize transient scores; they do not prove absence of artifacts for every possible post-pause orientation.'},out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('experiment',choices=['E1','E2','E3','F1','F2','H2']);args=p.parse_args()
    if args.experiment=='E1':timing()
    elif args.experiment=='H2':pause()
    else:stream(args.experiment)
