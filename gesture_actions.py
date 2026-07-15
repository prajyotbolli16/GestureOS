"""Maps recognized gestures to input actions."""
from __future__ import annotations

from config import AppConfig
from gesture_detector import Gesture, GestureResult
from keyboard_controller import KeyboardController
from mouse_controller import MouseController
from utils import RateLimiter


class GestureActions:
    """The only place that connects gesture meaning to OS behavior."""

    def __init__(self, config: AppConfig, keyboard: KeyboardController, mouse: MouseController) -> None:
        self.config, self.keyboard, self.mouse = config, keyboard, mouse
        self._palm_limiter = RateLimiter(config.gesture_cooldown)
        self._last_gesture = Gesture.NONE

    def execute(self, result: GestureResult) -> str:
        """Perform the gesture action and return a UI-friendly description."""
        if result.gesture != self._last_gesture:
            self.mouse.reset_modes()
        self._last_gesture = result.gesture
        hand = result.hand
        if result.gesture == Gesture.PALM and self._palm_limiter.ready():
            self.keyboard.press_windows()
            return "Opened Start menu"
        if not self.config.mouse_enabled or hand is None:
            return "Waiting"
        if result.gesture == Gesture.INDEX:
            self.mouse.move(hand)
            return "Mouse control" + (" + click" if self.mouse.detect_click(hand) else "")
        if result.gesture == Gesture.TWO_FINGERS:
            return "Scrolling" if self.mouse.scroll(hand) else "Scroll mode"
        return "Idle"
