"""Presentation artifacts rebuilt from identified raw evidence, not old prose."""
import argparse
import csv
import json
import numpy as np
import pandas as pd
import campaign as c

def setup():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    return plt

def savefig(fig,out,name):
    out.mkdir(exist_ok=True,parents=True)
    for ext in ['png','pdf']:fig.savefig(out/(name+'.'+ext),dpi=180,bbox_inches='tight')

def pairs():
    from stream_analysis import HIST,stats
    out=c.BASE/'presentation_N3';rows=[]
    for pair in [1,2,3]:
        for cond in ['loaded','reduced']:
            dtfile=HIST/f'scheduler_repeats/run{pair}_{cond}_dt.csv'
            dt=np.loadtxt(dtfile,delimiter=',',skiprows=1)/1000;n=len(dt)+1
            # Exact main() count behavior: gap resets, then CURRENT sample is appended.
            run=0;new=0;scored=0;gaps=0
            for gap in [False,*list(dt>.03)]:
                if gap:run=0;new=0;gaps+=1
                run+=1;new+=1
                if run>=60 and new>=15:scored+=1;new=0
            summary=json.loads((HIST/f'scheduler_repeats/run{pair}_{cond}_detector.json').read_text())
            rows.append({'pair':pair,'condition':cond,'raw_dt_sha256':c.sha(dtfile),'gap_count':gaps,
                         'gaps_per_min_actual_interval_time':gaps/(sum(dt)/60),'corrected_count_replay_scored':scored,
                         'C_D':scored/(1+(n-60)//15),'V_T':scored/(scored+gaps),
                         'historically_recorded_scored':summary['n_windows_generated'],
                         'processing_p99_ms':summary['per_window_latency_ms'].get('p99_ms')})
    out.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(out/'pairs.csv',index=False)
    plt=setup();fig,axes=plt.subplots(1,2,figsize=(8,3.5))
    for pair in [1,2,3]:
        rr=[r for r in rows if r['pair']==pair]
        for ax,key in zip(axes,['gaps_per_min_actual_interval_time','C_D']):ax.plot([0,1],[r[key] for r in rr],'o-',label=f'Pair {pair}')
    for ax,label in zip(axes,['Gaps/min (>30 ms)','Decision coverage']):ax.set(xticks=[0,1],xticklabels=['Loaded','Reduced'],ylabel=label);ax.legend()
    fig.suptitle('Historical matched pairs — recomputed from raw dt');fig.tight_layout();savefig(fig,out,'scheduler_pairs');plt.close(fig)
    c.finish(['N3'],'Individual scheduler-pair figure','COMPLETE (HISTORICAL INPUTS)',{'pairs':rows,
             'method':'Current sample appended after gap, matching deployed main(); old coverage helper incorrectly skipped that sample. 30-ms historical guard explicit. Actual dt sum used for exposure.',
             'limitation':'These are the three archived pairs, not new randomized/headless repetitions. Reversals are retained.'},out)

def dtplot():
    from stream_analysis import HIST
    out=c.BASE/'presentation_N4';plt=setup();fig,ax=plt.subplots(figsize=(7,4));sources=[]
    for cond in ['loaded','reduced']:
        files=sorted((HIST/'scheduler_repeats').glob(f'run*_{cond}_dt.csv'))
        data=np.concatenate([np.loadtxt(f,delimiter=',',skiprows=1) for f in files]);bins=np.arange(0,100.5,.5)
        ax.hist(data,bins=bins,histtype='step',density=True,label=f'{cond} (historical)')
        sources.append({'condition':cond,'files':[str(f.relative_to(c.ROOT)) for f in files],'n':len(data),'above_100ms':int(sum(data>100))})
    for value in [10,20,30,60]:ax.axvline(value,color='gray',linestyle='--',linewidth=.6)
    ax.set(xlabel='Host-observed interval (ms)',ylabel='Density within 0–100 ms',yscale='log',xlim=(0,100));ax.legend();fig.tight_layout();savefig(fig,out,'dt_distribution');plt.close(fig)
    c.finish(['N4'],'Timing distribution figure','COMPLETE (AVAILABLE HISTORICAL CONDITIONS)',{'sources':sources,'headless':'Not measured yet; no fabricated headless curves.','display':'0–100 ms; out-of-range counts explicitly reported. Reference lines 10/20/30/60 ms.'},out)

def benign():
    import crash_monitor as cm
    from stream_analysis import HIST
    out=c.BASE/'presentation_N5';out.mkdir(exist_ok=True)
    paths=[HIST/'clipping/motion_session_raw.csv',HIST/'clipping/motion_session_raw_part2.csv'];results=[]
    cfg=cm.load_config(c.BASE/'frozen/deploy/config.yaml');th=cm.load_model_thresholds(cfg)
    for path in paths:
        df=pd.read_csv(path,float_precision='round_trip');cols=['t_monotonic','ax_ms2','ay_ms2','az_ms2','gx_dps','gy_dps','gz_dps']
        old=len(df);df=df.dropna(subset=cols);df=df[df.t_monotonic>0]
        model=cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz')
        scorer=cm.WindowScorer(cfg,model,cm.CausalGravityFilter(.3,50));policy=cm.TriggerPolicy(*th,3,60);per={}
        # Original motion harness has NO SampleStreamGuard and preserves state at phase transitions.
        for _,r in df.iterrows():
            phase=str(r['phase']);rec=per.setdefault(phase,{'phase':phase,'samples':0,'windows':0,'max_classifier':0.,'max_reconstruction':0.,'classifier_crossings':0,'reconstruction_crossings':0,'OR_positive':0,'confirmed_alerts':0,'accel_exact_rail_hits':0,'gyro_exact_rail_hits':0})
            rec['samples']+=1
            for group,axes in [('accel',['ax','ay','az']),('gyro',['gx','gy','gz'])]:
                rec[group+'_exact_rail_hits']+=sum(r[a+'_raw'] in [-32768,32767] for a in axes)
            scorer.append(r[cols[1:]].to_numpy(dtype=float));res=scorer.try_score()
            if res is not None:
                pp,rr=res['crash_prob'],res['recon_error'];positive,trigger=policy.update(pp,rr,now=float(r.t_monotonic))
                rec['windows']+=1;rec['max_classifier']=max(rec['max_classifier'],pp);rec['max_reconstruction']=max(rec['max_reconstruction'],rr)
                rec['classifier_crossings']+=int(pp>th[0]);rec['reconstruction_crossings']+=int(rr>th[1]);rec['OR_positive']+=int(positive);rec['confirmed_alerts']+=int(trigger)
        results.append({'input':str(path.relative_to(c.ROOT)),'sha256':c.sha(path),'invalid_rows_removed':old-len(df),'phases':list(per.values())})
    pd.DataFrame([{**p,'input':r['input']} for r in results for p in r['phases']]).to_csv(out/'benign_motion.csv',index=False)
    c.finish(['N5'],'Benign-motion table recomputed','COMPLETE (HISTORICAL RAW REPLAY)',{'recordings':results,
             'method':'Replay original motion harness (no guard, continuous filter/scorer/policy across phase boundaries). Cooldown timestamps from recorded monotonic time. New raw replay, not a fresh physical motion trial.',
             'limits':'Unfinished pre-reboot phases and waiting phases are retained and identified; do not pool duplicate attempts as independent physical scenarios. Rail hits count axis observations. Original policy-call timestamps were not recorded; replay uses sample timestamps, so exact cooldown-boundary event reproduction is not guaranteed.'},out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('experiment',choices=['N3','N4','N5']);a=p.parse_args()
    {'N3':pairs,'N4':dtplot,'N5':benign}[a.experiment]()
