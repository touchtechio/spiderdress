from edi2c.i2c import I2CDevice

import sys

from time import time, sleep

dev = I2CDevice(0x04, debug=True)

while True:
    for level in range(12):
        dev.write_8(0x00, level)
        sleep(0.200)

