"""MediaPipe Tasks hand-landmark adapter for current MediaPipe releases."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = Path(__file__).parent / "assets" / "hand_landmarker.task"
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
    (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
)


@dataclass(frozen=True)
class HandData:
    """Normalized hand data made convenient for gesture code."""

    landmarks: tuple[tuple[float, float, float], ...]
    handedness: str

    @property
    def index_position(self) -> tuple[float, float, float]:
        return self.landmarks[8]

    @property
    def palm_center(self) -> tuple[float, float, float]:
        return tuple(sum(self.landmarks[i][axis] for i in (0, 5, 9, 13, 17)) / 5 for axis in range(3))  # type: ignore[return-value]

    @property
    def depth(self) -> float:
        return self.index_position[2]


class HandTracker:
    """Find, draw, and normalize at most one visible hand."""

    def __init__(self) -> None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Hand model not found: {MODEL_PATH}. Run the model-download command in README.md."
            )
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.65,
            min_hand_presence_confidence=0.60,
            min_tracking_confidence=0.60,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._current: Optional[HandData] = None
        self._timestamp_ms = 0

    def process(self, frame) -> Optional[HandData]:
        """Process a BGR frame, draw landmarks in place, and return hand data."""
        self._timestamp_ms += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(image, self._timestamp_ms)
        self._current = None
        if not result.hand_landmarks:
            return None
        points = result.hand_landmarks[0]
        label = result.handedness[0][0].category_name
        self._draw(frame, points)
        self._current = HandData(tuple((point.x, point.y, point.z) for point in points), label)
        return self._current

    @staticmethod
    def _draw(frame, points) -> None:
        height, width = frame.shape[:2]
        pixels = [(int(point.x * width), int(point.y * height)) for point in points]
        for start, end in HAND_CONNECTIONS:
            cv2.line(frame, pixels[start], pixels[end], (0, 220, 0), 2)
        for point in pixels:
            cv2.circle(frame, point, 3, (0, 100, 255), -1)

    def get_landmarks(self) -> Optional[tuple[tuple[float, float, float], ...]]:
        return self._current.landmarks if self._current else None

    def get_index_position(self) -> Optional[tuple[float, float, float]]:
        return self._current.index_position if self._current else None

    def get_hand_depth(self) -> Optional[float]:
        return self._current.depth if self._current else None

    def get_finger_states(self) -> tuple[bool, bool, bool, bool, bool]:
        if not self._current:
            return (False,) * 5
        p = self._current.landmarks
        thumb = p[4][0] < p[3][0] if self._current.handedness == "Right" else p[4][0] > p[3][0]
        return (thumb, *(p[tip][1] < p[tip - 2][1] for tip in (8, 12, 16, 20)))

    def close(self) -> None:
        self._landmarker.close()
