"""Provide proximity measurements.
"""
import sys
from time import time

from edi2c import ads1x15
import teensy


class Proximity:
    DEFAULT_CHANNELS=(2, 3)
    DEFAULT_VOLTAGE = 5.0
    DEFAULT_PGA = 6144
    DEFAULT_SPS = 250
    
    adc = None
    channels = None
    voltage = None
    pga = DEFAULT_PGA
    sps = DEFAULT_SPS

    def __init__(self, channels=DEFAULT_CHANNELS, voltage=DEFAULT_VOLTAGE, sps=DEFAULT_SPS):
        self.adc = ads1x15.ADS1X15(ic=ads1x15.IC_ADS1115)
        self.channels = channels
        self.voltage = float(voltage)
        self.sps = sps

        if len(channels) != 2:
            raise ValueError, "Proximity: only two channels are supported"


    def read_once(self):
        """Take a single reading from the channels.
        """
        result = []
        # pga should be 6144? verify the math here
        for channel in self.channels:
            value = self.adc.read_single_ended(channel, pga=self.pga, sps=self.sps) * 1024 / (1000 * self.voltage)
            result.append(int(round(value)))
        
        return result


    def read(self, filter_length=20, rejection_threshold_cm=40):
        """Take median filtered readings.
        """
        distances = ([], [])
        
        while filter_length >= 0:
            reading = self.read_once()
            distances[0].append(reading[0])
            distances[1].append(reading[1])
            filter_length -= 1

        medians = [0, 0]
        mean = 0

        for i, readings in enumerate(distances):
            # median filter
            readings.sort()
            median = readings[len(readings)/2]
            mean += median
            medians[i] = median

        mean /= float(len(distances))

        # TODO: use alternative median filtering? IEEE 05720809 when combining?
        
        # if we're beyond the rejection threshold and there are two or less sensors,
        # choose the reading from the sensor reporting a closer object (smaller value)
        
        for i, median in enumerate(medians):
            if abs(mean - median) >= rejection_threshold_cm:
                return float(medians[(i + 1) % 2])

        return mean


class Proxemic(Proximity):
    INTIMATE = 0
    PERSONAL = 1
    SOCIAL = 2
    PUBLIC = 3
    RANGE = [45, 120, 280, 720]
    
    def __init__(self, *args, **kwargs):
        Proximity.__init__(self, *args, **kwargs)

    def get_space_distance(self, filter_length=20, rejection_threshold_cm=40):
        distance = self.read(filter_length, rejection_threshold_cm)
        
        for i, limit in enumerate(Proxemic.RANGE):
            if distance <= limit:
                return i, distance
            
        return len(Proxemic.RANGE) - 1, distance


def main(args):
    channels = map(int, args) or Proximity.DEFAULT_CHANNELS
    pr = Proxemic(channels)
    
    tsy = None #teensy.Teensy()
    
    color_map = [ [255, 0, 0], [255, 255, 0], [0, 0, 255], [0, 0, 0] ]
    #function_map = [ tsy.set_intimate, tsy.set_personal, tsy.set_social, lambda x: tsy.set_off ]
    #do_function = lambda x: function_map[x]([255, 255, 180])
    
    current_color = None
    current_space = None
    current_space_time = 0
    
    while True:
        space, distance = pr.get_space_distance(3, 20)
        now = time()

        if space == current_space:
            if now - current_space_time < 0.33:
                continue
        else:
            current_space = space
            current_space_time = now
            #do_function(space)
            continue

        #color = color_map[space]
        #
        #if color != current_color:
        #    current_color = color
        #    tsy.set_color(color)
        #    tsy.set_proximity_leds(20)

        print int(round(distance)), "\t", space, " "*70, "\r",
        sys.stdout.flush()


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
    sys.exit(0)