import numpy as np
import pytest

from helmx_drowsiness.features.ocular import eye_aspect_ratio, normalized_to_pixels


def test_eye_aspect_ratio_matches_known_geometry() -> None:
    eye = np.array([[0.0, 0.0], [1.0, -1.0], [3.0, -1.0], [4.0, 0.0], [3.0, 1.0], [1.0, 1.0]])
    assert eye_aspect_ratio(eye) == pytest.approx(0.5)


def test_pixel_conversion_corrects_non_square_frames() -> None:
    points = normalized_to_pixels([[0.5, 0.5], [1.0, 1.0]], width=1280, height=720)
    np.testing.assert_allclose(points, [[640.0, 360.0], [1280.0, 720.0]])


def test_zero_width_eye_is_rejected() -> None:
    with pytest.raises(ValueError, match="width is zero"):
        eye_aspect_ratio(np.zeros((6, 2)))
