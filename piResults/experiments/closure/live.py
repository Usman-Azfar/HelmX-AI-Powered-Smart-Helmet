"""Instrument the real deployed polling/scoring path, without sending alerts.

This is a measurement harness, not a replacement monitor. Alarm handling is
recorded as a policy event; no countdown block, GPIO output, or SMS occurs.
"""
import argparse
import csv
import gc
import json
import logging
import os
import resource
import signal
import struct
import time
from pathlib import Path
import numpy as np
import psutil
import smbus2
import campaign as c
import crash_monitor as cm
from hardware import REGS,registers
from stream_analysis import stats
from headless_gate import interactive

def main():
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--seconds',type=float,default=1200)
    p.add_argument('--filtered',action='store_true');p.add_argument('--high-range',action='store_true')
    p.add_argument('--mode',choices=['polling','fifo','drdy','fifo-drdy'],default='polling')
    p.add_argument('--ids',default='');p.add_argument('--require-headless',action='store_true')
    p.add_argument('--scheduler-trace',action='store_true',help='Record filtered acquisition-thread perf scheduler events')
    p.add_argument('--operator-phase',default='',help='User-confirmed guided phase; operator action is not independently measured')
    args=p.parse_args()
    out=c.BASE/args.label;out.mkdir(parents=True,exist_ok=False)
    meta=c.metadata();c.save(out/'metadata.json',meta)
    c.save(out/'throttled_start.json',c.command(['vcgencmd','get_throttled']))
    def interrupted(signum,frame):raise InterruptedError('Termination requested; preserve partial capture and restore registers')
    signal.signal(signal.SIGTERM,interrupted)
    if args.require_headless:
        live=interactive()
        if live:raise RuntimeError('Headless gate failed: interactive processes still running '+repr(live))
    cfg=cm.load_config(c.BASE/'frozen/deploy/config.yaml');c.save(out/'configuration.json',cfg)
    if cm.mpu6050 is None:
        raise RuntimeError('Sensor driver unavailable in this Python environment; install mpu6050-raspberrypi into .pi_research_venv (not only the user site).')
    logger=logging.getLogger('capture');logger.addHandler(logging.FileHandler(out/'errors.log'));logger.setLevel(logging.WARNING)
    model=cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz')
    scorer=cm.WindowScorer(cfg,model,cm.CausalGravityFilter(.3,50));thresholds=cm.load_model_thresholds(cfg)
    policy=cm.TriggerPolicy(*thresholds,3,60);guard=cm.SampleStreamGuard(cfg['sensor']['timing_guard'],.02,logger)
    bus=smbus2.SMBus(1);before=registers(bus);c.save(out/'registers_before.json',before)
    proc=psutil.Process();proc.cpu_percent();gc_events=[]
    def gc_cb(phase,info):gc_events.append({'t_monotonic':time.monotonic(),'phase':phase,'generation':info['generation']})
    gc.callbacks.append(gc_cb)
    intervals=[];latencies=[];reads=[];scores=[];n_samples=0;resources=[];n_errors=0;error=None;runs=[];run=0;invalid=0
    fifo_overflows=0;fifo_batches=[];pending=[];drdy=None;trace=None
    try:
       # if before['WHO_AM_I'] not in (0x68, 0x70):
        #    raise RuntimeError('Device identity differs from the audited register map')
        sensor=cm.mpu6050(0x68)
        # Constructor selects clock 0. Preserve that real deployment behavior,
        # and explicitly record it rather than silently assuming clock=1.
        if args.filtered:
            for reg,val in [(0x1a,4),(0x1b,0x18 if args.high_range else 0),(0x1c,0x18 if args.high_range else 0),(0x1d,4),(0x19,19)]:
                bus.write_byte_data(0x68,reg,val)
        elif args.high_range:raise ValueError('High range requires explicit filter condition')
        if args.mode=='fifo':
            if not args.filtered:raise ValueError('Verified FIFO requires filtered 50-Hz configuration')
            bus.write_byte_data(0x68,0x23,0);bus.write_byte_data(0x68,0x6a,4);time.sleep(.01)
            bus.write_byte_data(0x68,0x6a,0x40);bus.write_byte_data(0x68,0x38,0x10);bus.write_byte_data(0x68,0x23,0x78)
        if args.mode in ('drdy','fifo-drdy'):
            if not args.filtered:raise ValueError('DATA_RDY requires audited filtered 50-Hz configuration')
            if before['WHO_AM_I'] != 0x70:
                raise RuntimeError('DATA_RDY register map requires audited identity 0x70')
            if args.mode == 'fifo-drdy':
                from fifo_drdy import FifoDataReady as DataReady
            else:
                from drdy import DataReady
            drdy=DataReady(bus,out,args.high_range)
        configured=registers(bus)
        c.save(out/'registers_during.json',configured)
        if args.filtered:
            expected={'CONFIG':4,'ACCEL_CONFIG2':4,'SMPLRT_DIV':19,
                      'GYRO_CONFIG':0x18 if args.high_range else 0,
                      'ACCEL_CONFIG':0x18 if args.high_range else 0}
            if any(configured[k]!=v for k,v in expected.items()):
                raise RuntimeError('Sensor configuration readback mismatch')
        if args.scheduler_trace:
            from scheduler_trace import SchedulerTrace
            trace=SchedulerTrace(out)
            trace.start()
        start=time.monotonic();deadline=start+args.seconds;tick=start;resource_tick=start;progress=start+60
        with (out/'raw_sensor.csv').open('w',buffering=1) as f,(out/'window_scores.csv').open('w',buffering=1) as wf:
            rw=csv.writer(f);sw=csv.writer(wf)
            rw.writerow(['sample_idx','t_monotonic','dt_ms','ax_ms2','ay_ms2','az_ms2','gx_dps','gy_dps','gz_dps','sensor_read_ms'])
            sw.writerow(['window_idx','sample_idx','t_monotonic','crash_prob','recon_error','or_positive','confirmed_triggered','anomaly_streak','processing_ms'])
            while time.monotonic()<deadline:
                tick+=.02;t0=time.perf_counter()
                if args.mode in ('drdy','fifo-drdy'):
                    try:sample,now,drdy_read_ms=drdy.read()
                    except OSError:
                        n_errors+=1
                        raise
                    t1=time.perf_counter()
                elif args.mode=='fifo':
                    if not pending:
                        st=bus.read_byte_data(0x68,0x3a);fc=int.from_bytes(bytes(bus.read_i2c_block_data(0x68,0x72,2)),'big')
                        if st&0x10 or fc>=504:
                            fifo_overflows+=1;raise RuntimeError('FIFO overflow/near-full; abort rather than accept uncertain framing')
                        buf=bytearray();nb=fc//12*12
                        for offset in range(0,nb,24):buf.extend(bus.read_i2c_block_data(0x68,0x74,min(24,nb-offset)))
                        host=time.monotonic();fifo_batches.append([host,fc,st,nb//12])
                        scale=np.array([9.80665/(2048 if args.high_range else 16384)]*3+[1/(16.4 if args.high_range else 131)]*3)
                        pending=[(np.asarray(v)*scale,host) for v in struct.iter_unpack('>6h',buf)]
                    if not pending:
                        time.sleep(.005);tick=time.monotonic();continue
                    sample,now=pending.pop(0);t1=time.perf_counter()
                else:
                    sample=cm.read_sensor(sensor,logger);t1=time.perf_counter();now=time.monotonic()
                if sample is None:
                    n_errors+=1;raise RuntimeError('Sensor read error; abort trial rather than silently omit missing data')
                read_ms=drdy_read_ms if drdy is not None else (t1-t0)*1000;gap,dt=guard.observe(now)
                if gap:
                    scorer.clear();guard.record_window_invalidated();invalid+=1;runs.append(run);run=0
                    if dt>=guard.long_gap_reset_s:scorer.gravity_filter.reset()
                run+=1;pre_ms=scorer.append(sample)
                rw.writerow([n_samples,now,'' if dt is None else dt*1000,*sample,read_ms]);n_samples+=1
                delay=tick-time.monotonic()
                if args.mode=='polling' and delay>0:time.sleep(delay)
                else:tick=time.monotonic()
                r=scorer.try_score()
                if r is not None:
                    guard.record_window_scored();t=time.monotonic();positive,fired=policy.update(r['crash_prob'],r['recon_error'],now=t)
                    total=pre_ms+r['total_ms'];latencies.append(total)
                    sw.writerow([len(scores),n_samples-1,t,r['crash_prob'],r['recon_error'],positive,fired,policy.anomaly_streak,total])
                    scores.append([r['crash_prob'],r['recon_error'],positive,fired,t])
                if now>=resource_tick:
                    if trace is not None:trace.check()
                    ru=resource.getrusage(resource.RUSAGE_SELF);ctx=proc.num_ctx_switches()
                    temp_path='/sys/class/thermal/thermal_zone0/temp'
                    resources.append({'t_monotonic':now,'cpu_pct':proc.cpu_percent(),'rss_bytes':proc.memory_info().rss,
                                      'ctx_voluntary':ctx.voluntary,'ctx_involuntary':ctx.involuntary,'minor_faults':ru.ru_minflt,'major_faults':ru.ru_majflt,
                                      'cpu_temp_c':float(open(temp_path).read())/1000,
                                      'cpu_frequency_khz':{str(p):int(p.read_text()) for p in Path('/sys/devices/system/cpu/cpufreq').glob('policy*/scaling_cur_freq')},
                                      'sensor_temp_raw':struct.unpack('>h',bytes(bus.read_i2c_block_data(0x68,0x41,2)))[0]})
                    resource_tick=now+1
                if now>=progress:
                    print(args.label,'seconds',round(now-start),'samples',n_samples,'windows',len(scores),'gaps',invalid,flush=True);progress+=60
        elapsed=time.monotonic()-start
    except Exception as e:
        logger.exception('Capture failed')
        error=repr(e)
        elapsed=time.monotonic()-start if 'start' in locals() else 0
    finally:
        gc.callbacks.remove(gc_cb)
        try:
            bus.write_byte_data(0x68,0x23,0);bus.write_byte_data(0x68,0x6a,0)
            bus.write_byte_data(0x68,0x38,0)
            if drdy is not None:
                if args.mode == 'fifo-drdy':
                    fifo_batches=drdy.batches
                    fifo_overflows=drdy.overflows
                drdy.close()
            for name in ['SMPLRT_DIV','CONFIG','GYRO_CONFIG','ACCEL_CONFIG','ACCEL_CONFIG2','USER_CTRL','FIFO_EN','INT_PIN_CFG','INT_ENABLE','PWR_MGMT_1','PWR_MGMT_2']:
                bus.write_byte_data(0x68,REGS[name],before[name])
            c.save(out/'registers_restored.json',registers(bus))
        finally:
            try:bus.close()
            finally:
                if trace is not None:
                    trace_error=trace.stop()
                    if trace_error:error=(error+'; ' if error else '')+trace_error
    runs.append(run);c.save(out/'resources.json',resources);c.save(out/'gc_events.json',gc_events);c.save(out/'fifo_batches.json',fifo_batches)
    n=n_samples;nom=max(0,1+(n-60)//15);ss=np.asarray(scores).reshape(-1,5)
    # Raw sample arrays are loaded only AFTER measurement, avoiding sample-count
    # proportional memory growth in the long-run resource trace.
    if n:
        recorded=np.loadtxt(out/'raw_sensor.csv',delimiter=',',skiprows=1,usecols=(1,3,4,5,6,7,8,9),ndmin=2)
        arr=recorded[:,1:7];intervals=np.diff(recorded[:,0]).tolist();reads=recorded[:,7].tolist()
    else:arr=np.empty((0,6))
    scale=np.array([9.80665/(2048 if args.high_range else 16384)]*3+[1/(16.4 if args.high_range else 131)]*3)
    recovered=np.rint(arr/scale)
    result={'mode':args.mode,'capture_start_monotonic':start if 'start' in locals() else None,
            'capture_end_monotonic':start+elapsed if 'start' in locals() else None,
            'fifo_overflows':fifo_overflows,'seconds_requested':args.seconds,'elapsed_s':elapsed,'n_samples':n,'sample_rate_hz':n/elapsed if elapsed else None,
            'n_windows':len(scores),'i2c_failures':n_errors,'exception':error,'timing':stats(intervals) if intervals else {},
            'nominal_positions_received_samples':nom,'C_D':len(scores)/nom if nom else None,
            'V_T_scored_over_scored_plus_resets':len(scores)/max(1,len(scores)+invalid),
            'p_valid_90_sample_position':sum(max(0,r-89) for r in runs)/max(1,n-89),'gap_count':invalid,
            'processing_ms':{str(q):float(np.percentile(latencies,q)) for q in [0,50,95,99,99.9,100]} if latencies else {},
            'processing_over_300ms':int(sum(v>.3*1000 for v in latencies)),
            'sensor_read_ms':{str(q):float(np.percentile(reads,q)) for q in [50,95,99,100]} if reads else {},
            'confirmed_alert_events':int(ss[:,3].sum()) if len(ss) else 0,
            'or_positive_windows':int(ss[:,2].sum()) if len(ss) else 0,
            'rail_counts':{a:int(sum((recovered[:,i]<=-32768)|(recovered[:,i]>=32767))) for i,a in enumerate(['ax','ay','az','gx','gy','gz'])},
            'throttled_end':c.command(['vcgencmd','get_throttled']),
            'fifo_timing_note':'FIFO packets retain common host read-completion timestamps per batch. Zero dt within batches is intentional; these are host availability metrics, not direct physical-sample jitter measurements. No invented timestamps or decimation.',
            'conditions':('Guided operator phase: '+args.operator_phase+'. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/IDE active. ' if args.operator_phase else 'Unattended, desktop/IDE state in metadata. No physical mounting confirmation. ')+'No alarm countdown or communication blocks; policy events recorded only.',
            'memory_scope':'Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.',
            'timing_scope':'Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.'}
    if drdy is not None:
        result['data_ready']={'gpio_bcm':23,'physical_pin':16,'edges_read':drdy.edges,
            'stale_edges_discarded':drdy.stale,'timeouts':drdy.timeouts,
            'timestamp_scope':'Samples use host read completion. Separate GPIO kernel edge timestamps and wake/read times are in gpio_edges.csv. No synthesized sample timestamps.',
            'missed_sample_scope':'Stale queued edges are discarded above 15 ms age. libgpiod v1 cannot count kernel queue overflow; edge interval gaps are diagnostic, not an exact lost-sample count.',
            'read_path':'Coherent 14-byte burst; differs from deployed polling separate reads.',
            'register_map_source':'https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6500-Register-Map2.pdf'}
    if args.mode == 'fifo-drdy' and drdy is not None:
        result['data_ready'].update(
            read_path='Audited 12-byte six-axis FIFO packets drained on DATA_RDY; exact bytes in gpio_edges.csv.',
            missed_sample_scope='Queued edges may drain zero or multiple packets. No edge-age discard. Kernel queue loss is not directly measurable.',
            packets_drained=sum(b[3] for b in fifo_batches),
            packets_pending_at_deadline=len(drdy.pending),
            timestamp_scope='Shared host drain-completion time per batch. Zero inter-packet host intervals are intentional; no physical sample jitter claim.')
    if len(ss):
        result['score_distributions']={name:{str(q):float(np.percentile(ss[:,i],q)) for q in [0,50,95,99,99.9,100]} for i,name in enumerate(['classifier','reconstruction'])}
        positives=ss[:,2].astype(bool)
        result['overlapping_three_positive_positions']=int(sum(positives[:-2]&positives[1:-1]&positives[2:]))
        result['classifier_crossings']=int(sum(ss[:,0]>thresholds[0]));result['reconstruction_crossings']=int(sum(ss[:,1]>thresholds[1]))
    if n:
        result['physical_axes']={a:{'mean':float(arr[:,i].mean()),'std':float(arr[:,i].std()),'min':float(arr[:,i].min()),'max':float(arr[:,i].max()),'rms':float(np.sqrt(np.mean(arr[:,i]**2)))} for i,a in enumerate(['ax','ay','az','gx','gy','gz'])}
        result['magnitudes']={name:{'mean':float(np.linalg.norm(arr[:,sl],axis=1).mean()),'max':float(np.linalg.norm(arr[:,sl],axis=1).max())} for name,sl in [('accel',slice(0,3)),('gyro',slice(3,6))]}
    status='COMPLETE (GUIDED; OPERATOR-ATTESTED)' if args.operator_phase else 'COMPLETE (UNATTENDED)'
    c.finish(args.ids.split(',') if args.ids else [],args.label,status if error is None and elapsed>=args.seconds else 'FAIL',result,out)
    if error is not None or elapsed < args.seconds:
        raise SystemExit(1)

if __name__=='__main__':main()
