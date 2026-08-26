"""Pick a color from the camera frame and track matching objects.

Run this on the Raspberry Pi with a connected camera. Click a color in the
camera window to choose what to track, then adjust the HSV tolerance sliders in
the controls window until the mask isolates the object cleanly.
"""

import json
import time
from pathlib import Path

import cv2
import numpy as np

from motor_serial import DEFAULT_BAUD, DEFAULT_PORT, MotorSerial


WINDOW_CAMERA = "Color Picker Tracker"
WINDOW_MASK = "Tracked Mask"
WINDOW_CONTROLS = "HSV Controls"
SERIAL_PORT = DEFAULT_PORT
SERIAL_BAUD = DEFAULT_BAUD
SETTINGS_FILE = Path(__file__).with_name("color_picker_tracker_settings.json")
DEFAULT_SETTINGS = {
    "hue": 10,
    "sat": 60,
    "val": 60,
    "min_area": 500,
    "brightness": 0,
    "mirror": 0,
    "motor_enable": 0,
    "center_threshold": 30,
    "frame_rate": 5,
    "motor_pulse_ms": 250,
    "selected_hsv": None,
    "selected_bgr": None,
}


selected_hsv = None
selected_bgr = None


def nothing(_value):
    """OpenCV trackbar callback placeholder."""


def clamp(value, low, high):
    return max(low, min(high, value))


def clamp_int(value, low, high, default):
    try:
        return int(clamp(int(value), low, high))
    except (TypeError, ValueError):
        return default


def load_settings():
    settings = DEFAULT_SETTINGS.copy()
    if not SETTINGS_FILE.exists():
        return settings

    try:
        saved_settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return settings

    settings.update(
        {
            "hue": clamp_int(saved_settings.get("hue"), 0, 90, settings["hue"]),
            "sat": clamp_int(saved_settings.get("sat"), 0, 255, settings["sat"]),
            "val": clamp_int(saved_settings.get("val"), 0, 255, settings["val"]),
            "min_area": clamp_int(
                saved_settings.get("min_area"), 0, 20000, settings["min_area"]
            ),
            "brightness": clamp_int(
                saved_settings.get("brightness"), -100, 100, settings["brightness"]
            ),
            "mirror": clamp_int(saved_settings.get("mirror"), 0, 1, settings["mirror"]),
            "motor_enable": clamp_int(
                saved_settings.get("motor_enable"), 0, 1, settings["motor_enable"]
            ),
            "center_threshold": clamp_int(
                saved_settings.get("center_threshold"),
                5,
                300,
                settings["center_threshold"],
            ),
            "frame_rate": clamp_int(
                saved_settings.get("frame_rate"), 1, 30, settings["frame_rate"]
            ),
            "motor_pulse_ms": clamp_int(
                saved_settings.get("motor_pulse_ms"),
                0,
                3000,
                settings["motor_pulse_ms"],
            ),
        }
    )

    for key in ("selected_hsv", "selected_bgr"):
        value = saved_settings.get(key)
        if isinstance(value, list) and len(value) == 3:
            settings[key] = [clamp_int(component, 0, 255, 0) for component in value]

    if settings["selected_hsv"] is not None:
        settings["selected_hsv"][0] = clamp_int(settings["selected_hsv"][0], 0, 179, 0)

    return settings


def save_settings(settings):
    global selected_hsv, selected_bgr

    settings_to_save = {
        **settings,
        "selected_hsv": (
            [int(component) for component in selected_hsv]
            if selected_hsv is not None
            else None
        ),
        "selected_bgr": (
            [int(component) for component in selected_bgr]
            if selected_bgr is not None
            else None
        ),
    }

    SETTINGS_FILE.write_text(
        json.dumps(settings_to_save, indent=2) + "\n", encoding="utf-8"
    )


def on_mouse(event, x, y, _flags, frame_ref):
    """Save the HSV color under the mouse when the user clicks the frame."""
    global selected_hsv, selected_bgr

    if event != cv2.EVENT_LBUTTONDOWN:
        return

    frame = frame_ref["frame"]
    if frame is None:
        return

    selected_bgr = frame[y, x].copy()
    hsv_pixel = cv2.cvtColor(np.uint8([[selected_bgr]]), cv2.COLOR_BGR2HSV)
    selected_hsv = hsv_pixel[0][0]


def open_motor_serial():
    motors = MotorSerial(SERIAL_PORT, SERIAL_BAUD)
    motors.connect()
    return motors


