import numpy as np
import pandas as pd

from . import config


def _ensure_strictly_increasing(t):
    """np.interp silently produces wrong results if x-coordinates aren't
    strictly increasing. Real sensor logs occasionally have duplicate or
    out-of-order timestamps (logger jitter, clock resync); this clamps them
    non-decreasing then nudges by nanoseconds so ties become strict, without
    perceptibly moving well-formed timestamps."""
    t = np.maximum.accumulate(t)
    return t + np.arange(len(t)) * 1e-9


def resample_uniform(t, values_dict, rate_hz=config.TARGET_RATE_HZ):
    """Interpolates one or more channels (sharing timestamps `t`) onto a
    uniform grid at `rate_hz`. Used for single-sensor-stream sources."""
    t = _ensure_strictly_increasing(np.asarray(t, dtype=np.float64))
    t_start, t_end = t[0], t[-1]
    n = int(np.floor((t_end - t_start) * rate_hz)) + 1
    grid = t_start + np.arange(n) / rate_hz

    out = {"t": grid}
    for name, values in values_dict.items():
        out[name] = np.interp(grid, t, values)
    return pd.DataFrame(out)


def resample_two_streams(t_a, values_a, t_b, values_b, rate_hz=config.TARGET_RATE_HZ):
    """Time-aligns two independently-timestamped sensor streams (e.g. an
    accelerometer log and a gyroscope log recorded as separate files) onto one
    shared grid, instead of naively truncating both to the same row count."""
    t_a = _ensure_strictly_increasing(np.asarray(t_a, dtype=np.float64))
    t_b = _ensure_strictly_increasing(np.asarray(t_b, dtype=np.float64))

    t_start = max(t_a[0], t_b[0])
    t_end = min(t_a[-1], t_b[-1])
    if t_end <= t_start:
        return None

    n = int(np.floor((t_end - t_start) * rate_hz)) + 1
    grid = t_start + np.arange(n) / rate_hz

    out = {"t": grid}
    for name, values in values_a.items():
        out[name] = np.interp(grid, t_a, values)
    for name, values in values_b.items():
        out[name] = np.interp(grid, t_b, values)
    return pd.DataFrame(out)
