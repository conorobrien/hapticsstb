#! /usr/bin/env python
# -*- coding: utf-8 -*-

print "DONT RUN THIS, REFERENCE ONLY"
exit(1)

import pylab as pl
import numpy as np
import sys, os, glob, pdb, time, threading, subprocess
from cv2 import VideoCapture, VideoWriter
from cv2.cv import CV_FOURCC
from HapticsSTB import *
from STBClassTest import *



inputs = ArgParse(sys.argv)

## Video Capture Setup
if inputs['video_capture']:
	# OpenCV initialization, create videoCapture object and codec

	# Switch Capture Card input to s-video
	err = subprocess.call(['v4l2-ctl', '-i 4'])
	
	if err == 1:
		print "VIDEO CAPTURE ERROR, CHECK CARD AND TRY AGAIN"
		sys.exit()

	cap = VideoCapture(-1)
	fourcc = CV_FOURCC(*'XVID')

	# Thread function for video capture
	class OpenCVThread(threading.Thread):
		def __init__(self, cap, out):
			threading.Thread.__init__(self)
			self.stop = threading.Event()
			self.out = out
			self.cap = cap
			
		def run(self):
			while not self.stop.is_set():
				ret, frame = self.cap.read()
				if ret == True:
					self.out.write(frame)



# Graphing Initialization
if inputs['graphing']:

	inputs['sample_rate'] = 500;
	print 'Forcing sample rate to 500Hz for graphing'

	plot_objects = GraphingSetup(inputs)

# Auto Detection for USB, not needed on mac, but linux serial devices only
# show up as ttyACMn, not with a unique ID

(STB, PedalSerial) = DeviceID(inputs)

## BIASING
# read first 500 samples and average to get bias

print "DON'T TOUCH BOARD, BIASING..."
bias_hist = np.zeros((6,inputs['bias_sample']))

STB.start()

for ii in range(0, inputs['bias_sample']):

	try:
		dat = STB.read()
	except EmptyPacketError:
		print 'NOTHING RECIEVED, EXITING...'
		STB.close()
		if inputs['pedal']:
			PedalSerial.close()
		sys.exit()


	bias_hist[:,ii] = Serial2M40Volts(dat)

bias = np.mean(bias_hist, axis=1).T
print "SAFE TO TOUCH"
print 'BIAS MATRIX'
print bias
STB.stop()
## SAMPLING
# Code takes samples for seconds defined in sample_time

# set lengths for hist vectors, if pedal mode just preallocate for 10 min
# session

if inputs['pedal']:
	num_samples = inputs['sample_rate']*600
else:
	num_samples = inputs['sample_rate']*inputs['sample_time']


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

		# File operations, checks to make sure folders exist and  creates timestamp
		if inputs['write_data'] or inputs['video_capture']:
			data_dir = 'TestData'
			subject_dir = 'Subject'+str(inputs['subject']).zfill(3)
			test_filename =  'S' + str(inputs['subject']).zfill(3) + 'T' + str(inputs['task']) +'_' + time.strftime('%m-%d_%H-%M')
			test_path = data_dir + '/' + subject_dir + '/' + test_filename

			if [] == glob.glob(data_dir):
				print "MAKING " + data_dir
				os.mkdir(data_dir)

			if [] == glob.glob(data_dir + '/' + subject_dir):
				print "MAKING " + subject_dir
				os.mkdir(data_dir + '/' + subject_dir)

		# Video prep
		if inputs['video_capture']:
			out = VideoWriter(test_path+'.avi',fourcc, 29.970, (720,480))
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

		STB.start()

		for ii in range(0,num_samples):

			try:
				dat = STB.read()
			except EmptyPacketError:
				print 'NOTHING RECIEVED, EXITING...'
				STB.stop()
				if inputs['pedal']:
					PedalSerial.close()
				if inputs['video_capture']:
					videoThread.stop.set()
				sys.exit()


			DAT_hist[ii, 0:15] = Serial2Data(dat, bias)

			if inputs['graphing'] == 2:
				DAT_hist[ii,15:] = Serial2M40Volts(dat)

			# Update Graph
			if inputs['graphing']:
				if ii % inputs['update_interval'] == 0 and ii > inputs['line_length']:
						updated_data = DAT_hist[(ii + 1 - inputs['line_length']):(ii+1),:]
						GraphingUpdater(inputs, updated_data, plot_objects)

			if inputs['pedal']:
				pedal_input = PedalSerial.read()

				if pedal_input == '\x03':
					print 'THREE CLICKS'
					break


					sys.exit()
				elif pedal_input == '\x02':
					print 'PEDAL STOP'
					break

		STB.stop()

		print 'FINISHED SAMPLING'
		print time.time()-start

		if inputs['video_capture']:
			videoThread.stop.set()

		if inputs['write_data'] == 1:

			print 'WRITING DATA TO %s...' %test_filename

			np.savetxt(test_path + '.csv', DAT_hist[:(ii+1),0:15], delimiter=",")

			print 'FINISHED WRITING'

		if inputs['compress']:

			os.chdir(data_dir + '/' + subject_dir)
			err = subprocess.call(['7z','a',test_filename + '.7z', test_filename+ '.*'])
			os.chdir('../..')



		print '*'*80

		if not inputs['pedal']:
			break

except KeyboardInterrupt:
	print '***** ENDING TESTING *****'
	# STBserial.close()
	STB.stop()
	if inputs['pedal']:
		PedalSerial.close()
	if inputs['video_capture']:
		videoThread.stop.set()









































