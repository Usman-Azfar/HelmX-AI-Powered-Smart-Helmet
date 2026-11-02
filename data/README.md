# Local dataset layout

Raw data is intentionally **not distributed in this source repository**. The
software expects datasets to be obtained from their original sources and placed
under this directory for local training or evaluation. This avoids silently
relicensing third-party data under the repository's MIT software license.

## Original providers

All training and evaluation datasets are third-party public datasets. None was
collected by the HelmX author or team (corrected in v1.1.0; see
`../PROVENANCE_AUDIT_v1.1.md`).

| Directory | Original provider | Role |
|---|---|---|
| `carla/` | CARLA simulator (Dosovitskiy et al., 2017) | training source |
| `road/` | STRIDE, Khandakar et al. (2024), doi:10.6084/m9.figshare.25460755 — car-mounted smartphone recordings | training source (6/1/2 sessions) |
| `fall/` | Boubezoul et al. (2019), doi:10.1016/j.dib.2019.103828 | training source |
| `near-fall/` | Boubezoul et al. (2019), same dataset | training source |
| `darus/` | Rodegast et al., DaRUS, doi:10.18419/darus-3301 | training source |
| `extended_normal_road_raw/` | STRIDE (14 further sessions) | evaluation only, within-source |
| `external_scooter_riding_raw/` | Sanchez-Iborra et al. (2025), doi:10.5281/zenodo.14887437 | evaluation only, independent |
| `external_simra_bicycle_raw/` | SimRa project, TU Berlin (CC BY-NC 4.0) | evaluation only, independent |

A 2020 corrigendum to the Boubezoul dataset (doi:10.1016/j.dib.2020.105577)
corrected fall-data lateral acceleration; check which upstream revision you
download against the hashes in the reproducibility manifest.

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
