"""Label-scarcity ablation: since the literature review specifically flags
scarce abnormal (crash) labels as the central real-world constraint for this
kind of system, the most decision-relevant experiment isn't another
full-label ablation -- it's asking how Model A (joint hybrid) and Model B
(pure supervised, no reconstruction objective) each degrade as the amount of
LABELED crash-like training data shrinks: 100% -> 50% -> 25% -> 10%.

Design:
- Only the TRAINING split's crash-like (y=1) windows are subsampled. Normal
  (y=0) training windows are left untouched at every fraction -- Model A's
  reconstruction branch only ever trains on normal windows anyway
  (src/model.py: compute_sample_weights), so by construction it can't lose
  any training signal as crash labels shrink; only the classifier head (both
  models) sees fewer positive examples. This isolates exactly the effect the
  literature review's "scarce abnormal labels" framing is about.
- Validation and test splits are kept FULL/unchanged at every fraction --
  they represent evaluation, not training-data availability, and subsampling
  them too would just add threshold-calibration and metric noise on top of
  the effect being measured.
- Subsampling uses a single fixed random permutation of the positive-window
  indices (not four independent draws), so the 10% set is a strict subset of
  the 25% set, which is a subset of the 50% set, which is a subset of 100% --
  this makes the four points a genuine nested degradation curve rather than
  four unrelated random samples.
- Single seed (config.RANDOM_SEED) per fraction, not a multi-seed sweep --
  2 models x 4 fractions = 8 training runs is already the practical budget;
  treat this as a first-pass result, not the final multi-seed-averaged one
  (see changes.md for this caveat stated plainly).

Model A is evaluated three ways at each fraction: its classifier head alone
(apples-to-apples against Model B), its reconstruction branch alone (should
be roughly FRACTION-INVARIANT, since it never sees fewer normal windows --
this is the control that makes the experiment's logic checkable), and the
naive hybrid OR rule (does the recon backstop actually rescue degraded
classifier performance as labels shrink?)."""
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


def subsample_positive_windows(train_ds, fraction, seed):
    """Keeps ALL normal (y=0) windows and `fraction` of the crash-like (y=1)
    windows, chosen from a single fixed permutation so fractions nest."""
    rng = np.random.default_rng(seed)
    pos_idx = np.where(train_ds.y == 1)[0]
    neg_idx = np.where(train_ds.y == 0)[0]

    perm = rng.permutation(len(pos_idx))
    n_keep = max(1, round(fraction * len(pos_idx)))
    keep_pos = np.sort(pos_idx[perm[:n_keep]])
    keep_idx = np.sort(np.concatenate([neg_idx, keep_pos]))

    subsampled = manifest.Dataset(
        X_seq=train_ds.X_seq[keep_idx],
        X_aux=train_ds.X_aux[keep_idx],
        y=train_ds.y[keep_idx],
        session_id=train_ds.session_id[keep_idx],
        source=train_ds.source[keep_idx],
    )
    n_sessions_represented = len(set(train_ds.session_id[keep_pos].tolist()))
    return subsampled, n_keep, len(pos_idx), n_sessions_represented


def evaluate_model_a(model, normalizer, thresholds, test_ds):
    X_seq, X_aux = normalizer.transform(test_ds.X_seq, test_ds.X_aux)
    preds = model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
    crash_prob = preds["crash_prob"].ravel()
    recon_error = preds["recon_error"].ravel()

    hybrid_pred = (
        (crash_prob >= thresholds["classifier_prob_balanced"]) | (recon_error >= thresholds["recon_error"])
    ).astype(int)

    return {
        "classifier_head": evaluate.full_classification_metrics(
            test_ds.y, crash_prob, thresholds["classifier_prob_balanced"]
        ),
        "reconstruction_branch": evaluate.full_classification_metrics(
            test_ds.y, recon_error, thresholds["recon_error"]
        ),
        "hybrid_or_naive": evaluate.full_classification_metrics(
            test_ds.y, hybrid_pred.astype(float), 0.5
        ),
    }


def main():
    print("Loading sessions...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)

    train_ds_full = manifest.build_dataset(sessions, split_of, "train")
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")
    print(f"Full train set: {len(train_ds_full.y)} windows "
          f"({int((train_ds_full.y == 0).sum())} normal, {int((train_ds_full.y == 1).sum())} crash-like)")

    results = {}
    for fraction in FRACTIONS:
        key = f"{int(fraction * 100)}pct"
        print(f"\n=== Crash-label fraction: {fraction:.0%} ===")
        train_ds_sub, n_keep, n_total, n_sessions = subsample_positive_windows(
            train_ds_full, fraction, config.RANDOM_SEED
        )
        print(f"  Keeping {n_keep}/{n_total} crash-like training windows "
              f"(from {n_sessions} distinct sessions), "
              f"{int((train_ds_sub.y == 0).sum())} normal windows unchanged")

        print("  Training Model A (joint hybrid)...")
        model_a, norm_a, thresholds_a, _ = train_hybrid_from_datasets(
            config.RANDOM_SEED, train_ds_sub, val_ds, verbose=0,
        )
        model_a_results = evaluate_model_a(model_a, norm_a, thresholds_a, test_ds)

        print("  Training Model B (supervised only)...")
        model_b, norm_b, threshold_b, _ = train_classifier_only_from_datasets(
            config.RANDOM_SEED, train_ds_sub, val_ds, verbose=0,
        )
        X_seq_b, X_aux_b = norm_b.transform(test_ds.X_seq, test_ds.X_aux)
        test_crash_prob_b = model_b.predict({"seq": X_seq_b, "aux": X_aux_b}, verbose=0)["crash_prob"].ravel()
        model_b_results = evaluate.full_classification_metrics(test_ds.y, test_crash_prob_b, threshold_b)

        print(f"  Model A classifier head: ROC-AUC={model_a_results['classifier_head']['roc_auc']:.3f} "
              f"F1={model_a_results['classifier_head']['f1_score']:.3f}")
        print(f"  Model B:                 ROC-AUC={model_b_results['roc_auc']:.3f} "
              f"F1={model_b_results['f1_score']:.3f}")
        print(f"  Model A reconstruction:  ROC-AUC={model_a_results['reconstruction_branch']['roc_auc']:.3f} "
              "(expected ~fraction-invariant -- control check)")

        results[key] = {
            "fraction": fraction,
            "n_train_crash_windows_kept": n_keep,
            "n_train_crash_windows_full": n_total,
            "n_train_crash_sessions_represented": n_sessions,
            "model_a": model_a_results,
            "model_b": model_b_results,
        }

    report = {
        "description": (
            "Label-scarcity ablation: Model A (joint hybrid) vs Model B (pure supervised) as "
            "the fraction of LABELED crash-like training windows shrinks from 100% to 10%. "
            "Normal training windows are never subsampled. Single seed per fraction (not "
            "multi-seed averaged) -- see changes.md for this caveat."
        ),
        "fractions": FRACTIONS,
        "seed": config.RANDOM_SEED,
        "results": results,
    }
    print("\n" + json.dumps(report, indent=2))
    evaluate.save_metrics(report, "label_scarcity_experiment")


if __name__ == "__main__":
    main()
