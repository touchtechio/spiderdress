import cmd
import maestro_controller 

class Spider(cmd.Cmd):
    ''' A command line interface for testing maestro servo driving '''

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.maestro = maestro_controller.MaestroController()

    def do_set_position(self, line):
        '''set_position [servo] [angle]
         Moves leg of specified servo to specified angle between 0 to 180 '''
        
        args = line.split()
        servo = int(args[0])
        angle = int(args[1])

        self.maestro.set_position(servo, angle) 
        self.maestro.get_position(servo)

if __name__ == '__main__':
    Spider().cmdloop()
