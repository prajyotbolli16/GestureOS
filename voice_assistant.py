"""Background speech recognition and command interpretation."""
from __future__ import annotations

import logging
import queue
from threading import Event, Thread

import speech_recognition as sr

from keyboard_controller import KeyboardController

LOG = logging.getLogger(__name__)


class VoiceAssistant:
    """Listen in a daemon thread and queue recognized phrases for the UI."""

    def __init__(self, keyboard: KeyboardController) -> None:
        self.keyboard = keyboard
        self.commands: queue.Queue[str] = queue.Queue()
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(target=self._listen_loop, name="voice", daemon=True)
        self._thread.start()

    def _listen_loop(self) -> None:
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                while not self._stop.is_set():
                    try:
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        phrase = recognizer.recognize_google(audio).lower().strip()
                        if phrase:
                            self.commands.put(phrase)
                            self.execute(phrase)
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as error:
                        LOG.warning("Voice service unavailable: %s", error)
        except OSError as error:
            LOG.error("Microphone unavailable: %s", error)

    def execute(self, phrase: str) -> None:
        """Apply a small, predictable voice command vocabulary."""
        if phrase in {"open", "go", "close"}:
            self.keyboard.press_enter() if phrase != "close" else self.keyboard.hotkey("alt", "f4")
        elif phrase == "settings":
            self.keyboard.hotkey("win", "i")
        elif phrase in {"stop", "start"}:
            return  # UI reads these commands; reserved for application control.
        elif phrase.startswith("search "):
            self.keyboard.type_text(phrase.removeprefix("search "))
        else:
            self.keyboard.type_text(phrase)

    def latest_command(self) -> str | None:
        """Return the newest queued phrase, dropping stale status updates."""
        latest = None
        while not self.commands.empty():
            latest = self.commands.get_nowait()
        return latest

    def stop(self) -> None:
        self._stop.set()
