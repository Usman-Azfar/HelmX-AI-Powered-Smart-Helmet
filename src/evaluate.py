import json

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    precision_recall_curve, roc_curve, roc_auc_score, average_precision_score,
    confusion_matrix, precision_score, recall_score, f1_score, fbeta_score,
    accuracy_score, balanced_accuracy_score, matthews_corrcoef,
    mean_squared_error, mean_absolute_error,
)

from . import config


def choose_threshold_by_recall(y_true, scores, target_recall=0.95):
    """Picks the lowest-score threshold that still hits target_recall on the
    given (validation) split, biasing toward not missing crashes over
    avoiding false alarms."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    precision, recall = precision[:-1], recall[:-1]
    candidates = np.where(recall >= target_recall)[0]
    if len(candidates) == 0:
        return float(thresholds[np.argmax(recall)])
    best = candidates[np.argmax(precision[candidates])]
    return float(thresholds[best])


def choose_threshold_by_f1(y_true, scores):
    """Picks the threshold maximizing F1 -- a balanced operating point, for
    deployments where a high-recall threshold's false-alarm rate would be
    impractical (e.g. spamming SMS alerts)."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    precision, recall = precision[:-1], recall[:-1]
    f1 = np.where((precision + recall) > 0, 2 * precision * recall / (precision + recall + 1e-12), 0.0)
    return float(thresholds[np.argmax(f1)])


def session_durations_seconds(sessions):
    """Real, non-overlapping recording duration per session, in seconds --
    from each session's total resampled sample count, not from windowed
    sample counts. changesToMake2.txt item 2: `n_windows * window_seconds`
    overstates real exposure time by about 4x here (60-sample window,
    15-sample stride = 75% overlap), since the same riding time gets counted
    once per overlapping window instead of once."""
    return {s.session_id: len(s.df) / config.TARGET_RATE_HZ for s in sessions}


def normal_session_hours(sessions, split_of, split_name):
    """Real exposure time, in hours, of the whole normal-labeled *sessions*
    (not windows) assigned to `split_name` -- the correct false-alarm-rate
    denominator (changesToMake2.txt item 2), used in place of the previous
    `n_normal_windows * window_seconds` approximation."""
    durations = session_durations_seconds(sessions)
    total_seconds = sum(
        durations[s.session_id] for s in sessions
        if split_of.get(s.session_id) == split_name and s.label == 0
    )
    return total_seconds / 3600.0


def summarize_predictions(y_true, preds, normal_hours=None):
    cm = confusion_matrix(y_true, preds, labels=[0, 1])
    metrics = {
        "accuracy": float(accuracy_score(y_true, preds)),
        "precision": float(precision_score(y_true, preds, zero_division=0)),
        "recall": float(recall_score(y_true, preds, zero_division=0)),
        "f1": float(f1_score(y_true, preds, zero_division=0)),
        "confusion_matrix": cm.tolist(),
        "n_windows": int(len(y_true)),
    }

    if normal_hours is not None and normal_hours > 0:
        normal_mask = y_true == 0
        false_positives = int(((preds == 1) & normal_mask).sum())
        # NOT a real alert-rate: windows overlap 75%, and a window-level false
        # positive isn't necessarily an alert event (see simulate_deployed_alerts
        # for the corrected event-level rate). Diagnostic only.
        metrics["window_level_trigger_rate_per_hour"] = float(false_positives / normal_hours)

    return metrics


def summarize(y_true, scores, threshold, normal_hours=None):
    preds = (scores >= threshold).astype(int)
    metrics = summarize_predictions(y_true, preds, normal_hours=normal_hours)
    metrics["threshold"] = float(threshold)
    metrics["roc_auc"] = float(roc_auc_score(y_true, scores)) if len(set(y_true)) > 1 else None
    metrics["pr_auc"] = float(average_precision_score(y_true, scores)) if len(set(y_true)) > 1 else None
    return metrics


