#include <IRremote.hpp>

// Pin definitions for L298N motor driver
const int ENA = 10;  // Enable pin for motor A (left)
const int IN3 = 12;  // Control pin 1 for motor A
const int IN4 = 7;   // Control pin 2 for motor A
const int ENB = 9;   // Enable pin for motor B (right)
const int IN1 = 8;   // Control pin 1 for motor B
const int IN2 = 11;  // Control pin 2 for motor B

// IR receiver pin
const int IR_PIN = 3;

// Motor speed (0-255) for basic forward/back commands
int motorSpeed = 255;

// IR codes (replace with your own remote values)
#define IR_FORWARD  0x4233
#define IR_BACKWARD 0x4232
#define IR_LEFT     0x4234
#define IR_RIGHT    0x4235
#define IR_STOP     0x425C
#define IR_MODE     0x4247

void setup() {
  Serial.begin(115200);
  pinMode(ENA, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  IrReceiver.begin(IR_PIN, ENABLE_LED_FEEDBACK);
  Serial.println(F("IR control ready"));
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    handleCommand(command);
  }

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
        drive(-motorSpeed, motorSpeed); // pivot left
        break;
      case IR_RIGHT:
        Serial.println(F("Command: RIGHT"));
        drive(motorSpeed, -motorSpeed); // pivot right
        break;
      case IR_STOP:
        Serial.println(F("Command: STOP"));
        stopMotors();
        break;
    }

    IrReceiver.resume(); // Receive the next value
  }
}

void handleCommand(const String &command) {
  if (command == "F") {
    Serial.println(F("Command: FORWARD"));
    moveForward();
  } else if (command == "B") {
    Serial.println(F("Command: BACKWARD"));
    moveBackward();
  } else if (command == "S") {
    Serial.println(F("Command: STOP"));
    stopMotors();
  } else if (command.startsWith("M")) {
    // Command format: M<left>,<right> with -255..255 speeds
    int comma = command.indexOf(',');
    if (comma > 1) {
      int left = command.substring(1, comma).toInt();
      int right = command.substring(comma + 1).toInt();
      drive(left, right);
      Serial.print(F("Set motors L:"));
      Serial.print(left);
      Serial.print(F(" R:"));
      Serial.println(right);
    }
  }
}

void moveForward() {
  drive(motorSpeed, motorSpeed);
}

void moveBackward() {
  drive(-motorSpeed, -motorSpeed);
}

void stopMotors() {
  drive(0, 0);
}

// Drive motors with signed speeds (-255..255)
void drive(int left, int right) {
  setMotor(ENA, IN3, IN4, left);   // left motor
  setMotor(ENB, IN1, IN2, right);  // right motor
}

// Helper to set one motor's speed and direction
void setMotor(int en, int in1, int in2, int speed) {
  int pwm = constrain(abs(speed), 0, 255);
  if (speed >= 0) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
  } else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
  }
  analogWrite(en, pwm);
}
