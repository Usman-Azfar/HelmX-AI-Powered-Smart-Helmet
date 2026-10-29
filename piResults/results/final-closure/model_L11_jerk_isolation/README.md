# L11 — Jerk-feature discrepancy: isolated comparison and benign-motion replay

Status: COMPLETE (OFFLINE ANALYSIS AND REPLAY; NO NEW HARDWARE RUN)
Date: 2026-10-28

**Script:** `scripts/jerk_feature_study.py`. Run it from the repository root; it is deterministic.
**Outputs (this folder):**
- `summary.json`
- `benign_replay_windows.csv`, with per-window original vs corrected scores and decisions for the 12 replayed phases

The frozen model, normalizer and thresholds were used throughout, with no retraining.

**Relation to the other closure tests**

| Test | What it isolated | Result |
|---|---|---|
| L1 | The full composed chain, including this jerk mismatch | — |
| L2 | The causal filter alone | — |
| L3 | INT8 alone | — |
| L10 | All seven auxiliary inputs neutralized at once | Classifier MAE 0.043; crash-like agreement 0.944 |
| **L11** | **The jerk formula alone** | Classifier MAE 0.004 |

L11 then replays the closure benign-motion session (`../07_high_range_benign_motion`, reported as N5) with the original and corrected formulas.

## The discrepancy

| Path | Jerk formula | Units | Median on test windows |
|---|---|---|---|
| Training (`src/features.py`) | max \|np.gradient(\|a\|, t)\| | m/s³ | 46.2 |
| Deployed runtime (`deploy/crash_monitor.py: compute_aux_features`) | max \|diff(\|a\|)\| (no division by dt) | m/s² per sample | 1.34 |
| Corrected (tested here) | max \|np.gradient(\|a\|, 1/50 s)\| within the window | m/s³ | 47.6 |

**Effect on the normalized input.** The median training/runtime ratio is 33.4. After normalization (mean 72.2, std 152.9), the runtime jerk input is almost constant:

| Jerk path | Normalized z (p5 / p50 / p95) |
|---|---|
| Runtime | −0.472 / −0.463 / −0.441 |
| Training | −0.472 / −0.170 / +0.623 |
| Corrected | −0.472 / −0.160 / +0.681 |

The corrected formula matches the training feature to a median relative error of 4×10⁻⁸, because the 50 Hz grid is uniform. The deployed model therefore receives no usable jerk information at runtime.

The closure analyses measured the end-to-end fidelity gap (L1), the filter alone (L2) and INT8 alone (L3). This is the first measurement of the jerk formula alone.

## Part A — held-out test split (5,437 windows, 143 crash-like)

**A1. Isolated.** Frozen Keras model and offline zero-phase windows. Only the jerk feature changes; the reference uses training features throughout.

| Jerk | ROC-AUC | F1 | TP / FP | Classifier MAE vs ref. | Classifier decisions changed | OR-rule agreement | Event recall / false alerts |
|---|---|---|---|---|---|---|---|
| Training (reference) | 0.9459 | 0.333 | 29 / 2 | — | — | — | 5/5, 0 |
| Runtime (deployed) | 0.9470 | 0.324 | 28 / 2 | 0.0043 | 1 of 5,437 (one crash-like window lost) | 0.9998 | 5/5, 0 |
| Corrected | 0.9460 | 0.343 | 30 / 2 | 0.0003 | 1 of 5,437 (one crash-like window gained) | 0.9998 | 5/5, 0 |

**A2. Deployment path.** Causal EMA at 0.3 Hz, frozen INT8, compared with the same offline Keras reference. The runtime row is the closure L1 configuration.

| Jerk | ROC-AUC | F1 | TP / FP | Classifier MAE vs ref. | Crash-like agreement | Normal agreement | Event recall / false alerts |
|---|---|---|---|---|---|---|---|
| Runtime (L1) | 0.9181 | 0.378 | 34 / 3 | 0.0724 | 0.895 | 0.9991 | 5/5, 0 |
| Corrected | 0.9197 | 0.404 | 37 / 3 | 0.0735 | 0.902 | 0.9991 | 5/5, 0 |

