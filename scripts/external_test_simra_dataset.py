"""User request: a THIRD, independent two-wheeler external test set, to check
whether the reconstruction branch's OOD-generalization advantage (found on
DaRUS-holdout, Round 1, and the electric-scooter dataset, Round 7) is
reproducible beyond those two, or specific to them.

Data source: SimRa (github.com/simra-project/dataset), a crowdsourced bicycle
near-miss/ride dataset, Berlin, CC BY-NC 4.0. Chosen after a promising
same-domain candidate (Lee, Koo & Kim 2024, e-scooter pre-impact falls, CC BY
4.0 per Crossref) turned out to have no locatable public data repository
despite several search attempts -- flagged to the user rather than guessed
at further, per their explicit "tell me and provide a link" fallback
instruction from an earlier round. The user chose to proceed with SimRa,
used and reported honestly rather than treated as an equivalent substitute
-- see data/external_simra_bicycle_raw/ATTRIBUTION.md for the two important
caveats this carries and doesn't share with DaRUS/the scooter dataset:

1. SimRa's positive events are self-reported NEAR-MISSES (close passes,
   tailgating, near-dooring, etc.), not actual falls/collisions -- a milder,
   qualitatively different anomaly than DaRUS/scooter's real crash events.
2. It's a pedal bicycle, a bigger vehicle-domain gap from HelmX's motorcycle
   target than the electric scooter, AND its native accelerometer/gyroscope
   sampling rate is only ~4 Hz (measured directly, median inter-sample gap
   251ms) -- ~12x below this pipeline's 50 Hz target and far below every
   other source this project uses, meaning most of an analysis window's
   content here is interpolated, not genuinely resolved motion.

Both caveats mean this dataset's result should be read as "a third,
qualitatively different signal," not as a third repetition of the
crash-generalization test -- reported plainly, not glossed over.

Evaluates the already-deployed Model A (classifier + reconstruction + naive
OR rule) and Model B, unchanged -- no retraining, no threshold
recalibration, exactly like scripts/external_test_scooter_dataset.py."""
import json
import sys
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import tensorflow as tf

from src import config, preprocess, manifest, evaluate, normalize
from src.io_loaders import Session
from src.resampling import resample_uniform
from src import model as model_lib  # noqa: F401 (registers custom layers for load_model)
from experiment_common import evaluate_variant  # noqa: E402

EXTERNAL_DATA_DIR = config.DATA_DIR / "external_simra_bicycle_raw"
RIDE_COLUMNS = ["lat", "lon", "X", "Y", "Z", "timeStamp", "acc", "a", "b", "c",
                 "obsDistanceLeft1", "obsDistanceLeft2", "obsDistanceRight1", "obsDistanceRight2",
                 "obsClosePassEvent", "XL", "YL", "ZL", "RX", "RY", "RZ", "RC"]


