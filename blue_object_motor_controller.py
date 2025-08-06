"""Track a blue object and keep it centered using motor commands.

This script connects to an Arduino over serial and streams frames from the
default camera. A very simple computer vision pipeline finds the largest blue
object in each frame, compares its center to the center of the image and sends
single character commands to the Arduino to steer motors left/right/forward or
backward until the object is roughly centered.
"""

import cv2
import numpy as np
import serial
import time


def main():
    """Center a blue object using motor commands sent to an Arduino."""
    # Establish the serial connection. Adjust the port and baud rate for your
    # hardware configuration.
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    time.sleep(2)  # Wait briefly to allow the Arduino to reset

    # Open the default webcam. Index may need adjustment if multiple cameras
    # are present.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open video device")

    # Define the HSV range for a typical blue color. These values may require
    # calibration for different lighting conditions or cameras.
    lower_blue = np.array([100, 150, 50])
    upper_blue = np.array([140, 255, 255])

    center_threshold = 30  # How many pixels away from center is acceptable
    last_command = None  # Track previous command to avoid spamming serial

    while True:
        ret, frame = cap.read()
        if not ret:
            # If the frame cannot be read, exit the loop gracefully.
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        # Clean up the mask with a couple of erosions and dilations to remove
        # small blobs and noise.
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        command = 'S'
        if contours:
            # Use the largest contour found as our blue object.
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            # Draw a rectangle around the object for visualization.
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            frame_h, frame_w = frame.shape[:2]
            obj_x = x + w / 2
            obj_y = y + h / 2
            # Distance of the object center from the frame center.
            delta_x = obj_x - frame_w / 2
            delta_y = obj_y - frame_h / 2

            if abs(delta_x) > center_threshold:
                command = 'L' if delta_x < 0 else 'R'
            elif abs(delta_y) > center_threshold:
                command = 'F' if delta_y < 0 else 'B'

        # Only send a new command when it changes to avoid flooding the serial
        # connection.
        if command != last_command:
            ser.write((command + '\n').encode('utf-8'))
            last_command = command

        cv2.imshow('Blue Object Motor Controller', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Clean up resources on exit.
    cap.release()
    cv2.destroyAllWindows()
    ser.write(b'S\n')
    ser.close()


if __name__ == '__main__':
    main()
