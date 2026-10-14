import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config
from .resampling import resample_uniform, resample_two_streams


@dataclass
class Session:
    session_id: str
    source: str          # "carla" | "road" | "near_fall" | "fall" | "darus"
    label: int            # 0 = normal, 1 = crash-like (session-level fallback)
    gyro_in_deg_per_s: bool
    df: pd.DataFrame      # columns: t, ax, ay, az, gx, gy, gz (raw units, resampled)
    frame_labels: object = None  # optional per-sample 0/1 ground truth (np.ndarray), overrides
                                  # the peak-severity heuristic in manifest.py when present


def load_carla(path=None):
    path = path or (config.DATA_DIR / "carla" / "full_data_carla.csv")
    raw = pd.read_csv(path)

    sessions = []
    for driver, group in raw.groupby("class"):
        group = group.reset_index(drop=True)
        t = group.index.to_numpy(dtype=np.float64) / config.CARLA_ASSUMED_RATE_HZ
        df = pd.DataFrame({
            "t": t,
            "ax": group["accelX"].to_numpy(dtype=np.float64),
            "ay": group["accelY"].to_numpy(dtype=np.float64),
            "az": group["accelZ"].to_numpy(dtype=np.float64),
            "gx": group["gyroX"].to_numpy(dtype=np.float64),
            "gy": group["gyroY"].to_numpy(dtype=np.float64),
            "gz": group["gyroZ"].to_numpy(dtype=np.float64),
        })
        resampled = resample_uniform(
            df["t"], {c: df[c] for c in config.RAW_SENSOR_COLUMNS}
        )
        sessions.append(Session(
            session_id=f"carla_{driver}",
            source="carla",
            label=0,
            gyro_in_deg_per_s=False,
            df=resampled,
        ))
    return sessions


def _is_duplicate_dir(dirname):
    return "-Copy1" in dirname


def load_road_folder(folder=None):
    """os.walk's traversal order is filesystem/OS-dependent, not alphabetical
    -- left unsorted, the *order sessions are discovered* (and therefore fed
    into manifest.assign_splits's seeded shuffle) isn't reproducible across
    machines even with the same RANDOM_SEED. Sorting `dirs` in place (which
    os.walk respects for its own traversal) and `files` fixes that."""
    folder = folder or (config.DATA_DIR / "road")
    sessions = []

    for root, dirs, files in os.walk(folder):
        dirs.sort()
        files = sorted(files)
        root_name = os.path.basename(root)
        if _is_duplicate_dir(root_name):
            dirs[:] = []
            continue

        acc_file = next((f for f in files if "Accelerometer" in f), None)
        gyro_file = next((f for f in files if "Gyroscope" in f), None)
        if not (acc_file and gyro_file):
            continue

        acc = pd.read_csv(os.path.join(root, acc_file))
        gyro = pd.read_csv(os.path.join(root, gyro_file))

        merged = resample_two_streams(
            acc["seconds_elapsed"], {"ax": acc["x"], "ay": acc["y"], "az": acc["z"]},
            gyro["seconds_elapsed"], {"gx": gyro["x"], "gy": gyro["y"], "gz": gyro["z"]},
        )
        if merged is None or len(merged) < config.WINDOW_SAMPLES:
            continue

        session_id = os.path.relpath(root, folder).replace(os.sep, "_")
        sessions.append(Session(
            session_id=f"road_{session_id}",
            source="road",
            label=0,
            gyro_in_deg_per_s=False,
            df=merged,
        ))
    return sessions


_FALL_LIKE_COLUMNS = {
    "time(s)": "t",
    "Ax(m/s²)": "ax",
    "Ay(m/s²)": "ay",
    "Az(m/s²)": "az",
    "Rx(°/s)": "gx",
    "Ry.(°/s)": "gy",
    "Rz(°/s)": "gz",
}


def _load_fall_like_file(path):
    df = pd.read_csv(path, sep="\t", encoding="latin1", low_memory=False)
    df = df.rename(columns=lambda c: _FALL_LIKE_COLUMNS.get(c.strip(), c))
    cols = list(_FALL_LIKE_COLUMNS.values())
    df = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
    return resample_uniform(df["t"], {c: df[c] for c in config.RAW_SENSOR_COLUMNS})


def load_fall_like_folder(folder, source_name, label):
    sessions = []
    for fname in sorted(os.listdir(folder)):
        if not fname.endswith(".csv"):
            continue
        resampled = _load_fall_like_file(os.path.join(folder, fname))
        if len(resampled) < config.WINDOW_SAMPLES:
            continue
        session_id = f"{source_name}_{os.path.splitext(fname)[0]}"
        sessions.append(Session(
            session_id=session_id,
            source=source_name,
            label=label,
            gyro_in_deg_per_s=True,
            df=resampled,
        ))
    return sessions


