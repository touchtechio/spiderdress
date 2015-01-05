"""Get data from ADC channel(s)
"""
import sys
from time import time, sleep
from multiprocessing import Process, Value

from edi2c import ads1x15

class Respiration(object):
    def __init__(self):
        self.adc = ads1x15.ADS1X15(ic=ads1x15.IC_ADS1115)

        self.pga = 6144
        self.sps = 250
        self._monitor_process = None
        self._continue_process = Value('b', False)

    def monitor_respiration(self, callback):
        self._monitor_process = Process(target=self._monitor_respiration, args=(callback, ))
        self._continue_process.value = True

        self._monitor_process.start()

    def stop_monitor(self):
        self._continue_process.value = False
        self._monitor_process.join()

    def _monitor_respiration(self, callback):
        time_last_callback = 0

        while self._continue_process.value:
            volts = self.adc.read_single_ended(1, self.pga, self.sps)/1000
            now = time()

            if volts >= 1.36 and volts < 4.5:
                if now - time_last_callback >= 2:
                    time_last_callback = now
                    callback()
            sleep(1)
