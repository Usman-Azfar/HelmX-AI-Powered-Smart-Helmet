"""Offline causal replay of full videos through the deployed inference and alert pipeline.

Window-level classification metrics (``evaluation.metrics``) score isolated 3-second
snippets. They cannot say how quickly a continuously-running system raises a warning, or
how often it raises one when it should not - and the deployed system is judged on exactly
that. This module replays a whole video frame-by-frame through the same calibration,
temporal buffering, and :class:`~helmx_drowsiness.state_machine.AlertController` logic as
:func:`helmx_drowsiness.runtime.app.run_camera`, so event-level metrics reflect true
causal, deployed behaviour rather than an offline batch evaluation of independent windows.

Ground-truth mapping for UTA-RLDD's clip-level labels
-------------------------------------------------------
UTA-RLDD provides one label per whole video (alert / low_vigilance / drowsy), not
frame-level drowsy-event annotations. :func:`aggregate_event_study` therefore treats:

- an ``alert_label`` video as a pure negative recording, used only to measure false
  alarms per hour;
- a ``drowsy_label`` video as one continuous true event spanning the whole recording,
  used for event sensitivity and detection delay;
- a ``low_vigilance_label`` video as a deliberately separate slice, reported only as the
  fraction that ever reaches CAUTION or above. Folding this subtle intermediate class into
  a binary true/false event would misrepresent both the false-alarm rate and the
  detection-delay statistic.

This is a documented modelling choice, not a fact about the dataset - revisit it if the
final study needs a different definition of "event" for the low-vigilance class.

Per-video rows returned by :func:`aggregate_event_study` carry ``subject_id`` so a caller
can group by subject before pooling, per ``docs/RESEARCH_PROTOCOL.md``'s "aggregate first
by subject/session, then across subjects" rule. For UTA-RLDD, each subject contributes at
most one alert and one drowsy video, so video-level and subject-level pooling coincide
here; a dataset with multiple sessions per class per subject would need an extra grouping
step before pooling.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import deque
from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from helmx_drowsiness.config import AlertConfig, ProjectConfig
from helmx_drowsiness.datasets.preprocess import collect_neutral_calibration, sampled_frames
from helmx_drowsiness.evaluation.events import EventMetrics, event_metrics
from helmx_drowsiness.features.quality import landmark_quality, visual_quality
from helmx_drowsiness.features.temporal import (
    OcularObservation,
    PersonalBaseline,
    TemporalFeatureExtractor,
    fit_personal_baseline,
)
from helmx_drowsiness.runtime.app import padded_crop, prepare_face
from helmx_drowsiness.runtime.landmarks import FaceResult, MediaPipeFaceBackend, geometry
from helmx_drowsiness.runtime.onnx_runner import OnnxTemporalRunner
from helmx_drowsiness.state_machine import AlertController
from helmx_drowsiness.training.provenance import sha256_file, write_json
from helmx_drowsiness.types import AlertLevel, FrameEvidence

DEFAULT_MINIMUM_QUALITY = 0.35
REQUIRED_VIDEO_COLUMNS = {"dataset", "subject_id", "session_id", "path", "label"}


class FaceBackend(Protocol):
    def detect(
        self, frame_bgr: NDArray[np.uint8], timestamp_seconds: float
    ) -> FaceResult | None: ...


class TemporalRunner(Protocol):
    def predict(
        self,
        frames: NDArray[np.float32],
        physiology: NDArray[np.float32],
        quality: NDArray[np.float32],
    ) -> NDArray[np.float32]: ...


@dataclass(frozen=True, slots=True)
class VideoReplay:
    """Per-frame causal trace for one fully-replayed video."""

    dataset: str
    subject_id: str
    session_id: str
    label: int
    timestamps: NDArray[np.float64]
    quality: NDArray[np.float64]
    probability: NDArray[np.float64]
    levels: tuple[AlertLevel, ...]


def apply_alert_controller(
    replay: VideoReplay,
    alert_config: AlertConfig,
    *,
    minimum_quality: float = DEFAULT_MINIMUM_QUALITY,
) -> VideoReplay:
    """Recompute decisions from a cached causal model trace without rerunning video inference.

    A strictly positive probability marks the first completed model window. Softmax output is
    positive for every finite model logit; the replay loop deliberately stores zero before that
    first inference. Missing-face samples after inference retain the last probability and carry
    zero quality, so they still pass through the controller's unavailable-state logic.
    """

    controller = AlertController(alert_config, minimum_quality=minimum_quality)
    inference_started = False
    levels: list[AlertLevel] = []
    for timestamp, probability, quality in zip(
        replay.timestamps, replay.probability, replay.quality, strict=True
    ):
        inference_started = inference_started or probability > 0.0
        if not inference_started:
            levels.append(AlertLevel.UNAVAILABLE)
            continue
        decision = controller.update(
            FrameEvidence(float(timestamp), float(probability), float(quality))
        )
        levels.append(decision.level)
    return replace(replay, levels=tuple(levels))


def replay_video(
    frames: Iterable[tuple[float, NDArray[np.uint8]]],
    *,
    backend: FaceBackend,
    runner: TemporalRunner,
    controller: AlertController,
    config: ProjectConfig,
    dataset: str,
    subject_id: str,
    session_id: str,
    label: int,
    baseline: PersonalBaseline | None = None,
) -> VideoReplay:
    """Causally replay one video's sampled frames through calibration and the alert loop.

    Deliberately mirrors ``runtime.app.run_camera``'s control flow frame-for-frame
    (calibration gating, causal buffering, and exactly when ``controller.update`` is or is
    not called) so offline event metrics reflect what a rider would actually see, not an
    idealized simulation. ``frames`` must already be sampled at ``config.data.sample_fps``,
    e.g. via ``datasets.preprocess.sampled_frames``.
    """

    calibration: list[OcularObservation] = []
    calibration_target = max(
        30, math.ceil(config.data.calibration_seconds * config.data.sample_fps)
    )
    feature_extractor = TemporalFeatureExtractor(baseline) if baseline is not None else None
    frame_buffer: deque[NDArray[np.float32]] = deque(maxlen=config.data.sequence_length)
    feature_buffer: deque[NDArray[np.float32]] = deque(maxlen=config.data.sequence_length)
    quality_buffer: deque[NDArray[np.float32]] = deque(maxlen=config.data.sequence_length)

    timestamps: list[float] = []
    qualities: list[float] = []
    probabilities: list[float] = []
    levels: list[AlertLevel] = []
    probability = 0.0
    level = AlertLevel.UNAVAILABLE

    for timestamp, frame in frames:
        face = backend.detect(frame, timestamp)
        monitoring_quality = 0.0
        if face is not None:
            measured = geometry(face, frame.shape[1], frame.shape[0])
            crop = padded_crop(frame, measured.face_box, padding=0.15)
            face_fraction = (crop.shape[0] * crop.shape[1]) / (frame.shape[0] * frame.shape[1])
            visual, _ = visual_quality(crop, detection_confidence=1.0, face_fraction=face_fraction)
            physical, _ = landmark_quality(
                face.landmarks,
                left_ear=measured.left_ear,
                right_ear=measured.right_ear,
                mar=measured.mar,
            )
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
            if feature_extractor is None:
                if monitoring_quality >= 0.65 and len(calibration) < calibration_target:
                    calibration.append(observation)
                if len(calibration) >= calibration_target:
                    feature_extractor = TemporalFeatureExtractor(fit_personal_baseline(calibration))
            else:
                frame_buffer.append(
                    prepare_face(
                        crop,
                        config.data.image_size,
                        visual_region=config.data.visual_region,
                    )
                )
                feature_buffer.append(feature_extractor.update(observation))
                quality_buffer.append(np.asarray([visual, physical], dtype=np.float32))
                if len(frame_buffer) == config.data.sequence_length:
                    scores = runner.predict(
                        np.stack(frame_buffer)[None],
                        np.stack(feature_buffer)[None],
                        np.stack(quality_buffer)[None],
                    )
                    probability = float(scores[0, -1])
                    decision = controller.update(
                        FrameEvidence(timestamp, probability, monitoring_quality)
                    )
                    level = decision.level
        elif feature_extractor is not None:
            decision = controller.update(FrameEvidence(timestamp, probability, 0.0))
            level = decision.level

        timestamps.append(timestamp)
        qualities.append(monitoring_quality)
        probabilities.append(probability)
        levels.append(level)

    if not timestamps:
        raise ValueError("replay produced no sampled frames")
    return VideoReplay(
        dataset=dataset,
        subject_id=subject_id,
        session_id=session_id,
        label=label,
        timestamps=np.asarray(timestamps, dtype=np.float64),
        quality=np.asarray(qualities, dtype=np.float64),
        probability=np.asarray(probabilities, dtype=np.float64),
        levels=tuple(levels),
    )


@dataclass(frozen=True, slots=True)
class PerVideoEventSummary:
    """Deployment-facing signals for one video beyond plain event sensitivity/false alarms."""

    duration_seconds: float
    unavailable_fraction: float
    quality_suppressed_fraction: float
    alert_count: int
    mean_alert_duration_seconds: float
    time_to_first_alert_seconds: float | None


def summarize_video(
    replay: VideoReplay, *, minimum_quality: float = DEFAULT_MINIMUM_QUALITY
) -> PerVideoEventSummary:
    """Derive per-video no-face, quality-suppression, and alert-episode statistics."""

    levels = np.asarray([int(level) for level in replay.levels])
    duration = (
        float(replay.timestamps[-1] - replay.timestamps[0]) if len(replay.timestamps) > 1 else 0.0
    )
    unavailable_fraction = float((levels == int(AlertLevel.UNAVAILABLE)).mean())
    quality_suppressed_fraction = float((replay.quality < minimum_quality).mean())
    alert_active = levels >= int(AlertLevel.WARNING)
    runs = _boolean_runs(alert_active)
    mean_alert_duration = (
        float(np.mean([replay.timestamps[end] - replay.timestamps[start] for start, end in runs]))
        if runs
        else 0.0
    )
    time_to_first_alert = (
        float(replay.timestamps[int(np.argmax(alert_active))] - replay.timestamps[0])
        if alert_active.any()
        else None
    )
    return PerVideoEventSummary(
        duration_seconds=duration,
        unavailable_fraction=unavailable_fraction,
        quality_suppressed_fraction=quality_suppressed_fraction,
        alert_count=len(runs),
        mean_alert_duration_seconds=mean_alert_duration,
        time_to_first_alert_seconds=time_to_first_alert,
    )


@dataclass(frozen=True, slots=True)
class EventStudy:
    """Pooled causal event-level results across every alert/drowsy test video.

    Pooled from per-video :class:`~helmx_drowsiness.evaluation.events.EventMetrics`, never
    from concatenated per-frame arrays - videos are independent recording sessions, and
    concatenating their timelines would fabricate cross-video "events" and hours.
    """

    videos: int
    true_events: int
    detected_events: int
    event_sensitivity: float
    false_alert_events: int
    non_drowsy_hours: float
    false_alerts_per_hour: float
    median_detection_delay_seconds: float
    p95_detection_delay_seconds: float
    per_video: list[dict[str, Any]]
    low_vigilance: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class AlertThresholdCandidate:
    """One validation-only operating point on the event-level sensitivity/false-alert frontier."""

    release_probability: float
    caution_probability: float
    warning_probability: float
    critical_probability: float
    warning_seconds: float
    critical_seconds: float
    event_sensitivity: float
    detected_events: int
    true_events: int
    false_alert_events: int
    false_alerts_per_hour: float


@dataclass(frozen=True, slots=True)
class AlertThresholdFit:
    """Auditable validation-only selection of probability thresholds."""

    criterion: str
    validation_videos: int
    feasible: bool
    selected: AlertThresholdCandidate | None
    candidates: list[AlertThresholdCandidate]


def tune_event_thresholds(
    replays: list[VideoReplay],
    base_config: AlertConfig,
    *,
    alert_label: int,
    drowsy_label: int,
    warning_candidates: Iterable[float],
    warning_durations: Iterable[float] | None = None,
    minimum_quality: float = DEFAULT_MINIMUM_QUALITY,
) -> AlertThresholdFit:
    """Tune one threshold family using validation replays, never test replays.

    The preregistered offsets between release/caution/warning/critical are preserved, limiting
    this correction to one degree of freedom. Selection maximizes event sensitivity subject to
    zero observed false-alert events on validation alert clips; ties choose the higher (more
    conservative) warning threshold.
    """

    if not replays:
        raise ValueError("threshold tuning requires validation replays")
    candidates: list[AlertThresholdCandidate] = []
    probabilities = list(warning_candidates)
    durations = (
        list(warning_durations) if warning_durations is not None else [base_config.warning_seconds]
    )
    if not probabilities:
        raise ValueError("warning_candidates must not be empty")
    if not durations or any(duration <= 0 for duration in durations):
        raise ValueError("warning_durations must contain positive values")
    for warning_probability in probabilities:
        for warning_seconds in durations:
            candidate_config = _shift_alert_thresholds(
                base_config, float(warning_probability), float(warning_seconds)
            )
            rescored = [
                apply_alert_controller(replay, candidate_config, minimum_quality=minimum_quality)
                for replay in replays
            ]
            study = aggregate_event_study(
                rescored,
                alert_label=alert_label,
                drowsy_label=drowsy_label,
                minimum_quality=minimum_quality,
            )
            candidates.append(
                AlertThresholdCandidate(
                    release_probability=candidate_config.release_probability,
                    caution_probability=candidate_config.caution_probability,
                    warning_probability=candidate_config.warning_probability,
                    critical_probability=candidate_config.critical_probability,
                    warning_seconds=candidate_config.warning_seconds,
                    critical_seconds=candidate_config.critical_seconds,
                    event_sensitivity=study.event_sensitivity,
                    detected_events=study.detected_events,
                    true_events=study.true_events,
                    false_alert_events=study.false_alert_events,
                    false_alerts_per_hour=study.false_alerts_per_hour,
                )
            )
    feasible = [candidate for candidate in candidates if candidate.false_alert_events == 0]
    selected = (
        max(
            feasible,
            key=lambda candidate: (
                candidate.event_sensitivity,
                -candidate.warning_seconds,
                candidate.warning_probability,
            ),
        )
        if feasible
        else None
    )
    return AlertThresholdFit(
        criterion=(
            "maximize validation event sensitivity subject to zero observed validation "
            "false-alert events; break ties with shorter warning persistence, then the higher "
            "warning threshold"
        ),
        validation_videos=len(replays),
        feasible=bool(feasible),
        selected=selected,
        candidates=candidates,
    )


def _shift_alert_thresholds(
    base: AlertConfig, warning_probability: float, warning_seconds: float
) -> AlertConfig:
    caution_gap = base.warning_probability - base.caution_probability
    release_gap = base.warning_probability - base.release_probability
    critical_gap = base.critical_probability - base.warning_probability
    payload = base.model_dump()
    payload.update(
        {
            "release_probability": warning_probability - release_gap,
            "caution_probability": warning_probability - caution_gap,
            "warning_probability": warning_probability,
            "critical_probability": warning_probability + critical_gap,
            "warning_seconds": warning_seconds,
            "critical_seconds": max(base.critical_seconds, warning_seconds),
        }
    )
    return AlertConfig.model_validate(payload)


def aggregate_event_study(
    replays: list[VideoReplay],
    *,
    alert_label: int,
    drowsy_label: int,
    low_vigilance_label: int | None = None,
    minimum_quality: float = DEFAULT_MINIMUM_QUALITY,
) -> EventStudy:
    """Pool per-video event metrics per the module-level ground-truth mapping."""

    if not replays:
        raise ValueError("aggregate_event_study requires at least one replayed video")
    primary = [replay for replay in replays if replay.label in (alert_label, drowsy_label)]
    if not primary:
        raise ValueError("no alert- or drowsy-labeled videos to aggregate")

    per_video_metrics: list[EventMetrics] = []
    per_video_rows: list[dict[str, Any]] = []
    for replay in primary:
        truth = np.full(replay.timestamps.shape, replay.label == drowsy_label, dtype=bool)
        levels = np.asarray([int(level) for level in replay.levels])
        alert_active = levels >= int(AlertLevel.WARNING)
        metrics = event_metrics(replay.timestamps, truth, alert_active)
        per_video_metrics.append(metrics)
        summary = summarize_video(replay, minimum_quality=minimum_quality)
        per_video_rows.append(
            {
                "dataset": replay.dataset,
                "subject_id": replay.subject_id,
                "session_id": replay.session_id,
                "label": replay.label,
                **asdict(summary),
                **asdict(metrics),
            }
        )

    true_events = sum(metrics.true_events for metrics in per_video_metrics)
    detected_events = sum(metrics.detected_events for metrics in per_video_metrics)
    false_alert_events = sum(metrics.false_alert_events for metrics in per_video_metrics)
    non_drowsy_hours = sum(metrics.non_drowsy_hours for metrics in per_video_metrics)
    delays = [
        metrics.median_detection_delay_seconds
        for metrics in per_video_metrics
        if not math.isnan(metrics.median_detection_delay_seconds)
    ]

    return EventStudy(
        videos=len(primary),
        true_events=true_events,
        detected_events=detected_events,
        event_sensitivity=detected_events / true_events if true_events else float("nan"),
        false_alert_events=false_alert_events,
        non_drowsy_hours=non_drowsy_hours,
        false_alerts_per_hour=(
            false_alert_events / non_drowsy_hours if non_drowsy_hours > 0 else float("nan")
        ),
        median_detection_delay_seconds=float(np.median(delays)) if delays else float("nan"),
        p95_detection_delay_seconds=float(np.percentile(delays, 95)) if delays else float("nan"),
        per_video=per_video_rows,
        low_vigilance=_low_vigilance_summary(replays, low_vigilance_label),
    )


def _low_vigilance_summary(
    replays: list[VideoReplay], low_vigilance_label: int | None
) -> dict[str, Any] | None:
    if low_vigilance_label is None:
        return None
    videos = [replay for replay in replays if replay.label == low_vigilance_label]
    if not videos:
        return None
    reached_caution = [
        any(int(level) >= int(AlertLevel.CAUTION) for level in replay.levels) for replay in videos
    ]
    return {
        "videos": len(videos),
        "fraction_reaching_caution_or_above": float(np.mean(reached_caution)),
    }


def run_event_study(
    videos: pd.DataFrame,
    *,
    config: ProjectConfig,
    onnx_model: str | Path,
    face_landmarker: str | Path,
    alert_label: int,
    drowsy_label: int,
    low_vigilance_label: int | None = None,
    minimum_quality: float = DEFAULT_MINIMUM_QUALITY,
    cache_dir: str | Path | None = None,
) -> EventStudy:
    """Causally replay every row of a raw-video table and pool the resulting event study.

    ``videos`` needs ``dataset``, ``subject_id``, ``session_id``, ``path``, and ``label``
    columns, where ``path`` points at an original continuous recording, not a preprocessed
    NPZ training window - detection delay and false-alarm rate require an unbroken
    per-video timeline, which the sparsely-windowed training manifest does not preserve.
    """

    missing = REQUIRED_VIDEO_COLUMNS.difference(videos.columns)
    if missing:
        raise ValueError(f"video table is missing columns: {sorted(missing)}")
    if videos.empty:
        raise ValueError("video table is empty")

    cache_root = Path(cache_dir) if cache_dir is not None else None
    if cache_root is not None:
        _validate_event_cache(cache_root, config, onnx_model, face_landmarker)
    runner = OnnxTemporalRunner(onnx_model)
    replays: list[VideoReplay] = []
    for row in videos.itertuples():
        replay_cache = (
            cache_root / f"replay_{_row_cache_key(row)}.npz" if cache_root is not None else None
        )
        if replay_cache is not None and replay_cache.is_file():
            replays.append(
                apply_alert_controller(
                    _load_replay_cache(replay_cache),
                    config.alert,
                    minimum_quality=minimum_quality,
                )
            )
            continue
        baseline = _load_or_fit_event_baseline(
            row,
            cache_root,
            face_landmarker,
            sample_fps=config.data.sample_fps,
        )
        controller = AlertController(config.alert, minimum_quality=minimum_quality)
        frames = sampled_frames(str(row.path), config.data.sample_fps)
        # MediaPipe VIDEO mode requires timestamps to increase within one stream. Each raw
        # file starts again at t=0, so do not carry tracking/timestamp state between videos.
        with MediaPipeFaceBackend(face_landmarker) as backend:
            replay = replay_video(
                frames,
                backend=backend,
                runner=runner,
                controller=controller,
                config=config,
                dataset=str(row.dataset),
                subject_id=str(row.subject_id),
                session_id=str(row.session_id),
                label=int(row.label),
                baseline=baseline,
            )
        replays.append(replay)
        if replay_cache is not None:
            _save_replay_cache(replay_cache, replay)
    return aggregate_event_study(
        replays,
        alert_label=alert_label,
        drowsy_label=drowsy_label,
        low_vigilance_label=low_vigilance_label,
        minimum_quality=minimum_quality,
    )


def _load_or_fit_event_baseline(
    row: Any,
    cache_root: Path | None,
    face_landmarker: str | Path,
    *,
    sample_fps: float,
) -> PersonalBaseline | None:
    calibration_path = getattr(row, "calibration_path", None)
    if calibration_path is None or pd.isna(calibration_path):
        return None
    baseline_cache = (
        cache_root / f"baseline_{_subject_cache_key(row)}.json" if cache_root is not None else None
    )
    if baseline_cache is not None and baseline_cache.is_file():
        return PersonalBaseline(**json.loads(baseline_cache.read_text(encoding="utf-8")))
    baseline = collect_neutral_calibration(
        str(calibration_path), face_landmarker, sample_fps=sample_fps, seconds=20.0
    )
    if baseline_cache is not None:
        write_json(baseline_cache, asdict(baseline))
    return baseline


def _validate_event_cache(
    cache_root: Path,
    config: ProjectConfig,
    onnx_model: str | Path,
    face_landmarker: str | Path,
) -> None:
    cache_root.mkdir(parents=True, exist_ok=True)
    model_path = Path(onnx_model)
    sidecar = model_path.with_suffix(model_path.suffix + ".data")
    provenance: dict[str, Any] = {
        "schema_version": 2,
        # Alert thresholds are intentionally excluded: cached timestamps/probabilities/quality
        # are inference traces, and apply_alert_controller safely rescores them. This permits
        # validation-only threshold tuning without spending hours decoding every video again.
        "inference_config": {
            "data": config.data.model_dump(mode="json"),
            "model": config.model.model_dump(mode="json"),
        },
        "onnx_sha256": sha256_file(model_path),
        "onnx_data_sha256": sha256_file(sidecar) if sidecar.is_file() else None,
        "face_landmarker_sha256": sha256_file(face_landmarker),
    }
    path = cache_root / "provenance.json"
    if path.is_file():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != provenance:
            # ``visual_region`` was added after the original full-face event traces were
            # generated.  Treat its absent value as the historical full-face default so
            # those expensive traces remain resumable, while still rejecting an eye-band
            # configuration (or any other genuine inference-contract change).
            existing_inference = existing.get("inference_config", {})
            existing_data = dict(existing_inference.get("data", {}))
            existing_data.setdefault("visual_region", "full_face")
            current_data = provenance["inference_config"]["data"]
            current_model = provenance["inference_config"]["model"]
            schema_two_matches = (
                existing.get("schema_version") == 2
                and existing_data == current_data
                and existing_inference.get("model") == current_model
                and existing.get("onnx_sha256") == provenance["onnx_sha256"]
                and existing.get("onnx_data_sha256") == provenance["onnx_data_sha256"]
                and existing.get("face_landmarker_sha256") == provenance["face_landmarker_sha256"]
            )
            legacy_config = existing.get("config", {})
            legacy_data = dict(legacy_config.get("data", {}))
            legacy_data.setdefault("visual_region", "full_face")
            legacy_matches = (
                legacy_data == current_data
                and legacy_config.get("model") == current_model
                and existing.get("onnx_sha256") == provenance["onnx_sha256"]
                and existing.get("onnx_data_sha256") == provenance["onnx_data_sha256"]
                and existing.get("face_landmarker_sha256") == provenance["face_landmarker_sha256"]
            )
            if not (schema_two_matches or legacy_matches):
                raise ValueError("event cache provenance does not match inference config/assets")
            write_json(path, provenance)
    else:
        write_json(path, provenance)


def load_replay_caches(cache_dir: str | Path) -> list[VideoReplay]:
    """Load raw causal inference traces for validation-only controller tuning."""

    paths = sorted(Path(cache_dir).glob("replay_*.npz"))
    if not paths:
        raise ValueError(f"no replay caches found under {cache_dir}")
    return [_load_replay_cache(path) for path in paths]


def _save_replay_cache(path: Path, replay: VideoReplay) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(
            stream,
            dataset=np.asarray(replay.dataset),
            subject_id=np.asarray(replay.subject_id),
            session_id=np.asarray(replay.session_id),
            label=np.asarray(replay.label, dtype=np.int64),
            timestamps=replay.timestamps,
            quality=replay.quality,
            probability=replay.probability,
            levels=np.asarray([int(level) for level in replay.levels], dtype=np.int8),
        )
    temporary.replace(path)


def _load_replay_cache(path: Path) -> VideoReplay:
    with np.load(path, allow_pickle=False) as payload:
        return VideoReplay(
            dataset=str(payload["dataset"].item()),
            subject_id=str(payload["subject_id"].item()),
            session_id=str(payload["session_id"].item()),
            label=int(payload["label"].item()),
            timestamps=np.asarray(payload["timestamps"], dtype=np.float64),
            quality=np.asarray(payload["quality"], dtype=np.float64),
            probability=np.asarray(payload["probability"], dtype=np.float64),
            levels=tuple(AlertLevel(int(value)) for value in payload["levels"]),
        )


def _row_cache_key(row: Any) -> str:
    value = f"{row.dataset}|{row.subject_id}|{row.session_id}|{row.path}"
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _subject_cache_key(row: Any) -> str:
    value = f"{row.dataset}|{row.subject_id}|{row.calibration_path}"
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _boolean_runs(values: NDArray[np.bool_]) -> list[tuple[int, int]]:
    """Contiguous True-run start/end indices (inclusive).

    Mirrors ``evaluation.events._runs``; duplicated locally rather than imported since that
    helper is private to its module.
    """

    padded = np.pad(values.astype(np.int8), (1, 1))
    changes = np.diff(padded)
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1) - 1
    return list(zip(starts.tolist(), ends.tolist(), strict=True))