def simulate_deployed_alerts(y_true, scores, session_ids, threshold, consecutive=3,
                              cooldown_seconds=60.0, stride_seconds=None, normal_hours=None):
    """Approximates what deploy/crash_monitor.py actually does: an alert only
    fires after `consecutive` windows in a row score above threshold, then
    goes quiet for `cooldown_seconds` (default 60s, matching
    deploy/config.yaml: thresholds.cooldown_seconds -- changesToMake2.txt item
    2 flagged that this previously defaulted to ~4 windows/1.2s, nowhere near
    the real deployed cooldown). Window-level false-positive-rate (used by
    `summarize`) overstates real-world alarm frequency for two reasons:
    isolated false positives don't survive the consecutive-window
    requirement, and overlapping windows overstate exposure time -- this
    reports the metric that actually matters for a deployed device: how many
    *alert events* (~SMS messages) it would have sent per real hour of
    normal riding (`normal_hours`, computed from real session durations via
    `normal_session_hours`, not window counts)."""
    if stride_seconds is None:
        stride_seconds = config.STRIDE_SAMPLES / config.TARGET_RATE_HZ
    cooldown_windows = max(1, round(cooldown_seconds / stride_seconds))

    preds = (scores >= threshold).astype(int)
    order = np.arange(len(preds))

    session_alert_counts = {}
    streak = 0
    cooldown = 0
    prev_sid = None
    for i in order:
        sid = session_ids[i]
        if sid != prev_sid:
            streak, cooldown, prev_sid = 0, 0, sid
        streak = streak + 1 if preds[i] else 0
        if cooldown > 0:
            cooldown -= 1
        elif streak >= consecutive:
            session_alert_counts[sid] = session_alert_counts.get(sid, 0) + 1
            streak, cooldown = 0, cooldown_windows

    # A session counts as "anomaly" if ANY of its windows are labeled 1 -- with
    # per-window peak-severity relabeling (see manifest._windows_for_session),
    # most windows in a fall/near-fall session are actually 0, so this can't
    # just take one window's label as the session's.
    unique_sessions = {}
    for i in order:
        sid = session_ids[i]
        unique_sessions[sid] = max(unique_sessions.get(sid, 0), int(y_true[i]))

    normal_sessions = [sid for sid, label in unique_sessions.items() if label == 0]
    anomaly_sessions = [sid for sid, label in unique_sessions.items() if label == 1]

    alerted_anomaly = sum(1 for sid in anomaly_sessions if session_alert_counts.get(sid, 0) > 0)
    total_false_alerts = sum(session_alert_counts.get(sid, 0) for sid in normal_sessions)

    result = {
        "session_recall": alerted_anomaly / len(anomaly_sessions) if anomaly_sessions else None,
        "n_anomaly_sessions": len(anomaly_sessions),
        "n_normal_sessions": len(normal_sessions),
        "total_false_alert_events": total_false_alerts,
        "cooldown_seconds": cooldown_seconds,
        "cooldown_windows": cooldown_windows,
    }
    if normal_hours is not None and normal_hours > 0:
        result["normal_exposure_hours"] = normal_hours
        result["false_alerts_per_hour"] = total_false_alerts / normal_hours
    return result


def recall_at_specificity(y_true, scores, target_specificity=0.95):
    """Recall (sensitivity) at the least-permissive threshold that still
    achieves >= target_specificity on the ROC curve -- the updated
    ExperimentsToPerform.txt's "recall at fixed specificity" primary metric,
    reported alongside ROC-AUC/PR-AUC/F1 so a headline AUC gain can't hide a
    collapse in usable recall at a real deployment-like operating point."""
    y_true = np.asarray(y_true)
    if len(set(y_true)) < 2:
        return {"recall": None, "specificity_achieved": None, "threshold": None}
    fpr, tpr, thresholds = roc_curve(y_true, scores)
    specificity = 1 - fpr
    valid = specificity >= target_specificity
    if not valid.any():
        return {"recall": 0.0, "specificity_achieved": float(specificity.max()), "threshold": None}
    idx = np.where(valid)[0][np.argmax(tpr[valid])]
    return {
        "recall": float(tpr[idx]),
        "specificity_achieved": float(specificity[idx]),
        "threshold": float(thresholds[idx]),
    }


