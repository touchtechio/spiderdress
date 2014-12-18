import cmd
from multiprocessing import Process, Value
from time import time
import maestro_controller
import teensy
import proximity
import pubsub

class Spider(cmd.Cmd):
    ''' A command line interface for testing maestro servo driving '''

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.maestro = maestro_controller.MaestroController()
        self.teensy = teensy.Teensy()
        self.proxemic = proximity.Proxemic(proximity.Proximity.DEFAULT_CHANNELS)
        self.color = [255, 255, 180]

        pubsub.subscribe(self.maestro.prox_sensor_listener, "proximity_data")
        #TODO: subscribe with teensy here

        self.prox_continue = Value('d', True)
        self.prox_process = Process(target=prox_worker)

    def do_set_position_multiple(self, line):
        '''set_position_multiple [servo] [angles]
        Moves leg of servos starting at [servo] to specified angles between -75 to 75 '''

        args = line.split()
        servo = int(args.pop(0))
        self.maestro.set_position_multiple(servo, *args)

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

    def do_animate(self, line):
        '''animate [script_name] [speed_safe] [speed_final]
        Sets the position of all servos to [script_name] at [speed_safe] and [speed_final].'''
        args = line.split()
        script_name = args[0]
        speed_safe = int(args[1])
        speed_final = int(args[2])

        self.maestro.animate(script_name, [speed_safe]*6, [speed_final]*6)

    def do_animation(self, line):
        '''animation [animation_name]
        Runs through the animation [animation_name]'''
        args = line.split()
        animation_name = args[0]

        self.maestro.animation(animation_name)

    def do_start_ces_interaction(self, line):
        '''start_ces_interaction
        Start proximity sensor that will interact with the legs and the lights.'''
        self.prox_process.start()

    def do_stop_ces_interaction(self, line):
        '''stop_ces_interaction
        Stop proximity sensor and interaction.'''
        self.prox_continue.value = False
        self.prox_process.join()

def prox_worker(self):
    current_space = None
    current_space_time = 0

    while self.prox_continue.value:
        space, distance = self.proxemic.get_space_distance(3, 20)
        now = time()

        if space == current_space:
            if now - current_space_time < 0.33:
                continue
        else:
            current_space = space
            current_space_time = now
            pubsub.send_message("proximity_data", space=space, distance=distance)
            continue

if __name__ == '__main__':
    Spider().cmdloop()
