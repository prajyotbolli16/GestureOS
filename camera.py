"""Threaded webcam capture."""
from __future__ import annotations

import logging
from threading import Event, Lock, Thread
from typing import Optional

import cv2

from config import AppConfig

LOG = logging.getLogger(__name__)


class Camera:
    """Continuously capture frames without blocking the interface."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._capture: Optional[cv2.VideoCapture] = None
        self._frame = None
        self._lock = Lock()
        self._stop = Event()
        self._thread: Optional[Thread] = None

    def start(self) -> bool:
        """Open the configured webcam and begin capture."""
        if self._thread and self._thread.is_alive():
            return True
        self._capture = cv2.VideoCapture(self.config.camera_index, cv2.CAP_DSHOW)
        if not self._capture.isOpened():
            LOG.error("Unable to open camera %d", self.config.camera_index)
            self._capture.release()
            self._capture = None
            return False
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.camera_width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.camera_height)
        self._stop.clear()
        self._thread = Thread(target=self._capture_loop, name="camera", daemon=True)
        self._thread.start()
        return True

    def _capture_loop(self) -> None:
        while not self._stop.is_set() and self._capture:
            ok, frame = self._capture.read()
            if ok:
                with self._lock:
                    self._frame = frame
            else:
                LOG.warning("Camera returned an empty frame")

    def get_frame(self):
        """Return a copy of the newest frame, if any."""
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def stop(self) -> None:
        """Stop capture and release the webcam."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        if self._capture:
            self._capture.release()
        self._capture = None
