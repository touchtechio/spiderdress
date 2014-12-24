"""maestro_controller.py
Classes and functions necessary to drive two daisy chained Maestro servo controllers,
including the ability to define poses and animate between them.
"""

import serial
from time import time, sleep
import random
from multiprocessing import Process, Value
from itertools import izip
import teensy

#http://www.pololu.com/docs/0J40/5.e
class MaestroController(object):
    """MaestroController gives access to two Maestro's connected via UART, as well as
    the ability to run animations based on pre defined positions.
    """
    INTIMATE = 0
    PERSONAL = 1
    SOCIAL = 2
    PUBLIC = 3

    COLOR = [255, 255, 180]

    def __init__(self):
        self.serial = get_serial('/dev/ttyMFD1', 9600)
        self.positions = {}
        self.animations = {}
        self.animations_by_zone = {}

        self.setup_positions("positions_dress_a")
        self.setup_animations()

        self.current_position = "park"
        self.current_space = Value('d', MaestroController.PUBLIC, lock=True)
        self.big_breath = Value('b', False, lock=True)

        self.run_ces = Value('b', False, lock=True)
        self.ces_animation_process = Process(target=self._ces_animation_process)
        self.animating = False

        self.tsy = teensy.Teensy()
        self.ces_teensy_process = Process(target=self._ces_teensy_process)

        self.move_to(self.positions[self.current_position], [(10, 10)]*24)

    def setup_positions(self, filename):
        """Setup predefined positions and their safe routes.
        """
        position_file = open(filename, "r")
        line = position_file.readline()
        while line != "":
            leg_positions = []

            #Position name
            position_name = line.rstrip('\n')

            #Read in the leg values
            for i in range(6):
                pos = position_file.readline().split(',')
                pos = [int(s) for s in pos]
                leg_positions.append(pos)

            self.positions[position_name] = ServoPositions(leg_positions)
            line = position_file.readline()

    def setup_animations(self):
        """Setup predefined animations (tuple of a list of positions, and times).
        """
        park = [("park", [1500]*6)]
        extend = [("extend", [1500]*6)]
        breathe = [
            ("extend", [1300]*6),
            ("park", [1300]*6),
            ("extend_half", [1300]*6),
            ("park", [1300]*6)]
        slow_breathe = [
            ("extend", [2000]*6),
            ("park", [2000]*6),
            ("extend_half", [1750]*6),
            ("pause", 450),
            ("park", [1750]*6),
            ("pause", 450),
            ("extend", [2000]*6),
            ("park", [2000]*6),
            ("extend_half", [1750]*6),
            ("pause", 450),
            ("park", [1750]*6)]
        knife = [
            ("knife", [600]*6),
            ("pause", 500),
            ("park", [1000]*6)]
        attack = [
            ("extend", [750]*6),
            ("park", [900]*6)]
        point = [ #note, don't use point as much
            ("point", [1500]*6),
            ("park", [1500]*6)]
        jugendstil = [ #note, pause around 0.5 between position
            ("jugendstil_half", [1500]*6),
            ("pause", 750),
            ("jugendstil", [1500]*6),
            ("pause", 850),
            ("park", [1500]*6)]
        challenge = [
            ("challenge", [1500]*6),
            ("pause", 1000),
            ("park", [1500]*6)]
        wiggle = [
            ("wiggle_up", [750]*6),
            ("wiggle_down", [100]*6),
            ("wiggle_up", [100]*6),
            ("wiggle_down", [100]*6),
            ("wiggle_up", [100]*6),
            ("park", [750]*6)]
        ninja = [
            ("extend", [600]*6),
            ("park", [1000]*6),
            ("knife", [500]*6),
            ("park", [1500]*6)]
        dance = [
            ]

        self.animations["park"] = park
        self.animations["extend"] = extend
        self.animations["breathe"] = breathe
        self.animations["slow_breathe"] = slow_breathe
        self.animations["knife"] = knife
        self.animations["attack"] = attack
        self.animations["point"] = point
        self.animations["jugendstil"] = jugendstil
        self.animations["challenge"] = challenge
        self.animations["wiggle"] = wiggle
        self.animations["ninja"] = ninja
        self.animations["dance"] = dance

        self.animations_by_zone["personal"] = [
            ["attack", "challenge", "breathe"],
            ["ninja", "wiggle", "breathe"],
            ["knife", "jugendstil", "breathe"]]
        self.animations_by_zone["social_public"] = ["park"]
        self.animations_by_zone["intimate"] = ["push_away"]

    def prox_distance_listener(self, distance):
        """Get distance data from prox sensor.
        """
        pass

    def prox_space_listener(self, space):
        """Get space data from prox sensor.
        """
        self.current_space.value = space
        print space
        return self.run_ces.value

    def respiration_listener(self):
        self.big_breath.value = True

    def start_ces_animation(self):
        self.run_ces.value = True
        self.ces_teensy_process.start()
        self.ces_animation_process.start()

    def stop_ces_animation(self):
        self.run_ces.value = False
        self.ces_teensy_process.join()
        self.ces_animation_process.join()

        self.ces_teensy_process = Process(target=self._ces_teensy_process)
        self.ces_animation_process = Process(target=self._ces_animation_process)

    def _ces_animation_process(self):
        random.seed()

        #For PERSONAL prox zone, we run through a series of animations and
        #must keep track of our progress.
        zone_index = random.choice(self.animations_by_zone["personal"])
        zone_progress = 0

        while self.run_ces.value:
            #print self.current_space.value
            space = self.current_space.value
            respiration = self.big_breath.value

            if respiration:
                self.big_breath.value = False
                zone_progress = 0
                zone_index = random.choice(self.animations_by_zone["personal"])
                self.animation("slow_breathe")
            elif space == MaestroController.INTIMATE:
                self.animation("park")
                zone_progress = 0
                random.choice(self.animations_by_zone["personal"])
            elif space == MaestroController.PERSONAL:
                self.animation(zone_index[zone_progress])
                zone_progress += 1
                if zone_progress >= 3:
                    zone_progress = 2
            else:
                zone_progress = 0
                random.choice(self.animations_by_zone["personal"])
                self.animation(self.animations_by_zone["social_public"][0])

    def _ces_teensy_process(self):
        space = self.current_space.value
        while self.run_ces.value:
            prev_space = space
            space = self.current_space.value

            if space == prev_space:
                continue

            if space == MaestroController.INTIMATE:
                self.tsy.set_intimate(MaestroController.COLOR)
            elif space == MaestroController.PERSONAL:
                self.tsy.set_personal(MaestroController.COLOR)
            elif space == MaestroController.SOCIAL:
                self.tsy.set_social(MaestroController.COLOR)
            elif space == MaestroController.PUBLIC:
                #TODO: change when Karli updates teensy.
                self.tsy.set_animation(teensy.GLOW_SLOW) #GLOW_SLOW for now

    def animation(self, animation_name):
        """Run through animation found with animation_name.
        """
        if self.animating or self.current_position == animation_name:
            return

        anim = self.animations[animation_name]
        anim_length = len(anim)

        self.animating = True
        i = 0
        while i < anim_length:
            self.animate(anim[i][0], anim[i][1])
            i += 1
        sleep(3)
        self.animating = False

    def animate(self, script_name, animation_times):
        """Run through script. Animate will take animation_time_safe to reach safe route
        position, and animation_time_final to reach final destination. Times should
        be a list of 6 values for each leg.
        """
        #print script_name
        if script_name == "pause":
            sleep((animation_times+100)/1000)
            return

        #Determine the difference between the common route and our final position so we can
        #calculate the speed and acceleration necessary to get there.
        difference_final = self.positions[self.current_position] - self.positions[script_name]
        max_diff, max_index = difference_final.legs[0][0], (0, 0)
        speed_accel = []
        for leg, animation_time in izip(difference_final.legs, animation_times):
            for servo in leg:
                speed_accel.append(time_to_speed_accel(animation_time, servo, 0))
        for i in range(6):
            for j in range(4):
                if max_diff < difference_final.legs[i][j]:
                    max_diff = difference_final.legs[i][j]
                    max_index = (i, j)
        index = max_index[0]*4+max_index[1]
        max_value = self.positions[script_name].legs[max_index[0]][max_index[1]]

        #Animate to common route.
        self.move_to(self.positions[script_name], speed_accel)
        sleep(0.05)

        are_servos_moving = True
        while are_servos_moving:
            current_position = self.get_position(index)
            #print current_position
            if current_position is not None and abs(current_position - max_value) <= max_diff*0.03:
                are_servos_moving = False

        self.current_position = script_name

    def move_to(self, position, speed_accel):
        """Send speed, acceleration and position data to the Maestro.
        """
        pulse_widths = []

        # Immediately set the speed and accel values through maestro,
        # but not position. This is done so that all servos can
        # move in a syncronized way.
        i = 0
        while i < 24:
            self.set_speed(i, speed_accel[i][0])
            self.set_accel(i, speed_accel[i][1])
            pulse_widths.append(position.legs[i/4][i%4])
            i += 1

        self.set_position_multiple(0, *pulse_widths)

    def go_home(self):
        """Return all servos to "home" position.
        """
        cmd = chr(0xaa) + chr(0x0c) + chr(0x22)
        self.serial.write(cmd)

    def set_position_multiple(self, first_servo, *pulse_widths):
        """Set position of multiple servos, starting at first servo, going to
        pulse_widths.length servos. Uses raw pulse width.
        """
        num_targets = len(pulse_widths)
        if first_servo+num_targets > 24:
            print "Too many servo targets."
            return

        #We must determine if the servo range straddles both of the chained Maestro's.
        #If so, we have to fiddle a bit to make sure we send the correct commands to
        #each one.
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
            if (pulse_width < 736 or pulse_width > 2272) and pulse_width != 0:
                print "Pulse width outside of range [736, 2272] for controller 12", pulse_width
                return

            pulse_width = int(pulse_width) * 4

            low_bits = pulse_width & 0x7f
            high_bits = (pulse_width >> 7) & 0x7f
            target_bits.append(low_bits)
            target_bits.append(high_bits)

        cmd = chr(0xaa) + chr(device&0xff) + chr(0x1f) + chr((targets1)&0xff) + chr(channel)
        for byte in target_bits:
            cmd += chr(byte)

        if both_devices is True:
            target_bits2 = []
            channel2 = 0
            for pulse_width in pulse_widths[12-first_servo:]:
                if (pulse_width < 736 or pulse_width > 2272) and pulse_width != 0:
                    print "Pulse width outside of range [736, 2272] for controller 13", pulse_width
                    return

                pulse_width = int(pulse_width) * 4

                low_bits = pulse_width & 0x7f
                high_bits = (pulse_width >> 7) & 0x7f
                target_bits2.append(low_bits)
                target_bits2.append(high_bits)

            cmd2 = chr(0xaa) + chr(0x0d) + chr(0x1f) + chr((targets2)&0xff) + chr(channel2)
            for byte in target_bits2:
                cmd2 += chr(byte)
            self.serial.write(cmd2)

        self.serial.write(cmd)

    def get_position(self, servo):
        """Return two hex bytes, representing the position of servo as
        pulse width * 4 per maestro protocol.
        """
        self.serial.flushInput()
        if servo < 12:
            device = 12
        else:
            device = 13
            servo = servo - 12
        channel = servo &0x7F
        cmd = chr(0xaa) + chr(device) + chr(0x10) + chr(channel)
        self.serial.write(cmd)
        byte1 = self.serial.read()
        byte2 = self.serial.read()
        self.serial.flushInput()

        if len(byte1) < 1 or len(byte2) < 1:
            return None
        if ord(byte2) > 35:
            return None

        return int((ord(byte1) | (ord(byte2) << 8)) / 4)

    def get_servos_moving(self):
        """Returns true if any servos are moving, false otherwise.
        """
        cmd1 = chr(0xaa) + chr(0x0c) + chr(0x13)
        self.serial.write(cmd1)
        byte = self.serial.read()
        if len(byte) > 0 and ord(byte) == 1:
            return True

        # cmd2 = chr(0xaa) + chr(0x0d) + chr(0x13)
        # self.serial.write(cmd2)
        # byte = self.serial.read()
        # if len(byte) > 0 and ord(byte) == 1:
        #     return True

        return False

    def get_errors(self, device):
        cmd = chr(0xaa) + chr(device) + chr(0x21)
        self.serial.write(cmd)
        response = self.serial.read(size=2)
        if len(response) < 2:
            print "Get Error had a read error."
            self.serial.flushInput()

        print response.encode("hex")

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

    def test_get_position(self):
        """Test get_position on chained maestro.
        """
        i = 0
        timeout_count = 0

        while i < 100:
            position = self.get_position(11)
            if position is None:
                timeout_count += 1

            i += 1

        print "Num failures: ", timeout_count

