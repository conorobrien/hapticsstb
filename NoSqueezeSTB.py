from __future__ import division
#!/usr/bin/env python

## BEFORE RUNNING ON NEW COMPUTER
# Install Phidget Libraries: http://www.phidgets.com/docs/OS_-_Linux#Getting_Started_with_Linux
# Install Phidget Python libraries: http://www.phidgets.com/docs/Language_-_Python#Linux
# Test Phidget with demo code: http://www.phidgets.com/downloads/examples/Python.zip
# Make sure it works with demo code, this code is pretty basic

# Phidget Python API reference: http://www.phidgets.com/documentation/web/PythonDoc/Phidgets.html
import csv
import argparse
import glob
import time
import os
import sys
import datetime
import termios
import fcntl
import numpy as np
import hapticsstb

import math 

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("-s", "--subject", type=str, default='1', help="Subject ID Number")
parser.add_argument("-t", "--task", type=str, default='1', help="Task ID Number")

parser.add_argument("-p", "--plot", type=int, default=0, choices=[1,2,3,4],
                    help=
"""Set sample rate to 500Hz and display line plots for
debugging
    1: F/T graph
    2: Mini40 Channel Voltages
    3: Accelerometer Gs
    4: Single Point Position
""")

parser.add_argument("--sample_rate", type=int, default=3000, help="STB sampling rate (default 3kHz, 500Hz if plotting)")
parser.add_argument("--sample_time", type=int, default=10, help="Length of trial run in sec (overridden if pedal active)")

parser.add_argument("--keyboard", default=False, action="store_true", help="Use keyboard to start and stop trials")
parser.add_argument("--no_pedal", dest="pedal", default=True, action="store_false", help="Don't use pedal to start and stop trials")
parser.add_argument("--no_video", dest="video", default=True, action="store_false", help="Don't record video")
parser.add_argument("--no_write", dest="write", default=True, action="store_false", help="Don't write data to disk")

args = parser.parse_args()

if args.keyboard:
    args.pedal = False
    fd = sys.stdin.fileno()
    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

def create_filename(subject, task, data_dir):
    subject_dir = 'Subject'+subject.zfill(3)
    test_filename =  'S' + subject.zfill(3) + 'TrainNoFB' + task +'_' + time.strftime('%m-%d_%H-%M')
    test_path = data_dir + '/' + subject_dir + '/' + test_filename

    if [] == glob.glob(data_dir):
        print "MAKING " + data_dir
        os.mkdir(data_dir)
    if [] == glob.glob(data_dir + '/' + subject_dir):
        print "MAKING " + subject_dir
        os.mkdir(data_dir + '/' + subject_dir)

    return test_path

from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Devices.AdvancedServo import AdvancedServo

