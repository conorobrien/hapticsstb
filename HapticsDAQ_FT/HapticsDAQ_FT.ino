#include <IntervalTimer.h>
#include <SPI.h>


#define RESET 			0x10

#define LED_1			4
#define LED_2			3
#define LED_3			6
#define LED_4			5

#define SETUP_ACC 		0x64
#define CONV_ACC 		0xC0
#define CS_ACC 			7

#define SETUP_FT		0x6B
#define CONV_FT 		0xD8
#define CS_FT			9

#define SAMPLE_RATE 	2000 // Delay in us between samples

#define SCAN_MODE00 	0x0
#define SCAN_MODE01 	0x1
#define SCAN_MODE10 	0x2
#define SCAN_MODE11 	0x3

#define CLOCK_MODE00 	0x0
#define CLOCK_MODE01 	0x1
#define CLOCK_MODE10 	0x2
#define CLOCK_MODE11 	0x3

#define REF_INT_DELAY 	0x0
#define REF_INT_NODELAY 0x2
#define REF_EXT_SINGLE	0x1
#define REF_EXT_DIFF	0x3

#define SINGLE		0x0
#define UNIPOLAR	0x2
#define BIPOLAR		0x3

#define START 0x01 
#define STOP 0x02
#define PING 0x03

IntervalTimer irq;


byte convReg(byte channel, byte scan_mode, byte temp)
{
	byte command = 0x80 | (channel << 3) | (scan_mode << 1) | (temp);
	return command;
}

byte setupReg(byte cksel, byte refsel, byte diffsel)
{
	byte command = 0x40 | (cksel << 4) | (refsel << 2) | (diffsel);
	return command;
}

void readADC(void)
{
	static byte j = 0;
	static byte data[31];
	byte i = 0;

	j++;

	Serial.flush();

	for (i = 0; i < 12; i++)
	{	
		digitalWrite(CS_FT, LOW);
		data[i] = SPI.transfer(0x00);
		digitalWrite(CS_FT, HIGH);
		delayMicroseconds(2);
	}

	for (i = 12; i < 30; i++)
	{	
		digitalWrite(CS_ACC, LOW);
		data[i] = SPI.transfer(0x00);
		digitalWrite(CS_ACC, HIGH);
		delayMicroseconds(2);
	}

	data[30] = j;

	Serial.write(data, 31);

	digitalWrite(CS_FT, LOW);
	SPI.transfer(CONV_FT);
	digitalWrite(CS_FT, HIGH);

	digitalWrite(CS_ACC, LOW);
	SPI.transfer(CONV_ACC);
	digitalWrite(CS_ACC, HIGH);

}
void pulseCS(char pin)
{
	// Pulses the CS line in between SPI bytes
	digitalWrite(pin, HIGH);
	delayMicroseconds(2);
	digitalWrite(pin, LOW);
}

void setupFT(void)
{
	digitalWrite(CS_FT, LOW);
	SPI.transfer(RESET);
	pulseCS(CS_FT);
	SPI.transfer(SETUP_FT);
	SPI.transfer(0xFF);
	pulseCS(CS_FT);
	SPI.transfer(CONV_FT);
	digitalWrite(CS_FT, HIGH);
}

void setupACC(void)
{
	digitalWrite(CS_ACC, LOW);
	SPI.transfer(RESET);
	pulseCS(CS_ACC);
	SPI.transfer(SETUP_ACC);
	pulseCS(CS_ACC);
	SPI.transfer(CONV_ACC);
	digitalWrite(CS_ACC, HIGH);
}

void setup(void)
{

	// Turn on LEDS (only LED_4 connected)
	pinMode(LED_1, OUTPUT);
	pinMode(LED_2, OUTPUT);
	pinMode(LED_3, OUTPUT);
	pinMode(LED_4, OUTPUT);
	digitalWrite(LED_1, HIGH);
	digitalWrite(LED_2, HIGH);
	digitalWrite(LED_3, HIGH);
	digitalWrite(LED_4, HIGH);

	// Start USB
	Serial.begin(9600);

	// Declare chip select pins, set to idle high
	pinMode(CS_ACC, OUTPUT);
	pinMode(CS_FT, OUTPUT);
	digitalWrite(CS_ACC, HIGH);
	digitalWrite(CS_FT, HIGH);

	// Start SPI, 8Mhz speed, Defaults to mode 0
	SPI.begin();
	SPI.setClockDivider(SPI_CLOCK_DIV2);
	SPI.setDataMode(SPI_MODE0);
}

void loop(void)
{
	byte message[5];
	byte sample_rate_buff[2];
	int sample_rate;
	byte packet_length;

	if (Serial.available())
	{
		noInterrupts();
		packet_length = Serial.available();

		for (int i = 0; i < packet_length; i++)
		{
			message[i] = Serial.read();
		}

		Serial.flush();

		if (message[0] == START)
		{
			if (packet_length > 1)
			{
				sample_rate = 1000000/((int)(message[1]<<8) + (int)message[2]);
				// delay(1);
			}

			else
			{
				sample_rate = SAMPLE_RATE;
			}
			
			// delay(1);
			setupACC();
			setupFT();
			
			delayMicroseconds(sample_rate);

			irq.begin(readADC, sample_rate);
		}

		if (message[0] == STOP)
			irq.end();

		if (message[0] == PING)
			{
				irq.end();
				Serial.flush();
				Serial.write(0x01);
			}
		
		if (!Serial.dtr())
			irq.end();	
		interrupts()

	}

}