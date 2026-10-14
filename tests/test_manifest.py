from pathlib import Path

import pandas as pd
import pytest

from helmx_drowsiness.datasets.manifest import read_manifest, validate_label_space


def write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def test_subject_leakage_is_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    write_manifest(
        manifest,
        [
            {
                "dataset": "demo",
                "subject_id": "s1",
                "session_id": "a",
                "path": "a.mp4",
                "label": 0,
                "split": "train",
            },
            {
                "dataset": "demo",
                "subject_id": "s1",
                "session_id": "b",
                "path": "b.mp4",
                "label": 2,
                "split": "test",
            },
        ],
    )
    with pytest.raises(ValueError, match="subject leakage"):
        read_manifest(manifest, check_paths=False)


def test_label_space_rejects_missing_and_fractional_classes() -> None:
    with pytest.raises(ValueError, match="missing class"):
        validate_label_space(pd.DataFrame({"label": [0, 1]}), 3, require_all=True)
    with pytest.raises(ValueError, match="integers"):
        validate_label_space(pd.DataFrame({"label": [0, 1.5, 2]}), 3)
