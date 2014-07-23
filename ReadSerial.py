#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pylab as pl
import numpy as np
import serial, sys, os, glob, pdb, time
from HapticsSTB import *


# Default values for command line inputs, checked right below here
inputs = {	'graphing' : 0,
			'line_length': 150,
			'bias_sample': 100,
			'update_interval': 50,
			'sample_time': 5,
			'write_data': 0,
			'sample_rate': 500,
}

help_message = """ ******
-bias_sample: Number of samples averaged to get Mini40 biasing vector
-sample_time: Sampling time in seconds
-sample_rate: data sampling rate in Hz (forced to 500Hz for plotting)
-write_data: Write data to timestamped file
-graphing: reduce sample rate and display line plots
    1: F/T graph
    2: Mini40 Channel Voltages
    3: Accelerometer Voltages
    4: Single Point Position
(GRAPHING OPTIONS)
-line_length: Length of graphing plot
-update_interval: Number of samples between plot updates
*****
"""

# Input handling, inputs beginning with '-' are considered commands, following
# string is converted to an int and assigned to the dictionary
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


# Open serial port, if default device not found list alternatives and ask for
# input

default_device = '/dev/tty.usbmodem409621'
alt_device = ''

try:
	ser = serial.Serial(default_device,6900, timeout=0.1)
except OSError:
	serial_devices = glob.glob('/dev/tty.usbmodem*')

	if serial_devices == []:
		print "NO SERIAL DEVICE FOUND, EXITING"
		sys.exit()

	for dev in range(0,len(serial_devices)):
		print "%d)" %dev + serial_devices[dev]

	use_device = input("Default device not found; Which do you want? :")

	try:
		alt_device = serial_devices[use_device]
		ser = serial.Serial(alt_device,6900, timeout=0.1)
	except OSError:
		print serial_devices[dev].upper() + " NOT VALID, EXITING"
		sys.exit()


# Graphing Initialization code
if inputs['graphing']:

	inputs['sample_rate'] = 500;
	print 'Forcing sample rate to 500Hz for graphing'
	line_length = inputs['line_length']
	pl.ion()

	# Force/Torque Graphing
	if inputs['graphing'] == 1:

		f, (axF, axT) =pl.subplots(2,1, sharex=True)

		axF.axis([0,line_length,-20,20])
		axF.grid()
		axT.axis([0,line_length,-2,2])
		axT.grid()


		FXline, = axF.plot([0] * line_length, color = 'r')
		FYline, = axF.plot([0] * line_length, color = 'g')
		FZline, = axF.plot([0] * line_length, color = 'b')
		TXline, = axT.plot([0] * line_length, color = 'c')
		TYline, = axT.plot([0] * line_length, color = 'm')
		TZline, = axT.plot([0] * line_length, color = 'y')

		axF.legend([FXline, FYline, FZline], ['FX', 'FY', 'FZ'])
		axT.legend([TXline, TYline, TZline], ['TX', 'TY', 'TZ'])



		pl.draw()

	# Mini40 Voltage Graphing
	elif inputs['graphing'] == 2:
		pl.axis([0,line_length,-5,5])
		pl.grid()

		C0line, = pl.plot([0] * line_length, color = 'brown')
		C1line, = pl.plot([0] * line_length, color = 'yellow')
		C2line, = pl.plot([0] * line_length, color = 'green')
		C3line, = pl.plot([0] * line_length, color = 'blue')
		C4line, = pl.plot([0] * line_length, color = 'purple')
		C5line, = pl.plot([0] * line_length, color = 'gray')

		pl.legend([C0line, C1line, C2line, C3line, C4line, C5line], 
			['Channel 0', 'Channel 1','Channel 2','Channel 3','Channel 4','Channel 5'])

		pl.draw()

	#Accelerometer Voltage Graphing
	elif inputs['graphing'] == 3:

		f, (ax1, ax2, ax3) =pl.subplots(3,1, sharex=True)

		ax1.axis([0,line_length,0,3.3])
		ax1.grid()
		ax2.axis([0,line_length,0,3.3])
		ax2.grid()
		ax3.axis([0,line_length,0,3.3])
		ax3.grid()

		A1Xline, = ax1.plot([0] * line_length, color = 'r')
		A1Yline, = ax1.plot([0] * line_length, color = 'g')
		A1Zline, = ax1.plot([0] * line_length, color = 'b')

		A2Xline, = ax2.plot([0] * line_length, color = 'r')
		A2Yline, = ax2.plot([0] * line_length, color = 'g')
		A2Zline, = ax2.plot([0] * line_length, color = 'b')

		A3Xline, = ax3.plot([0] * line_length, color = 'r')
		A3Yline, = ax3.plot([0] * line_length, color = 'g')
		A3Zline, = ax3.plot([0] * line_length, color = 'b')

		pl.draw()

	# 2D Position Plotting
	elif inputs['graphing'] == 4:

		pl.axis([-.075, .075, -.075, .075])
		pl.grid()
		touch_point, = pl.plot(0,0, marker="o", markersize=50)

		pl.draw()

	else:
		print "INVALID GRAPHING MODE"



# Try to read from serial port, if you don't get anything close and retry up
# to five times

def to16bit(x):
	if x > int('0b1111111111111111',2):
		raise ValueError

	high = (x&int('0b1111111100000000',2))>>8
	low = x&int('0b11111111',2)

	return chr(high)+chr(low)

ser.flush()
ser.write('\x02')
ser.write('\x01' + to16bit(inputs['sample_rate']))