The A2 runtime row reproduces the archived L1 result (`../model_L1`): classifier MAE 0.0724, crash-like agreement 0.8951, TP 35 / FP 4 on the OR rule.

## Part B — original vs corrected benign-motion replay

**Session.** 2026-10-11 high-range guided session (`../07_high_range_benign_motion`): ±16 g, ±2000 °/s, 60 s per phase, 11 accepted phases.

**Replay path.** Each phase is replayed sample by sample through the deployed code:
1. `SampleStreamGuard`
2. causal EMA filter
3. `WindowScorer`
4. INT8 model
5. `TriggerPolicy`, driven by the recorded timestamps

**Reproduction of the live run.** With the original formula, the replay reproduces every live OR-positive decision and confirmed alert exactly; the script aborts otherwise. Scores were bit-identical in 9 phases. In 06_moderate_rotation (2 windows) and 09_soft_placement (1 window), the classifier score differed by at most 0.035, far below the 0.989 threshold. This is the same INT8 model run on x86 TFLite rather than the Pi's ARM build.

| Phase | Original: classifier crossings / confirmed alerts | Corrected: classifier crossings / confirmed alerts |
|---|---|---|
| 01 stationary | 0 / 0 | 0 / 0 |
| 02 donning | 15 / **1** | 17 / **1** |
| 03 removing | 14 / **1** | 14 / **1** |
| 04 gentle rotation | 6 / **1** | 6 / **1** |
| 05 repeated tilt | 0 / 0 | 1 / 0 |
| 06 moderate rotation | 4 / **1** | 5 / **1** |
| 07 moderate shake | 1 / 0 | 0 / 0 |
| 08 stronger safe shake | 2 / 0 | 3 / 0 |
| 09 soft placement | 3 / **1** | 3 / **1** |
| 10 controlled bump | 0 / 0 | 0 / 0 |
| 11 hand-carried walking | 3 / **1** | 4 / **1** |
| **Accepted total** | **48 / 6** | **53 / 6** |
| *(discarded tilt attempt)* | 5 / 1 | 5 / 1 |

Reconstruction crossings were 0 in every phase under both formulas. Every false alert is classifier-driven.

## Conclusions

1. **The discrepancy is real and the protocol found it.** At runtime the deployed model receives a jerk input that is essentially constant (z ≈ −0.46) instead of the training distribution.
2. **Its measured effect is negligible.**
   - In isolation it changes 1 of 5,437 classifier decisions, with a classifier MAE of 0.004.
   - On the deployment path it accounts for almost none of the L1 gap, so that gap is dominated by the causal filter (L2) and INT8 (L3).
   - The model evidently places little weight on this auxiliary input.
3. **Correcting it does not remove the benign-motion false alarms.** The same 6 phases alert under both formulas, with nearly identical crossing counts. Those alarms are the classifier's response to helmet-handling motion that is unlike the training data. They are not an artefact of the jerk bug.

**Recommended wording.** Report the jerk mismatch as an implementation discrepancy that the validation protocol exposed and then quantified as inconsequential. Do not present it as an explanation for the handling false alarms.

**Fixing the code.** Either correct `compute_aux_features` (divide by dt), or retrain with the runtime definition. A code fix changes the deployed artefact's behaviour, so the Pi evidence would then describe the pre-fix runtime. The cleanest option for this submission is to report the discrepancy and these measurements, and to leave the frozen runtime unchanged.

## Scope

- **Benign-motion replay.** This is an offline replay of saved captures, not a new physical trial. Operator motion was neither amplitude-matched nor independently verified (`guided_plan.json`). Each phase is a separate trial with fresh filter and cooldown state.
- **Earlier 19 Sep session not used.** That session (±2 g, clipping) is superseded by this high-range session and was not replayed.
