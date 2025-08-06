import serial

def main():
    # Update '/dev/ttyACM0' to match the port your Arduino uses.
    with serial.Serial('/dev/ttyACM0', 115200, timeout=1) as ser:
        print("Enter commands: F, B, L, R, S or V<0-255>")
        while True:
            try:
                cmd = input('> ').strip()
            except EOFError:
                break
            if not cmd:
                continue
            ser.write((cmd + '\n').encode('utf-8'))

if __name__ == '__main__':
    main()
