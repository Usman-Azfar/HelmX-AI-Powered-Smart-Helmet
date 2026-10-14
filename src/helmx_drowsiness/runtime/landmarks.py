"""MediaPipe Tasks face-landmark backend with explicit lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from numpy.typing import NDArray

from helmx_drowsiness.features.ocular import eye_aspect_ratio, mouth_aspect_ratio

# Six-point ordering: outer, upper-outer, upper-inner, inner, lower-inner, lower-outer.
LEFT_EYE = np.asarray([362, 385, 387, 263, 373, 380])
RIGHT_EYE = np.asarray([33, 160, 158, 133, 153, 144])
MOUTH = np.asarray([61, 81, 13, 291, 14, 178])


@dataclass(frozen=True, slots=True)
class FaceResult:
    landmarks: NDArray[np.float32]
    blendshapes: dict[str, float]
    transform: NDArray[np.float32] | None


@dataclass(frozen=True, slots=True)
class FaceGeometry:
    left_ear: float
    right_ear: float
    mar: float
    pitch: float
    yaw: float
    roll: float
    face_box: tuple[int, int, int, int]


class MediaPipeFaceBackend:
    """Synchronous video-mode wrapper around the current FaceLandmarker task."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        detection_confidence: float = 0.5,
        presence_confidence: float = 0.5,
        tracking_confidence: float = 0.5,
    ) -> None:
        path = Path(model_path)
        if not path.is_file():
            raise FileNotFoundError(
                f"FaceLandmarker model not found: {path}. Run the asset download command first."
            )
        vision = mp.tasks.vision
        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(path)),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=detection_confidence,
            min_face_presence_confidence=presence_confidence,
            min_tracking_confidence=tracking_confidence,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1

    def detect(self, frame_bgr: NDArray[np.uint8], timestamp_seconds: float) -> FaceResult | None:
        timestamp_ms = max(self._last_timestamp_ms + 1, round(timestamp_seconds * 1000))
        self._last_timestamp_ms = timestamp_ms
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        if not result.face_landmarks:
            return None
        landmarks = np.asarray(
            [[item.x, item.y, item.z] for item in result.face_landmarks[0]], dtype=np.float32
        )
        blendshapes: dict[str, float] = {}
        if result.face_blendshapes:
            blendshapes = {
                item.category_name: float(item.score) for item in result.face_blendshapes[0]
            }
        transform = None
        if result.facial_transformation_matrixes:
            transform = np.asarray(result.facial_transformation_matrixes[0], dtype=np.float32)
        return FaceResult(landmarks, blendshapes, transform)

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> MediaPipeFaceBackend:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def geometry(result: FaceResult, frame_width: int, frame_height: int) -> FaceGeometry:
    """Derive pixel-correct geometry and Euler pose from a landmark result."""

    pixels = result.landmarks[:, :2].astype(np.float64)
    pixels[:, 0] *= frame_width
    pixels[:, 1] *= frame_height
    left_ear = eye_aspect_ratio(pixels[LEFT_EYE])
    right_ear = eye_aspect_ratio(pixels[RIGHT_EYE])
    mar = mouth_aspect_ratio(pixels[MOUTH])
    x_min, y_min = np.floor(pixels.min(axis=0)).astype(int)
    x_max, y_max = np.ceil(pixels.max(axis=0)).astype(int)
    x_min, y_min = max(0, x_min), max(0, y_min)
    x_max, y_max = min(frame_width, x_max), min(frame_height, y_max)
    pitch, yaw, roll = _euler_degrees(result.transform)
    return FaceGeometry(
        left_ear,
        right_ear,
        mar,
        pitch,
        yaw,
        roll,
        (x_min, y_min, x_max, y_max),
    )


def _euler_degrees(transform: NDArray[np.float32] | None) -> tuple[float, float, float]:
    if transform is None or transform.shape[0] < 3 or transform.shape[1] < 3:
        return 0.0, 0.0, 0.0
    rotation = transform[:3, :3].astype(np.float64)
    sy = np.hypot(rotation[0, 0], rotation[1, 0])
    singular = sy < 1e-6
    if not singular:
        pitch = np.arctan2(rotation[2, 1], rotation[2, 2])
        yaw = np.arctan2(-rotation[2, 0], sy)
        roll = np.arctan2(rotation[1, 0], rotation[0, 0])
    else:
        pitch = np.arctan2(-rotation[1, 2], rotation[1, 1])
        yaw = np.arctan2(-rotation[2, 0], sy)
        roll = 0.0
    degrees = np.degrees([pitch, yaw, roll])
    return float(degrees[0]), float(degrees[1]), float(degrees[2])
