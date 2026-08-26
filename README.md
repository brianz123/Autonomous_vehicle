# Autonomous Vehicle Control

This repository contains an Arduino sketch for controlling a tank-style vehicle via an L298N motor driver. The sketch now supports commands sent from a Raspberry Pi (or any computer) over a serial connection.

## Arduino Firmware

The file [`tank_ir_control/tank_ir_control.ino`](tank_ir_control/tank_ir_control.ino) listens for simple text commands on the USB serial port:

- `F` – move forward
- `B` – move backward
- `L` – turn left
- `R` – turn right
- `S` – stop
- `V<0-255>` – set motor speed, e.g. `V180`

IR remote commands from the original project continue to work.

## Raspberry Pi Example

Use the provided `pi_serial_controller.py` script to send commands from a Raspberry Pi:

```bash
pip install pyserial
python pi_serial_controller.py
```

The script opens `/dev/ttyACM0` at 115200 baud. Adjust the port if your Arduino appears elsewhere.

Once running, type commands like `F`, `V150`, or `S` and press Enter to control the vehicle.

To verify the motors before using camera tracking, run:

```bash
python motor_test.py --speed 180
```

Use `F`, `B`, `L`, `R`, and `S` to test individual commands. Type `T` to run a
short timed test of each direction, and `Q` to quit. The Pi sends these commands
over serial to the Arduino; the Arduino controls the L298N motor pins.

## Camera Color Picker Tracker

Use `color_picker_tracker.py` to choose a color directly from the camera frame
and track the largest matching object:

```bash
pip install opencv-python numpy pyserial
python color_picker_tracker.py
```

Click the object color in the camera window. Use the HSV controls to widen or
narrow the selected color range, and adjust `Min Area` to ignore small noisy
spots. Turn on `Mirror` if you want the camera view flipped horizontally.

The tracker can also send motor commands to the Arduino over `/dev/ttyACM0`.
Set `Motor Enable` to `1` to allow movement, or leave it at `0` while tuning.
The camera view displays the current action and command. Adjust
`Center Threshold` to change how close the object must be to the center before
the rover stops.

Settings are saved automatically when you quit and loaded the next time you run
the tracker. Press `s` to save immediately, or press `q` or `Esc` to quit.

## Hardware Connection

Connect the Raspberry Pi to the Arduino via USB or a direct TX/RX serial connection (ensure common ground). The Arduino drives the motors through an L298N driver board.

