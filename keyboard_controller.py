"""Safe wrappers around keyboard automation."""
from __future__ import annotations

import logging
import pyautogui

LOG = logging.getLogger(__name__)
pyautogui.PAUSE = 0.03
pyautogui.FAILSAFE = True


class KeyboardController:
    """Centralized keyboard actions make them easy to replace or test."""

    def press_key(self, key: str) -> None:
        pyautogui.press(key)

    def press_enter(self) -> None:
        self.press_key("enter")

    def press_windows(self) -> None:
        pyautogui.press("win")

    def type_text(self, text: str) -> None:
        pyautogui.write(text, interval=0.025)

    def hotkey(self, *keys: str) -> None:
        pyautogui.hotkey(*keys)
