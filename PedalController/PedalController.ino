
#define DOUBLE_TAP_MIN 50
#define DOUBLE_TAP_MAX 500

#define PEDAL_PIN 14
#define LED_PIN 13
volatile byte pedal_state = 0;
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
	digitalWrite(LED_PIN, pedal_state);
	// attachInterrupt(14, isrService, FALLING);
	// interrupts();

}


void loop()
{
	digitalWrite(LED_PIN, !(pedal_state-1));

	while (!digitalRead(PEDAL_PIN));
	pedal_state = 1;
	while (digitalRead(PEDAL_PIN));

	start_time = millis();
	tap_interval = 0;

	while ((tap_interval <= DOUBLE_TAP_MAX) && (pedal_state < 3))
	{
		if(digitalRead(PEDAL_PIN) && (tap_interval >= DOUBLE_TAP_MIN))
		{
			pedal_state += 1;
			start_time = millis();
			while (digitalRead(PEDAL_PIN));
		}
		tap_interval = millis() - start_time;
	}

	Serial.write(pedal_state);
}

void isrService()
{
	tap_interval = millis() - last_tap;
	last_tap = millis();

	if (tap_interval > DOUBLE_TAP_MAX)
	{
		pedal_state = 1;
		third_tap = false;
	}
	else
	{
		if ((tap_interval >= DOUBLE_TAP_MIN) && (tap_interval <= DOUBLE_TAP_MAX))
			if (third_tap)
			{
				pedal_state = 2;
				third_tap = false;
			}
			else
			{
				pedal_state = 0;
				third_tap = true;
			}
	}

	noInterrupts();
	Serial.write(pedal_state);
	interrupts();

}