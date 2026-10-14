import numpy as np
from scipy.signal import butter, filtfilt

from . import config

RAD2DEG = 180.0 / np.pi


def gyro_to_deg_per_s(df, already_deg_per_s):
    """Canonical gyro unit is deg/s (what the deployed MPU6050 library and the
    fall/near-fall reference data both report). CARLA and the road recordings
    come from Android's gyroscope sensor, which reports rad/s."""
    df = df.copy()
    if not already_deg_per_s:
        for col in ("gx", "gy", "gz"):
            df[col] = df[col] * RAD2DEG
    return df


def remove_gravity(df, rate_hz):
    """High-pass filters each accel axis to strip the static gravity/mounting-
    orientation bias, so every source ends up as comparable dynamic
    acceleration instead of relying on some sources already being
    gravity-compensated and others not."""
    df = df.copy()
    nyquist = rate_hz / 2.0
    normal_cutoff = config.GRAVITY_HIGHPASS_CUTOFF_HZ / nyquist
    b, a = butter(config.GRAVITY_HIGHPASS_ORDER, normal_cutoff, btype="highpass")

    min_len = 3 * max(len(a), len(b))
    for col in ("ax", "ay", "az"):
        values = df[col].to_numpy(dtype=np.float64)
        if len(values) > min_len:
            df[col] = filtfilt(b, a, values)
        else:
            df[col] = values - values.mean()
    return df
