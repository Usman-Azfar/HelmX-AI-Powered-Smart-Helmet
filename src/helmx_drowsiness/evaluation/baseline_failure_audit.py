"""Development-only failure audit for the retained categorical baseline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from helmx_drowsiness.datasets.manifest import read_manifest
from helmx_drowsiness.evaluation.metrics import classification_metrics
from helmx_drowsiness.evaluation.multifold_screen import (
    KEY_COLUMNS,
    PROBABILITY_COLUMNS,
    _read_predictions,
)
from helmx_drowsiness.evaluation.report import detailed_classification_report
from helmx_drowsiness.training.provenance import sha256_file, write_json

LABEL_NAMES = ("alert", "low_vigilance", "drowsy")
MINIMUM_QUALITY = 0.35


def run_baseline_failure_audit(
    root: str | Path,
    manifest_directory: str | Path,
    destination: str | Path,
    *,
    folds: tuple[int, ...] = (2, 3, 4, 5),
) -> dict[str, Any]:
    """Audit existing D2-D5 categorical predictions without model inference."""

    if tuple(sorted(folds)) != (2, 3, 4, 5):
        raise ValueError("baseline audit is restricted to development folds 2-5")

    source_root = Path(root)
    manifest_root = Path(manifest_directory)
    output = Path(destination)
    output.mkdir(parents=True, exist_ok=True)
    video_frames: list[pd.DataFrame] = []
    sources: list[dict[str, Any]] = []

    for fold in folds:
        prediction_path = (
            source_root
            / f"d{fold}"
            / "categorical"
            / "seed-13"
            / "validation_video_predictions.csv"
        )
        manifest_path = manifest_root / f"manifest_development_validation{fold}.csv"
        predictions = _read_predictions(prediction_path, fold)
        quality = _validation_video_quality(manifest_path, fold)
        videos = predictions.merge(quality, on=KEY_COLUMNS, how="left", validate="one_to_one")
        if videos["mean_monitoring_quality"].isna().any():
            raise ValueError(f"fold {fold} predictions are missing validation quality summaries")
        video_frames.append(_add_prediction_diagnostics(videos))
        sources.extend(
            [
                _source_record("categorical_predictions", fold, prediction_path),
                _source_record("development_manifest", fold, manifest_path),
            ]
        )

    pooled = pd.concat(video_frames, ignore_index=True)
    _write_csv(pooled, output / "video_diagnostics.csv")
    subjects = _subject_diagnostics(pooled)
    _write_csv(subjects, output / "subject_diagnostics.csv")

    scope_reports = {"pooled": _scope_report(pooled)}
    scope_reports.update(
        {f"d{fold}": _scope_report(pooled.loc[pooled["fold"] == fold]) for fold in folds}
    )
    quality_report = _quality_report(pooled)
    confidence_report = _confidence_report(pooled)
    subject_report = _subject_report(subjects)
    pooled_classes = scope_reports["pooled"]["detailed"]["per_class"]
    weakest_class = min(LABEL_NAMES, key=lambda name: pooled_classes[name]["recall"])
    report: dict[str, Any] = {
        "schema_version": 1,
        "scope": {
            "policy": "development folds 2-5 only; fold 1 and DROZY prohibited",
            "folds": list(folds),
            "subjects": int(pooled["cluster_id"].nunique()),
            "videos": len(pooled),
            "seed": 13,
            "model": "retained categorical quality-gated baseline",
        },
        "method": {
            "prediction_unit": "provider video",
            "quality_source": "cached validation NPZ windows; no model inference",
            "monitoring_quality": "geometric mean of visual and physical quality",
            "minimum_quality": MINIMUM_QUALITY,
        },
        "sources": sources,
        "scopes": scope_reports,
        "confidence": confidence_report,
        "quality": quality_report,
        "subjects": subject_report,
        "findings": {
            "weakest_recall_class": weakest_class,
            "weakest_recall": float(pooled_classes[weakest_class]["recall"]),
            "quality_association": _quality_association(quality_report),
            "next_action": (
                "use these development-only findings to preregister one model factor; do not "
                "train, inspect fold 1, or access DROZY before that amendment is frozen"
            ),
        },
    }
    write_json(output / "baseline_failure_audit.json", report)
    return report


def _validation_video_quality(manifest_path: Path, fold: int) -> pd.DataFrame:
    manifest = read_manifest(manifest_path)
    validation = manifest.loc[manifest["split"] == "validation"].copy()
    if validation.empty or set(validation["fold"].astype(int)) != {fold}:
        raise ValueError(f"manifest validation rows must contain only fold {fold}")

    rows: list[dict[str, Any]] = []
    for row in validation.itertuples(index=False):
        with np.load(manifest_path.parent / str(row.path), allow_pickle=False) as sample:
            quality = np.asarray(sample["quality"], dtype=np.float64)
        if quality.ndim != 2 or quality.shape[1] != 2:
            raise ValueError(f"invalid quality shape in {row.path}: {quality.shape}")
        if not np.isfinite(quality).all():
            raise ValueError(f"non-finite quality values in {row.path}")
        monitoring = np.sqrt(np.clip(quality[:, 0] * quality[:, 1], 0.0, None))
        rows.append(
            {
                "dataset": str(row.dataset),
                "subject_id": str(row.subject_id),
                "session_id": str(row.session_id),
                "fold": fold,
                "visual_quality_sum": float(quality[:, 0].sum()),
                "physical_quality_sum": float(quality[:, 1].sum()),
                "monitoring_quality_sum": float(monitoring.sum()),
                "low_quality_frames": int((monitoring < MINIMUM_QUALITY).sum()),
                "quality_frames": len(monitoring),
            }
        )
    windows = pd.DataFrame(rows)
    grouped = windows.groupby(KEY_COLUMNS, as_index=False, sort=True).sum(numeric_only=True)
    count = grouped["quality_frames"].to_numpy(dtype=np.float64)
    grouped["mean_visual_quality"] = grouped["visual_quality_sum"] / count
    grouped["mean_physical_quality"] = grouped["physical_quality_sum"] / count
    grouped["mean_monitoring_quality"] = grouped["monitoring_quality_sum"] / count
    grouped["low_quality_fraction"] = grouped["low_quality_frames"] / count
    return grouped.drop(
        columns=["visual_quality_sum", "physical_quality_sum", "monitoring_quality_sum"]
    )


def _add_prediction_diagnostics(frame: pd.DataFrame) -> pd.DataFrame:
    audited = frame.copy()
    scores = audited[PROBABILITY_COLUMNS].to_numpy(dtype=np.float64)
    labels = audited["label"].to_numpy(dtype=np.int64)
    order = np.argsort(scores, axis=1)
    audited["cluster_id"] = "d" + audited["fold"].astype(str) + "/" + audited["subject_id"]
    audited["prediction"] = scores.argmax(axis=1)
    audited["correct"] = audited["prediction"].to_numpy() == labels
    audited["confidence"] = scores.max(axis=1)
    audited["margin"] = (
        scores[np.arange(len(scores)), order[:, -1]] - scores[np.arange(len(scores)), order[:, -2]]
    )
    audited["true_class_probability"] = scores[np.arange(len(scores)), labels]
    audited["high_confidence_error"] = ~audited["correct"] & (audited["confidence"] >= 0.60)
    return audited


def _scope_report(frame: pd.DataFrame) -> dict[str, Any]:
    scores = frame[PROBABILITY_COLUMNS].to_numpy(dtype=np.float64)
    labels = frame["label"].to_numpy(dtype=np.int64)
    return {
        **classification_metrics(labels, scores).to_dict(),
        "subjects": int(frame["cluster_id"].nunique()),
        "videos": len(frame),
        "detailed": detailed_classification_report(labels, scores, LABEL_NAMES),
    }


def _confidence_report(frame: pd.DataFrame) -> dict[str, Any]:
    correct = frame.loc[frame["correct"]]
    incorrect = frame.loc[~frame["correct"]]
    high_confidence_errors = frame.loc[frame["high_confidence_error"]]
    return {
        "mean_confidence_correct": _safe_mean(correct["confidence"]),
        "mean_confidence_incorrect": _safe_mean(incorrect["confidence"]),
        "mean_margin_correct": _safe_mean(correct["margin"]),
        "mean_margin_incorrect": _safe_mean(incorrect["margin"]),
        "high_confidence_error_threshold": 0.60,
        "high_confidence_errors": len(high_confidence_errors),
        "high_confidence_error_fraction": len(high_confidence_errors) / len(frame),
        "high_confidence_errors_by_true_class": {
            LABEL_NAMES[label]: int((high_confidence_errors["label"] == label).sum())
            for label in range(len(LABEL_NAMES))
        },
    }


def _quality_report(frame: pd.DataFrame) -> dict[str, Any]:
    correct = frame.loc[frame["correct"]]
    incorrect = frame.loc[~frame["correct"]]
    quality_column = "mean_monitoring_quality"
    quantiles = min(4, int(frame[quality_column].nunique()))
    bins = pd.qcut(frame[quality_column], q=quantiles, duplicates="drop")
    quartiles: list[dict[str, Any]] = []
    for interval, group in frame.groupby(bins, observed=True, sort=True):
        quartiles.append(
            {
                "range": str(interval),
                "videos": len(group),
                "mean_quality": float(group[quality_column].mean()),
                "error_rate": float((~group["correct"]).mean()),
            }
        )
    return {
        "mean_monitoring_quality_correct": _safe_mean(correct[quality_column]),
        "mean_monitoring_quality_incorrect": _safe_mean(incorrect[quality_column]),
        "incorrect_minus_correct_quality": (
            _safe_mean(incorrect[quality_column]) - _safe_mean(correct[quality_column])
        ),
        "mean_low_quality_fraction_correct": _safe_mean(correct["low_quality_fraction"]),
        "mean_low_quality_fraction_incorrect": _safe_mean(incorrect["low_quality_fraction"]),
        "quality_quartiles": quartiles,
    }


def _subject_diagnostics(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for cluster_id, group in frame.groupby("cluster_id", observed=True, sort=True):
        rows.append(
            {
                "cluster_id": cluster_id,
                "fold": int(group["fold"].iloc[0]),
                "subject_id": str(group["subject_id"].iloc[0]),
                "videos": len(group),
                "accuracy": float(group["correct"].mean()),
                "mean_confidence": float(group["confidence"].mean()),
                "mean_monitoring_quality": float(group["mean_monitoring_quality"].mean()),
                "alert_correct": _class_correct(group, 0),
                "low_vigilance_correct": _class_correct(group, 1),
                "drowsy_correct": _class_correct(group, 2),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["accuracy", "mean_confidence", "cluster_id"], ascending=[True, False, True]
    )


def _subject_report(frame: pd.DataFrame) -> dict[str, Any]:
    worst = frame.head(10)
    return {
        "mean_subject_accuracy": float(frame["accuracy"].mean()),
        "subject_accuracy_std": float(frame["accuracy"].std(ddof=1)),
        "subjects_with_no_correct_videos": int((frame["accuracy"] == 0.0).sum()),
        "subjects_with_all_videos_correct": int((frame["accuracy"] == 1.0).sum()),
        "worst_subjects": worst.to_dict("records"),
    }


def _class_correct(frame: pd.DataFrame, label: int) -> bool | None:
    rows = frame.loc[frame["label"] == label, "correct"]
    return bool(rows.all()) if len(rows) else None


def _quality_association(report: dict[str, Any]) -> str:
    difference = float(report["incorrect_minus_correct_quality"])
    if difference <= -0.05:
        return "incorrect videos have materially lower mean monitoring quality"
    if difference >= 0.05:
        return "incorrect videos have materially higher mean monitoring quality"
    return "mean monitoring quality does not materially separate correct and incorrect videos"


def _source_record(kind: str, fold: int, path: Path) -> dict[str, Any]:
    return {"kind": kind, "fold": fold, "path": str(path), "sha256": sha256_file(path)}


def _safe_mean(values: pd.Series) -> float:
    return float(values.mean()) if len(values) else float("nan")


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)
