import serial
import time
import collections
import teensy

#http://www.pololu.com/docs/0J40/5.e
class MaestroController:
    def __init__(self):
        self.serial = self.get_serial('/dev/ttyMFD1', 9600)
       
    def get_serial(self, tty, baud):
        ser = serial.Serial()
        ser.port = tty
        ser.baudrate = baud
        ser.open()
        return ser
    
    def go_home(self):
        cmd = chr(0xaa) + chr(0x0c) + chr(0x22)
        self.serial.write(cmd)

    def set_position(self, servo, angle):
        pulse_width = self.translate(angle)
        if pulse_width == -1:
            print "Angle outside of range [-75, 75]"
            return

        if servo < 12:
            device = 12
        else:
            device = 13
            servo = servo - 12
        low_bits = pulse_width & 0x7f
        high_bits = (pulse_width >> 7) & 0x7f
        channel = servo & 0x7F
        
        cmd = chr(0xaa) + chr(device&0xff) + chr(0x04) + chr(channel) + chr(low_bits) + chr(high_bits)
        self.serial.write(cmd)

    def set_position_multiple(self, first_servo, *pulse_widths):
        num_targets = len(pulse_widths)
        if first_servo+num_targets > 24:
            print "Too many servo targets."
            return

        if first_servo < 12:
            device = 12
        else:
            device = 13
            first_servo = first_servo - 12

        both_devices = False
        targets1 = num_targets
        if device == 12 and first_servo+num_targets > 11:
            both_devices = True
            targets1 = 12 - first_servo
            targets2 = num_targets - targets1

        target_bits = []
        channel = int(first_servo) & 0x7f
        for pulse_width in pulse_widths[:12-first_servo]:
            if pulse_width < 736 or pulse_width > 2272:
                print "Pulse width outside of range [736, 2272]"
                return

            pulse_width = int(pulse_width) * 4

            low_bits = pulse_width & 0x7f
            high_bits = (pulse_width >> 7) & 0x7f
            target_bits.append(low_bits)
            target_bits.append(high_bits)

        cmd = chr(0xaa) + chr(device&0xff) + chr(0x1f) + chr((targets1)&0xff) + chr(channel)
        for byte in target_bits:
            cmd += chr(byte)
        #print ":".join("{:02x}".format(ord(c)) for c in cmd)

        if both_devices is True:
            target_bits2 = []
            channel2 = 0
            for pulse_width in pulse_widths[12-first_servo:]:
                if pulse_width < 736 or pulse_width > 2272:
                    print "Pulse width outside of range [736, 2272]"
                    return

                pulse_width = int(pulse_width) * 4

                low_bits = pulse_width & 0x7f
                high_bits = (pulse_width >> 7) & 0x7f
                target_bits2.append(low_bits)
                target_bits2.append(high_bits)

            cmd2 = chr(0xaa) + chr(0x0d) + chr(0x1f) + chr((targets2)&0xff) + chr(channel2)
            for byte in target_bits2:
                cmd2 += chr(byte)
            #print ":".join("{:02x}".format(ord(c)) for c in cmd2)
            self.serial.write(cmd2)

        self.serial.write(cmd)

    def get_position(self, servo):
        channel = servo &0x7F
        cmd = chr(0xaa) + chr(0x0c) + chr(0x10) + chr(channel)
        self.serial.write(cmd)
        w1 = self.serial.read()
        w2 = self.serial.read()
        return hex(ord(w1)), hex(ord(w2))

    def get_servos_moving(self):
        cmd1 = chr(0xaa) + chr(0x0c) + chr(0x13)
        self.serial.write(cmd1)
        r = self.serial.read()
        if ord(r) == 1:
            return True

        cmd2 = chr(0xaa) + chr(0x0d) + chr(0x13)
        self.serial.write(cmd2)
        r = self.serial.read()
        if ord(r) == 1:
            return True

        return False

    def set_speed(self, servo, speed):
        device = 12
        if servo > 11:
            servo = servo - 12
            device = 13
        channel = servo & 0x7f
        low_bits = speed & 0xff
        high_bits = (speed >> 8) & 0xff
        cmd = chr(0xaa) + chr(device&0xff) + chr(0x07) + chr(channel) + chr(low_bits) + chr(high_bits)

        self.serial.write(cmd)

    def set_accel(self, servo, accel):
        device = 12
        if servo > 11:
            servo = servo - 12
            device = 13
        channel = servo & 0x7f
        low_bits = accel & 0xff
        high_bits = (accel >> 8) & 0xff
        cmd = chr(0xaa) + chr(device&0xff) + chr(0x09) + chr(channel) + chr(low_bits) + chr(high_bits)

        self.serial.write(cmd)

    def translate(self, angle):
        # min_pulse, max_pulse, and mid_pulse have been determined by testing since
        # we don't have a data sheet for these servos. They are in microseconds.
        min_pulse, max_pulse, mid_pulse = 750, 2250, 1500
        min_angle, max_angle = -75, 75
        if angle < min_angle or angle > max_angle:
            return -1

        # according to servo specs, every 10us is ~1 degree.
        val = mid_pulse + (angle * 10)
        val = val * 4 # convert to 1/4us for servo controller protocol.
        return int(val)

