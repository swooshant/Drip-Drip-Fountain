#!/usr/bin/python3
from flask import Flask, render_template, request
import RPi.GPIO as GPIO
from datetime import datetime
from threading import Timer
import time

# Download the helper library from https://www.twilio.com/docs/python/install
from twilio.rest import Client
import json

# Your Account Sid and Auth Token from twilio.com/console
account_sid = 'AC46d36a4ab82814006a66eb3b06a167dd'
auth_token = '13cf326eb755f7f3e8cb28f79ff6fe5b'
client = Client(account_sid, auth_token)

def notify(msg):
	dateTime = datetime.now().strftime('%-I:%M%p')
	notification = client.notify \
	                     .services('ISff9f0fa161a287a09ebf3a8f6ad9bc36') \
	                     .notifications \
	                     .create(
	                          body= dateTime + ' - ' + msg,
	                          to_binding=json.dumps({
	                              'binding_type': 'sms',
	                              'address': '+15714421315'
	                          }),        
	                      )


app = Flask(__name__)

# Create a dictionary called pins to store the pin number, name, and pin state:
pin = 13
state = "off"
global event

GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.OUT)

onOff = {
	"on" : GPIO.HIGH,
	"off": GPIO.LOW
}

class RepeatingTimer(object):

    def __init__(self, interval, f, *args, **kwargs):
        self.interval = interval
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.startTime = time.time()
        self.timer = None
        self.timerStatus = 0

    def callback(self):
    	self.timerStatus = 0
    	self.f(*self.args, **self.kwargs)

    def cancel(self):
    	self.timerStatus = 0
    	self.timer.cancel()

    def elapsed(self):
    	return time.time() - self.startTime

    def remaining(self):
    	return self.interval - self.elapsed()

    def start(self):
        self.timer = Timer(self.interval, self.callback)
        self.startTime = time.time()
        self.timer.start()
        self.timerStatus = 1
        

def turnOnOff(action='off'):
	global state
	GPIO.output(pin, onOff[action])
	state = action

t = RepeatingTimer(5 * 60, turnOnOff)


try:
	GPIO.output(pin, GPIO.LOW)
except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
	print("Keyboard interrupt")

@app.route('/')
def index():
	return render_template('water.html')

@app.route('/timer/')
def timer():
	if t.timerStatus == 1:
		return str(int(t.remaining()))
	elif t.timerStatus == 0:
		return "stop"


@app.route('/changePin/<action>/', methods=["GET", "POST"])
def action(action):
	if request.method == 'GET':
		if action == "on" or action == "off":
			global state 
			if action != state:
				try:
					turnOnOff(action)
					if action == "on":
						notify('Raindrops, drop tops, drip drip, hehehe')
						t.start()
					elif action == "off":
						#notify('DDF no drip drip')
						t.cancel()
					return "Turned GPIO: " + action
				except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
					print("Keyboard interrupt")
			else:
				return "Already: " + action
		elif action == "status":
			return state
		else:
			return "Invalid Request"



if __name__ == '__main__':
    app.run(host='192.168.86.109')
    
