"""Derive remaining evidence from fresh hardware captures after completion."""
import argparse
import json
import numpy as np
import pandas as pd
import campaign as c

def aba_metrics():
    import itertools
    out=c.BASE/'05_corrected_aba_metrics';results={}
    for label in ['A1_polling','B_fifo','A2_polling']:
        directory=c.BASE/'05_corrected_aba'/label
        summary=json.loads((directory/'summary.json').read_text())
        if summary['exception'] or summary['elapsed_s']<1200:
            raise RuntimeError('Incomplete arm: '+label)
        raw=pd.read_csv(directory/'raw_sensor.csv',float_precision='round_trip')
        windows=pd.read_csv(directory/'window_scores.csv',float_precision='round_trip')
        resources=json.loads((directory/'resources.json').read_text())
        dt=np.diff(raw.t_monotonic.to_numpy());minutes=summary['elapsed_s']/60
        cfg=json.loads((directory/'configuration.json').read_text())
        cutoff=cfg['sensor']['timing_guard']['max_dt_s']
        dropped=sum(max(0,round(float(t)/.02)-1) for t in dt if t>cutoff)
        nominal_time=max(0,1+int(np.floor((summary['elapsed_s']*50-60)/15)))
        positive=windows.or_positive.astype(str).str.lower().isin(['true','1']).to_numpy()
        longest=max((len(list(group)) for value,group in itertools.groupby(positive) if value),default=0)
        frequencies=[v for row in resources for v in row['cpu_frequency_khz'].values()]
        results[label]={
            'raw_sha256':c.sha(directory/'raw_sensor.csv'),
            'windows_sha256':c.sha(directory/'window_scores.csv'),
            'dt_bins':{'lt10ms':int(sum(dt<.01)), '10_to_30ms_inclusive':int(sum((dt>=.01)&(dt<=.03))),
                       'above30_to_60ms_inclusive':int(sum((dt>.03)&(dt<=.06))), 'above60ms':int(sum(dt>.06))},
            'guard_cutoff_s':cutoff,'gaps_per_min':int(sum(dt>cutoff))/minutes,
            'guard_suspected_dropped_equivalent':dropped,'guard_dropped_equivalent_per_min':dropped/minutes,
            'nominal_elapsed_time_positions':nominal_time,
            'nominal_received_sample_positions':summary['nominal_positions_received_samples'],
            'scored_windows':len(windows),
            'unformed_received_sample_positions':summary['nominal_positions_received_samples']-len(windows),
            'elapsed_time_nominal_minus_scored_signed':nominal_time-len(windows),
            'C_D_elapsed_time_denominator':len(windows)/nominal_time if nominal_time else None,
            'longest_positive_scored_window_run':longest,
            'cpu_frequency_khz_observed_unique':sorted(set(frequencies)),
            'cpu_temp_min_max_c':[min(r['cpu_temp_c'] for r in resources),max(r['cpu_temp_c'] for r in resources)] if resources else None,
            'timing_note':'FIFO intervals reflect host batch availability; dropped-equivalent is the guard heuristic, not verified missing FIFO packets.',
            'coverage_note':'Resets are counted by the live guard; they are not the count of every unformed candidate. Received-sample and nominal elapsed-time denominators are both supplied. If measured sample rate exceeds 50 Hz, the elapsed-time count ratio can exceed one and its signed deficit can be negative; neither is a probability or a count of lost windows.'}
    c.finish(['B4'],'Corrected A–B–A additional timing and coverage metrics','COMPLETE (CONFIGURATION QUALIFIED)',
             {'arms':results,'scope':'Derived from the completed fresh three-arm acquisition. Main per-arm summaries retain scores, signal statistics, errors, latency, guard telemetry and alert counts.'},out)

