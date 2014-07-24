import serial

ser = serial.Serial('/dev/tty.usbmodem409631', 6900, timeout = None)

while 1:
	x = ser.read()

	if x:
		print x