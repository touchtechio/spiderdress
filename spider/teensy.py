#!/usr/bin/python

from edi2c.i2c import I2CDevice
import sys
from time import time, sleep

# Constants defining communication protocol with teensy
OFF = 0x00 
COLOR = 0x01
BRIGHTNESS = 0x02
ANIMATION = 0x03 
LED_COUNT = 0x04
PROXIMITY = 0x05

# Animation IDs
PARK = 0 
TERRITORIAL = 1 
POINT = 2 
GLOW = 3
GLOW_SLOW = 4

class Teensy():
  def __init__(self):
   # Initialize I2C device using the default address
    self.dev = I2CDevice(0x04, debug=True)

  def set_brightness(self, value):
    self.send_command(BRIGHTNESS, [value])

  def set_pixel_count(self, count):
    self.send_command(LED_COUNT, [count]);

  def set_color(self, r=0, g=0, b=127):
    self.send_command(COLOR, [r, g, b]) 
  
  def set_off(self):
    self.send_command(OFF, [])

  def set_animation(self,id):
    self.send_command(ANIMATION, [id])

  def set_proximity_leds(self, led_count):
    self.send_command(PROXIMITY, [led_count])
   
  def send_command(self, cmd, args):
    print args
    self.dev.write_list(cmd, args)


