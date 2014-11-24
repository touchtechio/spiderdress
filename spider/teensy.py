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
GLOW = 0 
GLOW_SLOW = 1 
HEARTBEAT = 2
SOLID = 3

class Teensy():
  def __init__(self):
   # Initialize I2C device using the default address
    self.dev = I2CDevice(0x04, debug=True)

  def set_brightness(self, value):
    self.send_command(BRIGHTNESS, [value])

  def set_pixel_count(self, count):
    self.send_command(LED_COUNT, [count]);

  def set_color(self, color):
    self.send_command(COLOR, color) 
  
  def set_off(self):
    self.send_command(OFF, [])

  def set_animation(self,id):
    self.send_command(ANIMATION, [id])

  def set_proximity_leds(self, led_count):
    self.send_command(PROXIMITY, [led_count])

  def set_intimate(self, color):
    self.set_off()
    self.set_color(color)
    self.set_animation(SOLID)

  def set_personal(self, color):
    self.set_off()
    self.set_color(color)
    self.set_animation(HEARTBEAT)
 
  def set_social(self, color):
    self.set_off()
    self.set_color(color)
    self.set_animation(GLOW)

  def set_photoshoot(self, index):
    self.set_off()
    if (index == 0):
      self.set_color([255, 255, 180])
    else:
      self.set_color([0, 0, 127])
 
    self.set_animation(SOLID)

  def send_command(self, cmd, args):
    print args
    self.dev.write_list(cmd, args)


