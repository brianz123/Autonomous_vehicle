"""Manually test Arduino motor commands from the Raspberry Pi."""

import argparse
import time

from motor_serial import DEFAULT_BAUD, DEFAULT_PORT, MotorSerial, VALID_COMMANDS


def parse_args():
    parser = argparse.ArgumentParser(description="Test rover motors over Arduino serial.")
    parser.add_argument("--port", default=DEFAULT_PORT, help="Arduino serial port")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="Serial baud rate")
    parser.add_argument("--speed", type=int, default=180, help="Motor speed, 0-255")
    parser.add_argument(
        "--seconds",
        type=float,
        default=0.5,
        help="How long timed test commands should run",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    motors = MotorSerial(args.port, args.baud)
    if not motors.connect():
        print(f"Could not connect: {motors.status}")
        print("Install pyserial and check whether the Arduino is /dev/ttyACM0.")
        return

    motors.set_speed(args.speed)
    print(f"Connected to {args.port} at {args.baud}. Speed set to {args.speed}.")
    print("Commands: F B L R S, V<0-255>, T timed test, Q quit")

    try:
        while True:
            command = input("> ").strip().upper()
            if not command:
                continue
            if command == "Q":
                break
            if command == "T":
                for test_command in ("F", "B", "L", "R"):
                    print(test_command)
                    motors.send(test_command, force=True)
                    time.sleep(args.seconds)
                    motors.stop()
                    time.sleep(0.25)
                continue
            if command.startswith("V"):
                motors.set_speed(command[1:])
                continue
            if command in VALID_COMMANDS:
                motors.send(command, force=True)
                continue
            print("Use F, B, L, R, S, V<0-255>, T, or Q.")
    finally:
        motors.close()
        print("Motors stopped.")


if __name__ == "__main__":
    main()
