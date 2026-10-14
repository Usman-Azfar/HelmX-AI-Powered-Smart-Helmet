"""Real GPIO calls and controlled recorded-trace injection; never sends SMS."""
import argparse
import dataclasses
import json
import logging
import signal
import time
import numpy as np
import campaign as c
import crash_monitor as cm
from model_analysis import CACHE

def alarm(out):
    log=logging.getLogger('gpio_test');log.setLevel(logging.INFO);log.addHandler(logging.FileHandler(out/'gpio.log'))
    obj=cm.LocalAlarm(18,log)
    if obj.device is None:raise RuntimeError('Real GPIO unavailable; log-only fallback is NOT a successful GPIO test')
    return obj,log

def pulses():
    out=c.BASE/'gpio_O1';out.mkdir(exist_ok=False);c.save(out/'metadata.json',c.metadata());obj,log=alarm(out);rows=[]
    try:
        for i in range(50):
            request=time.monotonic();before=time.monotonic();obj.device.on();after=time.monotonic()
            time.sleep(.05);off_before=time.monotonic();obj.device.off();off_after=time.monotonic()
            rows.append({'trial':i,'requested':request,'gpio_on_call_start':before,'gpio_on_call_return':after,'gpio_off_call_start':off_before,'gpio_off_call_return':off_after,'configured_high_s':.05})
            time.sleep(.05)
    finally:obj.stop();obj.device.close()
    c.save(out/'pulse_timestamps.json',rows)
    duration=[r['gpio_off_call_start']-r['gpio_on_call_return'] for r in rows]
    result={'trials':len(rows),'software_call_high_interval_s':{str(p):float(np.percentile(duration,p)) for p in [50,95,100]},
            'limitation':'Actual GPIO API used on BCM18, with timestamps surrounding calls. No oscilloscope/loopback: electrical edge timing and physical alarm perception are unmeasured.'}
    c.finish(['O1'],'GPIO actuation repeatability','COMPLETE (SOFTWARE TIMING)',result,out)

class RecordedAlarm:
    def __init__(self,wrapped):self.wrapped=wrapped;self.on_start=None;self.on_return=None;self.off_start=None;self.off_return=None
    def start(self):
        self.on_start=time.monotonic();self.wrapped.start();self.on_return=time.monotonic()
    def stop(self):
        self.off_start=time.monotonic();self.wrapped.stop();self.off_return=time.monotonic()

class ControlledCancel:
    def __init__(self,alarm):self.alarm=alarm;self.accepted_at=None
    def check_and_clear(self):
        now=time.monotonic()
        accepted=self.alarm.on_return is not None and now-self.alarm.on_return>=1.
        if accepted:self.accepted_at=now
        return accepted

class NoModem:
    def get_gps_coordinates(self,*args):raise RuntimeError('Unexpected GPS path: controlled cancel must prevent dispatch')
    def send_sms(self,*args):raise RuntimeError('SMS forbidden in this test')

