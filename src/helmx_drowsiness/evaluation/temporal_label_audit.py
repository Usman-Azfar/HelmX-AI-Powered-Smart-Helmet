"""Training/validation-only audit of clip labels against within-video temporal evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from helmx_drowsiness.datasets.manifest import read_manifest
from helmx_drowsiness.features.temporal import TemporalFeatureExtractor
from helmx_drowsiness.training.provenance import sha256_file, write_json

AUDIT_SPLITS = ("train", "validation")
TEMPORAL_BINS = ("early", "middle", "late")
AUDIT_FEATURES = (
    "relative_ear",
    "perclos",
    "blink_rate_per_minute",
    "mean_blink_seconds",
    "current_closure_seconds",
    "relative_mar",
    "mouth_open_fraction",
    "valid_fraction",
)
DROWSY_EXPECTED_DIRECTIONS = {
    "probability_2": 1.0,
    "relative_ear": -1.0,
    "perclos": 1.0,
    "mean_blink_seconds": 1.0,
    "current_closure_seconds": 1.0,
    "relative_mar": 1.0,
    "mouth_open_fraction": 1.0,
}


def run_temporal_label_audit(
    manifest_path: str | Path,
    train_predictions_path: str | Path,
    validation_predictions_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Audit temporal evidence without loading or selecting on the test split."""

    manifest_file = Path(manifest_path)
    manifest = read_manifest(manifest_file)
    development = manifest[manifest["split"].isin(AUDIT_SPLITS)].copy()
    predictions = pd.concat(
        [pd.read_csv(train_predictions_path), pd.read_csv(validation_predictions_path)],
        ignore_index=True,
    )
    _validate_prediction_identity(development, predictions)
    prediction_columns = [f"probability_{index}" for index in range(3)]
    merged = development.merge(
        predictions[["path", "prediction", *prediction_columns]],
        on="path",
        how="left",
        validate="one_to_one",
    )
    group_columns = ["subject_id", "session_id"]
    merged["video_end_seconds"] = merged.groupby(group_columns)["end_seconds"].transform("max")
    midpoint = (merged["start_seconds"] + merged["end_seconds"]) / 2.0
    merged["normalized_progress"] = midpoint / merged["video_end_seconds"].clip(lower=1e-6)
    merged["temporal_bin"] = pd.cut(
        merged["normalized_progress"],
        bins=[-np.inf, 1.0 / 3.0, 2.0 / 3.0, np.inf],
        labels=TEMPORAL_BINS,
        ordered=True,
    ).astype(str)

    root = manifest_file.parent
    feature_indices = {
        name: TemporalFeatureExtractor.feature_names.index(name) for name in AUDIT_FEATURES
    }
    feature_rows: list[dict[str, float]] = []
    for row in merged.itertuples(index=False):
        with np.load(root / str(row.path), allow_pickle=False) as sample:
            physiology = np.asarray(sample["physiology"], dtype=np.float64)
        if physiology.ndim != 2 or physiology.shape[1] != len(
            TemporalFeatureExtractor.feature_names
        ):
            raise ValueError(f"invalid physiology shape in {row.path}: {physiology.shape}")
        feature_rows.append(
            {name: float(physiology[-1, index]) for name, index in feature_indices.items()}
        )
    windows = pd.concat([merged.reset_index(drop=True), pd.DataFrame(feature_rows)], axis=1)
    metrics = [*prediction_columns, *AUDIT_FEATURES]
    summary = _summarize_bins(windows, metrics)
    slopes = _video_slopes(windows, metrics)
    report = {
        "schema_version": 1,
        "scope": {
            "included_splits": list(AUDIT_SPLITS),
            "excluded_split": "test",
            "windows": len(windows),
            "subjects": int(windows["subject_id"].nunique()),
            "videos": int(windows[group_columns].drop_duplicates().shape[0]),
        },
        "inputs": {
            "manifest": str(manifest_file.resolve()),
            "manifest_sha256": sha256_file(manifest_file),
            "train_predictions": str(Path(train_predictions_path).resolve()),
            "train_predictions_sha256": sha256_file(train_predictions_path),
            "validation_predictions": str(Path(validation_predictions_path).resolve()),
            "validation_predictions_sha256": sha256_file(validation_predictions_path),
        },
        "temporal_bins": {
            "early": [0.0, 1.0 / 3.0],
            "middle": [1.0 / 3.0, 2.0 / 3.0],
            "late": [2.0 / 3.0, 1.0],
            "basis": "window midpoint divided by final window end within subject/session",
        },
        "macro_f1_by_split_and_bin": _macro_f1_by_bin(windows),
        "drowsy_trajectory": _drowsy_trajectory(summary, metrics),
        "drowsy_video_consistency": _drowsy_video_consistency(windows),
        "late_drowsy_minus_alert": _late_class_separation(summary, metrics),
        "interpretation_rule": (
            "Evidence for temporal label dilution requires coherent late-versus-early movement "
            "toward drowsiness across model probability and ocular features; probability alone "
            "is insufficient. Fold 1 is excluded from this decision."
        ),
    }

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_csv_atomic(windows, output / "temporal_label_windows.csv")
    _write_csv_atomic(summary, output / "temporal_label_summary.csv")
    _write_csv_atomic(slopes, output / "temporal_label_video_slopes.csv")
    write_json(output / "temporal_label_audit.json", report)
    return report


