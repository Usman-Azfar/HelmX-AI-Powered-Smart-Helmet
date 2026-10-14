"""Development-only failure audit for paired multi-fold screening predictions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from helmx_drowsiness.evaluation.metrics import classification_metrics
from helmx_drowsiness.evaluation.multifold_screen import (
    KEY_COLUMNS,
    _pair_predictions,
    _probabilities,
    _read_predictions,
)
from helmx_drowsiness.evaluation.report import detailed_classification_report
from helmx_drowsiness.training.provenance import sha256_file, write_json

LABEL_NAMES = ("alert", "low_vigilance", "drowsy")


def run_multifold_failure_audit(
    root: str | Path,
    destination: str | Path,
    *,
    candidate_directory: str = "ordinal",
    folds: tuple[int, ...] = (2, 3, 4, 5),
) -> dict[str, Any]:
    """Audit paired OOF predictions without accessing any held-out or external data."""

    if not candidate_directory or Path(candidate_directory).name != candidate_directory:
        raise ValueError("candidate_directory must be one non-empty directory name")
    candidate_objective = {
        "ordinal": "cumulative_ordinal",
        "hybrid": "categorical_with_ordinal_regularization",
    }.get(candidate_directory, candidate_directory)

    source_root = Path(root)
    output = Path(destination)
    output.mkdir(parents=True, exist_ok=True)
    paired_folds: list[pd.DataFrame] = []
    sources: list[dict[str, Any]] = []
    for fold in folds:
        baseline_path = (
            source_root
            / f"d{fold}"
            / "categorical"
            / "seed-13"
            / "validation_video_predictions.csv"
        )
        candidate_path = (
            source_root
            / f"d{fold}"
            / candidate_directory
            / "seed-13"
            / "validation_video_predictions.csv"
        )
        paired = _pair_predictions(
            _read_predictions(baseline_path, fold),
            _read_predictions(candidate_path, fold),
            fold,
        )
        paired_folds.append(_add_audit_columns(paired, candidate_directory))
        sources.extend(
            [
                {
                    "fold": fold,
                    "model": "categorical",
                    "path": str(baseline_path),
                    "sha256": sha256_file(baseline_path),
                },
                {
                    "fold": fold,
                    "model": candidate_directory,
                    "path": str(candidate_path),
                    "sha256": sha256_file(candidate_path),
                },
            ]
        )
    pooled = pd.concat(paired_folds, ignore_index=True)
    _write_csv(pooled, output / "paired_video_changes.csv")

    subject_influence = _subject_influence(pooled, candidate_directory)
    _write_csv(subject_influence, output / "subject_influence.csv")
    scopes = {"pooled": pooled}
    scopes.update({f"d{fold}": pooled.loc[pooled["fold"] == fold].copy() for fold in folds})
    scope_reports = {
        name: _scope_report(frame, candidate_directory) for name, frame in scopes.items()
    }
    pooled_report = scope_reports["pooled"]
    baseline_recall = pooled_report["categorical"]["detailed"]["per_class"]
    candidate_recall = pooled_report[candidate_directory]["detailed"]["per_class"]
    recall_changes = {
        label: float(candidate_recall[label]["recall"] - baseline_recall[label]["recall"])
        for label in LABEL_NAMES
    }
    contribution_column = f"contribution_to_{candidate_directory}_difference"
    most_harmful = subject_influence.nsmallest(5, contribution_column)
    most_helpful = subject_influence.nlargest(5, contribution_column)
    report: dict[str, Any] = {
        "schema_version": 1,
        "scope": {
            "policy": "development folds 2-5 only; fold 1 and DROZY prohibited",
            "subjects": int(pooled["cluster_id"].nunique()),
            "videos": len(pooled),
            "folds": list(folds),
        },
        "method": {
            "pairing_keys": KEY_COLUMNS,
            "models": {"baseline": "categorical", "candidate": candidate_objective},
            "influence": (
                f"full pooled {candidate_directory}-minus-categorical macro-F1 difference minus "
                "the difference after leaving one subject out"
            ),
        },
        "sources": sources,
        "scopes": scope_reports,
        "pooled_recall_changes": recall_changes,
        "subject_influence": {
            f"most_harmful_to_{candidate_directory}": most_harmful.to_dict("records"),
            f"most_helpful_to_{candidate_directory}": most_helpful.to_dict("records"),
            "maximum_absolute_contribution": float(
                subject_influence[contribution_column].abs().max()
            ),
        },
        "findings": {
            "weakest_pooled_recall_change": min(recall_changes, key=recall_changes.__getitem__),
            "largest_pooled_recall_gain": max(recall_changes, key=recall_changes.__getitem__),
            "d3_macro_f1_difference": scope_reports["d3"]["macro_f1_difference"],
            "screening_outcome": f"reject {candidate_objective} objective",
            "authorization": (
                "no five-seed confirmation and no DROZY access; a new candidate requires a "
                "development-only one-factor amendment"
            ),
        },
    }
    write_json(output / "failure_audit.json", report)
    return report


def _add_audit_columns(frame: pd.DataFrame, candidate_name: str = "ordinal") -> pd.DataFrame:
    audited = frame.copy()
    baseline_scores = _probabilities(audited, "baseline")
    candidate_scores = _probabilities(audited, "candidate")
    labels = audited["label_baseline"].to_numpy(dtype=np.int64)
    row_indices = np.arange(len(audited), dtype=np.int64)
    audited["cluster_id"] = (
        "d" + audited["fold"].astype(str) + "/" + audited["subject_id"].astype(str)
    )
    audited["baseline_prediction"] = baseline_scores.argmax(axis=1)
    audited[f"{candidate_name}_prediction"] = candidate_scores.argmax(axis=1)
    audited["baseline_correct"] = audited["baseline_prediction"].to_numpy() == labels
    audited[f"{candidate_name}_correct"] = (
        audited[f"{candidate_name}_prediction"].to_numpy() == labels
    )
    audited["baseline_confidence"] = baseline_scores.max(axis=1)
    audited[f"{candidate_name}_confidence"] = candidate_scores.max(axis=1)
    audited["baseline_true_class_probability"] = baseline_scores[row_indices, labels]
    audited[f"{candidate_name}_true_class_probability"] = candidate_scores[row_indices, labels]
    audited["true_class_probability_change"] = (
        audited[f"{candidate_name}_true_class_probability"]
        - audited["baseline_true_class_probability"]
    )
    audited["prediction_changed"] = (
        audited["baseline_prediction"] != audited[f"{candidate_name}_prediction"]
    )
    audited["change_outcome"] = np.select(
        [
            audited["baseline_correct"] & audited[f"{candidate_name}_correct"],
            audited["baseline_correct"] & ~audited[f"{candidate_name}_correct"],
            ~audited["baseline_correct"] & audited[f"{candidate_name}_correct"],
        ],
        ["both_correct", "categorical_only_correct", f"{candidate_name}_only_correct"],
        default="both_wrong",
    )
    return audited


def _scope_report(frame: pd.DataFrame, candidate_name: str = "ordinal") -> dict[str, Any]:
    labels = frame["label_baseline"].to_numpy(dtype=np.int64)
    baseline = _model_report(labels, _probabilities(frame, "baseline"))
    candidate = _model_report(labels, _probabilities(frame, "candidate"))
    outcome_counts = frame["change_outcome"].value_counts()
    return {
        "subjects": int(frame["cluster_id"].nunique()),
        "videos": len(frame),
        "categorical": baseline,
        candidate_name: candidate,
        "macro_f1_difference": candidate["macro_f1"] - baseline["macro_f1"],
        "prediction_agreement": float(
            (frame["baseline_prediction"] == frame[f"{candidate_name}_prediction"]).mean()
        ),
        "prediction_changes": {
            name: int(outcome_counts.get(name, 0))
            for name in (
                "both_correct",
                "categorical_only_correct",
                f"{candidate_name}_only_correct",
                "both_wrong",
            )
        },
    }


def _model_report(labels: NDArray[np.int64], scores: NDArray[np.float64]) -> dict[str, Any]:
    metrics = classification_metrics(labels, scores).to_dict()
    predictions = scores.argmax(axis=1)
    correct = predictions == labels
    return {
        **metrics,
        "mean_confidence": float(scores.max(axis=1).mean()),
        "mean_confidence_correct": _safe_mean(scores.max(axis=1)[correct]),
        "mean_confidence_incorrect": _safe_mean(scores.max(axis=1)[~correct]),
        "detailed": detailed_classification_report(labels, scores, LABEL_NAMES),
    }


def _subject_influence(frame: pd.DataFrame, candidate_name: str = "ordinal") -> pd.DataFrame:
    full_difference = _macro_f1_difference(frame)
    rows: list[dict[str, Any]] = []
    for cluster_id, subject in frame.groupby("cluster_id", sort=True, observed=True):
        remaining = frame.drop(subject.index)
        leave_out_difference = _macro_f1_difference(remaining)
        rows.append(
            {
                "cluster_id": cluster_id,
                "fold": int(subject["fold"].iloc[0]),
                "subject_id": str(subject["subject_id"].iloc[0]),
                "videos": len(subject),
                "categorical_accuracy": float(subject["baseline_correct"].mean()),
                f"{candidate_name}_accuracy": float(subject[f"{candidate_name}_correct"].mean()),
                "accuracy_difference": float(
                    subject[f"{candidate_name}_correct"].mean() - subject["baseline_correct"].mean()
                ),
                "full_macro_f1_difference": full_difference,
                "leave_out_macro_f1_difference": leave_out_difference,
                f"contribution_to_{candidate_name}_difference": (
                    full_difference - leave_out_difference
                ),
            }
        )
    return pd.DataFrame(rows)


def _macro_f1_difference(frame: pd.DataFrame) -> float:
    labels = frame["label_baseline"].to_numpy(dtype=np.int64)
    baseline = classification_metrics(labels, _probabilities(frame, "baseline")).macro_f1
    candidate = classification_metrics(labels, _probabilities(frame, "candidate")).macro_f1
    return candidate - baseline


def _safe_mean(values: NDArray[np.float64]) -> float:
    return float(values.mean()) if len(values) else float("nan")


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)
