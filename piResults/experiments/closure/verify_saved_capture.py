"""Offline raw/score/policy replay and FIFO-byte verification; never opens hardware."""
import argparse
import json
import logging
import struct
import numpy as np
import pandas as pd
import campaign as c
import crash_monitor as cm


def verify(label, seconds):
    source=c.BASE/label
    read=lambda name:json.loads((source/name).read_text())
    s=read('summary.json');cfg=read('configuration.json')
    raw=pd.read_csv(source/'raw_sensor.csv',float_precision='round_trip')
    w=pd.read_csv(source/'window_scores.csv',float_precision='round_trip')
    before,after=[read('registers_'+name+'.json') for name in ['before','restored']]
    during=read('registers_during.json') if (source/'registers_during.json').exists() else {}
    fields=['SMPLRT_DIV','CONFIG','GYRO_CONFIG','ACCEL_CONFIG','ACCEL_CONFIG2','USER_CTRL','FIFO_EN','INT_PIN_CFG','INT_ENABLE','PWR_MGMT_1','PWR_MGMT_2']
    initial=json.loads((c.BASE/'hashes/initial_artifacts.json').read_text())
    checks={'frozen_artifacts_unchanged':all(c.sha(c.ROOT/name)==digest for name,digest in initial.items()),
            'full_duration':s['seconds_requested']==seconds and s['elapsed_s']>=seconds,
            'no_exception':s['exception'] is None,'no_i2c_errors':s['i2c_failures']==0,
            'raw_rows_match':len(raw)==s['n_samples'],'window_rows_match':len(w)==s['n_windows'],
            'nonempty':len(raw)>0 and len(w)>0,
            'indices_contiguous':bool(np.array_equal(raw.sample_idx,np.arange(len(raw)))),
            'times_nondecreasing':bool(np.all(np.diff(raw.t_monotonic)>=0)),
            'registers_restored':all(before[k]==after[k] for k in fields)}
    if s['mode']=='iio':
        checks.pop('no_i2c_errors')
        checks['cleanup_success']=not s['cleanup_errors']
    if not checks['frozen_artifacts_unchanged']:raise RuntimeError('Frozen artifacts changed')
    scorer=cm.WindowScorer(cfg,cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz'),cm.CausalGravityFilter(.3,50))
    guard=cm.SampleStreamGuard(cfg['sensor']['timing_guard'],.02,logging.getLogger('offline'))
    replay=[];gaps=0
    for r in raw.itertuples():
        gap,dt=guard.observe(r.t_monotonic)
        if gap:
            gaps+=1;scorer.clear()
            if dt>=guard.long_gap_reset_s:scorer.gravity_filter.reset()
        scorer.append([r.ax_ms2,r.ay_ms2,r.az_ms2,r.gx_dps,r.gy_dps,r.gz_dps])
        v=scorer.try_score()
        if v is not None:replay.append([r.sample_idx,v['crash_prob'],v['recon_error']])
    replay=np.asarray(replay).reshape(-1,3)
    policy=cm.TriggerPolicy(*cm.load_model_thresholds(cfg),3,60)
    decisions=[policy.update(r.crash_prob,r.recon_error,now=r.t_monotonic) for r in w.itertuples()]
    checks.update(replay_endpoints_exact=bool(np.array_equal(replay[:,0],w.sample_idx)),
                  replay_scores_exact=bool(np.array_equal(replay[:,1:],w[['crash_prob','recon_error']].to_numpy())),
                  replay_policy_exact=bool(np.array_equal(decisions,w[['or_positive','confirmed_triggered']].to_numpy())),
                  gap_count_matches=gaps==s['gap_count'])
    if s['mode']=='fifo-drdy':
        e=pd.read_csv(source/'gpio_edges.csv',float_precision='round_trip',keep_default_na=False)
        packets=[];times=[]
        for row in e.itertuples():
            vals=list(struct.iter_unpack('>6h',bytes.fromhex(row.payload_hex)))
            assert len(vals)==row.packets
            packets.extend(vals);times.extend([row.read_end_monotonic]*len(vals))
        scale=np.array([9.80665/16384]*3+[1/131]*3)
        arr=np.asarray(packets).reshape(-1,6)*scale
        checks.update(no_overflow=s['fifo_overflows']==0,no_edge_timeout=s['data_ready']['timeouts']==0,
                      edge_rows_match=len(e)==s['data_ready']['edges_read'],
                      fifo_packet_accounting=len(packets)==len(raw)+s['data_ready']['packets_pending_at_deadline'],
                      fifo_raw_decode_exact=bool(np.array_equal(arr[:len(raw)],raw[['ax_ms2','ay_ms2','az_ms2','gx_dps','gy_dps','gz_dps']].to_numpy())),
                      fifo_host_times_exact=bool(np.array_equal(times[:len(raw)],raw.t_monotonic)),
                      fifo_configuration_correct=all(during[k]==v for k,v in {'WHO_AM_I':112,'CONFIG':4,'ACCEL_CONFIG2':4,'SMPLRT_DIV':19,'GYRO_CONFIG':0,'ACCEL_CONFIG':0,'INT_PIN_CFG':0,'INT_ENABLE':17,'FIFO_EN':120,'USER_CTRL':64}.items()))
    if s['mode']=='iio':
        from iio_capture import decode,AXES
        config=read('iio_configuration.json');payload=(source/'iio_buffer.bin').read_bytes();size=config['record_bytes']
        decoded=[decode(payload[i:i+size],config['layout']) for i in range(0,len(payload),size)]
        vals=[[row[name]*(config['accel_scale'] if i<3 else config['gyro_scale_dps']) for i,name in enumerate(AXES)] for row in decoded]
        checks.update(iio_complete_records=len(payload)%size==0,iio_record_count=len(decoded)==len(raw),
            iio_raw_decode_exact=bool(np.array_equal(vals,raw[['ax_ms2','ay_ms2','az_ms2','gx_dps','gy_dps','gz_dps']].to_numpy())),
            iio_timestamp_decode_exact=bool(np.array_equal([row['in_timestamp']/1e9 for row in decoded],raw.t_monotonic)),
            iio_rate_configured=float(config['attrs']['sampling_frequency'])==50)
    resources=read('resources.json')
    metrics={k:s[k] for k in ['mode','elapsed_s','sample_rate_hz','n_samples','n_windows','gap_count','C_D','V_T_scored_over_scored_plus_resets','p_valid_90_sample_position','timing','processing_ms','i2c_failures','confirmed_alert_events','score_distributions','physical_axes']}
    metrics['resources']={k:{'min':min(v[k] for v in resources),'max':max(v[k] for v in resources),'mean':float(np.mean([v[k] for v in resources]))} for k in ['cpu_pct','rss_bytes','cpu_temp_c']}
    return {'label':label,'checks':checks,'metrics':metrics,'source_hashes':{p.name:c.sha(p) for p in source.iterdir() if p.is_file()},'scope':'Offline replay and byte integrity. FIFO shared host times are not physical sample jitter. Physical conditions require operator attestation.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--seconds',type=float,required=True);a=p.parse_args()
    result=verify(a.label,a.seconds)
    ok=all(result['checks'].values())
    c.finish([],'Saved capture verification','PASS' if ok else 'FAIL',result,c.BASE/(a.label+'_verification'))
    if not ok:raise SystemExit(1)
