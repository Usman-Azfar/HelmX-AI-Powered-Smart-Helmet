from pathlib import Path

import pandas as pd

from helmx_drowsiness.evaluation.multifold_screen import evaluate_multifold_screen


def test_multifold_screen_pairs_videos_and_applies_frozen_gates(tmp_path: Path) -> None:
    root = tmp_path / "screen"
    for fold in (2, 3, 4, 5):
        rows = []
        for subject in ("a", "b"):
            for label in (0, 1, 2):
                rows.append(
                    {
                        "dataset": "uta_rldd",
                        "subject_id": f"fold{fold}_{subject}",
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

    output = tmp_path / "report.json"
    report = evaluate_multifold_screen(root, output, resamples=100, seed=7)

    assert output.is_file()
    assert report["pooled"]["videos"] == 24
    assert report["pooled"]["subjects"] == 8
    assert report["screening_passed"] is True
    assert report["paired_subject_bootstrap_macro_f1_difference"]["lower"] > 0


def test_multifold_screen_accepts_explicit_candidate_directory(tmp_path: Path) -> None:
    root = tmp_path / "screen"
    for fold in (2, 3, 4, 5):
        rows = [
            {
                "dataset": "uta_rldd",
                "subject_id": f"fold{fold}_a",
                "session_id": f"class{label}",
                "label": label,
                "prediction": label,
                "windows": 2,
                "fold": fold,
                "probability_0": 0.8 if label == 0 else 0.1,
                "probability_1": 0.8 if label == 1 else 0.1,
                "probability_2": 0.8 if label == 2 else 0.1,
            }
            for label in (0, 1, 2)
        ]
        for model in ("categorical", "hybrid"):
            model_dir = root / f"d{fold}" / model / "seed-13"
            model_dir.mkdir(parents=True)
            pd.DataFrame(rows).to_csv(model_dir / "validation_video_predictions.csv", index=False)

    output = tmp_path / "hybrid-report.json"
    report = evaluate_multifold_screen(
        root, output, candidate_directory="hybrid", resamples=100, seed=7
    )

    assert report["candidate_directory"] == "hybrid"
    assert all("hybrid" in source["path"] for source in report["sources"][1::2])
