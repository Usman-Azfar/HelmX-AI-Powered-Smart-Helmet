from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from helmx_drowsiness.datasets.label_confidence import (
    add_adaptive_label_confidence,
    add_label_confidence,
    tercile_weight,
)


def test_tercile_weight_boundaries() -> None:
    assert tercile_weight(0.0) == 0.5
    assert tercile_weight(1.0 / 3.0) == 0.5
    assert tercile_weight(1.0 / 3.0 + 1e-9) == 0.75
    assert tercile_weight(2.0 / 3.0) == 0.75
    assert tercile_weight(2.0 / 3.0 + 1e-9) == 1.0
    assert tercile_weight(1.0) == 1.0


def _windows(
    subject: str, session: str, label: int, starts: list[float]
) -> list[dict[str, object]]:
    return [
        {
            "dataset": "uta_rldd",
            "subject_id": subject,
            "session_id": session,
            "path": f"{subject}_{session}_{index:03d}.npz",
            "label": label,
            "split": "train",
            "start_seconds": start,
            "end_seconds": start + 3.0,
        }
        for index, start in enumerate(starts)
    ]


def test_only_down_weighted_class_is_touched() -> None:
    rows = _windows("s1", "drowsy_clip", 2, [0.0, 30.0, 60.0, 90.0]) + _windows(
        "s2", "alert_clip", 0, [0.0, 30.0, 60.0, 90.0]
    )
    frame = pd.DataFrame(rows)
    weighted = add_label_confidence(frame, down_weighted_label=2)

    drowsy = weighted[weighted["subject_id"] == "s1"].sort_values("start_seconds")
    alert = weighted[weighted["subject_id"] == "s2"].sort_values("start_seconds")

    assert list(drowsy["label_confidence"]) == [0.5, 0.75, 0.75, 1.0]
    assert list(alert["label_confidence"]) == [1.0, 1.0, 1.0, 1.0]


def test_missing_columns_raise() -> None:
    with pytest.raises(ValueError, match="missing columns"):
        add_label_confidence(pd.DataFrame({"label": [2]}), down_weighted_label=2)


def _write_perclos_windows(
    tmp_path: Path,
    subject: str,
    session: str,
    label: int,
    starts: list[float],
    perclos: list[float],
) -> list[dict[str, object]]:
    rows = []
    for index, (start, value) in enumerate(zip(starts, perclos, strict=True)):
        name = f"{subject}_{session}_{index:03d}.npz"
        physiology = np.zeros((4, 12), dtype=np.float32)
        physiology[:, 2] = value
        np.savez_compressed(
            tmp_path / name,
            frames=np.zeros((4, 8, 8, 3), dtype=np.uint8),
            physiology=physiology,
            quality=np.ones((4, 2), dtype=np.float32),
        )
        rows.append(
            {
                "dataset": "uta_rldd",
                "subject_id": subject,
                "session_id": session,
                "path": name,
                "label": label,
                "split": "train",
                "start_seconds": start,
                "end_seconds": start + 3.0,
            }
        )
    return rows


def test_adaptive_confidence_only_down_weights_videos_with_drift(tmp_path: Path) -> None:
    ramping = _write_perclos_windows(
        tmp_path, "s1", "ramping", 2, [0.0, 30.0, 60.0, 90.0], [0.05, 0.10, 0.30, 0.60]
    )
    flat = _write_perclos_windows(
        tmp_path, "s2", "flat", 2, [0.0, 30.0, 60.0, 90.0], [0.60, 0.58, 0.59, 0.55]
    )
    frame = pd.DataFrame(ramping + flat)

    weighted = add_adaptive_label_confidence(frame, tmp_path, down_weighted_label=2)

    ramping_weights = weighted[weighted["subject_id"] == "s1"].sort_values("start_seconds")
    flat_weights = weighted[weighted["subject_id"] == "s2"].sort_values("start_seconds")

    assert list(ramping_weights["label_confidence"]) == [0.5, 0.75, 0.75, 1.0]
    assert list(flat_weights["label_confidence"]) == [1.0, 1.0, 1.0, 1.0]
