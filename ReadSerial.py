#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pylab as pl
import numpy as np
import serial, sys, os, glob, pdb, time, cv2, threading
from HapticsSTB import *




# Dict for command line inputs, contains default values
inputs = {	'subject': 1,
			'task': 1,
			'graphing': 0,
			'line_length': 150,
			'bias_sample': 100,
			'update_interval': 50,
			'sample_time': 5,
			'write_data': 0,
			'sample_rate': 3000,
			'pedal': 0,
			'video_capture': 0,
}

# Message displayed for command line help
help_message = """ ******
-subject: Subject ID number
-task: Task ID number
-pedal: use foot pedal for controlling sampling
-bias_sample: Number of samples averaged to get Mini40 biasing vector
-sample_time: Length of sample in seconds
-sample_rate: data sampling rate in Hz (forced to 500Hz for plotting)
-write_data: Write data to timestamped file
-graphing: reduce sample rate and display line plots for debugging
    1: F/T graph
    2: Mini40 Channel Voltages
    3: Accelerometer Voltages
    4: Single Point Position
(GRAPHING OPTIONS)
-line_length: number of samples shown on graph
-update_interval: Number of samples between plot updates
*****
"""

## Input handling, inputs beginning with '-' are considered commands, following
# string is converted to an int and assigned to the inputs dict
try:
	if len(sys.argv) > 1:
		for arg in range(1,len(sys.argv)):
			command = sys.argv[arg]
			if command[0] == '-':
				if command == '-help':
					print help_message
					sys.exit()
				else:
					if command[1:] in inputs.keys():
						inputs[command[1:].lower()] = int(sys.argv[arg+1])
					else:
						print "Invalid Command!"
						sys.exit()
except (NameError, ValueError, IndexError):
	print "Invalid Command!"
	sys.exit()


## Video Capture Setup
if inputs['video_capture']:
	# OpenCV initiliazation, create videoCapture object and codec
	cap = cv2.VideoCapture(-1)
	fourcc = cv2.cv.CV_FOURCC(*'XVID')

	# Thread function for video capture
	class OpenCVThread(threading.Thread):
		def __init__(self, cap, out):
			threading.Thread.__init__(self)
			self.stop = threading.Event()
			self.out = out
			self.cap = cap
			self.i = 0
		def run(self):
			while not self.stop.is_set():
				ret, frame = self.cap.read()
				if ret==True:
					frame = cv2.flip(frame,0)
			    	self.out.write(frame)


# Graphing Initialization
if inputs['graphing']:

	inputs['sample_rate'] = 500;
	print 'Forcing sample rate to 500Hz for graphing'

	plot_objects = GraphingSetup(inputs)

# Auto Detection for USB, not needed on mac, but linux serial devices only
# show up as ttyACMn, not with a unique ID

if sys.platform == 'darwin':
	device_folder = '/dev/tty.usbmodem*'

elif sys.platform == 'linux2':
	device_folder = '/dev/ttyACM*'

devices = glob.glob(device_folder)

if len(devices) < 2:
	print 'NOT ENOUGH DEVICES CONNECTED, EXITING...'
	sys.exit()

STBserial = PedalSerial = 0

for dev in devices:
	# Step through devices, pinging each one for a device ID
	test_device = serial.Serial(dev, timeout=0.1)
	test_device.write('\x02')
	time.sleep(0.05)
	test_device.flushInput()
	test_device.write('\x03')
 	
	devID = test_device.read(200)[-1]	#Read out everything in the buffer, and look at the last byte for the ID

	if devID == '\x01':
		STBserial = test_device
		STBserial.timeout = 0.01
	elif devID == '\x02':
		PedalSerial = test_device
		PedalSerial.timeout = 0
	else:
		print 'UNKNOWN DEVICE, EXITING...'
		sys.exit()

if not STBserial or (inputs['pedal'] and not PedalSerial):
	print 'NOT ALL DEVICES FOUND, EXITING...'
	sys.exit()

## BIASING
# read first 500 samples and average to get bias

print "DON'T TOUCH BOARD, BIASING..."
bias_hist = np.zeros((6,inputs['bias_sample']))

STBserial.write('\x01' + to16bit(inputs['sample_rate']))

for ii in range(0, inputs['bias_sample']):

	dat = STBserial.read(31)
	
	if dat == '':
		print 'NOTHING RECIEVED, EXITING...'
		STBserial.close()
		if inputs['pedal']:
			PedalSerial.close()
		sys.exit()

	packet = ord(dat[30])
	
	if ii == 0:
		packet_old = packet
	elif (packet != (packet_old+1)%256):
		print 'MISSED PACKET', packet, packet_old

	packet_old = packet
	bias_hist[:,ii] = Serial2M40Volts(dat)