def _parse_ride_file(path):
    """SimRa's file format: incident-annotation rows, a blank line, a
    "=========================" separator, then the ride-data section (its
    own CSV header + rows) -- not a plain CSV, hence a custom parser rather
    than pd.read_csv directly on the whole file."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    sep_idx = next((i for i, l in enumerate(lines) if l.startswith("=====")), None)
    if sep_idx is None:
        return None
    ride_lines = lines[sep_idx + 2:]  # skip the "=====" line and the ride-section's own header line
    ride_csv = "".join(ride_lines)
    df = pd.read_csv(StringIO(ride_csv), header=None, names=RIDE_COLUMNS, engine="python")
    df = df[["timeStamp", "X", "Y", "Z", "a", "b", "c"]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(df) < 2:
        return None
    df = df.sort_values("timeStamp")
    t = (df["timeStamp"] - df["timeStamp"].iloc[0]) / 1000.0
    return resample_uniform(
        t, {"ax": df["X"], "ay": df["Y"], "az": df["Z"], "gx": df["a"], "gy": df["b"], "gz": df["c"]},
    )


def load_external_simra_sessions():
    """Standalone loader -- deliberately NOT wired into
    src/io_loaders.py: load_all_sessions()."""
    sessions = []
    for label, subdir in ((0, "normal"), (1, "incident")):
        folder = EXTERNAL_DATA_DIR / subdir
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.csv")):
            resampled = _parse_ride_file(path)
            if resampled is None or len(resampled) < config.WINDOW_SAMPLES:
                print(f"  skipping {path.name}: too short after resampling")
                continue
            session_id = f"simra_{subdir}_{path.stem}"
            sessions.append(Session(
                session_id=session_id, source="external_simra", label=label,
                gyro_in_deg_per_s=False, df=resampled,
            ))
    return sessions


def main():
    print(f"Loading SimRa sessions from {EXTERNAL_DATA_DIR} ...")
    sessions = load_external_simra_sessions()
    n_normal = sum(1 for s in sessions if s.label == 0)
    n_incident = sum(1 for s in sessions if s.label == 1)
    print(f"Loaded {len(sessions)} sessions ({n_normal} normal, {n_incident} incident/near-miss)")

    sessions = preprocess.canonicalize_all(sessions)
    label_of = {s.session_id: s.label for s in sessions}
    split_of = {s.session_id: "external" for s in sessions}
    ds = manifest.build_dataset(sessions, split_of, "external")
    print(f"Windows: {len(ds.y)} ({int((ds.y == 0).sum())} normal / {int((ds.y == 1).sum())} "
          f"weak-labeled anomalous)")

    session_seconds = evaluate.session_durations_seconds(sessions)
    normal_hours = sum(sec for sid, sec in session_seconds.items() if label_of[sid] == 0) / 3600.0

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

    hybrid_pred = (
        (crash_prob_a > thresholds["classifier_prob_balanced"])
        | (recon_error_a > thresholds["recon_error"])
    )

    signals = {
        "model_a_classifier": (crash_prob_a, thresholds["classifier_prob_balanced"]),
        "model_a_reconstruction": (recon_error_a, thresholds["recon_error"]),
        "model_b_classifier": (crash_prob_b, model_b_threshold),
    }
    metrics, deployed_alerts = {}, {}
    for name, (scores, thresh) in signals.items():
        metrics[name] = evaluate_variant(ds.y, scores, ds.session_id, thresh)
        deployed_alerts[name] = evaluate.simulate_deployed_alerts(
            ds.y, scores, ds.session_id, thresh, normal_hours=normal_hours if normal_hours > 0 else None,
        )
        print(f"{name}: ROC-AUC={metrics[name]['roc_auc']:.3f} "
              f"event_recall={deployed_alerts[name]['session_recall']} "
              f"false_alerts/hr={deployed_alerts[name].get('false_alerts_per_hour')}")

    metrics["hybrid_or_fusion_deployed_rule"] = evaluate_variant(
        ds.y, hybrid_pred.astype(float), ds.session_id, 0.5,
    )
    deployed_alerts["hybrid_or_fusion_deployed_rule"] = evaluate.simulate_deployed_alerts(
        ds.y, hybrid_pred.astype(float), ds.session_id, 0.5,
        normal_hours=normal_hours if normal_hours > 0 else None,
    )
    print(f"hybrid_or_fusion_deployed_rule: "
          f"event_recall={deployed_alerts['hybrid_or_fusion_deployed_rule']['session_recall']} "
          f"false_alerts/hr={deployed_alerts['hybrid_or_fusion_deployed_rule'].get('false_alerts_per_hour')}")

    report = {
        "description": (
            "Third external test: SimRa bicycle near-miss dataset (Berlin, CC BY-NC 4.0), "
            "evaluated with the ALREADY DEPLOYED Model A (classifier + reconstruction + OR-fusion) "
            "and Model B -- no retraining, no threshold recalibration. Qualitatively different from "
            "DaRUS/the scooter dataset: near-miss (not crash) events, pedal bicycle (not motorized "
            "two-wheeler), and a much lower native sampling rate (~4 Hz) -- see ATTRIBUTION.md."
        ),
        "source_citation": (
            "SimRa dataset, simra-project (TU Berlin / Digital Future), "
            "https://github.com/simra-project/dataset, Berlin_2024_03 folder. CC BY-NC 4.0."
        ),
        "caveats": [
            "Positive events are self-reported near-misses, not actual falls/collisions.",
            "Pedal bicycle, not a motorized two-wheeler -- a bigger domain gap than the scooter dataset.",
            "Native accelerometer/gyroscope sampling rate measured at ~4 Hz, ~12x below this "
            "pipeline's 50 Hz target -- window content here is far more interpolated than any "
            "other source this project uses.",
        ],
        "n_sessions": len(sessions),
        "n_normal_sessions": n_normal,
        "n_incident_sessions": n_incident,
        "n_windows": int(len(ds.y)),
        "normal_riding_hours": normal_hours,
        "window_level_metrics": metrics,
        "event_level_deployed_alert_simulation": deployed_alerts,
    }
    evaluate.save_metrics(report, "external_test_simra_dataset")
    print("\nSaved results/external-validation/external_test_simra_dataset.json")


if __name__ == "__main__":
    main()
