from pathlib import Path

import pandas as pd

from helmx_drowsiness.evaluation.failure_audit import (
    aggregate_video_predictions,
    run_failure_audit,
)


def _predictions(selected: bool) -> pd.DataFrame:
    rows = []
    for subject, label in (("s0a", 0), ("s0b", 0), ("s1a", 1), ("s1b", 1)):
        for window in range(2):
            correct_probability = 0.8 if selected else 0.2
            probability_0 = correct_probability if label == 0 else 1 - correct_probability
            rows.append(
                {
                    "dataset": "synthetic",
                    "subject_id": subject,
                    "session_id": f"video_{subject}",
                    "label": label,
                    "prediction": int(probability_0 < 0.5),
                    "probability_0": probability_0,
                    "probability_1": 1 - probability_0,
                    "start_seconds": float(window),
                }
            )
    return pd.DataFrame(rows)


def test_failure_audit_writes_video_subject_and_influence_artifacts(tmp_path: Path) -> None:
    selected = _predictions(True)
    candidate = _predictions(False)
    paths = []
    for name, frame in (
        ("selected_validation", selected),
        ("selected_test", selected),
        ("candidate_validation", candidate),
        ("candidate_test", candidate),
    ):
        path = tmp_path / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths.append(path)

    report = run_failure_audit(*paths, tmp_path / "audit")

    assert report["metrics"]["selected_validation"]["videos"]["macro_f1"] == 1.0
    assert report["metrics"]["candidate_validation"]["videos"]["macro_f1"] == 0.0
    assert (tmp_path / "audit" / "failure_audit.json").is_file()
    assert (tmp_path / "audit" / "video_predictions.csv").is_file()
    assert (tmp_path / "audit" / "subject_summary.csv").is_file()
    assert (tmp_path / "audit" / "candidate_validation_influence.csv").is_file()


def test_video_aggregation_uses_all_windows() -> None:
    videos = aggregate_video_predictions(_predictions(True))
    assert len(videos) == 4
    assert videos["windows"].tolist() == [2, 2, 2, 2]
    assert videos["correct"].all()
