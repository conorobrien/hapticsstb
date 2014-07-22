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
}


# Input handling, inputs beginning with '-' are considered commands, following
# string is converted to an int and assigned to the dictionary
try:
	if len(sys.argv) > 1:
		for arg in range(1,len(sys.argv)):
			if sys.argv[arg][0] == '-':
				if sys.argv[arg] == '-help':
					print '-bias_sample: Number of samples averaged to get Mini40 offset vector'
					print '-sample_time: Sampling time in seconds'
					print '-graphing: reduce sample rate and display line plots'
					print '    1: F/T graph'
					print '    2: Mini40 Channel Voltages'
					print '    3: Accelerometer Voltages'
					print '    4: Single Point Position'
					print '(GRAPHING OPTIONS)'
					print '-line_length: Length of graphing plot'
					print '-update_interval: Number of samples between plot updates'
					sys.exit()
				else:
					inputs[sys.argv[arg][1:].lower()] = int(sys.argv[arg+1])
except NameError:
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


# Try to read from serial port, if you don't get anything close and retry up
# to five times
for ii in range(1,6):
	testdat = ser.read(31)

	if testdat == '':
		if ii == 5:
			sys.exit()

		print 'Packet empty, retry #%d' %ii
		ser.close()
		if alt_device:
			ser = serial.Serial(alt_device,6900, timeout=0.1)
			ser.flush()
		else:
			ser = serial.Serial(default_device,6900, timeout=0.1)
			ser.flush()

	else:
		break


# Graphing Initialization code
if inputs['graphing']:

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
		touch_point, = pl.plot(0,0, marker="o", markersize=50)

		pl.draw()

	else:
		print "INVALID GRAPHING MODE"

# Prep serial connection
ser.flush()

## BIASING
# read first 500 samples and average to get bias

print "DON'T TOUCH BOARD..."
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
# Code takes samples for seconds defined in sample_time (500 HZ SAMPLE RATE NOW)

for ii in range(0,500*inputs['sample_time']):

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

	FT = Serial2FT(dat, bias)
	ACC = Serial2Acc(dat)

	if ii == 0:
		FT_hist = FT
		ACC_hist = ACC
		if inputs['graphing'] == 2:
			V_hist = Serial2M40Volts(dat)


	else:
		FT_hist = np.vstack((FT_hist,FT))
		ACC_hist = np.vstack((ACC_hist, ACC))
		if inputs['graphing'] == 2:
			V_hist = np.vstack((V_hist, Serial2M40Volts(dat)))

	# pdb.set_trace()

	# Update Graph code
	if inputs['graphing']:
		if ii % inputs['update_interval'] == 0 and ii > line_length:

			if inputs['graphing'] == 1:

				FXline.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],0].T)
				FYline.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],1].T)
				FZline.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],2].T)
				TXline.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],3].T)
				TYline.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],4].T)
				TZline.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],5].T)

			if inputs['graphing'] == 2:

				C0line.set_ydata(V_hist[(V_hist.shape[0] - line_length):V_hist.shape[0],0].T)
				C1line.set_ydata(V_hist[(V_hist.shape[0] - line_length):V_hist.shape[0],1].T)
				C2line.set_ydata(V_hist[(V_hist.shape[0] - line_length):V_hist.shape[0],2].T)
				C3line.set_ydata(V_hist[(V_hist.shape[0] - line_length):V_hist.shape[0],3].T)
				C4line.set_ydata(V_hist[(V_hist.shape[0] - line_length):V_hist.shape[0],4].T)
				C5line.set_ydata(V_hist[(V_hist.shape[0] - line_length):V_hist.shape[0],5].T)
			
			if inputs['graphing'] == 3:

				A1Xline.set_ydata(ACC_hist[(ACC_hist.shape[0] - line_length):ACC_hist.shape[0],0].T)
				A1Yline.set_ydata(ACC_hist[(ACC_hist.shape[0] - line_length):ACC_hist.shape[0],1].T)
				A1Zline.set_ydata(ACC_hist[(ACC_hist.shape[0] - line_length):ACC_hist.shape[0],2].T)

				A2Xline.set_ydata(ACC_hist[(ACC_hist.shape[0] - line_length):ACC_hist.shape[0],3].T)
				A2Yline.set_ydata(ACC_hist[(ACC_hist.shape[0] - line_length):ACC_hist.shape[0],4].T)
				A2Zline.set_ydata(ACC_hist[(ACC_hist.shape[0] - line_length):ACC_hist.shape[0],5].T)

				A3Xline.set_ydata(ACC_hist[(ACC_hist.shape[0] - line_length):ACC_hist.shape[0],6].T)
				A3Yline.set_ydata(ACC_hist[(ACC_hist.shape[0] - line_length):ACC_hist.shape[0],7].T)
				A3Zline.set_ydata(ACC_hist[(ACC_hist.shape[0] - line_length):ACC_hist.shape[0],8].T)

			if inputs['graphing'] == 4:

				if abs(FT[2]) > .1:
					x = -1*FT[4]/FT[2]
					y = FT[3]/FT[2]
				else:
					x = y = 0

				touch_point.set_ydata(y)
				touch_point.set_xdata(x)

			pl.draw()

ser.flush()
ser.close()

## RECORDING
# Saves data in timestamped .csv in TestData folder, creates folder if needed

if inputs['write_data'] == 1:
	filename = 'TestData/STBTD_' + time.strftime('%Y-%m-%d_%H:%M') + '.csv'
	try:
		np.savetxt(filename, V_hist, delimiter=",")
	except:
		os.mkdir('TestData')
		np.savetxt(filename, V_hist, delimiter=",")







		