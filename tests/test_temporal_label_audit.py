from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from helmx_drowsiness.evaluation.temporal_label_audit import run_temporal_label_audit


def test_temporal_label_audit_uses_only_development_splits_and_writes_artifacts(
    tmp_path: Path,
) -> None:
    rows = []
    predictions = {"train": [], "validation": []}
    starts = (0.0, 10.0, 20.0)
    for split in ("train", "validation"):
        for label in (0, 1, 2):
            subject = f"{split}-subject-{label}"
            session = f"class-{label}"
            for index, start in enumerate(starts):
                path = f"{split}_{label}_{index}.npz"
                physiology = np.zeros((4, 12), dtype=np.float32)
                physiology[-1, 0] = 1.0 - 0.1 * index if label == 2 else 1.0
                physiology[-1, 2] = 0.1 * index if label == 2 else 0.0
                physiology[-1, 11] = 1.0
                np.savez_compressed(
                    tmp_path / path,
                    frames=np.zeros((4, 8, 8, 3), dtype=np.uint8),
                    physiology=physiology,
                    quality=np.ones((4, 2), dtype=np.float32),
                )
                rows.append(
                    {
                        "dataset": "synthetic",
                        "subject_id": subject,
                        "session_id": session,
                        "path": path,
                        "label": label,
                        "split": split,
                        "start_seconds": start,
                        "end_seconds": start + 3.0,
                    }
                )
                drowsy_probability = 0.2 + 0.2 * index if label == 2 else 0.1
                probabilities = [0.7, 0.2, 0.1]
                if label == 2:
                    probabilities = [0.2, 0.8 - drowsy_probability, drowsy_probability]
                predictions[split].append(
                    {
                        "path": path,
                        "label": label,
                        "prediction": int(np.argmax(probabilities)),
                        "probability_0": probabilities[0],
                        "probability_1": probabilities[1],
                        "probability_2": probabilities[2],
                    }
                )
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame(rows).to_csv(manifest, index=False)
    train_predictions = tmp_path / "train_predictions.csv"
    validation_predictions = tmp_path / "validation_predictions.csv"
    pd.DataFrame(predictions["train"]).to_csv(train_predictions, index=False)
    pd.DataFrame(predictions["validation"]).to_csv(validation_predictions, index=False)

    report = run_temporal_label_audit(
        manifest, train_predictions, validation_predictions, tmp_path / "audit"
    )

    assert report["scope"]["included_splits"] == ["train", "validation"]
    assert report["scope"]["windows"] == 18
    assert report["drowsy_trajectory"]["validation"]["probability_2"][
        "late_minus_early"
    ] == pytest.approx(0.4)
    assert (
        report["drowsy_video_consistency"]["validation"]["probability_2"][
            "expected_direction_fraction"
        ]
        == 1.0
    )
    for name in (
        "temporal_label_windows.csv",
        "temporal_label_summary.csv",
        "temporal_label_video_slopes.csv",
        "temporal_label_audit.json",
    ):
        assert (tmp_path / "audit" / name).is_file()
