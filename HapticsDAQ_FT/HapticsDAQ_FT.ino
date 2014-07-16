#include <IntervalTimer.h>
#include <SPI.h>


#define RESET 			0x10
#define SETUP_ACC 		0x64
#define CONV_ACC 		0x90
#define CS_ACC 			7
#define SETUP_FT		0x6B
#define CONV_FT 		0xD8
#define CS_FT			9
#define SAMPLE_RATE 	5000 // Delay in us between samples

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


IntervalTimer irq;
byte conv_ft;
byte setup_ft;


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

void readADC_FT(void)
{
	static byte j = 0;
	static byte data[30];
	byte i = 0;

	j++;

	Serial.flush();

	// Read 6 bytes from ADC, conv. bit has already been sent
	for (i = 0; i < 12; i++)
	{	
		digitalWrite(CS_FT, LOW);
		data[i] = SPI.transfer(0x00);
		digitalWrite(CS_FT, HIGH);
		delayMicroseconds(2);
	}

	digitalWrite(CS_FT, HIGH);

	// Last byte of package is incremented, check for lost packets on master side
	data[12] = j;

	// Write data through USB
	Serial.write(data, 13);

	// Send conv start byte for next IRQ
	digitalWrite(CS_FT, LOW);
	SPI.transfer(CONV_FT);
	digitalWrite(CS_FT, HIGH);

}

void pulseCS(char pin)
{
	// Pulses the CS line in between SPI bytes
	digitalWrite(pin, HIGH);
	delayMicroseconds(2);
	digitalWrite(pin, LOW);
}

void setup(void)
{
	//define setup and conversion bits

	setup_ft = SETUP_FT ; //setupReg(CLOCK_MODE10, REF_INT_NODELAY, BIPOLAR); //0x6b
	conv_ft = CONV_FT; //convReg(11, SCAN_MODE00, 0);

	// Declare chip select pins, set to idle high
	pinMode(CS_ACC, OUTPUT);
	pinMode(CS_FT, OUTPUT);
	digitalWrite(CS_ACC, HIGH);
	digitalWrite(CS_FT, HIGH);

	// Start SPI, 8Mhz speed, Defaults to mode 0
	SPI.begin();
	SPI.setClockDivider(SPI_CLOCK_DIV2);
	SPI.setDataMode(SPI_MODE3);

	// Setup for Accelerometer ADC, resets, writes setup byte, then starts first conversion
	digitalWrite(CS_FT, LOW);
	SPI.transfer(RESET);
	pulseCS(CS_FT);
	SPI.transfer(setup_ft);
	// pulseCS(CS_FT);
	SPI.transfer(0xFF);
	pulseCS(CS_FT);
	SPI.transfer(conv_ft);
	digitalWrite(CS_FT, HIGH);

	// Short delay to let everything settle
	delay(100);

	// Start USB
	Serial.begin(9600);

	//Start timer interrupt
	irq.begin(readADC_FT, SAMPLE_RATE);

}

void loop(void)
{

}