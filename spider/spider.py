import sys
from multiprocessing import Process, Value
from time import sleep

import maestro_controller
import respiration
import proximity
import button

NO_MOVE_MODE = 0
CES_MODE = 1
SLOW_BREATHE_MODE = 2

class Spider(object):
    def __init__(self, leg_file):
        self.leg_file = leg_file
        self.mode = NO_MOVE_MODE

        self.maestro = maestro_controller.MaestroController(leg_file)
        self.proxemic = proximity.Proxemic(proximity.Proximity.DEFAULT_CHANNELS)
        self.respiration = respiration.Respiration()
        self.button = button.Button()
        self.start_mode_flag = Value('b', False, lock=True)

        self.no_move_process = None
        self._no_move_continue = Value('b', False, lock=True)

    def start(self):
        self.button.monitor_button(self._button_listener)
        self._start_mode()

        while True:
            if self.start_mode_flag.value:
                self.start_mode_flag.value = False

                self._stop_mode()

                if self.mode == NO_MOVE_MODE:
                    self.mode = SLOW_BREATHE_MODE
                elif self.mode == SLOW_BREATHE_MODE:
                    self.mode = CES_MODE
                else:
                    self.mode = NO_MOVE_MODE

                self._start_mode()

    def stop(self):
        self._stop_mode()

    def _start_mode(self):
        if self.mode == NO_MOVE_MODE:
            self._no_move_continue.value = True
            self.no_move_process = Process(target=self._no_move_process)
            self.no_move_process.start()
        elif self.mode == CES_MODE:
            self.maestro.start_ces_animation()
            self.proxemic.monitor_space(
                self.maestro.prox_space_listener, self.maestro.prox_distance_listener)
            self.respiration.monitor_respiration(self.maestro.respiration_listener)
        elif self.mode == SLOW_BREATHE_MODE:
            self.maestro.start_slow_breathe_mode()

    def _stop_mode(self):
        if self.mode == NO_MOVE_MODE:
            self._no_move_continue.value = False
            self.no_move_process.join()
        elif self.mode == CES_MODE:
            self.maestro.stop_ces_animation()
            self.respiration.stop_monitor()
        elif self.mode == SLOW_BREATHE_MODE:
            self.maestro.stop_slow_breathe_mode()

    def _button_listener(self):
        self.start_mode_flag.value = True

        return True

    def _no_move_process(self):
        while self._no_move_continue.value:
            sleep(2)

def main(args):
    spider = Spider(args[0])
    spider.start()

if __name__ == '__main__':
    main(sys.argv[1:])
