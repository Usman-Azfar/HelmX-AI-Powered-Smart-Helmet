from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from helmx_drowsiness.config import ProjectConfig
from helmx_drowsiness.evaluation.causal_harness import (
    _validate_event_cache,
    aggregate_event_study,
    apply_alert_controller,
    replay_video,
    run_event_study,
    summarize_video,
    tune_event_thresholds,
)
from helmx_drowsiness.features.temporal import PersonalBaseline
from helmx_drowsiness.runtime.landmarks import FaceResult
from helmx_drowsiness.state_machine import AlertController
from helmx_drowsiness.training.provenance import sha256_file
from helmx_drowsiness.types import AlertLevel

SAMPLE_FPS = 8.0
FRAME_INTERVAL = 1.0 / SAMPLE_FPS
RNG = np.random.default_rng(2026)


def _config() -> ProjectConfig:
    return ProjectConfig.model_validate(
        {
            "schema_version": 1,
            "seed": 1,
            "data": {
                "manifest": "unused.csv",
                "image_size": 64,
                "sequence_length": 4,
                "sample_fps": SAMPLE_FPS,
                "calibration_seconds": 3.0,
                "window_stride": 4,
                "num_workers": 0,
                "augmentation": False,
                "label_names": ["alert", "low_vigilance", "drowsy"],
            },
            "model": {
                "fusion_mode": "quality_gated",
                "backbone": "mobilenetv3_small_100",
                "pretrained": False,
                "eye_pretraining_checkpoint": None,
                "physiology_features": 12,
                "hidden_size": 32,
                "temporal_blocks": 1,
                "dropout": 0.0,
                "num_classes": 3,
            },
            "training": {
                "epochs": 1,
                "batch_size": 1,
                "learning_rate": 0.001,
                "weight_decay": 0.0,
                "label_smoothing": 0.0,
                "mixed_precision": False,
                "gradient_accumulation": 1,
                "early_stopping_patience": 1,
                "seeds": [1],
            },
            "alert": {
                "caution_probability": 0.55,
                "warning_probability": 0.72,
                "critical_probability": 0.88,
                "release_probability": 0.40,
                "caution_seconds": 0.1,
                "warning_seconds": 0.1,
                "critical_seconds": 0.1,
                "release_seconds": 0.1,
                "unavailable_seconds": 0.5,
                "alarm_cooldown_seconds": 0.0,
            },
        }
    )


def _good_face_result() -> FaceResult:
    landmarks = np.zeros((478, 3), dtype=np.float32)
    shape = np.array(
        [[0.2, 0.5], [0.3, 0.4], [0.5, 0.4], [0.6, 0.5], [0.5, 0.6], [0.3, 0.6]],
        dtype=np.float32,
    )
    left = [362, 385, 387, 263, 373, 380]
    right = [33, 160, 158, 133, 153, 144]
    mouth = [61, 81, 13, 291, 14, 178]
    landmarks[left, :2] = shape
    landmarks[right, :2] = shape
    landmarks[mouth, :2] = shape
    return FaceResult(landmarks, {}, None)


def test_event_cache_migrates_missing_full_face_visual_region(tmp_path) -> None:
    config = _config()
    model_path = tmp_path / "model.onnx"
    landmarker_path = tmp_path / "face.task"
    model_path.write_bytes(b"model")
    landmarker_path.write_bytes(b"landmarker")
    cache_root = tmp_path / "cache"
    cache_root.mkdir()
    old_data = config.data.model_dump(mode="json")
    old_data.pop("visual_region")
    old_provenance = {
        "schema_version": 2,
        "inference_config": {
            "data": old_data,
            "model": config.model.model_dump(mode="json"),
        },
        "onnx_sha256": sha256_file(model_path),
        "onnx_data_sha256": None,
        "face_landmarker_sha256": sha256_file(landmarker_path),
    }
    (cache_root / "provenance.json").write_text(json.dumps(old_provenance), encoding="utf-8")

    _validate_event_cache(cache_root, config, model_path, landmarker_path)

    migrated = json.loads((cache_root / "provenance.json").read_text(encoding="utf-8"))
    assert migrated["inference_config"]["data"]["visual_region"] == "full_face"


