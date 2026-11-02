# HelmX v1.1.0 — Dataset provenance correction

> **Note for this GitHub branch.** This is the maintained copy of the document
> deposited in Zenodo v1.1.0 (https://doi.org/10.5281/zenodo.23770989).
> Statements below about byte-identical files, and the change inventory they
> cite, refer to that archive. On this branch, some historical records and
> scripts use portable paths and neutral tool names; the byte-exact originals
> and the model binaries are in the Zenodo archive. The study-conduct sentence
> in item 2 was corrected on 2026-11-03 to match the journal manuscript.

This document is **corrected metadata** issued with v1.1.0 (2026-11-01). It
does not change any model, threshold, split, dataset hash or measured value.
Historical scripts, logs, run records and historical reports inside this
archive are byte-identical to v1.0.0 (verified file by file; see
`ZENODO_V1.1_CHANGE_INVENTORY.csv`). Two maintained summary documents are
deliberate exceptions: `piResults/results/COMPLETE_RESULTS.md` (the curated
results report: C1 stationary-noise sample count corrected from 247,151 to
186,081 to match the unchanged raw capture, a Q2 evidence link, and new L11 and
benign-movement rows) and `piResults/documentation/status/FINAL_CLOSURE_STATUS.md`
(L11 and Q2 entries added). Where a historical file describes a data source
differently, this document is authoritative (see "Historical files not edited"
below).

## What was wrong

Parts of the v1.0.0 documentation described `data/road/` as in-house or
author-collected motorcycle riding (for example, v1.0.0 `DATA_LICENSES.md`
"simulator-generated and in-house recordings" and v1.0.0 `performance.md`
"Real phone-logged motorcycle rides"). That is incorrect.

## Basis of the correction

1. **Archived source comparison.** `scripts/extended_false_alarm_evaluation.py`
   (unchanged since v1.0.0) records that the six STRIDE Driving Behaviour
   sessions and STRIDE Road Anomalies Bump 1, Bump 2 and Pothole 10 were found
   identical to the nine sessions already under `data/road/` (row counts and
   values, not only folder names). `system_understanding.md` §12 records the
   same check. This is a **documented prior audit**. The raw datasets are not
   redistributed, so the comparison was **not repeated** for v1.1.0.
2. **Author confirmation (2026-11-01).** All model-development and benchmark
   riding/impact datasets were downloaded from third-party providers. The
   author's own project activities were limited to Raspberry Pi and helmet
   hardware work: stationary sensor measurements, helmet donning/removal,
   walking and rotation, guided handling, and manually controlled helmet
   drops/impacts. Those measurements are the Raspberry Pi evidence under
   `piResults/`; **none of them was used to create a model-training session.**
   The author alone performed these trials; no other individuals were
   recruited or measured. The academic supervisor verbally reviewed and
   endorsed these activities. No institutional ethics application was made and
   no formal approval or exemption is claimed. Identifiable media were collected
   but are not included in this archive.

## Corrected source map

| Directory | Original source | Use |
|---|---|---|
| `data/carla` | CARLA simulator, Dosovitskiy et al. (2017) | 7 sessions: 5 train / 1 val / 1 test |
| `data/road` | **STRIDE**, Khandakar et al. (2024), https://doi.org/10.6084/m9.figshare.25460755, CC BY 4.0 — car-mounted smartphone recordings | 9 sessions: **6 train / 1 val / 2 test** |
| `data/fall` | Boubezoul et al. (2019), https://doi.org/10.1016/j.dib.2019.103828 | 4 sessions: 2 / 1 / 1 |
| `data/near-fall` | Boubezoul et al. (2019), same dataset | 7 sessions: 5 / 1 / 1 |
| `data/darus` | Rodegast et al., DaRUS, https://doi.org/10.18419/darus-3301 | 39 sessions: 28 / 6 / 5 |
| `data/extended_normal_road_raw` | **STRIDE**, 14 further Road Anomalies sessions | evaluation only; held-out **within-source** |
| `data/external_scooter_riding_raw` | Sanchez-Iborra et al. (2025), https://doi.org/10.5281/zenodo.14887437 | evaluation only; independent source |
| `data/external_simra_bicycle_raw` | SimRa project, TU Berlin | evaluation only; independent source |

Session counts were derived from `split_session_ids` in
`results/reproducibility/reproducibility_manifest.json` (seed 42; 66 sessions,
46/10/10; 69 hashed files). Per-folder licences are in `DATA_LICENSES.md`;
a machine-readable version is `THIRD_PARTY_SOURCE_MAP.csv`.

## Consequences for interpretation

- **Held-out test composition.** The 10-session test split has 5,437 windows:
  5,294 normal and 143 weakly labelled crash-like. The two STRIDE test sessions
  contribute 2,368 normal windows (`road_2. Aggressive` 2,355, `road_2.Bump`
  13) and CARLA `carla_onder` contributes 2,614. Together, car and simulation
  sources account for **4,982 / 5,294 = 94.1 %** of normal test windows
  (counted from `results/experiments/heldout_window_predictions.csv`). Zero
  alerts on that split therefore do not establish a false-alert rate for
  helmet-mounted motorcycle riding.
- **STRIDE false-alert evaluation.** The 14 extra STRIDE sessions (0.290 h,
  4.10 km) are disjoint from the nine `data/road` sessions, but come from the
  same dataset, sensor modality and provider. They are a **held-out
  within-source** evaluation, not an independent external domain. Scooter and
  SimRa are the independent external sources.
- **Falls and near-falls.** Both folders come from Boubezoul et al. and must be
  cited to that source. A 2020 corrigendum (*Data in Brief* 30, 105577,
  https://doi.org/10.1016/j.dib.2020.105577) corrected the lateral
  acceleration (`Ay`) values in the fall data. **It has not been established
  whether the frozen `data/fall` files correspond to the original or the
  corrected upstream release.** Reproductions with a different upstream
  revision may not match the archived file hashes.

## Historical files not edited

The following v1.0.0 files contain older wording about data sources. They are
generated records or experiment scripts and are kept byte-identical as
historical evidence; read them together with this document:

- `scripts/extended_false_alarm_evaluation.py` (docstring) describes the
  STRIDE car sessions as "more real riding data"; it correctly names STRIDE as
  the source;
- `piResults/experiments/closure/provenance.py` and
  `piResults/results/final-closure/provenance_M1/` record the road-data origin
  as an explicit unknown ("This table does not certify an in-house origin or
  source license");
- `piResults/documentation/` contains earlier working protocols and status
  notes, labelled as historical in `piResults/documentation/README.md`.

Documentation files that are maintained (not generated records) were corrected
in place in v1.1.0: `DATA_LICENSES.md`, `README.md`, `ZENODO_README.md`,
`RELEASE_NOTES.md`, `EVIDENCE_INDEX.md`, `data/README.md`, `performance.md`
(§1 and §17), `system_understanding.md` (§3.1), `models/MODEL_CARD.md`,
`results/README.md` and `results/experiments/BASELINE_AND_FILTER_SENSITIVITY.md`.
`ZENODO_V1.1_CHANGELOG.md` lists every change.

## Unchanged by this correction

The frozen model, normalizer, thresholds, deployment configuration, dataset
file hashes, split assignments, archived metrics and all Raspberry Pi results
are unchanged. Numerical stability does not remove the limitations above.