class ServoScript:
    """Define a script for servo motion.

    This takes 6 legs and will attempt to move all servos into their
    positions at provided speed and acceleration.
    """
    __isDefined = False

    def __init__(self, maestro):
        self.maestro = maestro

    def define_script(self, leg0, leg1, leg2, leg3, leg4, leg5):
        """Store given leg position/speed/acceleration information
        to be run later.
        """

        self.legs = []
        self.legs.append(leg0)
        self.legs.append(leg1)
        self.legs.append(leg2)
        self.legs.append(leg3)
        self.legs.append(leg4)
        self.legs.append(leg5)
        self.__isDefined = True

    def run_script(self):
        """Run the stored script assuming it has been defined."""

        if self.__isDefined is not True:
            print "Must define script before running."
            return

        positions = []

        # Immediately set the speed and accel values through maestro,
        # but not position. This is done so that all servos can
        # move in a syncronized way.
        for i in range(0, 24):
            self.maestro.set_speed(i, self.legs[i/4].speeds[i%4])
            self.maestro.set_accel(i, self.legs[i/4].accels[i%4])
            positions.append(self.legs[i/4].positions[i%4])

        #print positions
        self.maestro.set_position_multiple(0, *positions)

# Leg abstracts 4 individual servos into their respective positions,
# and the speed and acceleration to move into this position.
Leg = collections.namedtuple('Leg', ['positions', 'speeds', 'accels'])

def setup_scripts(maestro, scripts):
    """Predefine scripts so that they may be run in response to
    various sensors.
    """

    leg0 = Leg([1070, 2070, 980, 1380], [40]*4, [10]*4)
    leg1 = Leg([1960, 1280, 1500, 1500], [40]*4, [10]*4)
    leg2 = Leg([1500, 1690, 1380, 1550], [40]*4, [10]*4)
    leg3 = Leg([1650, 1110, 1990, 1550], [40]*4, [10]*4)
    leg4 = Leg([820, 1610, 1500, 1500], [40]*4, [10]*4)
    leg5 = Leg([1500, 2030, 1300, 1150], [40]*4, [10]*4)
    extend = ServoScript(maestro)
    extend.define_script(leg0, leg1, leg2, leg3, leg4, leg5)
    scripts["ex"] = extend

    leg0 = Leg([1070, 2070, 1560, 2150], [40]*4, [10]*4)
    leg1 = Leg([1280, 1980, 1500, 1500], [40]*4, [10]*4)
    leg2 = Leg([1500, 1690, 750, 850], [40]*4, [10]*4)
    leg3 = Leg([1650, 1110, 1320, 840], [40]*4, [10]*4)
    leg4 = Leg([1520, 910, 1500, 1500], [40]*4, [10]*4)
    leg5 = Leg([1500, 2030, 1960, 1870], [40]*4, [10]*4)
    parke = ServoScript(maestro)
    parke.define_script(leg0, leg1, leg2, leg3, leg4, leg5)
    scripts["pae"] = parke

    leg0 = Leg([1070, 2260, 740, 1500], [20, 5, 20, 20], [8]*4)
    leg1 = Leg([1950, 1210, 1500, 1500], [20]*4, [8]*4)
    leg2 = Leg([1500, 1630, 1190, 2000], [20, 3, 20, 50], [8]*4)
    leg3 = Leg([1650, 940, 2150, 1460], [20, 5, 20, 20], [8]*4)
    leg4 = Leg([820, 1680, 1500, 1500], [20]*4, [8]*4)
    leg5 = Leg([1500, 2090, 1500, 740], [20, 3, 20, 50], [8]*4)
    jugendstil = ServoScript(maestro)
    jugendstil.define_script(leg0, leg1, leg2, leg3, leg4, leg5)
    scripts["ju"] = jugendstil

    leg0 = Leg([1070, 2070, 1560, 2150], [20, 5, 20, 20], [8]*4)
    leg1 = Leg([1280, 1980, 1500, 1500], [20]*4, [8]*4)
    leg2 = Leg([1500, 1690, 750, 850], [20, 3, 20, 50], [8]*4)
    leg3 = Leg([1650, 1110, 1320, 840], [20, 5, 20, 20], [8]*4)
    leg4 = Leg([1520, 910, 1500, 1500], [20]*4, [8]*4)
    leg5 = Leg([1500, 2030, 1960, 1870], [20, 3, 20, 50], [8]*4)
    parkj = ServoScript(maestro)
    parkj.define_script(leg0, leg1, leg2, leg3, leg4, leg5)
    scripts["paj"] = parkj

if __name__ == '__main__':
    maestro = MaestroController()
    teensy = teensy.Teensy()
    color = [255, 255, 180]
    
    scripts = {}
    setup_scripts(maestro, scripts)

    while True:
        scripts["pae"].run_script()
        while maestro.get_servos_moving() is True:
            time.sleep(0.1)
            
        teensy.set_brightness(255)
        teensy.set_color(color)
        teensy.set_intimate(color)
        time.sleep(3)

        scripts["ex"].run_script()
        teensy.set_brightness(255)
        teensy.set_color(color)
        teensy.set_personal(color)
        time.sleep(0.5)
        while maestro.get_servos_moving() is True:
            time.sleep(0.1)

        scripts["pae"].run_script()
        time.sleep(0.5)
        while maestro.get_servos_moving() is True:
            time.sleep(0.1)
        teensy.set_brightness(255)
        teensy.set_color(color)
        teensy.set_intimate(color)
        time.sleep(1)

        scripts["ju"].run_script()
        teensy.set_brightness(255)
        teensy.set_color(color)
        teensy.set_personal(color)
        time.sleep(0.5)
        while maestro.get_servos_moving() is True:
            time.sleep(0.1)
        time.sleep(1)

        scripts["paj"].run_script()
        time.sleep(0.5)
        while maestro.get_servos_moving() is True:
            time.sleep(0.1)

        teensy.set_brightness(255)
        teensy.set_color(color)
        teensy.set_social(color)
        time.sleep(5)
        teensy.set_off()
        teensy.set_off()
        teensy.set_off()