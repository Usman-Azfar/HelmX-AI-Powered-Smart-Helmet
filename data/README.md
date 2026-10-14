# Local dataset layout

Raw data is intentionally **not distributed in this source repository**. The
software expects datasets to be obtained from their original sources and placed
under this directory for local training or evaluation. This avoids silently
relicensing third-party data and participant recordings under the repository's
MIT software license.

Expected training layout:

```text
data/
├── carla/
├── darus/
├── fall/
├── near-fall/
└── road/
```

Optional evaluation-only inputs:

```text
data/
├── extended_normal_road_raw/
├── external_scooter_riding_raw/
└── external_simra_bicycle_raw/
```

The loaders in `src/io_loaders.py` read the five canonical training directories
directly. Do not recreate the former `datasets/`, `datasets2/`, or
`datasets_used/` mirrors: they duplicate data and are not used by the pipeline.

Before reproducing published metrics:

1. Review `DATA_LICENSES.md` and obtain every dataset from its authoritative
   source under terms applicable to your use.
2. Recreate the directory layout above without renaming source files.
3. Compare local SHA-256 hashes with
   `results/reproducibility/reproducibility_manifest.json`.
4. Run `python scripts/freeze_reproducibility.py` after training and evaluation
   to record the current data snapshot and split assignments.

The external evaluation directories must never be passed to the training
loaders. Their separation is part of the experiment design.
