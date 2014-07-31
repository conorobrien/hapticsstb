
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

}


void loop()
{
	if (Serial.available())
	{
		if (Serial.read() == 0x03)
			Serial.write(0x02);
	}

	digitalWrite(LED_PIN, !(pedal_state-1));

	while (!digitalRead(PEDAL_PIN))
	{
		if (Serial.available())
		{
			if (Serial.read() == 0x03)
				Serial.write(0x02);
		}
	}
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