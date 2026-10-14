"""Real-time, calibrated HelmX camera application."""

from __future__ import annotations

import time
from collections import deque
from math import ceil
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from helmx_drowsiness.config import ProjectConfig
from helmx_drowsiness.features.quality import landmark_quality, visual_quality
from helmx_drowsiness.features.temporal import (
    OcularObservation,
    TemporalFeatureExtractor,
    fit_personal_baseline,
)
from helmx_drowsiness.features.visual_input import VisualRegion, prepare_visual_rgb
from helmx_drowsiness.runtime.alarm import play_alarm
from helmx_drowsiness.runtime.landmarks import MediaPipeFaceBackend, geometry
from helmx_drowsiness.runtime.onnx_runner import OnnxTemporalRunner
from helmx_drowsiness.state_machine import AlertController
from helmx_drowsiness.types import AlertLevel, FrameEvidence

COLORS = {
    AlertLevel.UNAVAILABLE: (128, 128, 128),
    AlertLevel.ALERT: (40, 200, 40),
    AlertLevel.CAUTION: (0, 215, 255),
    AlertLevel.WARNING: (0, 128, 255),
    AlertLevel.CRITICAL: (0, 0, 255),
}
IMAGENET_MEAN = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)[:, None, None]
IMAGENET_STD = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)[:, None, None]


def run_camera(
    config: ProjectConfig,
    *,
    onnx_model: str | Path,
    face_landmarker: str | Path,
    alarm_path: str | Path,
    camera: int = 0,
) -> None:
    """Run calibrated causal inference until the user presses ``q``."""

    capture = cv2.VideoCapture(camera)
    if not capture.isOpened():
        raise RuntimeError(f"could not open camera {camera}")
    runner = OnnxTemporalRunner(onnx_model)
    controller = AlertController(config.alert)
    calibration: list[OcularObservation] = []
    feature_extractor: TemporalFeatureExtractor | None = None
    frames: deque[NDArray[np.float32]] = deque(maxlen=config.data.sequence_length)
    features: deque[NDArray[np.float32]] = deque(maxlen=config.data.sequence_length)
    qualities: deque[NDArray[np.float32]] = deque(maxlen=config.data.sequence_length)
    last_sample = float("-inf")
    probability = 0.0
    level = AlertLevel.UNAVAILABLE
    calibration_target = max(30, ceil(config.data.calibration_seconds * config.data.sample_fps))

    try:
        with MediaPipeFaceBackend(face_landmarker) as backend:
            while capture.isOpened():
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("camera frame acquisition failed")
                frame_array: NDArray[np.uint8] = np.asarray(frame, dtype=np.uint8)
                now = time.monotonic()
                face = backend.detect(frame_array, now)
                message = "Face unavailable"
                quality_score = 0.0
                physiology_quality = 0.0
                monitoring_quality = 0.0

                if face is not None:
                    measured = geometry(face, frame_array.shape[1], frame_array.shape[0])
                    crop = padded_crop(frame_array, measured.face_box, padding=0.15)
                    face_fraction = (crop.shape[0] * crop.shape[1]) / (
                        frame_array.shape[0] * frame_array.shape[1]
                    )
                    quality_score, _ = visual_quality(
                        crop, detection_confidence=1.0, face_fraction=face_fraction
                    )
                    physiology_quality, _ = landmark_quality(
                        face.landmarks,
                        left_ear=measured.left_ear,
                        right_ear=measured.right_ear,
                        mar=measured.mar,
                    )
                    monitoring_quality = float(np.sqrt(quality_score * physiology_quality))
                    observation = OcularObservation(
                        now,
                        measured.left_ear,
                        measured.right_ear,
                        measured.mar,
                        measured.pitch,
                        measured.yaw,
                        measured.roll,
                        monitoring_quality,
                    )
                    if feature_extractor is None:
                        if (
                            monitoring_quality >= 0.65
                            and now - last_sample >= 1.0 / config.data.sample_fps
                        ):
                            calibration.append(observation)
                            last_sample = now
                        message = (
                            f"Calibration: {min(len(calibration), calibration_target)}/"
                            f"{calibration_target} - look ahead"
                        )
                        if len(calibration) >= calibration_target:
                            feature_extractor = TemporalFeatureExtractor(
                                fit_personal_baseline(calibration)
                            )
                            message = "Calibration complete"
                    elif now - last_sample >= 1.0 / config.data.sample_fps:
                        frames.append(
                            prepare_face(
                                crop,
                                config.data.image_size,
                                visual_region=config.data.visual_region,
                            )
                        )
                        features.append(feature_extractor.update(observation))
                        qualities.append(
                            np.asarray([quality_score, physiology_quality], dtype=np.float32)
                        )
                        last_sample = now
                        if len(frames) == config.data.sequence_length:
                            scores = runner.predict(
                                np.stack(frames)[None],
                                np.stack(features)[None],
                                np.stack(qualities)[None],
                            )
                            probability = float(scores[0, -1])
                            decision = controller.update(
                                FrameEvidence(now, probability, monitoring_quality)
                            )
                            level = decision.level
                            message = decision.reason
                            if decision.should_alarm:
                                play_alarm(alarm_path)
                        else:
                            message = f"Temporal warm-up: {len(frames)}/{frames.maxlen}"
                elif feature_extractor is not None:
                    decision = controller.update(FrameEvidence(now, probability, 0.0))
                    level = decision.level
                    message = decision.reason

                _draw_status(frame_array, level, probability, monitoring_quality, message)
                cv2.imshow("HelmX Drowsiness Monitor", frame_array)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        capture.release()
        cv2.destroyAllWindows()


def padded_crop(
    frame: NDArray[np.uint8], box: tuple[int, int, int, int], *, padding: float
) -> NDArray[np.uint8]:
    """Crop a padded face region.

    Shared with ``evaluation.causal_harness`` so offline event replay preprocesses frames
    identically to the live camera loop.
    """

    x_min, y_min, x_max, y_max = box
    width, height = x_max - x_min, y_max - y_min
    x_pad, y_pad = round(width * padding), round(height * padding)
    x_min, x_max = max(0, x_min - x_pad), min(frame.shape[1], x_max + x_pad)
    y_min, y_max = max(0, y_min - y_pad), min(frame.shape[0], y_max + y_pad)
    crop = frame[y_min:y_max, x_min:x_max]
    if crop.size == 0:
        raise ValueError("face crop is empty")
    return crop


def prepare_face(
    face_bgr: NDArray[np.uint8], size: int, *, visual_region: VisualRegion = "full_face"
) -> NDArray[np.float32]:
    rgb = prepare_visual_rgb(face_bgr, size, visual_region)
    chw = np.transpose(rgb.astype(np.float32) / 255.0, (2, 0, 1))
    return ((chw - IMAGENET_MEAN) / IMAGENET_STD).astype(np.float32)


def _draw_status(
    frame: NDArray[np.uint8],
    level: AlertLevel,
    probability: float,
    quality: float,
    message: str,
) -> None:
    color = COLORS[level]
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 94), (15, 15, 15), -1)
    cv2.putText(
        frame,
        f"{level.name}  drowsy={probability:.2f}  quality={quality:.2f}",
        (12, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        color,
        2,
    )
    cv2.putText(frame, message, (12, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.58, color, 1)
