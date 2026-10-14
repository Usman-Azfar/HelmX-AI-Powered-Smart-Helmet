"""GPIO23 rising-edge acquisition; libgpiod v1, audited 0x70 device map.

INT_PIN_CFG=0: active high, push-pull, 50-us pulse, status-read clear.
INT_ENABLE=1: raw data ready only. No alarm GPIO is requested.
Source: TDK RM-MPU-6500A-00, registers 55, 56, 58.
"""
import csv
import struct
import time
import gpiod
import numpy as np


class DataReady:
    def __init__(self, bus, out, high_range=False):
        self.bus = bus
        self.chip = gpiod.Chip('gpiochip0')
        self.line = self.chip.get_line(23)
        self.line.request(consumer='helmx-drdy-research', type=gpiod.LINE_REQ_EV_RISING_EDGE)
        self.file = (out/'gpio_edges.csv').open('w', buffering=1)
        self.writer = csv.writer(self.file)
        self.writer.writerow(['edge_monotonic', 'host_wake_monotonic', 'read_end_monotonic', 'accepted'])
        self.scale = np.array([9.80665/(2048 if high_range else 16384)]*3 + [1/(16.4 if high_range else 131)]*3)
        self.edges = self.stale = self.timeouts = 0
        bus.write_byte_data(0x68, 0x38, 0)
        bus.write_byte_data(0x68, 0x23, 0)
        bus.write_byte_data(0x68, 0x6a, 0)
        bus.write_byte_data(0x68, 0x37, 0)
        bus.read_byte_data(0x68, 0x3a)
        bus.write_byte_data(0x68, 0x38, 1)

    def read(self):
        while True:
            if not self.line.event_wait(sec=1):
                self.timeouts += 1
                raise RuntimeError('No DATA_RDY edge on GPIO23 for one second')
            ev = self.line.event_read()
            edge = ev.sec + ev.nsec/1e9
            wake = time.monotonic()
            self.edges += 1
            # Register output has no history: never replay old queued edges as samples.
            if wake-edge > .015:
                self.stale += 1
                self.writer.writerow([edge, wake, '', False])
                continue
            values = struct.unpack('>7h', bytes(self.bus.read_i2c_block_data(0x68, 0x3b, 14)))
            end = time.monotonic()
            self.writer.writerow([edge, wake, end, True])
            return np.asarray(values[:3]+values[4:])*self.scale, end, (end-wake)*1000

    def close(self):
        self.line.release()
        self.chip.close()
        self.file.close()
