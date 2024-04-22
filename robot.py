# This is where your main robot code resides. It extendeds from the BrickPi Interface File
# It includes all the code inside brickpiinterface. 
# The self.command and self.Routine are important because they can keep track of robot functions and commands. 
# Remember Flask is using Threading (e.g. more than once process which can confuse the robot)
from interfaces.robotinterface import RobotInterface
import logging, sys, os, time

def CreateDetectionColours(colours):
    
    detection_colours = []

    for colour, count in colours.items():
        if count > 0:
            detection_colours.append(colour)
    # This loop goes through the number of each coloured block left and checks if there are any left and then if there is at least 1 it adds it to the list of colours being looked for in the move_direction_until_detection function

    return detection_colours

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
        self.look_up()

        endtime = time.time() + timelimit

        colours = {}

        if red > 0:
            colours['red'] = red

        if blue > 0:
            colours['blue'] = blue

        if green > 0:
            colours['green'] = green 

        self.SOUND.load_mp3('static/music/missionimpossible.mp3')

        while self.routine == 'automated_search' and time.time() < endtime:
            #self.SOUND.say('Searching')
            detection_colours = CreateDetectionColours(colours) #uses function above to get colours still being looked for

            while len(detection_colours) > 0: #loop continues until there are no blocks left
                data = self.move_direction_until_detection(movetype='turnright',distanceto=250,detection_types=['colour'],detection_colours=detection_colours,timelimit=2,confirmlevel=1)
                print(detection_colours, len(detection_colours))
                found = 'none' 
                
                if 'red' in data['detect_colour']:
                    if 'found' in data['detect_colour']['red']:
                        found = 'red'
                elif 'blue' in data['detect_colour']:
                    if 'found' in data['detect_colour']['blue']:
                        found = 'blue'
                elif 'green' in data['detect_colour']:
                    if 'found' in data['detect_colour']['green']:
                        found = 'green'
                #this figures out which colour has been detected and selects it for the following actions

                self.stop()
                if found != 'none':
                    #self.SOUND.say("Moving towards object")
                    print(detection_colours,found)
                    data = self.move_toward_colour_detected(colour=found)
                    if self.routine != 'automated_search':
                        break
                    self.look_down()
                    time.sleep(1)
                    data = self.move_toward_colour_detected(colour=found) #Moves toward the block

                    if self.routine != 'automated_search':
                        break

                    data = self.rotate_arm_until_colour_detected_is_centered(colour=found)
                    
                    data = self.pick_up_centered_object_with_look_down(data['y'])

                    data = self.rotate_arm_until_colour_detected_is_centered(colour=found)

                    while (self.was_object_pickup_successful(colour=found))['success'] == False:
                        if self.routine != 'automated_search':
                            break
                        data = self.move_toward_colour_detected(colour=found) #Moves toward the block

                        data = self.rotate_arm_until_colour_detected_is_centered(colour=found)

                        data = self.pick_up_centered_object_with_look_down(data['y'])
                        print(self.was_object_pickup_successful(colour=found))

                    #This loop will repeat aligning the arm with the block and attempting to pick it up
                    data = self.look_up_closed()
                    #SQL_QUERY("INSERT INTO missions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (self.id, "Look Up", data, "Look Up", starttime, time.time(), "Yes"))
                	#starttime = time.time()
                    data = self.move_direction_until_detection(movetype='turnright',distanceto=250,detection_types=['colour'],detection_colours=['white'],timelimit=2,confirmlevel=1)

                    data = self.move_toward_colour_detected(colour='white')
                    #SQL_QUERY("INSERT INTO missions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (self.id, "Move Toward Colour Detected", data, "Forward", starttime, time.time(), "Yes"))
                    time.sleep(1)
                	#starttime = time.time()
                    data = self.move_toward_colour_detected(colour='white')
                    #SQL_QUERY("INSERT INTO missions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (self.id, "Move Toward Colour Detected", data, "Forward", starttime, time.time(), "Yes"))
                	#starttime = time.time()
                    data = self.reset_arm() #Moves to the yellow mat and drops the block
                    #SQL_QUERY("INSERT INTO missions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (self.id, "Reset Arm", data, "Reset Arm", starttime, time.time(), "Yes"))
                    colours[found] -= 1 #removes a block from the dictionary of block amounts
                else:
                    #self.SOUND.say('No colours detected') #if after the search the robot does not find any blocks from the selected colours it will end the mission
                    print("No colours detected")
                    break
                break
        self.routine = "ready"
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

'''
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
'''
