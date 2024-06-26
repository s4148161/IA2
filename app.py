from flask import *
from interfaces.databaseinterface import Database
from interfaces.hashing import *
from robot import Robot
import logging, time, sys

#---CONFIGURE APP---------------------------------------------------
app = Flask(__name__)
logging.basicConfig(filename='logs/flask.log', level=logging.INFO)
sys.tracebacklimit = 10
app.config['SECRET_KEY'] = "Type in a secret line of text"

#---EMBED OBJECTS---------------------------------------------------
DATABASE = Database("databases/db.db", app.logger)
ROBOT = None

#---VIEW FUNCTIONS----------------------------------------------------
# Backdoor 
@app.route('/backdoor')
def backdoor():
    results = ""
    if DATABASE:
        results = DATABASE.ViewQuery("SELECT * FROM users")
    return jsonify(results)

@app.route('/')
def missionredirect():
    return redirect('/mission') #redirect to the mission page

# Login as the admin user
@app.route('/login', methods=['GET','POST']) #allow both get and post methods to the route
def login():
    if 'userid' in session:
        return redirect('/') #if the user is already logged in redirect to the mission page

    error = ""
    if request.method == "POST": #user has submitted the form
        email = request.form['email']
        password = request.form['password'] #get email and password
    
        userlist = DATABASE.ViewQuery("SELECT * FROM users WHERE email = ?", (email,)) #get all users with matching email
        if not userlist:
            error = "No user exists with that email address" 
            return render_template("login.html", message=error) #return error to page
        else:
            user = userlist[0] #get the user from the sql query results
            p = user['password']
            if check_password(p, password) == False: #check if the hashed passwords match
                error = 'Password incorrect!'
            else:
                session['userid'] = user['userid']
                if email == "admin@admin":
                    session['permission'] = 'admin'
                else:
                    session['permission'] = 'user'

                return redirect('/mission') #after user has logged in redirect them to the mission page
            return render_template("login.html", message=error)
    else:
        return render_template("login.html", message=error) #render the login page

@app.route('/register', methods=['GET','POST'])
def register():
    if 'userid' in session:
        return redirect('/mission') #if the user is logged in return them to the mission page

    error = "Please register"
    if request.method == "POST": #if the form is submitted
        email = request.form['email'].strip()
        password = request.form['password']
        passwordconfirm = request.form['passwordconfirm']
        firstname = request.form['firstname'].strip()
        lastname = request.form['lastname'].strip() #gets all of the information from the form
        robotids = request.form['robotid'] 
        robotids = robotids.split(",") #splits the comma seperated robotids into an Array of Strings
        userlist = DATABASE.ViewQuery("SELECT * FROM users WHERE email = ?", (email,)) #get all users with the email

        if len(password) < 8: #check password length
            error = "Password is too short"
        elif userlist != False: #check if another user with that email exists
            error = "Another account with that email already exists"
        else:
            if passwordconfirm != password: #check to see if passwords match
                error = "Passwords do not match"
            else:
                DATABASE.ModifyQuery("INSERT INTO users (email, password, firstname, lastname) VALUES (?,?,?,?)", (email, hash_password(password), firstname, lastname))
                #inserts the new user into the database, hashing the password at the same time
                userid = DATABASE.ViewQuery("SELECT userid FROM users WHERE email = ?", (email,))
                session['userid'] = userid[0]['userid']
                #gets the userid that is generated by the database when the new user is created and adds it to the session

                for robot in robotids: #loops through all of the robotids provided in the form and adds them to the database
                    robotid = int(robot)
                    DATABASE.ModifyQuery("INSERT INTO robots (userid, robotid) VALUES (?,?)", (session['userid'], robotid))

                if email == "admin@admin":
                    session['permission'] = 'admin' #if the user is the admin add it to the session
                else:
                    session['permission'] = 'user'

                return redirect('./') #redirect the user to the home page if the login is successful

    return render_template("register.html", message=error) #render the register page


