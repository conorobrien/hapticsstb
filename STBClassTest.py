import numpy as np
import pylab as pl
import serial, sys, glob, time, pdb

# Error for HapticsSTB class
class EmptyPacketError(Exception):
	pass

# Class for the Sensor STB. Currently manages initialization, stop, start and reading raw serial packets
class STBSensor:

	def __init__(self, serial_device, sample_rate):
		self.device = serial_device
		if sample_rate > int('0xFFFF',16):
			raise ValueError
		high = (sample_rate&int('0xFF00',16))>>8
		low = sample_rate&int('0x00FF',16)
		self.sample_rate = chr(high)+chr(low)

	def start(self):
		self.device.write('\x01' + self.sample_rate)
		self.packet_old = 300

	def stop(self):
		self.device.write('\x02')
		self.device.flush()

	def read(self):
		dat = self.device.read(31)

		if dat == '' or len(dat) != 31:
			raise EmptyPacketError
		self.packet = ord(dat[30])
		
		if self.packet_old == 300:
			self.packet_old = self.packet
		elif self.packet != (self.packet_old+1)%256:
			print 'MISSED PACKET', self.packet, self.packet_old
			self.packet_old = self.packet
		else:
			self.packet_old = self.packet
		
		return dat

	def readMini40(self):
		dat = self.readSerial()
		return Serial2M40(dat)

	def readACC(self):
		dat = self.readSerial()
		return Serial2Acc(dat)

	def close(self):
		self.stop()
		self.device.close()

def ArgParse(args):
	# Dict for command line inputs, contains default values
	inputs = {	'subject': 1,
				'task': 1,
				'graphing': 0,
				'line_length': 250,
				'bias_sample': 100,
				'update_interval': 50,
				'sample_time': 5,
				'write_data': 1,
				'sample_rate': 3000,
				'pedal': 1,
				'video_capture': 1,
				'compress': 0,
	}

	# Message displayed for command line help
	help_message = """ ******
	-subject: Subject ID number
	-task: Task ID number
	-pedal: use foot pedal for controlling sampling
	-video_capture: Record video from Da Vinci
	-write_data: Write data to timestamped file
	-compress: Compresses data after recording, produces a 7z archive
	-bias_sample: Number of samples averaged to get Mini40 biasing vector
	-sample_time: Length of sample in seconds
	-sample_rate: data sampling rate in Hz (default 3kHz, forced to 500Hz for plotting)
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
		if len(args) > 1:
			for arg in range(0,len(args)):
				command = args[arg]
				if command[0] == '-':
					if command == '-help' or command == '-h':
						print help_message
						sys.exit()
					else:
						inputs[command[1:].lower()] = int(args[arg+1])
		return inputs
	except (NameError, ValueError, IndexError, KeyError) as e:
		print "Invalid Command!: " + str(e)
		sys.exit()

def DeviceID(inputs):

	devices = glob.glob('/dev/ttyACM*')

	if len(devices) < 2:
		print 'NOT ENOUGH DEVICES CONNECTED, EXITING...'
		sys.exit()

	STB = PedalSerial = 0

	for dev in devices:
		# Step through devices, pinging each one for a device ID
		test_device = serial.Serial(dev, timeout=0.1)
		test_device.write('\x02')
		time.sleep(0.05)
		test_device.flushInput()
		test_device.write('\x03')
	 	
		devID = test_device.read(200)[-1]	#Read out everything in the buffer, and look at the last byte for the ID

		if devID == '\x01':
			test_device.timeout = 0.05
			STB = STBSensor(test_device, inputs['sample_rate'])
		elif devID == '\x02':
			PedalSerial = test_device
			PedalSerial.timeout = 0
		else:
			print 'UNKNOWN DEVICE, EXITING...'
			sys.exit()

	if not STB or (inputs['pedal'] and not PedalSerial):
		return ()
	else:
		return (STB, PedalSerial)

def GraphingSetup(inputs):

	line_length = inputs['line_length']
	pl.ion()

	if inputs['graphing'] in [1,2,3]:
		start_time = -1*(line_length-1)/500.0
		times = np.linspace(start_time, 0, line_length)

	# Force/Torque Graphing
	if inputs['graphing'] == 1:

		f, (axF, axT) =pl.subplots(2,1, sharex=True)

		axF.axis([start_time, 0,-5,5])
		axF.grid()
		axT.axis([start_time, 0,-.5,.5])
		axT.grid()

		FXline, = axF.plot(times, [0] * line_length, color = 'r')
		FYline, = axF.plot(times, [0] * line_length, color = 'g')
		FZline, = axF.plot(times, [0] * line_length, color = 'b')
		TXline, = axT.plot(times, [0] * line_length, color = 'c')
		TYline, = axT.plot(times, [0] * line_length, color = 'm')
		TZline, = axT.plot(times, [0] * line_length, color = 'y')

		axF.legend([FXline, FYline, FZline], ['FX', 'FY', 'FZ'])
		axT.legend([TXline, TYline, TZline], ['TX', 'TY', 'TZ'])

		plot_objects = (FXline, FYline, FZline, TXline, TYline, TZline)

		pl.draw()

	# Mini40 Voltage Graphing
	elif inputs['graphing'] == 2:

		pl.axis([start_time, 0,-2,2])
		pl.grid()

		C0line, = pl.plot(times, [0] * line_length, color = 'brown')
		C1line, = pl.plot(times, [0] * line_length, color = 'yellow')
		C2line, = pl.plot(times, [0] * line_length, color = 'green')
		C3line, = pl.plot(times, [0] * line_length, color = 'blue')
		C4line, = pl.plot(times, [0] * line_length, color = 'purple')
		C5line, = pl.plot(times, [0] * line_length, color = 'gray')

		pl.legend([C0line, C1line, C2line, C3line, C4line, C5line], 
			['Channel 0', 'Channel 1','Channel 2','Channel 3','Channel 4','Channel 5'], loc=2)

		plot_objects = (C0line, C1line, C2line, C3line, C4line, C5line)
		pl.draw()

	#Accelerometer Voltage Graphing
	elif inputs['graphing'] == 3:

		f, (ax1, ax2, ax3) =pl.subplots(3,1, sharex=True)

		ax1.axis([start_time, 0,-.1,3.4])
		ax2.axis([start_time, 0,-.1,3.4])
		ax3.axis([start_time, 0,-.1,3.4])
		ax1.grid()
		ax2.grid()
		ax3.grid()

		A1Xline, = ax1.plot(times, [0] * line_length, color = 'r')
		A1Yline, = ax1.plot(times, [0] * line_length, color = 'g')
		A1Zline, = ax1.plot(times, [0] * line_length, color = 'b')
		A2Xline, = ax2.plot(times, [0] * line_length, color = 'r')
		A2Yline, = ax2.plot(times, [0] * line_length, color = 'g')
		A2Zline, = ax2.plot(times, [0] * line_length, color = 'b')
		A3Xline, = ax3.plot(times, [0] * line_length, color = 'r')
		A3Yline, = ax3.plot(times, [0] * line_length, color = 'g')
		A3Zline, = ax3.plot(times, [0] * line_length, color = 'b')

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
		return 0

	return plot_objects
