#!/usr/bin/env python

from cv2 import VideoCapture, VideoWriter
from cv2.cv import CV_FOURCC

import sys, os, glob, pdb, time, threading, subprocess

cap = VideoCapture(-1)
fourcc = CV_FOURCC(*'AVC1')

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

out = VideoWriter('test.mp4',fourcc, 20, (640,480))
videoThread = OpenCVThread(cap, out)
videoThread.start()

time.sleep(10)

videoThread.stop.set()