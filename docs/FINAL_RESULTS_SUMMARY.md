# HelmX driver drowsiness detection: final results and complete experiment log

Consolidated 2026-09-22. This document is the single point of reference for everything tried,
what was kept, what was rejected, and why. It summarizes and cross-references the individual
frozen hypothesis documents, `docs/RESEARCH_PROTOCOL.md`, and `docs/MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`;
those documents remain the detailed, citable record and are not duplicated here beyond the numbers
needed to understand the outcome.

## 1. What the system is

A causal, personalized driver/rider drowsiness detector for an in-helmet or dashboard camera:
MediaPipe face landmarks feed (a) pixel-correct EAR/MAR/head-pose geometry reduced to a 12-feature
causal physiology vector (PERCLOS, blink rate/duration, relative eye/mouth/pose state against a
per-rider neutral calibration baseline) and (b) a padded face crop through a MobileNetV3-Small
visual encoder. The two streams are fused by a learned quality-aware gate, passed through a stack of
causal dilated TCN blocks, and classified into three stages (alert / low-vigilance / drowsy). A
hysteretic, elapsed-time `AlertController` turns the calibrated probability stream into
caution/warning/critical alerts. The full pipeline (preprocessing, training, calibration,
event-level evaluation, ONNX export, quantization, and the live app) is implemented in
`src/helmx_drowsiness/`, covered by 150 automated tests, and enforces subject-disjoint splits,
provenance hashing, and validation-only threshold/temperature selection throughout.

Training and screening data is UTA-RLDD (official 60-subject/182-video corpus). Labels are
per-video (KSS-style 0/5/10 -> alert/low-vigilance/drowsy), not per-second — this single fact turns
out to be the central constraint on everything below.

## 2. Selected model and its measured performance

The retained model across all experiments is the **quality-gated fusion model with the categorical
cross-entropy objective** (`fusion_mode: quality_gated`, `classification_objective:
categorical_cross_entropy`), trained separately per development rotation
(`configs/uta-multifold-d{2..5}-categorical.yaml`, checkpoints under
`runs/uta-multifold-screen/d{2..5}/categorical/seed-13/`). No challenger ever beat it.

**Window/video-level classification** (pooled out-of-fold over D2-D5, 146 videos, 48 subjects,
`runs/uta-multifold-screen/*_screening_gate_report.json` "baseline" block):

| Metric | Value |
|---|---|
| Macro-F1 | 0.64212 |
| Balanced accuracy | 0.64389 |
| Matthews correlation | 0.46782 |
| Quadratic kappa | 0.58655 |
| Macro ROC-AUC (OvR) | 0.77917 |
| Expected calibration error | 0.10533 |

Per-class recall is uneven: alert 0.75000, drowsy 0.64000, **low-vigilance 0.54167** (the
persistent weak class across every experiment in this project, per
`runs/uta-multifold-screen/categorical_baseline_failure_audit/`).

**Event-level performance** (causal replay of full raw fold-2 validation video through the exact
live inference + `AlertController` path, `evaluate-events`; see
`docs/EVENT_THRESHOLD_FRONTIER.md` for full method and provenance):

| Operating point | Event sensitivity | Detected/true events | False alerts/hour |
|---|---|---|---|
| Raw (untuned) thresholds | 16.67% | 2/12 | 0.000 |
| Zero-false-alarm-tuned (current default) | 33.33% | 4/12 | 0.000 |
| Allowing <=1 false-alert event | **58.33%** | 7/12 | 0.490 |
| Allowing <=5 false-alert events | 66.67% | 8/12 | 2.451 |
| Unconstrained | 100.00% | 12/12 | 3.922 |

These event numbers were re-measured on 2026-09-22 directly against the current best (D2
categorical) checkpoint family and reproduce the same raw/zero-FA figures previously reported for
the earlier, weaker single-fold pilot checkpoint — i.e. the low event-level sensitivity is a
property of the label/threshold structure, not of a particular checkpoint's classification quality.

Fold 1 had already been consumed by the preregistered MIL confirmation described below, so it was
excluded from every later D2-D5 screening decision and cannot be treated as an untouched test set.
DROZY remains unaccessed and locked under
`docs/MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`.

## 3. Complete experiment log

Every candidate below changed exactly one factor from a frozen baseline, was evaluated on
development data only (fold 1 and DROZY excluded), and was governed by a pre-registered advancement
gate written before training. Full quantitative detail and reasoning for each lives in the linked
document.

