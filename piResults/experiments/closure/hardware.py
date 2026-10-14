"""Read-only preflight; subsequent acquisition commands added after register audit."""
import argparse
import collections
import csv
import json
import signal
import struct
import time
from pathlib import Path
import campaign as c

REGS={'SMPLRT_DIV':0x19,'CONFIG':0x1a,'GYRO_CONFIG':0x1b,'ACCEL_CONFIG':0x1c,
      'ACCEL_CONFIG2':0x1d,'FIFO_EN':0x23,'INT_PIN_CFG':0x37,'INT_ENABLE':0x38,
      'INT_STATUS':0x3a,'USER_CTRL':0x6a,'PWR_MGMT_1':0x6b,'PWR_MGMT_2':0x6c,
      'FIFO_COUNT_H':0x72,'FIFO_COUNT_L':0x73,'WHO_AM_I':0x75}

def registers(bus):
    return {name:bus.read_byte_data(0x68,reg) for name,reg in REGS.items()}

def probe():
    import smbus2
    out=c.BASE/'metadata/hardware_preflight';out.mkdir(parents=True,exist_ok=True)
    meta=c.metadata();c.save(out/'metadata.json',meta)
    with smbus2.SMBus(1) as bus:
        ids=[]
        for i in range(100):
            ids.append({'index':i,'t_monotonic':time.monotonic(),'who_am_i':bus.read_byte_data(0x68,0x75)})
            time.sleep(.01)
        regs=registers(bus)
        samples=[]
        for _ in range(100):
            samples.append(struct.unpack('>7h',bytes(bus.read_i2c_block_data(0x68,0x3b,14))))
            time.sleep(.02)
    c.save(out/'identity_reads.json',ids);c.save(out/'raw_register_samples.json',samples)
    result={'identity_counts':dict(collections.Counter(hex(x['who_am_i']) for x in ids)),
            'registers_hex':{k:hex(v) for k,v in regs.items()},
            'i2cdetect':c.command(['i2cdetect','-y','1']),
            'limitation':'Single current boot only. NOT the three independent power cycles required by A1/H1. No sensor configuration changed.'}
    c.finish([], 'Hardware preflight, not A1 completion','OBSERVED',result,out)

