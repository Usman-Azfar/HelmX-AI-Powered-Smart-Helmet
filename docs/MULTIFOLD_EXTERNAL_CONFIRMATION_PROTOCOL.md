# Multi-fold development and external confirmation protocol

Status: **frozen before any new model training or external-data download** on 2026-09-06.

This amendment replaces the old plan to treat UTA-RLDD fold 1 as an untouched final test. Fold 1
was legitimately opened after the video-MIL pilot passed its preregistered fold-2 gate, and is now
permanently consumed. Its results may be reported and used for failure description, but never for
architecture, preprocessing, hyperparameter, calibration, threshold, or stopping decisions.

## Stage A: UTA-RLDD multi-fold development

The development universe is provider folds 2-5 only. For each outer rotation, one fold is
validation and the other three are training:

| Rotation | Training folds | Validation fold |
|---|---|---|
| D2 | 3, 4, 5 | 2 |
| D3 | 2, 4, 5 | 3 |
| D4 | 2, 3, 5 | 4 |
| D5 | 2, 3, 4 | 5 |

Subjects, sessions, and provider labels remain intact. No windows from a validation subject may
enter training, physiology-scaler fitting, augmentation selection, early stopping, temperature
calibration, or operating-threshold selection. Each rotation uses its own training-only scaler and
validation-only temperature. The primary unit is a provider video; per-window results are
secondary deployment diagnostics.

Any new hypothesis must be written as a one-factor amendment before launching D2. The retained
quality-gated architecture is retrained as the matched baseline under every rotation. Candidate
and baseline use identical preprocessing, MRL initialization, optimizer, augmentation, maximum
epochs, patience, and seed schedule. The screening seed is 13. A candidate reaches the confirmatory
seed stage only if all of these hold on the four seed-13 rotations:

1. It improves video macro-F1 over the matched baseline in at least three of four folds.
2. Its pooled out-of-fold video macro-F1 improvement is at least 0.020 absolute.
3. No fold is worse by more than 0.020 absolute.
4. A paired subject-clustered 2,000-resample bootstrap of the pooled macro-F1 difference has a
   lower 95% bound above zero.

If screening passes, freeze the candidate and run seeds `[13, 37, 73, 101, 137]` on all four
rotations. Advancement then requires mean paired improvement of at least 0.020, improvement in at
least 15 of 20 fold-seed pairs, a lower 95% hierarchical subject/fold bootstrap bound above zero,
and no pooled class recall decrease greater than 0.050. Failed candidates and all seed histories
remain archived. Fold 1 cannot rescue any failure.

The final development artifact is the four-fold, five-seed ensemble. Each member is calibrated
only on its own validation fold. Ensemble probabilities are arithmetic means of the 20 calibrated
member probabilities. Nothing is refit using external confirmation labels.

## Stage B: independent confirmation on DROZY

The primary independent dataset is **DROZY**, distributed by the University of Liège through its
official ORBi record: <https://orbi.uliege.be/handle/2268/191620>. The provider documents 14
subjects, three tests per subject, KSS scores from 1-9, encoded near-infrared face videos,
timestamps, PVT, and PSG. Six subject/test recordings do not exist, leaving 36 documented valid
sessions. This provides stronger alertness evidence than an acted-eye-closure dataset and a real
sensor-domain shift from UTA-RLDD RGB.

The official 2018 license is at
<https://orbi.uliege.be/bitstream/2268/191620/5/DROZY-LicenseAgreement-20180718.pdf>. Download or use
means accepting it. DROZY is research/evaluation-only: do not redistribute it, do not use it for a
commercial product, do not reveal subject identities, do not publish images except those the
provider marks publishable, and cite the WACV 2016 DROZY paper. Raw data must stay ignored under
`data/raw/drozy/`; derived samples and montages must not be committed or shared.

No DROZY file is downloaded or inspected until a candidate and its Stage-A ensemble are frozen.
When authorized, place the provider archive exactly at:

```text
data/raw/drozy/source/DROZY.zip
```

Extract it exactly under:

```text
data/raw/drozy/extracted/
```

Record the archive SHA-256, license version, extracted file inventory, missing-session list, and
the unmodified `KSS.txt` hash before preprocessing.

### Frozen label and preprocessing contract

- Include every one of the 36 provider-documented valid sessions; exclude only tests 7-1, 9-1,
  10-2, 12-2, 12-3, and 13-3 because the provider states they did not occur or were lost.
- Map session KSS without inspecting predictions: KSS 1-5 = alert, 6-7 = low vigilance, and 8-9 =
  drowsy. KSS 0 is invalid/missing and cannot become alert.
- Before inference, require at least three subjects and four sessions in every mapped class. If
  this preflight fails, DROZY is reported as descriptive only and no alternative mapping is tried.
- Decode only the encoded `videos_i8` NIR videos, replicate intensity to three channels, and apply
  the unchanged full-face/physiology preprocessing contract. Use 24 samples at 8 Hz (about three
  causal seconds) with window starts every 30 seconds. Preserve provider timestamps and
  `interpIndices`; do not silently bridge missing frames.
- Keep the existing five-second per-session calibration behavior and explicitly report it as a
  limitation because a DROZY session is not guaranteed to begin alert.
- Do not fine-tune, fit a scaler, fit temperature, choose a threshold, reject a subject, or alter
  face/quality rules using DROZY. Report face/landmark coverage before class metrics.
- Confirmation requires at least 90% of valid sessions to yield a prediction. Lower coverage is an
  end-to-end failure, not permission to redesign preprocessing after seeing labels.

### Frozen external endpoints

Primary metrics are video macro-F1 and the paired difference between candidate and retained
quality-gated baseline. Secondary metrics are per-class recall, balanced accuracy, MCC, PR-AUC,
calibration error, valid-window/session coverage, and unavailable-session count. Pool all causal
window logits within each session before ensemble averaging. Report subject-clustered 95%
intervals with 2,000 resamples and per-subject results.

A new candidate is externally confirmed only if it passed Stage A, DROZY coverage is at least 90%,
its video macro-F1 exceeds the retained baseline by at least 0.020, the paired subject-clustered
95% interval has a lower bound above zero, and no class recall is lower by more than 0.050. There is
no second external attempt, label remapping, or target-domain calibration after results are seen.
The 2026 RGB-only DMD release and restricted UL-DD record may support separately preregistered
future studies; they cannot replace DROZY after its outcome is known.

## Current authorization boundary

This document alone authorizes dataset-access preparation and implementation of generic
fold/manifest tooling only. It does **not** authorize a new model hypothesis, DROZY download,
preprocessing, training, or inference. A model-specific amendment must first provide a concrete
one-factor rationale derived without fold 1 or DROZY outcomes.

The first such amendment is now frozen in `ORDINAL_OBJECTIVE_HYPOTHESIS.md`. It authorizes
implementation and verification of the cumulative ordinal objective and matched video-level
selection, but no training launch until its implementation gate passes and README records the
verified resolved-config comparison. DROZY remains inaccessible until all Stage-A gates pass.

All candidates listed in `FINAL_RESULTS_SUMMARY.md` have now completed screening and were rejected.
No candidate passed the four Stage-A gates, so the five-seed confirmation stage and DROZY access
were never authorized. Fold 1 remains consumed and may not be reused for selection. Any future
hypothesis requires a new one-factor amendment written before training; this protocol does not
authorize post-hoc reuse of locked or consumed data.
