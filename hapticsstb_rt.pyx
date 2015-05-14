# cython: profile=True

# These functions are time-sensitive functions for hapticsstb.py, you shouldn't have to call any of them directly

import numpy as np
cimport numpy as np
import pylab as pl

# Constants for plot types
PLOT_FT = 1
PLOT_M40V = 2
PLOT_ACC = 3
PLOT_POS = 4

# Calibrated linear transform for out Mini40, from channel voltages to forces
# and torques

M40_transform = np.array(  [[ 0.165175269, 	6.193716635,	-0.05972626,	0.020033203, 	-0.136667224, 	-6.42215241	],
							[ 0.002429674, 	-3.63579423,	0.466390998, 	7.308900211, 	-0.18369186, 	-3.65179797	],
							[ -10.5385017,	0.802731009,	-10.1357248,	0.359714766,	-10.0934065,	0.442593679	],
							[ 0.144765089,	-0.032574325,	0.004132077,	0.038285567, 	-0.145061852,	-0.010347366],
							[ -0.089833077,	-0.024635731,	0.165602185,	-0.009131771,	-0.080132747,	0.039589968	],
							[ 0.001846317,	0.085776855,	0.005262967,	0.088317691, 	0.001450272,	0.087714269	]], dtype=np.float) 

# Takes in a serial packet and 6-element bias vector, outputs a 6-element
# vector with forces and torques
# [Fx, Fy, Fz, Tx, Ty, Tz] = Serial2FT(packet, bias)

def serial_m40(str x, np.ndarray[np.float64_t, ndim = 1] bias):
	volts = np.zeros((6), dtype = np.float64)
	cdef int i, j, y

	for i in range(0,6):
		j = i*2
		y = (ord(x[j])<<8) + (ord(x[j+1]))
		if y > 2048:
			volts[5-i] = <float>(y - 4096)*0.002
		else:
			volts[5-i] = <float>y*0.002

	return np.dot(M40_transform, (volts - bias).T)


# Takes serial packet, returns accelerometer voltages
# [Acc1X, Acc1Y, Acc1Z, Acc2X, Acc2Y, Acc2Z, Acc3X, Acc3Y, Acc3Z] = Serial2Acc(packet)

def serial_acc(str x):
	gees = np.zeros((9), dtype = np.float64)
	acc_order = [0,1,2,5,3,4,8,6,7] #Puts acc channels in x,y,z order

	cdef int i,j,y

	for i in range(0,9):
		j = (acc_order[i]+6)*2
		y = (ord(x[j])<<8) + (ord(x[j+1]))
		gees[i] = ((<float>y/1241)-1.65)*(15.0/3.3)

	return gees

# Takes serial packet and bias, calls other two functions and returns both
# [Fx, Fy, Fz, Tx, Ty, Tz, Acc1X, Acc1Y, Acc1Z, Acc2X, Acc2Y, Acc2Z, Acc3X, Acc3Y, Acc3Z] = Serial2Data(packet, bias)
def serial_data(str x, np.ndarray[np.float64_t, ndim = 1] bias):
	FT = serial_m40(x, bias)
	ACC = serial_acc(x)

	return np.hstack((FT, ACC))

# Takes serial packet, returns Mini40 Voltages
# [V0, V1, V2, V3, V4, V5] = Serial2M40Volts(data)

def serial_m40v(str x):
	cdef int i, j, y
	volts = np.zeros((6), dtype = np.float64)
	for i in range(0,6):
		j = i*2
		y = (ord(x[j])<<8) + (ord(x[j+1]))
		if y > 2048: # This handles the twos complement negatives
			volts[5-i] = <float>(y - 4096)*0.002
		else:
			volts[5-i] = <float>y*0.002

	return volts

# Convenience function for creating two-byte serial packet for ints
def to16bit(x):
	if x > int('0xFFFF',16):
		raise ValueError

	high = (x&int('0xFF00',16))>>8
	low = x&int('0x00FF',16)

	return chr(high)+chr(low)

# Updates plots, called by STB.plot_update()
def plotting_updater(plot_type, np.ndarray[np.float64_t, ndim = 2] data, plot_objects):

	if plot_type == PLOT_FT:

		plot_objects[0].set_ydata(data[:,0].T)
		plot_objects[1].set_ydata(data[:,1].T)
		plot_objects[2].set_ydata(data[:,2].T)
		plot_objects[3].set_ydata(data[:,3].T)
		plot_objects[4].set_ydata(data[:,4].T)
		plot_objects[5].set_ydata(data[:,5].T)

	if plot_type == PLOT_M40V:

		plot_objects[0].set_ydata(data[:,0].T)
		plot_objects[1].set_ydata(data[:,1].T)
		plot_objects[2].set_ydata(data[:,2].T)
		plot_objects[3].set_ydata(data[:,3].T)
		plot_objects[4].set_ydata(data[:,4].T)
		plot_objects[5].set_ydata(data[:,5].T)
	
	if plot_type == PLOT_ACC:

		plot_objects[0].set_ydata(data[:,0].T)
		plot_objects[1].set_ydata(data[:,1].T)
		plot_objects[2].set_ydata(data[:,2].T)		

		plot_objects[3].set_ydata(data[:,3].T)
		plot_objects[4].set_ydata(data[:,4].T)
		plot_objects[5].set_ydata(data[:,5].T)		

		plot_objects[6].set_ydata(data[:,6].T)
		plot_objects[7].set_ydata(data[:,7].T)
		plot_objects[8].set_ydata(data[:,8].T)


	if plot_type == PLOT_POS:

		if abs(data[-1,2]) > .15:
			x = -1*data[-1,4]/data[-1,2]
			y = data[-1,3]/data[-1,2]
		else:
			x = y = 0

		plot_objects[0].set_ydata(y)
		plot_objects[0].set_xdata(x)

	pl.draw()
