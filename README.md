# AI Virtual Mouse

Control the desktop pointer with a webcam and one hand. The app uses OpenCV for video, MediaPipe for 21-point hand tracking, and PyAutoGUI for mouse events.

## Setup

1. Install Python 3.10 or newer.
2. In this folder, install dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

3. Start the app:

   ```powershell
   py virtual_mouse.py
   ```

Use `py virtual_mouse.py --camera 1` if your webcam is not camera 0. Press `Q` or `Esc` to exit. Moving the physical pointer to a screen corner also triggers PyAutoGUI's emergency stop.

## Render deployment

Create a new Render Blueprint from this repository and select `render.yaml`. Render will install the dependencies and start the web health page automatically.

The hosted page is informational only: Render cannot access your webcam, display, or desktop mouse. Run the project locally for gesture control.

## Gestures

| Gesture | Action |
| --- | --- |
| Move index finger | Move cursor |
| Pinch thumb + index | Left click |
| Pinch thumb + middle | Right click |
| Pinch thumb + index + middle, keep pinched | Drag; release to drop |
| Hold index + middle close and move up/down | Scroll |

## Notes

Good, even lighting and a plain background improve tracking. The green rectangle is the active camera area mapped to the full screen; keeping your index finger inside it improves edge control.
