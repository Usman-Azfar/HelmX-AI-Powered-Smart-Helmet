"""Pre-training manifest and physiology-feature sanity checks.

Two checks that must run once real UTA-RLDD preprocessing produces a manifest, before
spending compute on the full 5-fold x 5-seed study:

1. Window-level class balance. UTA-RLDD is balanced by subject and video (one video per
   class per subject), but window extraction is duration-proportional (one window per
   ``window_stride`` seconds), so window counts are not guaranteed balanced even when
   subject/video counts are. See ``docs/RESEARCH_PROTOCOL.md``.
2. Physiology feature distributions, split into windows drawn from early in a video versus
   later, since the causal rolling extractor's history is still filling during the first
   part of every recording (see ``features.temporal.TemporalFeatureExtractor``).

Neither check decides anything automatically - inspect the output and decide by hand
whether class weighting or a feature-definition fix is actually warranted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from helmx_drowsiness.features.temporal import TemporalFeatureExtractor

PERCENTILES = (1, 5, 50, 95, 99)


def manifest_class_balance(frame: pd.DataFrame) -> dict[str, Any]:
    """Per-split, per-class subject/video/window counts and windows-per-subject spread.

    Compare each class's ``window_proportion`` against its share of subjects/videos: a
    close match means window extraction did not introduce meaningful imbalance; a large gap
    means it did, and the primary classification loss may need class weighting (weighted
    CE or a weighted sampler - not both) per the protocol in docs/RESEARCH_PROTOCOL.md.
    """

    result: dict[str, Any] = {}
    for split, split_frame in frame.groupby("split"):
        by_class: dict[str, Any] = {}
        total_windows = len(split_frame)
        for label, class_frame in split_frame.groupby("label"):
            videos = class_frame[["subject_id", "session_id"]].drop_duplicates().shape[0]
            windows = len(class_frame)
            by_class[str(label)] = {
                "subjects": int(class_frame["subject_id"].nunique()),
                "videos": int(videos),
                "windows": int(windows),
                "window_proportion": windows / total_windows if total_windows else float("nan"),
            }
        per_subject = split_frame.groupby("subject_id").size()
        result[str(split)] = {
            "by_class": by_class,
            "windows_per_subject": {
                "mean": float(per_subject.mean()),
                "std": float(per_subject.std(ddof=1)) if len(per_subject) > 1 else 0.0,
                "min": int(per_subject.min()),
                "max": int(per_subject.max()),
            },
        }
    return result


def physiology_feature_report(
    frame: pd.DataFrame, root: str | Path, *, early_seconds: float = 60.0
) -> pd.DataFrame:
    """Per-feature min/p1/p5/median/p95/p99/max and NaN+Inf fraction, split early vs. later.

    ``early_seconds`` buckets windows by their manifest ``start_seconds`` (defaulting a
    window with no such column to "early", the conservative choice). A blown-out early-only
    ``blink_rate_per_minute`` tail is the signature of the divide-by-tiny-elapsed-duration
    issue that ``TemporalFeatureExtractor.minimum_elapsed_seconds`` guards against; if it
    still appears, the floor needs to be raised, not just the training data trusted as-is.
    """

    root_path = Path(root)
    buckets: dict[str, list[np.ndarray]] = {"early": [], "later": []}
    has_start = "start_seconds" in frame.columns
    for row in frame.itertuples():
        with np.load(root_path / str(row.path), allow_pickle=False) as sample:
            physiology = np.asarray(sample["physiology"], dtype=np.float64)
        start = float(row.start_seconds) if has_start else 0.0
        buckets["early" if start < early_seconds else "later"].append(physiology)

    rows: list[dict[str, Any]] = []
    for bucket_name, arrays in buckets.items():
        if not arrays:
            continue
        values = np.concatenate(arrays, axis=0)
        for index, name in enumerate(TemporalFeatureExtractor.feature_names):
            column = values[:, index]
            finite = np.isfinite(column)
            finite_column = column[finite]
            row_data: dict[str, Any] = {
                "window_bucket": bucket_name,
                "feature": name,
                "count": int(column.size),
                "nan_inf_fraction": float(1.0 - finite.mean()) if column.size else float("nan"),
            }
            if finite_column.size:
                percentiles = np.percentile(finite_column, PERCENTILES)
                row_data.update(
                    {
                        "min": float(finite_column.min()),
                        "p1": float(percentiles[0]),
                        "p5": float(percentiles[1]),
                        "median": float(percentiles[2]),
                        "p95": float(percentiles[3]),
                        "p99": float(percentiles[4]),
                        "max": float(finite_column.max()),
                    }
                )
            else:
                row_data.update(
                    dict.fromkeys(("min", "p1", "p5", "median", "p95", "p99", "max"), float("nan"))
                )
            rows.append(row_data)
    return pd.DataFrame(rows)