#Do Not Make Force_Scale less than 1
FORCE_SCALE  = 1
def Error(e):
    try:
        source = e.device
        print("Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))

# Setup Phidget
servo = AdvancedServo()
servo.setOnErrorhandler(Error)

# Open Phidget
servo.openPhidget()
servo.waitForAttach(500)

# Set Phidget servo parameters
try:
	motor = 0
	servo.setEngaged(0, True)
	servo.setEngaged(1, True)
	servo_min = servo.getPositionMin(motor) + 100
	servo_max = servo.getPositionMin(motor) + 150
	servo_mid = (servo_max - servo_min)/2
	servo.setAcceleration(1, 500)
	servo.setAcceleration(motor, 500) # I just picked these to be smooth, feel free to change
	servo.setVelocityLimit(1, 2000)
	servo.setVelocityLimit(motor, 2000)
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

# Set up STB
sample_rate = 50 # This works best with low sampling rates

# Call STB's constructer (init)
sensor = hapticsstb.STB(sample_rate, pedal=args.pedal)

if args.plot:
   sensor.plot_init(args.plot, 5)

# Preallocate hist vector, use sensor.sample_rate since sample rate changes if you turn graphing on
if not args.pedal:
    sample_length = sensor.sample_rate*args.sample_time
else:
    sample_time = 1800
    sample_length = sensor.sample_rate*sample_time

sensor_hist = np.zeros((sample_length, 17))

print '*'*80
print "Biasing, make sure board is clear"
sensor.bias() # Tares the sensor, make sure that nothing's touching the bordcr
print sensor.bias_vector
print "Done!"
print '*'*80

#run_time = 500
volt = 3.3
#start_time = time.time()
#sensor.start_sampling() # Starts the STB hardware sampling loop

while True: # Runs once if args.pedal is false

	try:
		#fname = time.strftime("%H_%M_%S_%m_%d_%Y")
		#newdir = "/home/haptics/joshdata/" 
		#os.chdir(newdir)
		#while time.time() - start_time <= run_time:
        # read_M40 returns [Fx, Fy, Fz, Tx, Ty, Tz]

    	# Block until single pedal press if using pedal
		if args.pedal:
		    print "Waiting for Pedal Input"

		    while True:
		        pedal = sensor.pedal()
		        if pedal == 1:
		            break
		        elif pedal == 3:
		            print "Quitting!"
		            sys.exit()

		elif args.keyboard:
		    print "Waiting for Keyboard Input (space to start/stop, q to quit)"

		    while True:
		        try:
		            keypress = sys.stdin.read(1)
		            if keypress == ' ':
		                break
		            elif keypress == 'q':
		                print "Quitting!"
		                sys.exit()
		        except IOError: pass

		if args.write or args.video:
		    test_filename = create_filename(args.subject, args.task, 'TestData')

		if args.video:
		    video_filename = test_filename + '.avi'
		    sensor.video_init(video_filename)

		else:
		    print "Starting " + str(args.sample_time) + " second trial"

		print '*'*80
		print "Starting Sampling ..."
		sensor.start_sampling()


		for ii in range(0,sample_length):
			sensor_data = sensor.read_m40()
			handedness = sensor.read_acc()
			#print("left hand" + str((handedness[0])))
			#print("right hand" + str((handedness[1])))
			#print sensor_data[0]
			#print sensor_data[1]
			#print sensor_data[2]
			mag = (sensor_data[0]**2 + sensor_data[1]**2 + sensor_data[2]**2) ** (1/2)
			#print handedness[0],handedness[1],mag
			conv = (5/7)
			pos = servo_min + (mag * ((servo_max - servo_min)*conv) / FORCE_SCALE)
			#pos = servo_max;
			#eric = (pos, "left")
			#josh = (pos, "right")
			#sensor_hist[ii, 0:15] = sensor.read_data()
			#sensor_hist[ii,:] = np.append(sensor_hist[ii,:],[pos, mag])	
			sensor_hist[ii,:] = np.hstack((sensor.read_data(),[pos,mag]))	
			
			
			servo.setPosition(1, servo_min)
			servo.setPosition(0, servo_min)

			if args.plot:
				sensor.plot_update()

			if args.pedal:
				if sensor.pedal() == 2:
					print "Pedal Break ..."
					print '*'*80
					servo.setPosition(1, servo_min)
					servo.setPosition(0, servo_min)
					break
			elif args.keyboard:
				try:
					if sys.stdin.read(1) == ' ':
						print "Key Break ..."
						print '*'*80
						servo.setPosition(1, servo_min)
						servo.setPosition(0, servo_min)
						break
				except IOError: pass

		else:
		    if args.pedal or args.keyboard:
			print "Time Limit Reached! " + str(args.sample_time) + "s limit, adjust in code if needed"
			print '*'*80

 	#cat = (pos, time.time()-start_time, sensor_data[0], sensor_data[1], sensor_data[2])
#sensor_data[0] is force in x
#sensor_data[1] is force in y
#sensor_data[2] is force in z

        #with open(fname + ".csv", "a") as csvfile:
            #spamwriter = csv.writer(csvfile, delimiter = ',')
            #spamwriter.writerow(cat)

	
        # Scale force to +- 30N for whole range of servo
		#pos = servo_mid + (sensor_data[2])*(servo_max - servo_mid)/FORCE_SCALE
		#if pos <= servo_max and pos >= servo_min:
		#	servo.setPosition(motor, pos)
		#	servo.setPosition(1, pos)
		#elif pos > servo_max:
		#	servo.setPosition(motor, servo_max)
		#	servo.setPosition(1, servo_max)
		#	
		#elif pos < servo_min:
		#	servo.setPosition(motor, servo_min)
		#	servo.setPosition(1, servo_min)
		# print( "Sensor data: " + str(sensor_data) );
       
	except KeyboardInterrupt: # This lets you ctrl-c out of the sampling loop safely, also breaks out of while loop
        	break

	except PhidgetException as e:
		print("Phidget Exception %i: %s" % (e.code, e.details))
		print("Exiting....")
		exit(1)

	except:
		print "Closing Serial Port ..."
		sensor.close() # Need to run this when you're done, stops STB and closes serial port
		servo.closePhidget()
		if args.keyboard:
		    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
		    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
		raise

	print 'Finished Sampling!'

	sensor.stop_sampling()

 	if args.write:
		np.savetxt(test_filename + '.csv', sensor_hist[:(ii+1),0:17], delimiter=",")
		print 'Finished Writing!'

    	print '*'*80

    	if not args.pedal:
		break

servo.setPosition(1, servo_min)
servo.setPosition(0, servo_min)
sensor.close()
servo.closePhidget()
if args.keyboard:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
