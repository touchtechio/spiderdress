"""Support for the PCA9685 PWM servo/LED controller.

Based almost entirely on:
    https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code
"""
from time import time, sleep
import math
import sys
from i2c import I2CDevice

# Registers/etc.
MODE1 = 0x00
MODE2 = 0x01
SUBADR1 = 0x02
SUBADR2 = 0x03
SUBADR3 = 0x04
PRESCALE = 0xFE
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09
ALL_LED_ON_L = 0xFA
ALL_LED_ON_H = 0xFB
ALL_LED_OFF_L = 0xFC
ALL_LED_OFF_H = 0xFD

LED_N_ON_H = lambda n: (LED0_ON_H + (4 * n))
LED_N_ON_L = lambda n: (LED0_ON_L + (4 * n))
LED_N_OFF_H = lambda n: (LED0_OFF_H + (4 * n))
LED_N_OFF_L = lambda n: (LED0_OFF_L + (4 * n))

RESOLUTION = 0x1000
CHANNELS = 0x10

LED_BASE_REGISTER = [
    ALL_LED_ON_L if c is CHANNELS else LED_N_ON_L(c) for c in range(CHANNELS+1)
]

# Bits
LED_FULL = 0x10
RESTART = 0x80
SLEEP = 0x10
ALLCALL = 0x01
INVRT = 0x10
OUTDRV = 0x04

POLICY_DISALLOW_OPEN_DRAIN = True
POLICY_DISALLOW_INVERT = True
POLICY_DISALLOW_FULL_ON = True

PWM_DEFAULT_FREQUENCY = 1500
PWM_MAX_ON = 0
PWM_MAX_OFF = 4095

