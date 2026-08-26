from motor_serial import DEFAULT_BAUD, DEFAULT_PORT, MotorSerial

def main():
    motors = MotorSerial(DEFAULT_PORT, DEFAULT_BAUD)
    if not motors.connect():
        print(f"Could not connect: {motors.status}")
        return

    print("Enter commands: F, B, L, R, S or V<0-255>. Type Q to quit.")
    try:
        while True:
            try:
                cmd = input('> ').strip().upper()
            except EOFError:
                break
            if not cmd:
                continue
            if cmd == "Q":
                break
            if cmd.startswith("V"):
                motors.set_speed(cmd[1:])
            else:
                motors.send(cmd, force=True)
    finally:
        motors.close()

if __name__ == '__main__':
    main()
