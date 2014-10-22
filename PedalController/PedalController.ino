
#define DOUBLE_TAP_MIN 75
#define DOUBLE_TAP_MAX 200

#define PEDAL_PIN 14
#define LED_PIN 13
#define STATUS_PIN 10
#define STATUS_INT 255

volatile byte pedal_state = 2;
unsigned long start_time;
volatile unsigned long tap_interval = 1000;
volatile unsigned long last_tap = 0;
volatile boolean third_tap = 0;
byte first = 0;

void setup()
{
	Serial.begin(9600);
	pinMode(LED_PIN, OUTPUT);
	pinMode(PEDAL_PIN, INPUT);
	pinMode(STATUS_PIN, OUTPUT);
	digitalWrite(LED_PIN, pedal_state);
	analogWrite(STATUS_PIN, 0);

}


void loop()
{
	if (Serial.available())
	{
		if (Serial.read() == 0x03)
			Serial.write(0x02);
	}
	digitalWrite(LED_PIN, LOW);

	if (pedal_state == 1)
	{
		// analogWrite(STATUS_PIN, 0);
		digitalWrite(STATUS_PIN, LOW);
	}
	else
	{
		// analogWrite(STATUS_PIN, 200);
		digitalWrite(STATUS_PIN, HIGH);
	}

	while (!digitalRead(PEDAL_PIN))
	{
		if (Serial.available())
		{
			if (Serial.read() == 0x03)
				Serial.write(0x02);
		}
	}

	pedal_state = 1;
		digitalWrite(LED_PIN, HIGH);
	delay(DOUBLE_TAP_MIN);
	while (digitalRead(PEDAL_PIN));
	digitalWrite(LED_PIN, LOW);

	start_time = millis();
	tap_interval = 0;

	while (tap_interval <= DOUBLE_TAP_MAX)
	{	

		if(digitalRead(PEDAL_PIN) && (tap_interval >= DOUBLE_TAP_MIN))
		{
			pedal_state += 1;
			delay(DOUBLE_TAP_MIN);
			while (digitalRead(PEDAL_PIN));
			start_time = millis();

		}
		tap_interval = millis() - start_time;
	}

	if (pedal_state > 3)
		pedal_state = 3;

	Serial.write(pedal_state);
}