def full_classification_metrics(y_true, scores, threshold, normal_hours=None):
    """The complete classification-metrics suite (confusion matrix, accuracy,
    precision, recall/sensitivity, specificity, F1, F2, balanced accuracy,
    MCC, ROC-AUC, PR-AUC) at one operating point -- for performance.md."""
    y_true = np.asarray(y_true)
    preds = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, preds, labels=[0, 1]).ravel()

    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    metrics = {
        "confusion_matrix": {"TP": int(tp), "TN": int(tn), "FP": int(fp), "FN": int(fn)},
        "accuracy": float(accuracy_score(y_true, preds)),
        "precision": float(precision_score(y_true, preds, zero_division=0)),
        "recall_sensitivity": float(recall_score(y_true, preds, zero_division=0)),
        "specificity": float(specificity),
        "f1_score": float(f1_score(y_true, preds, zero_division=0)),
        "f2_score": float(fbeta_score(y_true, preds, beta=2, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, preds)),
        "matthews_corrcoef": float(matthews_corrcoef(y_true, preds)) if len(set(preds)) > 1 else 0.0,
        "roc_auc": float(roc_auc_score(y_true, scores)) if len(set(y_true)) > 1 else None,
        "pr_auc": float(average_precision_score(y_true, scores)) if len(set(y_true)) > 1 else None,
        "threshold": float(threshold),
        "n_windows": int(len(y_true)),
    }
    if normal_hours is not None and normal_hours > 0:
        # NOT a real alert-rate -- see simulate_deployed_alerts for the
        # corrected event-level rate (changesToMake2.txt item 2). Diagnostic
        # only: how often a raw window-level positive fires per real hour of
        # normal riding.
        metrics["window_level_trigger_rate_per_hour"] = float(fp / normal_hours)
    return metrics


def bootstrap_metric_difference(y_true, scores_a, threshold_a, scores_b, threshold_b,
                                 metric="f1", n_bootstrap=2000, seed=0):
    """Paired bootstrap over test windows: resamples window indices with
    replacement `n_bootstrap` times, recomputes `metric` for both fixed
    (score, threshold) decision rules ('a' = baseline, 'b' = candidate) on
    each resample, and returns the distribution of (metric_b - metric_a) plus
    a 95% CI. Answers changesToMake2.txt item 4's "we do not yet have
    statistical evidence for significant": a point-estimate F1 improvement
    (e.g. 0.333 -> 0.343) says nothing about whether that difference would
    hold on a different sample of the same underlying population -- this
    does, at least approximately, given the same fixed test set."""
    y_true = np.asarray(y_true)
    scores_a = np.asarray(scores_a)
    scores_b = np.asarray(scores_b)
    n = len(y_true)
    metric_fn = {"f1": f1_score, "precision": precision_score, "recall": recall_score}[metric]

    rng = np.random.default_rng(seed)
    diffs = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        idx = rng.integers(0, n, n)
        yt = y_true[idx]
        pa = (scores_a[idx] >= threshold_a).astype(int)
        pb = (scores_b[idx] >= threshold_b).astype(int)
        diffs[i] = metric_fn(yt, pb, zero_division=0) - metric_fn(yt, pa, zero_division=0)

    ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])
    return {
        "metric": metric,
        "n_bootstrap": n_bootstrap,
        "point_estimate_diff": float(metric_fn(y_true, (scores_b >= threshold_b).astype(int), zero_division=0)
                                      - metric_fn(y_true, (scores_a >= threshold_a).astype(int), zero_division=0)),
        "bootstrap_mean_diff": float(diffs.mean()),
        "ci_95_low": float(ci_low),
        "ci_95_high": float(ci_high),
        "fraction_of_resamples_b_not_better": float((diffs <= 0).mean()),
        "significant_at_0.05_two_sided": bool(ci_low > 0 or ci_high < 0),
    }