### 3.1 Pre-protocol single-fold pilots (fold-2 validation only; gate: beat the quality-gated pilot's 0.46337 macro-F1)

Source: `docs/RESEARCH_PROTOCOL.md`.

| # | Candidate | Fold-2 macro-F1 | vs. gate (0.46337) | Outcome |
|---|---|---|---|---|
| 1 | Equal-weight fusion (no learned gate) | 0.44683 | below | rejected |
| 2 | Training-only modality dropout (25%) | 0.45610 | below | rejected |
| 3 | Full-face visual-only baseline | 0.38777 | below | rejected |
| 4 | Eye-band visual-only | 0.40457 | below | rejected (better than #3, still short) |
| 5 | Eye-band visual-only, no MRL init | 0.31645 | below | rejected decisively (confirms MRL init helps) |
| 6 | Dual-single-eye visual-only | 0.40542 | below | rejected (~tied with #4) |
| 7 | Video-level multiple-instance (MIL) weak supervision | 0.51736 (fold-2) | **passed** | **rejected on fold-1 confirmation**: 0.33232 vs. retained model's 0.56481 under identical aggregation — did not generalize |

Candidate 7 is the important one: it is the only pre-protocol candidate that passed its own
development gate, and it failed specifically because it overfit the fold used to select it. This
directly motivated freezing the stricter four-fold (D2-D5) confirmation protocol used for every
later candidate.

A companion **development-only temporal-label audit** (also in `docs/RESEARCH_PROTOCOL.md`) is the
evidentiary basis for most later work: restricting evaluation windows to a clip's early/middle/late
third raised fold-2 macro-F1 monotonically (0.36634 -> 0.40005 -> 0.44763), and physiological
signals (PERCLOS, blink duration, closure duration) moved toward drowsiness late-vs-early in 5-10 of
12 drowsy clips, not all 12. This is the clip-level label-noise finding that later motivated the
label-confidence candidates (#13, #14 below).

### 3.2 Formal D2-D5 multifold screening candidates (pooled baseline macro-F1 0.64212, 146 videos/48 subjects; gates: >=3/4 fold wins, pooled improvement >=0.020, no fold worse than -0.020, paired subject-bootstrap 95% lower bound > 0 — all four required)

| # | Candidate | Fold wins | Pooled Δ macro-F1 | Worst fold | Bootstrap 95% CI | Outcome | Doc |
|---|---|---|---|---|---|---|---|
| 8 | Cumulative ordinal objective | 3/4 | +0.00970 | D3 -0.06416 | [-0.04556, +0.06517] | rejected (3 of 4 gates failed) | `ORDINAL_OBJECTIVE_HYPOTHESIS.md` |
| 9 | Categorical + 0.5x ordinal (hybrid) | 2/4 (1 tie) | +0.00934 | D3 -0.00666 | [-0.01835, +0.03941] | rejected | `HYBRID_OBJECTIVE_HYPOTHESIS.md` |
| 10 | Quality-concat fusion (vs. learned gate) | 0/4 | -0.09776 | D2 -0.12360 | [-0.16420, -0.02620] | rejected decisively | `QUALITY_CONCAT_FUSION_HYPOTHESIS.md` |
| 11 | Frozen visual backbone | 1/4 | -0.07191 | D3 -0.16504 | [-0.16546, +0.02614] | rejected decisively | `FROZEN_VISUAL_BACKBONE_HYPOTHESIS.md` |
| 12 | Subject-class-balanced window sampling | 1/4 | -0.02062 | D3 -0.06014 | [-0.09813, +0.05795] | rejected | `SUBJECT_CLASS_BALANCED_SAMPLING_HYPOTHESIS.md` |
| 13 | Label-confidence weighting (blanket, all drowsy windows) | 1/4 | -0.00589 | D3 -0.04623 | [-0.03578, +0.02478] | rejected | `LABEL_CONFIDENCE_WEIGHTING_HYPOTHESIS.md` |
| 14 | Label-confidence weighting (adaptive, per-video PERCLOS-drift-gated) | 1/4 | -0.01036 | D3 -0.06386 | [-0.04697, +0.02511] | rejected | `LABEL_CONFIDENCE_WEIGHTING_HYPOTHESIS.md` |

No candidate passed all four gates. D2 is the only fold that responds positively to most
interventions (candidates 8, 13, 14 all won D2); D3 is the fold that resists nearly every
intervention, including two independently designed attempts (13, 14) to specifically correct its
underlying label-noise problem — evidence the D3 rotation's difficulty is not caused by the
*mechanism* of any one candidate.

### 3.3 Positive finding: event-level threshold frontier (no retraining)

Source: `docs/EVENT_THRESHOLD_FRONTIER.md`. Not a training candidate — a re-analysis of the existing
best model's already-computed inference traces. The zero-false-alarm constraint used for the
headline 33.33% sensitivity figure is a policy choice, not a ceiling: allowing roughly one false
alert per two hours of alert-video footage (0.49/hour) raises sensitivity to 58.33% on the same
checkpoint. This is the single largest improvement found in the entire project, and it cost minutes
of compute rather than hours of retraining.

## 4. Interpretation

1. **Architecture and training-time interventions are exhausted, not under-explored.** Fusion
   mechanism (learned gate vs. concat vs. equal-weight), backbone trainability (frozen vs.
   fine-tuned), classification objective shape (categorical vs. ordinal vs. hybrid), sampling policy
   (uniform vs. subject-class-balanced), supervision granularity (window vs. video-level MIL), and
   two different label-noise-correction mechanisms (blanket and per-video-adaptive confidence
   weighting) were all tried as controlled one-factor changes from the same frozen baseline. All
   fourteen failed to beat the original quality-gated categorical model.
2. **The root cause is data annotation, not model capacity.** UTA-RLDD's per-video labels assign a
   single class to windows that are demonstrably heterogeneous (the temporal-label audit, and both
   label-confidence candidates' D3/D4 regressions regardless of how the down-weighting was
   targeted). No architecture change removes noise that is present in the ground truth itself.
3. **The event-level bottleneck is a threshold policy artifact more than a classifier-quality
   artifact.** A materially better window/video classifier (0.642 pooled macro-F1 vs. the original
   pilot's lower score) produced the *identical* 16.67% raw event sensitivity, but relaxing the
   zero-false-alarm constraint nearly doubled sensitivity on the same model. This means further
   chasing window-level macro-F1 has a low ceiling for event-level impact; reporting the full
   sensitivity/false-alarm trade-off is more informative than optimizing one point on it.

## 5. Honest limitations (for the thesis write-up)

- Every result in this document is a **development-only** measurement on UTA-RLDD folds 2-5. Fold 1
  was consumed by the earlier MIL confirmation but was not used to select or report the D2-D5
  numbers; DROZY has not been downloaded. No number here should be presented
  as a final, generalization-tested result — that stage was never reached because no candidate
  passed the gate authorizing it.
- All screening used a single seed (13). The project's five-seed confirmatory stage
  (`MULTIFOLD_EXTERNAL_CONFIRMATION_PROTOCOL.md`) was never authorized because no candidate passed
  development screening, so none of these differences have been checked for seed-to-seed stability.
- Auxiliary heads (eye-closure, yawn, head-pose, quality) remain intentionally zero-weighted: no
  dataset in this pipeline currently supplies real labels for them.
- Low-vigilance recall (0.542) is the weakest class in every single experiment above, including the
  retained model. It was a secondary diagnostic throughout, never a primary gate, and remains
  unresolved.
- The event-level "detection delay" terminology is deliberately restricted to "time-to-first-alert
  within drowsy-labelled clips" throughout this project (see `docs/RESEARCH_PROTOCOL.md`), because
  UTA-RLDD does not provide physiological drowsiness-onset timestamps. Do not describe any number in
  this document as an onset-based detection delay.
- This is a research prototype. The safety disclaimer in `README.md` applies without qualification.

## 6. Reproducibility

- Engineering quality gate at time of writing: 150 tests passing, Ruff clean, strict MyPy clean
  across `src/helmx_drowsiness` (54 source files).
- Every rejected candidate's exact config, checkpoint, predictions CSV, and screening-gate JSON
  report (with SHA-256 hashes of the compared prediction files) is preserved under
  `runs/uta-multifold-screen/`; nothing was deleted after rejection.
- The event-threshold frontier is reproducible from the existing cache with no retraining:
  `helmx-drowsiness tune-event-thresholds runs/uta-multifold-screen/d2/categorical/seed-13/event_cache --config configs/uta-multifold-d2-categorical.yaml`.
- The label-confidence tooling is a general-purpose CLI command, not a one-off script:
  `helmx-drowsiness apply-label-confidence <manifest> <output> --down-weighted-label 2 [--adaptive --minimum-drift 0.05]`.
