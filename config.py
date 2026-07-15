"""Application settings and persistent configuration."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path

LOG = logging.getLogger(__name__)
CONFIG_PATH = Path(__file__).with_name("settings.json")


@dataclass
class AppConfig:
    """Settings exposed by GestureOS."""

    camera_width: int = 640
    camera_height: int = 480
    camera_index: int = 0
    mouse_sensitivity: float = 1.0
    cursor_smoothing: float = 0.14
    cursor_deadzone: int = 4
    click_threshold: float = 0.055
    scroll_speed: int = 4
    voice_enabled: bool = False
    mouse_enabled: bool = True
    gesture_cooldown: float = 0.65
    fps_limit: int = 30

    @classmethod
    def load(cls) -> "AppConfig":
        """Load saved values, falling back safely to defaults."""
        if not CONFIG_PATH.exists():
            return cls()
        try:
            values = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            allowed = {key: value for key, value in values.items() if key in cls.__dataclass_fields__}
            return cls(**allowed)
        except (OSError, json.JSONDecodeError, TypeError) as error:
            LOG.warning("Could not read settings: %s", error)
            return cls()

    def save(self) -> None:
        """Persist settings beside the application."""
        try:
            CONFIG_PATH.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except OSError as error:
            LOG.error("Could not save settings: %s", error)