def _validate_prediction_identity(manifest: pd.DataFrame, predictions: pd.DataFrame) -> None:
    required = {"path", "label", "prediction", "probability_0", "probability_1", "probability_2"}
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"prediction files are missing columns: {sorted(missing)}")
    if predictions["path"].duplicated().any():
        raise ValueError("prediction files contain duplicate paths")
    expected = set(manifest["path"].astype(str))
    actual = set(predictions["path"].astype(str))
    if expected != actual:
        raise ValueError(
            f"development prediction paths differ: missing={len(expected - actual)}, "
            f"unexpected={len(actual - expected)}"
        )
    labels = manifest[["path", "label"]].merge(
        predictions[["path", "label"]], on="path", suffixes=("_manifest", "_prediction")
    )
    if not (labels["label_manifest"] == labels["label_prediction"]).all():
        raise ValueError("prediction labels do not match the manifest")


def _summarize_bins(windows: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (split, label, temporal_bin), group in windows.groupby(
        ["split", "label", "temporal_bin"], observed=True
    ):
        row: dict[str, Any] = {
            "split": str(split),
            "label": int(label),
            "temporal_bin": str(temporal_bin),
            "windows": len(group),
            "subjects": int(group["subject_id"].nunique()),
            "videos": int(group[["subject_id", "session_id"]].drop_duplicates().shape[0]),
        }
        for metric in metrics:
            values = group[metric].to_numpy(dtype=np.float64)
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_median"] = float(np.median(values))
        rows.append(row)
    return pd.DataFrame(rows)


def _video_slopes(windows: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (split, subject, session, label), group in windows.groupby(
        ["split", "subject_id", "session_id", "label"], observed=True
    ):
        ordered = group.sort_values("normalized_progress")
        progress = ordered["normalized_progress"].to_numpy(dtype=np.float64)
        row: dict[str, Any] = {
            "split": str(split),
            "subject_id": str(subject),
            "session_id": str(session),
            "label": int(label),
            "windows": len(ordered),
        }
        for metric in metrics:
            values = ordered[metric].to_numpy(dtype=np.float64)
            row[f"{metric}_slope"] = (
                float(np.polyfit(progress, values, 1)[0]) if len(progress) >= 2 else float("nan")
            )
        rows.append(row)
    return pd.DataFrame(rows)


def _macro_f1_by_bin(windows: pd.DataFrame) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for split in AUDIT_SPLITS:
        result[split] = {}
        selected = windows[windows["split"] == split]
        for temporal_bin in TEMPORAL_BINS:
            group = selected[selected["temporal_bin"] == temporal_bin]
            result[split][temporal_bin] = float(
                f1_score(group["label"], group["prediction"], average="macro", zero_division=0)
            )
    return result


def _drowsy_trajectory(summary: pd.DataFrame, metrics: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for split in AUDIT_SPLITS:
        selected = summary[(summary["split"] == split) & (summary["label"] == 2)].set_index(
            "temporal_bin"
        )
        split_result: dict[str, Any] = {}
        for metric in metrics:
            values = {
                bucket: float(selected.loc[bucket, f"{metric}_mean"]) for bucket in TEMPORAL_BINS
            }
            values["late_minus_early"] = values["late"] - values["early"]
            split_result[metric] = values
        result[split] = split_result
    return result


def _late_class_separation(summary: pd.DataFrame, metrics: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for split in AUDIT_SPLITS:
        late = summary[(summary["split"] == split) & (summary["temporal_bin"] == "late")].set_index(
            "label"
        )
        result[split] = {
            metric: float(late.loc[2, f"{metric}_mean"] - late.loc[0, f"{metric}_mean"])
            for metric in metrics
        }
    return result


def _drowsy_video_consistency(windows: pd.DataFrame) -> dict[str, Any]:
    """Report paired late-minus-early changes so pooled outliers cannot hide heterogeneity."""

    result: dict[str, Any] = {}
    for split in AUDIT_SPLITS:
        selected = windows[(windows["split"] == split) & (windows["label"] == 2)]
        pivot = selected.pivot_table(
            index=["subject_id", "session_id"],
            columns="temporal_bin",
            values=list(DROWSY_EXPECTED_DIRECTIONS),
            aggfunc="mean",
        )
        split_result: dict[str, Any] = {}
        for metric, direction in DROWSY_EXPECTED_DIRECTIONS.items():
            delta = (pivot[(metric, "late")] - pivot[(metric, "early")]).dropna()
            expected = direction * delta > 0.0
            split_result[metric] = {
                "videos": len(delta),
                "mean_late_minus_early": float(delta.mean()),
                "median_late_minus_early": float(delta.median()),
                "expected_direction_videos": int(expected.sum()),
                "expected_direction_fraction": float(expected.mean()),
            }
        result[split] = split_result
    return result


def _write_csv_atomic(frame: pd.DataFrame, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(destination)
