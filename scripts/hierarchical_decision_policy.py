"""User request following Round 7's external scooter-dataset evaluation:
"redesign the decision policy, not the feature-learning architecture" --
specifically a hierarchical rule where the supervised classifier is primary
and the reconstruction branch acts as a fallback/OOD-escalation channel,
rather than the deployed naive OR (`crash_prob > t1 OR recon_error > t2`,
both thresholds tuned independently) or Round 1/2's already-tried tuned-OR
(`tune_hybrid_or_thresholds`: a single JOINT recon threshold, always active).

`src/evaluate.py: apply_hierarchical_policy`/`tune_hierarchical_thresholds`
implement this: the classifier decides alone in its confident zones
(>= t_high crash, <= t_low normal); only the ambiguous middle band and the
confident-normal band consult reconstruction, and at two DIFFERENT
thresholds -- overriding a confident-normal call requires the stricter
t_recon_escalate ("this doesn't look like anything I've seen"), while
tipping an already-ambiguous call only needs t_recon_ambiguous. This is a
genuine structural change, not just a renamed OR: t_low == t_high collapses
it to exactly tuned-OR, so the search space strictly contains tuned-OR's.

CRITICAL constraint, per the user's explicit instruction: **all four
thresholds are calibrated on the VALIDATION split only.** The external
scooter dataset (already inspected once in Round 7) must never be touched
during calibration -- it is evaluated here, with the frozen thresholds,
exactly once, as a pure held-out check, never as a tuning set. This script
recomputes the naive-OR and tuned-OR baselines fresh (not reused from older
files) so all four policies in the comparison table are scored by identical
code on identical held-out data -- the same discipline Round 6 applied to
its B/A0 rerun.

Deployed model, normalizer, and models/thresholds.json are read but never
written to -- this is purely an evaluation/comparison exercise. If a policy
here is ever adopted for real deployment, deploy/crash_monitor.py's decision
logic would need to be updated separately and deliberately, not as a side
effect of running this script."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import tensorflow as tf

from src import config, io_loaders, preprocess, manifest, evaluate, normalize
from src import model as model_lib  # noqa: F401 (registers custom layers for load_model)
from experiment_common import evaluate_variant, METRIC_NAMES  # noqa: E402
from external_test_scooter_dataset import load_external_scooter_sessions  # noqa: E402
from external_test_simra_dataset import load_external_simra_sessions  # noqa: E402

N_GRID = 12


def _binary_metrics(y_true, binary_pred, session_ids):
    return evaluate_variant(y_true, binary_pred.astype(float), session_ids, threshold=0.5)


def _binary_deployed_alerts(y_true, binary_pred, session_ids, normal_hours=None):
    return evaluate.simulate_deployed_alerts(
        y_true, binary_pred.astype(float), session_ids, 0.5, normal_hours=normal_hours,
    )


def main():
    print("Loading sessions (train/val/test split, same frozen RANDOM_SEED as the deployed model)...")
    sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    split_of = manifest.assign_splits(sessions)
    val_ds = manifest.build_dataset(sessions, split_of, "val")
    test_ds = manifest.build_dataset(sessions, split_of, "test")
    print(f"Val: {len(val_ds.y)} windows, Test: {len(test_ds.y)} windows")

    normalizer = normalize.Normalizer.load(config.MODELS_DIR / "normalizer.npz")
    model = tf.keras.models.load_model(config.MODELS_DIR / "helmx_crash_model.keras")
    with open(config.MODELS_DIR / "thresholds.json") as f:
        deployed_thresholds = json.load(f)

    def predict(ds):
        X_seq, X_aux = normalizer.transform(ds.X_seq, ds.X_aux)
        out = model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
        return out["crash_prob"].ravel(), out["recon_error"].ravel()

    clf_val, recon_val = predict(val_ds)
    clf_test, recon_test = predict(test_ds)

    print("\nCalibrating thresholds on VALIDATION ONLY...")
    (naive_t_clf, naive_t_recon) = (
        deployed_thresholds["classifier_prob_balanced"], deployed_thresholds["recon_error"],
    )
    (tuned_t_clf, tuned_t_recon), tuned_val_f1 = evaluate.tune_hybrid_or_thresholds(
        val_ds.y, clf_val, recon_val, n_grid=50,
    )
    (h_t_low, h_t_high, h_t_amb, h_t_esc), hier_val_f1 = evaluate.tune_hierarchical_thresholds(
        val_ds.y, clf_val, recon_val, n_grid=N_GRID,
    )
    print(f"  naive OR (deployed):  t_clf={naive_t_clf:.4f} t_recon={naive_t_recon:.4f}")
    print(f"  tuned OR:             t_clf={tuned_t_clf:.4f} t_recon={tuned_t_recon:.4f} (val F1={tuned_val_f1:.4f})")
    print(f"  hierarchical:         t_low={h_t_low:.4f} t_high={h_t_high:.4f} "
          f"t_recon_ambiguous={h_t_amb:.4f} t_recon_escalate={h_t_esc:.4f} (val F1={hier_val_f1:.4f})")

    def evaluate_policies(y_true, clf_scores, recon_scores, session_ids, normal_hours=None):
        classifier_pred = clf_scores >= naive_t_clf
        recon_pred = recon_scores >= naive_t_recon
        naive_or_pred = classifier_pred | recon_pred
        tuned_or_pred = (clf_scores >= tuned_t_clf) | (recon_scores >= tuned_t_recon)
        hier_pred = evaluate.apply_hierarchical_policy(
            clf_scores, recon_scores, h_t_low, h_t_high, h_t_amb, h_t_esc,
        )

        results = {
            "classifier_alone": evaluate_variant(y_true, clf_scores, session_ids, naive_t_clf),
            "reconstruction_alone": evaluate_variant(y_true, recon_scores, session_ids, naive_t_recon),
            "naive_or_deployed": _binary_metrics(y_true, naive_or_pred, session_ids),
            "tuned_or": _binary_metrics(y_true, tuned_or_pred, session_ids),
            "hierarchical": _binary_metrics(y_true, hier_pred, session_ids),
        }
        alerts = {
            "classifier_alone": evaluate.simulate_deployed_alerts(
                y_true, clf_scores, session_ids, naive_t_clf, normal_hours=normal_hours),
            "reconstruction_alone": evaluate.simulate_deployed_alerts(
                y_true, recon_scores, session_ids, naive_t_recon, normal_hours=normal_hours),
            "naive_or_deployed": _binary_deployed_alerts(y_true, naive_or_pred, session_ids, normal_hours),
            "tuned_or": _binary_deployed_alerts(y_true, tuned_or_pred, session_ids, normal_hours),
            "hierarchical": _binary_deployed_alerts(y_true, hier_pred, session_ids, normal_hours),
        }
        return results, alerts

    print("\n=== Evaluating on the TEST split (in-distribution, held out from calibration) ===")
    test_normal_hours = evaluate.normal_session_hours(sessions, split_of, "test")
    test_metrics, test_alerts = evaluate_policies(
        test_ds.y, clf_test, recon_test, test_ds.session_id, normal_hours=test_normal_hours,
    )
    for name, m in test_metrics.items():
        print(f"  {name}: ROC-AUC={m['roc_auc']} F1={m['f1_score']:.3f} "
              f"event_recall={m['event_level_session_recall']}")

    def evaluate_external(name, loader_fn):
        print(f"\n=== Evaluating on the FROZEN {name} dataset (pure held-out, NEVER used for tuning) ===")
        ext_sessions = loader_fn()
        n_ext_normal = sum(1 for s in ext_sessions if s.label == 0)
        ext_sessions_c = preprocess.canonicalize_all(ext_sessions)
        ext_split_of = {s.session_id: "external" for s in ext_sessions_c}
        ext_ds = manifest.build_dataset(ext_sessions_c, ext_split_of, "external")
        ext_session_seconds = evaluate.session_durations_seconds(ext_sessions_c)
        ext_label_of = {s.session_id: s.label for s in ext_sessions_c}
        ext_normal_hours = sum(
            sec for sid, sec in ext_session_seconds.items() if ext_label_of[sid] == 0
        ) / 3600.0
        clf_ext, recon_ext = predict(ext_ds)
        ext_metrics, ext_alerts = evaluate_policies(
            ext_ds.y, clf_ext, recon_ext, ext_ds.session_id, normal_hours=ext_normal_hours,
        )
        for pname, m in ext_metrics.items():
            print(f"  {pname}: ROC-AUC={m['roc_auc']} F1={m['f1_score']:.3f} "
                  f"event_recall={m['event_level_session_recall']}")
        return {
            "n_sessions": len(ext_sessions_c), "n_normal_sessions": n_ext_normal,
            "n_windows": int(len(ext_ds.y)), "normal_hours": ext_normal_hours,
            "window_level_metrics": ext_metrics, "event_level_deployed_alert_simulation": ext_alerts,
            "note": "Same frozen thresholds as calibrated on validation above -- zero recalibration on this data.",
        }

    scooter_result = evaluate_external("external scooter (Round 7)", load_external_scooter_sessions)
    simra_result = evaluate_external(
        "external SimRa bicycle near-miss (qualitatively different -- see its ATTRIBUTION.md)",
        load_external_simra_sessions,
    )

    report = {
        "description": (
            "Classifier-primary, reconstruction-fallback ('hierarchical') decision policy, "
            "compared against classifier-alone, reconstruction-alone, the deployed naive OR "
            "rule, and a freshly-tuned OR rule -- all four thresholds of the hierarchical "
            "policy (and the tuned-OR pair) calibrated on VALIDATION ONLY, then applied "
            "unchanged to the held-out test split and the Round 7 external scooter dataset "
            "(never used for any tuning, evaluated here exactly once as a pure check)."
        ),
        "thresholds": {
            "naive_or_deployed": {"t_clf": naive_t_clf, "t_recon": naive_t_recon},
            "tuned_or": {"t_clf": tuned_t_clf, "t_recon": tuned_t_recon, "val_f1": tuned_val_f1},
            "hierarchical": {
                "t_low": h_t_low, "t_high": h_t_high,
                "t_recon_ambiguous": h_t_amb, "t_recon_escalate": h_t_esc,
                "val_f1": hier_val_f1,
            },
        },
        "test_split": {
            "n_windows": int(len(test_ds.y)), "normal_hours": test_normal_hours,
            "window_level_metrics": test_metrics, "event_level_deployed_alert_simulation": test_alerts,
        },
        "external_scooter_dataset": scooter_result,
        "external_simra_dataset": simra_result,
    }
    evaluate.save_metrics(report, "hierarchical_decision_policy")
    print("\nSaved results/experiments/hierarchical_decision_policy.json")


if __name__ == "__main__":
    main()