def reconstruction_error_metrics(X_true, X_pred, y_true=None):
    """MSE/RMSE/MAE of the decoder's reconstruction. If y_true is given, also
    breaks these down for normal vs. crash-like windows -- the whole point of
    the reconstruction head is that normal windows should reconstruct well
    and crash-like ones poorly."""
    def _metrics(true_block, pred_block):
        if len(true_block) == 0:
            return None
        true_flat = true_block.reshape(-1, true_block.shape[-1])
        pred_flat = pred_block.reshape(-1, pred_block.shape[-1])
        mse = float(mean_squared_error(true_flat, pred_flat))
        return {
            "mse": mse,
            "rmse": float(np.sqrt(mse)),
            "mae": float(mean_absolute_error(true_flat, pred_flat)),
        }

    result = {"overall": _metrics(X_true, X_pred)}
    if y_true is not None:
        y_true = np.asarray(y_true)
        result["normal_windows"] = _metrics(X_true[y_true == 0], X_pred[y_true == 0])
        result["crash_like_windows"] = _metrics(X_true[y_true == 1], X_pred[y_true == 1])
    return result


def reconstruction_error_distribution(recon_error, y_true):
    """Percentile distribution of the reconstruction-error (anomaly) score,
    split by class -- shows how separated the two distributions are, which is
    what the recon_error threshold in models/thresholds.json relies on."""
    y_true = np.asarray(y_true)

    def _stats(values):
        if len(values) == 0:
            return None
        return {
            "mean": float(np.mean(values)), "std": float(np.std(values)),
            "min": float(np.min(values)), "p25": float(np.percentile(values, 25)),
            "median": float(np.median(values)), "p75": float(np.percentile(values, 75)),
            "p95": float(np.percentile(values, 95)), "p99": float(np.percentile(values, 99)),
            "max": float(np.max(values)),
        }

    return {
        "normal_windows": _stats(recon_error[y_true == 0]),
        "crash_like_windows": _stats(recon_error[y_true == 1]),
    }


def detection_latency_stats(sessions, split_of, split_name, model, normalizer, threshold,
                             consecutive_windows=3):
    """Real, computed detection latency: time from the true onset of a crash
    to the moment the deployed 'N consecutive windows above threshold' rule
    would fire, using sessions with genuine per-timestep ground truth
    (currently only data/darus/ -- fall/near-fall only have the peak-severity
    heuristic label, not a true onset time, so they're excluded here)."""
    from . import manifest as manifest_mod

    latencies_seconds = []
    stride_seconds = config.STRIDE_SAMPLES / config.TARGET_RATE_HZ

    for s in sessions:
        if (split_of.get(s.session_id) != split_name or s.frame_labels is None
                or s.label != 1):
            continue
        seqs, aux, labels = manifest_mod._windows_for_session(s, config.WINDOW_SAMPLES, config.STRIDE_SAMPLES)
        if not seqs:
            continue

        onset_idx = next((i for i, l in enumerate(labels) if l == 1), None)
        if onset_idx is None:
            continue

        X_seq = np.stack(seqs).astype(np.float32)
        X_aux = np.array(aux, dtype=np.float32)
        X_seq_n, X_aux_n = normalizer.transform(X_seq, X_aux)
        scores = model.predict({"seq": X_seq_n, "aux": X_aux_n}, verbose=0)["crash_prob"].ravel()

        streak, fire_idx = 0, None
        for i, sc in enumerate(scores):
            streak = streak + 1 if sc >= threshold else 0
            if streak >= consecutive_windows:
                fire_idx = i
                break

        if fire_idx is not None and fire_idx >= onset_idx:
            latencies_seconds.append((fire_idx - onset_idx) * stride_seconds)

    if not latencies_seconds:
        return {"n_sessions_detected": 0, "n_sessions_evaluated": None, "mean_s": None,
                "median_s": None, "min_s": None, "max_s": None}
    return {
        "n_sessions_detected": len(latencies_seconds),
        "mean_s": float(np.mean(latencies_seconds)),
        "median_s": float(np.median(latencies_seconds)),
        "min_s": float(np.min(latencies_seconds)),
        "max_s": float(np.max(latencies_seconds)),
    }