def traces():
    out=c.BASE/'gpio_G_O2';out.mkdir(exist_ok=False);c.save(out/'metadata.json',c.metadata());obj,log=alarm(out)
    cfg=cm.load_config(c.BASE/'frozen/deploy/config.yaml');raw=np.load(CACHE/'raw_test_sessions.npz')
    cached=json.loads((c.BASE/'model_L1/summary.json').read_text())['transformed_events']
    model=cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz');th=cm.load_model_thresholds(cfg)
    reports=[]
    try:
        for sid in raw.files:
            values=raw[sid];ev=cached[sid]['trigger_indices']
            # For an expected trigger retain six seconds of pre-trigger history.
            # Normal/non-trigger controls use the first six seconds.
            end=(59+15*ev[0]+31) if ev else min(len(values),300)
            start=max(0,end-360);end=min(len(values),end);trace=values[start:end]
            scorer=cm.WindowScorer(cfg,model,cm.CausalGravityFilter(.3,50));policy=cm.TriggerPolicy(*th,3,60)
            onset=time.monotonic();dec=[];streak=[];confirm=None;ar=RecordedAlarm(obj);outcome=None
            cancellation_start=None;cancellation_end=None;cancel=ControlledCancel(ar)
            for i,v in enumerate(trace):
                delay=onset+i*.02-time.monotonic()
                if delay>0:time.sleep(delay)
                scorer.append(v);r=scorer.try_score()
                if r is None:continue
                now=time.monotonic();positive,fired=policy.update(r['crash_prob'],r['recon_error'],now=now)
                streak=streak+[now] if positive else []
                dec.append({'sample_index':i,'absolute_source_sample':start+i,'t_monotonic':now,'crash_prob':r['crash_prob'],'recon_error':r['recon_error'],'positive':positive,'triggered':fired})
                if fired:
                    confirm=now
                    cancellation_start=time.monotonic()
                    outcome=dataclasses.asdict(cm.handle_suspected_crash(ar,cancel,NoModem(),cfg,log))
                    cancellation_end=time.monotonic()
                    if not outcome['cancelled'] or outcome['sms_attempted']:
                        raise RuntimeError('Controlled cancellation did not prevent dispatch')
                    break
            row={'session':sid,'source_samples':[start,end],'injected_samples':i+1,'onset':onset,'confirmation':confirm,
                 'first_anomaly':next((r['t_monotonic'] for r in dec if r['positive']),None),
                 'confirmation_triplet_times':streak[-3:] if confirm else [],'gpio_on_call_start':ar.on_start,'gpio_on_call_return':ar.on_return,
                 'gpio_off_call_start':ar.off_start,'gpio_off_call_return':ar.off_return,'cancel_outcome':outcome,'decisions':dec,
                 'cancellation_handler_start':cancellation_start,'cancellation_accepted':cancel.accepted_at,'cancellation_handler_end':cancellation_end,
                 'outcome':'triggered and controlled-cancelled' if confirm else 'no trigger within injected segment'}
            c.save(out/(str(len(reports))+'_trace.json'),row);reports.append(row)
    finally:obj.stop();obj.device.close()
    lat={}
    for name,begin,endkey in [('onset_to_first_anomaly','onset','first_anomaly'),('onset_to_confirmation','onset','confirmation'),('onset_to_gpio_call','onset','gpio_on_call_start'),('first_anomaly_to_confirmation','first_anomaly','confirmation'),('confirmation_to_gpio_call','confirmation','gpio_on_call_start')]:
        vals=[r[endkey]-r[begin] for r in reports if r[begin] is not None and r[endkey] is not None]
        lat[name]={'n':len(vals),**{str(p):float(np.percentile(vals,p)) for p in [50,95,100]}} if vals else {'n':0}
    c.finish(['G','O2'],'Controlled injected-trace onset-to-local-alert timing','COMPLETE (CONTROLLED TRACE SEGMENTS)',
             {'trials':len(reports),'unique_sessions':len(set(r['session'] for r in reports)),'triggered':sum(r['confirmation'] is not None for r in reports),
              'latencies_s':lat,'trace_summary':[{k:v for k,v in r.items() if k!='decisions'} for r in reports],
              'selection':'One segment per held-out session; trigger-bearing segments selected around prior composed-replay trigger position. Controls use first six seconds. Filter starts fresh per segment; this is not a blind sensitivity experiment.',
              'limitations':'Software GPIO-call timestamps, not measured electrical edges. Synthetic 50-Hz pacing, no live IMU acquisition. Triggered trials execute actual cancellation handler with a controlled software cancellation after one second; no voice-recognition or GPS/GSM validation. Injection onset is NOT physical crash onset.'},out)

if __name__=='__main__':
    def stop(signum,frame):raise InterruptedError('Termination requested; deassert GPIO before exit')
    signal.signal(signal.SIGTERM,stop)
    p=argparse.ArgumentParser();p.add_argument('experiment',choices=['O1','G']);a=p.parse_args()
    if a.experiment=='O1':pulses()
    else:traces()
