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
DATABASE = Database("databases/test.db", app.logger)
ROBOT = None

#---VIEW FUNCTIONS----------------------------------------------------
# Backdoor 
@app.route('/backdoor')
def backdoor():
    if DATABASE:
        results = DATABASE.ViewQuery("SELECT * FROM users")
    return jsonify(results)

# Login as the admin user
@app.route('/', methods=["GET","POST"])
def login():
    if 'userid' in session:
        return redirect('/mission')
    app.logger.info("Login")
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        session['permission'] = 'user'
        if email == 'admin@admin' and password == 'admin': 
            session['userid'] = 1
            session['permission'] = 'admin'

            return redirect('./mission') #takes 3 seconds for the CAMERA to start
    return render_template("login.html")

# Dashboard for the robot
@app.route('/mission', methods=['GET','POST'])
def mission():
    if not 'userid' in session:
        return redirect('/')
    loaded = 0
    if ROBOT:
        loaded = 1
    return render_template('mission.html', robot_loaded=loaded)

#load the robot
@app.route('/load_robot', methods=['GET','POST'])
def load_robot():
    global ROBOT
    if not ROBOT:
        app.logger.info('Loading Robot')
        ROBOT = Robot(DATABASE)
        time.sleep(3) #takes 3 seconds to load the robot
    return jsonify({'message':'robot loaded'})

# YOUR FLASK CODE------------------------------------------------------------------------


@app.route('/registration', methods=['GET','POST'])
def register():

    return render_template('registration.html')

@app.route('/maintenance', methods=['GET','POST'])
def maintenance():
    if 'userid' not in session:
        return redirect('/')

    return render_template('maintenance.html')

@app.route('/admin', methods=['GET','POST'])
def admin():
    if 'userid' not in session and session['permission'] != 'admin':
        return redirect('/')

    return render_template('admin.html')

@app.route('/missionhistory', methods=['GET','POST'])
def missionhistory():
    if 'userid' not in session:
        return redirect('/')

    return render_template('missionhistory.html')


@app.route('/look_up', methods=['GET','POST'])
def look_up():
    app.logger.info('look up')
    if ROBOT:
        ROBOT.look_up()
    return jsonify({'message':'look up'})

@app.route('/look_down', methods=['GET','POST'])
def look_down():
    app.logger.info('look down')
    if ROBOT:
        ROBOT.look_down()
    return jsonify({'message':'look down'})

@app.route('/move_forward/<angle>', methods=['GET','POST'])
def move_forward(angle):
    app.logger.info('move forward')
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
        ROBOT.stop()
    return jsonify({'message':'stop'})

@app.route('/start_mission', methods=['GET','POST'])
def start_mission():
    app.logger.info('start mission')
    red_num = request.form['red_num']
    green_num = request.form['green_num']
    blue_num = request.form['blue_num']

    if ROBOT:
        try:
            ROBOT.automated_search(int(red_num), int(green_num), int(blue_num))
        except Exception as e:
            print(e)
            ROBOT.stop_automated_search()
            ROBOT.stop()
    return jsonify({'message':'starting mission', 'red_num':red_num})

@app.route('/stop_mission', methods=['GET','POST'])
def stop_mission():
    app.logger.info('stop_mission')
    if ROBOT:
        ROBOT.stop_automated_search()
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
