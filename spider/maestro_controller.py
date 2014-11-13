import serial
import time

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

        low_bits = pulse_width & 0x7f
        high_bits = (pulse_width >> 7) & 0x7f
        channel = servo & 0x7F
        cmd = chr(0xaa) + chr(0x0c) + chr(0x04) + chr(channel) + chr(low_bits) + chr(high_bits)
        self.serial.write(cmd)

    def set_position_multiple(self, first_servo, *angles):
        num_targets = len(angles)
        target_bits = []
        channel = int(first_servo) & 0x7f
        for angle in angles:
            angle = int(angle)
            pulse_width = self.translate(angle)
            if pulse_width == -1:
                print "Angle outside of range [-75, 75]"
                return

            low_bits = pulse_width & 0x7f
            high_bits = (pulse_width >> 7) & 0x7f
            target_bits.append(low_bits)
            target_bits.append(high_bits)

        cmd = chr(0xaa) + chr(0x0c) + chr(0x1f) + chr(num_targets&0xff) + chr(channel)
        for byte in target_bits:
            cmd += chr(byte)
        print ":".join("{:02x}".format(ord(c)) for c in cmd)
        self.serial.write(cmd)

    def get_position(self, servo):
        channel = servo &0x7F
        cmd = chr(0xaa) + chr(0x0c) + chr(0x10) + chr(channel)
        self.serial.write(cmd)
        w1 = self.serial.read()
        w2 = self.serial.read()
        return hex(ord(w1)), hex(ord(w2))

    def set_speed(self, servo, speed):
        channel = servo & 0x7f
        low_bits = speed & 0xff
        high_bits = (speed >> 8) & 0xff
        cmd = chr(0xaa) + chr(0x0c) + chr(0x07) + chr(channel) + chr(low_bits) + chr(high_bits)

        self.serial.write(cmd)

    def set_accel(self, servo, accel):
        channel = servo & 0x7f
        low_bits = accel & 0xff
        high_bits = (accel >> 8) & 0xff
        cmd = chr(0xaa) + chr(0x0c) + chr(0x09) + chr(channel) + chr(low_bits) + chr(high_bits)

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

if __name__ == '__main__':
    maestro = MaestroController()
    
    print "Testing servo 0..."
    maestro.set_position(0, 0)
    print "Return to neutral position..."
    time.sleep(1)

    maestro.set_position(0, -75)
    print "Move to -75 degrees..."
    time.sleep(1)

    maestro.set_position(0, 75)
    print "Move to 75 degrees..."
    time.sleep(1)

    maestro.set_position(0, 0)
    print "Return to neutral position... Test complete."