def peak_reconstruction_error(seq_true, seq_pred):
    """Max-over-time (instead of mean-over-time-and-channel) reconstruction
    error: DaRUS/near-fall crash signatures are brief spikes inside a 1.2s
    window, so averaging over all 60 timesteps (the model's built-in
    `recon_error` output) dilutes a spike that may only be a few samples
    wide. Taking the worst single timestep instead should separate classes
    better -- see changes.md item 2."""
    per_step_se = np.mean(np.square(seq_true - seq_pred), axis=-1)  # (N, window)
    return np.max(per_step_se, axis=1)  # (N,)


def tune_hybrid_or_thresholds(y_true, clf_scores, recon_scores, n_grid=50):
    """Grid-searches a *joint* (clf_threshold, recon_threshold) pair to
    maximize F1 of the `clf >= t_clf OR recon >= t_recon` rule on the given
    (validation) split. The naive hybrid rule in scripts/evaluate_model.py
    instead reuses each signal's own independently-optimal threshold, which
    is exactly why OR-ing them in only adds false positives without gaining
    recall -- this jointly optimizes the pair so the recon signal only
    contributes where it doesn't cost more FPs than it's worth."""
    y_true = np.asarray(y_true)
    clf_candidates = np.unique(np.quantile(clf_scores, np.linspace(0, 1, n_grid)))
    recon_candidates = np.unique(np.quantile(recon_scores, np.linspace(0, 1, n_grid)))

    best_f1 = -1.0
    best = (float(clf_candidates[-1]), float(recon_candidates[-1]))
    for ct in clf_candidates:
        clf_pred = clf_scores >= ct
        for rt in recon_candidates:
            pred = (clf_pred | (recon_scores >= rt)).astype(int)
            f1 = f1_score(y_true, pred, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best = (float(ct), float(rt))
    return best, float(best_f1)


def apply_hierarchical_policy(clf_scores, recon_scores, t_low, t_high, t_recon_ambiguous, t_recon_escalate):
    """Classifier-primary, reconstruction-fallback decision rule (as opposed
    to the naive/tuned OR rules above, which always OR the two signals with
    ONE fixed recon threshold): windows the classifier is confident about
    (>= t_high, or <= t_low) are decided by the classifier alone; only the
    ambiguous middle band and the confident-normal band consult
    reconstruction, and at two DIFFERENT thresholds -- overriding a
    confident-normal classifier call ("this doesn't look like anything I've
    seen" escalation) requires t_recon_escalate, deliberately meant to be the
    stricter of the two, while tipping an already-ambiguous call only needs
    t_recon_ambiguous. Returns a boolean prediction array."""
    clf_scores = np.asarray(clf_scores)
    recon_scores = np.asarray(recon_scores)
    confident_crash = clf_scores >= t_high
    confident_normal = clf_scores <= t_low
    ambiguous = ~confident_crash & ~confident_normal

    pred = confident_crash.copy()
    pred |= confident_normal & (recon_scores >= t_recon_escalate)
    pred |= ambiguous & (recon_scores >= t_recon_ambiguous)
    return pred


def tune_hierarchical_thresholds(y_true, clf_scores, recon_scores, n_grid=12):
    """Grid-searches (t_low, t_high, t_recon_ambiguous, t_recon_escalate) to
    maximize F1 of apply_hierarchical_policy on the given (validation) split,
    subject to t_low <= t_high (the classifier's confident-crash/confident-
    normal zones can't invert) and t_recon_escalate >= t_recon_ambiguous (the
    escalation threshold that overrides a confident-normal call must be at
    least as strict as the one that merely tips an ambiguous call -- the
    hypothesis under test, not something to let the grid search violate
    silently). Setting t_low == t_high collapses this to exactly the
    tune_hybrid_or_thresholds rule (single shared recon threshold, always
    active), so this search structurally generalizes it -- meaning it can
    never score worse than tuned OR on the SAME validation objective; the
    informative comparison is what happens on held-out data (test split, and
    especially the frozen external test sets), not on validation itself."""
    y_true = np.asarray(y_true)
    clf_scores = np.asarray(clf_scores)
    recon_scores = np.asarray(recon_scores)

    clf_candidates = np.unique(np.quantile(clf_scores, np.linspace(0, 1, n_grid)))
    recon_candidates = np.unique(np.quantile(recon_scores, np.linspace(0, 1, n_grid)))

    best_f1 = -1.0
    best = (float(clf_candidates[-1]), float(clf_candidates[-1]),
            float(recon_candidates[-1]), float(recon_candidates[-1]))
    for t_low in clf_candidates:
        confident_normal = clf_scores <= t_low
        for t_high in clf_candidates:
            if t_high < t_low:
                continue
            confident_crash = clf_scores >= t_high
            ambiguous = ~confident_crash & ~confident_normal
            for t_amb in recon_candidates:
                escalate_candidates = recon_candidates[recon_candidates >= t_amb]
                for t_esc in escalate_candidates:
                    pred = confident_crash.copy()
                    pred |= confident_normal & (recon_scores >= t_esc)
                    pred |= ambiguous & (recon_scores >= t_amb)
                    f1 = f1_score(y_true, pred.astype(int), zero_division=0)
                    if f1 > best_f1:
                        best_f1 = f1
                        best = (float(t_low), float(t_high), float(t_amb), float(t_esc))
    return best, float(best_f1)


def fit_stacked_classifier(y_true, feature_matrix, C=1.0):
    """A small logistic-regression meta-classifier stacking the classifier
    probability, the (mean + peak) reconstruction errors, and (as of
    changesToMake2.txt item 4) the engineered aux features -- lets the
    hybrid decision learn how much to trust each signal instead of a fixed
    OR-rule, fit only on the validation split (never train/test). `C` (L2
    inverse regularization strength) is a free parameter so callers can
    select it by validation performance rather than assume a default is
    best -- see scripts/evaluate_model.py: _select_stacked_classifier."""
    clf = LogisticRegression(class_weight="balanced", max_iter=1000, C=C)
    clf.fit(feature_matrix, y_true)
    return clf


def roc_pr_curves(y_true, scores):
    fpr, tpr, _ = roc_curve(y_true, scores)
    precision, recall, _ = precision_recall_curve(y_true, scores)
    return {"fpr": fpr, "tpr": tpr, "precision": precision, "recall": recall}


def save_metrics(metrics, name):
    metric_names = {"test_metrics", "full_metrics", "model_b_metrics", "model_c_metrics", "seed_variance"}
    external_names = {
        "extended_false_alarm_evaluation", "external_test_scooter_dataset",
        "external_test_simra_dataset", "unseen_crash_experiment",
    }
    if name in metric_names:
        output_dir = config.METRICS_DIR
    elif name in external_names:
        output_dir = config.EXTERNAL_VALIDATION_DIR
    else:
        output_dir = config.EXPERIMENTS_DIR
    output_dir.mkdir(exist_ok=True, parents=True)
    path = output_dir / f"{name}.json"
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)
    return path
