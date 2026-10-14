"""Packet framing and overflow refusal; no hardware access."""
import struct
import unittest
from collections import deque
from unittest.mock import Mock
import numpy as np
from fifo_drdy import FifoDataReady, decode_packets

class FifoTests(unittest.TestCase):
    def test_signed_axes_and_multiple_packets(self):
        p=struct.pack('>12h',16384,-16384,0,131,-131,32767,-32768,1,2,3,4,5)
        decoded=decode_packets(p)
        np.testing.assert_allclose(decoded[0],[9.80665,-9.80665,0,1,-1,32767/131])
        self.assertEqual(len(decoded),2)
        self.assertEqual(decoded[1][0],-2*9.80665)
    def test_partial_packet_refused(self):
        with self.assertRaises(ValueError):decode_packets(bytes(13))
    def test_overflow_refused_before_fifo_read(self):
        for status,count in [(16,12),(1,504)]:
            obj=FifoDataReady.__new__(FifoDataReady)
            obj.pending=deque();obj.edges=obj.timeouts=obj.overflows=0
            obj.line=Mock();obj.line.event_wait.return_value=True
            obj.line.event_read.return_value=Mock(sec=1,nsec=0)
            obj.bus=Mock();obj.bus.read_byte_data.return_value=status
            obj.bus.read_i2c_block_data.return_value=list(count.to_bytes(2,'big'))
            obj.writer=Mock()
            with self.assertRaisesRegex(RuntimeError,'overflow'):obj.read()
            self.assertEqual(obj.overflows,1)
            obj.bus.read_i2c_block_data.assert_called_once_with(0x68,0x72,2)

if __name__=='__main__':unittest.main()
