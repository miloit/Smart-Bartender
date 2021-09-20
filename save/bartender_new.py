import gaugette.ssd1306
#import gaugette.platform
import gaugette.gpio
import time
import sys
import RPi.GPIO as GPIO
import json
import threading
import traceback
import random
import os
import psutil
from threading import Thread
from flask import Flask, render_template, request, url_for, redirect, flash, session, abort, jsonify
from multiprocessing import Process
from flask_sqlalchemy import sqlalchemy, SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

#from dotstar import Adafruit_DotStar
import board
import adafruit_dotstar as dotstar
from menu import MenuItem, Menu, Back, MenuContext, MenuDelegate
from drinks import drink_options

with open('static/json/drinks.json', 'r') as f:
    drink_list = json.load(f, encoding='uft-8')
    f.close()




ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = '/home/pi/'

# Change dbname here
db_users = "database/users.db"

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{db}'.format(db=db_users)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# SECRET_KEY required for session, flash and Flask Sqlalchemy to work
app.config['SECRET_KEY'] = 'configure strong secret key here'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy(app)


GPIO.setmode(GPIO.BCM)

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64

LEFT_BTN_PIN = 13
LEFT_PIN_BOUNCE = 200

RIGHT_BTN_PIN = 5
RIGHT_PIN_BOUNCE = 200

OLED_RESET_PIN = 15
OLED_DC_PIN = 16

NUMBER_NEOPIXELS = 72
NEOPIXEL_DATA_PIN = 26
NEOPIXEL_CLOCK_PIN = 6
NEOPIXEL_BRIGHTNESS = 0.2

FLOW_RATE = 60.0 / 100.0
bartender = 0
processbartender = 0




