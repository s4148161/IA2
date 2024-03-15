# This is where your main robot code resides. It extendeds from the BrickPi Interface File
# It includes all the code inside brickpiinterface. 
# The self.command and self.Routine are important because they can keep track of robot functions and commands. 
# Remember Flask is using Threading (e.g. more than once process which can confuse the robot)
from interfaces.robotinterface import RobotInterface
import logging, sys, os, time

class Robot(RobotInterface): 
    
    def __init__(self, DATABASE):
        super().__init__()
        self.DATABASE = DATABASE
        self.routine = "Ready" #use this stop or start routines
        return
     
    # Write a function for automated search, pickup and putdown, and save instructions to the database
    def automated_search(self,red=0,green=0,blue=0,timelimit=300):
        self.routine = 'automated_search'
        self.logger.info('Beginning Automated Search')
        endtime = time.time() + timelimit

        total_red = 0
        total_green = 0
        total_blue = 0
        self.SOUND.load_mp3('static/music/missionimpossible.mp3')

        while self.routine == 'automated_search' and time.time() < endtime:
            self.SOUND.say('Searching for the colour red')
            self.look_up()
            data = self.move_direction_until_detection(movetype='turnleft',distanceto=250,detection_types=['colour'],detection_colours=['red'],timelimit=5,confirmlevel=1)
            print(data)
            found = False
            if 'red' in data['detect_colour']:
                if 'found' in data['detect_colour']['red']:
                    found = True

            self.stop()
            if found:
                data = self.move_toward_colour_detected(colour='red')
                self.look_down()
                data = self.move_toward_colour_detected(colour='red')
                data = self.rotate_arm_until_colour_detected_is_centered('red')
                print(data)
                #data = self.pick_up_centred_object_with_lookdown(y)
            else:
                print("no red")


            self.logger.info(data) 
            break

        return

    def stop_automated_search(self):
        self.routine = 'ready'
        return

    
# Only execute if this is the main file, good for testing code
if __name__ == '__main__':
    ROBOT = Robot(None)
    ROBOT.stop()
    input("Press enter to begin testing:")
    ROBOT.automated_search()
