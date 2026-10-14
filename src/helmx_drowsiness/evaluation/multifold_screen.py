"""Frozen multi-fold candidate-screening analysis."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.metrics import f1_score

from helmx_drowsiness.evaluation.bootstrap import paired_clustered_prediction_bootstrap
from helmx_drowsiness.evaluation.metrics import classification_metrics
from helmx_drowsiness.training.provenance import sha256_file, write_json

KEY_COLUMNS = ["dataset", "subject_id", "session_id", "fold"]
MATCH_COLUMNS = ["label", "windows"]
PROBABILITY_COLUMNS = ["probability_0", "probability_1", "probability_2"]


def evaluate_multifold_screen(
    root: str | Path,
    output: str | Path,
    *,
    candidate_directory: str = "ordinal",
    folds: tuple[int, ...] = (2, 3, 4, 5),
    resamples: int = 2000,
    seed: int = 2026,
) -> dict[str, Any]:
    """Evaluate every frozen seed-13 gate on paired validation-video predictions."""

    if not candidate_directory or Path(candidate_directory).name != candidate_directory:
        raise ValueError("candidate_directory must be one non-empty directory name")

    source_root = Path(root)
    paired_folds: list[pd.DataFrame] = []
    fold_results: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for fold in folds:
        baseline_path = (
            source_root
            / f"d{fold}"
            / "categorical"
            / "seed-13"
            / ("validation_video_predictions.csv")
        )
        candidate_path = (
            source_root
            / f"d{fold}"
            / candidate_directory
            / "seed-13"
            / "validation_video_predictions.csv"
        )
        baseline = _read_predictions(baseline_path, fold)
        candidate = _read_predictions(candidate_path, fold)
        paired = _pair_predictions(baseline, candidate, fold)
        paired_folds.append(paired)
        baseline_scores = _probabilities(paired, "baseline")
        candidate_scores = _probabilities(paired, "candidate")
        labels = paired["label_baseline"].to_numpy(dtype=np.int64)
        baseline_f1 = classification_metrics(labels, baseline_scores).macro_f1
        candidate_f1 = classification_metrics(labels, candidate_scores).macro_f1
        fold_results.append(
            {
                "fold": fold,
                "subjects": int(paired["subject_id"].nunique()),
                "videos": len(paired),
                "baseline_macro_f1": baseline_f1,
                "candidate_macro_f1": candidate_f1,
                "difference": candidate_f1 - baseline_f1,
                "candidate_wins": candidate_f1 > baseline_f1,
            }
        )
        sources.extend(
            [
                {
                    "fold": fold,
                    "model": "baseline",
                    "path": str(baseline_path),
                    "sha256": sha256_file(baseline_path),
                },
                {
                    "fold": fold,
                    "model": "candidate",
                    "path": str(candidate_path),
                    "sha256": sha256_file(candidate_path),
                },
            ]
        )

    pooled = pd.concat(paired_folds, ignore_index=True)
    labels = pooled["label_baseline"].to_numpy(dtype=np.int64)
    baseline_scores = _probabilities(pooled, "baseline")
    candidate_scores = _probabilities(pooled, "candidate")
    baseline_metrics = classification_metrics(labels, baseline_scores)
    candidate_metrics = classification_metrics(labels, candidate_scores)

    def macro_f1(targets: NDArray[np.int64], probabilities: NDArray[np.float64]) -> float:
        return float(
            f1_score(
                targets,
                probabilities.argmax(axis=1),
                labels=[0, 1, 2],
                average="macro",
                zero_division=0,
            )
        )

    interval = paired_clustered_prediction_bootstrap(
        labels,
        baseline_scores,
        candidate_scores,
        pooled["subject_id"].to_numpy(),
        macro_f1,
        resamples=resamples,
        seed=seed,
    )
    differences = [float(result["difference"]) for result in fold_results]
    wins = sum(bool(result["candidate_wins"]) for result in fold_results)
    pooled_difference = candidate_metrics.macro_f1 - baseline_metrics.macro_f1
    gates: dict[str, dict[str, int | float | bool]] = {
        "wins_at_least_three_of_four": {"value": wins, "threshold": 3, "passed": wins >= 3},
        "pooled_macro_f1_improvement": {
            "value": pooled_difference,
            "threshold": 0.020,
            "passed": pooled_difference >= 0.020,
        },
        "no_fold_worse_by_more_than_0_020": {
            "value": min(differences),
            "threshold": -0.020,
            "passed": min(differences) >= -0.020,
        },
        "paired_subject_bootstrap_lower_above_zero": {
            "value": interval.lower,
            "threshold": 0.0,
            "passed": interval.lower > 0.0,
        },
    }
    passed = all(bool(gate["passed"]) for gate in gates.values())
    report: dict[str, Any] = {
        "schema_version": 1,
        "protocol": "docs/MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md",
        "screening_seed": 13,
        "baseline_directory": "categorical",
        "candidate_directory": candidate_directory,
        "folds": fold_results,
        "pooled": {
            "subjects": int(pooled["subject_id"].nunique()),
            "videos": len(pooled),
            "baseline": baseline_metrics.to_dict(),
            "candidate": candidate_metrics.to_dict(),
            "macro_f1_difference": pooled_difference,
        },
        "paired_subject_bootstrap_macro_f1_difference": asdict(interval),
        "gates": gates,
        "screening_passed": passed,
        "confirmatory_five_seed_stage_authorized": passed,
        "drozy_access_authorized": False,
        "sources": sources,
    }
    write_json(output, report)
    return report


def _read_predictions(path: Path, fold: int) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"missing fold-{fold} prediction file: {path}")
    frame = pd.read_csv(path)
    required = set(KEY_COLUMNS + MATCH_COLUMNS + PROBABILITY_COLUMNS)
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")
    if frame.duplicated(KEY_COLUMNS).any():
        raise ValueError(f"{path} contains duplicate video keys")
    if set(frame["fold"].astype(int).unique()) != {fold}:
        raise ValueError(f"{path} contains rows outside fold {fold}")
    return frame


def _pair_predictions(baseline: pd.DataFrame, candidate: pd.DataFrame, fold: int) -> pd.DataFrame:
    paired = baseline.merge(
        candidate,
        on=KEY_COLUMNS,
        how="inner",
        suffixes=("_baseline", "_candidate"),
        validate="one_to_one",
    )
    if len(paired) != len(baseline) or len(paired) != len(candidate):
        raise ValueError(f"fold {fold} baseline and candidate video keys do not match exactly")
    for column in MATCH_COLUMNS:
        if not (paired[f"{column}_baseline"] == paired[f"{column}_candidate"]).all():
            raise ValueError(f"fold {fold} has mismatched paired {column} values")
    return paired.sort_values(KEY_COLUMNS, ignore_index=True)


def _probabilities(frame: pd.DataFrame, suffix: str) -> NDArray[np.float64]:
    columns = [f"{column}_{suffix}" for column in PROBABILITY_COLUMNS]
    probabilities: NDArray[np.float64] = np.asarray(frame[columns].to_numpy(), dtype=np.float64)
    if not np.isfinite(probabilities).all() or (probabilities < 0).any():
        raise ValueError("prediction probabilities must be finite and non-negative")
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-5):
        raise ValueError("prediction probability rows must sum to one")
    return probabilities