def capture(args):
    import numpy as np
    import smbus2
    def interrupted(signum,frame):raise InterruptedError('Termination requested; restore registers and preserve partial evidence')
    signal.signal(signal.SIGTERM,interrupted)
    out=c.BASE/args.label
    out.mkdir(parents=True,exist_ok=False)
    c.save(out/'metadata.json',c.metadata())
    axes=['ax','ay','az','gx','gy','gz']
    bus=smbus2.SMBus(1);before=registers(bus);c.save(out/'registers_before.json',before)
    if before['WHO_AM_I'] != 0x70:
        raise RuntimeError('Register map not verified for this device identity')
    restore_names=['SMPLRT_DIV','CONFIG','GYRO_CONFIG','ACCEL_CONFIG','ACCEL_CONFIG2','FIFO_EN','USER_CTRL','INT_ENABLE']
    raw=[]; timestamps=[]; temperatures=[]; batchlog=[]; errors=0; overflows=0;exception=None
    scale=np.array([9.80665/(2048 if args.high_range else 16384)]*3+[1/(16.4 if args.high_range else 131)]*3)
    try:
        bus.write_byte_data(0x68,0x23,0)
        bus.write_byte_data(0x68,0x6a,0)
        if args.filtered:
            for reg,val in [(0x1a,4),(0x1b,0x18 if args.high_range else 0),(0x1c,0x18 if args.high_range else 0),(0x1d,4),(0x19,19)]:
                bus.write_byte_data(0x68,reg,val)
        elif args.high_range:
            raise ValueError('High range requires explicitly filtered condition')
        time.sleep(.2)
        if args.mode=='fifo':
            if not args.filtered: raise ValueError('FIFO requires verified 50 Hz filtered setup')
            bus.write_byte_data(0x68,0x6a,4);time.sleep(.01)
            bus.write_byte_data(0x68,0x6a,0x40)
            bus.write_byte_data(0x68,0x38,0x10)
            bus.write_byte_data(0x68,0x23,0x78)
        configured=registers(bus);c.save(out/'registers_during.json',configured)
        if args.filtered:
            expected={'CONFIG':4,'ACCEL_CONFIG2':4,'SMPLRT_DIV':19,
                      'GYRO_CONFIG':0x18 if args.high_range else 0,
                      'ACCEL_CONFIG':0x18 if args.high_range else 0}
            if any(configured[k]!=v for k,v in expected.items()):
                raise RuntimeError('Sensor configuration readback mismatch')
        start=time.monotonic();end=start+args.seconds;tick=start;progress=start+60
        with (out/'raw.csv').open('w',buffering=1) as f:
            writer=csv.writer(f);writer.writerow(['index','host_read_end_monotonic','batch_id',*[a+'_raw' for a in axes],*axes,'temperature_raw'])
            while time.monotonic()<end:
                try:
                    if args.mode=='fifo':
                        status=bus.read_byte_data(0x68,0x3a)
                        count=int.from_bytes(bytes(bus.read_i2c_block_data(0x68,0x72,2)),'big')
                        if status&0x10 or count>=504:
                            overflows+=1
                            raise RuntimeError(f'FIFO overflow/near-full: status={status:#x}, bytes={count}; abort, no ambiguous packets accepted')
                        nbytes=(count//12)*12; buf=bytearray()
                        for offset in range(0,nbytes,24):
                            buf.extend(bus.read_i2c_block_data(0x68,0x74,min(24,nbytes-offset)))
                        now=time.monotonic()
                        samples=list(struct.iter_unpack('>6h',buf));temperature=None
                        batchlog.append([now,count,status,len(samples)])
                    else:
                        # One coherent register burst; explicitly differs from deployed library's separate reads.
                        values=struct.unpack('>7h',bytes(bus.read_i2c_block_data(0x68,0x3b,14)))
                        samples=[values[:3]+values[4:]];temperature=values[3];temperatures.append(temperature);now=time.monotonic()
                    for s in samples:
                        v=np.asarray(s)*scale
                        writer.writerow([len(raw),now,len(batchlog)-1,*s,*v,temperature])
                        raw.append(s);timestamps.append(now)
                    if now>=progress:
                        f.flush(); print(f'{args.label}: {now-start:.0f}s, samples={len(raw)}, I2C errors={errors}, overflows={overflows}',flush=True);progress+=60
                    tick+=.005 if args.mode=='fifo' else .02
                    delay=tick-time.monotonic()
                    if delay>0: time.sleep(delay)
                    else:tick=time.monotonic()
                except OSError:
                    errors+=1
                    raise
        elapsed=time.monotonic()-start
    except Exception as e:
        exception=repr(e);elapsed=time.monotonic()-start if 'start' in locals() else 0
    finally:
        bus.write_byte_data(0x68,0x23,0);bus.write_byte_data(0x68,0x6a,4);time.sleep(.01)
        for name in restore_names:bus.write_byte_data(0x68,REGS[name],before[name])
        c.save(out/'registers_restored.json',registers(bus));bus.close()
    data=np.asarray(raw,dtype=float).reshape(-1,6);physical=data*scale
    def stats(x):
        return {'mean':float(x.mean()),'std':float(x.std()),'rms':float(np.sqrt(np.mean(x*x))),
                'min':float(x.min()),'max':float(x.max()),'p1':float(np.percentile(x,1)),
                'p50':float(np.median(x)),'p99':float(np.percentile(x,99))} if len(x) else {}
    result={'mode':args.mode,'seconds_requested':args.seconds,'elapsed_s':elapsed,'samples':len(raw),
            'achieved_samples_per_s':len(raw)/elapsed if elapsed else None,'filtered':args.filtered,
            'high_range':args.high_range,'i2c_errors':errors,'overflows':overflows,'exception':exception,
            'raw':{a:{**stats(data[:,i]),'negative_rail':int(sum(data[:,i]==-32768)),'positive_rail':int(sum(data[:,i]==32767))} for i,a in enumerate(axes)},
            'physical':{a:stats(physical[:,i]) for i,a in enumerate(axes)},
            'accel_magnitude':stats(np.linalg.norm(physical[:,:3],axis=1)),
            'gyro_magnitude':stats(np.linalg.norm(physical[:,3:],axis=1)),
            'quantization_step':{a:float(scale[i]) for i,a in enumerate(axes)},
            'temperature_raw':stats(np.asarray(temperatures,dtype=float)),
            'temperature_c_map_estimate':stats(np.asarray(temperatures,dtype=float)/333.87+21),
            'temperature_note':'Raw signed counts preserved. Celsius estimate uses compatible MPU6500 map: raw/333.87+21; untrimmed internal sensor, not calibrated ambient temperature. Temperature is not enabled in the six-axis FIFO packets.',
            'temperature_source':'TDK MPU6500 product specification section 3.3.2: https://product.tdk.com/system/files/dam/doc/product/sensor/mortion-inertial/imu/data_sheet/mpu-6500-datasheet2.pdf',
            'decoded_configuration':{'AFS_SEL':(configured['ACCEL_CONFIG']>>3)&3,
                'FS_SEL':(configured['GYRO_CONFIG']>>3)&3,'DLPF_CFG':configured['CONFIG']&7,
                'FCHOICE_B':configured['GYRO_CONFIG']&3,'A_DLPF_CFG':configured['ACCEL_CONFIG2']&7,
                'SMPLRT_DIV':configured['SMPLRT_DIV'],'nominal_output_rate_hz':50 if args.filtered else None,
                'host_target_rate_hz':50 if args.mode=='polling' else 200,
                'rate_note':'50 Hz is the configured nominal ODR, not an independent measurement of silicon timing. FIFO observed output rate and host polling throughput are reported separately.'},
            'host_interval_ms':stats(np.diff(timestamps)*1000),
            'fifo_packet_bytes':12 if args.mode=='fifo' else None,
            'fifo_sample_bytes_read':12*len(raw) if args.mode=='fifo' else None,
            'timestamp_note':'Host read completion times, not physical sample timestamps. FIFO batch samples share host time; never interpret those intervals as sensor dt.',
            'conditions':'Unattended; no physical mounting/stationarity confirmation from user. No inference, GPIO, or SMS.',
            'configuration_note':'Filtered 50-Hz ODR changes CONFIG/ACCEL_CONFIG2/SMPLRT_DIV from deployment. Polling equivalence must use these SAME settings.'}
    c.save(out/'fifo_batches.json',batchlog)
    baseline_path=c.BASE/'04_polling_fifo_equivalence/polling/summary.json'
    if args.high_range and baseline_path.exists():
        baseline=json.loads(baseline_path.read_text())
        result['low_range_comparison']={
            'baseline_file':str(baseline_path.relative_to(c.ROOT)),
            'baseline_sha256':c.sha(baseline_path),
            'configuration':'Sequential coherent-burst polling captures with identical corrected filter/divider settings; low range +/-2g, +/-250deg/s versus high range +/-16g, +/-2000deg/s.',
            'axes':{a:{'high_minus_low_mean':result['physical'][a]['mean']-baseline['physical'][a]['mean'],
                       'high_over_low_std':result['physical'][a]['std']/baseline['physical'][a]['std'] if baseline['physical'][a]['std'] else None,
                       'low_range_physical':baseline['physical'][a]} for a in axes} if len(raw) else {},
            'limitation':'Sequential unattended placement, not confirmed identical motion/temperature. Low-range baseline did not preserve temperature; no temperature-matched noise attribution.'}
    sane=bool(len(raw) and 8<result['accel_magnitude']['mean']<12 and result['gyro_magnitude']['mean']<10 and not np.any((data==-32768)|(data==32767)))
    result['stationary_physical_plausibility_gate']=sane
    complete=exception is None and elapsed>=args.seconds and errors==0 and overflows==0
    status='PASS (UNATTENDED PHYSICAL CONDITIONS)' if complete and sane else 'FAIL'
    c.finish(args.ids.split(',') if args.ids else [],args.label,status,result,out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['probe','capture'])
    p.add_argument('--mode',choices=['polling','fifo'],default='polling')
    p.add_argument('--filtered',action='store_true');p.add_argument('--high-range',action='store_true')
    p.add_argument('--seconds',type=float,default=600);p.add_argument('--label');p.add_argument('--ids',default='')
    args=p.parse_args()
    if args.action=='probe':probe()
    else:capture(args)
