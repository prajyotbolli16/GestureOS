# GestureOS

GestureOS is a modular Windows desktop controller that uses webcam hand gestures and optional speech commands.

## Run

1. Use Python 3.12+ and install dependencies: `pip install -r requirements.txt`
2. Download the official MediaPipe Hand Landmarker model:
   ```powershell
   New-Item -ItemType Directory -Force assets
   Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task" -OutFile "assets/hand_landmarker.task"
   ```
3. Start the application: `python main.py`
4. Click **Start Detection** and grant camera/microphone permissions if Windows asks.

Voice control is optional. The core gesture application runs without PyAudio. To use a microphone with SpeechRecognition on Windows, install a PyAudio wheel compatible with your exact Python version, then enable **Voice** in the app.

GestureOS uses the current MediaPipe Hand Landmarker Tasks API. The hand model is intentionally kept out of the source files and downloaded into `assets/` during setup.

## Gestures

| Gesture | Behavior |
| --- | --- |
| Open palm | Opens the Windows Start menu |
| Index finger | Smooth cursor movement; pinch-to-click and hold-to-drag |
| Index + middle | Hand-up scrolls down; hand-down scrolls up |
| Pinch | Left-click on pinch start, hold to drag, release on pinch end |

Settings are kept in `settings.json`, generated on clean exit. Move the cursor into a screen corner to use PyAutoGUI's built-in failsafe.

The cursor uses a five-frame average, a low-pass smoothing filter, and a four-pixel dead zone. This makes it steadier at the cost of a small amount of lag; adjust `cursor_smoothing` (lower is smoother) and `cursor_deadzone` in `settings.json` after closing the app. Pinch interactions use the thumb-tip to index-tip distance with separate start and release thresholds, plus a 300 ms hold before drag begins.
