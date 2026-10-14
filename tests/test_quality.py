import numpy as np
import pytest

from helmx_drowsiness.features.quality import landmark_quality, visual_quality


def test_blank_image_has_low_visual_quality() -> None:
    blank = np.zeros((64, 64, 3), dtype=np.uint8)
    score, components = visual_quality(blank, detection_confidence=1.0, face_fraction=0.2)
    assert score < 0.01
    assert components["sharpness"] == 0.0


def test_plausible_in_frame_landmarks_have_high_quality() -> None:
    landmarks = np.full((478, 3), 0.5, dtype=np.float32)
    score, components = landmark_quality(landmarks, left_ear=0.3, right_ear=0.3, mar=0.2)
    assert score > 0.99
    assert components["coverage"] == pytest.approx(1.0)


def test_implausible_geometry_is_rejected() -> None:
    landmarks = np.full((478, 3), 0.5, dtype=np.float32)
    score, _ = landmark_quality(landmarks, left_ear=4.0, right_ear=0.3, mar=0.2)
    assert score < 0.02
