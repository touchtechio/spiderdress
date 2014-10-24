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
            print "Angle outside of range [0-180]"
            return

        low_bits = pulse_width & 0x7f
        high_bits = (pulse_width >> 7) & 0x7f
        channel = servo & 0x7F
        cmd = chr(0xaa) + chr(0x0c) + chr(0x04) + chr(channel) + chr(low_bits) + chr(high_bits)
        self.serial.write(cmd)

    def get_position(self, servo):
        channel = servo &0x7F
        cmd = chr(0xaa) + chr(0x0c) + chr(0x10) + chr(channel)
        self.serial.write(cmd)
        w1 = self.serial.read()
        w2 = self.serial.read()
        return hex(ord(w1)), hex(ord(w2))

    def translate(self, angle):
        # min_pulse and max_pulse have been determined by testing since
        # we don't have a data sheet for these servos. 0x0FFF is the
        # minimum, while 0x1EE1 is the maximum. These have been converted
        # to integers.
        min_pulse, max_pulse = 4095, 7905
        min_angle, max_angle = 0, 180
        if angle < min_angle or angle > max_angle:
            return -1

        val = (angle * (max_pulse-min_pulse)) / max_angle + min_pulse
        return int(val)

if __name__ == '__main__':
    maestro = MaestroController()
    
    try:
        for x in range (0, 4):
            print 'Turning servo %d' % (x)
            #0 to 254 are valid target values
            #where 0 is ~ 0 degress and 127 ~90 degrees
	    #and 254 is ~180 degress
            maestro.set_position(x, 90)
            print maestro.get_position(x)
            #maestro.go_home()
            time.sleep(.05)
            print maestro.get_position(x)

    except Exception, e:
        print e
    except KeyboardInterrupt:
        print
 
