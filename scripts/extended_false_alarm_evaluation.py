"""ExperimentsToPerform.txt item 3: strengthen the false-alert evidence with
more real riding data (potholes, speed bumps, hard braking, aggressive
acceleration, sharp turns, rough roads), reporting total unique riding
duration, total distance if available, false alert events, false alerts/hour,
and false alerts/km.

Data source: the CC BY 4.0 Figshare dataset "STRIDE (Sensor Technologies for
Road Insights and Driving Evaluation) Dataset" by Khandakar et al. (2024),
DOI 10.6084/m9.figshare.25460755 -- same license class already used for
DaRUS in this repo, confirmed directly via the Figshare API's dataset record
(api.figshare.com/v2/articles/25460755), not assumed from the companion
paper's own PDF text (which states a stricter NC-ND license for the article
itself, not the dataset -- see data/extended_normal_road_raw/ATTRIBUTION.md).

IMPORTANT, and disclosed honestly rather than silently worked around:
checking this dataset against what's already in data/road/ before using it
found that its "Driving Behaviour" folders (aggressive/standard/slow, 6
sessions) and 3 of its 17 "Road Anomalies" folders (Bump 1, Bump 2, Pothole
10) are BYTE-IDENTICAL to sessions already in data/road/ and already used in
training -- i.e. this repo's existing data/road/ folder appears to have been
originally sourced as a subset of this exact published dataset. Those
duplicate sessions are correctly excluded here: they add zero new evidence.
Only the genuinely new 14 sessions (Bump 3-9, Pothole 11-17) are used below.
This means the requested "hard braking / aggressive acceleration / sharp
turns" coverage could NOT be added from this particular source (that portion
was all duplicate) -- only new pothole and speed-bump coverage. A second,
license-compatible candidate (Mendeley Data 10.17632/9vr83n7z5j, CC BY 4.0,
car driver-behavior accelerometer/gyroscope data) was identified but its
actual file-download endpoint could not be resolved via the public API in
this session -- flagged as a follow-up, not silently dropped.

Recorded on a car (per the source paper), not a motorcycle -- same
car-vs-motorcycle caveat already disclosed for CARLA in this repo. Evaluated
with the ALREADY DEPLOYED model/normalizer/thresholds -- NO retraining, so
this is a genuine held-out, never-seen-during-training evaluation, kept
entirely separate from the five canonical training inputs under data/ (the snapshot from
Round 1) so it cannot perturb that reproducibility guarantee."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import tensorflow as tf

from src import config, normalize, evaluate, preprocess, manifest
from src.io_loaders import Session
from src.resampling import resample_two_streams
from src import model as model_lib  # noqa: F401 (registers custom layers for load_model)

EXTENDED_DATA_DIR = config.DATA_DIR / "extended_normal_road_raw" / "Road Anomalies"


def load_extended_normal_sessions():
    """Standalone loader -- deliberately NOT wired into
    src/io_loaders.py: load_all_sessions(), so this evaluation-only data can
    never be silently pulled into the frozen training pipeline."""
    sessions = []
    distances_km = {}

    for folder in sorted(p for p in EXTENDED_DATA_DIR.iterdir() if p.is_dir()):
        acc_path, gyro_path = folder / "Accelerometer.csv", folder / "Gyroscope.csv"
        if not (acc_path.exists() and gyro_path.exists()):
            continue

        acc = pd.read_csv(acc_path)
        gyro = pd.read_csv(gyro_path)
        merged = resample_two_streams(
            acc["seconds_elapsed"], {"ax": acc["x"], "ay": acc["y"], "az": acc["z"]},
            gyro["seconds_elapsed"], {"gx": gyro["x"], "gy": gyro["y"], "gz": gyro["z"]},
        )
        if merged is None or len(merged) < config.WINDOW_SAMPLES:
            print(f"  skipping {folder.name}: too short after resampling")
            continue

        session_id = "extended_" + folder.name.replace(" ", "_").replace(".", "")
        sessions.append(Session(
            session_id=session_id, source="extended_normal_road", label=0,
            gyro_in_deg_per_s=False, df=merged,
        ))

        distance_km = None
        loc_path = folder / "Location.csv"
        if loc_path.exists():
            try:
                loc = pd.read_csv(loc_path)
                if "speed" in loc.columns and len(loc) >= 2:
                    t = loc["seconds_elapsed"].to_numpy(dtype=float)
                    speed = np.clip(loc["speed"].to_numpy(dtype=float), 0, None)  # m/s, clip GPS noise below 0
                    order = np.argsort(t)
                    distance_km = float(np.trapz(speed[order], t[order])) / 1000.0
            except Exception as e:
                print(f"  {folder.name}: distance unavailable ({e})")
        distances_km[session_id] = distance_km

    return sessions, distances_km


def main():
    print(f"Loading extended normal-riding sessions from {EXTENDED_DATA_DIR} ...")
    sessions, distances_km = load_extended_normal_sessions()
    print(f"Loaded {len(sessions)} new sessions (all normal, label=0)")

    sessions = preprocess.canonicalize_all(sessions)
    split_of = {s.session_id: "extended" for s in sessions}
    ds = manifest.build_dataset(sessions, split_of, "extended")
    print(f"Windows: {len(ds.y)} (all normal by construction)")

    session_seconds = evaluate.session_durations_seconds(sessions)
    total_seconds = sum(session_seconds.values())
    total_hours = total_seconds / 3600.0

    usable_distances = [d for d in distances_km.values() if d is not None]
    total_distance_km = sum(usable_distances) if usable_distances else None
    n_with_gps = len(usable_distances)

    print(f"Total real duration (new data only): {total_hours:.4f} h ({total_seconds:.1f} s)")
    print(f"Sessions with usable GPS speed for distance: {n_with_gps}/{len(sessions)} "
          f"-> total distance {total_distance_km} km" if total_distance_km is not None
          else f"Sessions with usable GPS speed for distance: {n_with_gps}/{len(sessions)}")

    normalizer = normalize.Normalizer.load(config.MODELS_DIR / "normalizer.npz")
    model = tf.keras.models.load_model(config.MODELS_DIR / "helmx_crash_model.keras")
    with open(config.MODELS_DIR / "thresholds.json") as f:
        thresholds = json.load(f)

    X_seq, X_aux = normalizer.transform(ds.X_seq, ds.X_aux)
    crash_prob = model.predict({"seq": X_seq, "aux": X_aux}, verbose=0)["crash_prob"].ravel()

    deployed = evaluate.simulate_deployed_alerts(
        ds.y, crash_prob, ds.session_id, thresholds["classifier_prob_balanced"],
        normal_hours=total_hours,
    )
    if total_distance_km and total_distance_km > 0:
        deployed["false_alerts_per_km"] = deployed["total_false_alert_events"] / total_distance_km
    else:
        deployed["false_alerts_per_km"] = None

    combined = None
    test_metrics_path = config.METRICS_DIR / "test_metrics.json"
    if test_metrics_path.exists():
        with open(test_metrics_path) as f:
            existing = json.load(f)
        existing_balanced = existing["deployed_alert_simulation"]["classifier_only_balanced"]
        existing_hours = existing_balanced["normal_exposure_hours"]
        existing_events = existing_balanced["total_false_alert_events"]
        combined_hours = existing_hours + total_hours
        combined_events = existing_events + deployed["total_false_alert_events"]
        combined = {
            "existing_test_split_hours": existing_hours,
            "existing_test_split_false_alert_events": existing_events,
            "new_extended_data_hours": total_hours,
            "new_extended_data_false_alert_events": deployed["total_false_alert_events"],
            "combined_total_hours": combined_hours,
            "combined_total_false_alert_events": combined_events,
            "combined_false_alerts_per_hour": (
                combined_events / combined_hours if combined_hours > 0 else None
            ),
        }

    report = {
        "description": (
            "Extended false-alarm evaluation on new real-world normal-riding data "
            "(potholes + speed bumps only -- see module docstring for why hard-braking/"
            "aggressive-acceleration/sharp-turns coverage could not be added from this "
            "particular source), evaluated with the already-deployed model (no retraining)."
        ),
        "source_citation": (
            "Khandakar, A., Michelson, D. G., Naznine, M., Salam, A., Nahiduzzaman, Md., "
            "Khan, K., Suganthan, P. N., Ayari, M. A., Menouar, H., & Haider, J. (2024). "
            "STRIDE (Sensor Technologies for Road Insights and Driving Evaluation) Dataset "
            "[Data set]. Figshare. https://doi.org/10.6084/m9.figshare.25460755 (CC BY 4.0, "
            "verified via the Figshare API)."
        ),
        "vehicle_caveat": "Recorded on a car, not a motorcycle -- evaluation-only, not used for training.",
        "n_new_sessions": len(sessions),
        "n_new_windows": int(len(ds.y)),
        "sessions_excluded_as_duplicates_of_data_road": [
            "Driving Behaviour 1-6 (all)", "Road Anomalies Bump 1", "Road Anomalies Bump 2",
            "Road Anomalies Pothole 10",
        ],
        "total_real_duration_hours_new_data_only": total_hours,
        "total_distance_km_new_data_only": total_distance_km,
        "n_sessions_with_usable_gps": n_with_gps,
        "n_sessions_total": len(sessions),
        "deployed_alert_simulation_new_data_only": deployed,
        "combined_with_existing_test_split_evidence": combined,
    }
    print("\n" + json.dumps(report, indent=2))
    evaluate.save_metrics(report, "extended_false_alarm_evaluation")


if __name__ == "__main__":
    main()
