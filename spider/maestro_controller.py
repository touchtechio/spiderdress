import serial
import time
from itertools import izip

#http://www.pololu.com/docs/0J40/5.e
class MaestroController(object):
    def __init__(self):
        self.serial = self.get_serial('/dev/ttyMFD1', 9600)
        self.positions = {}
        self.scripts = {}

        self.setup_positions()
        self.current_position = "park"
        self.animate(self.current_position, [1000*6])

    def get_serial(self, tty, baud):
        """Retrieve and open UART connection to maestro controllers.
        """
        ser = serial.Serial()
        ser.port = tty
        ser.baudrate = baud
        ser.open()
        return ser

    def setup_positions(self):
        park = ServoPositions([
            [1070, 2070, 1560, 2150], [1280, 1980, 1500, 1500],
            [1500, 1690, 750, 850], [1650, 1110, 1320, 840],
            [1520, 910, 1500, 1500], [1500, 2030, 1960, 1870]])

        extend = ServoPositions([
            [1070, 2070, 980, 1380], [1960, 1280, 1500, 1500],
            [1500, 1690, 1380, 1550], [1650, 1110, 1990, 1550],
            [820, 1610, 1500, 1500], [1500, 2030, 1300, 1150]])

        jugendstil = ServoPositions([
            [1070, 2260, 740, 1500], [1950, 1210, 1500, 1500],
            [1500, 1630, 1190, 2000], [1650, 940, 2150, 1460],
            [820, 1680, 1500, 1500], [1500, 2090, 1500, 740]])

        self.positions["park"] = park
        self.positions["extend"] = extend
        self.positions["jugendstil"] = jugendstil

    def animate(self, script_name, animation_times):
        """Run through script. animation_times should be a list of 6 values
        for each leg.
        """
        animation_times = [t/2 for t in animation_times]
        common_route = self.find_common_route(
            self.positions[self.current_position].safe_routes,
            self.positions[script_name].safe_routes)
        print "common route: ", common_route, "\n"

        difference_route = self.positions[self.current_position] - self.positions[common_route]
        print "diff route: ", str(difference_route), "\n"
        speed_accel_route = []
        for leg, animation_time in izip(difference_route.legs, animation_times):
            for servo in leg:
                speed_accel_route.append(self.time_to_speed_accel(animation_time, servo, 0))
        print "speed_accel route: ", speed_accel_route, "\n"

        difference_final = self.positions[common_route] - self.positions[script_name]
        print "diff final: ", str(difference_final), "\n"
        speed_accel_final = []
        for leg, animation_time in izip(difference_final.legs, animation_times):
            for servo in leg:
                speed_accel_final.append(self.time_to_speed_accel(animation_time, servo, 0))
        print "speed_accel final: ", speed_accel_final, "\n"

        #animate to route
        self.move_to(self.positions[common_route], speed_accel_route)

        while self.get_servos_moving() is True:
            time.sleep(0.01)

        #animate to script_name
        self.move_to(self.positions[script_name], speed_accel_final)

        self.current_position = script_name


    def find_common_route(self, routes1, routes2):
        common_routes = routes1 & routes2

        if len(common_routes) > 0:
            return common_routes.pop()

        return "park"

    def move_to(self, position, speed_accel):
        pulse_widths = []

        # Immediately set the speed and accel values through maestro,
        # but not position. This is done so that all servos can
        # move in a syncronized way.
        for i in range(0, 24):
            self.set_speed(i, speed_accel[i][0])
            self.set_accel(i, speed_accel[i][1])
            pulse_widths.append(position.legs[i/4][i%4])
        print "pulse_widths: ", pulse_widths, "\n"

        self.set_position_multiple(0, *pulse_widths)

    def time_to_speed_accel(self, anim_time, distance, initial_velocity):
        half_time = float(anim_time)/2
        half_distance = distance/2.0

        accel = (2.0*(half_distance-(initial_velocity*half_time))) / (half_time**2)
        max_speed = initial_velocity + (accel * half_time)

        accel = accel * 10 * 80 / 0.25 + 0.5
        max_speed = max_speed * 10 / 0.25 + 0.5

        return int(max(max_speed, 1)), int(max(accel, 1))

    def go_home(self):
        """Return all servos to "home" position.
        """
        cmd = chr(0xaa) + chr(0x0c) + chr(0x22)
        self.serial.write(cmd)

    def set_position(self, servo, angle):
        """Set the position of servo to an angle between [-75, 75].
        """
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

        cmd = chr(0xaa) + chr(device&0xff) + chr(0x04) + chr(channel)
        cmd = cmd + chr(low_bits) + chr(high_bits)
        self.serial.write(cmd)

    def set_position_multiple(self, first_servo, *pulse_widths):
        """Set position of multiple servos, starting at first servo,
        going to pulse_widths.length servos. Uses raw pulse width instead
        of angle conversion.
        """
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
        """Return two hex bytes, representing the position of servo as
        pulse width * 4 per maestro protocol.
        """
        channel = servo &0x7F
        cmd = chr(0xaa) + chr(0x0c) + chr(0x10) + chr(channel)
        self.serial.write(cmd)
        byte1 = self.serial.read()
        byte2 = self.serial.read()
        return hex(ord(byte1)), hex(ord(byte2))

    def get_servos_moving(self):
        """Returns true if any servos are moving, false otherwise.
        """
        cmd1 = chr(0xaa) + chr(0x0c) + chr(0x13)
        self.serial.write(cmd1)
        byte = self.serial.read()
        if ord(byte) == 1:
            return True

        cmd2 = chr(0xaa) + chr(0x0d) + chr(0x13)
        self.serial.write(cmd2)
        byte = self.serial.read()
        if ord(byte) == 1:
            return True

        return False

    def set_speed(self, servo, speed):
        """Set the maximum speed of servo.
        """
        device = 12
        if servo > 11:
            servo = servo - 12
            device = 13
        channel = servo & 0x7f
        low_bits = speed & 0xff
        high_bits = (speed >> 8) & 0xff
        cmd = chr(0xaa) + chr(device&0xff) + chr(0x07) + chr(channel)
        cmd = cmd + chr(low_bits) + chr(high_bits)

        self.serial.write(cmd)

    def set_accel(self, servo, accel):
        """Set the acceleration of servo. Will accelerate up to max speed,
        then as the servo approaches position, will decelerate smoothly.
        """
        device = 12
        if servo > 11:
            servo = servo - 12
            device = 13
        channel = servo & 0x7f
        low_bits = accel & 0xff
        high_bits = (accel >> 8) & 0xff
        cmd = chr(0xaa) + chr(device&0xff) + chr(0x09) + chr(channel) + \
            chr(low_bits) + chr(high_bits)

        self.serial.write(cmd)

    def translate(self, angle):
        """Translate an angle to pulse width * 4, for the maestro protocol.
        """
        mid_pulse = 1500
        min_angle, max_angle = -75, 75
        if angle < min_angle or angle > max_angle:
            return -1

        # according to servo specs, every 10us is ~1 degree.
        val = mid_pulse + (angle * 10)
        val = val * 4 # convert to 1/4us for servo controller protocol.
        return int(val)

class ServoPositions(object):
    def __init__(self, legs):
        self.legs = legs
        self.safe_routes = set()

    def add_safe_route(self, route_name):
        self.safe_routes.add(route_name)

    def __sub__(self, other):
        abs0 = [abs(a - b) for a, b in zip(self.legs[0], other.legs[0])]
        abs1 = [abs(a - b) for a, b in zip(self.legs[1], other.legs[1])]
        abs2 = [abs(a - b) for a, b in zip(self.legs[2], other.legs[2])]
        abs3 = [abs(a - b) for a, b in zip(self.legs[3], other.legs[3])]
        abs4 = [abs(a - b) for a, b in zip(self.legs[4], other.legs[4])]
        abs5 = [abs(a - b) for a, b in zip(self.legs[5], other.legs[5])]

        return ServoPositions([abs0, abs1, abs2, abs3, abs4, abs5])

    def __str__(self):
        return str(self.legs)

if __name__ == "__main__":
    MAESTRO = MaestroController()

    print "Animate EXTEND: "
    MAESTRO.animate("extend", [1000, 1000, 1500, 1000, 1000, 1500])

    print "\nAnimate JUGENDSTIL: "
    MAESTRO.animate("jugendstil", [500, 500, 1500, 500, 500, 1500])
