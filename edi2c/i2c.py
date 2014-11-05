"""I2C stuff.

Based almost entirely on:
    https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code
"""
import smbus
import sys

DEFAULT_BUS = 6


class I2CDevice(object):
    def __init__(self, address, busnum=DEFAULT_BUS, debug=False):
        self.address = address
        self.bus = smbus.SMBus(busnum)
        self.debug = debug

    def bus_reset(self):
        """Reset all devices on the i2c bus that respond to this command.
        """
        address = self.address
        self.address = 0
        try:
            self.write_raw_8(0x06)
        finally:
            self.address = address

    def write_8(self, reg, value):
        """Writes an 8-bit value to the specified register/address"""
        self.bus.write_byte_data(self.address, reg, value)
        if self.debug:
            print >>sys.stderr, "I2C: Wrote 0x%02X to register 0x%02X" % (value, reg)

    def write_16(self, reg, value):
        """Writes a 16-bit value to the specified register/address pair"""
        self.bus.write_word_data(self.address, reg, value)
        if self.debug:
            print >>sys.stderr, ("I2C: Wrote 0x%02X to register pair 0x%02X,0x%02X" %
                                (value, reg, reg + 1))

    def write_raw_8(self, value):
        """Writes an 8-bit value on the bus"""
        self.bus.write_byte(self.address, value)
        if self.debug:
            print >>sys.stderr, "I2C: Wrote 0x%02X" % value

    def write_list(self, reg, lst):
        """Writes an array of bytes using I2C format"""
        if self.debug:
            print >>sys.stderr, "I2C: Writing list to register 0x%02X:" % reg
            print >>sys.stderr, "I2C:", lst
        self.bus.write_i2c_block_data(self.address, reg, lst)

    def read_list(self, reg, length):
        """Read a list of bytes from the I2C device"""
        results = self.bus.read_i2c_block_data(self.address, reg, length)
        if self.debug:
            print >>sys.stderr, ("I2C: Device 0x%02X returned the following from reg 0x%02X" %
                   (self.address, reg))
            print results
        return results

    def read_u8(self, reg):
        """Read an unsigned byte from the I2C device"""
        result = self.bus.read_byte_data(self.address, reg)
        if self.debug:
            print >>sys.stderr, ("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" %
                   (self.address, result & 0xFF, reg))
        return result

    def read_s8(self, reg):
        """Reads a signed byte from the I2C device"""
        result = self.bus.read_byte_data(self.address, reg)
        if result > 127:
            result -= 256
        if self.debug:
            print >>sys.stderr, ("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" %
                   (self.address, result & 0xFF, reg))
        return result

    def read_u16(self, reg, little_endian=True):
        """Reads an unsigned 16-bit value from the I2C device"""
        result = self.bus.read_word_data(self.address, reg)
        # Swap bytes if using big endian because read_word_data assumes little 
        # endian on ARM (little endian) systems.
        if not little_endian:
            result = ((result << 8) & 0xFF00) + (result >> 8)
        if self.debug:
            print >>sys.stderr, "I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, result & 0xFFFF, reg)
        return result

    def read_s16(self, reg, little_endian=True):
        """Reads a signed 16-bit value from the I2C device"""
        result = self.read_u16(reg, little_endian)
        if result > 32767:
            result -= 65536
        return result


def reverse_byte_order(data):
    """Reverses the byte order of an int (16-bit) or long (32-bit) value"""
    # Courtesy Vishal Sapre
    byte_count = len(hex(data)[2:].replace('L', '')[::2])
    val = 0
    for i in range(byte_count):
        val = (val << 8) | (data & 0xff)
        data >>= 8
    return val
