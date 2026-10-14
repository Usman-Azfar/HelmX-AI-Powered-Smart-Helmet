"""Focused pre-training diagnostics for the official UTA-RLDD pilot split."""

from __future__ import annotations

import heapq
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from helmx_drowsiness.datasets.manifest import read_manifest
from helmx_drowsiness.datasets.preprocess import (
    _crop,
    _qualities,
    collect_neutral_calibration,
    sampled_frames,
)
from helmx_drowsiness.datasets.scaling import fit_physiology_scaler
from helmx_drowsiness.datasets.uta_rldd import UtaVideo, discover_uta_videos
from helmx_drowsiness.features.temporal import (
    OcularObservation,
    PersonalBaseline,
    TemporalFeatureExtractor,
)
from helmx_drowsiness.runtime.landmarks import MediaPipeFaceBackend, geometry
from helmx_drowsiness.training.provenance import write_json


def run_uta_pilot_diagnostics(
    raw_root: str | Path,
    manifest_path: str | Path,
    face_landmarker: str | Path,
    output_path: str | Path,
    *,
    sample_fps: float = 8.0,
    calibration_seconds: float = 20.0,
    diagnostic_seconds: float = 10.0,
) -> dict[str, Any]:
    """Replay non-test video starts and quantify boundary/scaling behavior.

    Per-subject baselines and per-video samples are atomically cached next to the report so an
    interrupted diagnostic resumes without reprocessing completed videos. Test-fold subjects are
    deliberately excluded because this is a pre-training selection gate.
    """

    manifest = read_manifest(manifest_path)
    development = manifest.loc[manifest["split"].isin(["train", "validation"])].copy()
    allowed_subjects = set(development["subject_id"].astype(str))
    videos = [
        item
        for item in discover_uta_videos(raw_root)
        if _canonical_subject(item) in allowed_subjects
    ]
    if not videos:
        raise ValueError("no non-test UTA videos match the manifest")

    output = Path(output_path)
    cache_root = output.parent / "uta_pilot_diagnostic_cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[UtaVideo]] = {}
    for video in videos:
        grouped.setdefault(_canonical_subject(video), []).append(video)

    samples: list[dict[str, Any]] = []
    baselines: dict[str, PersonalBaseline] = {}
    for subject_id, subject_videos in sorted(grouped.items()):
        alert_videos = [item for item in subject_videos if item.label == 0]
        if len(alert_videos) != 1:
            raise ValueError(f"expected one alert calibration video for {subject_id}")
        baseline_path = cache_root / f"baseline_{subject_id}.json"
        if baseline_path.is_file():
            baseline = PersonalBaseline(**json.loads(baseline_path.read_text(encoding="utf-8")))
        else:
            baseline = collect_neutral_calibration(
                alert_videos[0].path,
                face_landmarker,
                sample_fps=sample_fps,
                seconds=calibration_seconds,
            )
            write_json(baseline_path, asdict(baseline))
        baselines[subject_id] = baseline

        for video in sorted(subject_videos, key=lambda item: (item.label, item.session_id)):
            cache_path = cache_root / (
                f"samples_{subject_id}_{video.label}_{video.session_id}.json"
            )
            if cache_path.is_file():
                video_samples = json.loads(cache_path.read_text(encoding="utf-8"))
            else:
                video_samples = _sample_video_start(
                    video,
                    subject_id,
                    baseline,
                    face_landmarker,
                    sample_fps=sample_fps,
                    diagnostic_seconds=diagnostic_seconds,
                )
                write_json(cache_path, video_samples)
            samples.extend(video_samples)

    sample_frame = pd.DataFrame(samples)
    samples_path = output.with_name(f"{output.stem}_samples.csv")
    samples_path.parent.mkdir(parents=True, exist_ok=True)
    sample_frame.to_csv(samples_path, index=False)
    payload = {
        "scope": {
            "excluded_split": "test",
            "subjects": len(grouped),
            "videos": len(videos),
            "sample_fps": sample_fps,
            "calibration_seconds": calibration_seconds,
            "diagnostic_seconds": diagnostic_seconds,
            "samples": len(sample_frame),
            "samples_csv": str(samples_path),
        },
        "five_second_boundary": summarize_boundary_samples(sample_frame),
        "baseline_mar": _baseline_mar_summary(baselines),
        "scaling_and_outliers": physiology_scaling_outlier_report(
            development,
            Path(manifest_path).parent,
            baselines,
        ),
    }
    write_json(output, payload)
    return payload