for ii in range(1,6):
	testdat = ser.read(31)

	if testdat == '':
		if ii == 5:
			sys.exit()

		print 'Packet empty, retry #%d' %ii
		ser.close()
		
		if alt_device:
			ser = serial.Serial(alt_device,6900, timeout=0.1)
		else:
			ser = serial.Serial(default_device,6900, timeout=0.1)

		ser.flush()
		ser.write('\x02')
		ser.write('\x01')
		ser.write(to16bit(inputs['sample_rate']))


	else:
		break

# Prep serial connection
ser.flush()

## BIASING
# read first 500 samples and average to get bias

print "DON'T TOUCH BOARD, BIASING..."
bias_hist = np.zeros((6,inputs['bias_sample']))

for ii in range(0, inputs['bias_sample']):

	dat = ser.read(31)
	
	if dat == '':
		print 'nothing recieved'
		ser.close()
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


## SAMPLING
# Code takes samples for seconds defined in sample_time
# need to preallocate vectors

print 'STARTING DATA COLLECTION'
start = time.time()
num_samples = inputs['sample_rate']*inputs['sample_time']

FT_hist = np.zeros((num_samples, 6))
if inputs['graphing'] == 2:
	V_hist = np.zeros((num_samples,6))
ACC_hist = np.zeros((num_samples, 9))

for ii in range(0,num_samples):

	dat = ser.read(31)
	
	if dat == '':
		print 'nothing recieved!'
		ser.close()
		sys.exit()

	packet = ord(dat[30])
	
	if ii == 0:
		packet_old = packet
	elif packet > (packet_old+1)%256:
		print 'MISSED PACKET', packet, packet_old

	packet_old = packet

	# if ii == 0:
	# 	FT_hist = FT
	# 	ACC_hist = ACC
	# 	if inputs['graphing'] == 2:
	# 		V_hist = Serial2M40Volts(dat)
	FT_hist[ii,:] = Serial2FT(dat, bias)
	ACC_hist[ii,:] = Serial2Acc(dat)

	if inputs['graphing'] == 2:
		V_hist[ii,:] = Serial2M40Volts(dat)

	# Update Graph code
	if inputs['graphing']:
		if ii % inputs['update_interval'] == 0 and ii > line_length:

			current_frame = ii + 1
			if inputs['graphing'] == 1:

				FXline.set_ydata(FT_hist[(current_frame - line_length):current_frame,0].T)
				FYline.set_ydata(FT_hist[(current_frame - line_length):current_frame,1].T)
				FZline.set_ydata(FT_hist[(current_frame - line_length):current_frame,2].T)
				TXline.set_ydata(FT_hist[(current_frame - line_length):current_frame,3].T)
				TYline.set_ydata(FT_hist[(current_frame - line_length):current_frame,4].T)
				TZline.set_ydata(FT_hist[(current_frame - line_length):current_frame,5].T)

			if inputs['graphing'] == 2:

				C0line.set_ydata(V_hist[(current_frame- line_length):current_frame,0].T)
				C1line.set_ydata(V_hist[(current_frame- line_length):current_frame,1].T)
				C2line.set_ydata(V_hist[(current_frame- line_length):current_frame,2].T)
				C3line.set_ydata(V_hist[(current_frame- line_length):current_frame,3].T)
				C4line.set_ydata(V_hist[(current_frame- line_length):current_frame,4].T)
				C5line.set_ydata(V_hist[(current_frame- line_length):current_frame,5].T)
			
			if inputs['graphing'] == 3:

				A1Xline.set_ydata(ACC_hist[(current_frame - line_length):current_frame,0].T)
				A1Yline.set_ydata(ACC_hist[(current_frame - line_length):current_frame,1].T)
				A1Zline.set_ydata(ACC_hist[(current_frame - line_length):current_frame,2].T)

				A2Xline.set_ydata(ACC_hist[(current_frame - line_length):current_frame,3].T)
				A2Yline.set_ydata(ACC_hist[(current_frame - line_length):current_frame,4].T)
				A2Zline.set_ydata(ACC_hist[(current_frame - line_length):current_frame,5].T)

				A3Xline.set_ydata(ACC_hist[(current_frame - line_length):current_frame,6].T)
				A3Yline.set_ydata(ACC_hist[(current_frame - line_length):current_frame,7].T)
				A3Zline.set_ydata(ACC_hist[(current_frame - line_length):current_frame,8].T)

			if inputs['graphing'] == 4:

				if abs(FT[2]) > .1:
					x = -1*FT[4]/FT[2]
					y = FT[3]/FT[2]
				else:
					x = y = 0

				touch_point.set_ydata(y)
				touch_point.set_xdata(x)

			pl.draw()

ser.write('\x02')
ser.flush()
ser.close()
print 'Finished Sampling'
print time.time()-start
## RECORDING
# Saves data in timestamped .csv in TestData folder, creates folders if needed

if inputs['write_data'] == 1:

	data_dir = 'TestData'
	test_filename = 'STB_' + time.strftime('%H:%M')
	test_dir = time.strftime('%Y-%m-%d')

	if '' == glob.glob(data_dir):
		os.mkdir(data_dir)

	if '' == glob.glob(data_dir + '/' + test_dir):
		os.mkdir(data_dir + '/' + test_dir)

	test_path = data_dir + '/' + test_dir + '/' + test_filename
	np.savetxt(test_path, np.hstack((FT_hist, ACC_hist)), delimiter=",")







		