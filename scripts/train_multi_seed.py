"""changesToMake.txt item 5: rather than pretend a single training run's
metrics are exact (TF weight init / shuffling aren't seeded per-run, only the
data split is), train config.SEEDS worth of independent model instances --
same frozen data split every time -- and report mean +/- std on the held-out
test split. The scientifically stronger alternative to full seeding that the
paper reviewer explicitly preferred."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from src import config, io_loaders, preprocess, manifest, evaluate
from train import train_one  # noqa: E402


def evaluate_seed(model, normalizer, thresholds, sessions, split_of):
    test_ds = manifest.build_dataset(sessions, split_of, "test")
    X_seq, X_aux = normalizer.transform(test_ds.X_seq, test_ds.X_aux)
    preds = model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
    crash_prob = preds["crash_prob"].ravel()

    m = evaluate.full_classification_metrics(test_ds.y, crash_prob, thresholds["classifier_prob_balanced"])
    return {
        "roc_auc": m["roc_auc"],
        "pr_auc": m["pr_auc"],
        "f1_score": m["f1_score"],
        "precision": m["precision"],
        "recall_sensitivity": m["recall_sensitivity"],
    }


def _mean_std(values):
    arr = np.array(values, dtype=np.float64)
    return {"mean": float(arr.mean()), "std": float(arr.std())}


def main():
    print("Loading sessions once (shared across all seeds -- data split is fixed)...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    per_seed = {}
    for seed in config.SEEDS:
        print(f"\n=== Training seed {seed} ===")
        model, normalizer, thresholds, _history, _s, _sp = train_one(
            seed, sessions=sessions, split_of=split_of, verbose=0,
        )
        metrics = evaluate_seed(model, normalizer, thresholds, sessions, split_of)
        per_seed[seed] = metrics
        print(f"  seed {seed}: {metrics}")

    metric_names = ["roc_auc", "pr_auc", "f1_score", "precision", "recall_sensitivity"]
    summary = {
        name: _mean_std([per_seed[seed][name] for seed in config.SEEDS])
        for name in metric_names
    }

    report = {
        "seeds": config.SEEDS,
        "operating_point": "classifier_prob_balanced (per-seed, calibrated on that seed's own validation predictions)",
        "per_seed": per_seed,
        "mean_std": summary,
    }
    print("\n" + json.dumps(report, indent=2))
    evaluate.save_metrics(report, "seed_variance")


if __name__ == "__main__":
    main()
