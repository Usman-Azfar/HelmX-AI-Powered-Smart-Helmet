# Experiment and training scripts

Run scripts from the repository root in a Python 3.11 environment. Raw datasets
must first be installed according to `data/README.md`.

Core workflow:

```powershell
python scripts/train.py
python scripts/evaluate_model.py
python scripts/full_metrics.py
python scripts/export_model.py
python scripts/freeze_reproducibility.py
```

The remaining scripts implement the ablations and external-validation studies
reported in `performance.md`. They are deliberately separate entry points so
the parameters and output of each experiment remain auditable. Generated
public artifacts belong in the categorized `results/` tree; raw datasets,
temporary caches, and private device logs do not.

Version 1.1 offline analyses (no hardware, deterministic; run after the core workflow):

```powershell
python scripts/baseline_simple_detector.py   # second detector under the same protocol
python scripts/session_bootstrap.py          # session-clustered F1-difference CIs (--from-csv to reuse predictions)
python scripts/jerk_feature_study.py         # closure test L11: jerk-formula isolation + benign-motion replay
```

The first two write to `results/experiments/`. The third writes to
`piResults/results/final-closure/model_L11_jerk_isolation/` and reads the saved high-range
benign-motion captures in `piResults/results/final-closure/07_high_range_benign_motion/`.

`freeze_reproducibility.py` must run last. It hashes the canonical local
`data/` inputs, records the session split, thresholds, package versions, and
current Git commit, then writes the reproducibility manifest.

Before committing a public release, run:

```powershell
python scripts/check_public_release.py
```

It rejects tracked private archives, raw datasets, unlicensed derived model
artifacts, stale nested snapshots, and files close to GitHub's size limit.
