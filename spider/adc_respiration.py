"""Get data from ADC channel(s)
"""
import sys
import time


from edi2c import ads1x15



adc = ads1x15.ADS1X15(ic=ads1x15.IC_ADS1115)
s= 'Positive Breathe'


pga = 4096
sps = 250
logfile = open('respiration_data.txt', 'w')

def logdata():

        while True:
                volts = -1*adc.read_single_ended(0,pga,sps)/1000
                #print "%.6f" % (volts)
                #v = str(volts)
                #logfile.write(s)
                logfile.write("\n")
                if volts <= 3.0:
                        print s
                        logfile.write(s)



                time.sleep(1)


logdata()
logfile.close()



