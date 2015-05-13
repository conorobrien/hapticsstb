import numpy as np
import pylab as pl

import glob
import serial
import subprocess
import sys
import threading
import time

from cv2 import VideoCapture, VideoWriter
from cv2.cv import CV_FOURCC

import hapticsstb_rt

# Constants for plotting
PLOT_FT = 1
PLOT_M40V = 2
PLOT_ACC = 3
PLOT_POS = 4

# Error for STB class
class EmptyPacketError(Exception):
    pass

# Class for the Haptics STB. Currently manages initialization, stop, start and reading raw serial packets
class STB:
    def __init__(self, sample_rate, **kwargs):
        if 'device' not in kwargs or kwargs['device'] == '':
            if sys.platform == 'darwin':
                devices = glob.glob('/dev/tty.usbmodem*')
            elif sys.platform == 'linux2':
                devices = glob.glob('/dev/ttyACM*')
            else:
                print "Unrecognized Platform!"

            for dev in devices:
                test_device = serial.Serial(dev, timeout=0.1)
                test_device.write('\x02')
                time.sleep(0.05)
                test_device.flushInput()
                test_device.write('\x03')

                devID = test_device.read(200)[-1]

                if devID == '\x01':
                    self.device = test_device
                    break
            else:
                print 'STB not found! Check all cables!'
                sys.exit()
        else:
            self.device = serial.Serial(kwargs['device'])

        if sample_rate > 100:
            self.device.timeout = 0.05
        else:
            self.device.timeout = 0.5

        if 'video' in kwargs and kwargs['video']:
            self.video = True
            err = subprocess.call(['v4l2-ctl', '-i 4'])
            if err == 1:
                print "VIDEO CAPTURE ERROR, CHECK CARD AND TRY AGAIN"
                sys.exit()

            self.cap = VideoCapture(-1)
            fourcc = CV_FOURCC(*'XVID')

            self.record = True
            self.out = VideoWriter(test_path+'.avi',fourcc, 29.970, (720,480))
            self.video_thread = OpenCVThread(self.cap, self.out)

        else:
            self.video = False

        self.frame = 0

        if sample_rate > 3000:
            print 'Sampling Rate too high!'
            raise ValueError

        self.update_rate(sample_rate)
        self.bias_vector = np.zeros(6,dtype=np.float64)

    def update_rate(self,sample_rate):
        self.sample_rate = sample_rate
        high = (sample_rate&int('0xFF00', 16))>>8
        low = sample_rate&int('0x00FF', 16)
        self.sample_rate_bytes = chr(high)+chr(low)

    def bias(self):
        bias_hist = np.zeros((self.sample_rate/5,6))
        self.start_sampling()
        for ii in range(0, self.sample_rate/5):
            bias_hist[ii,:] = self.read_M40V()

        self.stop_sampling()
        self.bias_vector = np.mean(bias_hist, axis=0)

    def start_sampling(self):
        self.device.write('\x01' + self.sample_rate_bytes)
        self.packet_old = 300

        if self.video:
            self.video_thread.start()

    def stop_sampling(self):
        self.device.write('\x02')
        self.device.flush()

        if self.video:
            self.video_thread.stop.set()

    def read_packet(self):
        pack = self.device.read(31)

        if pack == '' or len(pack) != 31:
            raise EmptyPacketError
        packet_new = ord(pack[30])
        
        if self.packet_old >= 256:
            self.packet_old = packet_new
        elif packet_new != (self.packet_old+1)%256:
            print 'MISSED PACKET', packet_new, self.packet_old
        
        self.packet_old = packet_new
        self.pack = pack
        return pack

    def read_data(self):
        self.pack = self.read_packet()
        return hapticsstb_rt.Serial2Data(self.pack, self.bias_vector)

    def read_M40(self):
        self.pack = self.read_packet()
        return hapticsstb_rt.Serial2M40(self.pack, self.bias_vector)

    def get_M40(self):
        return hapticsstb_rt.Serial2M40(self.pack, self.bias_vector)

    def read_M40V(self):
        self.pack = self.read_packet()
        return hapticsstb_rt.Serial2M40Volts(self.pack)

    def get_M40V(self):
        return hapticsstb_rt.Serial2M40Volts(self.pack)

    def read_ACC(self):
        self.pack = self.read_packet()
        return hapticsstb_rt.Serial2Acc(self.pack)

    def get_ACC(self):
        return hapticsstb_rt.Serial2Acc(self.pack)

    def plot_init(self, plot_type, plot_length):
        self.update_rate(500)
        self.line_length = self.sample_rate*plot_length
        self.plot_objects = PlottingSetup(plot_type, self.line_length)
        self.plot_type = plot_type
        self.frame = 1

        if self.plot_type in [PLOT_FT, PLOT_M40V, PLOT_POS]:
            self.plot_data = np.zeros((self.line_length, 6))
        elif self.plot_type == PLOT_ACC:
            self.plot_data = np.zeros((self.line_length, 9))
        else:
            print "Unrecognized plotting type!"
            sys.exit

    def plot_update(self):
        if self.plot_type in [PLOT_FT, PLOT_POS]:
            new_data = self.get_M40()
        elif self.plot_type == PLOT_M40V:
            new_data = self.get_M40V()
        elif self.plot_type == PLOT_ACC:
            new_data = self.get_ACC()

        self.plot_data = np.roll(self.plot_data,-1,axis=0)
        self.plot_data[self.line_length-1,0:] = new_data
        if self.frame % 50 == 0:
            hapticsstb_rt.PlottingUpdater(self.plot_type, self.plot_data, self.plot_objects)
            self.frame = 1
        else:
            self.frame += 1

    def close(self):
        self.stop_sampling()
        self.device.close()

# Used by HapticsSTB class to access pedal
# class Pedal:

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

def ArgParse(args):
    # Dict for command line inputs, contains default values
    inputs = {  'subject': 1,
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
        
        devID = test_device.read(200)[-1]   #Read out everything in the buffer, and look at the last byte for the ID

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

class Plot:
    def __init__(self, plot_type, plot_length):
        self.line_length = 500*plot_length
        self.plot_objects = PlottingSetup(plot_type, self.line_length)
        self.plot_type = plot_type
        self.frame = 1

        self.data = np.ones((self.line_length, 15))

    def Update(self, new_data):
        self.data = np.roll(self.data,-1,axis=0)
        self.data[self.line_length-1,0:] = new_data
        if self.frame % 50 == 0:
            hapticsstb_rt.PlottingUpdater(self.plot_type, self.data, self.plot_objects)
            self.frame = 1
        else:
            self.frame += 1


def PlottingSetup(plot_type, line_length):

    pl.ion()

    if plot_type in [PLOT_FT,PLOT_M40V,PLOT_ACC]:
        start_time = -1*(line_length-1)/500.0
        times = np.linspace(start_time, 0, line_length)

    # Force/Torque Graphing
    if plot_type == PLOT_FT:

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
    elif plot_type == PLOT_M40V:

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
    elif plot_type == PLOT_ACC:

        f, (ax1, ax2, ax3) =pl.subplots(3,1, sharex=True)

        ax1.axis([start_time, 0,-7,7])
        ax2.axis([start_time, 0,-7,7])
        ax3.axis([start_time, 0,-7,7])
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
    elif plot_type == 4:

        pl.axis([-.075, .075, -.075, .075])
        pl.grid()
        touch_point, = pl.plot(0,0, marker="o", markersize=50)

        plot_objects = (touch_point,)
        pl.draw()

    else:
        print "INVALID GRAPHING MODE"
        return 0

    return plot_objects