def summarize_boundary_samples(frame: pd.DataFrame) -> dict[str, Any]:
    """Summarize blink-rate behavior in one-second bins and across the five-second floor."""

    required = {"timestamp", "blink_rate_per_minute", "subject_id", "session_id"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"boundary samples are missing columns: {sorted(missing)}")
    values = pd.to_numeric(frame["blink_rate_per_minute"], errors="coerce").to_numpy()
    finite = np.isfinite(values)
    bins: list[dict[str, Any]] = []
    working = frame.copy()
    working["second"] = np.floor(working["timestamp"].astype(float)).astype(int)
    for second, group in working.groupby("second"):
        column = pd.to_numeric(group["blink_rate_per_minute"], errors="coerce").to_numpy()
        column = column[np.isfinite(column)]
        bins.append(
            {
                "second": int(second),
                "samples": len(group),
                "videos": int(group[["subject_id", "session_id"]].drop_duplicates().shape[0]),
                "median": float(np.median(column)),
                "p95": float(np.percentile(column, 95)),
                "p99": float(np.percentile(column, 99)),
                "max": float(column.max()),
            }
        )

    before = _boundary_interval(working, 4.0, 5.0)
    after = _boundary_interval(working, 5.0, 6.0)
    return {
        "nan_inf_fraction": float(1.0 - finite.mean()),
        "one_second_bins": bins,
        "seconds_4_to_5": before,
        "seconds_5_to_6": after,
        "p99_change_at_boundary": after["p99"] - before["p99"],
        "max_change_at_boundary": after["max"] - before["max"],
    }


def physiology_scaling_outlier_report(
    frame: pd.DataFrame,
    root: str | Path,
    baselines: dict[str, PersonalBaseline],
    *,
    top_n: int = 20,
    standardized_clip: float = 10.0,
) -> dict[str, Any]:
    """Fit the training-only scaler and attribute extreme development-set physiology values."""

    training = frame.loc[frame["split"] == "train"]
    scaler = fit_physiology_scaler(training, root)
    feature_names = TemporalFeatureExtractor.feature_names
    all_standardized: list[np.ndarray[Any, Any]] = []
    relative_mar_index = feature_names.index("relative_mar")
    largest: list[tuple[float, int, dict[str, Any]]] = []
    counter = 0
    root_path = Path(root)
    for row in frame.itertuples():
        with np.load(root_path / str(row.path), allow_pickle=False) as sample:
            physiology = np.asarray(sample["physiology"], dtype=np.float64)
            quality = np.asarray(sample["quality"], dtype=np.float64)
        standardized = (physiology - scaler.center) / scaler.scale
        all_standardized.append(standardized)
        baseline = baselines.get(str(row.subject_id))
        for timestep, value in enumerate(physiology[:, relative_mar_index]):
            record = {
                "split": str(row.split),
                "subject_id": str(row.subject_id),
                "session_id": str(row.session_id),
                "label": int(row.label),
                "path": str(row.path),
                "start_seconds": float(row.start_seconds),
                "timestep": timestep,
                "relative_mar": float(value),
                "standardized_relative_mar": float(standardized[timestep, relative_mar_index]),
                "visual_quality": float(quality[timestep, 0]),
                "physical_quality": float(quality[timestep, 1]),
                "baseline_mar": float(baseline.mar) if baseline is not None else None,
                "estimated_raw_mar": (
                    float(value * baseline.mar) if baseline is not None else None
                ),
            }
            candidate = (float(value), counter, record)
            counter += 1
            if len(largest) < top_n:
                heapq.heappush(largest, candidate)
            elif candidate[0] > largest[0][0]:
                heapq.heapreplace(largest, candidate)

    standardized_values = np.concatenate(all_standardized, axis=0)
    absolute = np.abs(standardized_values)
    per_feature = []
    for index, name in enumerate(feature_names):
        per_feature.append(
            {
                "feature": name,
                "center": float(scaler.center[index]),
                "scale": float(scaler.scale[index]),
                "standardized_abs_p99": float(np.percentile(absolute[:, index], 99)),
                "standardized_abs_max": float(absolute[:, index].max()),
                "fraction_clipped": float(np.mean(absolute[:, index] > standardized_clip)),
                "post_clip_abs_max": float(np.minimum(absolute[:, index], standardized_clip).max()),
            }
        )
    return {
        "scaler_fit_split": "train",
        "evaluated_splits": ["train", "validation"],
        "scaler_observations": scaler.observations,
        "standardized_clip": standardized_clip,
        "per_feature": per_feature,
        "largest_relative_mar": [item[2] for item in sorted(largest, reverse=True)],
    }


