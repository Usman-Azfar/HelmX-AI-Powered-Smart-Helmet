from pathlib import Path

import pandas as pd

from helmx_drowsiness.datasets.development_folds import build_development_fold_manifests
from helmx_drowsiness.datasets.manifest import read_manifest


def test_development_manifests_exclude_fold_one_and_rotate_validation(tmp_path: Path) -> None:
    rows = []
    for fold in range(1, 6):
        for label in range(3):
            name = f"fold{fold}_{label}.npz"
            (tmp_path / name).write_bytes(b"fixture")
            rows.append(
                {
                    "dataset": "synthetic",
                    "subject_id": f"fold{fold}_subject",
                    "session_id": f"class{label}",
                    "path": name,
                    "label": label,
                    "split": "test" if fold == 1 else "train",
                    "fold": fold,
                }
            )
    source = tmp_path / "source.csv"
    pd.DataFrame(rows).to_csv(source, index=False)

    report = build_development_fold_manifests(source)

    assert set(report["manifests"]) == {"D2", "D3", "D4", "D5"}
    for validation_fold in range(2, 6):
        manifest = read_manifest(tmp_path / f"manifest_development_validation{validation_fold}.csv")
        assert set(manifest["fold"]) == {2, 3, 4, 5}
        assert set(manifest.loc[manifest["split"] == "validation", "fold"]) == {validation_fold}
        assert set(manifest.loc[manifest["split"] == "train", "fold"]) == (
            {2, 3, 4, 5} - {validation_fold}
        )
        assert "test" not in set(manifest["split"])
    assert (tmp_path / "development_fold_manifests.json").is_file()
