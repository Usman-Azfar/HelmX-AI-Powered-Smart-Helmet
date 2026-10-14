"""Capture a USER-performed power cycle; never reboots the Pi itself."""
import argparse
import collections
import time
import json
import csv
from pathlib import Path
import smbus2
import campaign as c
from hardware import registers

def main():
    p=argparse.ArgumentParser();p.add_argument('--boot',type=int,choices=[1,2,3,4],required=True)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--user-reported-power-off-seconds',type=float)
    mode.add_argument('--await-power-attestation',action='store_true')
    p.add_argument('--attest-existing',action='store_true');a=p.parse_args()
    if a.user_reported_power_off_seconds is not None and a.user_reported_power_off_seconds<10:
        raise ValueError('Protocol needs at least 10 seconds fully powered off')
    out=c.BASE/'01_identity_three_boots'/f'boot{a.boot}'
    if a.attest_existing:
        if a.user_reported_power_off_seconds is None:
            raise ValueError('Attestation requires the actual reported power-off interval')
        result=json.loads((out/'summary.json').read_text())
        if result.get('user_reported_power_off_seconds') is not None:
            raise RuntimeError('Already attested; preserve the previous statement')
        result['user_reported_power_off_seconds']=a.user_reported_power_off_seconds
        result['attestation_utc']=c.metadata()['utc']
        result['limitation']='Power removal is user-attested after automatic capture. OS boot ID was recorded independently.'
        record(out,a.boot,result)
        return
    meta=c.metadata()
    for old in (c.BASE/'01_identity_three_boots').glob('boot*/metadata.json'):
        if json.loads(old.read_text())['boot_id']==meta['boot_id']:raise RuntimeError('This OS boot has already been captured; do not count it as a new power cycle')
    out.mkdir(parents=True,exist_ok=False)
    c.save(out/'metadata.json',meta)
    with smbus2.SMBus(1) as bus:
        ids=[]
        for i in range(100):ids.append({'index':i,'t_monotonic':time.monotonic(),'value':bus.read_byte_data(0x68,0x75)});time.sleep(.01)
        regs=registers(bus)
    c.save(out/'identity_reads.json',ids)
    baud={'hz':None,'source':'not available'}
    alias=Path('/proc/device-tree/aliases/i2c1')
    if alias.exists():
        node=alias.read_bytes().rstrip(b'\0').decode()
        clock=Path('/proc/device-tree')/node.lstrip('/')/'clock-frequency'
        if clock.exists():baud={'hz':int.from_bytes(clock.read_bytes(),'big'),'source':str(clock)}
    decoded={'accel_full_scale_g':[2,4,8,16][(regs['ACCEL_CONFIG']>>3)&3],
             'gyro_full_scale_deg_s':[250,500,1000,2000][(regs['GYRO_CONFIG']>>3)&3],
             'DLPF_CFG':regs['CONFIG']&7,'A_DLPF_CFG':regs['ACCEL_CONFIG2']&7,
             'SMPLRT_DIV':regs['SMPLRT_DIV'],'FIFO_EN':regs['FIFO_EN'],
             'FIFO_enabled':bool(regs['USER_CTRL']&0x40),'DATA_RDY_enabled':bool(regs['INT_ENABLE']&1)}
    result={'boot':a.boot,'boot_id':meta['boot_id'],'identity_counts':dict(collections.Counter(hex(r['value']) for r in ids)),
            'i2c_bus':1,'i2c_address_hex':'0x68','configured_i2c_baud':baud,'decoded_configuration':decoded,
            'os_kernel':meta['platform'],'script_sha256':c.sha(Path(__file__)),
            'registers':regs,'i2cdetect':c.command(['i2cdetect','-y','1']),'user_reported_power_off_seconds':a.user_reported_power_off_seconds,
            'limitation':'Cold power removal is user-attested; distinct OS boot ID is independently recorded. Script does not infer a power cycle from a service restart.'}
    record(out,a.boot,result)

def record(out,boot,result):
    if result['user_reported_power_off_seconds'] is None:
        result['limitation']='Automatic startup capture. Power removal has NOT yet been attested; this is not yet an accepted physical power-cycle trial.'
    status=('OBSERVED; POWER REMOVAL NOT YET ATTESTED' if result['user_reported_power_off_seconds'] is None
            else 'OBSERVED; THREE-BOOT SERIES IN PROGRESS')
    c.finish([],f'A1 boot {boot} capture',status,result,out)
    (out.parent/f'identity_boot{boot}.txt').write_text((out/'README.txt').read_text())
    completed=list((c.BASE/'01_identity_three_boots').glob('boot*/summary.json'))
    summaries=[json.loads(x.read_text()) for x in sorted(completed)]
    rows=[{'boot':x['boot'],'boot_id':x['boot_id'],'identity_counts':json.dumps(x['identity_counts']),
           'i2c_bus':x['i2c_bus'],'address':x['i2c_address_hex'],'configured_i2c_baud':x['configured_i2c_baud']['hz'],
           'user_reported_power_off_seconds':x['user_reported_power_off_seconds'],
           **x['decoded_configuration'],'registers':json.dumps(x['registers'])} for x in summaries]
    with (out.parent/'identity_summary.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    if len(completed)==3 and all(x.get('user_reported_power_off_seconds') is not None and x['user_reported_power_off_seconds']>=10 for x in summaries):
        if len({x['boot_id'] for x in summaries})!=3:raise RuntimeError('Boot IDs are not distinct')
        c.finish(['A1'],'Three power-cycle identity records','COMPLETE (POWER REMOVAL USER-ATTESTED)',{'boots':summaries},c.BASE/'01_identity_three_boots')

if __name__=='__main__':main()
