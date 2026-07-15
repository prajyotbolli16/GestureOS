import unittest
from unittest.mock import patch

import mouse_controller
from config import AppConfig
from hand_tracker import HandData
from mouse_controller import MouseController


class MouseControllerPinchTests(unittest.TestCase):
    def make_hand(self, thumb_x: float, index_x: float) -> HandData:
        landmarks = tuple(
            (x, y, z) for x, y, z in [
                (0.0, 0.0, 0.0),
                (0.1, 0.1, 0.0),
                (0.2, 0.2, 0.0),
                (0.3, 0.3, 0.0),
                (thumb_x, 0.05, 0.0),
                (0.4, 0.4, 0.0),
                (0.5, 0.5, 0.0),
                (0.6, 0.6, 0.0),
                (index_x, 0.07, 0.0),
                (0.7, 0.7, 0.0),
                (0.8, 0.8, 0.0),
                (0.9, 0.9, 0.0),
                (1.0, 1.0, 0.0),
                (1.1, 1.1, 0.0),
                (1.2, 1.2, 0.0),
                (1.3, 1.3, 0.0),
                (1.4, 1.4, 0.0),
                (1.5, 1.5, 0.0),
                (1.6, 1.6, 0.0),
                (1.7, 1.7, 0.0),
                (1.8, 1.8, 0.0),
                (1.9, 1.9, 0.0),
            ]
        )
        return HandData(landmarks=landmarks, handedness="Right")

    def test_single_click_once_per_pinch(self) -> None:
        controller = MouseController(AppConfig())
        pinched = self.make_hand(0.05, 0.05)

        with patch.object(mouse_controller.pyautogui, "click") as click_mock:
            self.assertTrue(controller.detect_click(pinched))
            self.assertFalse(controller.detect_click(pinched))
            self.assertFalse(controller.detect_click(pinched))

        click_mock.assert_called_once_with()

    def test_drag_begins_after_hold_timeout_and_releases_on_release(self) -> None:
        controller = MouseController(AppConfig())
        pinched = self.make_hand(0.05, 0.05)
        released = self.make_hand(0.20, 0.20)

        with patch.object(mouse_controller.pyautogui, "click") as click_mock, \
             patch.object(mouse_controller.pyautogui, "mouseDown") as mouse_down_mock, \
             patch.object(mouse_controller.pyautogui, "mouseUp") as mouse_up_mock, \
             patch.object(mouse_controller.time, "monotonic", side_effect=[1000.0, 1000.0, 1000.301, 1000.301, 1000.301]):
            self.assertTrue(controller.detect_click(pinched))
            self.assertFalse(controller.detect_click(pinched))
            self.assertTrue(controller.detect_click(pinched))
            self.assertFalse(controller.detect_click(released))
            self.assertFalse(controller.detect_click(released))

        click_mock.assert_called_once_with()
        mouse_down_mock.assert_called_once_with()
        mouse_up_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