def _high_quality_frames(count: int) -> list[tuple[float, np.ndarray]]:
    # Random noise gives a high Laplacian variance (sharp) so visual quality clears the
    # 0.65 calibration threshold without depending on a real camera frame.
    return [
        (index * FRAME_INTERVAL, RNG.integers(0, 255, (120, 120, 3), dtype=np.uint8))
        for index in range(count)
    ]


class _ConstantBackend:
    def __init__(self, result: FaceResult | None) -> None:
        self.result = result

    def detect(self, frame_bgr: np.ndarray, timestamp_seconds: float) -> FaceResult | None:
        return self.result


class _ConstantRunner:
    def __init__(self, drowsy_probability: float, num_classes: int = 3) -> None:
        self.drowsy_probability = drowsy_probability
        self.num_classes = num_classes

    def predict(
        self, frames: np.ndarray, physiology: np.ndarray, quality: np.ndarray
    ) -> np.ndarray:
        scores = np.zeros((1, self.num_classes), dtype=np.float32)
        scores[0, -1] = self.drowsy_probability
        scores[0, 0] = 1.0 - self.drowsy_probability
        return scores


def _replay(config: ProjectConfig, drowsy_probability: float, *, label: int, frame_count: int = 60):
    return replay_video(
        _high_quality_frames(frame_count),
        backend=_ConstantBackend(_good_face_result()),
        runner=_ConstantRunner(drowsy_probability),
        controller=AlertController(config.alert),
        config=config,
        dataset="synthetic",
        subject_id="subject-1",
        session_id="session-1",
        label=label,
    )


def test_replay_stays_unavailable_during_calibration_and_warmup() -> None:
    config = _config()
    replay = _replay(config, drowsy_probability=0.95, label=2, frame_count=32)
    # 30 calibration frames + 4 buffer warm-up frames leaves no room for a prediction yet.
    assert all(level == AlertLevel.UNAVAILABLE for level in replay.levels)


def test_replay_reaches_critical_once_probability_is_sustained() -> None:
    config = _config()
    replay = _replay(config, drowsy_probability=0.95, label=2, frame_count=60)
    assert AlertLevel.CRITICAL in replay.levels
    assert replay.probability[-1] == pytest.approx(0.95)


def test_external_neutral_baseline_skips_in_clip_calibration() -> None:
    config = _config()
    baseline = PersonalBaseline(ear=0.3, mar=0.2, pitch=0.0, yaw=0.0, roll=0.0)
    replay = replay_video(
        _high_quality_frames(12),
        backend=_ConstantBackend(_good_face_result()),
        runner=_ConstantRunner(0.95),
        controller=AlertController(config.alert),
        config=config,
        dataset="synthetic",
        subject_id="subject-1",
        session_id="session-1",
        label=2,
        baseline=baseline,
    )

    assert replay.probability[-1] == pytest.approx(0.95)


def test_replay_never_alerts_for_a_consistently_alert_probability() -> None:
    config = _config()
    replay = _replay(config, drowsy_probability=0.05, label=0, frame_count=60)
    assert max(replay.levels) < AlertLevel.WARNING


def test_cached_trace_can_be_rescored_without_rerunning_inference() -> None:
    config = _config()
    replay = _replay(config, drowsy_probability=0.60, label=2, frame_count=60)
    assert max(replay.levels) < AlertLevel.WARNING
    lowered = config.alert.model_copy(
        update={
            "release_probability": 0.20,
            "caution_probability": 0.35,
            "warning_probability": 0.50,
            "critical_probability": 0.66,
        }
    )

    rescored = apply_alert_controller(replay, lowered)

    assert AlertLevel.WARNING in rescored.levels
    assert np.array_equal(rescored.probability, replay.probability)