def _sample_video_start(
    video: UtaVideo,
    subject_id: str,
    baseline: PersonalBaseline,
    face_landmarker: str | Path,
    *,
    sample_fps: float,
    diagnostic_seconds: float,
) -> list[dict[str, Any]]:
    extractor = TemporalFeatureExtractor(baseline)
    rows: list[dict[str, Any]] = []
    with MediaPipeFaceBackend(face_landmarker) as backend:
        for timestamp, frame in sampled_frames(
            video.path, sample_fps, limit_seconds=diagnostic_seconds
        ):
            observation = OcularObservation(timestamp, 0, 0, 0, 0, 0, 0, 0)
            result = backend.detect(frame, timestamp)
            if result is not None:
                try:
                    measured = geometry(result, frame.shape[1], frame.shape[0])
                    crop = _crop(frame, measured.face_box)
                    visual, physical = _qualities(result.landmarks, measured, crop, frame)
                    observation = OcularObservation(
                        timestamp,
                        measured.left_ear,
                        measured.right_ear,
                        measured.mar,
                        measured.pitch,
                        measured.yaw,
                        measured.roll,
                        float(np.sqrt(visual * physical)),
                    )
                except ValueError:
                    pass
            features = extractor.update(observation)
            row: dict[str, Any] = {
                "fold": video.fold,
                "subject_id": subject_id,
                "session_id": video.session_id,
                "label": video.label,
                "timestamp": timestamp,
                "instantaneous_quality": observation.quality,
                "instantaneous_mar": observation.mar,
                "baseline_mar": baseline.mar,
            }
            row.update(
                {
                    name: float(features[index])
                    for index, name in enumerate(TemporalFeatureExtractor.feature_names)
                }
            )
            rows.append(row)
    return rows


def _boundary_interval(frame: pd.DataFrame, start: float, end: float) -> dict[str, Any]:
    selected = frame.loc[(frame["timestamp"] >= start) & (frame["timestamp"] < end)]
    values = pd.to_numeric(selected["blink_rate_per_minute"], errors="coerce").to_numpy()
    values = values[np.isfinite(values)]
    if values.size == 0:
        raise ValueError(f"no finite blink-rate samples in [{start}, {end})")
    return {
        "samples": len(selected),
        "median": float(np.median(values)),
        "p95": float(np.percentile(values, 95)),
        "p99": float(np.percentile(values, 99)),
        "max": float(values.max()),
    }


def _baseline_mar_summary(baselines: dict[str, PersonalBaseline]) -> dict[str, Any]:
    values = np.asarray([item.mar for item in baselines.values()], dtype=np.float64)
    return {
        "subjects": len(values),
        "min": float(values.min()),
        "p1": float(np.percentile(values, 1)),
        "median": float(np.median(values)),
        "p99": float(np.percentile(values, 99)),
        "max": float(values.max()),
        "by_subject": {key: value.mar for key, value in sorted(baselines.items())},
    }


def _canonical_subject(video: UtaVideo) -> str:
    return f"fold{video.fold}_{video.subject_id}"
