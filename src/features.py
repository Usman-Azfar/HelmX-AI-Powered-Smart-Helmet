import numpy as np


def add_derived_columns(df):
    """Orientation-invariant engineered signals (magnitude doesn't depend on
    how the sensor is mounted) plus jerk, all standard features in the
    fall/crash-detection literature."""
    df = df.copy()
    df["accel_mag"] = np.sqrt(df.ax ** 2 + df.ay ** 2 + df.az ** 2)
    df["gyro_mag"] = np.sqrt(df.gx ** 2 + df.gy ** 2 + df.gz ** 2)
    df["jerk"] = np.gradient(df["accel_mag"].to_numpy(), df["t"].to_numpy())
    return df
