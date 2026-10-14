"""Tercile-based loss-weighting for video-level-labeled temporal windows.

UTA-RLDD assigns one label to an entire ~10-minute recording even though the
temporal-label audit (see ``docs/RESEARCH_PROTOCOL.md``) found window-level macro-F1
rises monotonically from the early to the late third of drowsy clips (0.36634 ->
0.40005 -> 0.44763 on fold-2), evidence that early windows in a drowsy-labelled video
frequently still look alert. Relabeling those windows outright would be wrong for the
clips that are drowsy throughout (the audit found only 5-10 of 12 drowsy videos show
the expected late-greater-than-early drift), so instead this module down-weights their
contribution to the classification loss according to position within the clip, using
the same tercile split already used for video-bag window selection in
``datasets.sequences.VideoBagDataset``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_TERCILE_WEIGHTS: tuple[float, float, float] = (0.5, 0.75, 1.0)
PERCLOS_FEATURE_INDEX = 2

REQUIRED_COLUMNS = {"subject_id", "session_id", "label", "start_seconds", "end_seconds"}


def tercile_weight(
    progress: float, weights: tuple[float, float, float] = DEFAULT_TERCILE_WEIGHTS
) -> float:
    """Map a clip-progress fraction in [0, 1] to its tercile confidence weight."""

    if progress <= 1.0 / 3.0:
        return weights[0]
    if progress <= 2.0 / 3.0:
        return weights[1]
    return weights[2]


def add_label_confidence(
    frame: pd.DataFrame,
    *,
    down_weighted_label: int,
    tercile_weights: tuple[float, float, float] = DEFAULT_TERCILE_WEIGHTS,
) -> pd.DataFrame:
    """Return a copy of ``frame`` with a ``label_confidence`` column added.

    Windows belonging to a video whose label equals ``down_weighted_label`` are
    weighted by their position within that video (early/middle/late thirds). Every
    other window keeps full confidence (1.0), since the audit evidence only supports
    down-weighting the down-weighted class.
    """

    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"manifest is missing columns for label confidence: {sorted(missing)}")
    if len(tercile_weights) != 3:
        raise ValueError("tercile_weights must have exactly three entries")

    result = frame.copy()
    result["label_confidence"] = 1.0
    for (_subject, _session), group in result.groupby(["subject_id", "session_id"], sort=False):
        if int(group["label"].iloc[0]) != down_weighted_label:
            continue
        video_start = float(group["start_seconds"].min())
        video_end = float(group["end_seconds"].max())
        span = max(video_end - video_start, 1e-6)
        midpoint = (group["start_seconds"] + group["end_seconds"]) / 2.0
        progress = (midpoint - video_start) / span
        weight = progress.apply(lambda value: tercile_weight(value, tercile_weights))
        result.loc[group.index, "label_confidence"] = weight
    return result


def compute_drift_flags(
    frame: pd.DataFrame,
    root: str | Path,
    *,
    down_weighted_label: int,
    perclos_feature_index: int = PERCLOS_FEATURE_INDEX,
    minimum_drift: float = 0.0,
) -> dict[tuple[str, str], bool]:
    """Flag each ``down_weighted_label`` video by whether it shows late>early PERCLOS drift.

    The temporal-label audit found only 5-10 of 12 drowsy videos show the expected
    late-greater-than-early physiological drift; the rest are drowsy throughout. This
    measures that per-video, from the already-cached causal PERCLOS feature, so a
    uniform blanket assumption is not applied to videos it does not describe.
    """

    root_path = Path(root)
    flags: dict[tuple[str, str], bool] = {}
    for (subject, session), group in frame.groupby(["subject_id", "session_id"], sort=False):
        if int(group["label"].iloc[0]) != down_weighted_label:
            continue
        ordered = group.sort_values("start_seconds")
        video_start = float(ordered["start_seconds"].min())
        video_end = float(ordered["end_seconds"].max())
        span = max(video_end - video_start, 1e-6)
        early_values: list[float] = []
        late_values: list[float] = []
        for _, row in ordered.iterrows():
            midpoint = (float(row["start_seconds"]) + float(row["end_seconds"])) / 2.0
            progress = (midpoint - video_start) / span
            with np.load(root_path / str(row["path"]), allow_pickle=False) as sample:
                value = float(sample["physiology"][:, perclos_feature_index].mean())
            if progress <= 1.0 / 3.0:
                early_values.append(value)
            elif progress > 2.0 / 3.0:
                late_values.append(value)
        drift = (
            (sum(late_values) / len(late_values)) - (sum(early_values) / len(early_values))
            if early_values and late_values
            else 0.0
        )
        flags[(str(subject), str(session))] = drift > minimum_drift
    return flags


def add_adaptive_label_confidence(
    frame: pd.DataFrame,
    root: str | Path,
    *,
    down_weighted_label: int,
    tercile_weights: tuple[float, float, float] = DEFAULT_TERCILE_WEIGHTS,
    minimum_drift: float = 0.0,
    perclos_feature_index: int = PERCLOS_FEATURE_INDEX,
) -> pd.DataFrame:
    """Tercile-weight only the ``down_weighted_label`` videos that show late>early drift.

    Videos of that class without measured drift keep full label confidence: their
    early windows are not assumed to be mislabeled just because the class as a whole
    sometimes exhibits that pattern.
    """

    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"manifest is missing columns for label confidence: {sorted(missing)}")
    if len(tercile_weights) != 3:
        raise ValueError("tercile_weights must have exactly three entries")

    flags = compute_drift_flags(
        frame,
        root,
        down_weighted_label=down_weighted_label,
        perclos_feature_index=perclos_feature_index,
        minimum_drift=minimum_drift,
    )
    result = frame.copy()
    result["label_confidence"] = 1.0
    for (subject, session), group in result.groupby(["subject_id", "session_id"], sort=False):
        if not flags.get((str(subject), str(session)), False):
            continue
        video_start = float(group["start_seconds"].min())
        video_end = float(group["end_seconds"].max())
        span = max(video_end - video_start, 1e-6)
        midpoint = (group["start_seconds"] + group["end_seconds"]) / 2.0
        progress = (midpoint - video_start) / span
        weight = progress.apply(lambda value: tercile_weight(value, tercile_weights))
        result.loc[group.index, "label_confidence"] = weight
    return result
