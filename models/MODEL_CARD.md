# HelmX model card

## Purpose

HelmX is a research prototype for detecting motorcycle crash-like inertial
motion from accelerometer and gyroscope windows. It combines a supervised
classifier score with an autoencoder reconstruction score and exports a
TensorFlow Lite model for Raspberry Pi inference.

It is **not a certified emergency system** and must not be relied on as the sole
means of contacting emergency services. Deployment requires hardware-specific
validation, a rider-visible cancellation path, and monitoring for sensor or
communications failures.

## Inputs and outputs

- Input `seq`: 60 samples × 6 channels (`ax`, `ay`, `az`, `gx`, `gy`, `gz`) at
  50 Hz after canonical preprocessing.
- Input `aux`: seven window statistics defined in `src/config.py`.
- Outputs: classifier probability and reconstruction error.
- Decision policy: OR fusion followed by consecutive-window confirmation and a
  cooldown; calibrated thresholds are recorded in `thresholds.json`.

## Training and evaluation

Training, evaluation, and export entry points are documented in
`scripts/README.md`. Session-level splitting prevents windows from the same
recording from crossing train, validation, and test partitions. Full metrics,
negative results, external validation, and limitations are reported in
`performance.md` and the machine-readable `results/` package.

Known limitations include scarce labeled crash sessions, simulated or staged
crash data, a documented assumed CARLA sample rate, domain-shift sensitivity,
and no validation on real unstaged motorcycle crashes. See `performance.md`
before interpreting any headline metric.

## Artifact policy

Binary weights (`.keras`, `.tflite`) and fitted normalization state (`.npz`)
are excluded from the public source release until the redistribution rights of
all contributing training data are confirmed. This repository does not assign
a license to those derived artifacts. See `DATA_LICENSES.md`.

When publishing an authorized model release, attach these artifacts to a tagged
GitHub release and record:

- the Git commit and training command;
- dataset and split hashes from the reproducibility manifest;
- Python/package versions and random seeds;
- SHA-256 for every released artifact;
- the exact operating thresholds and intended hardware;
- the separate license governing the weights.

Hashes of the currently evaluated local artifacts are recorded in
`ARTIFACT_HASHES.sha256`. A matching hash verifies identity; it does not grant
permission to redistribute the corresponding binary.