bias = np.mean(bias_hist, axis=1).T
print "SAFE TO TOUCH"
print 'BIAS MATRIX'
print bias
STBserial.write('\x02')

## SAMPLING
# Code takes samples for seconds defined in sample_time

# set lengths for hist vectors, if pedal mode just preallocate for 10 min
# session

if inputs['pedal']:
	num_samples = inputs['sample_rate']*600
else:
	num_samples = inputs['sample_rate']*inputs['sample_time']



frame_start = time.time()

try:
	while 1:

		# Pedal input blocking, single or double tap starts trial, triple quits
		if inputs['pedal']:		
			print 'WAITING FOR PEDAL INPUT...'
			pedal_input = ''
			while pedal_input != '\x01':
				pedal_input = PedalSerial.read()

				if pedal_input == '\x03':
					print 'QUITTING...'
					sys.exit()

			

		# File operations, checks to make sure everything exists and timestamps
		if inputs['write_data'] or inputs['video_capture']:
			data_dir = 'TestData'
			subject_dir = 'Subject'+str(inputs['subject']).zfill(3)
			test_filename =  'S' + str(inputs['subject']).zfill(3) + 'T' + str(inputs['task']) +'_' + time.strftime('%m-%d_%H:%M')
			test_path = data_dir + '/' + subject_dir + '/' + test_filename


			if [] == glob.glob(data_dir):
				print "MAKING " + data_dir
				os.mkdir(data_dir)

			if [] == glob.glob(data_dir + '/' + subject_dir):
				print "MAKING " + subject_dir
				os.mkdir(data_dir + '/' + subject_dir)

		# Video prep, creates video folder
		if inputs['video_capture']:
			# pdb.set_trace()
			out = cv2.VideoWriter(test_path+'.avi',fourcc, 20.0, (640,480))
			videoThread = OpenCVThread(cap, out)
			videoThread.start()

		print 'STARTING DATA COLLECTION...'
		start = time.time()

		# If plotting voltage as well, DAT_hist has an extra six columns at the end
		# which contain the voltage channels
		if inputs['graphing'] == 2:
			DAT_hist = np.zeros((num_samples,21))
		else:
			DAT_hist = np.zeros((num_samples, 15))

		STBserial.write('\x01' + to16bit(inputs['sample_rate']))

		for ii in range(0,num_samples):

			dat = STBserial.read(31)
			
			if dat == '':
				print 'NOTHING RECIEVED, EXITING...'
				STBserial.close()
				if inputs['pedal']:
					PedalSerial.close()
				if inputs['video_capture']:
					videoThread.stop.set()
				sys.exit()

			# Missed packet detection, last byte of usb packet counts up
			packet = ord(dat[30])
			if ii == 0:
				packet_old = packet
			elif packet != (packet_old+1)%256:
				print 'MISSED PACKET', packet, packet_old
			packet_old = packet

			DAT_hist[ii, 0:15] = Serial2Data(dat, bias)

			if inputs['graphing'] == 2:
				DAT_hist[ii,15:] = Serial2M40Volts(dat)

			# Update Graph
			if inputs['graphing']:
				if ii % inputs['update_interval'] == 0 and ii > inputs['line_length']:
						current_frame = ii + 1
						updated_data = DAT_hist[(current_frame - inputs['line_length']):current_frame,:]
						GraphingUpdater(inputs, updated_data, plot_objects)

			if inputs['pedal']:
				pedal_input = PedalSerial.read()

				if pedal_input == '\x03':
					print 'QUITTING...'
					STBserial.close()
					if inputs['pedal']:
						PedalSerial.close()
					if inputs['video_capture']:
						videoThread.stop.set()


					sys.exit()
				elif pedal_input == '\x02':
					print 'PEDAL STOP'
					break

		# Send stop byte and get rid of any unread data
		STBserial.write('\x02')
		STBserial.flush()
		print 'FINISHED SAMPLING'
		print time.time()-start

		if inputs['video_capture']:
			videoThread.stop.set()

		if inputs['write_data'] == 1:

			print 'WRITING DATA TO %s...' %test_filename

			np.savetxt(test_path + '.csv', DAT_hist[:(ii+1),0:15], delimiter=",")

			print 'FINISHED WRITING'


		print '*'*80

		if not inputs['pedal']:
			break

except KeyboardInterrupt:
	print '***** ENDING TESTING *****'
	STBserial.close()
	if inputs['pedal']:
		PedalSerial.close()
	if inputs['video_capture']:
		videoThread.stop.set()









































