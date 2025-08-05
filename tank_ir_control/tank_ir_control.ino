#include <IRremote.hpp>

// Pin definitions for L298N motor driver
const int ENA = 9;   // Enable pin for motor A
const int IN1 = 8;   // Control pin 1 for motor A
const int IN2 = 7;   // Control pin 2 for motor A
const int ENB = 10;  // Enable pin for motor B
const int IN3 = 11;  // Control pin 1 for motor B
const int IN4 = 12;  // Control pin 2 for motor B

// IR receiver pin
const int IR_PIN = 3;

// Motor speed (0-255)
const int MOTOR_SPEED = 200;

// IR codes (replace with codes from your own remote)
#define IR_FORWARD  0x4243
#define IR_BACKWARD 0x4232
#define IR_LEFT     0x4234
#define IR_RIGHT    0x4235
#define IR_STOP     0x42C5
#define IR_MODE		0x4247
void setup() {
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  IrReceiver.begin(IR_PIN, ENABLE_LED_FEEDBACK);
}

void loop() {
  if (IrReceiver.decode()) {
    uint32_t code = IrReceiver.decodedIRData.decodedRawData;

    switch (code) {
      case IR_FORWARD:
        moveForward();
        break;
      case IR_BACKWARD:
        moveBackward();
        break;
      case IR_LEFT:
        turnLeft();
        break;
      case IR_RIGHT:
        turnRight();
        break;
      case IR_STOP:
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

