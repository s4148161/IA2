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
    
    def __init__(self, DATABASE, userid):
        super().__init__()
        self.DATABASE = DATABASE
        self.robotid = userid 
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
        #The if statements create the colours dictionary with the number of each colour block

        self.SOUND.load_mp3('static/music/missionimpossible.mp3')

        while self.routine == 'automated_search' and time.time() < endtime:
            detection_colours = CreateDetectionColours(colours) #uses function above to get colours still being looked for
            robotid = self.robotid

            while len(detection_colours) > 0: #loop continues until there are no blocks left
                starttime = time.time()
                data = self.move_direction_until_detection(movetype='turnright',distanceto=250,detection_types=['colour'],detection_colours=detection_colours,timelimit=2,confirmlevel=1)
                self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Move Direction Until Detection", data, "Turn Left", starttime, time.time(), "Yes"))
                #The robot moves around to the right looking for the required colours
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
                    starttime = time.time()
                    data = self.move_toward_colour_detected(colour=found)
                    self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Move Direction Until Detection", data, "Turn Left", starttime, time.time(), "Yes"))
                    if self.routine != 'automated_search':
                        break
                    starttime = time.time()
                    self.look_down()
                    self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Look Down", data, "Look Down", starttime, time.time(), "Yes"))
                    time.sleep(1)
                    starttime = time.time()
                    data = self.move_toward_colour_detected(colour=found) #Moves toward the block
                    self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Move Toward Colour Detected", data, "Forward", starttime, time.time(), "Yes"))

                    if self.routine != 'automated_search':
                        break

                    starttime = time.time()
                    data = self.rotate_arm_until_colour_detected_is_centered(colour=found)
                    self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Rotate Arm Until Colour Detected is Centered", data, "Rotate Arm", starttime, time.time(), "Yes"))
                    
                    starttime = time.time()
                    data = self.pick_up_centered_object_with_look_down(data['y'])
                    #The robot moves toward the coloured block it has detected, centres the arm and attempts a pickup
                    self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Pick Up Centred Object with Look Down", data, "Pick Up", starttime, time.time(), (self.was_object_pickup_successful())['success']))

                    while (self.was_object_pickup_successful(colour=found, timelimit=1))['success'] == False: #This loop checks if the block has been picked up and if it has not it repeats until it has been
                        if self.routine != 'automated_search':
                            break
                        starttime = time.time()
                        data = self.move_toward_colour_detected(colour=found) #Moves toward the block
                        self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Move Toward Colour Detected", data, "Forward", starttime, time.time(), "Yes"))

                        starttime = time.time()
                        data = self.rotate_arm_until_colour_detected_is_centered(colour=found)
                        self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Rotate Arm Until Colour Detected is Centered", data, "Rotate Arm", starttime, time.time(), "Yes"))

                        starttime = time.time()
                        data = self.pick_up_centered_object_with_look_down(data['y']) #attempts the pickup again after recentering the block
                        self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Pick Up Centred Object with Look Down", data, "Pick Up", starttime, time.time(), (self.was_object_pickup_successful())['success']))

                    starttime = time.time()
                    data = self.look_up_closed() #once the block is in the arms it looks up
                    self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Look Up", data, "Look Up", starttime, time.time(), "Yes"))

                    starttime = time.time()
                    data = self.move_direction_until_detection(movetype='turnright',distanceto=250,detection_types=['colour'],detection_colours=['white'],timelimit=3,confirmlevel=1)
                    self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Move direction untill detection", data, "Turn Right", starttime, time.time(), "Yes"))

                    starttime = time.time()
                    data = self.move_toward_colour_detected(colour='white')
                    self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Move Toward Colour Detected", data, "Forward", starttime, time.time(), "Yes"))

                    time.sleep(1)

                    starttime = time.time()
                    data = self.move_toward_colour_detected(colour='white')
                    self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Move Toward Colour Detected", data, "Forward", starttime, time.time(), "Yes"))

                    starttime = time.time()
                    data = self.look_up() #Moves to the yellow mat and drops the block
                    self.DATABASE.ModifyQuery("INSERT INTO actions (robotid, command, detectiondata, movementtype, starttime, endtime, success) VALUES (?,?,?,?,?,?,?)", (robotid, "Reset Arm", data, "Reset Arm", starttime, time.time(), "Yes"))
                    colours[found] -= 1 #removes a block from the dictionary of block amounts then repeats until all of the blocks are picked up
                else:
                    #if after the search the robot does not find any blocks from the selected colours it will end the mission
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
    ROBOT = Robot(None,None)
    ROBOT.stop()
    input("Press enter to begin testing:")
    ROBOT.automated_search()

