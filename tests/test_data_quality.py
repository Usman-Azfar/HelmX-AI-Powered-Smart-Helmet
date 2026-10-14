from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from helmx_drowsiness.evaluation.data_quality import (
    manifest_class_balance,
    physiology_feature_report,
)
from helmx_drowsiness.features.temporal import TemporalFeatureExtractor

BLINK_RATE_INDEX = TemporalFeatureExtractor.feature_names.index("blink_rate_per_minute")


def test_manifest_class_balance_flags_window_imbalance_despite_balanced_videos() -> None:
    rows = []
    windows_by_video = {
        ("s1", "alert-0"): 2,
        ("s2", "alert-1"): 2,
        ("s3", "alert-2"): 2,
        ("s1", "drowsy-0"): 5,
        ("s2", "drowsy-1"): 6,
        ("s3", "drowsy-2"): 4,
    }
    for (subject, session), count in windows_by_video.items():
        label = 0 if session.startswith("alert") else 2
        for index in range(count):
            rows.append(
                {
                    "dataset": "uta_rldd",
                    "subject_id": subject,
                    "session_id": session,
                    "path": f"{session}_{index}.npz",
                    "label": label,
                    "split": "train",
                }
            )
    frame = pd.DataFrame(rows)

    balance = manifest_class_balance(frame)

    alert = balance["train"]["by_class"]["0"]
    drowsy = balance["train"]["by_class"]["2"]
    assert alert["subjects"] == 3
    assert drowsy["subjects"] == 3
    assert alert["videos"] == 3
    assert drowsy["videos"] == 3
    # Videos and subjects are balanced by construction; windows are not, which is exactly
    # the gap this report exists to surface before training.
    assert alert["windows"] == 6
    assert drowsy["windows"] == 15
    assert alert["window_proportion"] < drowsy["window_proportion"]


def _write_physiology_npz(path: Path, *, blink_rate: float, timesteps: int = 3) -> None:
    physiology = np.zeros(
        (timesteps, len(TemporalFeatureExtractor.feature_names)), dtype=np.float32
    )
    physiology[:, BLINK_RATE_INDEX] = blink_rate
    np.savez_compressed(path, physiology=physiology)


def test_physiology_feature_report_separates_early_from_later_windows(tmp_path: Path) -> None:
    _write_physiology_npz(tmp_path / "early.npz", blink_rate=300.0)
    _write_physiology_npz(tmp_path / "later.npz", blink_rate=12.0)
    frame = pd.DataFrame(
        [
            {
                "dataset": "uta_rldd",
                "subject_id": "s1",
                "session_id": "drowsy-0",
                "path": "early.npz",
                "label": 2,
                "split": "train",
                "start_seconds": 0.0,
            },
            {
                "dataset": "uta_rldd",
                "subject_id": "s1",
                "session_id": "drowsy-0",
                "path": "later.npz",
                "label": 2,
                "split": "train",
                "start_seconds": 300.0,
            },
        ]
    )

    report = physiology_feature_report(frame, tmp_path, early_seconds=60.0)

    blink_rows = report[report["feature"] == "blink_rate_per_minute"].set_index("window_bucket")
    assert blink_rows.loc["early", "max"] == 300.0
    assert blink_rows.loc["later", "max"] == 12.0
    assert blink_rows["nan_inf_fraction"].eq(0.0).all()


def test_physiology_feature_report_defaults_missing_start_seconds_to_early(
    tmp_path: Path,
) -> None:
    _write_physiology_npz(tmp_path / "sample.npz", blink_rate=42.0)
    frame = pd.DataFrame(
        [
            {
                "dataset": "uta_rldd",
                "subject_id": "s1",
                "session_id": "drowsy-0",
                "path": "sample.npz",
                "label": 2,
                "split": "train",
            }
        ]
    )

    report = physiology_feature_report(frame, tmp_path)

    assert set(report["window_bucket"]) == {"early"}
