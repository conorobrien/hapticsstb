#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pylab as pl
import numpy as np
import serial, sys, os, glob, pdb, time, argparse
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
			'sample_rate': 500,
			'pedal': 0,
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

# Input handling, inputs beginning with '-' are considered commands, following
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


# Graphing Initialization
if inputs['graphing']:

	inputs['sample_rate'] = 500;
	print 'Forcing sample rate to 500Hz for graphing'

	plot_objects = GraphingSetup(inputs)

# Open serial port, if default STB not found list alternatives and ask for
# input

#This shouldnt be needed except for changing teensys

if sys.platform == 'darwin':
	device_folder = '/dev/tty.usbmodem*'

elif sys.platform == 'linux2':
	device_folder = '/dev/ttyACM*'

devices = glob.glob(device_folder)

for dev in devices:
	test_device = serial.Serial(dev, timeout=0.1)
	test_device.write('\x03')
	devID = test_device.read(1)

	if devID == '\x01':
		STBserial = test_device
		STBserial_port = dev
	elif devID == '\x02':
		PedalSerial = test_device
		PedalSerial.timeout = 0

# try:
# 	STBserial = serial.Serial(default_STB, timeout=0.1)
# except:
# 	serial_devices = glob.glob(device_folder)

# 	if serial_devices == []:
# 		print "NO SERIAL DEVICE FOUND, EXITING"
# 		sys.exit()

# 	for dev in range(0,len(serial_devices)):
# 		print "%d)" %dev + serial_devices[dev]

# 	use_device = input("Default device not found; Which do you want? :")

# 	try:
# 		alt_STB = serial_devices[use_device]
# 		STBserial = serial.Serial(alt_STB, timeout=0.1)
# 	except OSError:
# 		print serial_devices[dev].upper() + " NOT VALID, EXITING"
# 		sys.exit()

# Try to read from serial port, if you don't get anything close and retry up
# to five times

# Send a stop/start command in case of improper stop last time

STBserial.flush()
STBserial.write('\x02')
STBserial.write('\x01' + to16bit(inputs['sample_rate']))

for ii in range(1,6):
	testdat = STBserial.read(31)

	if testdat == '':
		if ii == 5:
			sys.exit()

		print 'Packet empty, retry #%d' %ii
		STBserial.close()

		ser = serial.Serial(STBserial_port,6900, timeout=0.1)

		STBserial.flush()
		STBserial.write('\x02')
		STBserial.write('\x01' + to16bit(inputs['sample_rate']))


	else:
		break

## BIASING
# read first 500 samples and average to get bias

print "DON'T TOUCH BOARD, BIASING..."
bias_hist = np.zeros((6,inputs['bias_sample']))

for ii in range(0, inputs['bias_sample']):

	dat = STBserial.read(31)
	
	if dat == '':
		print 'nothing recieved'
		STBserial.close()
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

# If plotting voltage as well, DAT_hist has an extra six columns at the end
# which contain the voltage channels

try:
	while 1:

		if inputs['pedal']:		
			print 'WAITING FOR PEDAL INPUT...'
			pedal_input = ''
			while pedal_input == '':
				pedal_input = PedalSerial.read()

			if pedal_input == '\x03':
				print 'QUITTING...'
				sys.exit()


		print 'STARTING DATA COLLECTION...'
		start = time.time()

		if inputs['graphing'] == 2:
			DAT_hist = np.zeros((num_samples,21))
		else:
			DAT_hist = np.zeros((num_samples, 15))

		STBserial.write('\x01' + to16bit(inputs['sample_rate']))

		for ii in range(0,num_samples):

			dat = STBserial.read(31)
			
			if dat == '':
				print 'NOTHING RECIEVED!'
				STBserial.close()
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
					sys.exit()
				elif pedal_input == '\x02':
					print 'PEDAL STOP'
					break

				
		# Send stop byte and get rid of any unread data
		STBserial.write('\x02')
		STBserial.flush()
		print 'FINISHED SAMPLING'
		print time.time()-start

		if inputs['write_data'] == 1:


			data_dir = 'TestData'
			subject_dir = 'Subject'+str(inputs['subject']).zfill(3)
			task_dir = 'Task' + str(inputs['task'])
			test_filename =  'S' + str(inputs['subject']).zfill(3) + 'T' + str(inputs['task']) +'_' + time.strftime('%m-%d_%H:%M')

			if [] == glob.glob(data_dir):
				print "MAKING " + data_dir
				os.mkdir(data_dir)

			if [] == glob.glob(data_dir + '/' + subject_dir):
				print "MAKING " + subject_dir
				os.mkdir(data_dir + '/' + subject_dir)

			print 'WRITING DATA TO %s...' %test_filename

			test_path = data_dir + '/' + subject_dir + '/' + test_filename + '.csv'
			np.savetxt(test_path, DAT_hist[:(ii+1),0:15], delimiter=",")

			print 'FINISHED WRITING'


		print '*'*80

		if not inputs['pedal']:
			break

except KeyboardInterrupt:
	print '***** ENDING TESTING *****'
	STBserial.close()
	PedalSerial.close()







































