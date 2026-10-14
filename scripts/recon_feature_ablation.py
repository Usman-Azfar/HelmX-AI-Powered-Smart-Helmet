"""Follow-up to changesToMake.txt item 2: right now the classifier head only
ever sees one aggregated scalar (mean reconstruction error) from the
unsupervised branch. That throws away structure a crash could show up in --
one axis hit much harder than others, only a few timesteps affected, or a
distinct onset/offset shape rather than a flat elevated mean.

Ablates model_lib.build_model()'s `recon_feature_mode` across
{"none", "scalar", "mean_peak", "rich"} (see src/model.py: ReconstructionFeatures)
over config.SEEDS, training from scratch each time (deliberately NOT combined
with two-stage pretraining here, to isolate just the feature-richness effect
-- see scripts/two_stage_pretraining_experiment.py for that ablation, and
changes.md for the natural follow-up once both are independently evaluated).

If richer reconstruction features improve Model A's classifier head while
Model B (which has no such features to add) is unaffected by construction,
that is a genuine hybrid-specific advantage -- unlike the naive/tuned
OR-fusion or post-hoc stacking approaches already tried, this changes what
the classifier itself is trained on, end-to-end."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from src import config, io_loaders, preprocess, manifest, evaluate
from train import train_hybrid_from_datasets  # noqa: E402

FEATURE_MODES = ["none", "scalar", "mean_peak", "rich"]


def evaluate_on_test(model, normalizer, thresholds, test_ds):
    X_seq, X_aux = normalizer.transform(test_ds.X_seq, test_ds.X_aux)
    crash_prob = model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)["crash_prob"].ravel()
    m = evaluate.full_classification_metrics(test_ds.y, crash_prob, thresholds["classifier_prob_balanced"])
    return {k: m[k] for k in ["roc_auc", "pr_auc", "f1_score", "precision", "recall_sensitivity"]}


def _mean_std(values):
    arr = np.array(values, dtype=np.float64)
    return {"mean": float(arr.mean()), "std": float(arr.std())}


def main():
    print("Loading sessions...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    train_ds = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")
    print(f"Train: {len(train_ds.y)} windows, Val: {len(val_ds.y)}, Test: {len(test_ds.y)}")

    per_mode = {mode: [] for mode in FEATURE_MODES}
    for seed in config.SEEDS:
        for mode in FEATURE_MODES:
            print(f"\n=== seed {seed}, recon_feature_mode={mode!r} ===")
            model, normalizer, thresholds, _ = train_hybrid_from_datasets(
                seed, train_ds, val_ds, verbose=0, recon_feature_mode=mode,
            )
            m = evaluate_on_test(model, normalizer, thresholds, test_ds)
            print(f"  ROC-AUC={m['roc_auc']:.3f} F1={m['f1_score']:.3f} PR-AUC={m['pr_auc']:.3f}")
            per_mode[mode].append({"seed": seed, **m})

    metric_names = ["roc_auc", "pr_auc", "f1_score", "precision", "recall_sensitivity"]
    summary = {
        mode: {name: _mean_std([r[name] for r in runs]) for name in metric_names}
        for mode, runs in per_mode.items()
    }

    report = {
        "description": (
            "Reconstruction-feature richness ablation: model_lib.build_model()'s "
            "recon_feature_mode in {none, scalar, mean_peak, rich}, from-scratch training "
            "(no two-stage pretraining), 5 seeds each, same frozen 100%-label split as every "
            "other experiment."
        ),
        "feature_modes": FEATURE_MODES,
        "feature_counts": {"none": 0, "scalar": 1, "mean_peak": 2, "rich": 12},
        "seeds": config.SEEDS,
        "summary_mean_std": summary,
        "per_seed_runs": per_mode,
    }
    print("\n" + json.dumps(summary, indent=2))
    evaluate.save_metrics(report, "recon_feature_ablation")


if __name__ == "__main__":
    main()
