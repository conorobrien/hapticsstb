#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pylab as pl
import numpy as np
import serial, sys, os, glob, pdb, time
from HapticsSTB import *


# Default values for command line inputs, checked right below here
inputs = {	'graphing' : 0,
			'line_length': 100,
			'bias_sample': 100,
			'update_interval': 20,
			'sample_length': 5,
}


# Input handling, inputs beginning with '-' are considered commands, following
# string is converted to an int and assigned to the dictionary
try:
	if len(sys.argv) > 1:
		for arg in range(0,len(sys.argv)):
			if sys.argv[arg][0] == '-':
				inputs[sys.argv[arg][1:].lower()] = int(sys.argv[arg+1])
except:
	print "Invalid Command!"

# Open serial port, if default device not found list alternatives and ask for
# input
try:
	ser = serial.Serial('/dev/tty.usbmodem409621',6900, timeout=0.1)
except OSError:
	serial_devices = glob.glob('/dev/tty.usbmodem*')

	if serial_devices == []:
		print "NO SERIAL DEVICE FOUND, EXITING"
		sys.exit()

	for dev in range(0,len(serial_devices)):
		print "%d)" %dev + serial_devices[dev]

	use_device = input("Default device not found; Which do you want? :")

	try:
		ser = serial.Serial(serial_devices[use_device],6900, timeout=0.1)
	except OSError:
		print serial_devices[dev].upper() + " NOT VALID, EXITING PROGRAM"
		sys.exit()

# Graphing Initialization code
if inputs['graphing']:

	line_length = inputs['line_length']
	pl.ion()
	pl.axis([0,line_length,-20,20])

	# Start interactive plot, initialize line objects

	Line1, = pl.plot([0] * line_length, color = 'r')
	Line2, = pl.plot([0] * line_length, color = 'g')
	Line3, = pl.plot([0] * line_length, color = 'b')
	Line4, = pl.plot([0] * line_length, color = 'c')
	Line5, = pl.plot([0] * line_length, color = 'm')
	Line6, = pl.plot([0] * line_length, color = 'y')

	pl.draw()

# Prep serial connection
ser.flush()

## BIASING
# read first 500 samples and average to get bias

bias_hist = np.zeros((6,inputs['bias_sample']))

for ii in range(0, inputs['bias_sample']):

	dat = ser.read(13)
	
	if dat == '':
		print 'nothing recieved'
		break

	packet = ord(dat[12])
	
	if ii == 0:
		packet_old = packet
	elif (packet > (packet_old+1)%256):
		print 'MISSED PACKET', packet, packet_old

	packet_old = packet

	bias_hist[:,ii] = [Serial2Volts(dat[10:12]),Serial2Volts(dat[8:10]),Serial2Volts(dat[6:8]),
						Serial2Volts(dat[4:6]),Serial2Volts(dat[2:4]),Serial2Volts(dat[0:2])]

bias = np.mean(bias_hist, axis=1).T
print 'BIAS MATRIX'
print bias


## SAMPLING
# Code takes samples for seconds defined in sample_length

for ii in range(0,500*inputs['sample_length']):

	dat = ser.read(13)
	
	if dat == '':
		print 'nothing recieved'
		break

	packet = ord(dat[12])
	
	if packet > (packet_old+1)%256:
		print 'MISSED PACKET', packet, packet_old

	packet_old = packet

	FT = Serial2FT(dat, bias)

	if ii == 0:
		FT_hist = FT

	else:
		# V = np.array([Serial2Volts(dat[0:2]),Serial2Volts(dat[2:4]),Serial2Volts(dat[4:6]),
		# 	 Serial2Volts(dat[6:8]),Serial2Volts(dat[8:10]),Serial2Volts(dat[10:12])])
		FT_hist = np.vstack((FT_hist,FT))

	# pdb.set_trace()

	if inputs['graphing']:
		if ii % inputs['update_interval'] == 0 and ii > line_length:
			# pdb.set_trace()
			Line1.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],0].T)
			Line2.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],1].T)
			Line3.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],2].T)
			Line4.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],3].T)
			Line5.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],4].T)
			Line6.set_ydata(FT_hist[(FT_hist.shape[0] - line_length):FT_hist.shape[0],5].T)

			
			pl.draw()


ser.close()

filename = 'TestData/STBTD_' + time.strftime('%Y-%m-%d_%H:%M') + '.csv'
try:
	np.savetxt(filename, FT_hist, delimiter=",")
except:
	os.mkdir('TestData')
	np.savetxt(filename, FT_hist, delimiter=",")







		