"""Camera-controlled desktop mouse powered by MediaPipe hand tracking."""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass

import cv2
import mediapipe as mp


def running_under_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except ImportError:
        return False
    return get_script_run_ctx() is not None


if not running_under_streamlit():
    import pyautogui


@dataclass
class Settings:
    camera: int = 0
    frame_margin: int = 100
    smoothing: float = 0.22
    pinch_threshold: float = 0.045
    scroll_gain: float = 800.0


class VirtualMouse:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.screen_w, self.screen_h = pyautogui.size()
        self.prev_x = self.screen_w / 2
        self.prev_y = self.screen_h / 2
        self.dragging = False
        self.left_click_latched = False
        self.right_click_latched = False
        self.scroll_anchor: float | None = None

        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=0.65,
            min_tracking_confidence=0.65,
        )
        self.drawer = mp.solutions.drawing_utils
        self.hand_connections = mp.solutions.hands.HAND_CONNECTIONS

    @staticmethod
    def distance(a, b) -> float:
        return math.hypot(a.x - b.x, a.y - b.y)

    def release_buttons(self) -> None:
        if self.dragging:
            pyautogui.mouseUp(button="left")
            self.dragging = False

    def move_pointer(self, point, width: int, height: int) -> None:
        margin = self.settings.frame_margin
        x = min(max(point.x * width, margin), width - margin)
        y = min(max(point.y * height, margin), height - margin)
        target_x = (x - margin) * self.screen_w / (width - 2 * margin)
        target_y = (y - margin) * self.screen_h / (height - 2 * margin)
        alpha = self.settings.smoothing
        self.prev_x += (target_x - self.prev_x) * alpha
        self.prev_y += (target_y - self.prev_y) * alpha
        pyautogui.moveTo(self.prev_x, self.prev_y, _pause=False)

    def handle_hand(self, landmarks, width: int, height: int) -> str:
        thumb, index, middle = landmarks[4], landmarks[8], landmarks[12]
        thumb_index = self.distance(thumb, index)
        thumb_middle = self.distance(thumb, middle)

        # Index finger always steers the cursor. Pinching is then used for actions.
        self.move_pointer(index, width, height)

        if thumb_index < self.settings.pinch_threshold and thumb_middle < self.settings.pinch_threshold:
            # Three-finger pinch is a drag. Releasing ends it.
            if not self.dragging:
                pyautogui.mouseDown(button="left")
                self.dragging = True
            self.left_click_latched = True
            self.right_click_latched = True
            self.scroll_anchor = None
            return "DRAG"

        if thumb_index < self.settings.pinch_threshold:
            self.release_buttons()
            if not self.left_click_latched:
                pyautogui.click(button="left")
                self.left_click_latched = True
            self.right_click_latched = False
            self.scroll_anchor = None
            return "LEFT CLICK"

        if thumb_middle < self.settings.pinch_threshold:
            self.release_buttons()
            if not self.right_click_latched:
                pyautogui.click(button="right")
                self.right_click_latched = True
            self.left_click_latched = False
            self.scroll_anchor = None
            return "RIGHT CLICK"

        # Index and middle held close together become a scrolling mode.
        if self.distance(index, middle) < 0.065:
            if self.scroll_anchor is None:
                self.scroll_anchor = index.y
            delta = (self.scroll_anchor - index.y) * self.settings.scroll_gain
            if abs(delta) >= 1:
                pyautogui.scroll(int(delta), _pause=False)
                self.scroll_anchor = index.y
            self.release_buttons()
            self.left_click_latched = False
            self.right_click_latched = False
            return "SCROLL"

        self.release_buttons()
        self.left_click_latched = False
        self.right_click_latched = False
        self.scroll_anchor = None
        return "MOVE"

    def run(self) -> None:
        capture = cv2.VideoCapture(self.settings.camera)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if not capture.isOpened():
            raise RuntimeError(f"Could not open camera {self.settings.camera}.")

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("Camera frame could not be read.")
                frame = cv2.flip(frame, 1)
                height, width = frame.shape[:2]
                result = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                label = "NO HAND"

                if result.multi_hand_landmarks:
                    hand = result.multi_hand_landmarks[0]
                    self.drawer.draw_landmarks(frame, hand, self.hand_connections)
                    label = self.handle_hand(hand.landmark, width, height)
                else:
                    self.release_buttons()
                    self.left_click_latched = False
                    self.right_click_latched = False
                    self.scroll_anchor = None

                margin = self.settings.frame_margin
                cv2.rectangle(frame, (margin, margin), (width - margin, height - margin), (80, 220, 80), 2)
                cv2.putText(frame, label, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1, (80, 220, 80), 2)
                cv2.putText(frame, "Q: quit", (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 240, 240), 1)
                cv2.imshow("AI Virtual Mouse", frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
        finally:
            self.release_buttons()
            capture.release()
            self.hands.close()
            cv2.destroyAllWindows()


def parse_args() -> Settings:
    parser = argparse.ArgumentParser(description="Control your mouse with hand gestures.")
    parser.add_argument("--camera", type=int, default=0, help="camera index (default: 0)")
    parser.add_argument("--margin", type=int, default=100, help="active-frame margin in pixels")
    parser.add_argument("--smoothing", type=float, default=0.22, help="cursor smoothing, 0 to 1")
    args = parser.parse_args()
    if args.margin < 0:
        parser.error("--margin must be zero or greater")
    if not 0 < args.smoothing <= 1:
        parser.error("--smoothing must be greater than 0 and no greater than 1")
    return Settings(camera=args.camera, frame_margin=args.margin, smoothing=args.smoothing)


if __name__ == "__main__":
    if running_under_streamlit():
        import streamlit as st

        st.title("AI Virtual Mouse")
        st.warning("Run this app locally to use your webcam and control your desktop mouse.")
        st.write("Streamlit Cloud does not provide access to your webcam, display, or desktop pointer.")
    else:
        pyautogui.FAILSAFE = True
        try:
            VirtualMouse(parse_args()).run()
        except KeyboardInterrupt:
            pass
        except Exception as error:
            print(f"Error: {error}", file=sys.stderr)
            sys.exit(1)
