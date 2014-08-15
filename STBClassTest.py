
class EmptyPacketError(Exception):
	pass

class HapticsSTB:

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

