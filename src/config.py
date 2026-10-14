from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"
METRICS_DIR = RESULTS_DIR / "metrics"
FIGURES_DIR = RESULTS_DIR / "figures"
EXPERIMENTS_DIR = RESULTS_DIR / "experiments"
EXTERNAL_VALIDATION_DIR = RESULTS_DIR / "external-validation"
REPRODUCIBILITY_DIR = RESULTS_DIR / "reproducibility"
PROCESSED_DIR = ROOT / "processed"

# Common resample grid every source is projected onto before windowing, so a
# window always spans the same real-world duration regardless of native rate.
TARGET_RATE_HZ = 50.0
WINDOW_SAMPLES = 60
STRIDE_SAMPLES = 15

# full_data_carla.csv carries no timestamp column, only row order per driver
# session. 20Hz is CARLA's common fixed-delta setting; correct this if the
# real capture rate used for this dataset is known.
CARLA_ASSUMED_RATE_HZ = 20.0

# Gravity/orientation-bias removal applied to every accelerometer stream so
# CARLA (gravity-inclusive) and phone recordings (already gravity-compensated)
# land on the same physical quantity: dynamic/linear acceleration.
GRAVITY_HIGHPASS_CUTOFF_HZ = 0.3
GRAVITY_HIGHPASS_ORDER = 2

ROAD_DUPLICATE_GLOB = "*-Copy1*"

RAW_SENSOR_COLUMNS = ["ax", "ay", "az", "gx", "gy", "gz"]
AUX_FEATURE_COLUMNS = [
    "accel_mag_mean", "accel_mag_std", "accel_mag_peak",
    "gyro_mag_mean", "gyro_mag_std", "gyro_mag_peak",
    "jerk_peak",
]

RANDOM_SEED = 42
TRAIN_FRAC = 0.7
VAL_FRAC = 0.15
# remaining 0.15 -> test

# Seeds for model init + training shuffle only (scripts/train_multi_seed.py) --
# NOT used for the data split, which always stays keyed on RANDOM_SEED above so
# the split is identical and reproducible across every run (changesToMake.txt
# item 4/5). Reporting mean +/- std across these is the scientifically stronger
# alternative to fully seeding TF (item 5) recommended by the paper reviewer.
SEEDS = [42, 43, 44, 45, 46]

# Fraction of windows kept as positive within each fall/near-fall session,
# selected by peak accel magnitude, to counter file-level label noise (see
# manifest._windows_for_session).
ANOMALY_TOP_FRACTION = 0.3
