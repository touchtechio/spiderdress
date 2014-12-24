import cmd
from multiprocessing import Process, Value
from time import time
import maestro_controller
import respiration
import proximity

class Spider(cmd.Cmd):
    ''' A command line interface for testing maestro servo driving '''

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.maestro = maestro_controller.MaestroController()
        self.proxemic = proximity.Proxemic(proximity.Proximity.DEFAULT_CHANNELS)
        self.respiration = respiration.Respiration()
        self.color = [255, 255, 180]

    def do_set_position_multiple(self, line):
        '''set_position_multiple [servo] [angles]
        Moves leg of servos starting at [servo] to specified angles between -75 to 75 '''

        args = line.split()
        servo = int(args.pop(0))
        self.maestro.set_position_multiple(servo, *args)

    def do_disable_servos(self, line):
        self.maestro.set_position_multiple(0, *([0]*24))

    def do_get_position(self, line):
        '''get_position [servo],
                        get position of specified servo 1 - 12'''
        servo = int(line.split()[0])
        print self.maestro.get_position(servo)

    def do_set_speed(self, line):
        '''set_speed [servo] [speed]
        Sets [speed] of [servo]. '''
        args = line.split()
        servo = int(args[0])
        speed = int(args[1])

        self.maestro.set_speed(servo, speed)

    def do_set_accel(self, line):
        '''set_accel [servo] [accel]
        Sets [accel] of [servo]. Valid [accel] range from 0-255. '''
        args = line.split()
        servo = int(args[0])
        accel = int(args[1])

        self.maestro.set_accel(servo, accel)

    def do_get_moving(self, line):
        '''get_moving
        '''
        self.maestro.get_servos_moving()

    def do_get_errors(self, line):
        '''get_error
        '''

        args = line.split()
        device = int(args[0])

        self.maestro.get_errors(device)

    def do_animate(self, line):
        '''animate [script_name][speed_final]
        Sets the position of all servos to [script_name] at [speed_final].'''
        args = line.split()
        script_name = args[0]
        speed_final = int(args[1])

        self.maestro.animate(script_name, [speed_final]*6)

    def do_animation(self, line):
        '''animation [animation_name]
        Runs through the animation [animation_name]'''
        args = line.split()
        animation_name = args[0]

        self.maestro.animation(animation_name)

    def do_start_ces_interaction(self, line):
        '''start_ces_interaction
        Start proximity sensor that will interact with the legs and the lights.'''
        self.maestro.start_ces_animation()
        self.proxemic.monitor_space(self.maestro.prox_space_listener, self.maestro.prox_distance_listener)
        self.respiration.monitor_respiration(self.maestro.respiration_listener)

    def do_stop_ces_interaction(self, line):
        '''stop_ces_interaction
        Stop proximity sensor and interaction.'''
        self.maestro.stop_ces_animation()
        self.respiration.stop_monitor()

    def do_test_get_position(self, line):
        '''test_get_position
        Test Maestro's get position on chained Maestro.'''
        self.maestro.test_get_position()

if __name__ == '__main__':
    Spider().cmdloop()