def load_near_fall():
    return load_fall_like_folder(config.DATA_DIR / "near-fall", "near_fall", label=1)


def load_fall():
    return load_fall_like_folder(config.DATA_DIR / "fall", "fall", label=1)


_DARUS_COLUMNS = {
    "Time": "t",
    "MotoBody_linaccX": "ax",
    "MotoBody_linaccY": "ay",
    "MotoBody_linaccZ": "az",
    "MotoBody_angvelX": "gx",
    "MotoBody_angvelY": "gy",
    "MotoBody_angvelZ": "gz",
    "CrashLabelML": "crash_label",
}


def _pad_centered(resampled, frame_labels, min_len, rate_hz):
    """Pads a short sequence with edge-value blocks on both sides so the real
    (very brief) data sits away from the boundary the windowing loop drops
    (range(0, len-window, stride) never covers the last few samples) -- and
    gives the padding its own correctly-spaced 't' values, strictly
    increasing, so downstream jerk (np.gradient over 't') doesn't divide by a
    zero timestep from duplicated padding rows."""
    if len(resampled) >= min_len:
        return resampled, frame_labels

    total_pad = min_len - len(resampled)
    pad_before, pad_after = total_pad // 2, total_pad - total_pad // 2
    dt = 1.0 / rate_hz
    t_idx = resampled.columns.get_loc("t")

    before = np.tile(resampled.iloc[0].to_numpy(), (pad_before, 1))
    if pad_before > 0:
        before[:, t_idx] = resampled.iloc[0]["t"] - dt * np.arange(pad_before, 0, -1)

    after = np.tile(resampled.iloc[-1].to_numpy(), (pad_after, 1))
    if pad_after > 0:
        after[:, t_idx] = resampled.iloc[-1]["t"] + dt * np.arange(1, pad_after + 1)

    padded = pd.DataFrame(np.vstack([before, resampled.to_numpy(), after]), columns=resampled.columns)
    padded_labels = np.concatenate([
        np.zeros(pad_before, dtype=np.int64), frame_labels, np.zeros(pad_after, dtype=np.int64)
    ])
    return padded, padded_labels


def _load_darus_file(path):
    """DaRUS (Stuttgart) ISO 13232 motorcycle-crash simulation files: real
    per-timestep crash ground truth (CrashLabelML), ~2000Hz. The crash-impact
    traces are very short (0.05-0.25s -- they capture just the collision, not
    a full ride) so after resampling to our 50Hz grid they're padded with
    edge-value blocks (a defensible stand-in for "ordinary riding around this
    trace") on both sides so several full sliding windows land on the real
    impact instead of it collapsing to a couple of samples right at an edge
    the windowing loop would drop."""
    df = pd.read_csv(path, sep="\t")
    df = df.rename(columns=lambda c: _DARUS_COLUMNS.get(c.strip(), c))
    cols = list(_DARUS_COLUMNS.values())
    df = df[cols].apply(pd.to_numeric, errors="coerce").dropna()

    resampled = resample_uniform(
        df["t"],
        {**{c: df[c] for c in config.RAW_SENSOR_COLUMNS}, "crash_label": df["crash_label"]},
    )
    frame_labels = (resampled.pop("crash_label").to_numpy() > 0.5).astype(np.int64)

    min_len = config.WINDOW_SAMPLES + 6 * config.STRIDE_SAMPLES
    resampled, frame_labels = _pad_centered(resampled, frame_labels, min_len, config.TARGET_RATE_HZ)

    return resampled, frame_labels


def load_darus():
    sessions = []
    for label, subdir in [(1, "crash"), (0, "non_crash")]:
        folder = config.DATA_DIR / "darus" / subdir
        if not folder.exists():
            continue
        for fname in sorted(os.listdir(folder)):
            if not fname.endswith(".tab"):
                continue
            resampled, frame_labels = _load_darus_file(folder / fname)
            if len(resampled) < config.WINDOW_SAMPLES:
                continue
            sessions.append(Session(
                session_id=f"darus_{subdir}_{os.path.splitext(fname)[0]}",
                source="darus",
                label=label,
                gyro_in_deg_per_s=False,
                df=resampled,
                frame_labels=frame_labels,
            ))
    return sessions


def load_all_sessions():
    return load_carla() + load_road_folder() + load_near_fall() + load_fall() + load_darus()
