"""Smooth cursor, depth-click, and scroll control."""
from __future__ import annotations

from collections import deque
from typing import Optional
import pyautogui

from config import AppConfig
from hand_tracker import HandData
from utils import RateLimiter


class MouseController:
    """Translate normalized hand data into restrained OS mouse actions."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._screen_width, self._screen_height = pyautogui.size()
        self._smoothed: Optional[tuple[float, float]] = None
        self._position_history: deque[tuple[float, float]] = deque(maxlen=5)
        self._click_baseline_z: Optional[float] = None
        self._push_depth_z: Optional[float] = None
        self._previous_scroll_y: Optional[float] = None
        self._click_limiter = RateLimiter(config.gesture_cooldown)

    def move(self, hand: HandData) -> None:
        """Move toward the index-tip target using exponential smoothing."""
        x, y, _ = hand.index_position
        target = (max(0, min(self._screen_width - 1, x * self._screen_width * self.config.mouse_sensitivity)),
                  max(0, min(self._screen_height - 1, y * self._screen_height * self.config.mouse_sensitivity)))
        self._position_history.append(target)
        target = tuple(sum(point[axis] for point in self._position_history) / len(self._position_history)
                       for axis in range(2))
        if self._smoothed is None:
            self._smoothed = target
        alpha = self.config.cursor_smoothing
        candidate = tuple(old + alpha * (new - old) for old, new in zip(self._smoothed, target))
        if max(abs(new - old) for old, new in zip(self._smoothed, candidate)) < self.config.cursor_deadzone:
            return
        self._smoothed = candidate
        pyautogui.moveTo(*self._smoothed, duration=0)

    def detect_click(self, hand: HandData) -> bool:
        """Click only after a forward (more negative Z) push then return."""
        z = hand.depth
        if self._click_baseline_z is None:
            self._click_baseline_z = z
            return False
        if self._push_depth_z is None:
            if z < self._click_baseline_z - self.config.click_threshold:
                self._push_depth_z = z
            else:
                # Adapt slowly to a resting hand without absorbing a quick push.
                self._click_baseline_z = self._click_baseline_z * 0.9 + z * 0.1
            return False
        if z >= self._push_depth_z + self.config.click_threshold * 0.5 and self._click_limiter.ready():
            pyautogui.click()
            self._click_baseline_z = z
            self._push_depth_z = None
            return True
        return False

    def scroll(self, hand: HandData) -> bool:
        """Scroll when the two-finger hand moves far enough vertically."""
        y = hand.index_position[1]
        if self._previous_scroll_y is None:
            self._previous_scroll_y = y
            return False
        movement = y - self._previous_scroll_y
        if abs(movement) < 0.018:
            return False
        # Screen coordinates increase downward; upward movement scrolls down.
        pyautogui.scroll(-self.config.scroll_speed if movement < 0 else self.config.scroll_speed)
        self._previous_scroll_y = y
        return True

    def reset_modes(self) -> None:
        """Discard motion state when changing gesture modes."""
        self._click_baseline_z = None
        self._push_depth_z = None
        self._previous_scroll_y = None
        self._position_history.clear()
