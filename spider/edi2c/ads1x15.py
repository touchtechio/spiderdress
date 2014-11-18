"""Support for the ADS1015 and ADS1115 analog-digital converters.

Based almost entirely on:
    https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code

NOT IMPLEMENTED: Conversion ready pin, page 15 datasheet.
"""
import time
import sys
import flock
from i2c import I2CDevice

# IC Identifiers
IC_ADS1015 = 0x00
IC_ADS1115 = 0x01

# Pointer Register
ADS1015_REG_POINTER_MASK = 0x03
ADS1015_REG_POINTER_CONVERT = 0x00
ADS1015_REG_POINTER_CONFIG = 0x01
ADS1015_REG_POINTER_LOWTHRESH = 0x02
ADS1015_REG_POINTER_HITHRESH = 0x03

# Config Register
ADS1015_REG_CONFIG_OS_MASK = 0x8000
ADS1015_REG_CONFIG_OS_SINGLE = 0x8000  # Write: Set to start a single-conversion
ADS1015_REG_CONFIG_OS_BUSY = 0x0000  # Read: Bit = 0 when conversion is in progress
ADS1015_REG_CONFIG_OS_NOTBUSY = 0x8000  # Read: Bit = 1 when device is not performing a conversion

ADS1015_REG_CONFIG_MUX_MASK = 0x7000
ADS1015_REG_CONFIG_MUX_DIFF_0_1 = 0x0000  # Differential P = AIN0, N = AIN1 (default)
ADS1015_REG_CONFIG_MUX_DIFF_0_3 = 0x1000  # Differential P = AIN0, N = AIN3
ADS1015_REG_CONFIG_MUX_DIFF_1_3 = 0x2000  # Differential P = AIN1, N = AIN3
ADS1015_REG_CONFIG_MUX_DIFF_2_3 = 0x3000  # Differential P = AIN2, N = AIN3
ADS1015_REG_CONFIG_MUX_SINGLE_0 = 0x4000  # Single-ended AIN0
ADS1015_REG_CONFIG_MUX_SINGLE_1 = 0x5000  # Single-ended AIN1
ADS1015_REG_CONFIG_MUX_SINGLE_2 = 0x6000  # Single-ended AIN2
ADS1015_REG_CONFIG_MUX_SINGLE_3 = 0x7000  # Single-ended AIN3

ADS1015_REG_CONFIG_PGA_MASK = 0x0E00
ADS1015_REG_CONFIG_PGA_6_144V = 0x0000  # +/-6.144V range
ADS1015_REG_CONFIG_PGA_4_096V = 0x0200  # +/-4.096V range
ADS1015_REG_CONFIG_PGA_2_048V = 0x0400  # +/-2.048V range (default)
ADS1015_REG_CONFIG_PGA_1_024V = 0x0600  # +/-1.024V range
ADS1015_REG_CONFIG_PGA_0_512V = 0x0800  # +/-0.512V range
ADS1015_REG_CONFIG_PGA_0_256V = 0x0A00  # +/-0.256V range

ADS1015_REG_CONFIG_MODE_MASK = 0x0100
ADS1015_REG_CONFIG_MODE_CONTIN = 0x0000  # Continuous conversion mode
ADS1015_REG_CONFIG_MODE_SINGLE = 0x0100  # Power-down single-shot mode (default)

ADS1015_REG_CONFIG_DR_MASK = 0x00E0
ADS1015_REG_CONFIG_DR_128SPS = 0x0000  # 128 samples per second
ADS1015_REG_CONFIG_DR_250SPS = 0x0020  # 250 samples per second
ADS1015_REG_CONFIG_DR_490SPS = 0x0040  # 490 samples per second
ADS1015_REG_CONFIG_DR_920SPS = 0x0060  # 920 samples per second
ADS1015_REG_CONFIG_DR_1600SPS = 0x0080  # 1600 samples per second (default)
ADS1015_REG_CONFIG_DR_2400SPS = 0x00A0  # 2400 samples per second
ADS1015_REG_CONFIG_DR_3300SPS = 0x00C0  # 3300 samples per second (also 0x00E0)

