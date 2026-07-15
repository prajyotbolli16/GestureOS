"""Smooth cursor, pinch-click, drag, and scroll control."""
from __future__ import annotations

import math
import time
from collections import deque
from typing import Optional

import pyautogui

from config import AppConfig
from hand_tracker import HandData


class MouseController:
    """Translate normalized hand data into restrained OS mouse actions."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._screen_width, self._screen_height = pyautogui.size()
        self._smoothed: Optional[tuple[float, float]] = None
        self._position_history: deque[tuple[float, float]] = deque(maxlen=5)
        self._previous_scroll_y: Optional[float] = None
        self._pinch_state = "idle"
        self._pinch_started_at: Optional[float] = None
        self._mouse_pressed = False
        self._pinch_threshold = config.pinch_threshold
        self._release_threshold = config.release_threshold
        self._drag_hold_time_ms = config.drag_hold_time_ms

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

    def _thumb_index_distance(self, hand: HandData) -> float:
        thumb = hand.landmarks[4]
        index = hand.landmarks[8]
        return math.hypot(index[0] - thumb[0], index[1] - thumb[1])

    def detect_click(self, hand: HandData) -> bool:
        """Drive a thumb-index pinch state machine for single-click and drag interaction."""
        distance = self._thumb_index_distance(hand)
        now = time.monotonic()

        if self._pinch_state == "idle":
            if distance < self._pinch_threshold:
                self._pinch_state = "pinch_started"
                self._pinch_started_at = now
                pyautogui.click()
                return True
            return False

        if distance > self._release_threshold:
            if self._mouse_pressed:
                pyautogui.mouseUp()
                self._mouse_pressed = False
            self._pinch_state = "idle"
            self._pinch_started_at = None
            return False

        if self._pinch_state in {"pinch_started", "holding_pinch"}:
            if self._pinch_started_at is not None and now - self._pinch_started_at >= self._drag_hold_time_ms / 1000.0:
                if not self._mouse_pressed:
                    pyautogui.mouseDown()
                    self._mouse_pressed = True
                self._pinch_state = "dragging"
                return True
            self._pinch_state = "holding_pinch"
            return False

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
        if self._mouse_pressed:
            pyautogui.mouseUp()
            self._mouse_pressed = False
        self._pinch_state = "idle"
        self._pinch_started_at = None
        self._previous_scroll_y = None
        self._position_history.clear()