class ServoPositions(object):
    """Holds the positions for 24 legs, and the safe routes required to
    navigate there.
    """
    def __init__(self, legs):
        self.legs = legs
        self.safe_routes = set()

    def __sub__(self, other):
        #We want the absolute value of the difference of each matched servo. This
        #is essentially the distance each servo is traveling. We use this to determine
        #speed and acceleration values later on.
        abs0 = [abs(a - b) for a, b in zip(self.legs[0], other.legs[0])]
        abs1 = [abs(a - b) for a, b in zip(self.legs[1], other.legs[1])]
        abs2 = [abs(a - b) for a, b in zip(self.legs[2], other.legs[2])]
        abs3 = [abs(a - b) for a, b in zip(self.legs[3], other.legs[3])]
        abs4 = [abs(a - b) for a, b in zip(self.legs[4], other.legs[4])]
        abs5 = [abs(a - b) for a, b in zip(self.legs[5], other.legs[5])]

        return ServoPositions([abs0, abs1, abs2, abs3, abs4, abs5])

    def __str__(self):
        return str(self.legs)

def get_serial(tty, baud):
    """Retrieve and open UART connection to maestro controllers.
    """
    ser = serial.Serial()
    ser.port = tty
    ser.baudrate = baud
    ser.timeout = 0.5
    ser.open()
    return ser

def time_to_speed_accel(anim_time, distance, initial_velocity):
    """Convert an animation time over a certain distance with an initial velocity
    to a speed and acceleration based on the Maestro protocol.
    """
    half_time = float(anim_time)/2
    half_distance = distance/2.0

    accel = (2.0*(half_distance-(initial_velocity*half_time))) / (half_time**2)
    max_speed = initial_velocity + (accel * half_time)

    accel = accel * 10 * 80 / 0.25 + 0.5
    max_speed = max_speed * 10 / 0.25 + 0.5

    #Since a speed and acceleration of 0 is basically uncapped according to the
    #Maestro protocol, we set the minimum to be one.
    return int(max(max_speed, 1)), int(max(accel, 1))

def find_common_route(routes1, routes2):
    """Given two sets of safe routes, return an arbitrary safe route in common.
    """
    common_routes = routes1 & routes2

    if len(common_routes) > 0:
        return common_routes.pop()

    return "park"

if __name__ == "__main__":
    MAESTRO = MaestroController()

    print "Animate EXTEND"
    MAESTRO.animate("extend", [1500]*6)

    while MAESTRO.get_servos_moving() is True:
        sleep(0.01)

    print "Animate PARK"
    MAESTRO.animate("park", [1500]*6)
