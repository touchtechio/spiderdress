#!/usr/bin/python

from edi2c.i2c import I2CDevice
import sys
from time import time, sleep

# Constants defining communication protocol with teensy
OFF = 0x00 
COLOR = 0x01
ANIMATION = 0x02 
LED_COUNT = 0x03

# Animation IDs
PARK = 0 
TERRITORIAL = 1 
POINT = 2 

class Teensy():

  def __init__(self):
    # Initialize I2C device using the default address
    self.dev = I2CDevice(0x04, debug=True)

  def setPixelCount(self, count):
    self.send_command(LED_COUNT, count);

  def setColor(self, r=0, g=0, b=127):
    self.send_command(COLOR,[r, g, b]) 
  
  def setOff(self):
    self.send_command(OFF, [])

  def setAnimation(self,id):
    self.send_command(ANIMATION, [id])
  
  def send_command(self, cmd, args):
    self.dev.write_list(cmd, args)


