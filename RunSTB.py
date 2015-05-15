#!/usr/bin/env python

import argparse
import glob
import os
import time

import numpy as np
import hapticsstb

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("-s", "--subject", type=str, default=1, help="Subject ID Number")
parser.add_argument("-t", "--task", type=str, default=1, help="Task ID Number")

parser.add_argument("-p", "--plot", type=int, default=0, choices=[1,2,3,4],
                    help=
"""Set sample rate to 500Hz and display line plots for\ndebugging
    1: F/T graph
    2: Mini40 Channel Voltages
    3: Accelerometer Gs
    4: Single Point Plate Position
""")

parser.add_argument("--no_pedal", dest="pedal", action="store_false", help="Don't use pedal to start and stop trials")
parser.add_argument("--no_video", dest="video", action="store_false", help="Don't record video")
parser.add_argument("--no_write", dest="write", action="store_false", help="Don't write data to disk")

parser.add_argument("--sample_rate", type=int, default=3000, help="STB sampling rate (default 3kHz, 500Hz if plotting)")
parser.add_argument("--sample_time", type=float, default=30, help="Length of trial run in sec (overridden if pedal active)")

args = parser.parse_args()

if args.write or args.video:
    data_dir = 'TestData'
    subject_dir = 'Subject'+args.subject.zfill(3)
    test_filename =  'S' + args.subject.zfill(3) + 'T' + args.task.zfill(2) +'_' + time.strftime('%m-%d_%H-%M')
    test_path = data_dir + '/' + subject_dir + '/' + test_filename

    if [] == glob.glob(data_dir):
        print "MAKING " + data_dir
        os.mkdir(data_dir)
    if [] == glob.glob(data_dir + '/' + subject_dir):
        print "MAKING " + subject_dir
        os.mkdir(data_dir + '/' + subject_dir)

if args.video:
    video_filename = test_filename + '.avi'
else:
    video_filename = ''

sensor = hapticsstb.STB(args.sample_rate, pedal=args.pedal, video=video_filename)

# Preallocate hist vector, use sensor.sample_rate since sample rate changes if you turn graphing on
if not args.pedal:
    sample_length = sensor.sample_rate*args.sample_time
else:
    sample_time = 600
    sample_length = sensor.sample_rate*sample_time

sensor_hist = np.zeros((sample_length,15))

if args.plot:
    sensor.plot_init(args.plot, 5)

print '*'*80
print "Biasing, make sure board is clear"
sensor.bias():
print sensor.bias_vector
print "Done!"
print '*'*80



# Block until single pedal press
if args.pedal:
    print "Waiting for Pedal Input"

    while sensor.pedal() != 1:
        pass

else:
    print 'Starting ' + str(args.sample_time) ' second trial'

print '*'*80
print "Starting Sampling ..."
sensor.start_sampling()

try:
    for ii in range(0,sample_length):
        sensor_hist[ii, 0:15] = sensor.read_data()
        if args.plot:
            sensor.plot_update()

        if args.pedal:
            if sensor.pedal() == 2:
                print "Pedal Break, Finishing Testing"
                print '*'*80
                break

    else:
        if args.pedal:
            print "Time Limit Reached! " + str(args.sample_time) + "s limit, adjust in code if needed"
            print '*'*80

except KeyboardInterrupt: # This lets you ctrl-c out of the sampling loop safely
    pass

except:
    sensor.close()
    raise

sensor.close()

if args.write:
    np.savetxt(test_filename + '.csv', sensor_hist[:(ii+1),0:15], delimiter=",")
