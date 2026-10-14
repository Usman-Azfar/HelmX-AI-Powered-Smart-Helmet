"""Build fold-1-free UTA development manifests for rotations D2-D5."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from helmx_drowsiness.datasets.manifest import read_manifest, validate_label_space
from helmx_drowsiness.training.provenance import sha256_file, write_json

DEVELOPMENT_FOLDS = (2, 3, 4, 5)


def build_development_fold_manifests(source: str | Path) -> dict[str, Any]:
    """Derive four atomic train/validation manifests while excluding fold 1 entirely."""

    source_path = Path(source)
    frame = read_manifest(source_path, check_paths=False)
    if "fold" not in frame:
        raise ValueError("source manifest must contain a fold column")
    numeric_folds = pd.to_numeric(frame["fold"], errors="raise").astype(int)
    unexpected = sorted(set(numeric_folds) - set(range(1, 6)))
    if unexpected:
        raise ValueError(f"source manifest contains unexpected folds: {unexpected}")
    development = frame.loc[numeric_folds.isin(DEVELOPMENT_FOLDS)].copy()
    development["fold"] = numeric_folds.loc[development.index]
    if development.empty:
        raise ValueError("source manifest contains no folds 2-5")
    missing_paths = [
        str(value)
        for value in development["path"]
        if not (source_path.parent / str(value)).is_file()
    ]
    if missing_paths:
        raise FileNotFoundError(f"{len(missing_paths)} development paths do not exist")

    report: dict[str, Any] = {
        "source_manifest": str(source_path),
        "source_sha256": sha256_file(source_path),
        "excluded_folds": [1],
        "development_folds": list(DEVELOPMENT_FOLDS),
        "manifests": {},
    }
    for validation_fold in DEVELOPMENT_FOLDS:
        derived = development.copy()
        derived["split"] = "train"
        derived.loc[derived["fold"] == validation_fold, "split"] = "validation"
        train = derived.loc[derived["split"] == "train"]
        validation = derived.loc[derived["split"] == "validation"]
        validate_label_space(train, 3, require_all=True)
        validate_label_space(validation, 3, require_all=True)
        destination = source_path.parent / f"manifest_development_validation{validation_fold}.csv"
        temporary = destination.with_suffix(".csv.tmp")
        derived.to_csv(temporary, index=False)
        temporary.replace(destination)
        verified = read_manifest(destination, check_paths=True)
        if 1 in set(verified["fold"]):
            raise AssertionError("fold 1 leaked into a development manifest")
        report["manifests"][f"D{validation_fold}"] = {
            "path": str(destination),
            "sha256": sha256_file(destination),
            "rows": len(verified),
            "subjects": int(verified["subject_id"].nunique()),
            "videos": int(verified[["subject_id", "session_id"]].drop_duplicates().shape[0]),
            "train_rows": int((verified["split"] == "train").sum()),
            "validation_rows": int((verified["split"] == "validation").sum()),
            "train_subjects": int(train["subject_id"].nunique()),
            "validation_subjects": int(validation["subject_id"].nunique()),
            "train_class_rows": {
                str(label): int(count)
                for label, count in train["label"].value_counts().sort_index().items()
            },
            "validation_class_rows": {
                str(label): int(count)
                for label, count in validation["label"].value_counts().sort_index().items()
            },
        }
    write_json(source_path.parent / "development_fold_manifests.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_manifest", type=Path)
    args = parser.parse_args()
    build_development_fold_manifests(args.source_manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
