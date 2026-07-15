"""Small shared helpers."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time


def configure_logging() -> None:
    """Configure concise console and rotating file logging once."""
    if logging.getLogger().handlers:
        return
    log_file = Path(__file__).with_name("gestureos.log")
    handler = RotatingFileHandler(log_file, maxBytes=500_000, backupCount=2, encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), handler],
    )


class RateLimiter:
    """Simple monotonic-time cooldown guard."""

    def __init__(self, cooldown: float) -> None:
        self.cooldown = cooldown
        self._last = 0.0

    def ready(self) -> bool:
        now = time.monotonic()
        if now - self._last < self.cooldown:
            return False
        self._last = now
        return True
