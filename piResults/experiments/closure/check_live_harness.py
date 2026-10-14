"""Software checks of register restoration and output alignment; no real I2C/GPIO."""
import copy
import importlib
import struct
import tempfile
from pathlib import Path
from unittest.mock import patch
import campaign
import crash_monitor as cm
import live

CFG=cm.load_config(campaign.BASE/'frozen/deploy/config.yaml')

class Bus:
    def __init__(self):self.regs={r:0 for r in live.REGS.values()};self.regs[0x75]=0x70;self.regs[0x6b]=1;self.original=self.regs.copy()
    def read_byte_data(self,a,r):return self.regs.get(r,0)
    def write_byte_data(self,a,r,v):self.regs[r]=v
    def read_i2c_block_data(self,a,r,n):
        if r==0x72:return [0,12]
        if r==0x74:return list(struct.pack('>6h',0,0,16384,0,0,0))[:n]
        return [0]*n
    def close(self):pass

class Model:
    def __init__(self,*args):pass
    def predict(self,*args):return 0.,0.

def case(mode,fail):
    bus=Bus();results=[]
    with tempfile.TemporaryDirectory(prefix='helmx_harness_check_') as tmp:
        base=Path(tmp)
        argv=['live.py','--label','trial','--seconds','.12','--mode',mode,'--filtered']
        with patch.object(campaign,'BASE',base),patch.object(campaign,'metadata',return_value={'software_test':True}),patch.object(campaign,'command',return_value={}),patch.object(campaign,'finish',side_effect=lambda ids,title,status,result,directory:results.append((status,result))),patch.object(live.smbus2,'SMBus',return_value=bus),patch.object(cm,'mpu6050',return_value=object()),patch.object(cm,'CrashModel',Model),patch.object(cm,'load_config',return_value=copy.deepcopy(CFG)),patch.object(cm,'load_model_thresholds',return_value=(.989,10.878)),patch.object(cm,'read_sensor',return_value=None if fail else [0.,0.,9.81,0.,0.,0.]),patch('sys.argv',argv):
            if mode=='fifo':
                # Limit mock FIFO to one 20-ms sample using real delay.
                import time
                original=bus.read_i2c_block_data
                def delayed(a,r,n):
                    if r==0x72:time.sleep(.02)
                    return original(a,r,n)
                bus.read_i2c_block_data=delayed
            live.main()
        assert bus.regs==bus.original,('Registers not restored',mode,fail,bus.regs,bus.original)
        status,result=results[0]
        if fail:assert status=='FAIL' and result['i2c_failures']==1 and result['n_samples']==0
        else:
            assert status.startswith('COMPLETE') and result['n_samples']>0
            assert sum(1 for _ in (base/'trial/raw_sensor.csv').open())-1==result['n_samples']
        print('PASS mock',mode,'failure' if fail else 'success','register restoration and raw/summary alignment')

if __name__=='__main__':
    case('polling',False);case('polling',True);case('fifo',False)
