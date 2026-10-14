"""Compare a selected model with a failed held-out candidate at video/subject level."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from helmx_drowsiness.evaluation.metrics import classification_metrics
from helmx_drowsiness.evaluation.report import detailed_classification_report
from helmx_drowsiness.training.provenance import sha256_file, write_json

IDENTITY = ["dataset", "subject_id", "session_id", "label"]


def run_failure_audit(
    selected_validation: str | Path,
    selected_test: str | Path,
    candidate_validation: str | Path,
    candidate_test: str | Path,
    destination: str | Path,
) -> dict[str, Any]:
    """Write a reproducible selected-versus-candidate fold-shift audit."""

    sources = {
        "selected_validation": Path(selected_validation),
        "selected_test": Path(selected_test),
        "candidate_validation": Path(candidate_validation),
        "candidate_test": Path(candidate_test),
    }
    frames = {name: _read_predictions(path) for name, path in sources.items()}
    videos = {name: aggregate_video_predictions(frame) for name, frame in frames.items()}
    output = Path(destination)
    output.mkdir(parents=True, exist_ok=True)

    video_rows = []
    for source, frame in videos.items():
        model, split = source.split("_", maxsplit=1)
        tagged = frame.copy()
        tagged.insert(0, "split", split)
        tagged.insert(0, "model", model)
        video_rows.append(tagged)
    all_videos = pd.concat(video_rows, ignore_index=True)
    all_videos.to_csv(output / "video_predictions.csv", index=False)

    subject_rows = []
    for (model, split, subject), group in all_videos.groupby(
        ["model", "split", "subject_id"], sort=True, observed=True
    ):
        subject_rows.append(
            {
                "model": model,
                "split": split,
                "subject_id": subject,
                "videos": len(group),
                "correct_videos": int(group["correct"].sum()),
                "accuracy": float(group["correct"].mean()),
                "mean_confidence": float(group["confidence"].mean()),
            }
        )
    subject_frame = pd.DataFrame(subject_rows)
    subject_frame.to_csv(output / "subject_summary.csv", index=False)

    influence = _influence(videos["candidate_validation"])
    influence.to_csv(output / "candidate_validation_influence.csv", index=False)

    metrics: dict[str, dict[str, Any]] = {
        name: {
            "windows": _metrics(frame),
            "videos": _metrics(videos[name]),
            "video_mean_confidence": float(videos[name]["confidence"].mean()),
            "video_mean_confidence_correct": _safe_group_mean(videos[name], True),
            "video_mean_confidence_incorrect": _safe_group_mean(videos[name], False),
        }
        for name, frame in frames.items()
    }
    comparisons = {
        split: _paired_comparison(videos[f"selected_{split}"], videos[f"candidate_{split}"])
        for split in ("validation", "test")
    }
    subject_influence = influence.loc[influence["unit"] == "subject"]
    most_positive_subject = subject_influence.nlargest(1, "macro_f1_contribution").iloc[0]
    selected_validation_f1 = float(metrics["selected_validation"]["videos"]["macro_f1"])
    candidate_validation_f1 = float(metrics["candidate_validation"]["videos"]["macro_f1"])
    selected_test_f1 = float(metrics["selected_test"]["videos"]["macro_f1"])
    candidate_test_f1 = float(metrics["candidate_test"]["videos"]["macro_f1"])
    report: dict[str, Any] = {
        "method": {
            "video_identity": IDENTITY[:-1],
            "aggregation": (
                "arithmetic mean of log calibrated probabilities, equivalent for argmax to "
                "mean calibrated logits"
            ),
            "influence": "full candidate validation macro-F1 minus leave-group-out macro-F1",
            "prohibition": "descriptive audit only; test results cannot tune another model",
        },
        "sources": {
            name: {"path": str(path), "sha256": sha256_file(path)} for name, path in sources.items()
        },
        "metrics": metrics,
        "paired_comparison": comparisons,
        "fold_shift": {
            model: {
                "video_macro_f1_test_minus_validation": (
                    metrics[f"{model}_test"]["videos"]["macro_f1"]
                    - metrics[f"{model}_validation"]["videos"]["macro_f1"]
                ),
                "video_accuracy_test_minus_validation": (
                    metrics[f"{model}_test"]["videos"]["accuracy"]
                    - metrics[f"{model}_validation"]["videos"]["accuracy"]
                ),
                "video_confidence_test_minus_validation": (
                    metrics[f"{model}_test"]["video_mean_confidence"]
                    - metrics[f"{model}_validation"]["video_mean_confidence"]
                ),
            }
            for model in ("selected", "candidate")
        },
        "candidate_validation_influence": {
            "largest_video_contributions": influence.loc[influence["unit"] == "video"]
            .nlargest(5, "macro_f1_contribution")
            .to_dict("records"),
            "largest_subject_contributions": influence.loc[influence["unit"] == "subject"]
            .nlargest(5, "macro_f1_contribution")
            .to_dict("records"),
            "maximum_absolute_video_contribution": float(
                influence.loc[influence["unit"] == "video", "macro_f1_contribution"].abs().max()
            ),
            "maximum_absolute_subject_contribution": float(
                influence.loc[influence["unit"] == "subject", "macro_f1_contribution"].abs().max()
            ),
        },
        "findings": {
            "candidate_validation_gain_over_selected": (
                candidate_validation_f1 - selected_validation_f1
            ),
            "candidate_test_change_from_selected": candidate_test_f1 - selected_test_f1,
            "most_positive_validation_subject": str(most_positive_subject["identity"]),
            "candidate_validation_macro_f1_without_that_subject": float(
                most_positive_subject["leave_out_macro_f1"]
            ),
            "candidate_still_beats_selected_validation_without_that_subject": bool(
                most_positive_subject["leave_out_macro_f1"] > selected_validation_f1
            ),
            "recommendation": (
                "Retain the quality-gated model; reject MIL promotion. Do not tune on test. "
                "Require multi-fold development robustness for any new frozen hypothesis."
            ),
        },
    }
    write_json(output / "failure_audit.json", report)
    return report


def aggregate_video_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    """Geometric-pool calibrated probabilities into one auditable row per video."""

    probability_columns = _probability_columns(frame)
    rows: list[dict[str, Any]] = []
    for identity, group in frame.groupby(IDENTITY[:-1], sort=True, observed=True):
        labels = group["label"].unique()
        if len(labels) != 1:
            raise ValueError(f"video has multiple labels: {identity}")
        probabilities = group[probability_columns].to_numpy(dtype=np.float64)
        mean_log_probability = np.log(np.clip(probabilities, 1e-12, 1.0)).mean(axis=0)
        scores = np.exp(mean_log_probability - mean_log_probability.max())
        scores /= scores.sum()
        prediction = int(scores.argmax())
        row = dict(zip(IDENTITY[:-1], identity, strict=True))
        row.update(
            {
                "label": int(labels[0]),
                "prediction": prediction,
                "correct": prediction == int(labels[0]),
                "confidence": float(scores.max()),
                "windows": len(group),
            }
        )
        row.update(
            {
                column: float(value)
                for column, value in zip(probability_columns, scores, strict=True)
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _read_predictions(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = set(IDENTITY) | {"prediction"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"prediction CSV is missing columns: {sorted(missing)}")
    _probability_columns(frame)
    if frame.empty:
        raise ValueError("prediction CSV is empty")
    return frame


def _probability_columns(frame: pd.DataFrame) -> list[str]:
    columns = sorted(
        (column for column in frame if column.startswith("probability_")),
        key=lambda column: int(column.rsplit("_", maxsplit=1)[1]),
    )
    if len(columns) < 2:
        raise ValueError("prediction CSV must contain at least two probability columns")
    return columns


def _metrics(frame: pd.DataFrame) -> dict[str, Any]:
    probability_columns = _probability_columns(frame)
    labels = frame["label"].to_numpy(dtype=np.int64)
    probabilities = frame[probability_columns].to_numpy(dtype=np.float64)
    return {
        **classification_metrics(labels, probabilities).to_dict(),
        "detailed": detailed_classification_report(
            labels, probabilities, tuple(str(index) for index in range(len(probability_columns)))
        ),
    }


def _safe_group_mean(frame: pd.DataFrame, correct: bool) -> float:
    values = frame.loc[frame["correct"] == correct, "confidence"]
    return float(values.mean()) if len(values) else math.nan


def _paired_comparison(selected: pd.DataFrame, candidate: pd.DataFrame) -> dict[str, Any]:
    joined = selected.merge(candidate, on=IDENTITY, suffixes=("_selected", "_candidate"))
    if len(joined) != len(selected) or len(joined) != len(candidate):
        raise ValueError("selected and candidate video identities do not match")
    selected_correct = joined["correct_selected"].astype(bool)
    candidate_correct = joined["correct_candidate"].astype(bool)
    return {
        "videos": len(joined),
        "prediction_agreement": float(
            (joined["prediction_selected"] == joined["prediction_candidate"]).mean()
        ),
        "both_correct": int((selected_correct & candidate_correct).sum()),
        "selected_only_correct": int((selected_correct & ~candidate_correct).sum()),
        "candidate_only_correct": int((~selected_correct & candidate_correct).sum()),
        "both_wrong": int((~selected_correct & ~candidate_correct).sum()),
    }


def _influence(frame: pd.DataFrame) -> pd.DataFrame:
    probability_columns = _probability_columns(frame)
    full = classification_metrics(
        frame["label"].to_numpy(dtype=np.int64),
        frame[probability_columns].to_numpy(dtype=np.float64),
    ).macro_f1
    rows: list[dict[str, Any]] = []
    units = {
        "video": ["subject_id", "session_id"],
        "subject": ["subject_id"],
    }
    for unit, columns in units.items():
        for identity, group in frame.groupby(columns, sort=True, observed=True):
            identity_tuple = identity if isinstance(identity, tuple) else (identity,)
            remaining = frame.drop(group.index)
            score = classification_metrics(
                remaining["label"].to_numpy(dtype=np.int64),
                remaining[probability_columns].to_numpy(dtype=np.float64),
            ).macro_f1
            rows.append(
                {
                    "unit": unit,
                    "identity": "/".join(map(str, identity_tuple)),
                    "removed_videos": len(group),
                    "full_macro_f1": full,
                    "leave_out_macro_f1": score,
                    "macro_f1_contribution": full - score,
                }
            )
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selected_validation", type=Path)
    parser.add_argument("selected_test", type=Path)
    parser.add_argument("candidate_validation", type=Path)
    parser.add_argument("candidate_test", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    run_failure_audit(
        args.selected_validation,
        args.selected_test,
        args.candidate_validation,
        args.candidate_test,
        args.destination,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
