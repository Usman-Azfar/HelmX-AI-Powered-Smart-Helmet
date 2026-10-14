"""Deterministic raw-video to temporal-NPZ preprocessing."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from helmx_drowsiness.config import DataConfig
from helmx_drowsiness.features.quality import landmark_quality, visual_quality
from helmx_drowsiness.features.temporal import (
    OcularObservation,
    PersonalBaseline,
    TemporalFeatureExtractor,
    fit_personal_baseline,
)
from helmx_drowsiness.features.visual_input import prepare_visual_rgb
from helmx_drowsiness.runtime.landmarks import (
    FaceGeometry,
    MediaPipeFaceBackend,
    geometry,
)


@dataclass(frozen=True, slots=True)
class ProcessedWindow:
    dataset: str
    subject_id: str
    session_id: str
    path: str
    label: int
    split: str
    start_seconds: float
    end_seconds: float


def collect_neutral_calibration(
    video_path: str | Path,
    face_landmarker: str | Path,
    *,
    sample_fps: float = 8.0,
    seconds: float = 20.0,
) -> PersonalBaseline:
    """Fit a baseline from an explicitly alert/neutral subject recording."""

    observations: list[OcularObservation] = []
    with MediaPipeFaceBackend(face_landmarker) as backend:
        for timestamp, frame in sampled_frames(video_path, sample_fps, limit_seconds=seconds):
            result = backend.detect(frame, timestamp)
            if result is None:
                continue
            try:
                measured = geometry(result, frame.shape[1], frame.shape[0])
            except ValueError:
                continue
            face_crop = _crop(frame, measured.face_box)
            visual, physical = _qualities(result.landmarks, measured, face_crop, frame)
            observations.append(
                OcularObservation(
                    timestamp,
                    measured.left_ear,
                    measured.right_ear,
                    measured.mar,
                    measured.pitch,
                    measured.yaw,
                    measured.roll,
                    float(np.sqrt(visual * physical)),
                )
            )
    return fit_personal_baseline(observations)


def preprocess_video(
    video_path: str | Path,
    output_root: str | Path,
    face_landmarker: str | Path,
    baseline: PersonalBaseline,
    data_config: DataConfig,
    *,
    dataset: str,
    subject_id: str,
    session_id: str,
    label: int,
    split: str,
) -> list[ProcessedWindow]:
    """Create fixed causal windows and return canonical manifest records."""

    frame_buffer: list[NDArray[np.uint8]] = []
    feature_buffer: list[NDArray[np.float32]] = []
    quality_buffer: list[NDArray[np.float32]] = []
    timestamps: list[float] = []
    feature_extractor = TemporalFeatureExtractor(baseline)
    with MediaPipeFaceBackend(face_landmarker) as backend:
        for timestamp, frame in sampled_frames(video_path, data_config.sample_fps):
            result = backend.detect(frame, timestamp)
            visual = physical = 0.0
            face_rgb = np.zeros((data_config.image_size, data_config.image_size, 3), dtype=np.uint8)
            observation = OcularObservation(timestamp, 0, 0, 0, 0, 0, 0, 0)
            if result is not None:
                try:
                    measured = geometry(result, frame.shape[1], frame.shape[0])
                    face_crop = _crop(frame, measured.face_box)
                    visual, physical = _qualities(result.landmarks, measured, face_crop, frame)
                    monitoring_quality = float(np.sqrt(visual * physical))
                    observation = OcularObservation(
                        timestamp,
                        measured.left_ear,
                        measured.right_ear,
                        measured.mar,
                        measured.pitch,
                        measured.yaw,
                        measured.roll,
                        monitoring_quality,
                    )
                    face_rgb = prepare_visual_rgb(
                        face_crop, data_config.image_size, data_config.visual_region
                    )
                except ValueError:
                    pass
            frame_buffer.append(np.asarray(face_rgb, dtype=np.uint8))
            feature_buffer.append(feature_extractor.update(observation))
            quality_buffer.append(np.asarray([visual, physical], dtype=np.float32))
            timestamps.append(timestamp)

    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    records: list[ProcessedWindow] = []
    length = data_config.sequence_length
    for start in range(0, len(frame_buffer) - length + 1, data_config.window_stride):
        end = start + length
        name = f"{dataset}_{subject_id}_{session_id}_{start:07d}.npz"
        destination = output / name
        np.savez_compressed(
            destination,
            frames=np.stack(frame_buffer[start:end]),
            physiology=np.stack(feature_buffer[start:end]),
            quality=np.stack(quality_buffer[start:end]),
        )
        records.append(
            ProcessedWindow(
                dataset=dataset,
                subject_id=subject_id,
                session_id=session_id,
                path=name,
                label=label,
                split=split,
                start_seconds=timestamps[start],
                end_seconds=timestamps[end - 1],
            )
        )
    return records


def records_as_dicts(records: list[ProcessedWindow]) -> list[dict[str, object]]:
    return [asdict(record) for record in records]


def sampled_frames(
    video_path: str | Path,
    sample_fps: float,
    *,
    limit_seconds: float | None = None,
) -> Iterator[tuple[float, NDArray[np.uint8]]]:
    """Deterministically decimate a video to a fixed sample rate using source timestamps.

    Shared by preprocessing and the offline event-evaluation harness
    (``evaluation.causal_harness``) so both read training and evaluation video the same way.
    """
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"could not open video: {video_path}")
    source_fps = float(capture.get(cv2.CAP_PROP_FPS))
    if not np.isfinite(source_fps) or source_fps <= 0:
        capture.release()
        raise ValueError(f"video has invalid FPS metadata: {video_path}")
    interval = 1.0 / sample_fps
    next_sample = 0.0
    frame_index = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            timestamp = frame_index / source_fps
            frame_index += 1
            if limit_seconds is not None and timestamp > limit_seconds:
                break
            if timestamp + (0.5 / source_fps) < next_sample:
                continue
            next_sample += interval
            yield timestamp, np.asarray(frame, dtype=np.uint8)
    finally:
        capture.release()


def _crop(
    frame: NDArray[np.uint8], box: tuple[int, int, int, int], padding: float = 0.15
) -> NDArray[np.uint8]:
    x_min, y_min, x_max, y_max = box
    width, height = x_max - x_min, y_max - y_min
    x_pad, y_pad = round(width * padding), round(height * padding)
    x_min, x_max = max(0, x_min - x_pad), min(frame.shape[1], x_max + x_pad)
    y_min, y_max = max(0, y_min - y_pad), min(frame.shape[0], y_max + y_pad)
    result = frame[y_min:y_max, x_min:x_max]
    if result.size == 0:
        raise ValueError("empty face crop")
    return result


def _qualities(
    result_landmarks: NDArray[np.float32],
    measured: FaceGeometry,
    crop: NDArray[np.uint8],
    frame: NDArray[np.uint8],
) -> tuple[float, float]:
    face_fraction = (crop.shape[0] * crop.shape[1]) / (frame.shape[0] * frame.shape[1])
    visual, _ = visual_quality(crop, detection_confidence=1.0, face_fraction=face_fraction)
    physical, _ = landmark_quality(
        result_landmarks,
        left_ear=measured.left_ear,
        right_ear=measured.right_ear,
        mar=measured.mar,
    )
    return visual, physical
