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
        target = int(254 * angle / 180)
        cmd = chr(0xFF) + chr(servo) + chr(target)
        self.serial.write(cmd)

    def get_position(self, servo):
       channel = servo &0x7F
       cmd = chr(0xaa) + chr(0x0c) + chr(0x10) + chr(channel)
       self.serial.write(cmd)
       w1 = self.serial.read()
       w2 = self.serial.read()
       return w1, w2


if __name__ == '__main__':
    maestro = MaestroController()
    
    try:
        for x in range (0, 4):
            print 'Turning servo %d' % (x)
            #0 to 254 are valid target values
            #where 0 is ~ 0 degress and 127 ~90 degrees
	    #and 254 is ~180 degress
            maestro.set_position(x, 60)
            print maestro.get_position(x)
            maestro.go_home()
            time.sleep(.05)
            print maestro.get_position(x)

    except Exception, e:
        print e
    except KeyboardInterrupt:
        print
 
