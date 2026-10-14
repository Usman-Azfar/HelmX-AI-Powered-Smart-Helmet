from pathlib import Path

import pandas as pd

from helmx_drowsiness.evaluation.multifold_failure_audit import run_multifold_failure_audit


def test_multifold_failure_audit_writes_paired_and_subject_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "screen"
    for fold in (2, 3, 4, 5):
        rows = []
        for subject in ("a", "b"):
            for label in (0, 1, 2):
                rows.append(
                    {
                        "dataset": "uta_rldd",
                        "subject_id": f"subject_{subject}",
                        "session_id": f"class{label}",
                        "label": label,
                        "prediction": label,
                        "windows": 2,
                        "fold": fold,
                        "probability_0": 0.8 if label == 0 else 0.1,
                        "probability_1": 0.8 if label == 1 else 0.1,
                        "probability_2": 0.8 if label == 2 else 0.1,
                    }
                )
        candidate = pd.DataFrame(rows)
        baseline = candidate.copy()
        baseline[["probability_0", "probability_1"]] = baseline[
            ["probability_1", "probability_0"]
        ].to_numpy()
        baseline_dir = root / f"d{fold}" / "categorical" / "seed-13"
        candidate_dir = root / f"d{fold}" / "ordinal" / "seed-13"
        baseline_dir.mkdir(parents=True)
        candidate_dir.mkdir(parents=True)
        baseline.to_csv(baseline_dir / "validation_video_predictions.csv", index=False)
        candidate.to_csv(candidate_dir / "validation_video_predictions.csv", index=False)
        hybrid_dir = root / f"d{fold}" / "hybrid" / "seed-13"
        hybrid_dir.mkdir(parents=True)
        candidate.to_csv(hybrid_dir / "validation_video_predictions.csv", index=False)

    output = tmp_path / "audit"
    report = run_multifold_failure_audit(root, output)

    assert report["scope"] == {
        "policy": "development folds 2-5 only; fold 1 and DROZY prohibited",
        "subjects": 8,
        "videos": 24,
        "folds": [2, 3, 4, 5],
    }
    assert report["scopes"]["pooled"]["macro_f1_difference"] > 0
    assert len(report["subject_influence"]["most_harmful_to_ordinal"]) == 5
    assert (output / "failure_audit.json").is_file()
    assert len(pd.read_csv(output / "paired_video_changes.csv")) == 24
    assert len(pd.read_csv(output / "subject_influence.csv")) == 8

    hybrid_output = tmp_path / "hybrid-audit"
    hybrid = run_multifold_failure_audit(root, hybrid_output, candidate_directory="hybrid")
    assert hybrid["method"]["models"]["candidate"] == ("categorical_with_ordinal_regularization")
    assert "hybrid" in hybrid["scopes"]["pooled"]
    assert "most_harmful_to_hybrid" in hybrid["subject_influence"]
