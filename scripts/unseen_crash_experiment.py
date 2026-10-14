"""changesToMake.txt closing ask: an "unseen crash" experiment using data
imported from the web. Reuses the already-imported DaRUS ISO 13232 dataset
(https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi:10.18419/darus-3301)
as a genuinely unseen holdout, WITHOUT changing the real/deployed pipeline:

- The deployed model (scripts/train.py), Model C (scripts/train_model_c.py),
  and the multi-seed/hybrid-ablation scripts all still include DaRUS in the
  normal stratified train/val/test split -- unchanged.
- This script is additive only: it trains a SEPARATE, throwaway model on
  CARLA + road + fall + near-fall alone (DaRUS fully excluded from training
  and validation), then evaluates that model against ALL 39 DaRUS sessions
  (25 crash + 14 non_crash) as an externally-sourced, never-trained-on test
  set. The resulting model is saved under results/, never models/, so it can
  never be mistaken for or accidentally deployed as the real model.

This gives two honest, separately-labeled numbers for changes.md/performance.md:
"DaRUS in-distribution" (the real deployed model, DaRUS included in training)
vs. "DaRUS as unseen holdout" (this experiment, DaRUS excluded entirely)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import config, io_loaders, preprocess, manifest, evaluate
from train import train_one  # noqa: E402


def main():
    print("Loading sessions...")
    all_sessions = preprocess.canonicalize_all(io_loaders.load_all_sessions())
    non_darus = [s for s in all_sessions if s.source != "darus"]
    darus_sessions = [s for s in all_sessions if s.source == "darus"]
    print(f"Non-DaRUS sessions (train+val pool): {len(non_darus)}")
    print(f"DaRUS sessions (fully unseen test set): {len(darus_sessions)} "
          f"({sum(1 for s in darus_sessions if s.label == 1)} crash, "
          f"{sum(1 for s in darus_sessions if s.label == 0)} non_crash)")

    split_of = manifest.assign_splits(non_darus)
    for name in ("train", "val"):
        ds = manifest.build_dataset(non_darus, split_of, name)
        print(f"  {name}: {len(ds.y)} windows "
              f"({int((ds.y == 0).sum())} normal, {int((ds.y == 1).sum())} anomaly)")

    model, normalizer, thresholds, _history, _sessions, _split_of = train_one(
        config.RANDOM_SEED, sessions=non_darus, split_of=split_of,
    )

    experimental_models_dir = config.MODELS_DIR / "experimental"
    experimental_models_dir.mkdir(exist_ok=True, parents=True)
    model.save(experimental_models_dir / "unseen_experiment_model.keras")

    # Every DaRUS session is "unseen" -- no train/val/test split needed, just
    # window and score all of it.
    darus_split_of = {s.session_id: "unseen" for s in darus_sessions}
    unseen_ds = manifest.build_dataset(darus_sessions, darus_split_of, "unseen")
    print(f"Unseen DaRUS windows: {len(unseen_ds.y)} "
          f"({int((unseen_ds.y == 0).sum())} normal, {int((unseen_ds.y == 1).sum())} crash-like)")

    X_seq, X_aux = normalizer.transform(unseen_ds.X_seq, unseen_ds.X_aux)
    preds = model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
    crash_prob = preds["crash_prob"].ravel()
    recon_error = preds["recon_error"].ravel()
    recon_error_peak = evaluate.peak_reconstruction_error(X_seq, preds["reconstruction"])

    # Real (non-overlapping) exposure time from the non_crash DaRUS sessions'
    # actual durations -- see src/evaluate.py: normal_session_hours
    # (changesToMake2.txt item 2). Caveat: DaRUS non_crash sessions are short,
    # edge-padded simulation snippets (src/io_loaders.py: _pad_centered), not
    # continuous real-world riding, so even this corrected per-hour figure is
    # rougher here than on the main test set -- treat it as a diagnostic, not
    # a claim about real-world DaRUS-like riding conditions.
    normal_hours = evaluate.normal_session_hours(darus_sessions, darus_split_of, "unseen")
    print(f"Real normal (non_crash DaRUS) exposure time: {normal_hours:.4f} hours")

    report = {
        "description": (
            "Model trained on CARLA + road + fall + near-fall only (DaRUS fully excluded "
            "from training/validation), evaluated against all 39 DaRUS sessions as an "
            "unseen, externally-sourced (ISO 13232 collision-physics) test set."
        ),
        "n_train_val_sessions_non_darus": len(non_darus),
        "n_unseen_darus_sessions": len(darus_sessions),
        "n_unseen_windows": int(len(unseen_ds.y)),
        "normal_exposure_hours_caveat": (
            "DaRUS non_crash sessions are short, edge-padded simulation snippets, not "
            "continuous riding -- per-hour figures here are rougher than the main test set."
        ),
        "normal_exposure_hours": normal_hours,
        "thresholds_from_non_darus_validation": thresholds,
        "classifier_only": evaluate.full_classification_metrics(
            unseen_ds.y, crash_prob, thresholds["classifier_prob_balanced"], normal_hours
        ),
        "classifier_only_high_recall": evaluate.full_classification_metrics(
            unseen_ds.y, crash_prob, thresholds["classifier_prob_high_recall"], normal_hours
        ),
        "reconstruction_only_mean": evaluate.full_classification_metrics(
            unseen_ds.y, recon_error, thresholds["recon_error"], normal_hours
        ),
        "reconstruction_only_peak": evaluate.full_classification_metrics(
            unseen_ds.y, recon_error_peak, thresholds["recon_error_peak"], normal_hours
        ),
    }

    # Event-level simulation with the real 60s deployed cooldown (previously
    # defaulted to ~1.2s/4 windows -- changesToMake2.txt item 2, second issue).
    report["deployed_alert_simulation"] = {
        "classifier_only_balanced": evaluate.simulate_deployed_alerts(
            unseen_ds.y, crash_prob, unseen_ds.session_id, thresholds["classifier_prob_balanced"],
            normal_hours=normal_hours,
        ),
    }

    report["detection_latency_seconds_balanced"] = evaluate.detection_latency_stats(
        darus_sessions, darus_split_of, "unseen", model, normalizer,
        thresholds["classifier_prob_balanced"],
    )

    print(json.dumps(report, indent=2))
    evaluate.save_metrics(report, "unseen_crash_experiment")


if __name__ == "__main__":
    main()
