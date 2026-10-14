"""One-shot future-boot cold/warm raw recording, with minimal startup imports.

No model import before cold capture. Does not shut down or reboot the Pi.
A nonzero startup delay is measured and never represented as time-zero coverage.
"""
import argparse
import csv
import datetime
import fcntl
import json
from pathlib import Path
import signal
import struct
import subprocess
import time

BASE=Path(__file__).resolve().parents[1]
STATE=BASE/'metadata/cold_warm_arm.json'
REGS={'SMPLRT_DIV':0x19,'CONFIG':0x1a,'GYRO_CONFIG':0x1b,'ACCEL_CONFIG':0x1c,'ACCEL_CONFIG2':0x1d,'FIFO_EN':0x23,'INT_PIN_CFG':0x37,'INT_ENABLE':0x38,'USER_CTRL':0x6a,'PWR_MGMT_1':0x6b,'PWR_MGMT_2':0x6c}

def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def boot():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def uptime():return float(Path('/proc/uptime').read_text().split()[0])

def capture(folder,seconds):
    import smbus2
    folder.mkdir()
    bus=smbus2.SMBus(1);before={k:bus.read_byte_data(0x68,v) for k,v in REGS.items()}
    save(folder/'registers_before.json',before)
    start=None;count=0;first=None;last=None;error=None;cleanup=None
    try:
        identity=bus.read_byte_data(0x68,0x75)
        if identity!=112:raise RuntimeError('Requires audited identity 0x70')
        for reg,value in [(0x38,0),(0x23,0),(0x6a,0),(0x6b,0),(0x6c,0),(0x1a,4),(0x1b,0),(0x1c,0),(0x1d,4),(0x19,19)]:bus.write_byte_data(0x68,reg,value)
        during={k:bus.read_byte_data(0x68,v) for k,v in REGS.items()};save(folder/'registers_during.json',during)
        if any(during[k]!=v for k,v in {'CONFIG':4,'ACCEL_CONFIG2':4,'GYRO_CONFIG':0,'ACCEL_CONFIG':0,'SMPLRT_DIV':19}.items()):raise RuntimeError('Readback mismatch')
        start=time.monotonic();tick=start
        with (folder/'raw.csv').open('w',buffering=1) as f:
            w=csv.writer(f);w.writerow(['sample_idx','t_monotonic','ax_raw','ay_raw','az_raw','temperature_raw','gx_raw','gy_raw','gz_raw'])
            while time.monotonic()-start<seconds:
                vals=struct.unpack('>7h',bytes(bus.read_i2c_block_data(0x68,0x3b,14)));now=time.monotonic()
                if first is None:first=now
                last=now;w.writerow([count,now,*vals]);count+=1;tick+=.02
                delay=tick-time.monotonic()
                if delay>0:time.sleep(delay)
                else:tick=time.monotonic()
    except BaseException as e:error=repr(e)
    finally:
        elapsed=time.monotonic()-start if start else 0
        try:
            for k,v in before.items():bus.write_byte_data(0x68,REGS[k],v)
            after={k:bus.read_byte_data(0x68,v) for k,v in REGS.items()};save(folder/'registers_restored.json',after)
            if after!=before:raise RuntimeError('Register restoration mismatch')
        except BaseException as e:cleanup=repr(e)
        bus.close()
    result={'samples':count,'elapsed_s':elapsed,'seconds_requested':seconds,'first_sample_uptime_s':first,'last_sample_uptime_s':last,'exception':error,'cleanup_error':cleanup,
            'scope':'Matched filtered coherent-burst polling at nominal 50 Hz. No inference during acquisition. Offline score comparison required.'}
    save(folder/'summary.json',result)
    with (BASE.parent/'last_results.txt').open('a') as f:f.write('\nCold/warm raw capture '+str(folder.relative_to(BASE))+'\n'+json.dumps(result,indent=2)+'\n')
    if error or cleanup or elapsed<seconds:raise RuntimeError('Capture failed: '+repr(result))
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['arm','run','status']);a=p.parse_args()
    if a.action=='status':print(STATE.read_text() if STATE.exists() else 'Not armed');return
    if a.action=='arm':
        old=json.loads(STATE.read_text()) if STATE.exists() else {}
        if old.get('armed'):raise RuntimeError('Already armed; do not replace')
        state={'armed':True,'armed_boot_id':boot(),'prepared_date_pkt':'2026-10-07','cold_seconds':600,'warm_minimum_uptime_s':3600,'warm_seconds':600,
            'physical_condition':'Operator must fully remove Pi and IMU power >=10 seconds, preserve orientation, and leave untouched for at least 72 minutes after power-on. Attestation afterward.',
            'coverage_limit':'Earliest available userspace sample is later than boot. Missing startup interval stays explicit; literal first-ten-minute coverage cannot be claimed.'}
        save(STATE,state);print(json.dumps(state,indent=2));return
    lock=(BASE/'metadata/cold_warm.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=json.loads(STATE.read_text()) if STATE.exists() else {}
    if not state.get('armed') or state['armed_boot_id']==boot():print('Not armed for this boot');return
    state.update(armed=False,started_boot_id=boot(),started_uptime_s=uptime());save(STATE,state)
    def interrupt(signum,frame):raise InterruptedError('Capture interrupted')
    signal.signal(signal.SIGTERM,interrupt)
    out=BASE/('cold_warm_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir()
    save(out/'plan.json',state)
    result={'status':'STARTED','boot_id':boot(),'cold':None,'warm':None}
    try:
        for unit in ['helmx-crash-monitor.service','helmx-research-boot-capture.service']:
            r=subprocess.run(['systemctl','is-active',unit],capture_output=True,text=True)
            if r.stdout.strip() not in ['inactive','unknown']:raise RuntimeError('Competing service: '+unit)
        r=subprocess.run(['fuser','/dev/i2c-1'],capture_output=True,text=True)
        if r.returncode!=1:raise RuntimeError('I2C not confirmed free')
        result['cold']=capture(out/'cold',600);save(out/'summary.json',result)
        while uptime()<3600:time.sleep(min(30,3600-uptime()))
        if boot()!=result['boot_id']:raise RuntimeError('Boot changed')
        r=subprocess.run(['fuser','/dev/i2c-1'],capture_output=True,text=True)
        if r.returncode!=1:raise RuntimeError('I2C not free for warm capture')
        result['warm']=capture(out/'warm',600)
        result.update(status='CAPTURED; OFFLINE ANALYSIS AND OPERATOR ATTESTATION PENDING',missing_startup_seconds=min(600,result['cold']['first_sample_uptime_s']))
    except BaseException as e:result.update(status='FAILED',error=repr(e));raise
    finally:save(out/'summary.json',result)

if __name__=='__main__':main()
