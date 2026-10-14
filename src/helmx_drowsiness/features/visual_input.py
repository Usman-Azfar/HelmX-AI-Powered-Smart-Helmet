"""Shared full-face, eye-band, and packed dual-eye visual input contracts."""

from __future__ import annotations

from typing import Literal

import cv2
import numpy as np
from numpy.typing import NDArray

VisualRegion = Literal["full_face", "eye_band", "dual_eye"]
EYE_X_MIN = 0.05
EYE_X_MAX = 0.95
EYE_Y_MIN = 0.18
EYE_Y_MAX = 0.55
LEFT_EYE_X_MAX = 0.48
RIGHT_EYE_X_MIN = 0.52


def eye_band(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """Crop the bilateral-eye band from an already landmark-derived face crop."""

    if image.ndim != 3 or image.shape[2] != 3 or image.size == 0:
        raise ValueError("visual input must be a non-empty uint8 HxWx3 image")
    height, width = image.shape[:2]
    x_min, x_max = round(EYE_X_MIN * width), round(EYE_X_MAX * width)
    y_min, y_max = round(EYE_Y_MIN * height), round(EYE_Y_MAX * height)
    result = image[y_min:y_max, x_min:x_max]
    if result.size == 0:
        raise ValueError("eye-band crop is empty")
    return np.asarray(result, dtype=np.uint8)


def dual_eye_crops(
    image: NDArray[np.uint8], size: int, *, color_conversion: int
) -> tuple[NDArray[np.uint8], NDArray[np.uint8]]:
    """Return fixed left/right grayscale eye crops from a padded face image."""

    if image.ndim != 3 or image.shape[2] != 3 or image.size == 0:
        raise ValueError("visual input must be a non-empty uint8 HxWx3 image")
    if size <= 0:
        raise ValueError("visual input size must be positive")
    height, width = image.shape[:2]
    y_min, y_max = round(EYE_Y_MIN * height), round(EYE_Y_MAX * height)
    bounds = (
        (round(EYE_X_MIN * width), round(LEFT_EYE_X_MAX * width)),
        (round(RIGHT_EYE_X_MIN * width), round(EYE_X_MAX * width)),
    )
    results: list[NDArray[np.uint8]] = []
    for x_min, x_max in bounds:
        crop = image[y_min:y_max, x_min:x_max]
        if crop.size == 0:
            raise ValueError("single-eye crop is empty")
        resized = cv2.resize(crop, (size, size))
        gray = cv2.cvtColor(resized, color_conversion)
        results.append(np.repeat(gray[..., None], 3, axis=2).astype(np.uint8, copy=False))
    return results[0], results[1]


def prepare_visual_rgb(
    face_bgr: NDArray[np.uint8], size: int, region: VisualRegion
) -> NDArray[np.uint8]:
    """Create the stored RGB tensor for the configured visual region."""

    if size <= 0:
        raise ValueError("visual input size must be positive")
    if region == "full_face":
        resized = cv2.resize(face_bgr, (size, size))
        return np.asarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB), dtype=np.uint8)
    if region == "dual_eye":
        left, right = dual_eye_crops(face_bgr, size, color_conversion=cv2.COLOR_BGR2GRAY)
        return np.concatenate((left, right), axis=1)
    selected = eye_band(face_bgr)
    resized = cv2.resize(selected, (size, size))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    return np.repeat(gray[..., None], 3, axis=2).astype(np.uint8, copy=False)


def derive_eye_band_rgb(frames_rgb: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """Transform cached full-face RGB sequences into MRL-compatible eye-band RGB."""

    if frames_rgb.ndim != 4 or frames_rgb.shape[-1] != 3 or frames_rgb.dtype != np.uint8:
        raise ValueError("cached frames must be uint8 with shape [T, H, W, 3]")
    size = frames_rgb.shape[1]
    if frames_rgb.shape[2] != size:
        raise ValueError("cached face frames must be square")
    result: list[NDArray[np.uint8]] = []
    for frame in frames_rgb:
        selected = eye_band(frame)
        resized = cv2.resize(selected, (size, size))
        gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
        result.append(np.repeat(gray[..., None], 3, axis=2).astype(np.uint8, copy=False))
    return np.stack(result)


def derive_dual_eye_rgb(frames_rgb: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """Pack two square grayscale eye crops side-by-side for shared encoding."""

    if frames_rgb.ndim != 4 or frames_rgb.shape[-1] != 3 or frames_rgb.dtype != np.uint8:
        raise ValueError("cached frames must be uint8 with shape [T, H, W, 3]")
    size = frames_rgb.shape[1]
    if frames_rgb.shape[2] != size:
        raise ValueError("cached face frames must be square")
    result: list[NDArray[np.uint8]] = []
    for frame in frames_rgb:
        left, right = dual_eye_crops(frame, size, color_conversion=cv2.COLOR_RGB2GRAY)
        result.append(np.concatenate((left, right), axis=1))
    return np.stack(result)
