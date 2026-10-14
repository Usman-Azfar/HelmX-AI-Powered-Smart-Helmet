from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from helmx_drowsiness.evaluation.uta_pilot import (
    physiology_scaling_outlier_report,
    summarize_boundary_samples,
)
from helmx_drowsiness.features.temporal import PersonalBaseline, TemporalFeatureExtractor


def test_boundary_summary_measures_change_across_five_seconds() -> None:
    frame = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "blink_rate_per_minute": rate,
                "subject_id": "fold2_13",
                "session_id": "0",
            }
            for timestamp, rate in ((4.1, 10.0), (4.9, 12.0), (5.1, 12.5), (5.9, 13.0))
        ]
    )

    report = summarize_boundary_samples(frame)

    assert report["nan_inf_fraction"] == 0.0
    assert report["seconds_4_to_5"]["max"] == 12.0
    assert report["seconds_5_to_6"]["max"] == 13.0
    assert report["max_change_at_boundary"] == pytest.approx(1.0)


def test_scaling_report_fits_train_only_and_attributes_mar_outlier(tmp_path: Path) -> None:
    names = TemporalFeatureExtractor.feature_names
    mar_index = names.index("relative_mar")
    for name, mar in (("train.npz", 1.0), ("validation.npz", 100.0)):
        physiology = np.ones((2, len(names)), dtype=np.float32)
        physiology[:, mar_index] = mar
        quality = np.full((2, 2), 0.8, dtype=np.float32)
        np.savez_compressed(tmp_path / name, physiology=physiology, quality=quality)
    frame = pd.DataFrame(
        [
            {
                "path": "train.npz",
                "split": "train",
                "subject_id": "fold3_25",
                "session_id": "0",
                "label": 0,
                "start_seconds": 0.0,
            },
            {
                "path": "validation.npz",
                "split": "validation",
                "subject_id": "fold2_13",
                "session_id": "10",
                "label": 2,
                "start_seconds": 30.0,
            },
        ]
    )
    baselines = {
        "fold2_13": PersonalBaseline(0.3, 0.01, 0.0, 0.0, 0.0),
        "fold3_25": PersonalBaseline(0.3, 0.2, 0.0, 0.0, 0.0),
    }

    report = physiology_scaling_outlier_report(frame, tmp_path, baselines, top_n=1)

    assert report["scaler_observations"] == 2
    assert report["standardized_clip"] == 10.0
    assert all(item["post_clip_abs_max"] <= 10.0 for item in report["per_feature"])
    outlier = report["largest_relative_mar"][0]
    assert outlier["split"] == "validation"
    assert outlier["relative_mar"] == 100.0
    assert outlier["estimated_raw_mar"] == pytest.approx(1.0)
