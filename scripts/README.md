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

`freeze_reproducibility.py` must run last. It hashes the canonical local
`data/` inputs, records the session split, thresholds, package versions, and
current Git commit, then writes the reproducibility manifest.

Before committing a public release, run:

```powershell
python scripts/check_public_release.py
```

It rejects tracked private archives, raw datasets, unlicensed derived model
artifacts, stale nested snapshots, and files close to GitHub's size limit.
