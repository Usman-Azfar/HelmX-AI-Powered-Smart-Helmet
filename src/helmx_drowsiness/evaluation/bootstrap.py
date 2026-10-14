"""Subject-clustered bootstrap confidence intervals."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    estimate: float
    lower: float
    upper: float
    confidence: float
    resamples: int


def clustered_bootstrap(
    values: ArrayLike,
    groups: ArrayLike,
    statistic: Callable[[NDArray[np.float64]], float] = np.mean,
    *,
    resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 2026,
) -> ConfidenceInterval:
    """Bootstrap whole subjects/sessions so frames do not become fake replicates."""

    measurements = np.asarray(values, dtype=np.float64)
    cluster_ids = np.asarray(groups)
    if measurements.ndim != 1 or cluster_ids.shape != measurements.shape:
        raise ValueError("values and groups must be equal-length vectors")
    if resamples < 100:
        raise ValueError("at least 100 resamples are required")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    unique_groups = np.unique(cluster_ids)
    if len(unique_groups) < 2:
        raise ValueError("at least two independent groups are required")

    rng = np.random.default_rng(seed)
    results = np.empty(resamples, dtype=np.float64)
    indices = {group: np.flatnonzero(cluster_ids == group) for group in unique_groups}
    for index in range(resamples):
        selected_groups = rng.choice(unique_groups, size=len(unique_groups), replace=True)
        sampled = np.concatenate([measurements[indices[group]] for group in selected_groups])
        results[index] = statistic(sampled)
    alpha = (1.0 - confidence) / 2.0
    return ConfidenceInterval(
        estimate=float(statistic(measurements)),
        lower=float(np.quantile(results, alpha)),
        upper=float(np.quantile(results, 1.0 - alpha)),
        confidence=confidence,
        resamples=resamples,
    )


def clustered_prediction_bootstrap(
    labels: ArrayLike,
    probabilities: ArrayLike,
    groups: ArrayLike,
    statistic: Callable[[NDArray[np.int64], NDArray[np.float64]], float],
    *,
    resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 2026,
) -> ConfidenceInterval:
    """Bootstrap subjects while recomputing a prediction metric on every resample."""

    targets = np.asarray(labels, dtype=np.int64)
    scores = np.asarray(probabilities, dtype=np.float64)
    cluster_ids = np.asarray(groups)
    if targets.ndim != 1 or scores.ndim != 2 or scores.shape[0] != len(targets):
        raise ValueError("labels and probabilities have incompatible shapes")
    if cluster_ids.shape != targets.shape:
        raise ValueError("groups must have one entry per prediction")
    if resamples < 100:
        raise ValueError("at least 100 resamples are required")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    unique_groups = np.unique(cluster_ids)
    if len(unique_groups) < 2:
        raise ValueError("at least two independent groups are required")

    rng = np.random.default_rng(seed)
    results = np.empty(resamples, dtype=np.float64)
    indices = {group: np.flatnonzero(cluster_ids == group) for group in unique_groups}
    for index in range(resamples):
        selected_groups = rng.choice(unique_groups, size=len(unique_groups), replace=True)
        sampled = np.concatenate([indices[group] for group in selected_groups])
        results[index] = statistic(targets[sampled], scores[sampled])
    alpha = (1.0 - confidence) / 2.0
    estimate = statistic(targets, scores)
    return ConfidenceInterval(
        estimate=float(estimate),
        lower=float(np.quantile(results, alpha)),
        upper=float(np.quantile(results, 1.0 - alpha)),
        confidence=confidence,
        resamples=resamples,
    )


def paired_clustered_prediction_bootstrap(
    labels: ArrayLike,
    baseline_probabilities: ArrayLike,
    candidate_probabilities: ArrayLike,
    groups: ArrayLike,
    statistic: Callable[[NDArray[np.int64], NDArray[np.float64]], float],
    *,
    resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 2026,
) -> ConfidenceInterval:
    """Bootstrap paired model predictions by subject and return candidate minus baseline."""

    targets = np.asarray(labels, dtype=np.int64)
    baseline = np.asarray(baseline_probabilities, dtype=np.float64)
    candidate = np.asarray(candidate_probabilities, dtype=np.float64)
    cluster_ids = np.asarray(groups)
    if targets.ndim != 1 or baseline.ndim != 2 or baseline.shape[0] != len(targets):
        raise ValueError("labels and baseline probabilities have incompatible shapes")
    if candidate.shape != baseline.shape:
        raise ValueError("baseline and candidate probabilities must have equal shapes")
    if cluster_ids.shape != targets.shape:
        raise ValueError("groups must have one entry per prediction")
    if resamples < 100:
        raise ValueError("at least 100 resamples are required")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    unique_groups = np.unique(cluster_ids)
    if len(unique_groups) < 2:
        raise ValueError("at least two independent groups are required")

    def difference(indices: NDArray[np.int64]) -> float:
        candidate_score = statistic(targets[indices], candidate[indices])
        baseline_score = statistic(targets[indices], baseline[indices])
        return float(candidate_score - baseline_score)

    rng = np.random.default_rng(seed)
    results = np.empty(resamples, dtype=np.float64)
    indices_by_group = {group: np.flatnonzero(cluster_ids == group) for group in unique_groups}
    for index in range(resamples):
        selected_groups = rng.choice(unique_groups, size=len(unique_groups), replace=True)
        sampled = np.concatenate([indices_by_group[group] for group in selected_groups])
        results[index] = difference(sampled)
    alpha = (1.0 - confidence) / 2.0
    all_indices = np.arange(len(targets), dtype=np.int64)
    return ConfidenceInterval(
        estimate=difference(all_indices),
        lower=float(np.quantile(results, alpha)),
        upper=float(np.quantile(results, 1.0 - alpha)),
        confidence=confidence,
        resamples=resamples,
    )
