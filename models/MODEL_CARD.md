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

Training data come only from third-party datasets: CARLA simulation, nine
sessions of the STRIDE car-mounted smartphone dataset, the Boubezoul et al.
fall and near-fall recordings, and the DaRUS collision/operational
simulations. No helmet-mounted motorcycle riding recorded by the author was
used for training. Sources and licences: `DATA_LICENSES.md` and
`PROVENANCE_AUDIT_v1.1.md`.

The deposited primary model was trained by the maintained `scripts/train.py`
workflow with model/training seed 42 and the fixed session split seed 42.
Early stopping selected the epoch with maximum validation classifier ROC-AUC
(`val_crash_prob_auc`, patience 8, restored best weights). Batch size was 128,
the maximum was 60 epochs, and the default Adam optimizer settings in
TensorFlow 2.16.1 were used. Reconstruction/classification loss weights were
2:1, with the derived reconstruction-error output assigned zero loss weight.
The five-seed study is the preferred performance estimate; seed 42 identifies
the frozen deployable instance rather than a claim that it was the best test
run.

Known limitations include scarce labeled crash sessions, simulated or staged
crash data, a documented assumed CARLA sample rate, domain-shift sensitivity,
and no validation on real unstaged motorcycle crashes. See `performance.md`
before interpreting any headline metric.

## Artifact policy

Binary weights (`.keras`, `.tflite`) and fitted normalization state (`.npz`)
are excluded from this Git branch. The frozen artifacts are distributed in the
Zenodo reproducibility archive (https://doi.org/10.5281/zenodo.23770989) under
the research-artifact notice in `LICENSES.md`; the repository MIT license does
not apply to them. See `DATA_LICENSES.md`.

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
