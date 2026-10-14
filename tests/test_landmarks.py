import numpy as np
import pytest

from helmx_drowsiness.runtime.landmarks import FaceResult, geometry


def test_geometry_uses_pixel_coordinates() -> None:
    landmarks = np.zeros((478, 3), dtype=np.float32)
    left = [362, 385, 387, 263, 373, 380]
    right = [33, 160, 158, 133, 153, 144]
    mouth = [61, 81, 13, 291, 14, 178]
    shape = np.array(
        [[0.2, 0.5], [0.3, 0.4], [0.5, 0.4], [0.6, 0.5], [0.5, 0.6], [0.3, 0.6]],
        dtype=np.float32,
    )
    landmarks[left, :2] = shape
    landmarks[right, :2] = shape
    landmarks[mouth, :2] = shape
    result = geometry(FaceResult(landmarks, {}, None), frame_width=100, frame_height=100)
    assert result.left_ear == pytest.approx(0.5)
    assert result.right_ear == pytest.approx(0.5)
