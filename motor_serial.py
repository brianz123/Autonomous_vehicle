"""Serial helpers for sending motor commands to the Arduino."""

import time

try:
    import serial
except ImportError:
    serial = None


DEFAULT_PORT = "/dev/ttyACM0"
DEFAULT_BAUD = 115200
VALID_COMMANDS = {"F", "B", "L", "R", "S"}


class MotorSerial:
    def __init__(self, port=DEFAULT_PORT, baud=DEFAULT_BAUD):
        self.port = port
        self.baud = baud
        self.connection = None
        self.last_command = None
        self.status = "disconnected"

    def connect(self):
        if serial is None:
            self.status = "pyserial not installed"
            return False

        try:
            self.connection = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)
            self.status = f"connected {self.port}"
            self.last_command = None
            return True
        except serial.SerialException as exc:
            self.connection = None
            self.status = f"unavailable: {exc}"
            return False

    def send(self, command, force=False):
        command = command.strip().upper()
        if not self.connection:
            return False
        if command == self.last_command and not force:
            return True

        try:
            self.connection.write((command + "\n").encode("utf-8"))
            self.last_command = command
            return True
        except serial.SerialException as exc:
            self.status = f"write failed: {exc}"
            return False

    def set_speed(self, speed):
        try:
            speed = int(speed)
        except (TypeError, ValueError):
            self.status = "invalid speed"
            return False

        speed = max(0, min(255, speed))
        return self.send(f"V{speed}", force=True)

    def stop(self, force=False):
        return self.send("S", force=force)

    def close(self):
        if self.connection:
            self.stop(force=True)
            self.connection.close()
            self.connection = None
        self.status = "disconnected"