ADS1115_REG_CONFIG_DR_8SPS = 0x0000  # 8 samples per second
ADS1115_REG_CONFIG_DR_16SPS = 0x0020  # 16 samples per second
ADS1115_REG_CONFIG_DR_32SPS = 0x0040  # 32 samples per second
ADS1115_REG_CONFIG_DR_64SPS = 0x0060  # 64 samples per second
ADS1115_REG_CONFIG_DR_128SPS = 0x0080  # 128 samples per second
ADS1115_REG_CONFIG_DR_250SPS = 0x00A0  # 250 samples per second (default)
ADS1115_REG_CONFIG_DR_475SPS = 0x00C0  # 475 samples per second
ADS1115_REG_CONFIG_DR_860SPS = 0x00E0  # 860 samples per second

ADS1015_REG_CONFIG_CMODE_MASK = 0x0010
ADS1015_REG_CONFIG_CMODE_TRAD = 0x0000  # Traditional comparator with hysteresis (default)
ADS1015_REG_CONFIG_CMODE_WINDOW = 0x0010  # Window comparator

ADS1015_REG_CONFIG_CPOL_MASK = 0x0008
ADS1015_REG_CONFIG_CPOL_ACTVLOW = 0x0000  # ALERT/RDY pin is low when active (default)
ADS1015_REG_CONFIG_CPOL_ACTVHI = 0x0008  # ALERT/RDY pin is high when active

ADS1015_REG_CONFIG_CLAT_MASK = 0x0004  # Determines if ALERT/RDY pin latches once asserted
ADS1015_REG_CONFIG_CLAT_NONLAT = 0x0000  # Non-latching comparator (default)
ADS1015_REG_CONFIG_CLAT_LATCH = 0x0004  # Latching comparator

ADS1015_REG_CONFIG_CQUE_MASK = 0x0003
ADS1015_REG_CONFIG_CQUE_1CONV = 0x0000  # Assert ALERT/RDY after one conversions
ADS1015_REG_CONFIG_CQUE_2CONV = 0x0001  # Assert ALERT/RDY after two conversions
ADS1015_REG_CONFIG_CQUE_4CONV = 0x0002  # Assert ALERT/RDY after four conversions
ADS1015_REG_CONFIG_CQUE_NONE = 0x0003  # Disable the comparator and put ALERT/RDY in high state (default)

SPS_ADS1115 = {
    8: ADS1115_REG_CONFIG_DR_8SPS,
    16: ADS1115_REG_CONFIG_DR_16SPS,
    32: ADS1115_REG_CONFIG_DR_32SPS,
    64: ADS1115_REG_CONFIG_DR_64SPS,
    128: ADS1115_REG_CONFIG_DR_128SPS,
    250: ADS1115_REG_CONFIG_DR_250SPS,
    475: ADS1115_REG_CONFIG_DR_475SPS,
    860: ADS1115_REG_CONFIG_DR_860SPS
}

SPS_ADS1015 = {
    128: ADS1015_REG_CONFIG_DR_128SPS,
    250: ADS1015_REG_CONFIG_DR_250SPS,
    490: ADS1015_REG_CONFIG_DR_490SPS,
    920: ADS1015_REG_CONFIG_DR_920SPS,
    1600: ADS1015_REG_CONFIG_DR_1600SPS,
    2400: ADS1015_REG_CONFIG_DR_2400SPS,
    3300: ADS1015_REG_CONFIG_DR_3300SPS
}

PGA_ADS1X15 = {
    6144: ADS1015_REG_CONFIG_PGA_6_144V,
    4096: ADS1015_REG_CONFIG_PGA_4_096V,
    2048: ADS1015_REG_CONFIG_PGA_2_048V,
    1024: ADS1015_REG_CONFIG_PGA_1_024V,
    512: ADS1015_REG_CONFIG_PGA_0_512V,
    256: ADS1015_REG_CONFIG_PGA_0_256V
}


