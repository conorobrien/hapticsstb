#!/usr/bin/env python

import argparse
import glob
import os
import sys
import time
import termios
import fcntl

import numpy as np
import hapticsstb

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("-s", "--subject", type=str, default='1', help="Subject ID Number")
parser.add_argument("-t", "--task", type=str, default='1', help="Task ID Number")

parser.add_argument("-p", "--plot", type=int, default=0, choices=[1,2,3,4],
                    help=
"""Set sample rate to 500Hz and display line plots for
debugging
    1: F/T graph
    2: Mini40 Channel Voltages
    3: Accelerometer Gs
    4: Single Point Position
""")

parser.add_argument("--sample_rate", type=int, default=3000, help="STB sampling rate (default 3kHz, 500Hz if plotting)")
parser.add_argument("--sample_time", type=int, default=10, help="Length of trial run in sec (overridden if pedal active)")

parser.add_argument("--keyboard", default=False, action="store_true", help="Use keyboard to start and stop trials")
parser.add_argument("--no_pedal", dest="pedal", default=True, action="store_false", help="Don't use pedal to start and stop trials")
parser.add_argument("--no_video", dest="video", default=True, action="store_false", help="Don't record video")
parser.add_argument("--no_write", dest="write", default=True, action="store_false", help="Don't write data to disk")

args = parser.parse_args()

if args.keyboard:
    args.pedal = False
    fd = sys.stdin.fileno()
    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

def create_filename(subject, task, data_dir):
    subject_dir = 'Subject'+subject.zfill(3)
    test_filename =  'S' + subject.zfill(3) + 'T' + task +'_' + time.strftime('%m-%d_%H-%M')
    test_path = data_dir + '/' + subject_dir + '/' + test_filename

    if [] == glob.glob(data_dir):
        print "MAKING " + data_dir
        os.mkdir(data_dir)
    if [] == glob.glob(data_dir + '/' + subject_dir):
        print "MAKING " + subject_dir
        os.mkdir(data_dir + '/' + subject_dir)

    return test_path

sensor = hapticsstb.STB(args.sample_rate, pedal=args.pedal)

if args.plot:
    sensor.plot_init(args.plot, 5)

# Preallocate hist vector, use sensor.sample_rate since sample rate changes if you turn graphing on
if not args.pedal:
    sample_length = sensor.sample_rate*args.sample_time
else:
    sample_time = 1800
    sample_length = sensor.sample_rate*sample_time

sensor_hist = np.zeros((sample_length, 15))

print '*'*80
print "Biasing, make sure board is clear"
sensor.bias()
print sensor.bias_vector
print "Done!"
print '*'*80

while True: # Runs once if args.pedal is false
    try:

        # Block until single pedal press if using pedal
        if args.pedal:
            print "Waiting for Pedal Input"

            while True:
                pedal = sensor.pedal()
                if pedal == 1:
                    break
                elif pedal == 3:
                    print "Quitting!"
                    sys.exit()

        elif args.keyboard:
            print "Waiting for Keyboard Input (space to start/stop, q to quit)"

            while True:
                try:
                    keypress = sys.stdin.read(1)
                    if keypress == ' ':
                        break
                    elif keypress == 'q':
                        print "Quitting!"
                        sys.exit()
                except IOError: pass

        if args.write or args.video:
            test_filename = create_filename(args.subject, args.task, 'TestData')

        if args.video:
            video_filename = test_filename + '.avi'
            sensor.video_init(video_filename)

        else:
            print "Starting " + str(args.sample_time) + " second trial"

        print '*'*80
        print "Starting Sampling ..."
        sensor.start_sampling()

        for ii in range(0,sample_length):
            sensor_hist[ii, 0:15] = sensor.read_data()
            if args.plot:
                sensor.plot_update()

            if args.pedal:
                if sensor.pedal() == 2:
                    print "Pedal Break ..."
                    print '*'*80
                    break
            elif args.keyboard:
                try:
                    if sys.stdin.read(1) == ' ':
                        print "Key Break ..."
                        print '*'*80
                        break
                except IOError: pass

        else:
            if args.pedal or args.keyboard:
                print "Time Limit Reached! " + str(args.sample_time) + "s limit, adjust in code if needed"
                print '*'*80

    except KeyboardInterrupt: # This lets you ctrl-c out of the sampling loop safely, also breaks out of while loop
        break

    except:
        print "Closing Serial Port ..."
        sensor.close()
        if args.keyboard:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
        raise

    print 'Finished Sampling!'

    sensor.stop_sampling()
    
    if args.write:
        np.savetxt(test_filename + '.csv', sensor_hist[:(ii+1),0:15], delimiter=",")
        print 'Finished Writing!'

    print '*'*80

    if not args.pedal:
        break

sensor.close()
if args.keyboard:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