# Dashboard for the robot
@app.route('/mission', methods=['GET','POST'])
def mission():
    if 'userid' not in session: #redirect the user to the login page if they are not logged in
        return redirect('/login')
    loaded = 0
    if ROBOT:
        loaded = 1 #show the mission camera view and buttons if the robot is loaded
    return render_template('mission.html', robot_loaded=loaded)

#load the robot
@app.route('/load_robot', methods=['GET','POST'])
def load_robot():
    global ROBOT
    if not ROBOT:
        app.logger.info('Loading Robot')
        ROBOT = Robot(DATABASE, session['userid'])
        time.sleep(3) #takes 3 seconds to load the robot
    return jsonify({'message':'robot loaded'})

# YOUR FLASK CODE------------------------------------------------------------------------



@app.route('/maintenance', methods=['GET','POST'])
def maintenance():
    if 'userid' not in session: #redirect the user to the login page if they are not logged in
        return redirect('/')

    if request.method == "POST":
        robotid = request.form['robotid'] #if the form is submitted get all of the form contents
        date = request.form['date']
        problem = request.form['description']

        DATABASE.ModifyQuery("INSERT INTO maintenancelogs (userid, robotid, date, problem) VALUES (?,?,?,?)", (session['userid'], robotid, date, problem))
        #add the form contents to the database
    
    robotids = DATABASE.ViewQuery("SELECT robotid FROM robots WHERE userid = ?", (session['userid'],)) 
    #gets all of the robotids associated with the user to fill in the dropdown menu
    ids = []
    if robotids != False:
        for id in robotids:
            ids.append(id['robotid']) #reformat the ids to be used by Jinja templating

    problems = DATABASE.ViewQuery("SELECT * FROM maintenancelogs WHERE userid = ?", (session['userid'],))
    #gets all of the previous maintenance logs from the database

    return render_template('maintenance.html', ids=ids, problems=problems)

@app.route('/admin', methods=['GET','POST'])
def admin():
    if 'userid' in session and session['permission'] == 'admin': #if the user is not an admin redirect them to the home page
        results = ""
        if DATABASE:
            results = DATABASE.ViewQuery("SELECT * FROM users") #gets all of the user data and displays it in json form
        return jsonify(results)
    else:
        return redirect('/')

@app.route('/missionhistory', methods=['GET','POST'])
def missionhistory():
    if 'userid' not in session:  #redirect the user to the login page if they are not logged in
        return redirect('/')

    robotids = DATABASE.ViewQuery("SELECT robotid FROM robots WHERE userid = ?", (session['userid'],)) #gets all of the robots associated with the user
    missions = []
    actions = {}
    if robotids != False:
        for id in robotids:
            missionquery = DATABASE.ViewQuery("SELECT * FROM missions WHERE robotid = ?", (id['robotid'],)) #for each robot the user has look for all of its missions
            if missionquery != False:
                missions.append(missionquery[0]) #if there are any missions add them to the Array which is a better format for the flask templating
    for mission in missions:
        missionactions = DATABASE.ViewQuery("SELECT * FROM actions WHERE missionid = ?", (mission['missionid'],)) #get all of the actions associated with the missionid
        if missionactions != False: #if there are any actions add them to a dictionary with the missionid
            actions[mission['missionid']] = missionactions

    return render_template('missionhistory.html',missions=missions, actions=actions)

@app.route('/look_up', methods=['GET','POST'])
def look_up():
    app.logger.info('look up')
    if ROBOT:
        ROBOT.look_up() #tells the robot to look up
    return jsonify({'message':'look up'})

@app.route('/look_down', methods=['GET','POST'])
def look_down():
    app.logger.info('look down')
    if ROBOT:
        ROBOT.look_down() #tells the robot to look down
    return jsonify({'message':'look down'})

