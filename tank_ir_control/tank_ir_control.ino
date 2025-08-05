#include <IRremote.hpp>

// Pin definitions for L298N motor driver
const int ENA = 10;   // Enable pin for motor A
const int IN1 = 12;   // Control pin 1 for motor A
const int IN2 = 7;   // Control pin 2 for motor A
const int ENB = 9; // Enable pin for motor B
const int IN3 = 8;  // Control pin 1 for motor B
const int IN4 = 11;  // Control pin 2 for motor B

// IR receiver pin
const int IR_PIN = 3;

// Motor speed (0-255)
const int MOTOR_SPEED = 255;

// IR codes (replace with codes from your own remote)
#define IR_FORWARD  0x4233
#define IR_BACKWARD 0x4232
#define IR_LEFT     0x4234
#define IR_RIGHT    0x4235
#define IR_STOP     0x425C
#define IR_MODE		0x4247
void setup() {
  Serial.begin(115200);
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  IrReceiver.begin(IR_PIN, ENABLE_LED_FEEDBACK);
  Serial.println(F("IR control ready"));
}

void loop() {
  if (IrReceiver.decode()) {
    uint32_t code = IrReceiver.decodedIRData.decodedRawData;
    Serial.print(F("Received code: 0x"));
    Serial.println(code, HEX);

    switch (code) {
      case IR_FORWARD:
        Serial.println(F("Command: FORWARD"));
        moveForward();
        break;
      case IR_BACKWARD:
        Serial.println(F("Command: BACKWARD"));
        moveBackward();
        break;
      case IR_LEFT:
        Serial.println(F("Command: LEFT"));
        turnLeft();
        break;
      case IR_RIGHT:
        Serial.println(F("Command: RIGHT"));
        turnRight();
        break;
      case IR_STOP:
        Serial.println(F("Command: STOP"));
        stopMotors();
        break;

    }

    IrReceiver.resume(); // Receive the next value
  }
}

void moveForward() {
  analogWrite(ENA, MOTOR_SPEED);
  analogWrite(ENB, MOTOR_SPEED);
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void moveBackward() {
  analogWrite(ENA, MOTOR_SPEED);
  analogWrite(ENB, MOTOR_SPEED);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void turnLeft() {
  analogWrite(ENA, MOTOR_SPEED);
  analogWrite(ENB, MOTOR_SPEED);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void turnRight() {
  analogWrite(ENA, MOTOR_SPEED);
  analogWrite(ENB, MOTOR_SPEED);
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void stopMotors() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

