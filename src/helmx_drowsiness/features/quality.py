"""Transparent image-quality signals used for missing-modality gating."""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray


def visual_quality(
    face_bgr: NDArray[np.uint8],
    *,
    detection_confidence: float,
    face_fraction: float,
) -> tuple[float, dict[str, float]]:
    """Score blur, exposure, face scale, and detector confidence in [0, 1]."""

    if face_bgr.size == 0:
        return 0.0, {"sharpness": 0.0, "exposure": 0.0, "scale": 0.0, "detection": 0.0}
    gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY) if face_bgr.ndim == 3 else face_bgr
    laplacian_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    sharpness = float(np.clip(laplacian_variance / 150.0, 0.0, 1.0))
    dark_fraction = float(np.mean(gray <= 8))
    bright_fraction = float(np.mean(gray >= 247))
    exposure = float(np.clip(1.0 - dark_fraction - bright_fraction, 0.0, 1.0))
    scale = float(np.clip(face_fraction / 0.12, 0.0, 1.0))
    detection = float(np.clip(detection_confidence, 0.0, 1.0))
    components = {
        "sharpness": sharpness,
        "exposure": exposure,
        "scale": scale,
        "detection": detection,
    }
    # Geometric mean prevents one severely failed component from being hidden by others.
    quality = float(np.prod(np.maximum(list(components.values()), 1e-6)) ** 0.25)
    return quality, components


def landmark_quality(
    normalized_landmarks: NDArray[np.floating],
    *,
    left_ear: float,
    right_ear: float,
    mar: float,
) -> tuple[float, dict[str, float]]:
    """Measure landmark coverage and physiological plausibility independently of blur."""

    landmarks = np.asarray(normalized_landmarks, dtype=np.float64)
    if landmarks.ndim != 2 or landmarks.shape[1] < 2 or not np.isfinite(landmarks).all():
        return 0.0, {"coverage": 0.0, "plausibility": 0.0, "symmetry": 0.0}
    inside = (
        (landmarks[:, 0] >= 0)
        & (landmarks[:, 0] <= 1)
        & (landmarks[:, 1] >= 0)
        & (landmarks[:, 1] <= 1)
    )
    coverage = float(np.clip((inside.mean() - 0.80) / 0.20, 0.0, 1.0))
    plausible = 0.03 <= left_ear <= 0.80 and 0.03 <= right_ear <= 0.80 and 0.0 <= mar <= 2.0
    plausibility = float(plausible)
    mean_ear = max((left_ear + right_ear) / 2.0, 1e-6)
    symmetry = float(np.clip(1.0 - abs(left_ear - right_ear) / mean_ear, 0.0, 1.0))
    components = {
        "coverage": coverage,
        "plausibility": plausibility,
        "symmetry": symmetry,
    }
    score = float(np.prod(np.maximum(list(components.values()), 1e-6)) ** (1.0 / 3.0))
    return score, components
