## BEFORE RUNNING ON NEW COMPUTER
# Install Phidget Libraries: http://www.phidgets.com/docs/OS_-_Linux#Getting_Started_with_Linux
# Install Phidget Python libraries: http://www.phidgets.com/docs/Language_-_Python#Linux
# Test Phidget with demo code: http://www.phidgets.com/downloads/examples/Python.zip
# Make sure it works with demo code, theirs is much more verbose, this is pretty basic

# Phidget Python API reference: http://www.phidgets.com/documentation/web/PythonDoc/Phidgets.html

import numpy as np
import hapticsstb

from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, CurrentChangeEventArgs, PositionChangeEventArgs, VelocityChangeEventArgs
from Phidgets.Devices.AdvancedServo import AdvancedServo
from Phidgets.Devices.Servo import ServoTypes

# Setup Phidget
try:
    servo = AdvancedServo()
except RuntimeError as e:
  print("Runtime Error: %s" % e.message)

# Open Phidget
try:
servo.openPhidget()
except PhidgetException as e:
  print (“Phidget Exception %i: %s” % (e.code, e.detail))       
  exit(1)

# Set Phidget servo parameters
motor = 0
servo.setEngaged(motor, True)
servo_min = servo.getPositionMin(motor)
servo_max = servo.getPositionMax(motor)
servo_mid = (servo_max - servo_min)/2
servo.setAcceleration(motor, 1000) # I just picked these to be smooth, feel free to change
servo.setVelocityLimit(motor, 1000)

# Set up STB
sample_rate = 10 # This works best with a sampling rate of below 25 Hz
sample_length = sample_rate*30

sensor = hapticsstb.STB(sample_rate)

sensor.bias() # Tares the sensor, make sure that nothing's touching the board
print sensor.bias_vector

sensor.start_sampling() # Starts the STB hardware sampling loop
try:
    for ii in range(0,sample_length):
        # read_M40 returns [Fx, Fy, Fz, Tx, Ty, Tz]
		sensor_data = sensor.read_M40()

        # Scale force to +- 30N for whole range of servo
		pos = servo_mid + (sensor_data[2])*(servo_max - servo_mid)/30
		if pos <= servo_max and pos >= servo_min:
			servo.setPosition(motor, pos)
		elif pos > servo_max:
			servo.setPosition(motor, servo_max)
		elif pos < servo_min:
			servo.setPosition(motor, servo_min)

except KeyboardInterrupt:
    pass

except:
	sensor.close() # Need to run this when you're done, stops STB and closes serial port
	servo.closePhidget()
	raise

sensor.stop_sampling()
sensor.close()
servo.closePhidget()
