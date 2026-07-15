"""Extensible rule-based gesture recognition."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from math import hypot
from typing import Iterable

from hand_tracker import HandData


class Gesture(str, Enum):
    NONE = "No hand"
    FIST = "Closed fist"
    PALM = "Open palm"
    INDEX = "Index finger"
    TWO_FINGERS = "Two fingers"
    PINCH = "Pinch"


@dataclass(frozen=True)
class GestureResult:
    gesture: Gesture
    hand: HandData | None


class GestureRule(ABC):
    """A plug-in point for new gesture recognizers."""

    gesture: Gesture

    @abstractmethod
    def matches(self, hand: HandData) -> bool: ...


class FingerPattern(GestureRule):
    """Match index-to-little finger states while intentionally ignoring thumb.

    A thumb naturally rests in different positions depending on hand orientation,
    so including it makes practical webcam gestures unnecessarily unreliable.
    """

    def __init__(self, gesture: Gesture, pattern: tuple[bool, bool, bool, bool]) -> None:
        self.gesture, self.pattern = gesture, pattern

    def matches(self, hand: HandData) -> bool:
        p = hand.landmarks
        actual = tuple(p[tip][1] < p[tip - 2][1] for tip in (8, 12, 16, 20))
        return actual == self.pattern


class PinchRule(GestureRule):
    gesture = Gesture.PINCH

    def matches(self, hand: HandData) -> bool:
        a, b = hand.landmarks[4], hand.landmarks[8]
        return hypot(a[0] - b[0], a[1] - b[1]) < 0.045


class GestureDetector:
    """Recognize the first matching gesture using ordered rules."""

    def __init__(self, rules: Iterable[GestureRule] | None = None) -> None:
        self.rules = list(rules or (
            (PinchRule(), FingerPattern(Gesture.PALM, (True, True, True, True)),
             FingerPattern(Gesture.INDEX, (True, False, False, False)),
             FingerPattern(Gesture.TWO_FINGERS, (True, True, False, False)),
             FingerPattern(Gesture.FIST, (False, False, False, False)))
        ))

    def detect(self, hand: HandData | None) -> GestureResult:
        if hand is None:
            return GestureResult(Gesture.NONE, None)
        for rule in self.rules:
            if rule.matches(hand):
                return GestureResult(rule.gesture, hand)
        return GestureResult(Gesture.NONE, hand)
