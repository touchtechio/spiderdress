"""Get data from ADC channel(s)
"""
import sys
import time

from edi2c import ads1x15

def read(adc, channel, pga=6144, sps=3300):
    return adc.read_single_ended(channel, pga, sps)

def main(args):
    if len(args) <= 0:
        print >>sys.stderr, "usage:", sys.argv[0], "<channel>", "[channel]", "[...]"
        return

    channels = map(int, args) or [0]
    adc = ads1x15.ADS1X15(ic=ads1x15.IC_ADS1115)

    while True:
        print "\t".join(str(round(read(adc, channel))) for channel in channels), " "*70, "\r",
        sys.stdout.flush()

if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
    sys.exit(0)
