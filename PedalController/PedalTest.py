import serial

ser = serial.Serial('/dev/tty.usbmodem409631', 6900, timeout = .1)

while 1:
	if ser.Available():
		print ser.read()