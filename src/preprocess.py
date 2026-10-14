import dataclasses

from . import config, units, features


def canonicalize(session):
    """Projects a Session's raw dataframe onto canonical units (gyro deg/s,
    accel gravity-removed) and appends derived features. Safe to apply to
    every source uniformly: sources whose accel is already gravity-free pass
    through the high-pass filter with only a minor edge transient."""
    df = units.gyro_to_deg_per_s(session.df, session.gyro_in_deg_per_s)
    df = units.remove_gravity(df, config.TARGET_RATE_HZ)
    df = features.add_derived_columns(df)
    return dataclasses.replace(session, df=df, gyro_in_deg_per_s=True)


def canonicalize_all(sessions):
    return [canonicalize(s) for s in sessions]
