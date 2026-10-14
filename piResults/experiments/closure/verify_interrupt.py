"""Verify J1 capture, replay scores, and compare explicitly historical polling."""
import json
import logging
import numpy as np
import pandas as pd
import campaign as c
import crash_monitor as cm
from stream_analysis import stats


def main():
    source=c.BASE/'13_optional_drdy/stationary_20min_20261006'
    summary=json.loads((source/'summary.json').read_text())
    raw=pd.read_csv(source/'raw_sensor.csv',float_precision='round_trip')
    windows=pd.read_csv(source/'window_scores.csv',float_precision='round_trip')
    edges=pd.read_csv(source/'gpio_edges.csv',float_precision='round_trip')
    before,during,after=[json.loads((source/f'registers_{s}.json').read_text()) for s in ['before','during','restored']]
    fields=['SMPLRT_DIV','CONFIG','GYRO_CONFIG','ACCEL_CONFIG','ACCEL_CONFIG2','USER_CTRL','FIFO_EN','INT_PIN_CFG','INT_ENABLE','PWR_MGMT_1','PWR_MGMT_2']
    cfg=json.loads((source/'configuration.json').read_text())
    scorer=cm.WindowScorer(cfg,cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz'),cm.CausalGravityFilter(.3,50))
    guard=cm.SampleStreamGuard(cfg['sensor']['timing_guard'],.02,logging.getLogger('replay'))
    replay=[]
    for r in raw.itertuples():
        gap,dt=guard.observe(r.t_monotonic)
        if gap:
            scorer.clear()
            if dt>=guard.long_gap_reset_s:scorer.gravity_filter.reset()
        scorer.append([r.ax_ms2,r.ay_ms2,r.az_ms2,r.gx_dps,r.gy_dps,r.gz_dps])
        v=scorer.try_score()
        if v is not None:replay.append([r.sample_idx,v['crash_prob'],v['recon_error']])
    replay=np.asarray(replay).reshape(-1,3)
    policy=cm.TriggerPolicy(*cm.load_model_thresholds(cfg),3,60)
    decisions=[policy.update(r.crash_prob,r.recon_error,now=r.t_monotonic) for r in windows.itertuples()]
    accepted=edges[edges.accepted]
    initial=json.loads((c.BASE/'hashes/initial_artifacts.json').read_text())
    checks={
        'frozen_artifacts_unchanged':all(c.sha(c.ROOT/name)==digest for name,digest in initial.items()),
        'full_twenty_minutes':summary['seconds_requested']==1200 and summary['elapsed_s']>=1200,
        'no_capture_exception':summary['exception'] is None,
        'no_i2c_errors':summary['i2c_failures']==0,
        'no_edge_timeout':summary['data_ready']['timeouts']==0,
        'raw_rows_match':len(raw)==summary['n_samples'],
        'window_rows_match':len(windows)==summary['n_windows'],
        'accepted_edges_match':len(accepted)==len(raw),
        'edge_counts_match':len(edges)==summary['data_ready']['edges_read'],
        'discard_count_matches':len(edges)-len(accepted)==summary['data_ready']['stale_edges_discarded'],
        'sample_indices_contiguous':bool(np.array_equal(raw.sample_idx,np.arange(len(raw)))),
        'sample_times_increasing':bool(np.all(np.diff(raw.t_monotonic)>0)),
        'edge_times_increasing':bool(np.all(np.diff(edges.edge_monotonic)>0)),
        'edge_to_sample_alignment':bool(np.array_equal(accepted.read_end_monotonic.to_numpy(),raw.t_monotonic.to_numpy())),
        'registers_restored':all(before[k]==after[k] for k in fields),
        'configuration_correct':all(during[k]==v for k,v in {'WHO_AM_I':112,'CONFIG':4,'ACCEL_CONFIG2':4,'SMPLRT_DIV':19,'GYRO_CONFIG':0,'ACCEL_CONFIG':0,'INT_PIN_CFG':0,'INT_ENABLE':1,'FIFO_EN':0,'USER_CTRL':0}.items()),
        'replay_endpoints_exact':bool(np.array_equal(replay[:,0],windows.sample_idx)),
        'replay_scores_exact':bool(np.array_equal(replay[:,1:],windows[['crash_prob','recon_error']].to_numpy())),
        'policy_replay_exact':bool(np.array_equal(np.asarray(decisions),windows[['or_positive','confirmed_triggered']].to_numpy())),
    }
    records=[]
    for label,path in [('DATA_RDY current',source),('A1 polling historical',c.BASE/'05_corrected_aba/A1_polling'),('A2 polling historical',c.BASE/'05_corrected_aba/A2_polling')]:
        s=json.loads((path/'summary.json').read_text())
        resources=json.loads((path/'resources.json').read_text())
        records.append({'label':label,'source':str(path.relative_to(c.ROOT)),
            'sample_rate_hz':s['sample_rate_hz'],'dt_std_ms':s['timing']['std_ms'],'dt_p99_ms':s['timing']['p99_ms'],'dt_max_ms':s['timing']['max_ms'],
            'V_T':s['V_T_scored_over_scored_plus_resets'],'C_D':s['C_D'],'survival_90_samples':s['p_valid_90_sample_position'],
            'gaps':s['gap_count'],'i2c_errors':s['i2c_failures'],'processing_p99_ms':s['processing_ms']['99'],
            'cpu_percent_mean':float(np.mean([r['cpu_pct'] for r in resources[1:]])),
            'rss_peak_bytes':max(r['rss_bytes'] for r in resources),
            'scores':s['score_distributions'],'events':s['confirmed_alert_events'],
            'summary_sha256':c.sha(path/'summary.json')})
    out=c.BASE/'13_optional_drdy/verification_comparison_20261006'
    out.mkdir(exist_ok=True)
    flat=[{k:v for k,v in r.items() if k!='scores'} for r in records]
    pd.DataFrame(flat).to_csv(out/'comparison.csv',index=False)
    result={'checks':checks,'comparisons':records,
        'kernel_edge_intervals':stats(np.diff(edges.edge_monotonic)),
        'edge_to_host_wake_ms':{str(q):float(np.percentile((edges.host_wake_monotonic-edges.edge_monotonic)*1000,q)) for q in [50,95,99,100]},
        'stale_edges_discarded':summary['data_ready']['stale_edges_discarded'],
        'source_hashes':{p.name:c.sha(p) for p in source.iterdir() if p.is_file()},
        'limitations':'Historical polling has matching filter/range/divider and power configuration, but different boot, physical placement, workload and separate-read acquisition. This is a descriptive comparison, not a paired causal estimate of interrupt benefit. GPIO kernel timestamps are not oscilloscope measurements. libgpiod v1 provides no exact overflow count. Host sample coverage denominators use received samples. Physical stationarity is operator-reported. J3 FIFO+DATA_RDY and J2 IIO have not been performed.'}
    ok=all(checks.values())
    c.finish(['J1'] if ok else [],'DATA_RDY stationary capture verification and historical polling comparison','COMPLETE (VERIFIED; HISTORICAL COMPARATOR)' if ok else 'FAIL',result,out)
    if not ok:raise RuntimeError('Interrupt verification failed; see checks')


if __name__=='__main__':main()