def aba_replay():
    import crash_monitor as cm
    import logging
    out=c.BASE/'05_corrected_aba_replay';out.mkdir(exist_ok=True);result={}
    cfg=cm.load_config(c.BASE/'frozen/deploy/config.yaml');thresholds=cm.load_model_thresholds(cfg)
    for label in ['A1_polling','B_fifo','A2_polling']:
        directory=c.BASE/'05_corrected_aba'/label
        raw=pd.read_csv(directory/'raw_sensor.csv',float_precision='round_trip');live=pd.read_csv(directory/'window_scores.csv',float_precision='round_trip')
        model=cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz')
        scorer=cm.WindowScorer(cfg,model,cm.CausalGravityFilter(.3,50));guard=cm.SampleStreamGuard(cfg['sensor']['timing_guard'],.02,logging.getLogger('replay'))
        reconstructed=[]
        for row in raw.itertuples():
            gap,dt=guard.observe(row.t_monotonic)
            if gap:
                scorer.clear()
                if dt>=1:scorer.gravity_filter.reset()
            scorer.append([row.ax_ms2,row.ay_ms2,row.az_ms2,row.gx_dps,row.gy_dps,row.gz_dps]);r=scorer.try_score()
            if r is not None:reconstructed.append([row.sample_idx,r['crash_prob'],r['recon_error']])
        arr=np.asarray(reconstructed);assert np.array_equal(arr[:,0],live.sample_idx.to_numpy()),'Window alignment failure'
        observed=live[['crash_prob','recon_error']].to_numpy();delta=abs(arr[:,1:]-observed)
        np.save(out/(label+'_scores.npy'),arr)
        result[label]={'windows':len(arr),'raw_sha256':c.sha(directory/'raw_sensor.csv'),
                       'max_abs_score_difference':delta.max(axis=0).tolist(),'mean_abs_score_difference':delta.mean(axis=0).tolist(),
                       'exact_float_equal':bool(np.array_equal(arr[:,1:],observed)),
                       'or_agreement':float(np.mean(((arr[:,1]>thresholds[0])|(arr[:,2]>thresholds[1]))==((observed[:,0]>thresholds[0])|(observed[:,1]>thresholds[1]))))}
    c.finish(['B5'],'Fresh acquisition replay diagnostic','COMPLETE',{'arms':result,
             'method':'Same raw samples, host availability timestamps, scorer/guard/filter/model; no re-estimated sensor timestamps. Score equivalence checked at identical endpoint sample indices. Policy event timing remains host-execution-dependent.'},out)

def aba_figure():
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=c.BASE/'presentation_N1';fig,axes=plt.subplots(2,3,figsize=(12,5),sharex='col',sharey='row')
    for col,name in enumerate(['A1_polling','B_fifo','A2_polling']):
        path=c.BASE/'05_corrected_aba'/name/'raw_sensor.csv';d=pd.read_csv(path);t=d.t_monotonic-d.t_monotonic.iloc[0];mask=(t>=60)&(t<=65)
        for i,cols in enumerate([['ax_ms2','ay_ms2','az_ms2'],['gx_dps','gy_dps','gz_dps']]):
            for axis in cols:axes[i,col].plot(t[mask]-60,d.loc[mask,axis],label=axis[:2],linewidth=.7)
            axes[i,col].legend(fontsize=7);axes[i,col].set_ylabel('m/s²' if i==0 else 'deg/s')
        axes[0,col].set_title(name);axes[1,col].set_xlabel('Elapsed within selected segment (s)')
    fig.suptitle('Matched elapsed-time segments; sequential trials, not simultaneous recordings');fig.tight_layout();out.mkdir(exist_ok=True)
    for ext in ['png','pdf']:fig.savefig(out/('raw_aba.'+ext),dpi=180)
    plt.close(fig);c.finish(['N1'],'Corrected A–B–A raw signal figure','COMPLETE',{'segment':'Seconds 60–65 from each sequential corrected trial, identical y axes per sensor type. Traces are NOT physically simultaneous.','files':['raw_aba.png','raw_aba.pdf']},out)

