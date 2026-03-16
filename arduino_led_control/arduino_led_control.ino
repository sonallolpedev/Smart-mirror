/*
 * Smart Mirror LED Control
 * Upload this code to your Arduino
 * 
 * Connections:
 * - LED positive (longer leg) -> Pin 13 (or your chosen pin)
 * - LED negative (shorter leg) -> GND (through 220 ohm resistor)
 * 
 * Or use the built-in LED on pin 13
 */

const int LED_PIN = 13;  // Change this if using different pin
bool ledState = false;

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);  // Start with LED off
  
  // Blink twice to indicate ready
  for(int i = 0; i < 2; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
  Serial.println("Arduino Ready");
}

void loop() {
  while (Serial.available() > 0) {
    char command = Serial.read();
    
    // Ignore newline and carriage return
    if (command == '\n' || command == '\r') {
      continue;
    }
    
    if (command == '1') {
      // Turn LED ON
      digitalWrite(LED_PIN, HIGH);
      ledState = true;
      Serial.println("LED ON");
    }
    else if (command == '0') {
      // Turn LED OFF
      digitalWrite(LED_PIN, LOW);
      ledState = false;
      Serial.println("LED OFF");
    }
  }
}
