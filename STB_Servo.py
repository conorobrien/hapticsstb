
import numpy as np
import hapticsstb
import time
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, CurrentChangeEventArgs, PositionChangeEventArgs, VelocityChangeEventArgs
from Phidgets.Devices.AdvancedServo import AdvancedServo
from Phidgets.Devices.Servo import ServoTypes

# Setup Phidget

servo = AdvancedServo()
def Error(e):
    try:
        source = e.device
        print("Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))

servo.setOnErrorhandler(Error)

servo.openPhidget()
try:
    servo.waitForAttach(1000)
except PhidgetException:
	servo.closePhidget()

motor = 0
servo.setEngaged(motor, True)
servo_min = servo.getPositionMin(motor)
servo_max = servo.getPositionMax(motor)
servo_mid = (servo_max - servo_min)/2

servo.setAcceleration(motor, 1000)
servo.setVelocityLimit(motor, 1000)

sample_rate = 10
sample_length = sample_rate*30

sensor = hapticsstb.STB(sample_rate)

sensor.bias()
print sensor.bias_vector

sensor.start_sampling()

try:
    for ii in range(0,sample_length):
		sensor_data = sensor.read_data()
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
	sensor.close()
	servo.closePhidget()
	raise

sensor.stop_sampling()
sensor.close()
servo.closePhidget()
