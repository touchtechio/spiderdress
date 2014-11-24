import cmd
import sys
from time import time, sleep
import teensy 

class TeensyTester(cmd.Cmd):
    ''' A command line interface for driving teensy lights '''

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.teensy = teensy.Teensy() 
        self.color = [255, 255, 180]

    def do_set_brightness(self, line):
        '''set_brightness [value]
        Sets brightness of strip 0 to 255 '''
        
        args = line.split()
        self.teensy.set_brightness(int(args[0]))

    def do_set_color(self, line):
        '''set_color [r] [g] [b]
         Sets color on neopixel strip. RGB values are 0 - 255 '''
        
        args = line.split()
        r = int(args[0])
        g = int(args[1])
	b = int(args[2])

        self.teensy.set_color([r, g, b])

    def do_set_count(self, line):
	args = line.split()
	self.teensy.set_pixel_count(int(args[0]))

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

    def do_set_intimate(self, line):
    	color = self.parse_color(line)
	self.teensy.set_intimate(color)

    def do_set_personal(self, line):
        color = self.parse_color(line)
	self.teensy.set_personal(color)
    
    def do_set_social(self, line):
	color = self.parse_color(line)
	print color
        self.teensy.set_social(color);

    def do_set_photoshoot(self, line='1'):
        args = line.split()
        self.teensy.set_photoshoot(int(args[0]))
    
    def parse_color(self, line):
        if not line:                                                             
          line = '255 255 180'                                                   
                                                    
        args = line.split()                         
        r = int(args[0])                            
        g = int(args[1])                            
        b = int(args[2]) 

        return [r, g, b]

if __name__ == '__main__':
    TeensyTester().cmdloop()
