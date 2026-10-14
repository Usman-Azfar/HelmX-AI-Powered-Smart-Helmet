from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from helmx_drowsiness.evaluation.baseline_failure_audit import run_baseline_failure_audit


def test_baseline_failure_audit_uses_only_development_validation_rows(tmp_path: Path) -> None:
    screen = tmp_path / "screen"
    manifests = tmp_path / "processed"
    manifests.mkdir()
    for fold in (2, 3, 4, 5):
        prediction_rows = []
        manifest_rows = []
        for subject_index, subject in enumerate(("a", "b")):
            for label in (0, 1, 2):
                session = f"class{label}"
                sample = f"fold{fold}_{subject}_{label}.npz"
                quality = 0.9 if subject == "a" else 0.2
                np.savez(
                    manifests / sample,
                    quality=np.full((2, 2), quality, dtype=np.float32),
                )
                manifest_rows.append(
                    {
                        "dataset": "uta_rldd",
                        "subject_id": f"fold{fold}_{subject}",
                        "session_id": session,
                        "path": sample,
                        "label": label,
                        "split": "validation",
                        "fold": fold,
                    }
                )
                prediction = label if subject_index == 0 else (label + 1) % 3
                probabilities = np.full(3, 0.1)
                probabilities[prediction] = 0.8
                prediction_rows.append(
                    {
                        "dataset": "uta_rldd",
                        "subject_id": f"fold{fold}_{subject}",
                        "session_id": session,
                        "label": label,
                        "prediction": prediction,
                        "windows": 1,
                        "fold": fold,
                        **{
                            f"probability_{index}": value
                            for index, value in enumerate(probabilities)
                        },
                    }
                )
        pd.DataFrame(manifest_rows).to_csv(
            manifests / f"manifest_development_validation{fold}.csv", index=False
        )
        prediction_dir = screen / f"d{fold}" / "categorical" / "seed-13"
        prediction_dir.mkdir(parents=True)
        pd.DataFrame(prediction_rows).to_csv(
            prediction_dir / "validation_video_predictions.csv", index=False
        )

    output = tmp_path / "audit"
    report = run_baseline_failure_audit(screen, manifests, output)

    assert report["scope"]["subjects"] == 8
    assert report["scope"]["videos"] == 24
    assert report["quality"]["mean_monitoring_quality_incorrect"] == pytest.approx(0.2)
    assert report["quality"]["mean_monitoring_quality_correct"] == pytest.approx(0.9)
    assert report["subjects"]["subjects_with_no_correct_videos"] == 4
    assert report["confidence"]["high_confidence_errors"] == 12
    assert (output / "baseline_failure_audit.json").is_file()
    assert len(pd.read_csv(output / "video_diagnostics.csv")) == 24
    assert len(pd.read_csv(output / "subject_diagnostics.csv")) == 8


def test_baseline_failure_audit_rejects_non_development_scope(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="restricted to development folds 2-5"):
        run_baseline_failure_audit(tmp_path, tmp_path, tmp_path / "output", folds=(1, 2, 3, 4))
