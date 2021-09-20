import gaugette.ssd1306
import gaugette.platform
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
from flask import Flask, render_template, jsonify, request, redirect, url_for
from multiprocessing import Process
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import NumberRange, Length
import board
import adafruit_dotstar as dotstar
from menu import MenuItem, Menu, Back, MenuContext, MenuDelegate
from drinks import drink_options

with open('static/json/drinks.json') as f:
  drink_list = json.load(f)




app = Flask(__name__)
app.config['SECRET_KEY'] = 'NOT SO SECRET'

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
NEOPIXEL_BRIGHTNESS = 30

FLOW_RATE = 60.0/100.0
bartender = 0
processbartender = 0





class Form(FlaskForm):
    username = StringField('Username', [
        Length(min=3, max=15, message='Username must be at least %(min)s but no more than %(max)s characters')
    ])
    age = IntegerField('Age', [
        NumberRange(min=14, message='You must be %(min)s or older to sign up')
    ])


@app.route("/about")
def about():
    return render_template("home.html_save")

@app.route('/')
def index():
    return render_template("home.html")

@app.route('/home')
def home():
    return render_template("home.html")

@app.route("/poweroff")
def power():
    os.system("shutdown -h now")

@app.route('/withajax', methods=['GET', 'POST'])
def withajax():
    form = Form()
    if request.method == 'POST':
        if form.validate():
            req = request.form
            print((form.csrf_token.data))
            return 'WOOT WOOT!'
        return jsonify(form.errors), 400
    return render_template('withajax.html', form=form)

#def shutdown_server():
    #func = request.environ.get('werkzeug.server.shutdown')
    #if func is None:
        #raise RuntimeError('Not running with the Werkzeug Server')
    #func()

@app.route("/reboot")
def restart():
	try:
		os.system('reboot')
		return 'Server restarting...'
	except Exception as e:
		print((str(e)))

class Bartender(MenuDelegate): 
        #processbartender = 0

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
		spi_bus = 0
		spi_device = 0
		gpio = gaugette.gpio.GPIO()
		spi = gaugette.spi.SPI(spi_bus, spi_device)

		# Very important... This lets py-gaugette 'know' what pins to use in order to reset the display
		self.led = gaugette.ssd1306.SSD1306(gpio, spi, reset_pin=OLED_RESET_PIN, dc_pin=OLED_DC_PIN, rows=self.screen_height, cols=self.screen_width) # Change rows & cols values depending on your display dimensions.
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
		self.numpixels = NUMBER_NEOPIXELS # Number of LEDs in strip

		# Here's how to control the strip from any two GPIO pins:
		datapin  = NEOPIXEL_DATA_PIN
		clockpin = NEOPIXEL_CLOCK_PIN
                self.strip = dotstar.DotStar(datapin, clockpin, self.numpixels, brightness=NEOPIXEL_BRIGHTNESS)
		#self.strip = Adafruit_DotStar(self.numpixels, datapin, clockpin)
		#self.strip.begin()           # Initialize pins for output
		#self.strip.setBrightness(NEOPIXEL_BRIGHTNESS) # Limit brightness to ~1/4 duty cycle

		# turn everything off
		for i in range(0, self.numpixels):
			#self.strip.setPixelColor(i, 0x000000)
                        self.strip[i] =  [0,0,0]
		#self.strip.show() 
		self.buildMenu(drink_list, drink_options)
		processbartender = Process(target=self.run, args=())
	        processbartender.daemon = True                       # Daemonize it
        	processbartender.start()
		print ("Done initializing")
	
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
		#time.sleep(1)
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
				config.addOption(MenuItem('pump_selection', opt["name"], {"key": p, "value": opt["value"], "name": opt["name"]}))
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
		elif(menuItem.type == "pump_selection"):
			self.pump_configuration[menuItem.attributes["key"]]["value"] = menuItem.attributes["value"]
			Bartender.writePumpConfiguration(self.pump_configuration)
			return True
		elif(menuItem.type == "clean"):
			self.clean()
			return True
                elif(menuItem.type == "loadpumps"):
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
		print((menuItem.name))
		self.led.clear_display()
		self.led.draw_text2(0,20,menuItem.name,2)
		self.led.display()
        
	def random_color():
    		return random.randrange(0, 7) * 32

	def cycleLights(self):
		t = threading.currentThread()
		#head  = 0               # Index of first 'on' pixel
		#tail  = -10             # Index of last 'off' pixel
		#color = 0xFF0000        # 'On' color (starts red)

		while getattr(t, "do_run", True):
			r = random.randrange(0, 7) * 32
                        g = random.randrange(0, 7) * 32
                        b = random.randrange(0, 7) * 32
                        #randombasecolor=random.randint(0,0xFFFFFF)
			for  dot in range(0,self.numpixels):
				#self.strip.setPixelColor(dot,randombasecolor)
                                self.strip[dot] = [r,g,b] 
			self.strip.show()
			
			#randomdotcolor=random.randint(0,0xFFFFFF)
                        r = random.randrange(0, 7) * 32
                        g = random.randrange(0, 7) * 32
                        b = random.randrange(0, 7) * 32
			randomdots=random.randint(0,self.numpixels)
			#for dot in range(randomdots, (randomdots+10)):
                        #        self.strip.[dot] = [r,g,b]
                        self.strip.show()
			time.sleep(0.25)
                        #self.strip.setPixelColor(head, color) # Turn on 'head' pixel
			#self.strip.setPixelColor(tail, 0)     # Turn off 'tail'
			#self.strip.show()                     # Refresh strip
			#time.sleep(1.0 / 80)             # Pause 20 milliseconds (~50 fps)

			#head += 1                        # Advance head position
			#if(head >= self.numpixels):           # Off end of strip?
			#	head    = 0              # Reset to start
			#	color >>= 1              # Red->green->blue->black
			#	if(color == 0): color = 0xFF0000 # If black, reset to red

			#tail += 1                        # Advance tail position
			#if(tail >= self.numpixels): tail = 0  # Off end? Reset

	def lightsEndingSequence(self):
		# make lights green
		for i in range(0, self.numpixels):
			self.strip.setPixelColor(i, 0xFF0000)
		self.strip.show()

		time.sleep(5)

		# turn lights off
		for i in range(0, self.numpixels):
			self.strip.setPixelColor(i, 0)
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
                #self.menuContext.showMenu()

	def left_btn(self, ctx):
		if not self.running:
			self.menuContext.advance()

	def right_btn(self, ctx):
		if not self.running:
			self.menuContext.select()

	def updateProgressBar(self, percent, x=15, y=15):
		height = 10
		width = self.screen_width-2*x
		for w in range(0, width):
			self.led.draw_pixel(w + x, y)
			self.led.draw_pixel(w + x, y + height)
		for h in range(0, height):
			self.led.draw_pixel(x, h + y)
			self.led.draw_pixel(self.screen_width-x, h + y)
			for p in range(0, percent):
				p_loc = int(p/100.0*width)
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
			print ("CTRL+C pressed")
		finally:
			GPIO.cleanup()           # clean up GPIO on normal exit 

		#traceback.print_exc()
def main():
    	"""
    	Main entry point into program execution

    	PARAMETERS: none
    	"""
	try:
		bartender = Bartender()
		app.run(host='0.0.0.0', port=80, use_reloader=False, debug=True, threaded=True)
		#processbartender.join()
	except KeyboardInterrupt:
		print ("Exit")

main()