class ADS1X15:
    dev = None
    lock = None

    def __init__(self, address=0x48, ic=IC_ADS1115, debug=False):
        self.dev = I2CDevice(address, debug=debug)
        self.address = address
        self.debug = debug
        self.lock = flock.Flock('/tmp/ADS1X15.lock')

        # Make sure the IC specified is valid
        if (ic != IC_ADS1015) and (ic != IC_ADS1115):
            if self.debug:
                print "ADS1x15: Invalid IC specfied: 0x%02X" % ic
        else:
            self.ic = ic

        # Set pga value, so that getLastConversionResult() can use it,
        # any function that accepts a pga value must update this.
        self.pga = 6144

    def read_single_ended(self, channel=0, pga=6144, sps=250):
        """Gets a single-ended ADC reading from the specified channel in mV.

        The sample rate for this mode (single-shot) can be used to lower the noise
        (low sps) or to lower the power consumption (high sps) by duty cycling,
        see datasheet page 14 for more info.
        
        The pga must be given in mV, see page 13 for the supported values.
        """

        # With invalid channel return -1
        if channel < 0 or channel > 3:
            raise ValueError("ADS1X15: Invalid channel %d" % channel)

        # Disable comparator, Non-latching, Alert/Rdy active low
        # traditional comparator, single-shot mode
        config = (
            ADS1015_REG_CONFIG_CQUE_NONE |
            ADS1015_REG_CONFIG_CLAT_NONLAT |
            ADS1015_REG_CONFIG_CPOL_ACTVLOW |
            ADS1015_REG_CONFIG_CMODE_TRAD |
            ADS1015_REG_CONFIG_MODE_SINGLE
        )
        
        try:
            self.lock.acquire()

            # Set sample per seconds, defaults to 250sps
            # If sps is in the dictionary it returns the value of the constant,
            # othewise it returns the value for 250sps. This saves a lot of if/elif/else code!
            if self.ic == IC_ADS1015:
                config |= SPS_ADS1015.get(sps, ADS1015_REG_CONFIG_DR_1600SPS)
            else:
                if (sps not in SPS_ADS1115) and self.debug:
                    print >>sys.stderr, "ADS1X15: Invalid sps specified: %d, using 6144mV" % sps
                config |= SPS_ADS1115.get(sps, ADS1115_REG_CONFIG_DR_250SPS)

            # Set PGA/voltage range, defaults to +-6.144V
            if (pga not in PGA_ADS1X15) and self.debug:
                print >>sys.stderr, "ADS1X15: Invalid pga specified: %d, using 6144mV" % sps
            config |= PGA_ADS1X15.get(pga, ADS1015_REG_CONFIG_PGA_6_144V)
            self.pga = pga

            # Set the channel to be converted
            if channel == 3:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_3
            elif channel == 2:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_2
            elif channel == 1:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_1
            else:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_0

            # Set 'start single-conversion' bit
            config |= ADS1015_REG_CONFIG_OS_SINGLE

            # Write config register to the ADC
            config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
            self.dev.write_list(ADS1015_REG_POINTER_CONFIG, config_bytes)

            # Wait for the ADC conversion to complete
            # The minimum delay depends on the sps: delay >= 1/sps
            # Add at least 10ms to be sure
            delay = max(0.010, 1.0 / sps + 0.001)
            time.sleep(delay)

            # Read the conversion results
            result = self.dev.read_list(ADS1015_REG_POINTER_CONVERT, 2)
            if self.ic == IC_ADS1015:
                # Shift right 4 bits for the 12-bit ADS1015 and convert to mV
                return (((result[0] << 8) | (result[1] & 0xFF)) >> 4) * pga / 2048.0
            else:
                # Return a mV value for the ADS1115
                # (Take signed values into account as well)
                val = (result[0] << 8) | result[1]
                if val > 0x7FFF:
                    return (val - 0xFFFF) * pga / 32768.0
                else:
                    return ((result[0] << 8) | result[1]) * pga / 32768.0
        
        finally:
            self.lock.release()

    def read_differential(self, chp=0, chn=1, pga=6144, sps=250):
        """Gets a differential ADC reading from channels chP and chN in mV.
        
        The sample rate for this mode (single-shot) can be used to lower the noise
        (low sps) or to lower the power consumption (high sps) by duty cycling,
        see data sheet page 14 for more info.

        The pga must be given in mV, see page 13 for the supported values.
        """

        # Disable comparator, Non-latching, Alert/Rdy active low
        # traditional comparator, single-shot mode
        config = (
            ADS1015_REG_CONFIG_CQUE_NONE |
            ADS1015_REG_CONFIG_CLAT_NONLAT |
            ADS1015_REG_CONFIG_CPOL_ACTVLOW |
            ADS1015_REG_CONFIG_CMODE_TRAD |
            ADS1015_REG_CONFIG_MODE_SINGLE
        )

        # Set channels
        if chp == 0 and chn == 1:
            config |= ADS1015_REG_CONFIG_MUX_DIFF_0_1
        elif chp == 0 and chn == 3:
            config |= ADS1015_REG_CONFIG_MUX_DIFF_0_3
        elif chp == 2 and chn == 3:
            config |= ADS1015_REG_CONFIG_MUX_DIFF_2_3
        elif chp == 1 and chn == 3:
            config |= ADS1015_REG_CONFIG_MUX_DIFF_1_3
        else:
            raise ValueError("ADS1X15: Invalid channels specified: %d, %d" % (chp, chn))

        try:
            self.lock.acquire()

            # Set sample per seconds, defaults to 250sps
            # If sps is in the dictionary it returns the value of the constant,
            # othewise it returns the value for 250sps. This saves a lot of if/elif/else code!
            if self.ic == IC_ADS1015:
                config |= SPS_ADS1015.get(sps, ADS1015_REG_CONFIG_DR_1600SPS)
            else:
                if (sps not in SPS_ADS1115) and self.debug:
                    print >>sys.stderr, "ADS1X15: Invalid pga specified: %d, using 6144mV" % sps
                config |= SPS_ADS1115.get(sps, ADS1115_REG_CONFIG_DR_250SPS)

            # Set PGA/voltage range, defaults to +-6.144V
            if (pga not in PGA_ADS1X15) and self.debug:
                print "ADS1x15: Invalid pga specified: %d, using 6144mV" % sps
            config |= PGA_ADS1X15.get(pga, ADS1015_REG_CONFIG_PGA_6_144V)
            self.pga = pga

            # Set 'start single-conversion' bit
            config |= ADS1015_REG_CONFIG_OS_SINGLE

            # Write config register to the ADC
            config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
            self.dev.write_list(ADS1015_REG_POINTER_CONFIG, config_bytes)

            # Wait for the ADC conversion to complete
            # The minimum delay depends on the sps: delay >= 1/sps
            # Add at least 10ms to be sure
            delay = max(0.010, 1.0 / sps + 0.001)
            time.sleep(delay)

            # Read the conversion results
            result = self.dev.read_list(ADS1015_REG_POINTER_CONVERT, 2)
            if self.ic == IC_ADS1015:
                # Shift right 4 bits for the 12-bit ADS1015 and convert to mV
                return (((result[0] << 8) | (result[1] & 0xFF)) >> 4) * pga / 2048.0
            else:
                # Return a mV value for the ADS1115
                # (Take signed values into account as well)
                val = (result[0] << 8) | result[1]
                if val > 0x7FFF:
                    return (val - 0xFFFF) * pga / 32768.0
                else:
                    return ((result[0] << 8) | result[1]) * pga / 32768.0
                
        finally:
            self.lock.release()

    def read_differential_01(self, pga=6144, sps=250):
        """Gets a differential ADC reading from channels 0 and 1 in mV.

        The sample rate for this mode (single-shot) can be used to lower the noise
        (low sps) or to lower the power consumption (high sps) by duty cycling,
        see data sheet page 14 for more info.

        The pga must be given in mV, see page 13 for the supported values.
        """
        return self.read_differential(0, 1, pga, sps)

    def read_differential_03(self, pga=6144, sps=250):
        """Gets a differential ADC reading from channels 0 and 3 in mV.

        The sample rate for this mode (single-shot) can be used to lower the noise
        (low sps) or to lower the power consumption (high sps) by duty cycling,
        see data sheet page 14 for more info.

        The pga must be given in mV, see page 13 for the supported values.
        """
        return self.read_differential(0, 3, pga, sps)

    def read_differential_13(self, pga=6144, sps=250):
        """Gets a differential ADC reading from channels 1 and 3 in mV.

        The sample rate for this mode (single-shot) can be used to lower the noise
        (low sps) or to lower the power consumption (high sps) by duty cycling,
        see data sheet page 14 for more info.

        The pga must be given in mV, see page 13 for the supported values.
        """
        return self.read_differential(1, 3, pga, sps)

    def read_differential_23(self, pga=6144, sps=250):
        """Gets a differential ADC reading from channels 2 and 3 in mV.

        The sample rate for this mode (single-shot) can be used to lower the noise
        (low sps) or to lower the power consumption (high sps) by duty cycling,
        see data sheet page 14 for more info.

        The pga must be given in mV, see page 13 for the supported values.
        """
        return self.read_differential(2, 3, pga, sps)

    def start_continuous_conversion(self, channel=0, pga=6144, sps=250):
        """Starts the continuous conversion mode and returns the first ADC reading
        in mV from the specified channel.

        The sps controls the sample rate.

        The pga must be given in mV, see datasheet page 13 for the supported values.
        Use get_last_conversion_results() to read the next values and
        stop_continuous_conversion() to stop converting.
        """
        if channel < 0 or channel > 3:
            raise ValueError("ADS1X15: Invalid channel %d" % channel)

        # Disable comparator, Non-latching, Alert/Rdy active low
        # traditional comparator, continuous mode
        # The last flag is the only change we need, page 11 datasheet
        config = (
            ADS1015_REG_CONFIG_CQUE_NONE |
            ADS1015_REG_CONFIG_CLAT_NONLAT |
            ADS1015_REG_CONFIG_CPOL_ACTVLOW |
            ADS1015_REG_CONFIG_CMODE_TRAD |
            ADS1015_REG_CONFIG_MODE_CONTIN
        )

        try:
            self.lock.acquire()

            # Set sample per seconds, defaults to 250sps
            # If sps is in the dictionary it returns the value of the constant,
            # othewise it returns the value for 250sps. This saves a lot of if/elif/else code!
            if self.ic == IC_ADS1015:
                config |= SPS_ADS1015.get(sps, ADS1015_REG_CONFIG_DR_1600SPS)
            else:
                if (sps not in SPS_ADS1115) and self.debug:
                    print >>sys.stderr, "ADS1X15: Invalid pga specified: %d, using 6144mV" % sps
                config |= SPS_ADS1115.get(sps, ADS1115_REG_CONFIG_DR_250SPS)

            # Set PGA/voltage range, defaults to +-6.144V
            if (pga not in PGA_ADS1X15) and self.debug:
                print >>sys.stderr, "ADS1X15: Invalid pga specified: %d, using 6144mV" % sps
            config |= PGA_ADS1X15.get(pga, ADS1015_REG_CONFIG_PGA_6_144V)
            self.pga = pga

            # Set the channel to be converted
            if channel == 3:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_3
            elif channel == 2:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_2
            elif channel == 1:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_1
            else:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_0

                # Set 'start single-conversion' bit to begin conversions
            # No need to change this for continuous mode!
            config |= ADS1015_REG_CONFIG_OS_SINGLE

            # Write config register to the ADC
            # Once we write the ADC will convert continously
            # we can read the next values using getLastConversionResult
            config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
            self.dev.write_list(ADS1015_REG_POINTER_CONFIG, config_bytes)

            # Wait for the ADC conversion to complete
            # The minimum delay depends on the sps: delay >= 1/sps
            # Add at least 10ms to be sure
            delay = max(0.010, 1.0 / sps + 0.001)
            time.sleep(delay)

            # Read the conversion results
            result = self.dev.read_list(ADS1015_REG_POINTER_CONVERT, 2)
            if self.ic == IC_ADS1015:
                # Shift right 4 bits for the 12-bit ADS1015 and convert to mV
                return (((result[0] << 8) | (result[1] & 0xFF)) >> 4) * pga / 2048.0
            else:
                # Return a mV value for the ADS1115
                # (Take signed values into account as well)
                val = (result[0] << 8) | result[1]
                if val > 0x7FFF:
                    return (val - 0xFFFF) * pga / 32768.0
                else:
                    return ((result[0] << 8) | result[1]) * pga / 32768.0

        finally:
            self.lock.release()

    def start_continuous_differential_conversion(self, chp=0, chn=1, pga=6144, sps=250):
        """Starts the continuous differential conversion mode and returns the first ADC reading
        in mV as the difference from the specified channels.

        The sps controls the sample rate.

        The pga must be given in mV, see datasheet page 13 for the supported values.
        Use get_last_conversion_results() to read the next values and
        stop_continuous_conversion() to stop converting.
        """

        # Disable comparator, Non-latching, Alert/Rdy active low
        # traditional comparator, continuous mode
        # The last flag is the only change we need, page 11 datasheet
        config = (
            ADS1015_REG_CONFIG_CQUE_NONE |
            ADS1015_REG_CONFIG_CLAT_NONLAT |
            ADS1015_REG_CONFIG_CPOL_ACTVLOW |
            ADS1015_REG_CONFIG_CMODE_TRAD |
            ADS1015_REG_CONFIG_MODE_CONTIN
        )

        try:
            self.lock.acquire()

            # Set sample per seconds, defaults to 250sps
            # If sps is in the dictionary it returns the value of the constant,
            # othewise it returns the value for 250sps. This saves a lot of if/elif/else code!
            if self.ic == IC_ADS1015:
                config |= SPS_ADS1015.get(sps, ADS1015_REG_CONFIG_DR_1600SPS)
            else:
                if (sps not in SPS_ADS1115) and self.debug:
                    print >>sys.stderr, "ADS1X15: Invalid pga specified: %d, using 6144mV" % sps
                config |= SPS_ADS1115.get(sps, ADS1115_REG_CONFIG_DR_250SPS)

            # Set PGA/voltage range, defaults to +-6.144V
            if (pga not in PGA_ADS1X15) and self.debug:
                print >>sys.stderr, "ADS1X15: Invalid pga specified: %d, using 6144mV" % sps
            config |= PGA_ADS1X15.get(pga, ADS1015_REG_CONFIG_PGA_6_144V)
            self.pga = pga

            # Set channels
            if chp == 0 and chn == 1:
                config |= ADS1015_REG_CONFIG_MUX_DIFF_0_1
            elif chp == 0 and chn == 3:
                config |= ADS1015_REG_CONFIG_MUX_DIFF_0_3
            elif chp == 2 and chn == 3:
                config |= ADS1015_REG_CONFIG_MUX_DIFF_2_3
            elif chp == 1 and chn == 3:
                config |= ADS1015_REG_CONFIG_MUX_DIFF_1_3
            else:
                raise ValueError("ADS1X15: Invalid channels specified: %d, %d" % (chp, chn))

            # Set 'start single-conversion' bit to begin conversions
            # No need to change this for continuous mode!
            config |= ADS1015_REG_CONFIG_OS_SINGLE

            # Write config register to the ADC
            # Once we write the ADC will convert continously
            # we can read the next values using getLastConversionResult
            config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
            self.dev.write_list(ADS1015_REG_POINTER_CONFIG, config_bytes)

            # Wait for the ADC conversion to complete
            # The minimum delay depends on the sps: delay >= 1/sps
            # Add at least 10ms to be sure
            delay = max(0.010, 1.0 / sps + 0.001)
            time.sleep(delay)

            # Read the conversion results
            result = self.dev.read_list(ADS1015_REG_POINTER_CONVERT, 2)
            if self.ic == IC_ADS1015:
                # Shift right 4 bits for the 12-bit ADS1015 and convert to mV
                return (((result[0] << 8) | (result[1] & 0xFF)) >> 4) * pga / 2048.0
            else:
                # Return a mV value for the ADS1115
                # (Take signed values into account as well)
                val = (result[0] << 8) | result[1]
                if val > 0x7FFF:
                    return (val - 0xFFFF) * pga / 32768.0
                else:
                    return ((result[0] << 8) | result[1]) * pga / 32768.0

        except:
            self.lock.release()
            raise

    def stop_continuous_conversion(self):
        """Stops the ADC's conversions when in continuous mode and resets the
        configuration to its default value.
        """
        # Write the default config register to the ADC
        # Once we write, the ADC will do a single conversion and
        # enter power-off mode.
        config = 0x8583  # Page 18 datasheet.
        config_bytes = [(config >> 8) & 0xFF, config & 0xFF]

        try:
            self.dev.write_list(ADS1015_REG_POINTER_CONFIG, config_bytes)
        finally:
            self.lock.release()

        return True

    def get_last_conversion_results(self):
        """Returns the last ADC conversion result in mV.
        """
        # Read the conversion results
        result = self.dev.read_list(ADS1015_REG_POINTER_CONVERT, 2)
        if self.ic == IC_ADS1015:
            # Shift right 4 bits for the 12-bit ADS1015 and convert to mV
            return (((result[0] << 8) | (result[1] & 0xFF)) >> 4) * self.pga / 2048.0
        else:
            # Return a mV value for the ADS1115
            # (Take signed values into account as well)
            val = (result[0] << 8) | result[1]
            if val > 0x7FFF:
                return (val - 0xFFFF) * self.pga / 32768.0
            else:
                return ((result[0] << 8) | result[1]) * self.pga / 32768.0

    def start_single_ended_comparator(self, channel, threshold_high, threshold_low, 
                                      pga=6144, sps=250, active_low=True, traditional_mode=True,
                                      latching=False, num_readings=1):
        """Starts the comparator mode on the specified channel, see datasheet pg. 15.
        
        In traditional mode it alerts (ALERT pin will go low)  when voltage exceeds
        threshold_high until it falls below threshold_low (both given in mV).
        In window mode (traditional_mode=False) it alerts when voltage doesn't lie
        between both thresholds.
        
        In latching mode the alert will continue until the conversion value is read.
        
        num_readings controls how many readings are necessary to trigger an alert: 1, 2 or 4.
        
        Use get_last_conversion_results() to read the current value (which may differ
        from the one that triggered the alert) and clear the alert pin in latching mode.
        This function starts the continuous conversion mode.  The sps controls
        the sample rate and the pga the gain, see datasheet page 13.
        """
        if channel < 0 or channel > 3:
            raise ValueError("ADS1X15: Invalid channel %d" % channel)

        # Continuous mode
        config = ADS1015_REG_CONFIG_MODE_CONTIN

        if not active_low:
            config |= ADS1015_REG_CONFIG_CPOL_ACTVHI
        else:
            config |= ADS1015_REG_CONFIG_CPOL_ACTVLOW

        if not traditional_mode:
            config |= ADS1015_REG_CONFIG_CMODE_WINDOW
        else:
            config |= ADS1015_REG_CONFIG_CMODE_TRAD

        if latching:
            config |= ADS1015_REG_CONFIG_CLAT_LATCH
        else:
            config |= ADS1015_REG_CONFIG_CLAT_NONLAT

        if num_readings == 4:
            config |= ADS1015_REG_CONFIG_CQUE_4CONV
        elif num_readings == 2:
            config |= ADS1015_REG_CONFIG_CQUE_2CONV
        else:
            config |= ADS1015_REG_CONFIG_CQUE_1CONV

        try:
            self.lock.acquire()

            # Set sample per seconds, defaults to 250sps
            # If sps is in the dictionary it returns the value of the constant,
            # othewise it returns the value for 250sps. This saves a lot of if/elif/else code!
            if self.ic == IC_ADS1015:
                if (sps not in SPS_ADS1015) and self.debug:
                    print >>sys.stderr, "ADS1X15: Invalid sps specified: %d, using 1600sps" % sps
                config |= SPS_ADS1015.get(sps, ADS1015_REG_CONFIG_DR_1600SPS)
            else:
                if (sps not in SPS_ADS1115) and self.debug:
                    print >>sys.stderr, "ADS1X15: Invalid sps specified: %d, using 250sps" % sps
                config |= SPS_ADS1115.get(sps, ADS1115_REG_CONFIG_DR_250SPS)

            # Set PGA/voltage range, defaults to +-6.144V
            if (pga not in PGA_ADS1X15) and self.debug:
                print >>sys.stderr, "ADS1X15: Invalid pga specified: %d, using 6144mV" % pga
            config |= PGA_ADS1X15.get(pga, ADS1015_REG_CONFIG_PGA_6_144V)
            self.pga = pga

            # Set the channel to be converted
            if channel == 3:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_3
            elif channel == 2:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_2
            elif channel == 1:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_1
            else:
                config |= ADS1015_REG_CONFIG_MUX_SINGLE_0

            # Set 'start single-conversion' bit to begin conversions
            config |= ADS1015_REG_CONFIG_OS_SINGLE

            # Write threshold high and low registers to the ADC
            # V_digital = (2^(n-1)-1)/pga*V_analog
            if self.ic == IC_ADS1015:
                threshold_word_high = int(threshold_high * (2048.0 / pga))
            else:
                threshold_word_high = int(threshold_high * (32767.0 / pga))
            threshold_bytes = [(threshold_word_high >> 8) & 0xFF, threshold_word_high & 0xFF]
            self.dev.write_list(ADS1015_REG_POINTER_HITHRESH, threshold_bytes)

            if self.ic == IC_ADS1015:
                threshold_low_word = int(threshold_low * (2048.0 / pga))
            else:
                threshold_low_word = int(threshold_low * (32767.0 / pga))
            threshold_low_bytes = [(threshold_low_word >> 8) & 0xFF, threshold_low_word & 0xFF]
            self.dev.write_list(ADS1015_REG_POINTER_LOWTHRESH, threshold_low_bytes)

            # Write config register to the ADC
            # Once we write the ADC will convert continously and alert when things happen,
            # we can read the converted values using getLastConversionResult
            config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
            self.dev.write_list(ADS1015_REG_POINTER_CONFIG, config_bytes)

        except:
            self.lock.release()
            raise

    def start_differential_comparator(self, chp, chn, threshold_high, threshold_low,
                                      pga=6144, sps=250, active_low=True, traditional_mode=True,
                                      latching=False, num_readings=1):
        """Starts the comparator mode on the specified channel, see datasheet pg. 15. 
        In traditional mode it alerts (ALERT pin will go low)  when voltage exceeds
        threshold_high until it falls below threshold_low (both given in mV).

        In window mode (traditional_mode=False) it alerts when voltage doesn't lie
        between both thresholds.

        In latching mode the alert will continue until the conversion value is read.

        num_readings controls how many readings are necessary to trigger an alert: 1, 2 or 4.

        Use get_last_conversion_results() to read the current value  (which may differ
        from the one that triggered the alert) and clear the alert pin in latching mode.
        This function starts the continuous conversion mode.  The sps controls
        the sample rate and the pga the gain, see datasheet page 13.
        """
        # Continuous mode
        config = ADS1015_REG_CONFIG_MODE_CONTIN

        if not active_low:
            config |= ADS1015_REG_CONFIG_CPOL_ACTVHI
        else:
            config |= ADS1015_REG_CONFIG_CPOL_ACTVLOW

        if not traditional_mode:
            config |= ADS1015_REG_CONFIG_CMODE_WINDOW
        else:
            config |= ADS1015_REG_CONFIG_CMODE_TRAD

        if latching:
            config |= ADS1015_REG_CONFIG_CLAT_LATCH
        else:
            config |= ADS1015_REG_CONFIG_CLAT_NONLAT

        if num_readings == 4:
            config |= ADS1015_REG_CONFIG_CQUE_4CONV
        elif num_readings == 2:
            config |= ADS1015_REG_CONFIG_CQUE_2CONV
        else:
            config |= ADS1015_REG_CONFIG_CQUE_1CONV

        try:
            self.lock.acquire()

            # Set sample per seconds, defaults to 250sps
            # If sps is in the dictionary it returns the value of the constant,
            # othewise it returns the value for 250sps. This saves a lot of if/elif/else code!
            if self.ic == IC_ADS1015:
                if (sps not in SPS_ADS1015) and self.debug:
                    print >>sys.stderr, "ADS1X15: Invalid sps specified: %d, using 1600sps" % sps
                config |= SPS_ADS1015.get(sps, ADS1015_REG_CONFIG_DR_1600SPS)
            else:
                if (sps not in SPS_ADS1115) and self.debug:
                    print >>sys.stderr, "ADS1X15: Invalid sps specified: %d, using 250sps" % sps
                config |= SPS_ADS1115.get(sps, ADS1115_REG_CONFIG_DR_250SPS)

            # Set PGA/voltage range, defaults to +-6.144V
            if (pga not in PGA_ADS1X15) and self.debug:
                print >>sys.stderr, "ADS1x15: Invalid pga specified: %d, using 6144mV" % pga
            config |= PGA_ADS1X15.get(pga, ADS1015_REG_CONFIG_PGA_6_144V)
            self.pga = pga

            # Set channels
            if chp == 0 and chn == 1:
                config |= ADS1015_REG_CONFIG_MUX_DIFF_0_1
            elif chp == 0 and chn == 3:
                config |= ADS1015_REG_CONFIG_MUX_DIFF_0_3
            elif chp == 2 and chn == 3:
                config |= ADS1015_REG_CONFIG_MUX_DIFF_2_3
            elif chp == 1 and chn == 3:
                config |= ADS1015_REG_CONFIG_MUX_DIFF_1_3
            else:
                raise ValueError("ADS1X15: Invalid channels specified: %d, %d" % (chp, chn))

            # Set 'start single-conversion' bit to begin conversions
            config |= ADS1015_REG_CONFIG_OS_SINGLE

            # Write threshold high and low registers to the ADC
            # V_digital = (2^(n-1)-1)/pga*V_analog
            if self.ic == IC_ADS1015:
                threshold_word_high = int(threshold_high * (2048.0 / pga))
            else:
                threshold_word_high = int(threshold_high * (32767.0 / pga))
            threshold_high_bytes = [(threshold_word_high >> 8) & 0xFF, threshold_word_high & 0xFF]
            self.dev.write_list(ADS1015_REG_POINTER_HITHRESH, threshold_high_bytes)

            if self.ic == IC_ADS1015:
                threshold_word_low = int(threshold_low * (2048.0 / pga))
            else:
                threshold_word_low = int(threshold_low * (32767.0 / pga))
            threshold_low_bytes = [(threshold_word_low >> 8) & 0xFF, threshold_word_low & 0xFF]
            self.dev.write_list(ADS1015_REG_POINTER_LOWTHRESH, threshold_low_bytes)

            # Write config register to the ADC
            # Once we write the ADC will convert continously and alert when things happen,
            # we can read the converted values using getLastConversionResult
            config_bytes = [(config >> 8) & 0xFF, config & 0xFF]
            self.dev.write_list(ADS1015_REG_POINTER_CONFIG, config_bytes)

        except:
            self.lock.release()
            raise
