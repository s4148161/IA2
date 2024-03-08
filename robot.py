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
            data = self.move_direction_until_detection(movetype='turnleft',distanceto=250,detection_types=['colour'],detection_colours=['red'],timelimit=2,confirmlevel=1)
            self.SOUND.say('Colour detected')
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