class User(db.Model):
    __tablename__ = "users"
    """ Create user table"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.route("/about")
def about():
    return render_template("index.html")


#@app.route('/')
#def index():
#    session["sessionActive"] = flagSessionActive
#    return render_template("index.html")
@app.route('/home')
@app.route('/', methods=['GET', 'POST'])
def home():
    """ Session control"""
    try:
        if session['logged_in'] is None:
            session['logged_in'] = False
    except KeyError:
        session['logged_in'] = False

    try:
        if session['username'] is None:
            session['username'] = ''
    except KeyError:
        session['username'] = ''

    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        if request.method == 'POST':
            username = getname(request.form['username'])
            return render_template('index.html', data=getfollowedby(username))
        return render_template('index.html')

#@app.route('/home')
#def home():
#    return render_template("index.html")


@app.route("/poweroff")
def power():
    os.system("shutdown -h now")


# def shutdown_server():
# func = request.environ.get('werkzeug.server.shutdown')
# if func is None:
# raise RuntimeError('Not running with the Werkzeug Server')
# func()

@app.route("/reboot")
def restart():
    try:
        os.system('reboot')
        return 'Server restarting...'
    except Exception as e:
        print(str(e))

#@app.route("/signup/", methods=["GET", "POST"])
#def signup():
    """
    Implements signup functionality. Allows username and password for new user.
    Hashes password with salt using werkzeug.security.
    Stores username and hashed password inside database.

    Username should to be unique else raises sqlalchemy.exc.IntegrityError.
    """

#    if request.method == "POST":
#        username = request.form['username']
#        password = request.form['password']

#        if not (username and password):
#            flash("Username or Password cannot be empty")
#            return redirect(url_for('signup'))
#        else:
#            username = username.strip()
#            password = password.strip()

        # Returns salted pwd hash in format : method$salt$hashedvalue
#        hashed_pwd = generate_password_hash(password, 'sha256')

#        new_user = User(username=username, pass_hash=hashed_pwd)
#        db.session.add(new_user)

#        try:
#            db.session.commit()
#        except sqlalchemy.exc.IntegrityError:
#            flash("Username {u} is not available.".format(u=username))
#            return redirect(url_for('signup'))

#        flash("User account has been created.")
#        return redirect(url_for("login"))

#    return render_template("signup.html")
@app.route('/signup', methods=['GET', 'POST'])
@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    """Register Form"""
    try:
        if session['logged_in'] is None:
            session['logged_in'] = False
    except KeyError:
        session['logged_in'] = False

    try:
        if session['username'] is None:
            session['username'] = ''
    except KeyError:
        session['username'] = ''

    if request.method == 'POST':
        new_user = User(
            username=request.form['username'],
            password=request.form['password'])
        db.session.add(new_user)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            flash("Username {u} is not available.".format(u=request.form['username']))
            return redirect(url_for('signup'))
        flash("User account has been created.")
        return render_template('login.html')
    return render_template('signup.html')
#@app.route("/", methods=["GET", "POST"])
#@app.route("/Wlogin/", methods=["GET", "POST"])
#def login():
    """
    Provides login functionality by rendering login form on get request.
    On post checks password hash from db for given input username and password.
    If hash matches redirects authorized user to home page else redirect to
    login page with error message.
    """
#    print(session)
    #print(flagSessionActive)
#    print(current_user.is_authenticated)
#    if 1==1:
#        if request.method == "POST":
#            username = request.form['username']
#            password = request.form['password']

#            if not (username and password):
#                flash("Username or Password cannot be empty.")
#                return redirect(url_for('login'))
#            else:
#                username = username.strip()
#                password = password.strip()

#            user = User.query.filter_by(username=username).first()

#            if user and check_password_hash(user.pass_hash, password):
#                flagSessionActive = True
#                session["sessionActive"] =  True
                #session[username] = True
#                session['user'] = username
#                return redirect(url_for("user_home", username=username))
#            else:
#                flash("Invalid username or password.")

#        return render_template("login.html")
#    else:
#        return redirect(url_for("user_home", username=username))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    """Login Form"""
    try:
        if session['logged_in'] is None:
            session['logged_in'] = False
    except KeyError:
        session['logged_in'] = False

    try:
        if session['username'] is None:
            session['username'] = ''
    except KeyError:
        session['username'] = ''
 
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']
        
        if not (username and password):
             flash("Username or Password cannot be empty.")
             return redirect(url_for('login'))
        else:
            try:
                data = User.query.filter_by(username=username, password=password).first()
                #print("data")
                #print (data.username)
                if data is not None:
                    session['logged_in'] = True
                    session['username'] = data.username
                    #session['data'] = data
                    return redirect(url_for('home'))
                else:
                   #return 'Dontt Login'
                   flash("Invalid username or password.")
                   return redirect(url_for("login"))
            except Exception as e:
                flash("Error")
                return redirect(url_for("login"))
#               print(e)
#               return "Dont Login"

@app.route('/form', methods = ['GET', 'POST'])
def ajax_request():
    try:
        if session['logged_in'] is None:
            session['logged_in'] = False
    except KeyError:
        session['logged_in'] = False

    try:
        if session['username'] is None:
            session['username'] = ''
    except KeyError:
        session['username'] = ''

    if request.method == 'POST':
        #print (request.form['age'])
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            data = {"status": "error"}
            return jsonify(data), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        data = {"status": "ok"}
        return jsonify(data), 200
    else:
        return render_template('form.html')

def allowed_file(filename):
     return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/user/<username>/")
def user_home(username):
    """
    Home page for validated users.

    """
    if 'user' in session:
    	user = session['user']
    	print (user)
    else:
        print ("no")

    if not session.get(username):
        abort(401)
  
    return render_template("user_home.html", username=username)


#@app.route("/logout/<username>")
#def logout(username):
    """ Logout user and redirect to login page with success message."""
#    session.pop(username, None)
#    flash("successfully logged out.")
#    return redirect(url_for('login'))

@app.route("/logout")
def logout():
    """Logout Form"""
    session['logged_in'] = False
    session['username'] = ''
    return redirect(url_for('home'))



class Bartender(MenuDelegate):
    # processbartender = 0

    def __init__(self):
        self.running = False
        self._running = True

        # set the oled screen height
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT

        self.btn1Pin = LEFT_BTN_PIN
        self.btn2Pin = RIGHT_BTN_PIN

        # configure interrups for buttons
        GPIO.setup(self.btn1Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.btn2Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # configure screen
        #spi_bus = 0
        #spi_device = 0
        gpio = gaugette.gpio.GPIO()
        spi = gaugette.spi.SPI(bus=0, device=0)
        #spi = gaugette.spi.SPI(spi_bus, spi_device)

        # Very important... This lets py-gaugette 'know' what pins to use in order to reset the display
        self.led = gaugette.ssd1306.SSD1306(gpio, spi, reset_pin=OLED_RESET_PIN, dc_pin=OLED_DC_PIN,
                                            rows=self.screen_height,
                                            cols=self.screen_width)  # Change rows & cols values depending on your display dimensions.
        self.led.begin()
        self.led.clear_display()
        self.led.display()
        self.led.invert_display()
        time.sleep(0.5)
        self.led.normal_display()
        time.sleep(0.5)

        # load the pump configuration from file
        self.pump_configuration = Bartender.readPumpConfiguration()
        for pump in list(self.pump_configuration.keys()):
            GPIO.setup(self.pump_configuration[pump]["pin"], GPIO.OUT, initial=GPIO.HIGH)

        # setup pixels:
        self.numpixels = NUMBER_NEOPIXELS  # Number of LEDs in strip

        # Here's how to control the strip from any two GPIO pins:
        #datapin = NEOPIXEL_DATA_PIN
        #clockpin = NEOPIXEL_CLOCK_PIN
        #self.strip = Adafruit_DotStar(self.numpixels, datapin, clockpin)
        datapin  = NEOPIXEL_DATA_PIN
        clockpin = NEOPIXEL_CLOCK_PIN
        self.strip = dotstar.DotStar(board.D6, board.D26, self.numpixels, brightness=NEOPIXEL_BRIGHTNESS)
        #self.strip.begin()  # Initialize pins for output
        #self.strip.setBrightness(NEOPIXEL_BRIGHTNESS)  # Limit brightness to ~1/4 duty cycle

        # turn everything off
        #for i in range(0, self.numpixels):
        #    self.strip[i] = [0,0,0]
        self.strip.fill((0, 0, 0))
#        self.strip.show()
        self.buildMenu(drink_list, drink_options)
        processbartender = Process(target=self.run, args=())
        processbartender.daemon = True  # Daemonize it
        processbartender.start()
        print("Done initializing")

    def terminate(self):
        self._running = False

    @staticmethod
    def readPumpConfiguration():
        return json.load(open('/home/pi/bartender/Smart-Bartender/pump_config.json'))

    @staticmethod
    def readDrinkDescription():
        return json.load(open('/home/pi/bartender/Smart-Bartender/drinks.json'))

    @staticmethod
    def writePumpConfiguration(configuration):
        with open("/home/pi/bartender/Smart-Bartender/pump_config.json", "w") as jsonFile:
            json.dump(configuration, jsonFile)

    def startInterrupts(self):
        self.running = True
        GPIO.add_event_detect(self.btn1Pin, GPIO.FALLING, callback=self.left_btn, bouncetime=LEFT_PIN_BOUNCE)
        GPIO.add_event_detect(self.btn2Pin, GPIO.FALLING, callback=self.right_btn, bouncetime=RIGHT_PIN_BOUNCE)
        # time.sleep(1)
        self.running = False

    def stopInterrupts(self):
        GPIO.remove_event_detect(self.btn1Pin)
        GPIO.remove_event_detect(self.btn2Pin)

    def buildMenu(self, drink_list, drink_options):
        # create a new main menu
        m = Menu("Main Menu")

        # add drink options
        drink_opts = []
        for d in drink_list:
            drink_opts.append(MenuItem('drink', d["name"], {"ingredients": d["ingredients"]}))

        configuration_menu = Menu("Configure")

        # add pump configuration options
        pump_opts = []
        for p in sorted(self.pump_configuration.keys()):
            config = Menu(self.pump_configuration[p]["name"])
            # add fluid options for each pump
            for opt in drink_options:
                # star the selected option
                selected = "*" if opt["value"] == self.pump_configuration[p]["value"] else ""
                config.addOption(
                    MenuItem('pump_selection', opt["name"], {"key": p, "value": opt["value"], "name": opt["name"]}))
            # add a back button so the user can return without modifying
            config.addOption(Back("Back"))
            config.setParent(configuration_menu)
            pump_opts.append(config)

        # add pump menus to the configuration menu
        configuration_menu.addOptions(pump_opts)
        # add a back button to the configuration menu
        configuration_menu.addOption(Back("Back"))
        # adds an option that cleans all pumps to the configuration menu
        configuration_menu.addOption(MenuItem('clean', 'Clean'))
        configuration_menu.addOption(MenuItem('loadpumps', 'Load Pumps'))
        configuration_menu.setParent(m)

        m.addOptions(drink_opts)
        m.addOption(configuration_menu)
        # create a menu context
        self.menuContext = MenuContext(m, self)

    def filterDrinks(self, menu):
        """
        Removes any drinks that can't be handled by the pump configuration
        """
        for i in menu.options:
            if (i.type == "drink"):
                i.visible = False
                ingredients = i.attributes["ingredients"]
                presentIng = 0
                for ing in list(ingredients.keys()):
                    for p in list(self.pump_configuration.keys()):
                        if (ing == self.pump_configuration[p]["value"]):
                            presentIng += 1
                if (presentIng == len(list(ingredients.keys()))):
                    i.visible = True
            elif (i.type == "menu"):
                self.filterDrinks(i)

    def selectConfigurations(self, menu):
        """
        Adds a selection star to the pump configuration option
        """
        for i in menu.options:
            if (i.type == "pump_selection"):
                key = i.attributes["key"]
                if (self.pump_configuration[key]["value"] == i.attributes["value"]):
                    i.name = "%s %s" % (i.attributes["name"], "*")
                else:
                    i.name = i.attributes["name"]
            elif (i.type == "menu"):
                self.selectConfigurations(i)

    def prepareForRender(self, menu):
        self.filterDrinks(menu)
        self.selectConfigurations(menu)
        return True

    def menuItemClicked(self, menuItem):
        if (menuItem.type == "drink"):
            self.makeDrink(menuItem.name, menuItem.attributes["ingredients"])
            return True
        elif (menuItem.type == "pump_selection"):
            self.pump_configuration[menuItem.attributes["key"]]["value"] = menuItem.attributes["value"]
            Bartender.writePumpConfiguration(self.pump_configuration)
            return True
        elif (menuItem.type == "clean"):
            self.clean()
            return True
        elif (menuItem.type == "loadpumps"):
            self.loadpumps()
            return True
        return False

    def loadpumps(self):
        waitTime = 10
        pumpThreads = []

        # cancel any button presses while the drink is being made
        # self.stopInterrupts()
        self.running = True

        for pump in list(self.pump_configuration.keys()):
            pump_t = threading.Thread(target=self.pour, args=(self.pump_configuration[pump]["pin"], waitTime))
            pumpThreads.append(pump_t)

        # start the pump threads
        for thread in pumpThreads:
            thread.start()

        # start the progress bar
        self.progressBar(waitTime)

        # wait for threads to finish
        for thread in pumpThreads:
            thread.join()
        # show the main menu
        self.menuContext.showMenu()

        # sleep for a couple seconds to make sure the interrupts don't get triggered
        time.sleep(2);

        # reenable interrupts
        # self.startInterrupts()
        self.running = False

    def clean(self):
        waitTime = 20
        pumpThreads = []

        # cancel any button presses while the drink is being made
        self.stopInterrupts()
        self.running = True

        for pump in list(self.pump_configuration.keys()):
            pump_t = threading.Thread(target=self.pour, args=(self.pump_configuration[pump]["pin"], waitTime))
            pumpThreads.append(pump_t)

        # start the pump threads
        for thread in pumpThreads:
            thread.start()

        # start the progress bar
        self.progressBar(waitTime)

        # wait for threads to finish
        for thread in pumpThreads:
            thread.join()

        # show the main menu
        self.menuContext.showMenu()

        # sleep for a couple seconds to make sure the interrupts don't get triggered
        time.sleep(2);

        # reenable interrupts
        self.startInterrupts()
        self.running = False

    def displayMenuItem(self, menuItem):
        print(menuItem.name)
        self.led.clear_display()
        self.led.draw_text2(0, 20, menuItem.name, 2)
        self.led.display()

    def random_color():
        return random.randrange(0, 7) * 32

    def cycleLights(self):
        t = threading.currentThread()
        # head  = 0               # Index of first 'on' pixel
        # tail  = -10             # Index of last 'off' pixel
        # color = 0xFF0000        # 'On' color (starts red)

        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        self.strip[0:self.numpixels] = [(r,g,b)] *self.numpixels

        while getattr(t, "do_run", True):
            #randombasecolor = random.randint(0, 0xFFFFFF)
            r = random.randint(0, 100)
            g = random.randint(0, 100)
            b = random.randint(0, 100)
            randomdots = random.randint(0, self.numpixels)
            #for dot in range(randomdots, (randomdots + 10)):
            #    self.strip[dot] = [r,g,b]
            #print(r)
            #print(g)
            #print(b)
            #if ((randomdots+40) > self.numpixels):
            self.strip[randomdots:self.numpixels] =  [(r,g,b)] * (self.numpixels-randomdots)
            #else:
            #    self.strip[randomdots:(randomdots+40)] = [(r,g,b)] * 40

            #print(r)
            #print(g)
            #print(b)
            r = random.randint(0, 200)
            g = random.randint(0, 200)
            b = random.randint(0, 200)
            randomdots = random.randint(0, self.numpixels)
            #for dot in range(randomdots, (randomdots + 10)):
            #    self.strip[dot] = [r,g,b]
            #print(r)
            #print(g)
            #print(b)
            #if ((randomdots+40) > self.numpixels):
            self.strip[randomdots:self.numpixels] =  [(r,g,b)] * (self.numpixels-randomdots)
            #else:
            #    self.strip[randomdots:(randomdots+40)] = [(r,g,b)] * 40

            #for dot in range(0, self.numpixels):
            #    self.strip[dot] = [r,g,b]
            #self.strip[0:self.num.pixels] = [(r,g,b)] *self.numpixels
            #self.strip.show()
            r = random.randint(100, 200) 
            g = random.randint(100, 200) 
            b = random.randint(100, 200) 

            #randomdotcolor = random.randint(0, 0xFFFFFF)
            randomdots = random.randint(0, self.numpixels)
            #for dot in range(randomdots, (randomdots + 10)):
            #    self.strip[dot] = [r,g,b]
	    #print(r)
            #print(g)
            #print(b)
            #if ((randomdots+40) > self.numpixels):
            self.strip[randomdots:self.numpixels] =  [(r,g,b)] * (self.numpixels-randomdots)
            #else:
             #   self.strip[randomdots:(randomdots+40)] = [(r,g,b)] * 40
            #self.strip.show()
            #time.sleep(0.1)
        # self.strip.setPixelColor(head, color) # Turn on 'head' pixel

    # self.strip.setPixelColor(tail, 0)     # Turn off 'tail'
    # self.strip.show()                     # Refresh strip
    # time.sleep(1.0 / 80)             # Pause 20 milliseconds (~50 fps)

    # head += 1                        # Advance head position
    # if(head >= self.numpixels):           # Off end of strip?
    #	head    = 0              # Reset to start
    #	color >>= 1              # Red->green->blue->black
    #	if(color == 0): color = 0xFF0000 # If black, reset to red

    # tail += 1                        # Advance tail position
    # if(tail >= self.numpixels): tail = 0  # Off end? Reset

    def lightsEndingSequence(self):
        # make lights green
        #for i in range(0, self.numpixels):
        #    self.strip[i] = [0,255,0]
        self.strip.fill((0, 255, 0))
        self.strip.show()

        time.sleep(1)

        # turn lights off
        #for i in range(0, self.numpixels):
        #    self.strip[i] = [0,0,0]
        self.strip.fill((0, 0, 0))
        self.strip.show()

    def pour(self, pin, waitTime):
        GPIO.output(pin, GPIO.LOW)
        time.sleep(waitTime)
        GPIO.output(pin, GPIO.HIGH)

    def progressBar(self, waitTime):
        interval = waitTime / 100.0
        for x in range(1, 101):
            self.led.clear_display()
            self.updateProgressBar(x, y=35)
            self.led.display()
            time.sleep(interval)

    def makeDrink(self, drink, ingredients):
        # cancel any button presses while the drink is being made
        # self.stopInterrupts()
        self.running = True

        # launch a thread to control lighting
        lightsThread = threading.Thread(target=self.cycleLights)
        lightsThread.start()

        # Parse the drink ingredients and spawn threads for pumps
        maxTime = 0
        pumpThreads = []
        for ing in list(ingredients.keys()):
            for pump in list(self.pump_configuration.keys()):
                if ing == self.pump_configuration[pump]["value"]:
                    waitTime = ingredients[ing] * FLOW_RATE
                    if (waitTime > maxTime):
                        maxTime = waitTime
                    pump_t = threading.Thread(target=self.pour, args=(self.pump_configuration[pump]["pin"], waitTime))
                    pumpThreads.append(pump_t)

        # start the pump threads
        for thread in pumpThreads:
            thread.start()

        # start the progress bar
        self.progressBar(maxTime)

        # wait for threads to finish
        for thread in pumpThreads:
            thread.join()

        # show the main menu
        self.menuContext.showMenu()

        # stop the light thread
        lightsThread.do_run = False
        lightsThread.join()

        # show the ending sequence lights
        self.lightsEndingSequence()

        # sleep for a couple seconds to make sure the interrupts don't get triggered
        time.sleep(2);

        # reenable interrupts
        # self.startInterrupts()
        self.running = False

    # self.menuContext.showMenu()

    def left_btn(self, ctx):
        if not self.running:
            self.menuContext.advance()

    def right_btn(self, ctx):
        if not self.running:
            self.menuContext.select()

    def updateProgressBar(self, percent, x=15, y=15):
        height = 10
        width = self.screen_width - 2 * x
        for w in range(0, width):
            self.led.draw_pixel(w + x, y)
            self.led.draw_pixel(w + x, y + height)
        for h in range(0, height):
            self.led.draw_pixel(x, h + y)
            self.led.draw_pixel(self.screen_width - x, h + y)
            for p in range(0, percent):
                p_loc = int(p / 100.0 * width)
                self.led.draw_pixel(x + p_loc, h + y)

    def run(self):
        self.startInterrupts()
        self.readDrinkDescription()
        # main loop
        try:
            while self._running:
                time.sleep(0.1)

        except KeyboardInterrupt:
            self.terminate()
            print("CTRL+C pressed")
        finally:
            GPIO.cleanup()  # clean up GPIO on normal exit

    # traceback.print_exc()


def main():
    """
    Main entry point into program execution

    PARAMETERS: none
    """
    try:
        db.create_all()
        bartender = Bartender()
        app.run(host='0.0.0.0', port=80, use_reloader=False, debug=True, threaded=True)
    # processbartender.join()
    except KeyboardInterrupt:
        print("Exit")


main()
