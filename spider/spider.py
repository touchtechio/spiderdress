import sys

import maestro_controller
import respiration
import proximity
import button

CES_MODE = 0
SLOW_BREATHE_MODE = 1

class Spider(object):
    def __init__(self, leg_file):
        self.leg_file = leg_file
        self.mode = SLOW_BREATHE_MODE

        self.maestro = maestro_controller.MaestroController(leg_file)
        self.proxemic = proximity.Proxemic(proximity.Proximity.DEFAULT_CHANNELS)
        self.respiration = respiration.Respiration()
        self.button = button.Button()

    def start(self):
        self.button.monitor_button(self._button_listener)
        self._start_mode()

    def stop(self):
        self._stop_mode()

    def _start_mode(self):
        if self.mode == CES_MODE:
            self.maestro.start_ces_animation()
            self.proxemic.monitor_space(
                self.maestro.prox_space_listener, self.maestro.prox_distance_listener)
            self.respiration.monitor_respiration(self.maestro.respiration_listener)
        else:
            self.maestro.start_slow_breathe_mode()

    def _stop_mode(self):
        if self.mode == CES_MODE:
            self.maestro.stop_ces_animation()
            self.respiration.stop_monitor()
        else:
            self.maestro.stop_slow_breathe_mode()

    def _button_listener(self):
        if self.mode == CES_MODE:
            self._stop_mode()

            self.mode = SLOW_BREATHE_MODE
            self._start_mode()
        else:
            self._stop_mode()

            self.mode = CES_MODE
            self._start_mode()

        return True

def main(args):
    spider = Spider(args[0])
    spider.start()

if __name__ == '__main__':
    main(sys.argv[1:])
