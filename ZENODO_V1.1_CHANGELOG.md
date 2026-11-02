# HelmX reproducibility package — v1.1.0 change log

Previous version: 1.0.0 (2026-10-15), DOI 10.5281/zenodo.23401265, unchanged.
This version: 1.1.0, DOI 10.5281/zenodo.23770989 (published 2026-11-02).
Author: Usman Azfar.

> GitHub copy: this change log describes the Zenodo archive. The change
> inventory it cites is in that archive; the study-conduct line below was
> corrected on 2026-11-03.

**No model was retrained and no historical record was edited.** The frozen
Keras/TFLite models, the fitted normalizer, the thresholds
(θc = 0.9892255067825317, θr = 10.878735866546593), the deployment
configuration and runtime, the dataset hashes and split assignments, the
archived metrics, every Raspberry Pi record (measurements, run summaries,
READMEs, logs, traces), every historical report and protocol, and every
script from v1.0.0 are byte-identical to v1.0.0. The only v1.0.0 files that
differ are maintained documentation, the `piResults/provenance/` indices and
the curated report `piResults/results/COMPLETE_RESULTS.md` (section 4). No new hardware run was performed. Every file-level
difference from v1.0.0 is listed, with its category and reason, in
`ZENODO_V1.1_CHANGE_INVENTORY.csv` (in the [Zenodo archive](https://doi.org/10.5281/zenodo.23770989)).

## 1. New offline analyses

| Study | Script | Outputs | Main result |
|---|---|---|---|
| Simple baseline detectors under the same validation protocol | `scripts/baseline_simple_detector.py` | `results/experiments/baseline_simple_detector.json`, `baseline_filter_sensitivity.csv`, `BASELINE_AND_FILTER_SENSITIVITY.md` | Acceleration-peak, gyroscope-peak and 7-feature logistic-regression detectors with validation-only thresholds and the deployed 3-window / 60 s event rule. HelmX re-scored by the same code reproduces 8/8 archived values. On the held-out split HelmX has the highest F1; on external sets the simple rules show different trade-offs. |
| Jerk-feature discrepancy (closure test L11) | `scripts/jerk_feature_study.py` | `results/experiments/jerk_feature_study.json`, `jerk_benign_replay_windows.csv`, `JERK_FEATURE_STUDY.md` | Training uses np.gradient(\|a\|, t) (m/s³); the runtime uses max\|diff(\|a\|)\| without dividing by dt. Median per-window training/runtime ratio 33.4. In isolation the discrepancy changes 1 of 5,437 classifier decisions. The 11 accepted guided-handling phases give 6 confirmed alerts with both the original and corrected formula (the discarded tilt attempt is excluded). The deployed runtime was **not** changed or redeployed. |
| Session-clustered bootstrap | `scripts/session_bootstrap.py` | `results/experiments/heldout_window_predictions.csv` (5,437 rows), `session_bootstrap.json` | 10,000 stratified session resamples. Baseline − HelmX classifier F1, 95 % CI: logistic regression [−0.597, −0.035]; acceleration peak [−0.770, −0.052]; gyroscope peak [−0.944, +0.342] (not significant). Window-level intervals are kept for comparison only: windows overlap by 75 %, so they are unsuitable for primary inference. |
| Filter cutoff-sensitivity provenance | — | `piResults/results/final-validation/ema_sensitivity/README.md` | Documents the original per-cutoff output `ema_sensitivity.csv`, which is unchanged. |

`results/experiments/V1.1_STUDY_DEPENDENCIES.sha256` lists every existing file
the new scripts import or read; all are byte-identical to v1.0.0. The jerk
outputs were first written to
`piResults/results/final-closure/model_L11_jerk_isolation/`; those copies are
kept as the closure record and are byte-identical to the canonical outputs.

## 2. Dataset provenance correction

Documentation only. No data file, hash, split or result changed.

- `data/road/` is **nine sessions of the public STRIDE car-mounted smartphone
  dataset** (Khandakar et al., 2024, doi:10.6084/m9.figshare.25460755), with
  6 training, 1 validation and 2 held-out test sessions. v1.0.0 wording that
  described it as in-house or real motorcycle riding was wrong.
- `data/fall/` and `data/near-fall/` both come from Boubezoul et al. (2019,
  doi:10.1016/j.dib.2019.103828). The 2020 corrigendum
  (doi:10.1016/j.dib.2020.105577) is disclosed; whether the frozen fall files
  match the original or corrected upstream release is not established.
- The 14 extra STRIDE sessions used for false-alert evaluation are a held-out
  **within-source** evaluation (disjoint sessions, same dataset). Scooter and
  SimRa are the independent external sources.
- 94.1 % of held-out normal windows are CARLA simulation (2,614) or STRIDE car
  recordings (2,368).
- The author's own hardware activities produced only the Raspberry Pi evidence,
  never training data. The author alone performed them as supervised student
  work with verbal supervisor endorsement; no other individuals were recruited
  or measured, and no formal ethics approval or exemption is claimed.

New: `PROVENANCE_AUDIT_v1.1.md`, `THIRD_PARTY_SOURCE_MAP.csv`.
Replaced: `DATA_LICENSES.md`.
Corrected: `README.md`, `ZENODO_README.md`, `RELEASE_NOTES.md`,
`EVIDENCE_INDEX.md`, `LICENSES.md`, `data/README.md`, `performance.md` (§1,
§17), `system_understanding.md` (§3.1), `models/MODEL_CARD.md`,
`results/README.md`, `scripts/README.md`,
`results/experiments/BASELINE_AND_FILTER_SENSITIVITY.md`.
Historical scripts and generated records with older wording are kept
byte-identical to v1.0.0; the ones that mention data sources are listed in
`PROVENANCE_AUDIT_v1.1.md`.

## 3. Citation and release metadata

- `CITATION.cff`: version 1.1.0, DOI 10.5281/zenodo.23770989, sole author
  Usman Azfar, repository
  https://github.com/Usman-Azfar/HelmX-AI-Powered-Smart-Helmet/tree/crash-detection,
  relation to v1.0.0, mixed licence (MIT, CC BY 4.0), and references for every
  upstream dataset. The outdated "add the DOI after publication" instruction
  was removed.
- Authorship: Usman Azfar is the sole author. Abdul Hanan and the dataset
  providers are credited in the acknowledgements.
- `ARCHIVE_MANIFEST.sha256` is regenerated without a UTF-8 byte-order mark and
  covers every file except itself.

## 4. Corrections from the post-release evidence audit

- C1 stationary-noise sample count corrected to 186,081 in
  `piResults/results/COMPLETE_RESULTS.md` (matches the raw capture).
- New note `randomized_review_20261011/V1.1_PUBLICATION_NOTE.md`: the D4/K1
  raw captures are in the author's private archive (the original folder notes
  are unchanged).
- Previously omitted Pi evidence published: `training_config_Q2/`,
  `i2c_diagnostic_20261011/` and its verification (host snapshots excluded).
- `piResults/results/COMPLETE_RESULTS.md` is the one changed file under
  `piResults/results/`: the C1 correction, the Q2 evidence link and the new L11
  and benign-movement rows. It is the curated report, not a generated record.
- Restored before release: an intermediate v1.1.0 build had replaced
  development-tool names in 112 historical records and scripts and made three
  orchestration scripts portable. All of these were reverted to the exact
  v1.0.0 bytes (and two published I²C files to their original source bytes),
  so original descriptions of the tools running during the affected tests are
  preserved. The list is in `ZENODO_V1.1_CHANGE_INVENTORY.csv` (status
  `restored`).

## Licensing (unchanged)

MIT for original software and documentation; CC BY 4.0 for author-generated
Raspberry Pi evidence; a research-artifact redistribution notice for the
`.keras`, `.tflite` and fitted `.npz` artifacts; third-party datasets remain
under their own terms and are not included (see `LICENSES.md`,
`DATA_LICENSES.md`).
