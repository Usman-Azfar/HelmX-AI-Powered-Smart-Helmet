# Dataset and derived-artifact licensing

Version 1.1.0. This file replaces the v1.0.0 `DATA_LICENSES.md`, which
described `data/road/` as "in-house recordings". That description was wrong:
`data/road/` is a subset of the public STRIDE dataset. The correction and its
evidence are documented in [`PROVENANCE_AUDIT_v1.1.md`](PROVENANCE_AUDIT_v1.1.md)
and summarized per folder in [`THIRD_PARTY_SOURCE_MAP.csv`](THIRD_PARTY_SOURCE_MAP.csv).

The MIT license covers original HelmX software and documentation. It does not
replace upstream licenses or establish redistribution rights for datasets, model
weights, or derived caches. No raw third-party dataset is included in this
repository or in the Zenodo archive.

## Canonical training sources (the five directories read by `src/io_loaders.py`)

| Directory | Original provider and recorded license status | Deposit disposition |
|---|---|---|
| `data/carla` | CARLA simulated vehicle driving (Dosovitskiy et al., 2017, https://proceedings.mlr.press/v78/dosovitskiy17a.html). Simulator output; source-specific rights apply. | Local input only; obtain from the original provider and retain attribution. |
| `data/road` | Nine sessions of the **STRIDE** dataset (Sensor Technologies for Road Insights and Driving Evaluation; Khandakar et al., 2024), Figshare DOI https://doi.org/10.6084/m9.figshare.25460755, CC BY 4.0. **Car-mounted smartphone recordings, not helmet-mounted motorcycle data and not collected by the HelmX author or team.** Frozen split: 6 training, 1 validation, 2 held-out test sessions. | Local input only; cite the dataset and honor CC BY 4.0. |
| `data/fall`, `data/near-fall` | Boubezoul et al., "Dataset on powered two wheelers fall and critical events detection", *Data in Brief* 23, 103828 (2019), https://doi.org/10.1016/j.dib.2019.103828 — the source of **both** the fall and the near-fall folders. A 2020 corrigendum (https://doi.org/10.1016/j.dib.2020.105577) corrected lateral-acceleration (`Ay`) values in the fall data; whether the frozen local files match the original or corrected upstream release has **not** been established. Dataset redistribution terms have not been independently established; article licensing alone is insufficient evidence of file licensing. | Local input only; public redistribution pending source terms. |
| `data/darus` | Rodegast et al., DaRUS ISO 13232 motorcycle collision and operational simulations, University of Stuttgart, https://doi.org/10.18419/darus-3301. Repository records identify CC BY 4.0; attribution must be retained and current source terms verified before redistribution. | Local input only; no MIT relicensing. |

## Evaluation-only sources (never passed to the training loaders)

| Directory | Original provider and recorded license status | Relationship to training data |
|---|---|---|
| `data/extended_normal_road_raw` | 14 further STRIDE Road Anomalies sessions (Khandakar et al., 2024), https://doi.org/10.6084/m9.figshare.25460755, CC BY 4.0. | Disjoint sessions from the **same** dataset, sensor modality and provider as `data/road`. A held-out **within-source** evaluation, not an independent external dataset. |
| `data/external_scooter_riding_raw` | Sanchez-Iborra, Bernal-Escobedo and Santa, "Dataset on personal mobility vehicle's regular riding and fall events", *Data in Brief* 61, 111681 (2025), https://doi.org/10.1016/j.dib.2025.111681; data: Zenodo `jsanta-upct/scooter-riding` v1.1, https://doi.org/10.5281/zenodo.14887437, CC BY 4.0. | Independent source. |
| `data/external_simra_bicycle_raw` | SimRa project (Digital Future / TU Berlin), https://github.com/simra-project/dataset, `Berlin_2024_03` rides. **CC BY-NC 4.0 (non-commercial use only).** | Independent source; pedal bicycle, ~4 Hz native IMU rate. |

## Author-generated and derived material

| Material | Source and status | Deposit disposition |
|---|---|---|
| Model weights and fitted normalizers | Derived from the training sources above. On 2026-10-15 the author confirmed permission to redistribute the included author-generated derivative/model artifacts publicly. | Not tracked in this Git branch. Included in the Zenodo archive (https://doi.org/10.5281/zenodo.23770989) under the research-artifact redistribution notice in `LICENSES.md`; no source-dataset rights are conveyed. |
| Raspberry Pi measurements under `piResults/` | Recorded by the author's own hardware campaign: stationary sensor measurements, helmet donning/removal/rotation, guided handling and controlled physical demonstrations. **These measurements are not a source of any model-training session.** | Included as author-generated evidence under CC BY 4.0; see `LICENSES.md`. No identifiable participant images, videos, names or personal records are included. |

The original 7 October 2026 software-license record selected MIT for original
software. On 15 October 2026 the author additionally confirmed public
redistribution permission for the included model/normalizer artifacts and
authorized CC BY 4.0 for author-generated Raspberry Pi evidence. These grants do
not relicense excluded third-party datasets or imply permissions beyond the
scopes stated in `LICENSES.md`.

The author alone performed the original Raspberry Pi and helmet trials
(stationary, handling and controlled drop tests) as a supervised student
project; no other individuals were recruited or measured. The academic
supervisor verbally reviewed and endorsed these activities. No application was
made to an institutional ethics committee, and no formal ethics approval or
exemption is claimed. (Corrected on 2026-11-03; the Zenodo v1.1.0 copy of this
file used earlier participant wording.)

See `data/README.md` for the local directory layout and the reproducibility
manifest under `results/reproducibility/` for hashes of the exact files used in
reported runs.
