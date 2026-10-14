import random
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from . import config


def assign_splits(sessions, seed=config.RANDOM_SEED):
    """Splits at the session (whole recording) level, stratified by
    (source, label), so windows from the same file never leak across
    train/val/test."""
    rng = random.Random(seed)
    groups = defaultdict(list)
    for s in sessions:
        groups[(s.source, s.label)].append(s)

    split_of = {}
    for group in groups.values():
        group = group[:]
        rng.shuffle(group)
        n = len(group)

        if n <= 2:
            for s in group:
                split_of[s.session_id] = "train"
            continue

        n_train = min(max(1, round(n * config.TRAIN_FRAC)), n - 2)
        n_val = max(1, min(round(n * config.VAL_FRAC), n - n_train - 1))
        n_test = n - n_train - n_val

        for s in group[:n_train]:
            split_of[s.session_id] = "train"
        for s in group[n_train:n_train + n_val]:
            split_of[s.session_id] = "val"
        for s in group[n_train + n_val:]:
            split_of[s.session_id] = "test"

    return split_of


def _windows_for_session(session, window, stride):
    df = session.df
    raw = df[config.RAW_SENSOR_COLUMNS].to_numpy(dtype=np.float32)
    accel_mag = df["accel_mag"].to_numpy(dtype=np.float32)
    gyro_mag = df["gyro_mag"].to_numpy(dtype=np.float32)
    jerk = df["jerk"].to_numpy(dtype=np.float32)

    frame_labels = session.frame_labels

    seqs, aux, severity, window_frame_labels = [], [], [], []
    for i in range(0, len(df) - window, stride):
        seqs.append(raw[i:i + window])
        am, gm, jp = accel_mag[i:i + window], gyro_mag[i:i + window], jerk[i:i + window]
        aux.append([
            am.mean(), am.std(), am.max(),
            gm.mean(), gm.std(), gm.max(),
            np.abs(jp).max(),
        ])
        severity.append(am.max())
        if frame_labels is not None:
            window_frame_labels.append(int(frame_labels[i:i + window].any()))

    if frame_labels is not None:
        # Real per-timestep ground truth (currently only the DaRUS ISO 13232
        # crash-simulation source). The physical impact is real but brief
        # (often far under 1s even before our resampling), so a window
        # counts as crash if it touches the labeled impact at all, not by
        # majority -- a 60-sample/1.2s window can't be majority-impact for
        # an event that's genuinely only a few resampled instants long.
        labels = window_frame_labels
    else:
        labels = [session.label] * len(seqs)
        if session.label == 1 and len(seqs) > 0:
            # Whole fall/near-fall *files* are labeled anomalous, but the crash-like
            # event is only a brief part of each recording -- the rest is ordinary
            # riding. Rather than train the classifier on that file-level label
            # noise, keep only the highest-severity windows per session as
            # positives (peak accel magnitude is the dominant crash signal) and
            # relabel the quieter majority of the recording back to normal.
            cutoff = np.percentile(severity, 100 * (1 - config.ANOMALY_TOP_FRACTION))
            labels = [1 if sv >= cutoff else 0 for sv in severity]

    return seqs, aux, labels


@dataclass
class Dataset:
    X_seq: np.ndarray    # (N, window, 6)
    X_aux: np.ndarray    # (N, 7)
    y: np.ndarray        # (N,) 0/1
    session_id: np.ndarray
    source: np.ndarray


def build_dataset(sessions, split_of, split_name, window=config.WINDOW_SAMPLES, stride=config.STRIDE_SAMPLES):
    seqs, aux, labels, sids, sources = [], [], [], [], []
    for s in sessions:
        if split_of.get(s.session_id) != split_name:
            continue
        s_seqs, s_aux, s_labels = _windows_for_session(s, window, stride)
        if not s_seqs:
            continue
        seqs.extend(s_seqs)
        aux.extend(s_aux)
        labels.extend(s_labels)
        sids.extend([s.session_id] * len(s_seqs))
        sources.extend([s.source] * len(s_seqs))

    if not seqs:
        return Dataset(
            X_seq=np.empty((0, window, len(config.RAW_SENSOR_COLUMNS)), dtype=np.float32),
            X_aux=np.empty((0, len(config.AUX_FEATURE_COLUMNS)), dtype=np.float32),
            y=np.empty((0,), dtype=np.int64),
            session_id=np.empty((0,), dtype=object),
            source=np.empty((0,), dtype=object),
        )

    return Dataset(
        X_seq=np.stack(seqs),
        X_aux=np.array(aux, dtype=np.float32),
        y=np.array(labels, dtype=np.int64),
        session_id=np.array(sids, dtype=object),
        source=np.array(sources, dtype=object),
    )
