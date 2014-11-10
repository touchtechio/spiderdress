import cmd
import maestro_controller 

class Spider(cmd.Cmd):
    ''' A command line interface for testing maestro servo driving '''

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.maestro = maestro_controller.MaestroController()

    def do_set_position(self, line):
        '''set_position [servo] [angle]
         Moves leg of specified servo 0-11 to specified angle between 0-180 '''
        
        args = line.split()
        servo = int(args[0])
        angle = int(args[1])

        self.maestro.set_position(servo, angle)

    def do_set_position_multiple(self, line):
        '''set_position_multiple [servo] [angles]
        Moves leg of servos starting at [servo] to specified angles between 0-180 '''

        args = line.split()
        servo = int(args.pop(0))
        self.maestro.set_position_multiple(servo, *args)

    def do_get_position(self, line):
        '''get_position [servo],
                        get position of specified servo 1 - 12'''
        servo = int(line.split()[0])
        print self.maestro.get_position(servo)

if __name__ == '__main__':
    Spider().cmdloop()
