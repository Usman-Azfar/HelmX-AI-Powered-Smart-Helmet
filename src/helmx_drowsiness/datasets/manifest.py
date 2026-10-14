"""Canonical dataset manifest and subject-disjoint validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "dataset",
    "subject_id",
    "session_id",
    "path",
    "label",
    "split",
}
VALID_SPLITS = {"train", "validation", "test", "external"}


@dataclass(frozen=True, slots=True)
class ManifestSummary:
    rows: int
    datasets: int
    subjects: int
    sessions: int
    missing_paths: int


def read_manifest(path: str | Path, *, check_paths: bool = True) -> pd.DataFrame:
    """Load and validate a canonical CSV manifest.

    A subject may appear in only one split within each dataset. This catches the
    most common and most damaging form of leakage in video drowsiness research.
    """

    manifest_path = Path(path)
    frame = pd.read_csv(manifest_path)
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"manifest is missing columns: {sorted(missing_columns)}")
    if frame.empty:
        raise ValueError("manifest is empty")
    if frame[list(REQUIRED_COLUMNS)].isnull().any().any():
        raise ValueError("required manifest fields cannot be null")

    invalid_splits = set(frame["split"].astype(str)).difference(VALID_SPLITS)
    if invalid_splits:
        raise ValueError(f"invalid split values: {sorted(invalid_splits)}")

    split_counts = frame.groupby(["dataset", "subject_id"])["split"].nunique()
    leaked = split_counts[split_counts > 1]
    if not leaked.empty:
        examples = [f"{dataset}/{subject}" for dataset, subject in leaked.index[:10]]
        raise ValueError(f"subject leakage across splits: {examples}")

    duplicate_keys = frame.duplicated(
        subset=["dataset", "subject_id", "session_id", "path"], keep=False
    )
    if duplicate_keys.any():
        raise ValueError("manifest contains duplicate samples")

    if check_paths:
        base = manifest_path.parent
        missing = [value for value in frame["path"] if not (base / str(value)).exists()]
        if missing:
            raise FileNotFoundError(f"{len(missing)} manifest paths do not exist")
    return frame


def summarize_manifest(frame: pd.DataFrame, *, root: Path | None = None) -> ManifestSummary:
    """Return dataset cardinalities and optional path-availability information."""

    missing_paths = 0
    if root is not None:
        missing_paths = sum(not (root / str(path)).exists() for path in frame["path"])
    return ManifestSummary(
        rows=len(frame),
        datasets=frame["dataset"].nunique(),
        subjects=frame[["dataset", "subject_id"]].drop_duplicates().shape[0],
        sessions=frame[["dataset", "session_id"]].drop_duplicates().shape[0],
        missing_paths=missing_paths,
    )


def validate_label_space(
    frame: pd.DataFrame, num_classes: int, *, require_all: bool = False
) -> None:
    """Reject non-integer/out-of-range labels and optionally missing classes."""

    numeric = pd.to_numeric(frame["label"], errors="coerce")
    if numeric.isna().any() or (numeric != numeric.round()).any():
        raise ValueError("manifest labels must be integers")
    observed = set(numeric.astype(int))
    expected = set(range(num_classes))
    if not observed.issubset(expected):
        raise ValueError(f"manifest labels outside 0..{num_classes - 1}: {sorted(observed)}")
    if require_all and observed != expected:
        raise ValueError(f"split is missing class labels: {sorted(expected - observed)}")
