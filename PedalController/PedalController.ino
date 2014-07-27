
volatile byte LED_state = HIGH;

void setup()
{
	Serial.begin(9600);
	pinMode(13, OUTPUT);
	pinMode(14, INPUT);
	digitalWrite(13, LED_state);
	attachInterrupt(14, isrService, FALLING);
	interrupts();

}


void loop()
{
	digitalWrite(13, LED_state);
}

void isrService()
{
	if (LED_state == HIGH)
		LED_state = LOW;
	else
		LED_state = HIGH;

	noInterrupts();
	Serial.write(LED_state);
	interrupts();

}