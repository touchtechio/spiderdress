import cmd
import sys
from time import time, sleep
import teensy 

class TeensyTester(cmd.Cmd):
    ''' A command line interface for driving teensy lights '''

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.teensy = teensy.Teensy() 

    def do_set_color(self, line):
        '''set_color [r] [g] [b]
         Sets color on neopixel strip. RGB values are 0 - 255 '''
        
        args = line.split()
        r = int(args[0])
        g = int(args[1])
	b = int(args[2])

        self.teensy.set_color(r, g, b)

    def do_set_leds_off(self, line):
        '''set_leds_off 
         Turns strip off. '''

	self.teensy.set_off()

    def do_set_animation(self, line):
        '''set_animation [id],
                        tell teensy to play animation identified with id argument
                        where id is 0 for park, 1 for territorial, 2 for point'''
	args = line.split()	
	self.teensy.set_animation(int(args[0]))

    def do_set_proximity_leds(self, line):
        args = line.split()
        self.teensy.set_proximity_leds(int(args[0]))

if __name__ == '__main__':
    TeensyTester().cmdloop()
