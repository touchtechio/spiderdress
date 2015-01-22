"""PositionProcessor
intent: create a faster means to recreating the leg position files when servos change

envisioned functions (mostly none are implemented):

load(file) : file of the servo positions per leg

calibrate() :: key in calibrations :
 left shoulder:: q-p, a-;
 right :: Q-P A-:

switch() : 
 prints new current mode

write() : 
 to new file

send() : 
 to maestro for previewing

print() :
 send current position data to screen

disable() :
 turns off servos
 ?? maestro ???


"""
import sys
from time import time, sleep
import random
from multiprocessing import Process, Value
from itertools import izip

import maestro_controller


INCREMENT = 50;

increments = [1, 2, 3, 5, 10, 25, 50, 100, 250];


class PositionProcessor(object):


    def __init__(self, leg_file):

        self.positions = {}

        self.setup_positions(leg_file)

        self.current_position = 0;
    
        self.servoIncrement = 50;
       
        self.is_live = False

        self.save_file = "positions_tmp";
        self.serial_device = "/dev/tty.usbserial-DA013V2V"
        self.serial_device = "/dev/tty.usbmodem00096261"
        self.serial_device = "/dev/tty.usbserial-A5027W3T"


        self.maestro = maestro_controller.MaestroController(self.save_file);






    def setup_positions(self, filename):
        """Setup predefined positions and their safe routes.
        """
        position_file = open(filename, "r")
        line = position_file.readline()
        while line != "":
            leg_positions = []

            #Position name
            position_name = line.rstrip('\n')

            #Read in the leg values
            for i in range(6):
                pos = position_file.readline().split(',')
                pos = [int(s) for s in pos]
                leg_positions.append(pos)

            self.positions[position_name] = ServoPositions(leg_positions)
            line = position_file.readline()

    def print_position(self, position_key):
        
        print self.positions[position_key];

    def go_live(self, filename):
        
        self.maestro = maestro_controller.MaestroController(filename);

        self.maestro.animate(self.positions.keys()[self.current_position], [1500]*6)



    def print_help(self):
        print "z   - quit";
        print "x,c - position switch";
        print "q-p - incr left servo pwm value";
        print "a-; - decr left servo pwm value";
        print "Q-P - update right servo pwm value";
        print "A-: - update right servo pwm value";
        print "1-9 - update increment for servo pwm value changes";
        print "v   - enter or exit live mode";
        print "n   - disable servos";
        print "m   - save positions file 'positions_tmp'";
        print "?   - print this help";



    def print_current_position(self):

        print " POSITION : " , self.current_position;
        print " POSITION KEYS : " , self.positions.keys()[self.current_position];

    def update_position(self, position_key, servo, direction):

        if servo < 0: 
            print "ERROR SERVO NUMBER OUT OF RANGE: ", servo;
            return;
        
        if servo >= 20: 
            print "ERROR SERVO NUMBER OUT OF RANGE: ", servo;
            return;

        legNumber = -1;

        servoLegStart = [0, 4, 6, 10, 14, 16];

        for i in range(len(servoLegStart)):  
            if servo >= servoLegStart[i]:
                legNumber = i;
            else : continue;
     
        servoOnLeg = servo - servoLegStart[legNumber];

        print "leg : " , legNumber;
        print "servoOnLeg : " , servoOnLeg;


        if direction :
            # increment
            self.positions[position_key].legs[legNumber][servoOnLeg] += self.servoIncrement;
        else :
            self.positions[position_key].legs[legNumber][servoOnLeg] -= self.servoIncrement;

        self.print_position(position_key);

    def write_positions(self, filename):
        print "Opening the file..."
        target = open(filename, 'w')



        for key in self.positions.keys():
            target.write(key)
            target.write("\n")  
            for i in range(6):
                for j in range(4):
                    target.write(str(self.positions[key].legs[i][j]))
                    if j != 3 : target.write(",")      
                target.write("\n")  

        print "Opening the file..."

        target.close()



    def process_command(self, command):

        # Z is for quiting
        if command == 'z':
            return;
    
        # NEW_LINE is for help
        if ord(command) == 13:
            self.print_help();
            return;

        # ? is for help
        if command == '?':
            self.print_help();
            return;

        # m is for live mode
        if command == 'v':
            self.is_live = not self.is_live;
            if self.is_live:
                print "IS LIVE"
                self.go_live(self.save_file)
            else:
                print "SIMULATION"
            return;

        # n is for disabling 
        if command == 'n':
            print "DISABLE"

            return;

        # x and c switch position
        if command == 'x':
            self.current_position = self.current_position + len(self.positions.keys()) - 1; 
            self.current_position %= len(self.positions.keys());
            self.print_current_position();
            return;
        if command == 'c':
            self.current_position = self.current_position + 1; 
            self.current_position %= len(self.positions.keys());
            self.print_current_position();
            return;



        # change the increments by which the servo values are altered
        numericEntry = ord(command) - 48;   
        # x and c switch position
        if numericEntry > 0:
            if numericEntry < 10:
                print "numeric entry : " , numericEntry;
                self.servoIncrement = increments[numericEntry-1];
                print "increment : " , self.servoIncrement;
                return;
   
        #    
        # m - make a new file
        if command == "m":
            self.write_positions(self.save_file);
            return;
   

        #q-p a-; Q-P and A-: are for moving servos
        servoNumber = -1;
        moveUp = True;

        if command == 'q':
            servoNumber = 0; 
            moveUp = True;
        if command == 'a':
            servoNumber = 0; 
            moveUp = False;
        if command == 'w':
            servoNumber = 1; 
            moveUp = True;
        if command == 's':
            servoNumber = 1; 
            moveUp = False;
        if command == 'e':
            servoNumber = 2; 
            moveUp = True;
        if command == 'd':
            servoNumber = 2; 
            moveUp = False;
        if command == 'r':
            servoNumber = 3; 
            moveUp = True;
        if command == 'f':
            servoNumber = 3; 
            moveUp = False;
        if command == 't':
            servoNumber = 4; 
            moveUp = True;
        if command == 'g':
            servoNumber = 4; 
            moveUp = False;
        if command == 'y':
            servoNumber = 5; 
            moveUp = True;
        if command == 'h':
            servoNumber = 5; 
            moveUp = False;
        if command == 'u':
            servoNumber = 6; 
            moveUp = True;
        if command == 'j':
            servoNumber = 6; 
            moveUp = False;
        if command == 'i':
            servoNumber = 7; 
            moveUp = True;
        if command == 'k':
            servoNumber = 7; 
            moveUp = False;
        if command == 'o':
            servoNumber = 8; 
            moveUp = True;
        if command == 'l':
            servoNumber = 8; 
            moveUp = False;
        if command == 'p':
            servoNumber = 9; 
            moveUp = True;
        if command == ';':
            servoNumber = 9; 
            moveUp = False;


        if command == 'Q':
            servoNumber = 10; 
            moveUp = True;
        if command == 'A':
            servoNumber = 10; 
            moveUp = False;
        if command == 'W':
            servoNumber = 11; 
            moveUp = True;
        if command == 'S':
            servoNumber = 11; 
            moveUp = False;
        if command == 'E':
            servoNumber = 12; 
            moveUp = True;
        if command == 'D':
            servoNumber = 12; 
            moveUp = False;
        if command == 'R':
            servoNumber = 13; 
            moveUp = True;
        if command == 'F':
            servoNumber = 13; 
            moveUp = False;
        if command == 'T':
            servoNumber = 14; 
            moveUp = True;
        if command == 'G':
            servoNumber = 14; 
            moveUp = False;
        if command == 'Y':
            servoNumber = 15; 
            moveUp = True;
        if command == 'H':
            servoNumber = 15; 
            moveUp = False;
        if command == 'U':
            servoNumber = 16; 
            moveUp = True;
        if command == 'J':
            servoNumber = 16; 
            moveUp = False;
        if command == 'I':
            servoNumber = 17; 
            moveUp = True;
        if command == 'K':
            servoNumber = 17; 
            moveUp = False;
        if command == 'O':
            servoNumber = 18; 
            moveUp = True;
        if command == 'L':
            servoNumber = 18; 
            moveUp = False;
        if command == 'P':
            servoNumber = 19; 
            moveUp = True;
        if command == ':':
            servoNumber = 19; 
            moveUp = False;

        print "servo", servoNumber;
        if moveUp :
            print "UP";
        else :
            print "DOWN";

        self.print_current_position();

        print "increment : " , self.servoIncrement;

        self.update_position(self.positions.keys()[self.current_position], servoNumber, moveUp);