@app.route('/turn_right', methods=['GET','POST'])
def turn_right():
    app.logger.info('turn right')
    if ROBOT:
        ROBOT.rotate_speed_time(timelimit=2) #tells the robot to look down
    return jsonify({'message':'turn right'})

@app.route('/turn_left', methods=['GET','POST'])
def turn_left():
    app.logger.info('turn left')
    if ROBOT:
        ROBOT.rotate_speed_time(rotationspeed=-0.1, timelimit=2) #tells the robot to look down
    return jsonify({'message':'turn left'})

@app.route('/move_forward/<angle>', methods=['GET','POST'])
def move_forward(angle):
    app.logger.info('move forward') #makes the robot move forward or back depending on the <angle>
    angle = int(angle)
    if ROBOT:
        try:
            ROBOT.move_direction_time(timelimit=2, direction=angle)
        except:
            ROBOT.stop()
    return jsonify({'message':'move forward'})

@app.route('/stop', methods=['GET','POST'])
def stop():
    app.logger.info('stop')
    if ROBOT:
        ROBOT.stop() #tells the robot to stop
    return jsonify({'message':'stop'})

@app.route('/start_mission', methods=['GET','POST'])
def start_mission():
    app.logger.info('start mission')
    red_num = request.form['red_num']
    green_num = request.form['green_num']
    blue_num = request.form['blue_num'] #gets all of the form data from the mission page

    if ROBOT:
        try:
            ROBOT.automated_search(int(red_num), int(green_num), int(blue_num)) #starts the automated search with the numbers of blocks
        except Exception as e:
            print(e) #if there are any problems stop the search
            ROBOT.stop_automated_search()
            ROBOT.stop()
    return jsonify({'message':'starting mission'})


@app.route('/stop_mission', methods=['GET','POST'])
def stop_mission():
    app.logger.info('stop_mission')
    if ROBOT:
        ROBOT.stop_automated_search() #if the stop mission button is pressed tell the robot to stop the mission
    return jsonify({'message':'stopping mission'})





# CAMERA CODE-(do not touch!!)-------------------------------------------------------
# Continually gets the frame from the pi camera
def videostream():
    """Video streaming generator function."""
    while True:
        if ROBOT:
            frame = ROBOT.CAMERA.get_jpeg_frame() #can change quality to test efficiency
            if frame:
                yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                return '', 204
        else:
            return '', 204 

# Embeds the videofeed by returning a continual stream as above
@app.route('/videofeed')
def videofeed():
    if ROBOT:
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(videostream(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return '', 204

# Turn on detection mode
@app.route('/turn_on_detection', methods=['GET','POST'])
def turn_on_detection():
    app.logger.info('turn on detection')
    if ROBOT:
        ROBOT.CAMERA.detect_all(exclude_colours=['black'])
    return jsonify({'message':'Detection mode on!!'})

# Turn off detection mode
@app.route('/turn_off_detection', methods=['GET','POST'])
def turn_off_detection():
    app.logger.info('turn off detection')
    if ROBOT:
        ROBOT.CAMERA.end_detection()
    return jsonify({'message':'Detection mode off!!'})

# Log out
@app.route('/logout')
def logout():
    app.logger.info('logging off')
    session.clear()
    return redirect('/')

# Shut down the robot
@app.route('/shutdown_robot', methods=['GET','POST'])
def shutdown_robot():
    app.logger.info("Shut down robot")
    global ROBOT
    if ROBOT:
        ROBOT.CAMERA.stop()
        ROBOT.stop()
        time.sleep(0.5)
        ROBOT = None
    return jsonify({'message':'Shutting Down'})

# Exit the web server
@app.route('/exit', methods=['GET','POST'])
def exit():
    app.logger.info("Exiting")
    shutdown_robot()
    func = request.environ.get('werkzeug.server.shutdown')
    func()
    return jsonify({'message':'Exiting'})

#---------------------------------------------------------------------------
# main method called web server application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) #runs a local server on port 5000

