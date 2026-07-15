"""GestureOS application entry point and orchestration."""
from __future__ import annotations

import logging
import time

from camera import Camera
from config import AppConfig
from gesture_actions import GestureActions
from gesture_detector import GestureDetector
from hand_tracker import HandTracker
from keyboard_controller import KeyboardController
from mouse_controller import MouseController
from ui import GestureOSUI
from utils import configure_logging
from voice_assistant import VoiceAssistant

LOG = logging.getLogger(__name__)


class GestureOSApp:
    """Coordinates independent camera, recognition, voice, and UI components."""

    def __init__(self) -> None:
        self.config = AppConfig.load()
        self.camera = Camera(self.config)
        self.tracker = HandTracker()
        self.detector = GestureDetector()
        keyboard = KeyboardController()
        self.actions = GestureActions(self.config, keyboard, MouseController(self.config))
        self.voice = VoiceAssistant(keyboard)
        self.running = False
        self._last_frame_at = time.monotonic()
        self.ui = GestureOSUI(self.toggle_detection, self.close, self.show_settings,
                              self.set_voice, self.set_mouse)
        self.ui.voice_enabled.set(self.config.voice_enabled)
        self.ui.mouse_enabled.set(self.config.mouse_enabled)

    def run(self) -> None:
        self.ui.root.after(15, self._tick)
        self.ui.root.mainloop()

    def toggle_detection(self) -> None:
        if self.running:
            self.running = False
            self.camera.stop()
            self.ui.set_running(False)
            self.ui.update_status(0, "No hand", "Stopped")
            return
        if self.camera.start():
            self.running = True
            self.ui.set_running(True)
            if self.config.voice_enabled:
                self.voice.start()
        else:
            self.ui.update_status(0, "No camera", "Could not open webcam")

    def _tick(self) -> None:
        if self.running:
            frame = self.camera.get_frame()
            if frame is not None:
                now = time.monotonic()
                fps = 1 / max(now - self._last_frame_at, 0.001)
                self._last_frame_at = now
                hand = self.tracker.process(frame)
                result = self.detector.detect(hand)
                try:
                    action = self.actions.execute(result)
                except Exception as error:  # Keep preview alive if OS automation fails.
                    LOG.exception("Input action failed")
                    action = f"Input error: {error}"
                self.ui.show_frame(frame)
                self.ui.update_status(fps, result.gesture.value, action, self.voice.latest_command())
        self.ui.root.after(max(1, int(1000 / self.config.fps_limit)), self._tick)

    def set_voice(self, enabled: bool) -> None:
        self.config.voice_enabled = enabled
        if enabled and self.running:
            self.voice.start()

    def set_mouse(self, enabled: bool) -> None:
        self.config.mouse_enabled = enabled

    def show_settings(self) -> None:
        self.ui.show_settings({
            "Camera": f"{self.config.camera_width} × {self.config.camera_height}",
            "Cursor smoothing": self.config.cursor_smoothing,
            "Click threshold": self.config.click_threshold,
            "Scroll speed": self.config.scroll_speed,
            "FPS limit": self.config.fps_limit,
        })

    def close(self) -> None:
        self.running = False
        self.camera.stop()
        self.voice.stop()
        self.tracker.close()
        self.config.save()
        self.ui.root.destroy()


if __name__ == "__main__":
    configure_logging()
    GestureOSApp().run()
