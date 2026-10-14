"""ExperimentsToPerform.txt item 1: refines Round 3's window-level label-scarcity
ablation (scripts/label_scarcity_experiment.py) two ways:

1. Subsamples whole crash-like SESSIONS from the training pool, not individual
   windows. Round 3's window-level subsampling could (and did, at 10%) drop a
   session's positive windows piecemeal by chance, leaving an uncontrolled
   mix of "how many sessions" vs "how many windows per session" changing
   together. Session-level subsampling controls this directly: at fraction f,
   exactly round(f * n_train_crash_sessions) whole crash sessions are kept
   (with ALL their windows), the rest are dropped entirely.
2. Repeats over config.SEEDS (5 seeds) instead of one, reporting mean +/- std
   -- Round 3 was explicit that its single-seed, non-monotonic result could
   easily be noise; this is the follow-up that actually checks that.

Only Model A (joint hybrid) and Model B (pure supervised) are compared, per
the ask -- this is "the cleanest way to test whether hybrid learning helps
when fewer crash scenarios are available," without the extra reconstruction/
hybrid-rule variants cluttering the comparison (those are still computed as a
secondary control, same as Round 3, but the headline comparison is A vs B).

Reuses train_hybrid_from_datasets()/train_classifier_only_from_datasets() --
no training-loop code is duplicated. Session-level subsampling is implemented
by remapping dropped crash sessions to a throwaway split name and calling the
existing manifest.build_dataset(), rather than hand-rolling dataset
concatenation."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from src import config, io_loaders, preprocess, manifest, evaluate
from train import train_hybrid_from_datasets  # noqa: E402
from train_model_b import train_classifier_only_from_datasets  # noqa: E402

FRACTIONS = [1.0, 0.5, 0.25, 0.10]


def build_reduced_split(sessions, split_of, kept_crash_session_ids):
    """Returns a copy of split_of where train-split crash-like sessions NOT
    in kept_crash_session_ids are remapped away from "train" -- everything
    else (normal train sessions, val, test) is untouched."""
    reduced = dict(split_of)
    for s in sessions:
        if split_of.get(s.session_id) == "train" and s.label == 1 and s.session_id not in kept_crash_session_ids:
            reduced[s.session_id] = "excluded_by_label_scarcity"
    return reduced


def evaluate_model_a(model, normalizer, thresholds, test_ds):
    X_seq, X_aux = normalizer.transform(test_ds.X_seq, test_ds.X_aux)
    preds = model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
    crash_prob = preds["crash_prob"].ravel()
    recon_error = preds["recon_error"].ravel()
    return {
        "classifier_head": evaluate.full_classification_metrics(
            test_ds.y, crash_prob, thresholds["classifier_prob_balanced"]
        ),
        "reconstruction_branch": evaluate.full_classification_metrics(
            test_ds.y, recon_error, thresholds["recon_error"]
        ),
    }


def _mean_std(values):
    arr = np.array(values, dtype=np.float64)
    return {"mean": float(arr.mean()), "std": float(arr.std())}


def main():
    print("Loading sessions...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")

    train_crash_sessions = [
        s for s in sessions if split_of.get(s.session_id) == "train" and s.label == 1
    ]
    n_crash_sessions = len(train_crash_sessions)
    print(f"Train-split crash-like sessions available: {n_crash_sessions}")

    per_fraction_per_seed = {f"{int(f * 100)}pct": [] for f in FRACTIONS}

    for seed in config.SEEDS:
        rng = np.random.default_rng(seed)
        perm = rng.permutation(n_crash_sessions)
        permuted = [train_crash_sessions[i] for i in perm]

        for fraction in FRACTIONS:
            key = f"{int(fraction * 100)}pct"
            n_keep = max(1, round(fraction * n_crash_sessions))
            kept_ids = {s.session_id for s in permuted[:n_keep]}

            reduced_split = build_reduced_split(sessions, split_of, kept_ids)
            train_ds_sub = manifest.build_dataset(sessions, reduced_split, "train")

            print(f"\n=== seed {seed}, fraction {fraction:.0%}: "
                  f"{n_keep}/{n_crash_sessions} crash sessions, "
                  f"{len(train_ds_sub.y)} windows "
                  f"({int((train_ds_sub.y == 0).sum())} normal, {int((train_ds_sub.y == 1).sum())} crash-like) ===")

            model_a, norm_a, thresholds_a, _ = train_hybrid_from_datasets(
                seed, train_ds_sub, val_ds, verbose=0,
            )
            model_a_results = evaluate_model_a(model_a, norm_a, thresholds_a, test_ds)

            model_b, norm_b, threshold_b, _ = train_classifier_only_from_datasets(
                seed, train_ds_sub, val_ds, verbose=0,
            )
            X_seq_b, X_aux_b = norm_b.transform(test_ds.X_seq, test_ds.X_aux)
            test_crash_prob_b = model_b.predict({"seq": X_seq_b, "aux": X_aux_b}, verbose=0)["crash_prob"].ravel()
            model_b_results = evaluate.full_classification_metrics(test_ds.y, test_crash_prob_b, threshold_b)

            print(f"  Model A clf: ROC-AUC={model_a_results['classifier_head']['roc_auc']:.3f} "
                  f"F1={model_a_results['classifier_head']['f1_score']:.3f} | "
                  f"Model B: ROC-AUC={model_b_results['roc_auc']:.3f} F1={model_b_results['f1_score']:.3f}")

            per_fraction_per_seed[key].append({
                "seed": seed,
                "n_crash_sessions_kept": n_keep,
                "n_train_windows": int(len(train_ds_sub.y)),
                "n_train_crash_windows": int((train_ds_sub.y == 1).sum()),
                "model_a_classifier_roc_auc": model_a_results["classifier_head"]["roc_auc"],
                "model_a_classifier_f1": model_a_results["classifier_head"]["f1_score"],
                "model_a_reconstruction_roc_auc": model_a_results["reconstruction_branch"]["roc_auc"],
                "model_b_roc_auc": model_b_results["roc_auc"],
                "model_b_f1": model_b_results["f1_score"],
            })

    summary = {}
    for key, runs in per_fraction_per_seed.items():
        summary[key] = {
            "n_crash_sessions_kept": runs[0]["n_crash_sessions_kept"],
            "n_crash_sessions_total": n_crash_sessions,
            "model_a_classifier_roc_auc": _mean_std([r["model_a_classifier_roc_auc"] for r in runs]),
            "model_a_classifier_f1": _mean_std([r["model_a_classifier_f1"] for r in runs]),
            "model_a_reconstruction_roc_auc": _mean_std([r["model_a_reconstruction_roc_auc"] for r in runs]),
            "model_b_roc_auc": _mean_std([r["model_b_roc_auc"] for r in runs]),
            "model_b_f1": _mean_std([r["model_b_f1"] for r in runs]),
        }

    report = {
        "description": (
            "Session-level label-scarcity ablation, 5 seeds: Model A (joint hybrid) vs Model B "
            "(pure supervised) as the fraction of train-split crash-like SESSIONS (not windows) "
            "shrinks from 100% to 10%. Whole sessions are kept/dropped together; normal-session "
            "windows are never touched; val/test splits are full and unchanged."
        ),
        "fractions": FRACTIONS,
        "seeds": config.SEEDS,
        "n_train_crash_sessions_total": n_crash_sessions,
        "summary_mean_std": summary,
        "per_seed_runs": per_fraction_per_seed,
    }
    print("\n" + json.dumps(summary, indent=2))
    evaluate.save_metrics(report, "label_scarcity_session_level_experiment")


if __name__ == "__main__":
    main()