def gc_analysis():
    out=c.BASE/'runtime_K2';rows=[]
    for directory in [c.BASE/'08_high_range_20min',c.BASE/'thermal_3h']:
        if not (directory/'summary.json').exists():continue
        d=pd.read_csv(directory/'raw_sensor.csv');w=pd.read_csv(directory/'window_scores.csv');g=json.loads((directory/'gc_events.json').read_text());res=json.loads((directory/'resources.json').read_text())
        starts={};intervals=[]
        for event in g:
            gen=event['generation']
            if event['phase']=='start':starts[gen]=event['t_monotonic']
            elif gen in starts:intervals.append((starts.pop(gen),event['t_monotonic']))
        times=d.t_monotonic.to_numpy();dt=np.diff(times);long=np.flatnonzero(dt>.03)+1
        overlap=sum(any(a<=times[i] and b>=times[i-1] for a,b in intervals) for i in long)
        processing_tail=w[w.processing_ms>w.processing_ms.quantile(.99)]
        tail_overlap=sum(any(a<=r.t_monotonic and b>=r.t_monotonic-r.processing_ms/1000 for a,b in intervals) for r in processing_tail.itertuples())
        rows.append({'run':directory.name,'gc_intervals':len(intervals),'gc_duration_max_ms':max(((b-a)*1000 for a,b in intervals),default=0),
                     'dt_above_30ms':len(long),'long_dt_overlapping_gc':overlap,'processing_above_p99':len(processing_tail),'processing_tails_overlapping_gc':tail_overlap,
                     'context_switches_delta':{k:res[-1][k]-res[0][k] for k in ['ctx_voluntary','ctx_involuntary','minor_faults','major_faults']} if res else None})
    if not rows:raise RuntimeError('No completed fresh runtime capture')
    c.finish(['K2'],'GC/runtime overlap analysis','COMPLETE',{'runs':rows,'limitation':'Temporal overlap is descriptive association, not proof that GC caused a gap. Context switches/faults sampled at approximately 1 Hz; cannot localize all pauses to individual reads.'},out)

def high_range_summary():
    directory=c.BASE/'08_high_range_20min'
    summary=json.loads((directory/'summary.json').read_text())
    if summary['exception'] or summary['elapsed_s']<1200:
        raise RuntimeError('High-range run did not complete its full duration')
    resources=json.loads((directory/'resources.json').read_text())
    report={}
    for key in ['cpu_pct','rss_bytes','cpu_temp_c','sensor_temp_raw']:
        values=np.asarray([r[key] for r in resources],dtype=float)
        report[key]={'min':float(values.min()),'median':float(np.median(values)),
                     'p95':float(np.percentile(values,95)),'max':float(values.max()),
                     'first':float(values[0]),'last':float(values[-1])}
    restored={}
    for name in ['06_high_range_register_check','06_high_range_stationary','08_high_range_20min']:
        base=c.BASE/name
        before=json.loads((base/'registers_before.json').read_text())
        after=json.loads((base/'registers_restored.json').read_text())
        # Volatile status/count registers are not configuration restoration checks.
        fields=['SMPLRT_DIV','CONFIG','GYRO_CONFIG','ACCEL_CONFIG','ACCEL_CONFIG2',
                'FIFO_EN','USER_CTRL','INT_ENABLE','PWR_MGMT_1','PWR_MGMT_2']
        restored[name]={k:before[k]==after[k] for k in fields}
        if not all(restored[name].values()):raise RuntimeError('Register restoration mismatch: '+name)
    c.finish(['C4'],'High-range live resource and restoration supplement','COMPLETE (UNATTENDED)',
             {'primary_evidence':'piResults/results/final-closure/08_high_range_20min',
              'resources_sha256':c.sha(directory/'resources.json'),'resource_samples':len(resources),
              'resources':report,'restored_configuration_fields':restored,
              'summary':summary,
              'limits':'No independently confirmed mounting/stationarity. Scores and timing characterize technical compatibility, not crash sensitivity. RSS includes research recording buffers.'},
             c.BASE/'08_high_range_resource_summary')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('experiment',choices=['B4','B5','N1','K2','C4']);a=p.parse_args()
    {'B4':aba_metrics,'B5':aba_replay,'N1':aba_figure,'K2':gc_analysis,'C4':high_range_summary}[a.experiment]()