def get_trackbars():
    return {
        "hue": cv2.getTrackbarPos("Hue +/-", WINDOW_CONTROLS),
        "sat": cv2.getTrackbarPos("Sat +/-", WINDOW_CONTROLS),
        "val": cv2.getTrackbarPos("Val +/-", WINDOW_CONTROLS),
        "min_area": cv2.getTrackbarPos("Min Area", WINDOW_CONTROLS),
        "brightness": cv2.getTrackbarPos("Brightness", WINDOW_CONTROLS) - 100,
        "mirror": cv2.getTrackbarPos("Mirror", WINDOW_CONTROLS),
        "motor_enable": cv2.getTrackbarPos("Motor Enable", WINDOW_CONTROLS),
        "center_threshold": cv2.getTrackbarPos("Center Threshold", WINDOW_CONTROLS),
        "frame_rate": cv2.getTrackbarPos("Frame FPS", WINDOW_CONTROLS),
        "motor_pulse_ms": cv2.getTrackbarPos("Pulse ms", WINDOW_CONTROLS),
    }


def build_hsv_mask(hsv_frame, target_hsv, tolerance):
    hue, sat, val = [int(component) for component in target_hsv]

    sat_low = clamp(sat - tolerance["sat"], 0, 255)
    sat_high = clamp(sat + tolerance["sat"], 0, 255)
    val_low = clamp(val - tolerance["val"], 0, 255)
    val_high = clamp(val + tolerance["val"], 0, 255)

    hue_low = hue - tolerance["hue"]
    hue_high = hue + tolerance["hue"]

    lower = np.array([clamp(hue_low, 0, 179), sat_low, val_low])
    upper = np.array([clamp(hue_high, 0, 179), sat_high, val_high])

    if hue_low < 0:
        lower_a = np.array([0, sat_low, val_low])
        upper_a = upper
        lower_b = np.array([180 + hue_low, sat_low, val_low])
        upper_b = np.array([179, sat_high, val_high])
        return cv2.bitwise_or(
            cv2.inRange(hsv_frame, lower_a, upper_a),
            cv2.inRange(hsv_frame, lower_b, upper_b),
        )

    if hue_high > 179:
        lower_a = lower
        upper_a = np.array([179, sat_high, val_high])
        lower_b = np.array([0, sat_low, val_low])
        upper_b = np.array([hue_high - 180, sat_high, val_high])
        return cv2.bitwise_or(
            cv2.inRange(hsv_frame, lower_a, upper_a),
            cv2.inRange(hsv_frame, lower_b, upper_b),
        )

    return cv2.inRange(hsv_frame, lower, upper)


