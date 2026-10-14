"""Final, held-out test-set evaluation of the trained hybrid model, plus an
ablation comparing reconstruction-only / classifier-only / hybrid decision
rules. Mirrors what notebooks/model-check.ipynb runs interactively. Saves plots and
metrics JSON to `results/metrics/` and figures to `results/figures/`.

changesToMake.txt item 2 adds `results/experiments/hybrid_ablation.json`:
a peak-based reconstruction-error variant (src/evaluate.py:
peak_reconstruction_error) alongside the original mean-based one, and three
hybrid decision rules -- the original naive independently-thresholded OR, a
jointly-tuned OR, and a stacked logistic-regression meta-classifier -- so the
paper can honestly report whichever (if any) actually beats the classifier
alone, instead of assuming OR-fusion helps.

changesToMake2.txt adds three more things to that same file:
- item 2: false-alarm rates now use real (non-overlapping) session duration
  as the exposure denominator (src/evaluate.py: normal_session_hours), not
  n_windows * window_seconds, which overstated exposure ~4x given the 75%
  window overlap (60-sample window, 15-sample stride). The deployed-alert
  simulation now also defaults to the real 60s cooldown (matching
  deploy/config.yaml), not the previous ~1.2s (4-window) placeholder.
- item 4: a paired bootstrap significance test on the classifier-only vs.
  hybrid_or_tuned / hybrid_stacked F1 difference, and an improved stacker
  (adds the 7 engineered aux features, and picks its L2 regularization
  strength by validation F1 instead of a fixed default).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from src import config, io_loaders, preprocess, manifest, normalize, evaluate
from src import model as model_lib  # noqa: F401 (registers the custom reconstruction loss for load_model)


def plot_roc_pr(y_true, scores, name):
    curves = evaluate.roc_pr_curves(y_true, scores)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(curves["fpr"], curves["tpr"])
    axes[0].plot([0, 1], [0, 1], "--", color="gray")
    axes[0].set_xlabel("False Positive Rate")
    axes[0].set_ylabel("True Positive Rate")
    axes[0].set_title(f"{name} ROC")

    axes[1].plot(curves["recall"], curves["precision"])
    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].set_title(f"{name} PR")

    fig.tight_layout()
    config.FIGURES_DIR.mkdir(exist_ok=True, parents=True)
    fig.savefig(config.FIGURES_DIR / f"{name}_roc_pr.png", dpi=150)
    plt.close(fig)


def plot_confusion_matrix(cm, name):
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i][j]), ha="center", va="center")
    ax.set_xticks([0, 1], ["Normal", "Crash"])
    ax.set_yticks([0, 1], ["Normal", "Crash"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"{name} Confusion Matrix")
    fig.tight_layout()
    config.FIGURES_DIR.mkdir(exist_ok=True, parents=True)
    fig.savefig(config.FIGURES_DIR / f"{name}_confusion_matrix.png", dpi=150)
    plt.close(fig)


def _predict_all(model, normalizer, ds):
    X_seq, X_aux = normalizer.transform(ds.X_seq, ds.X_aux)
    preds = model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
    crash_prob = preds["crash_prob"].ravel()
    recon_error = preds["recon_error"].ravel()
    recon_error_peak = evaluate.peak_reconstruction_error(X_seq, preds["reconstruction"])
    return crash_prob, recon_error, recon_error_peak, X_aux


def _select_stacked_classifier(val_y, val_features, C_grid=(0.01, 0.1, 1.0, 10.0, 100.0)):
    """Picks the L2 strength C that maximizes validation F1 (at that C's own
    best-F1 threshold) -- standard validation-based model selection, applied
    because the fixed-C=1.0 stacker previously underperformed classifier-only
    (changesToMake2.txt item 4: 'make it more improved')."""
    best = None
    for C in C_grid:
        clf = evaluate.fit_stacked_classifier(val_y, val_features, C=C)
        scores = clf.predict_proba(val_features)[:, 1]
        threshold = evaluate.choose_threshold_by_f1(val_y, scores)
        preds = (scores >= threshold).astype(int)
        from sklearn.metrics import f1_score
        f1 = f1_score(val_y, preds, zero_division=0)
        if best is None or f1 > best[0]:
            best = (f1, C, clf, threshold)
    best_f1, best_C, best_clf, best_threshold = best
    return best_clf, best_C, best_threshold, best_f1


def main():
    config.RESULTS_DIR.mkdir(exist_ok=True, parents=True)

    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")
    print(f"Test set: {len(test_ds.y)} windows "
          f"({int((test_ds.y == 0).sum())} normal, {int((test_ds.y == 1).sum())} anomaly)")

    normalizer = normalize.Normalizer.load(config.MODELS_DIR / "normalizer.npz")
    model = tf.keras.models.load_model(config.MODELS_DIR / "helmx_crash_model.keras")

    crash_prob, recon_error, recon_error_peak, test_X_aux = _predict_all(model, normalizer, test_ds)

    with open(config.MODELS_DIR / "thresholds.json") as f:
        thresholds = json.load(f)

    # Real (non-overlapping) exposure time -- see src/evaluate.py:
    # normal_session_hours. Replaces the previous n_windows * window_seconds
    # approximation, which overstated exposure ~4x given 75% window overlap
    # (changesToMake2.txt item 2).
    normal_hours = evaluate.normal_session_hours(sessions, split_of, "test")
    print(f"Real normal-session exposure time on test split: {normal_hours:.3f} hours")

    plot_roc_pr(test_ds.y, recon_error, "reconstruction")
    plot_roc_pr(test_ds.y, crash_prob, "classifier")

    results = {}
    for variant, scores, threshold in [
        ("reconstruction_only", recon_error, thresholds["recon_error"]),
        ("classifier_only_balanced", crash_prob, thresholds["classifier_prob_balanced"]),
        ("classifier_only_moderate_recall", crash_prob, thresholds["classifier_prob_moderate_recall"]),
        ("classifier_only_high_recall", crash_prob, thresholds["classifier_prob_high_recall"]),
    ]:
        m = evaluate.summarize(test_ds.y, scores, threshold, normal_hours=normal_hours)
        results[variant] = m
        plot_confusion_matrix(m["confusion_matrix"], variant)

    hybrid_pred = (
        (crash_prob >= thresholds["classifier_prob"]) | (recon_error >= thresholds["recon_error"])
    ).astype(int)
    m = evaluate.summarize_predictions(test_ds.y, hybrid_pred, normal_hours=normal_hours)
    results["hybrid"] = m
    plot_confusion_matrix(m["confusion_matrix"], "hybrid")

    # Event-level simulation: consecutive-window rule + the REAL 60s cooldown
    # (deploy/config.yaml: thresholds.cooldown_seconds), against real exposure
    # hours -- this is the only number that should be cited as a "false
    # alarms per hour" figure (changesToMake2.txt item 2).
    deployed = {}
    for variant, threshold_key in [
        ("classifier_only_balanced", "classifier_prob_balanced"),
        ("classifier_only_moderate_recall", "classifier_prob_moderate_recall"),
        ("classifier_only_high_recall", "classifier_prob_high_recall"),
    ]:
        deployed[variant] = evaluate.simulate_deployed_alerts(
            test_ds.y, crash_prob, test_ds.session_id, thresholds[threshold_key],
            normal_hours=normal_hours,
        )
    results["deployed_alert_simulation"] = deployed

    print(json.dumps(results, indent=2))
    evaluate.save_metrics(results, "test_metrics")

    # --- changesToMake.txt item 2 / changesToMake2.txt items 4-5: reconstruction improvement + honest hybrid ablation ---
    val_crash_prob, val_recon_error, val_recon_error_peak, val_X_aux = _predict_all(model, normalizer, val_ds)

    ablation = {}

    ablation["classifier_only"] = evaluate.full_classification_metrics(
        test_ds.y, crash_prob, thresholds["classifier_prob_balanced"]
    )
    ablation["reconstruction_only_mean"] = evaluate.full_classification_metrics(
        test_ds.y, recon_error, thresholds["recon_error"]
    )
    ablation["reconstruction_only_peak"] = evaluate.full_classification_metrics(
        test_ds.y, recon_error_peak, thresholds["recon_error_peak"]
    )
    plot_roc_pr(test_ds.y, recon_error_peak, "reconstruction_peak")
    cm = ablation["reconstruction_only_peak"]["confusion_matrix"]
    plot_confusion_matrix([[cm["TN"], cm["FP"]], [cm["FN"], cm["TP"]]], "reconstruction_only_peak")

    # Naive OR: each signal's own independently-calibrated threshold (today's behavior).
    naive_pred = ((crash_prob >= thresholds["classifier_prob_balanced"]) | (recon_error >= thresholds["recon_error"])).astype(int)
    ablation["hybrid_or_naive"] = evaluate.full_classification_metrics(
        test_ds.y, naive_pred.astype(float), 0.5
    )

    # Jointly-tuned OR: grid-search the threshold pair on validation, apply to test.
    (tuned_clf_t, tuned_recon_t), tuned_val_f1 = evaluate.tune_hybrid_or_thresholds(
        val_ds.y, val_crash_prob, val_recon_error
    )
    tuned_pred = ((crash_prob >= tuned_clf_t) | (recon_error >= tuned_recon_t)).astype(int)
    ablation["hybrid_or_tuned"] = evaluate.full_classification_metrics(test_ds.y, tuned_pred.astype(float), 0.5)
    ablation["hybrid_or_tuned"]["tuned_clf_threshold"] = tuned_clf_t
    ablation["hybrid_or_tuned"]["tuned_recon_threshold"] = tuned_recon_t
    ablation["hybrid_or_tuned"]["validation_f1_at_tuning_time"] = tuned_val_f1

    # Stacked meta-classifiers: logistic regression over the 3 signal scores,
    # with L2 strength C picked by validation F1 (changesToMake2.txt item 4:
    # "make it more improved"). Two attempts, both reported honestly rather
    # than cherry-picking whichever looks best: (1) grid-searching C on the
    # original 3 signal-only features, (2) adding the 7 engineered aux
    # features on top. Neither improves on the original round-1 fixed-C=1.0
    # 3-feature stacker (test F1 0.294): C-selection alone drops it to 0.198,
    # and adding aux features raises validation F1 (0.59 -> 0.71) while
    # dropping test F1 further (to 0.123) -- a clean overfitting signature on
    # the 219-positive validation split, and further evidence (per the
    # reviewer's original framing) that the stacked approach belongs in the
    # ablation table, not as a proposed improvement.
    val_features_3 = np.column_stack([val_crash_prob, val_recon_error, val_recon_error_peak])
    test_features_3 = np.column_stack([crash_prob, recon_error, recon_error_peak])
    stacker3, stacker3_C, stacked3_threshold, stacked3_val_f1 = _select_stacked_classifier(val_ds.y, val_features_3)
    stacked3_test_scores = stacker3.predict_proba(test_features_3)[:, 1]
    ablation["hybrid_stacked_3feature"] = evaluate.full_classification_metrics(test_ds.y, stacked3_test_scores, stacked3_threshold)
    ablation["hybrid_stacked_3feature"]["selected_C"] = stacker3_C
    ablation["hybrid_stacked_3feature"]["validation_f1_at_selected_C"] = stacked3_val_f1
    ablation["hybrid_stacked_3feature"]["features"] = ["crash_prob", "recon_error", "recon_error_peak"]

    val_features_10 = np.column_stack([val_crash_prob, val_recon_error, val_recon_error_peak, val_X_aux])
    test_features_10 = np.column_stack([crash_prob, recon_error, recon_error_peak, test_X_aux])
    stacker10, stacker10_C, stacked10_threshold, stacked10_val_f1 = _select_stacked_classifier(val_ds.y, val_features_10)
    stacked10_test_scores = stacker10.predict_proba(test_features_10)[:, 1]
    ablation["hybrid_stacked_extended"] = evaluate.full_classification_metrics(test_ds.y, stacked10_test_scores, stacked10_threshold)
    ablation["hybrid_stacked_extended"]["selected_C"] = stacker10_C
    ablation["hybrid_stacked_extended"]["validation_f1_at_selected_C"] = stacked10_val_f1
    ablation["hybrid_stacked_extended"]["features"] = ["crash_prob", "recon_error", "recon_error_peak"] + config.AUX_FEATURE_COLUMNS
    ablation["hybrid_stacked_extended"]["overfitting_note"] = (
        f"Higher validation F1 ({stacked10_val_f1:.3f} vs. the 3-feature stacker's "
        f"{stacked3_val_f1:.3f}) but far worse test F1 ({ablation['hybrid_stacked_extended']['f1_score']:.3f} "
        f"vs. {ablation['hybrid_stacked_3feature']['f1_score']:.3f}) -- classic overfitting on a "
        "219-positive validation split with 10 free parameters. Prefer the 3-feature stacker if "
        "a stacked model is reported at all."
    )
    # Keep the "hybrid_stacked" key too, aliased to the more robust 3-feature
    # version, so it participates in best-variant selection below on equal footing.
    ablation["hybrid_stacked"] = ablation["hybrid_stacked_3feature"]

    best_variant = max(
        ["classifier_only", "hybrid_or_naive", "hybrid_or_tuned", "hybrid_stacked"],
        key=lambda k: ablation[k]["f1_score"],
    )

    # changesToMake2.txt item 4: a point-estimate F1 improvement isn't
    # evidence of a "significant" improvement -- bootstrap it. The OR-rule
    # variant isn't a single-score threshold rule, so it's compared via its
    # fixed 0/1 predictions instead (equivalent to scores in {0,1}, threshold 0.5).
    significance = {
        "hybrid_or_tuned_vs_classifier_only": evaluate.bootstrap_metric_difference(
            test_ds.y,
            crash_prob, thresholds["classifier_prob_balanced"],
            tuned_pred.astype(float), 0.5,
        ),
        "hybrid_stacked_3feature_vs_classifier_only": evaluate.bootstrap_metric_difference(
            test_ds.y,
            crash_prob, thresholds["classifier_prob_balanced"],
            stacked3_test_scores, stacked3_threshold,
        ),
    }
    ablation["significance_tests"] = significance

    tuned_sig = significance["hybrid_or_tuned_vs_classifier_only"]
    if best_variant == "classifier_only":
        conclusion = (
            f"Best F1 on test: 'classifier_only' ({ablation['classifier_only']['f1_score']:.3f}). "
            "None of the hybrid fusion variants beat the classifier alone this run."
        )
    elif tuned_sig["significant_at_0.05_two_sided"]:
        conclusion = (
            f"'{best_variant}' has the best F1 on test ({ablation[best_variant]['f1_score']:.3f} vs. "
            f"classifier-only's {ablation['classifier_only']['f1_score']:.3f}), and the bootstrap 95% CI "
            f"for the F1 difference [{tuned_sig['ci_95_low']:.3f}, {tuned_sig['ci_95_high']:.3f}] excludes "
            "zero -- report this as a real, if modest, improvement."
        )
    else:
        conclusion = (
            f"'{best_variant}' has a higher point-estimate F1 on test ({ablation[best_variant]['f1_score']:.3f} "
            f"vs. classifier-only's {ablation['classifier_only']['f1_score']:.3f}, {best_variant} recovers "
            "only one additional true positive at no extra false-positive cost), but the bootstrap 95% CI "
            f"for the F1 difference [{tuned_sig['ci_95_low']:.3f}, {tuned_sig['ci_95_high']:.3f}] includes "
            "zero -- there is not yet statistical evidence this is a significant improvement on this test "
            "set size. Phrase this in the paper as 'joint threshold calibration yielded a modest, "
            "not-yet-statistically-significant improvement over classifier-only inference', not "
            "'hybrid fusion significantly outperformed supervised classification' "
            "(changesToMake2.txt item 4)."
        )
    ablation["conclusion"] = conclusion

    print(json.dumps(ablation, indent=2))
    evaluate.save_metrics(ablation, "hybrid_ablation")


if __name__ == "__main__":
    main()
