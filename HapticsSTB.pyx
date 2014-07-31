# cython: profile=True

import numpy as np
cimport numpy as np
import pylab as pl
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

def Serial2Data(str x, np.ndarray[np.float64_t, ndim = 1] bias):
	FT = Serial2FT(x, bias)
	ACC = Serial2Acc(x)

	return np.hstack((FT, ACC))

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

def GraphingSetup(inputs):

	line_length = inputs['line_length']
	pl.ion()

	# Force/Torque Graphing
	if inputs['graphing'] == 1:

		f, (axF, axT) =pl.subplots(2,1, sharex=True)

		axF.axis([0,line_length,-5,5])
		axF.grid()
		axT.axis([0,line_length,-.5,.5])
		axT.grid()


		FXline, = axF.plot([0] * line_length, color = 'r')
		FYline, = axF.plot([0] * line_length, color = 'g')
		FZline, = axF.plot([0] * line_length, color = 'b')
		TXline, = axT.plot([0] * line_length, color = 'c')
		TYline, = axT.plot([0] * line_length, color = 'm')
		TZline, = axT.plot([0] * line_length, color = 'y')

		axF.legend([FXline, FYline, FZline], ['FX', 'FY', 'FZ'])
		axT.legend([TXline, TYline, TZline], ['TX', 'TY', 'TZ'])

		plot_objects = (FXline, FYline, FZline, TXline, TYline, TZline)

		pl.draw()

	# Mini40 Voltage Graphing
	elif inputs['graphing'] == 2:
		pl.axis([0,line_length,-2,2])
		pl.grid()

		C0line, = pl.plot([0] * line_length, color = 'brown')
		C1line, = pl.plot([0] * line_length, color = 'yellow')
		C2line, = pl.plot([0] * line_length, color = 'green')
		C3line, = pl.plot([0] * line_length, color = 'blue')
		C4line, = pl.plot([0] * line_length, color = 'purple')
		C5line, = pl.plot([0] * line_length, color = 'gray')

		pl.legend([C0line, C1line, C2line, C3line, C4line, C5line], 
			['Channel 0', 'Channel 1','Channel 2','Channel 3','Channel 4','Channel 5'], loc=2)

		plot_objects = (C0line, C1line, C2line, C3line, C4line, C5line)
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

		plot_objects = (A1Xline, A1Yline, A1Zline, A2Xline, A2Yline, A2Zline, A3Xline, A3Yline, A3Zline)
		pl.draw()

	# 2D Position Plotting
	elif inputs['graphing'] == 4:

		pl.axis([-.075, .075, -.075, .075])
		pl.grid()
		touch_point, = pl.plot(0,0, marker="o", markersize=50)

		plot_objects = (touch_point,)
		pl.draw()

	else:
		print "INVALID GRAPHING MODE"

	return plot_objects

def GraphingUpdater(inputs, np.ndarray[np.float64_t, ndim  = 2] data, plot_objects):

	if inputs['graphing'] == 1:

		plot_objects[0].set_ydata(data[:,0].T)
		plot_objects[1].set_ydata(data[:,1].T)
		plot_objects[2].set_ydata(data[:,2].T)
		plot_objects[3].set_ydata(data[:,3].T)
		plot_objects[4].set_ydata(data[:,4].T)
		plot_objects[5].set_ydata(data[:,5].T)

	if inputs['graphing'] == 2:

		plot_objects[0].set_ydata(data[:,15].T)
		plot_objects[1].set_ydata(data[:,16].T)
		plot_objects[2].set_ydata(data[:,17].T)
		plot_objects[3].set_ydata(data[:,18].T)
		plot_objects[4].set_ydata(data[:,19].T)
		plot_objects[5].set_ydata(data[:,20].T)
	
	if inputs['graphing'] == 3:

		plot_objects[0].set_ydata(data[:,6].T)
		plot_objects[1].set_ydata(data[:,7].T)
		plot_objects[2].set_ydata(data[:,8].T)		

		plot_objects[3].set_ydata(data[:,9].T)
		plot_objects[4].set_ydata(data[:,10].T)
		plot_objects[5].set_ydata(data[:,11].T)		

		plot_objects[6].set_ydata(data[:,12].T)
		plot_objects[7].set_ydata(data[:,13].T)
		plot_objects[8].set_ydata(data[:,14].T)


	if inputs['graphing'] == 4:

		if abs(data[-1,2]) > .15:
			x = -1*data[-1,4]/data[-1,2]
			y = data[-1,3]/data[-1,2]
		else:
			x = y = 0

		plot_objects[0].set_ydata(y)
		plot_objects[0].set_xdata(x)

	pl.draw()

def to16bit(x):
	if x > int('0b1111111111111111',2):
		raise ValueError

	high = (x&int('0b1111111100000000',2))>>8
	low = x&int('0b11111111',2)

	return chr(high)+chr(low)