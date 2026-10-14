"""Temporary MPU6500 IIO binding and buffered capture; restores direct-I2C state.

Driver-provided timestamps may be reconstructed from IRQ/ODR by the kernel.
They must not be described as independently measured physical sample times.
"""
import argparse
import csv
import json
import logging
import math
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import time

import numpy as np
import psutil
import smbus2
import campaign as c
import crash_monitor as cm
from hardware import registers, REGS
from stream_analysis import stats

FIELDS=['SMPLRT_DIV','CONFIG','GYRO_CONFIG','ACCEL_CONFIG','ACCEL_CONFIG2','USER_CTRL','FIFO_EN','INT_PIN_CFG','INT_ENABLE','PWR_MGMT_1','PWR_MGMT_2']
AXES=['in_accel_x','in_accel_y','in_accel_z','in_anglvel_x','in_anglvel_y','in_anglvel_z']


def layout(channels):
    result=[];offset=0;alignment=1
    for name,index,kind in sorted(channels,key=lambda v:v[1]):
        match=re.fullmatch(r'(le|be):([su])(\d+)/(\d+)>>(\d+)',kind)
        if not match:raise ValueError('Unsupported scan type: '+kind)
        endian,signed,bits,storage,shift=match.groups()
        bits,storage,shift=map(int,(bits,storage,shift))
        if storage%8 or bits+shift>storage:raise ValueError('Unsupported bit layout')
        size=storage//8;offset=(offset+size-1)//size*size;alignment=max(alignment,size)
        result.append({'name':name,'index':index,'endian':endian,'signed':signed=='s','bits':bits,'size':size,'shift':shift,'offset':offset})
        offset+=size
    return result,(offset+alignment-1)//alignment*alignment


def decode(buf,spec):
    values={}
    for ch in spec:
        value=int.from_bytes(buf[ch['offset']:ch['offset']+ch['size']], 'little' if ch['endian']=='le' else 'big')
        value=(value>>ch['shift'])&((1<<ch['bits'])-1)
        if ch['signed'] and value&(1<<(ch['bits']-1)):value-=1<<ch['bits']
        values[ch['name']]=value
    return values


