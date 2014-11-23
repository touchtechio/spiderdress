"""Support for Maxbotix MB12xx series sensors attached to an ADS1x15 ADC.
"""
import sys

from edi2c import ads1x15

class Maxbotix:
    DEFAULT_VOLTAGE = 5
    
    adc = None
    voltage = None

    def __init__(self, voltage=DEFAULT_VOLTAGE):
        self.voltage = voltage
        self.adc = ads1x15.ADS1X15(ic=ads1x15.IC_ADS1115)

    def read_once(self, channel, sps=1600):
        """Take a single reading from channel.
        """
        # pga should be 6144? verify the math here
        value = self.adc.read_single_ended(channel, pga=6144, sps=sps) * 1024 / (1000 * self.voltage)
        return int(round(value))

    def read(self, channels, sps=1600, filter_length=20, rejection_threshold_cm=40):
        """Take reading from multiple sensors.
        
        Filtered with a median filter and difference-based rejection of samples.
        """
        readings = {n: [] for n in channels}
        
        # trash single readings that deviate or filtered?
        
        while filter_length >= 0:
            for channel in channels:
                distance = self.read_once(channel, sps=sps)
                readings[channel].append(distance)
            
            filter_length -= 1

        medians = {}
        devs = {}
        mean = 0

        for channel in channels:
            # median filter
            readings[channel].sort()
            count = len(readings[channel])
            median = readings[channel][count/2]
            mean += median
            medians[channel] = median
            devs[channel] = abs(median - sum(readings[channel])/float(count))

        if len(channels) <= 1:
            return mean

        mean /= float(len(channels))

        # TODO: use alternative median filtering? IEEE 05720809 when combining?
        
        # if we're beyond the rejection threshold and there are two or less sensors,
        # choose the reading from the channel whose median reading is closest to its mean reading.
        
        for channel, median in medians.items():
            if abs(median - mean) <= rejection_threshold_cm:
                del medians[channel]
                
                if len(medians) == 1:
                    channel_dev = devs[channel]
                    # choose between this reading and that one by picking the most consistent
                    other_channel = medians.iterkeys().next()
                    dev_other = devs[other_channel]
                    if dev_other < channel_dev:
                        return medians[other_channel]
                    else:
                        return median

        return int(round(sum(medians.values()) / float(len(medians))))

    def read_combined(self, sps=1600, filter_length=20, rejection_threshold_cm=40):
        pass

def main(args):
    channels = map(int, args) or [0]
    mb = Maxbotix()
    
    while True:
        print int(round(mb.read(channels) / 10.)) * 10

if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
    sys.exit(0)