def _find_getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch





class ServoPositions(object):
    """Holds the positions for 24 legs, and the safe routes required to
    navigate there.
    """
    def __init__(self, legs):
        self.legs = legs
        self.safe_routes = set()

    def __sub__(self, other):
        #We want the absolute value of the difference of each matched servo. This
        #is essentially the distance each servo is traveling. We use this to determine
        #speed and acceleration values later on.
        abs0 = [abs(a - b) for a, b in zip(self.legs[0], other.legs[0])]
        abs1 = [abs(a - b) for a, b in zip(self.legs[1], other.legs[1])]
        abs2 = [abs(a - b) for a, b in zip(self.legs[2], other.legs[2])]
        abs3 = [abs(a - b) for a, b in zip(self.legs[3], other.legs[3])]
        abs4 = [abs(a - b) for a, b in zip(self.legs[4], other.legs[4])]
        abs5 = [abs(a - b) for a, b in zip(self.legs[5], other.legs[5])]

        return ServoPositions([abs0, abs1, abs2, abs3, abs4, abs5])

    def __str__(self):
        return str(self.legs)

def main(args):

    defaultFilename = "positions_dress_a"

    if len(args) > 0:
        filename = args[0];
    else:
        filename = defaultFilename;
        print "no file specified, using default"

    print "loading file : ", filename;

    processor = PositionProcessor(filename);

    print "PositionProcessor STARTed"

    print processor.positions["challenge"];

    print "loaded KEYS : ",  processor.positions.keys();

    #while processor.positions 

    getch = _find_getch();

    char = getch();
    while char != "z":
        char = getch();
        print char;
        # print ord(char);

        processor.process_command(char);

    print "done";
    
if __name__ == "__main__":
   main(sys.argv[1:])




