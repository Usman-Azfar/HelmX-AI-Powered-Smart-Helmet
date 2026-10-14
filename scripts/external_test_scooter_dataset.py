"""ExperimentsToPerform.txt (rewritten again): the advisor's highest-priority
next step is an external, never-trained-on IMU dataset with real crash/fall
events on a two-wheeler-like vehicle, used ONLY as a test set (no retraining,
no threshold recalibration) -- if the supervised branch struggles while the
reconstruction branch stays useful, that reinforces the complementary-
robustness argument this project's own unseen-crash experiment already found
(results/external-validation/unseen_crash_experiment.json: classifier ROC-AUC 0.35, reconstruction
ROC-AUC 0.87 on excluded DaRUS data).

Two candidate datasets were named, ranked by the advisor:

1. "Dataset on personal mobility vehicle's regular riding and fall events"
   (Sanchez-Iborra, Bernal-Escobedo & Santa, Data in Brief 61, 2025,
   DOI 10.1016/j.dib.2025.111681), data hosted on Zenodo
   (jsanta-upct/scooter-riding v1.1, DOI 10.5281/zenodo.14887437, CC BY 4.0,
   verified via the Zenodo API -- access_right: open). ~62 MB zip,
   downloaded and used directly (small enough not to need the user's help).
   Electric scooter, phone-mounted on-board unit, 5 normal-riding sessions +
   9 controlled overturn/collision sessions. THIS IS THE ONE USED BELOW.
   See data/external_scooter_riding_raw/ATTRIBUTION.md for the full session
   breakdown and license details.

2. "Dataset on powered two wheelers fall and critical events detection"
   (Boubezoul, Dufour, Bouaziz, Larnaudie & Espie, Data in Brief 23, 2019,
   DOI 10.1016/j.dib.2019.103828) -- the advisor's motorcycle-specific
   second choice. **Checked before doing anything else, and found to be
   NOT independent data at all**: its four fall scenarios (slippery-road,
   leaning, roundabout, curve) and its near-fall/extreme-maneuver sessions
   match -- by sampling rate (1000 Hz / 0.001s steps), column names/units
   (Ax/Ay/Az in m/s^2, Rx/Ry/Rz in deg/s), and scenario names -- exactly
   this project's own `data/fall/` (fall-in-a-curve.csv, fall-in-a-leaning.csv,
   fall-in-a-roundabout.csv, fall-in-a-slippery-road.csv) and `data/near-fall/`
   folders, which are already part of the FROZEN TRAINING snapshot
   (the canonical training inputs under data/). Using it as an "external" test set would be invalid --
   the deployed model has already been trained on this exact data. This is
   the same kind of duplicate-data trap Round 4 hit with the STRIDE dataset
   (see scripts/extended_false_alarm_evaluation.py's docstring) -- caught
   here BEFORE any download/evaluation work was done on it, not after.
   **Not used. Reported to the user as a finding, not silently skipped.**

Evaluates the already-deployed Model A (classifier head + reconstruction
branch + the exact naive OR-fusion decision rule from
deploy/crash_monitor.py, using models/thresholds.json's existing values
unchanged) and Model B (scripts/train_model_b.py) -- no retraining, no
threshold recalibration on this new data, per the user's explicit
instruction."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import tensorflow as tf

from src import config, preprocess, manifest, evaluate, normalize
from src.io_loaders import Session
from src.resampling import resample_two_streams
from src import model as model_lib  # noqa: F401 (registers custom layers for load_model)
from experiment_common import evaluate_variant  # noqa: E402

EXTERNAL_DATA_DIR = config.DATA_DIR / "external_scooter_riding_raw"

CRASH_FOLDERS = {
    "4-Left  overturn", "5-Right overturn", "6-Front collisiion",
    "9-Right overturn", "10-Right overturn", "11-Left overturn",
    "12-Left overturn", "13-Front collision", "14-Front collision",
}


def load_external_scooter_sessions():
    """Standalone loader -- deliberately NOT wired into
    src/io_loaders.py: load_all_sessions(), so this evaluation-only data can
    never be silently pulled into the frozen training pipeline. The source
    CSVs use a `Timestamp,Milliseconds,X,Y,Z` layout (Milliseconds is
    monotonically increasing elapsed-ms across the whole file, confirmed by
    inspection -- not a per-second reset), a different Android sensor-logger
    format than the `seconds_elapsed,x,y,z` layout src/io_loaders.py:
    load_road_folder() expects, hence the separate loader rather than reusing
    it directly."""
    sessions = []
    for folder in sorted(p for p in EXTERNAL_DATA_DIR.iterdir() if p.is_dir()):
        acc_path, gyro_path = folder / "Accelerometer.csv", folder / "Gyroscope.csv"
        if not (acc_path.exists() and gyro_path.exists()):
            continue

        acc = pd.read_csv(acc_path)
        gyro = pd.read_csv(gyro_path)
        t_acc = acc["Milliseconds"].to_numpy(dtype=float) / 1000.0
        t_gyro = gyro["Milliseconds"].to_numpy(dtype=float) / 1000.0
        merged = resample_two_streams(
            t_acc, {"ax": acc["X"], "ay": acc["Y"], "az": acc["Z"]},
            t_gyro, {"gx": gyro["X"], "gy": gyro["Y"], "gz": gyro["Z"]},
        )
        if merged is None or len(merged) < config.WINDOW_SAMPLES:
            print(f"  skipping {folder.name}: too short after resampling")
            continue

        label = 1 if folder.name in CRASH_FOLDERS else 0
        session_id = "ext_scooter_" + folder.name.replace(" ", "_")
        sessions.append(Session(
            # Android TYPE_ACCELEROMETER/TYPE_GYROSCOPE convention (raw accel
            # includes gravity, gyro in rad/s) -- confirmed by inspection:
            # peak |accel| ~67 m/s^2 (~6.8g, plausible collision) and peak
            # |gyro| ~2.9 rad/s (~166 deg/s, plausible tumble rate) in a
            # collision session; interpreting gyro as already deg/s would
            # imply an implausibly gentle ~2.9 deg/s during a violent impact.
            session_id=session_id, source="external_scooter", label=label,
            gyro_in_deg_per_s=False, df=merged,
        ))
    return sessions


def _binary_rule_metrics(y_true, binary_pred, session_ids):
    """Wraps a hard 0/1 decision (the OR-fusion rule) as a score so
    evaluate_variant's threshold-based helpers work unchanged (threshold=0.5
    on a {0,1}-valued score reproduces exactly the same confusion matrix as
    scoring the boolean decision directly)."""
    return evaluate_variant(y_true, binary_pred.astype(float), session_ids, threshold=0.5)


def main():
    print(f"Loading external scooter sessions from {EXTERNAL_DATA_DIR} ...")
    sessions = load_external_scooter_sessions()
    n_normal = sum(1 for s in sessions if s.label == 0)
    n_crash = sum(1 for s in sessions if s.label == 1)
    print(f"Loaded {len(sessions)} sessions ({n_normal} normal, {n_crash} crash-like)")

    sessions = preprocess.canonicalize_all(sessions)
    label_of = {s.session_id: s.label for s in sessions}
    split_of = {s.session_id: "external" for s in sessions}
    ds = manifest.build_dataset(sessions, split_of, "external")
    print(f"Windows: {len(ds.y)} ({int((ds.y == 0).sum())} normal / {int((ds.y == 1).sum())} "
          f"crash-like -- crash-session windows weak-labeled via the same "
          f"top-{config.ANOMALY_TOP_FRACTION:.0%}-peak-severity heuristic used for fall/near-fall)")

    session_seconds = evaluate.session_durations_seconds(sessions)
    normal_seconds = sum(sec for sid, sec in session_seconds.items() if label_of[sid] == 0)
    normal_hours = normal_seconds / 3600.0

    normalizer = normalize.Normalizer.load(config.MODELS_DIR / "normalizer.npz")
    model_a = tf.keras.models.load_model(config.MODELS_DIR / "helmx_crash_model.keras")
    model_b = tf.keras.models.load_model(config.MODELS_DIR / "helmx_classifier_only.keras")
    with open(config.MODELS_DIR / "thresholds.json") as f:
        thresholds = json.load(f)
    with open(config.METRICS_DIR / "model_b_metrics.json") as f:
        model_b_threshold = json.load(f)["threshold_balanced"]

    X_seq, X_aux = normalizer.transform(ds.X_seq, ds.X_aux)
    preds_a = model_a.predict({"seq": X_seq, "aux": X_aux}, verbose=0)
    crash_prob_a = preds_a["crash_prob"].ravel()
    recon_error_a = preds_a["recon_error"].ravel()
    crash_prob_b = model_b.predict({"seq": X_seq, "aux": X_aux}, verbose=0)["crash_prob"].ravel()

    # The exact deployed decision rule (deploy/crash_monitor.py):
    # crash_prob > classifier_prob_balanced OR recon_error > recon_error threshold.
    hybrid_pred = (
        (crash_prob_a > thresholds["classifier_prob_balanced"])
        | (recon_error_a > thresholds["recon_error"])
    )

    signals = {
        "model_a_classifier": (crash_prob_a, thresholds["classifier_prob_balanced"]),
        "model_a_reconstruction": (recon_error_a, thresholds["recon_error"]),
        "model_b_classifier": (crash_prob_b, model_b_threshold),
    }

    metrics = {}
    deployed_alerts = {}
    for name, (scores, thresh) in signals.items():
        metrics[name] = evaluate_variant(ds.y, scores, ds.session_id, thresh)
        deployed_alerts[name] = evaluate.simulate_deployed_alerts(
            ds.y, scores, ds.session_id, thresh,
            normal_hours=normal_hours if normal_hours > 0 else None,
        )
        print(f"{name}: ROC-AUC={metrics[name]['roc_auc']:.3f} "
              f"event-level session_recall={deployed_alerts[name]['session_recall']} "
              f"false_alerts/hr={deployed_alerts[name].get('false_alerts_per_hour')}")

    metrics["hybrid_or_fusion_deployed_rule"] = _binary_rule_metrics(ds.y, hybrid_pred, ds.session_id)
    deployed_alerts["hybrid_or_fusion_deployed_rule"] = evaluate.simulate_deployed_alerts(
        ds.y, hybrid_pred.astype(float), ds.session_id, 0.5,
        normal_hours=normal_hours if normal_hours > 0 else None,
    )
    print(f"hybrid_or_fusion_deployed_rule: "
          f"event-level session_recall={deployed_alerts['hybrid_or_fusion_deployed_rule']['session_recall']} "
          f"false_alerts/hr={deployed_alerts['hybrid_or_fusion_deployed_rule'].get('false_alerts_per_hour')}")

    report = {
        "description": (
            "External, never-trained-on test: electric scooter riding + controlled overturn/"
            "collision sessions (Sanchez-Iborra, Bernal-Escobedo & Santa 2025, Zenodo "
            "jsanta-upct/scooter-riding v1.1, CC BY 4.0). Evaluated with the ALREADY DEPLOYED "
            "Model A (classifier + reconstruction + exact OR-fusion rule) and Model B -- no "
            "retraining, no threshold recalibration."
        ),
        "source_citation": (
            "Sanchez-Iborra, R., Bernal-Escobedo, L., & Santa, J. (2025). Dataset on personal "
            "mobility vehicle's regular riding and fall events. Data in Brief, 61, 111681. "
            "https://doi.org/10.1016/j.dib.2025.111681. Data: Zenodo, "
            "https://doi.org/10.5281/zenodo.14887437 (CC BY 4.0, verified via the Zenodo API)."
        ),
        "second_candidate_dataset_finding": (
            "The advisor's second-ranked dataset (Boubezoul et al. 2019, DOI "
            "10.1016/j.dib.2019.103828, motorcycle fall/critical-events) was checked BEFORE any "
            "download and found to be byte-signature-identical (1000 Hz sampling, exact column "
            "names/units, exact scenario names) to this project's own data/fall/ and "
            "data/near-fall/ folders, which are already part of the FROZEN TRAINING snapshot "
            "(the canonical training inputs under data/). It is NOT independent data and cannot be used as an external test "
            "set here -- using it would silently re-test the model on its own training data. "
            "Not used; reported as a finding rather than silently skipped."
        ),
        "vehicle_domain_note": (
            "Electric scooter with a phone-based on-board unit, not a helmet-mounted motorcycle "
            "IMU -- closer to HelmX's two-wheeler domain than car-based sources (CARLA, STRIDE) "
            "already used elsewhere in this project, but not an exact sensor-placement match."
        ),
        "n_sessions": len(sessions),
        "n_normal_sessions": n_normal,
        "n_crash_sessions": n_crash,
        "n_windows": int(len(ds.y)),
        "n_normal_windows": int((ds.y == 0).sum()),
        "n_crash_windows": int((ds.y == 1).sum()),
        "normal_riding_hours": normal_hours,
        "window_level_metrics": metrics,
        "event_level_deployed_alert_simulation": deployed_alerts,
    }
    print("\n" + json.dumps({k: v for k, v in report.items() if k not in
                              ("window_level_metrics", "event_level_deployed_alert_simulation")}, indent=2))
    print("\nWindow-level metrics:\n" + json.dumps(metrics, indent=2))
    print("\nEvent-level deployed-alert simulation:\n" + json.dumps(deployed_alerts, indent=2))
    evaluate.save_metrics(report, "external_test_scooter_dataset")


if __name__ == "__main__":
    main()
