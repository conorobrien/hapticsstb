# -*- coding: utf-8 -*-

import pylab as pl
import numpy as np
import serial
import pdb

def Raw2Volts(x):
	# Takes a serial Packet 'x' and returns the 6 channels in Volts, Data is
	# given in twos complement formal
	y = (ord(x[0])<<8) + ord(x[1])
	if y > 2048:
		return (y - 4096)#*0.0025
	else:
		return y#*0.0025

def Raw2FT(x, FT_transform, bias):
	# Takes a serial packet 'x', 6x6 matrix 'FT_transform', and a 1x6 vector
	# 'bias', both matrices are Numpy matrices, not arrays. Currently the
	# channels in x and bias are backwards compared to the transform, theyre
	# flipped in the code but will change that later to make life easier
	C = np.matrix([[0.0],[0.0],[0.0],[0.0],[0.0],[0.0]])
	for i in range(0,6):
		j = i*2
		C[i] = Raw2Volts(x[j:(j+2)])
	FT = FT_transform * (C[::-1] - bias[::-1])
	return FT

# Matrix transform into forces and torques, no transformation needed, just
# conversion to FT

working_matrix = np.matrix([[ 0.165175269, 	6.193716635,	-0.05972626,	0.020033203, 	-0.136667224, 	-6.42215241	],
							[ 0.002429674, 	-3.63579423,	0.466390998, 	7.308900211, 	-0.18369186, 	-3.65179797	],
							[ -10.5385017,	0.802731009,	-10.1357248,	0.359714766,	-10.0934065,	0.442593679	],
							[ 0.144765089,	-0.032574325,	0.004132077,	0.038285567, 	-0.145061852,	-0.010347366],
							[ -0.089833077,	-0.024635731,	0.165602185,	-0.009131771,	-0.080132747,	0.039589968	],
							[ 0.001846317,	0.085776855,	0.005262967,	0.088317691, 	0.001450272,	0.087714269	]]) 

# Open serial port, must try to make this more general later rather than hard-
# coding it in
ser = serial.Serial('/dev/tty.usbmodem409621',6900, timeout=0.1)
# ser = serial.Serial('/dev/tty.usbmodem22491',6900, timeout=0.1)
bias_sample = 500
line_length = 100

# Initialize lists and arrays, no preallocation yet, will start writing these
# to files

FX = [0]*line_length
FY = [0]*line_length
FZ = [0]*line_length

B1 = np.array([])
B2 = np.array([])
B3 = np.array([])
B4 = np.array([])
B5 = np.array([])
B6 = np.array([])

# Start interactive plot, initialize line objects
pl.ion()
pl.axis([0,line_length,-3000,3000])

FXline, = pl.plot([0] * line_length, color = 'red')
FYline, = pl.plot([0] * line_length, color = 'green')
FZline, = pl.plot([0] * line_length, color = 'blue')

pl.draw()

packet_old = 0
ser.flush()

# take samples and average to get bias vector

for ii in range(0, bias_sample):

	dat = ser.read(13)
	
	if dat == '':
		print 'nothing recieved'
		break

	packet = ord(dat[12])
	
	if packet > (packet_old+1)%256:
		print 'MISSED PACKET', packet, packet_old

	packet_old = packet
	B1 = np.append(B1, Raw2Volts(dat[0:2]))
	B2 = np.append(B2, Raw2Volts(dat[2:4]))
	B3 = np.append(B3, Raw2Volts(dat[4:6]))
	B4 = np.append(B4, Raw2Volts(dat[6:8]))
	B5 = np.append(B5, Raw2Volts(dat[8:10]))
	B6 = np.append(B6, Raw2Volts(dat[10:12]))

# Bias should be a numpy matrix for calculations later
bias = np.matrix([[0.0],[0.0],[0.0],[0.0],[0.0],[0.0]])
bias[0] = B1.mean()
bias[1] = B2.mean()
bias[2] = B3.mean()
bias[3] = B4.mean()
bias[4] = B5.mean()
bias[5] = B6.mean()

print 'BIAS MATRIX'
print bias

i = 0
while 1:

	dat = ser.read(13)
	
	if dat == '':
		print 'nothing recieved'
		break

	packet = ord(dat[12])
	
	if packet > (packet_old+1)%256:
		print 'MISSED PACKET', packet, packet_old

	packet_old = packet
	FX.append(Raw2Volts(dat[0:2]))
	FY.append(Raw2Volts(dat[2:4]))
	FZ.append(Raw2Volts(dat[4:6]))
	# FX.append(Raw2Volts(dat[6:8]))
	# FY.append(Raw2Volts(dat[8:10]))
	# FZ.append(Raw2Volts(dat[10:12]))
	# FT = Raw2FT(dat, working_matrix, bias)
	# FX.append(FT.item(0))
	# FY.append(FT.item(1))
	# FZ.append(FT.item(2))

	# Update figure every ten samples
	if i % 20 == 0:

		FXline.set_ydata(FX[(len(FX) - line_length):len(FX)])
		FYline.set_ydata(FY[(len(FY) - line_length):len(FY)])
		FZline.set_ydata(FZ[(len(FZ) - line_length):len(FZ)])

		pl.draw()

	i = i+1

## TODO 

# Figure out quicker way for matrix multiplication. Would be nice to
# stay in python but not necessary, maybe try porting to MATLAB?

# -Write function in C, try Cython

# -Try julia, not sure about serial though

# -MATLAB

# -Give up and do transform after data collection is over

# -Larger USB packets? Only doing a 13 byte packet, can use up to 64
#	* This would give more time for processing, but adds data

# -Two-way communication, will need to update status leds, also could give
# start-end codes and debugging info










		