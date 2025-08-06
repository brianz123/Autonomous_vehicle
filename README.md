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

## Hardware Connection

Connect the Raspberry Pi to the Arduino via USB or a direct TX/RX serial connection (ensure common ground). The Arduino drives the motors through an L298N driver board.