def choose_motor_command(frame_shape, object_center, center_threshold):
    if object_center is None:
        return "S", "Searching"

    frame_h, frame_w = frame_shape[:2]
    frame_center = (frame_w // 2, frame_h // 2)
    delta_x = object_center[0] - frame_center[0]
    delta_y = object_center[1] - frame_center[1]

    if abs(delta_x) > center_threshold:
        return ("R", "Turn right") if delta_x < 0 else ("L", "Turn left")
    if abs(delta_y) > center_threshold:
        return ("F", "Move forward") if delta_y < 0 else ("B", "Move backward")
    return "S", "Centered"


def update_motor_pulse(motors, command, motor_enabled, pulse_ms, pulse_state):
    now = time.monotonic()
    if not motor_enabled or command == "S":
        motors.stop()
        pulse_state["command"] = None
        pulse_state["until"] = 0
        return

    pulse_seconds = pulse_ms / 1000
    pulse_expired = pulse_state["command"] is not None and now >= pulse_state["until"]
    command_changed = command != pulse_state["command"]

    if pulse_expired:
        motors.stop()
        pulse_state["command"] = None
        pulse_state["until"] = 0
        return

    if pulse_state["command"] is None or command_changed:
        motors.send(command, force=True)
        pulse_state["command"] = command
        pulse_state["until"] = now + pulse_seconds


def draw_center_threshold(frame, center_threshold):
    frame_h, frame_w = frame.shape[:2]
    center_x = frame_w // 2
    center_y = frame_h // 2
    cv2.rectangle(
        frame,
        (center_x - center_threshold, center_y - center_threshold),
        (center_x + center_threshold, center_y + center_threshold),
        (0, 255, 0),
        2,
    )
    cv2.line(frame, (center_x - 10, center_y), (center_x + 10, center_y), (0, 255, 0), 1)
    cv2.line(frame, (center_x, center_y - 10), (center_x, center_y + 10), (0, 255, 0), 1)


def draw_status(frame, action, command, motor_enabled, motor_status, settings):
    if selected_hsv is None:
        message = "Click an object color to track. Press s to save, q to quit."
    else:
        h, s, v = [int(component) for component in selected_hsv]
        b, g, r = [int(component) for component in selected_bgr]
        message = f"Tracking HSV({h}, {s}, {v})  BGR({b}, {g}, {r})"

    motor_mode = "ON" if motor_enabled else "OFF"
    action_message = f"Action: {action} ({command})  Motor: {motor_mode}"
    timing_message = (
        f"{motor_status}  FPS: {max(1, settings['frame_rate'])}  "
        f"Pulse: {settings['motor_pulse_ms']}ms"
    )

    cv2.rectangle(frame, (0, 0), (frame.shape[1], 94), (0, 0, 0), -1)
    cv2.putText(
        frame,
        message,
        (10, 23),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        action_message,
        (10, 52),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        timing_message,
        (10, 81),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )


def main():
    global selected_hsv, selected_bgr

    saved_settings = load_settings()
    if (
        saved_settings["selected_hsv"] is not None
        and saved_settings["selected_bgr"] is not None
    ):
        selected_hsv = np.array(saved_settings["selected_hsv"], dtype=np.uint8)
        selected_bgr = np.array(saved_settings["selected_bgr"], dtype=np.uint8)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open video device")

    motors = open_motor_serial()
    pulse_state = {"command": None, "until": 0}
    frame_ref = {"frame": None}

    cv2.namedWindow(WINDOW_CAMERA)
    cv2.namedWindow(WINDOW_MASK)
    cv2.namedWindow(WINDOW_CONTROLS)
    cv2.setMouseCallback(WINDOW_CAMERA, on_mouse, frame_ref)

    cv2.createTrackbar("Hue +/-", WINDOW_CONTROLS, saved_settings["hue"], 90, nothing)
    cv2.createTrackbar("Sat +/-", WINDOW_CONTROLS, saved_settings["sat"], 255, nothing)
    cv2.createTrackbar("Val +/-", WINDOW_CONTROLS, saved_settings["val"], 255, nothing)
    cv2.createTrackbar(
        "Min Area", WINDOW_CONTROLS, saved_settings["min_area"], 20000, nothing
    )
    cv2.createTrackbar(
        "Brightness", WINDOW_CONTROLS, saved_settings["brightness"] + 100, 200, nothing
    )
    cv2.createTrackbar("Mirror", WINDOW_CONTROLS, saved_settings["mirror"], 1, nothing)
    cv2.createTrackbar(
        "Motor Enable", WINDOW_CONTROLS, saved_settings["motor_enable"], 1, nothing
    )
    cv2.createTrackbar(
        "Center Threshold",
        WINDOW_CONTROLS,
        saved_settings["center_threshold"],
        300,
        nothing,
    )
    cv2.createTrackbar(
        "Frame FPS", WINDOW_CONTROLS, saved_settings["frame_rate"], 30, nothing
    )
    cv2.createTrackbar(
        "Pulse ms", WINDOW_CONTROLS, saved_settings["motor_pulse_ms"], 3000, nothing
    )

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        settings = get_trackbars()
        if settings["mirror"]:
            frame = cv2.flip(frame, 1)

        frame = cv2.convertScaleAbs(frame, alpha=1, beta=settings["brightness"])
        frame_ref["frame"] = frame
        display = frame.copy()
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        object_center = None

        if selected_hsv is not None:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = build_hsv_mask(hsv, selected_hsv, settings)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = [
                contour
                for contour in contours
                if cv2.contourArea(contour) >= settings["min_area"]
            ]

            if contours:
                contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(contour)
                center = (x + w // 2, y + h // 2)
                object_center = center
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.circle(display, center, 5, (0, 255, 255), -1)

        if selected_bgr is not None:
            color = tuple(int(component) for component in selected_bgr)
            cv2.rectangle(display, (10, 104), (70, 164), color, -1)
            cv2.rectangle(display, (10, 104), (70, 164), (255, 255, 255), 2)

        command, action = choose_motor_command(
            display.shape, object_center, settings["center_threshold"]
        )
        motor_enabled = bool(settings["motor_enable"])
        update_motor_pulse(
            motors,
            command,
            motor_enabled,
            settings["motor_pulse_ms"],
            pulse_state,
        )

        draw_center_threshold(display, settings["center_threshold"])
        draw_status(display, action, command, motor_enabled, motors.status, settings)
        cv2.imshow(WINDOW_CAMERA, display)
        cv2.imshow(WINDOW_MASK, mask)

        frame_delay_ms = int(1000 / max(1, settings["frame_rate"]))
        key = cv2.waitKey(frame_delay_ms) & 0xFF
        if key == ord("s"):
            save_settings(get_trackbars())
        elif key == ord("q") or key == 27:
            break

    save_settings(get_trackbars())
    motors.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
