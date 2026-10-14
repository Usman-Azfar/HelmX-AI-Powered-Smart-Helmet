import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import cold_warm_capture as cw

class FakeBus:
    def __init__(self):self.regs={v:7 for v in cw.REGS.values()};self.regs[0x75]=112;self.closed=False
    def read_byte_data(self,address,reg):return self.regs[reg]
    def write_byte_data(self,address,reg,value):self.regs[reg]=value
    def read_i2c_block_data(self,*args):raise OSError('Injected I2C read failure')
    def close(self):self.closed=True

class ColdWarmTests(unittest.TestCase):
    def test_restores_registers_after_read_failure(self):
        bus=FakeBus();before=dict(bus.regs)
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/'evidence';base.mkdir()
            with patch.object(cw,'BASE',base),patch('smbus2.SMBus',return_value=bus):
                with self.assertRaises(RuntimeError):cw.capture(base/'cold',1)
            self.assertEqual(bus.regs,before)
            self.assertTrue(bus.closed)
            s=json.loads((base/'cold/summary.json').read_text())
            self.assertIn('Injected I2C read failure',s['exception'])
            self.assertIsNone(s['cleanup_error'])
            self.assertEqual(s['samples'],0)

if __name__=='__main__':unittest.main()
