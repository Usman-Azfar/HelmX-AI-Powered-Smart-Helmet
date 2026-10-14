"""Resolution- and aspect-ratio-correct ocular geometry."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.floating]


def normalized_to_pixels(
    points: Sequence[Sequence[float]] | FloatArray, width: int, height: int
) -> NDArray[np.float64]:
    """Convert normalized landmarks to pixel coordinates before distance ratios."""

    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    array = np.asarray(points, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] < 2:
        raise ValueError("points must have shape [N, >=2]")
    result = array[:, :2].copy()
    result[:, 0] *= width
    result[:, 1] *= height
    return result


def eye_aspect_ratio(points: Sequence[Sequence[float]] | FloatArray) -> float:
    """Compute the canonical six-point EAR without arbitrary scaling.

    Points must be ordered as [outer, upper_outer, upper_inner, inner,
    lower_inner, lower_outer]. The result is dimensionless and is usually
    calibrated per subject rather than compared with a universal threshold.
    """

    eye = np.asarray(points, dtype=np.float64)
    if eye.shape != (6, 2):
        raise ValueError("EAR requires exactly six 2D points")
    horizontal = np.linalg.norm(eye[0] - eye[3])
    if horizontal <= np.finfo(np.float64).eps:
        raise ValueError("eye width is zero")
    vertical_outer = np.linalg.norm(eye[1] - eye[5])
    vertical_inner = np.linalg.norm(eye[2] - eye[4])
    return float((vertical_outer + vertical_inner) / (2.0 * horizontal))


def mouth_aspect_ratio(points: Sequence[Sequence[float]] | FloatArray) -> float:
    """Compute a six-point mouth opening ratio using the same geometry as EAR."""

    return eye_aspect_ratio(points)


def symmetric_mean(left: float, right: float) -> float:
    """Average two finite bilateral measurements."""

    if not np.isfinite(left) or not np.isfinite(right):
        raise ValueError("bilateral measurements must be finite")
    return float((left + right) / 2.0)
