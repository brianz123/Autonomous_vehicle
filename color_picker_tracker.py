"""Pick a color from the camera frame and track matching objects.

Run this on the Raspberry Pi with a connected camera. Click a color in the
camera window to choose what to track, then adjust the HSV tolerance sliders in
the controls window until the mask isolates the object cleanly.
"""

import cv2
import numpy as np


WINDOW_CAMERA = "Color Picker Tracker"
WINDOW_MASK = "Tracked Mask"
WINDOW_CONTROLS = "HSV Controls"
TARGET_FPS = 5


selected_hsv = None
selected_bgr = None


def nothing(_value):
    """OpenCV trackbar callback placeholder."""


def clamp(value, low, high):
    return max(low, min(high, value))


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


def get_trackbars():
    return {
        "hue": cv2.getTrackbarPos("Hue +/-", WINDOW_CONTROLS),
        "sat": cv2.getTrackbarPos("Sat +/-", WINDOW_CONTROLS),
        "val": cv2.getTrackbarPos("Val +/-", WINDOW_CONTROLS),
        "min_area": cv2.getTrackbarPos("Min Area", WINDOW_CONTROLS),
        "brightness": cv2.getTrackbarPos("Brightness", WINDOW_CONTROLS) - 100,
        "mirror": cv2.getTrackbarPos("Mirror", WINDOW_CONTROLS),
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


def draw_status(frame):
    if selected_hsv is None:
        message = "Click an object color to start tracking. Press q to quit."
    else:
        h, s, v = [int(component) for component in selected_hsv]
        b, g, r = [int(component) for component in selected_bgr]
        message = f"Tracking HSV({h}, {s}, {v})  BGR({b}, {g}, {r})"

    cv2.rectangle(frame, (0, 0), (frame.shape[1], 34), (0, 0, 0), -1)
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


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open video device")

    frame_delay_ms = int(1000 / TARGET_FPS)
    frame_ref = {"frame": None}

    cv2.namedWindow(WINDOW_CAMERA)
    cv2.namedWindow(WINDOW_MASK)
    cv2.namedWindow(WINDOW_CONTROLS)
    cv2.setMouseCallback(WINDOW_CAMERA, on_mouse, frame_ref)

    cv2.createTrackbar("Hue +/-", WINDOW_CONTROLS, 10, 90, nothing)
    cv2.createTrackbar("Sat +/-", WINDOW_CONTROLS, 60, 255, nothing)
    cv2.createTrackbar("Val +/-", WINDOW_CONTROLS, 60, 255, nothing)
    cv2.createTrackbar("Min Area", WINDOW_CONTROLS, 500, 20000, nothing)
    cv2.createTrackbar("Brightness", WINDOW_CONTROLS, 100, 200, nothing)
    cv2.createTrackbar("Mirror", WINDOW_CONTROLS, 0, 1, nothing)

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
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.circle(display, center, 5, (0, 255, 255), -1)

        if selected_bgr is not None:
            color = tuple(int(component) for component in selected_bgr)
            cv2.rectangle(display, (10, 44), (70, 104), color, -1)
            cv2.rectangle(display, (10, 44), (70, 104), (255, 255, 255), 2)

        draw_status(display)
        cv2.imshow(WINDOW_CAMERA, display)
        cv2.imshow(WINDOW_MASK, mask)

        key = cv2.waitKey(frame_delay_ms) & 0xFF
        if key == ord("q") or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