def test_replay_rejects_empty_frame_source() -> None:
    config = _config()
    with pytest.raises(ValueError, match="no sampled frames"):
        replay_video(
            [],
            backend=_ConstantBackend(None),
            runner=_ConstantRunner(0.0),
            controller=AlertController(config.alert),
            config=config,
            dataset="synthetic",
            subject_id="subject-1",
            session_id="session-1",
            label=0,
        )


def test_summarize_video_reports_time_to_first_alert() -> None:
    config = _config()
    replay = _replay(config, drowsy_probability=0.95, label=2, frame_count=60)
    summary = summarize_video(replay)
    assert summary.time_to_first_alert_seconds is not None
    assert summary.alert_count >= 1
    assert summary.unavailable_fraction > 0.0


def test_summarize_video_reports_no_alert_when_none_fired() -> None:
    config = _config()
    replay = _replay(config, drowsy_probability=0.05, label=0, frame_count=60)
    summary = summarize_video(replay)
    assert summary.time_to_first_alert_seconds is None
    assert summary.alert_count == 0


def test_aggregate_event_study_pools_detection_and_false_alarms() -> None:
    config = _config()
    drowsy = _replay(config, drowsy_probability=0.95, label=2, frame_count=60)
    alert = _replay(config, drowsy_probability=0.05, label=0, frame_count=60)
    low_vigilance = _replay(config, drowsy_probability=0.60, label=1, frame_count=60)

    study = aggregate_event_study(
        [drowsy, alert, low_vigilance],
        alert_label=0,
        drowsy_label=2,
        low_vigilance_label=1,
    )

    assert study.videos == 2
    assert study.true_events == 1
    assert study.detected_events == 1
    assert study.event_sensitivity == pytest.approx(1.0)
    assert study.false_alert_events == 0
    assert not np.isnan(study.median_detection_delay_seconds)
    assert study.low_vigilance is not None
    assert study.low_vigilance["videos"] == 1
    assert study.low_vigilance["fraction_reaching_caution_or_above"] == pytest.approx(1.0)


def test_aggregate_event_study_requires_alert_or_drowsy_videos() -> None:
    config = _config()
    low_vigilance = _replay(config, drowsy_probability=0.60, label=1, frame_count=60)
    with pytest.raises(ValueError, match="no alert- or drowsy-labeled"):
        aggregate_event_study([low_vigilance], alert_label=0, drowsy_label=2)


def test_threshold_tuning_uses_zero_false_alert_validation_frontier() -> None:
    config = _config()
    drowsy = _replay(config, drowsy_probability=0.60, label=2, frame_count=60)
    alert = _replay(config, drowsy_probability=0.20, label=0, frame_count=60)

    fit = tune_event_thresholds(
        [drowsy, alert],
        config.alert,
        alert_label=0,
        drowsy_label=2,
        warning_candidates=[0.50, 0.70],
    )

    assert fit.feasible
    assert fit.selected is not None
    assert fit.selected.warning_probability == pytest.approx(0.50)
    assert fit.selected.event_sensitivity == pytest.approx(1.0)
    assert fit.selected.false_alert_events == 0


def test_threshold_tuning_preserves_infeasible_frontier() -> None:
    config = _config()
    drowsy = _replay(config, drowsy_probability=0.60, label=2, frame_count=60)
    alert = _replay(config, drowsy_probability=0.60, label=0, frame_count=60)

    fit = tune_event_thresholds(
        [drowsy, alert],
        config.alert,
        alert_label=0,
        drowsy_label=2,
        warning_candidates=[0.50],
    )

    assert not fit.feasible
    assert fit.selected is None
    assert len(fit.candidates) == 1
    assert fit.candidates[0].false_alert_events == 1


def test_run_event_study_validates_required_columns_before_loading_models() -> None:
    config = _config()
    videos = pd.DataFrame({"dataset": ["uta_rldd"], "subject_id": ["s1"]})
    with pytest.raises(ValueError, match="missing columns"):
        run_event_study(
            videos,
            config=config,
            onnx_model="does-not-exist.onnx",
            face_landmarker="does-not-exist.task",
            alert_label=0,
            drowsy_label=2,
        )