def main():
    p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,required=True);p.add_argument('--label',required=True);a=p.parse_args()
    if os.geteuid()!=0:raise RuntimeError('Temporary kernel binding requires root')
    for unit in ['helmx-crash-monitor.service','helmx-research-boot-capture.service']:
        if c.command(['systemctl','is-active',unit]).get('stdout','').strip()!='inactive':raise RuntimeError('Competing service: '+unit)
    if c.command(['fuser','/dev/i2c-1']).get('returncode')!=1:raise RuntimeError('I2C bus is in use')
    if Path('/sys/bus/i2c/devices/1-0068').exists():raise RuntimeError('Existing kernel device; will not replace it')
    out=c.BASE/a.label;out.mkdir(parents=True,exist_ok=False)
    c.save(out/'metadata.json',c.metadata())
    cfg=cm.load_config(c.BASE/'frozen/deploy/config.yaml');c.save(out/'configuration.json',cfg)
    initial=json.loads((c.BASE/'hashes/initial_artifacts.json').read_text())
    if not all(c.sha(c.ROOT/k)==v for k,v in initial.items()):raise RuntimeError('Frozen artifacts changed')
    scorer=cm.WindowScorer(cfg,cm.CrashModel(c.BASE/'frozen/models/helmx_crash_model_int8.tflite',c.BASE/'frozen/models/normalizer.npz'),cm.CausalGravityFilter(.3,50))
    guard=cm.SampleStreamGuard(cfg['sensor']['timing_guard'],.02,logging.getLogger('iio'))
    policy=cm.TriggerPolicy(*cm.load_model_thresholds(cfg),3,60)
    with smbus2.SMBus(1) as bus:before=registers(bus)
    c.save(out/'registers_before.json',before)
    if before['WHO_AM_I']!=112:raise RuntimeError('Requires audited 0x70 MPU6500-compatible device')
    prep=c.BASE/'iio_preparation_20261007';overlay='helmx-mpu6500'
    subprocess.run(['dtc','-@','-I','dts','-O','dtb','-o',str(prep/(overlay+'.dtbo')),str(prep/(overlay+'.dts'))],check=True)
    bound=False;dev=None;fd=None;error=None;cleanup=[];n=0;windows=0;gaps=0;runs=[];run=0;events=0;positives=0;resources=[];processing=[];scores=[]
    def interrupt(signum,frame):raise InterruptedError('Capture interrupted')
    signal.signal(signal.SIGTERM,interrupt)
    proc=psutil.Process();proc.cpu_percent();start=None
    try:
        subprocess.run(['modprobe','inv_mpu6050_i2c'],check=True)
        subprocess.run(['dtoverlay','-d',str(prep),overlay],check=True);bound=True
        for _ in range(50):
            devices=[x for x in Path('/sys/bus/iio/devices').glob('iio:device*') if (x/'name').exists() and (x/'name').read_text().strip()=='mpu6500']
            if devices:break
            time.sleep(.1)
        if len(devices)!=1:raise RuntimeError('Expected exactly one MPU6500 IIO device')
        dev=devices[0]
        def write(name,value):(dev/name).write_text(str(value))
        write('buffer/enable',0)
        for field in (dev/'scan_elements').glob('*_en'):field.write_text('0')
        write('sampling_frequency',50)
        for name in AXES+['in_timestamp']:write('scan_elements/'+name+'_en',1)
        for kind in ['accel','anglvel']:
            choices=(dev/f'in_{kind}_scale_available').read_text().split()
            write(f'in_{kind}_scale',choices[0])
        triggers=[x for x in Path('/sys/bus/iio/devices').glob('trigger*') if (x/'name').exists() and 'mpu6500' in (x/'name').read_text()]
        if (dev/'trigger/current_trigger').exists() and triggers:write('trigger/current_trigger',(triggers[0]/'name').read_text().strip())
        if (dev/'current_timestamp_clock').exists():write('current_timestamp_clock','monotonic')
        channels=[(name,int((dev/'scan_elements'/f'{name}_index').read_text()),(dev/'scan_elements'/f'{name}_type').read_text().strip()) for name in AXES+['in_timestamp']]
        spec,record_size=layout(channels)
        accel=float((dev/'in_accel_scale').read_text());gyro=float((dev/'in_anglvel_scale').read_text())*180/math.pi
        attrs={str(x.relative_to(dev)):x.read_text().strip() for x in dev.glob('*') if x.name in ['name','sampling_frequency','in_accel_scale','in_anglvel_scale','current_timestamp_clock']}
        c.save(out/'iio_configuration.json',{'device':str(dev),'attrs':attrs,'channels':channels,'layout':spec,'record_bytes':record_size,'accel_scale':accel,'gyro_scale_dps':gyro,'source':'Raspberry Pi Linux rpi-6.12.y inv_mpu6050 driver','timestamp_scope':'Kernel driver timestamps; may reconstruct FIFO sample times from IRQ and ODR, not physical timestamp ground truth.'})
        write('buffer/length',256)
        if (dev/'buffer/watermark').exists():write('buffer/watermark',1)
        fd=os.open('/dev/'+dev.name,os.O_RDONLY|os.O_NONBLOCK)
        write('buffer/enable',1)
        start=time.monotonic();deadline=start+a.seconds;progress=start+60;resource_tick=start;pending=b''
        with (out/'iio_buffer.bin').open('wb') as binary,(out/'raw_sensor.csv').open('w',buffering=1) as rf,(out/'window_scores.csv').open('w',buffering=1) as wf:
            rw=csv.writer(rf);sw=csv.writer(wf)
            rw.writerow(['sample_idx','t_monotonic','dt_ms','ax_ms2','ay_ms2','az_ms2','gx_dps','gy_dps','gz_dps','sensor_read_ms','host_read_end_monotonic'])
            sw.writerow(['window_idx','sample_idx','t_monotonic','crash_prob','recon_error','or_positive','confirmed_triggered','anomaly_streak','processing_ms'])
            while time.monotonic()<deadline:
                if not select.select([fd],[],[],1)[0]:raise RuntimeError('No IIO buffer data for one second')
                t0=time.monotonic();chunk=os.read(fd,record_size*256);host=time.monotonic()
                if not chunk:raise RuntimeError('IIO buffer returned EOF')
                binary.write(chunk);pending+=chunk
                while len(pending)>=record_size:
                    vals=decode(pending[:record_size],spec);pending=pending[record_size:]
                    now=vals['in_timestamp']/1e9
                    sample=[vals[name]*(accel if i<3 else gyro) for i,name in enumerate(AXES)]
                    gap,dt=guard.observe(now)
                    if gap:
                        gaps+=1;runs.append(run);run=0;scorer.clear()
                        if dt>=guard.long_gap_reset_s:scorer.gravity_filter.reset()
                    run+=1;pre=scorer.append(sample)
                    rw.writerow([n,now,'' if dt is None else dt*1000,*sample,(host-t0)*1000,host]);n+=1
                    v=scorer.try_score()
                    if v is not None:
                        t=time.monotonic();positive,event=policy.update(v['crash_prob'],v['recon_error'],now=t)
                        total=pre+v['total_ms'];processing.append(total);events+=int(event);positives+=int(positive);scores.append([v['crash_prob'],v['recon_error']])
                        sw.writerow([windows,n-1,t,v['crash_prob'],v['recon_error'],positive,event,policy.anomaly_streak,total]);windows+=1
                if host>=resource_tick:
                    resources.append({'t_monotonic':host,'cpu_pct':proc.cpu_percent(),'rss_bytes':proc.memory_info().rss,'cpu_temp_c':float(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000});resource_tick=host+1
                if host>=progress:print(a.label,'seconds',round(host-start),'samples',n,'windows',windows,'gaps',gaps,flush=True);progress+=60
            if pending:raise RuntimeError('Partial IIO record at end')
    except Exception as e:error=repr(e)
    finally:
        elapsed=time.monotonic()-start if start else 0
        if dev is not None:
            try:(dev/'buffer/enable').write_text('0')
            except Exception as e:cleanup.append(repr(e))
        if fd is not None:os.close(fd)
        if bound:
            r=subprocess.run(['dtoverlay','-r',overlay],capture_output=True,text=True)
            if r.returncode:cleanup.append('Overlay removal failed: '+r.stderr)
        if not Path('/sys/bus/i2c/devices/1-0068').exists():
            try:
                with smbus2.SMBus(1) as bus:
                    for reg,value in [(0x38,0),(0x23,0),(0x6a,0)]:bus.write_byte_data(0x68,reg,value)
                    for name in FIELDS:bus.write_byte_data(0x68,REGS[name],before[name])
                    c.save(out/'registers_restored.json',registers(bus))
            except Exception as e:cleanup.append(repr(e))
        else:cleanup.append('Kernel still owns device; refused direct I2C restoration')
    runs.append(run);c.save(out/'resources.json',resources)
    result={'mode':'iio','seconds_requested':a.seconds,'elapsed_s':elapsed,'n_samples':n,'n_windows':windows,'exception':error,'cleanup_errors':cleanup,
            'sample_rate_hz':n/elapsed if elapsed else None,'gap_count':gaps,'i2c_failures':None,'i2c_failure_scope':'Kernel I2C failures are not counted by userspace; do not interpret null as zero.',
            'confirmed_alert_events':events,'or_positive_windows':positives,'C_D':windows/max(1,1+(n-60)//15),'V_T_scored_over_scored_plus_resets':windows/max(1,windows+gaps),
            'p_valid_90_sample_position':sum(max(0,x-89) for x in runs)/max(1,n-89),
            'processing_ms':{str(q):float(np.percentile(processing,q)) for q in [50,95,99,100]} if processing else {},
            'timestamp_scope':'Kernel FIFO timestamp reconstruction, not physical clock measurement. Host availability time is separately preserved.',
            'conditions':'Operator confirmed untouched on GPIO23 before test; desktop/agent active. No alarm/SMS.',
            'throttled_end':c.command(['vcgencmd','get_throttled'])}
    if n:
        import pandas as pd
        raw=pd.read_csv(out/'raw_sensor.csv',float_precision='round_trip')
        result['timing']=stats(np.diff(raw.t_monotonic))
        result['host_availability_timing']=stats(np.diff(raw.host_read_end_monotonic))
        result['physical_axes']={name:{'mean':float(raw[col].mean()),'std':float(raw[col].std(ddof=0)),'min':float(raw[col].min()),'max':float(raw[col].max())} for name,col in zip(['ax','ay','az','gx','gy','gz'],['ax_ms2','ay_ms2','az_ms2','gx_dps','gy_dps','gz_dps'])}
    if scores:result['score_distributions']={name:{str(q):float(np.percentile(np.array(scores)[:,i],q)) for q in [0,50,95,99,100]} for i,name in enumerate(['classifier','reconstruction'])}
    ok=error is None and not cleanup and elapsed>=a.seconds
    c.finish([],a.label,'CAPTURED; OFFLINE REVIEW PENDING' if ok else 'FAIL',result,out)
    if not ok:raise SystemExit(1)

if __name__=='__main__':main()
