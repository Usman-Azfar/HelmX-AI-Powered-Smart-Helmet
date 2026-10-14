import unittest
from iio_capture import layout,decode

class LayoutTests(unittest.TestCase):
    def test_mixed_endian_and_timestamp_alignment(self):
        spec,size=layout([('in_timestamp',6,'le:s64/64>>0'),('in_accel_x',0,'be:s16/16>>0'),('in_anglvel_x',1,'be:s16/16>>0')])
        self.assertEqual(size,16)
        self.assertEqual(spec[-1]['offset'],8)
        payload=(-32768).to_bytes(2,'big',signed=True)+(131).to_bytes(2,'big')+bytes(4)+(123456789).to_bytes(8,'little')
        self.assertEqual(decode(payload,spec),{'in_accel_x':-32768,'in_anglvel_x':131,'in_timestamp':123456789})
    def test_shifted_signed(self):
        spec,size=layout([('x',0,'le:s12/16>>4')])
        self.assertEqual(decode(bytes.fromhex('f0ff'),spec)['x'],-1)
    def test_unsupported_repeat_rejected(self):
        with self.assertRaises(ValueError):layout([('x',0,'be:s16/16X3>>0')])

if __name__=='__main__':unittest.main()
