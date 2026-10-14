"""Drain the audited 12-byte MPU6500 FIFO on GPIO23 DATA_RDY edges.

Host completion time is shared by every packet in a batch, never synthesized.
Queued edges may yield an empty FIFO; they never manufacture samples.
Register map: RM-MPU-6500A-00 rev 2.1, registers 35, 55, 56, 58, 106, 114–116.
"""
import csv
import struct
import time
from collections import deque

import gpiod
import numpy as np


def decode_packets(payload, high_range=False):
    if len(payload) % 12:
        raise ValueError('Incomplete FIFO packet')
    scale = np.array([9.80665 / (2048 if high_range else 16384)] * 3
                     + [1 / (16.4 if high_range else 131)] * 3)
    return [np.asarray(v) * scale for v in struct.iter_unpack('>6h', payload)]


class FifoDataReady:
    def __init__(self, bus, out, high_range=False):
        self.bus = bus
        self.high_range = high_range
        self.pending = deque()
        self.batches = []
        self.edges = self.stale = self.timeouts = self.overflows = 0
        self.chip = gpiod.Chip('gpiochip0')
        self.line = self.chip.get_line(23)
        self.file = None
        self.requested = False
        try:
            self.line.request(consumer='helmx-fifo-drdy', type=gpiod.LINE_REQ_EV_RISING_EDGE)
            self.requested = True
            self.file = (out / 'gpio_edges.csv').open('w', buffering=1)
            self.writer = csv.writer(self.file)
            self.writer.writerow(['edge_monotonic', 'host_wake_monotonic', 'read_end_monotonic',
                                  'accepted', 'fifo_count_bytes', 'int_status', 'packets', 'payload_hex'])
            for reg, value in [(0x38, 0), (0x23, 0), (0x6a, 0), (0x37, 0), (0x6a, 4)]:
                bus.write_byte_data(0x68, reg, value)
            time.sleep(.01)
            bus.write_byte_data(0x68, 0x6a, 0x40)
            bus.read_byte_data(0x68, 0x3a)
            bus.write_byte_data(0x68, 0x38, 0x11)
            bus.write_byte_data(0x68, 0x23, 0x78)
        except BaseException:
            self.close()
            raise

    def read(self):
        deadline = time.monotonic() + 1
        while not self.pending:
            if time.monotonic() >= deadline or not self.line.event_wait(sec=1):
                self.timeouts += 1
                raise RuntimeError('No FIFO packet from DATA_RDY for one second')
            ev = self.line.event_read()
            edge = ev.sec + ev.nsec / 1e9
            wake = time.monotonic()
            self.edges += 1
            status = self.bus.read_byte_data(0x68, 0x3a)
            count = int.from_bytes(bytes(self.bus.read_i2c_block_data(0x68, 0x72, 2)), 'big')
            if status & 0x10 or count >= 504:
                self.overflows += 1
                self.writer.writerow([edge, wake, time.monotonic(), False, count, status, 0, ''])
                raise RuntimeError('FIFO overflow/near-full; framing cannot be trusted')
            payload = bytearray()
            nbytes = count // 12 * 12
            for offset in range(0, nbytes, 24):
                size = min(24, nbytes - offset)
                block = self.bus.read_i2c_block_data(0x68, 0x74, size)
                if len(block) != size:
                    raise RuntimeError('Short FIFO read')
                payload.extend(block)
            end = time.monotonic()
            samples = decode_packets(payload, self.high_range)
            self.writer.writerow([edge, wake, end, bool(samples), count, status, len(samples), payload.hex()])
            self.batches.append([end, count, status, len(samples)])
            self.pending.extend((sample, end, (end - wake) * 1000) for sample in samples)
        return self.pending.popleft()

    def close(self):
        if self.requested:
            self.line.release()
            self.requested = False
        self.chip.close()
        if self.file is not None:
            self.file.close()