class PCA9685:
    dev = None

    def __init__(self, address=0x40, debug=False):
        self.dev = I2CDevice(address, debug=debug)
        self.address = address
        self.debug = debug
        install_cleanup_handlers()

    def reset(self, frequency=PWM_DEFAULT_FREQUENCY, invert=False, totem=True):
        if self.debug:
            print >>sys.stderr, "PCA9685: Reseting PCA9685 MODE1 (without SLEEP) and MODE2"

        self.set(None, 0, 0)

        mode2 = 0

        if totem:
            mode2 |= OUTDRV
        elif POLICY_DISALLOW_OPEN_DRAIN:
            mode2 |= OUTDRV
            print >>sys.stderr, "PCA9685: Policy disallows open drain"

        #if not invert:
        #    mode2 &= ~INVRT & 0xFF
        #else:
        if invert:
            if not POLICY_DISALLOW_INVERT:
                mode2 |= INVRT
            else:
                mode2 &= ~INVRT & 0xFF
                print >>sys.stderr, "PCA9685: Policy disallows invert"

        self.dev.write_8(MODE2, mode2)
        self.dev.write_8(MODE1, ALLCALL)
        sleep(0.005)  # wait for oscillator

        mode1 = self.dev.read_u8(MODE1)
        mode1 &= ~SLEEP & 0xFF  # wake up (reset sleep)
        self.dev.write_8(MODE1, mode1)
        sleep(0.005)  # wait for oscillator
        
        self.set_frequency(frequency)

    def invert(self):
        mode2 = self.dev.read_u8(MODE2)
        invert = mode2 & INVRT == 0

        if POLICY_DISALLOW_INVERT:
            invert = False
            print >>sys.stderr, "PCA9685: Policy disallows invert"

        if not invert:
            mode2 &= ~INVRT & 0xFF
        else:
            mode2 |= INVRT

        self.dev.write_8(MODE2, mode2)
        return invert

    def set_frequency(self, freq):
        prescaleval = 25000000.0  # 25MHz
        prescaleval /= 4096.0  # 12-bit
        prescaleval /= float(freq)
        prescaleval -= 1.0

        if self.debug:
            print >>sys.stderr, "PCA9685: Setting PWM frequency to %d Hz" % freq
            print >>sys.stderr, "PCA9685: Estimated pre-scale: %d" % prescaleval
        prescale = math.floor(prescaleval + 0.5)
        if self.debug:
            print >>sys.stderr, "PCA9685: Final pre-scale: %d" % prescale

        oldmode = self.dev.read_u8(MODE1)
        newmode = (oldmode & 0x7F) | 0x10  # sleep
        self.dev.write_8(MODE1, newmode)  # go to sleep
        self.dev.write_8(PRESCALE, int(math.floor(prescale)))
        self.dev.write_8(MODE1, oldmode)
        sleep(0.005)
        self.dev.write_8(MODE1, oldmode | 0x80)

    def get_frequency(self):
        prescale = self.dev.read_u8(PRESCALE)
        freq = 1.0 / ((prescale + 1) * (4096.0 / 25000000.0))
        return freq

    def set(self, channel, on, off):
        if channel is None or channel < 0 or channel >= CHANNELS:
            channel = -1

        if on < 0:
            on = 0
        elif on > PWM_MAX_ON:
            on = PWM_MAX_ON

        if off < 0:
            off = 0
        elif off > PWM_MAX_OFF:
            off = PWM_MAX_OFF

        reg = LED_BASE_REGISTER[channel]

        if on != 0 and POLICY_DISALLOW_SET_ON:
            on = 0
            print >>sys.stderr, "PCA9685: Policy disallows setting non-zero duty cycle ON time"

        self.dev.write_8(reg, on & 0xFF)
        self.dev.write_8(reg + 1, on >> 8)
        self.dev.write_8(reg + 2, off & 0xFF)
        self.dev.write_8(reg + 3, off >> 8)

    def set_on(self, channel, on, full=False):
        if channel is None or channel < 0 or channel >= CHANNELS:
            channel = -1

        if on < 0:
            on = 0
        elif on > PWM_MAX_ON:
            on = PWM_MAX_ON

        if full:
            if POLICY_DISALLOW_FULL_ON:
                print >>sys.stderr, "PCA9685: Policy disallows setting full-on bit"
            else:
                on |= LED_FULL << 8

        reg = LED_BASE_REGISTER[channel]

        if on != 0 and POLICY_DISALLOW_SET_ON:
            on = 0

        self.dev.write_8(reg, on & 0xFF)
        self.dev.write_8(reg + 1, on >> 8)

    def set_off(self, channel, off, full=False):
        if channel is None or channel < 0 or channel >= CHANNELS:
            channel = -1

        if off < 0:
            off = 0
        elif off > PWM_MAX_OFF:
            off = PWM_MAX_OFF

        if full:
            off |= LED_FULL << 8

        reg = LED_BASE_REGISTER[channel]
        #self.dev.write_list(reg, [off & 0xFF, off >> 8])
        self.dev.write_8(reg + 2, off & 0xFF)
        self.dev.write_8(reg + 3, off >> 8)

    test_program = [
        [0.0, [
            [-1, 0x000, 0x000],
        ]],
        [1.0, [
            [-1, 0x000, 0x0FF],
        ]],
        [1.0, [
            [-1, 0x000, 0xFFF],
        ]],
        [1.0, [
            [-1, 0x000, 0xEEE],
            [15, 0x000, 0x00F]
        ]],
        [1.0, [
            [-1, 0x000, 0x0FF],
        ]],
        [1.0, [
            [-1, 0x000, 0x000],
        ]],
    ]

    def run_program(self, program, debug=False):
        current = [
            [
                reg,
                self.dev.read_u8(reg+0), self.dev.read_u8(reg+1) << 8,
                self.dev.read_u8(reg+2), self.dev.read_u8(reg+3) << 8
            ]
            for reg in LED_BASE_REGISTER
        ]

        for (duration, action) in program:
            if callable(duration):
                duration = duration()

            if duration:
                ts = time()

            for (channel, on, off) in action:
                if channel is None or channel < 0 or channel >= CHANNELS:
                    channel = -1

                if on < 0:
                    on = 0
                elif on > PWM_MAX_ON:
                    on = PWM_MAX_ON

                if off < 0:
                    off = 0
                elif off > PWM_MAX_OFF:
                    off = PWM_MAX_OFF

                reg, current_on_l, current_on_h, current_off_l, current_off_h = current[channel]

                on_l = on & 0xFF
                on_h = on >> 8
                off_l = off & 0xFF
                off_h = off >> 8

                if on_l != current_on_l:
                    self.dev.write_8(reg + 0, on_l)
                    current[channel][1] = on_l

                if on_h != current_on_h:
                    self.dev.write_8(reg + 1, on_h)
                    current[channel][2] = on_h

                if off_l != current_off_l:
                    self.dev.write_8(reg + 2, off_l)
                    current[channel][3] = off_l

                if off_h != current_off_h:
                    self.dev.write_8(reg + 3, off_h)
                    current[channel][4] = off_h

            if duration:
                elapsed = time() - ts
                to_sleep = duration - elapsed

                if to_sleep > 0:
                    sleep(to_sleep)
                elif debug and duration > 0:
                    print >>sys.stderr, "PCA9685: Action specified %.3fms and took %.3fms to execute" \
                                        % (duration * 1000.0, elapsed * 1000.0)


CLEANUP_HANDLERS_INSTALLED = False

def install_cleanup_handlers():
    import atexit, signal
    global CLEANUP_HANDLERS_INSTALLED

    if CLEANUP_HANDLERS_INSTALLED:
        return

    def cleanup():
        pwm = PCA9685()
        pwm.reset()

    atexit.register(cleanup)

    def catch_signal(sig, frame):
        cleanup()
        handler = handlers[sig]
        
        if callable(handler):
            handler(sig, frame)

    signals = [signal.SIGABRT, signal.SIGFPE, signal.SIGILL,
               signal.SIGINT, signal.SIGSEGV, signal.SIGTERM,
               signal.SIGKILL, signal.SIGSTOP, signal.SIGTSTP]

    handlers = {sig: signal.getsignal(sig) for sig in signals}
        
    for sig in signals:
        try:
            signal.signal(sig, catch_signal)
        except Exception, e:
            pass

    CLEANUP_HANDLERS_INSTALLED = True
