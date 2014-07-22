# cython: profile=True

import numpy as np
cimport numpy as np
import pdb

# Calibrated linear transform for out Mini40, from channel voltages to forces
# and torques

ATI40_transform = np.array(    [[ 0.165175269, 	6.193716635,	-0.05972626,	0.020033203, 	-0.136667224, 	-6.42215241	],
								[ 0.002429674, 	-3.63579423,	0.466390998, 	7.308900211, 	-0.18369186, 	-3.65179797	],
								[ -10.5385017,	0.802731009,	-10.1357248,	0.359714766,	-10.0934065,	0.442593679	],
								[ 0.144765089,	-0.032574325,	0.004132077,	0.038285567, 	-0.145061852,	-0.010347366],
								[ -0.089833077,	-0.024635731,	0.165602185,	-0.009131771,	-0.080132747,	0.039589968	],
								[ 0.001846317,	0.085776855,	0.005262967,	0.088317691, 	0.001450272,	0.087714269	]], dtype=np.float) 

# Takes in a serial packet and 6-element bias vector, outputs a 6-element
# vector with forces and torques

# [Fx, Fy, Fz, Tx, Ty, Tz] = Serial2FT(data, bias)

def Serial2FT(str x, np.ndarray[np.float64_t, ndim = 1] bias):
	volts = np.zeros((6), dtype = np.float64)
	cdef int i, j, y

	for i in range(0,6):
		j = i*2
		y = (ord(x[j])<<8) + (ord(x[j+1]))
		if y > 2048:
			volts[5-i] = <float>(y - 4096)*0.002
		else:
			volts[5-i] = <float>y*0.002

	return np.dot(ATI40_transform, (volts - bias).T)

# Takes serial packet, returns accelerometer voltages

# [Acc1X, Acc1Y, Acc1Z, Acc2X, Acc2Y, Acc2Z, Acc3X, Acc3Y, Acc3Z] = Serial2Acc(data)

def Serial2Acc(str x):
	volts = np.zeros((9), dtype = np.float64)
	acc_order = [0,1,2,5,3,4,8,6,7] #Puts acc channels in x,y,z order

	cdef int i,j,y

	for i in range(0,9):
		j = (acc_order[i]+6)*2
		y = (ord(x[j])<<8) + (ord(x[j+1]))
		volts[i] = <float>y/1241

	return volts

# Takes serial packet, returns Mini40 Voltages

# [C0, C1, C2, C3, C4, C5] = Serial2M40Volts(data)

def Serial2M40Volts(str x):
	cdef int i, j, y
	volts = np.zeros((6), dtype = np.float64)
	for i in range(0,6):
		j = i*2
		y = (ord(x[j])<<8) + (ord(x[j+1]))
		if y > 2048:
			volts[5-i] = <float>(y - 4096)*0.002
		else:
			volts[5-i] = <float>y*0.002

	return volts


