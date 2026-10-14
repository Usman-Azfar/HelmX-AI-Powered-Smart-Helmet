"""Shared evaluation helper for the ExperimentsToPerform.txt (updated) staged
experiment (exp1/exp2/exp3_*.py) -- centralizes the metric set the file asks
for (PR-AUC, ROC-AUC, F1, recall at fixed specificity, event-level session
sensitivity) so all three scripts' comparison tables use an identical
definition per metric instead of each script computing its own subset."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from src import evaluate


def evaluate_variant(y_true, scores, session_ids, threshold, target_specificity=0.95):
    """One classifier-score array + one operating threshold -> the full
    metric set used across Experiments 1-3. `threshold` should be the
    val-calibrated `classifier_prob_balanced` threshold, matching what's
    actually deployed."""
    base = evaluate.full_classification_metrics(y_true, scores, threshold)
    spec = evaluate.recall_at_specificity(y_true, scores, target_specificity=target_specificity)
    deployed = evaluate.simulate_deployed_alerts(y_true, scores, np.asarray(session_ids), threshold)
    return {
        "roc_auc": base["roc_auc"],
        "pr_auc": base["pr_auc"],
        "f1_score": base["f1_score"],
        "precision": base["precision"],
        "recall_sensitivity": base["recall_sensitivity"],
        "specificity": base["specificity"],
        f"recall_at_{int(target_specificity * 100)}pct_specificity": spec["recall"],
        "specificity_achieved_for_recall_at_spec": spec["specificity_achieved"],
        "event_level_session_recall": deployed["session_recall"],
    }


def mean_std(runs, metric_names):
    """runs: list of per-seed metric dicts (as returned by evaluate_variant,
    plus a 'seed' key). Returns {metric: {"mean":..., "std":...}}."""
    out = {}
    for name in metric_names:
        values = [r[name] for r in runs if r.get(name) is not None]
        arr = np.array(values, dtype=np.float64)
        out[name] = {"mean": float(arr.mean()), "std": float(arr.std())} if len(arr) else {"mean": None, "std": None}
    return out


METRIC_NAMES = [
    "roc_auc", "pr_auc", "f1_score", "precision", "recall_sensitivity", "specificity",
    "recall_at_95pct_specificity", "specificity_achieved_for_recall_at_spec",
    "event_level_session_recall",
]
