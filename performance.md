# HelmX Crash Detection — Performance Report

This report combines the measured offline, external-validation, export, and edge-device
experiments behind the project. Machine-readable outputs under `results/` and `piResults/` are the
source of truth. Section 7 is explicitly assumption-based and must not be cited as measured field
performance. Event-rate calculations use unique recording duration and the deployed 60-second
cooldown rather than multiplying overlapping window counts by window length.

_Model family: `models/helmx_crash_model.keras` and the deployed INT8 export. Metrics are generated
by `scripts/full_metrics.py`, `scripts/evaluate_model.py`, and `scripts/export_model.py` against the
canonical local inputs in `data/`; hashes are archived in
`results/reproducibility/reproducibility_manifest.json`. Raw inputs and binary model artifacts may
be excluded from the public source release; see `DATA_LICENSES.md` and `models/MODEL_CARD.md`.
Because training is stochastic, §11's five-seed mean ± standard deviation is preferable to a
single-run value._

## 1. Datasets used

| Dataset | Purpose | Sessions | Normal / Crash-like |
|---|---|---|---|
| CARLA driving-simulator IMU logs (`data/carla/`) | Normal-riding training data across 7 simulated driver sessions | 7 | Normal |
| Real phone-logged motorcycle rides (`data/road/`) | Normal-riding training data: aggressive/standard/slow riding, bumps, potholes | 9 | Normal |
| Staged fall/near-fall maneuvers (`data/near-fall/`, `data/fall/`) — [Dataset on powered two-wheelers fall and critical events detection](https://www.sciencedirect.com/science/article/pii/S2352340919301799) | Crash-like training/eval data from a stuntman and professional riders performing controlled falls and near-fall maneuvers | 11 | Crash-like, file-level labels |
| ISO 13232 motorcycle-collision physics simulations (`data/darus/`) — [Rodegast et al., Stuttgart DaRUS](https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi:10.18419/darus-3301) | Real per-timestep-labeled crash data (25 collision scenarios) plus non-crash control scenarios (14: curbstone, pothole, speed bump, random-state riding) | 39 | Both, real ground truth |

**66 sessions total** (69 raw files) → split at the session level (stratified by source+label, seeded, `config.RANDOM_SEED=42`) into 46 train / 10 val / 10 test sessions, windowed into `(60, 6)` samples at 50Hz/stride-15 (`src/manifest.py`). This exact local dataset snapshot is hashed and archived in `results/reproducibility/reproducibility_manifest.json` (§19); installation and licensing notes are in `data/README.md` and `DATA_LICENSES.md`.

## 2. Classification metrics — Train split

18,720 windows (17,825 normal / 895 crash-like).

| Metric | Balanced operating point (deployed default) | High-recall operating point |
|---|---|---|
| TP / TN / FP / FN | 118 / 17,814 / 11 / 777 | 745 / 17,146 / 679 / 150 |
| Accuracy | 0.958 | 0.956 |
| Precision (PPV) | 0.915 | 0.523 |
| Recall (Sensitivity / TPR) | 0.132 | 0.832 |
| Specificity (TNR) | 0.999 | 0.962 |
| F1-Score | 0.230 | 0.643 |
| F2-Score | 0.159 | 0.744 |
| Balanced Accuracy | 0.566 | 0.897 |
| Matthews Correlation Coefficient | 0.338 | 0.639 |

## 3. Classification metrics — Test split (held out)

5,437 windows (5,294 normal / 143 crash-like), never used for training or threshold calibration.

| Metric | Balanced operating point (deployed default) | High-recall operating point |
|---|---|---|
| TP / TN / FP / FN | 29 / 5,292 / 2 / 114 | 111 / 4,741 / 553 / 32 |
| Accuracy | 0.979 | 0.892 |
| Precision (PPV) | 0.935 | 0.167 |
| Recall (Sensitivity / TPR) | 0.203 | 0.776 |
| Specificity (TNR) | 1.000 | 0.896 |
| F1-Score | 0.333 | 0.275 |
| F2-Score | 0.240 | 0.449 |
| Balanced Accuracy | 0.601 | 0.836 |
| Matthews Correlation Coefficient | 0.430 | 0.328 |

Window-level recall understates operational performance for the same reason as before — see §6
for the deployed 3-consecutive-window simulation, where the balanced operating point now reaches
**100% session recall with zero false alert events** on the test set (an improvement over the
previous run, driven mostly by run-to-run variance — see §11 for the 5-seed distribution this
sits within). This event-level result was re-verified under the real 60-second deployed cooldown
(previously the offline simulator used an ~1.2s placeholder) and
holds: it is a real result, not an artifact of an incorrect cooldown.

## 4. Threshold & curve-based metrics

| Signal | Split | ROC-AUC | PR-AUC (Average Precision) |
|---|---|---|---|
| Classifier (`crash_prob`) | Train | 0.980 | 0.740 |
| Classifier (`crash_prob`) | Test | 0.946 | 0.539 |
| Reconstruction error, mean-over-window (`recon_error`) | Test | 0.718 | 0.125 |
| Reconstruction error, peak-over-window (new, §8) | Test | 0.734 | 0.142 |

The classifier remains the primary in-distribution detection signal. See §8 for the peak-error
variant and the honest hybrid-fusion ablation, and §12 for the experiment where the reconstruction
branch actually outperforms the classifier by a wide margin (unseen, out-of-distribution data).

## 5. Autoencoder & anomaly (reconstruction head) metrics

Computed on the **normalized** window representation the decoder was actually trained to reconstruct.

| | Train — overall | Train — normal | Train — crash-like | Test — overall | Test — normal | Test — crash-like |
|---|---|---|---|---|---|---|
| MSE | 0.743 | 0.226 | 11.03 | 0.772 | 0.212 | 21.51 |
| RMSE | 0.862 | 0.475 | 3.322 | 0.879 | 0.461 | 4.638 |
| MAE | 0.217 | 0.199 | 0.585 | 0.186 | 0.171 | 0.752 |

Crash-like windows reconstruct ~49-101x worse (by MSE) than normal windows on both splits.

**Reconstruction-error (anomaly score) distribution, test split:**

| | Mean-over-window — Normal | Mean-over-window — Crash-like | Peak-over-window — Normal | Peak-over-window — Crash-like |
|---|---|---|---|---|
| Mean | 0.212 | 21.51 | 1.55 | 259.4 |
| P95 / P99 | 0.543 / 1.20 | 44.5 / 704.8 | 2.97 / 11.4 | 1077.3 / 7115.2 |
| Max | 283.9 | 751.8 | 2167.7 | 7544.2 |

The calibrated thresholds (99th percentile of *normal validation* windows) sit at **10.88**
(mean-error) and **134.2** (peak-error, new) — both well inside the crash-like distribution's
upper half.

## 6. Real-time & edge deployment metrics — measured (this development machine)

| Metric | Value |
|---|---|
| Detection latency (crash onset → 3-consecutive-window trigger fires), real per-timestep-labeled DaRUS test sessions, balanced threshold | mean 0.4s, median 0.6s, max 0.6s (3 of the eligible test sessions triggered a full detection this run) |
| Detection latency, high-recall threshold | mean 0.0s, median 0.0s, max 0.0s |
| Real normal-session exposure time, test split (`normal_session_hours`, non-overlapping) | **0.418 hours** (≈25 min) — vs. the old `n_windows * 1.2s` approximation's ≈1.76h, a 4.2x overstatement |
| Window-level trigger rate (diagnostic only — NOT a real alert rate, see caveat below), balanced threshold | 4.8 /hr |
| Window-level trigger rate (diagnostic only), high-recall threshold | 1,323.8 /hr |
| **Local-alarm trigger rate** — deployed rule (3 consecutive windows + REAL 60s cooldown), balanced | **0 /hr, 5/5 test crash sessions detected (100% session recall)** |
| Local-alarm trigger rate — deployed rule, moderate-recall | 0 /hr, 5/5 sessions detected |
| Local-alarm trigger rate — deployed rule, high-recall | 26.3 /hr (11 events / 0.418h), 5/5 sessions detected |
| **SMS false alarms (emergency contact notified for a non-crash)** | **Not applicable at the model-metrics level** — every trigger goes through the 30-second cancellation window before any SMS attempt. |
| Inference latency — Keras (fp32), single-window calls | mean 68.6ms, p95 82.0ms *(dominated by per-call Python/Keras overhead at batch size 1 — see TFLite figures for the representative on-device number)* |
| Inference latency — TFLite float16 | mean 0.16ms, p95 0.31ms |
| Inference latency — TFLite int8 | mean 0.23ms, p95 0.36ms |
| Throughput — TFLite float16 | ~6,173 windows/sec |
| Throughput — TFLite int8 | ~4,444 windows/sec |
| Model footprint — Keras (`.keras`) | 774.3 KB |
| Model footprint — TFLite float16 | 130.8 KB |
| Model footprint — **TFLite int8 (deployed)** | **81.6 KB** |

> **Only the "Local-alarm trigger rate" rows above are real, publication-safe alert-rate
> estimates** (`src/evaluate.py: simulate_deployed_alerts`, real exposure hours + the real
> 60-second deployed cooldown). The "window-level trigger rate" rows are diagnostic only — a
> window-level positive is not necessarily an alert event, since it must also survive the
> 3-consecutive-window rule and cooldown to become one. A previous version of this table computed
> exposure time as `n_normal_windows * window_seconds`, which overstates real riding time by
> ~4x given 60-sample/15-stride windows overlap 75%.

All benchmarks measured on the development machine, CPU-only, single-sample inference calls,
`scripts/full_metrics.py` / `scripts/export_model.py`.

---

## 7. Real-world projected performance — Raspberry Pi 4 deployment

> **⚠️ ESTIMATED / PROJECTED — NOT MEASURED FIELD DATA.** Unchanged from the original assessment;
> see the full assumptions/caveats previously documented in this section (hardware build, field
> trial design, and what field testing can/can't validate). No physical Raspberry Pi deployment or
> rider trial has been run as part of this round of changes. The measured inference/footprint
> numbers this section's projections are built from are refreshed in §6 above; the projection
> methodology and conclusions (e.g. Pi 4 throughput headroom, cancellation-window risk framing)
> are unchanged.

---

## 8. Reconstruction and hybrid-fusion ablation

Supporting artifact: `results/experiments/hybrid_ablation.json`. Summary table, test
split (`results/experiments/hybrid_ablation.json`):

| Variant | TP | FP | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| Classifier alone | 29 | 2 | 0.935 | 0.203 | 0.333 | 0.946 |
| Reconstruction only, mean error | 12 | 3 | 0.800 | 0.084 | 0.152 | 0.718 |
| Reconstruction only, peak error | 12 | 6 | 0.667 | 0.084 | 0.149 | **0.734** |
| Hybrid OR — naive (original, independently-thresholded) | 29 | 3 | 0.906 | 0.203 | 0.331 | — |
| **Hybrid OR — jointly tuned** | **30** | **2** | **0.938** | **0.210** | **0.343** | — |
| Hybrid stacked logistic regression (3 features, C=1.0, round 1) | 25 | 2 | 0.926 | 0.175 | 0.294 | 0.946 |
| Hybrid stacked, C grid-searched, 3 features | — | — | — | — | 0.198 | — |
| Hybrid stacked, C grid-searched, 3 + 7 aux features | — | — | — | — | 0.123 | 0.878 |

**Statistical significance** (`results/experiments/hybrid_ablation.json: significance_tests`, paired bootstrap,
2,000 resamples over the test set):

| Comparison | Point estimate (F1 diff) | Bootstrap 95% CI | Significant at α=0.05? |
|---|---|---|---|
| Hybrid OR (jointly tuned) vs. classifier alone | +0.0095 | [0.000, 0.032] | **No** |
| Hybrid stacked (3-feature) vs. classifier alone | −0.136 | [−0.204, −0.070] | Yes (significantly worse) |

**Conclusion, phrased per the reviewer's explicit guidance**: "joint threshold calibration
yielded a modest, not-yet-statistically-significant improvement over classifier-only inference"
— never "hybrid fusion significantly outperformed supervised classification." The jointly-tuned
OR rule is the best variant on test (F1 0.343 vs. 0.333, one extra true positive, no extra false
positives), but the bootstrap CI for that difference includes zero. Two independent attempts to
improve the stacked meta-classifier (regularization-strength search; adding 7 engineered
features) both *increased* validation F1 while *decreasing* test F1 (0.294 → 0.198 → 0.123) — a
clean overfitting signature on the 219-positive validation split. **The stacked approach remains
an ablation result, not a proposed improvement**, and attempting to improve it only reinforced
that conclusion.

## 9. Model C: autoencoder-only and denoising baselines

Supporting artifacts: `models/helmx_autoencoder_only.keras`,
`models/helmx_autoencoder_only_denoising.keras`, `results/metrics/model_c_metrics.json`.

| | Hybrid model's recon. branch | Model C, plain | **Model C, denoising** |
|---|---|---|---|
| Test ROC-AUC, mean error | 0.718 | 0.732 | **0.737** |
| Test ROC-AUC, peak error | 0.734 | 0.748 | **0.753** |
| Test PR-AUC, mean error | 0.125 | 0.128 | 0.129 |
| Test PR-AUC, peak error | 0.142 | 0.146 | 0.143 |

Training the autoencoder without a competing classifier-head gradient measurably improves its own
reconstruction quality; adding `GaussianNoise`-corrupted input during training (denoising
autoencoder, active only at train time, automatically inert at inference) improves it a further
small, genuine amount on both scoring variants. The progression (hybrid branch → standalone →
denoising) is monotonic on both mean- and peak-error ROC-AUC, which is the strongest evidence
these are real, stacking improvements rather than noise — reported as **modest**, matching the
reviewer's framing, not as a breakthrough. Both variants remain far below the supervised
classifier's in-distribution performance (ROC-AUC 0.946) — see §12 for where the reconstruction
branch's real value shows up instead.

## 10. Model B: supervised-only CNN baseline

Supporting artifacts: `models/helmx_classifier_only.keras`,
`results/metrics/model_b_metrics.json`.

| | Model B (no joint training) | Model A's classifier head (joint training) |
|---|---|---|
| Test ROC-AUC | **0.949** | 0.946 |
| Test PR-AUC | 0.475 | **0.539** |
| Test F1 | 0.324 | **0.333** |
| Test Precision | 0.933 | **0.935** |
| Test Recall | 0.196 | **0.203** |

**The two are essentially indistinguishable** — differences are well within the run-to-run noise
§11 already documents (F1 std ≈ 0.058 across 5 seeds). **Joint multi-task training does not
measurably help the classifier itself on this dataset.** The hybrid architecture's value over a
plain classifier does not come from training synergy in the classifier's own weights — it comes
from the reconstruction branch's independent detection signal, which is decisive in the unseen-crash
generalization case (§12) and marginally useful for fusion (§8), not from joint training improving
classification accuracy per se. Report this plainly in the paper rather than assuming joint
training helps.

## 11. Item 5 — Multi-seed variance (5 seeds, mean ± std)

Supporting artifact: `results/metrics/seed_variance.json`, seeds `[42, 43, 44, 45, 46]`
(data split fixed at `RANDOM_SEED=42` throughout — only model init/shuffle varies).

| Metric | Mean | Std | Coefficient of variation |
|---|---|---|---|
| ROC-AUC | 0.951 | 0.011 | 1.1% |
| PR-AUC | 0.527 | 0.050 | 9.5% |
| F1 (balanced threshold) | 0.317 | 0.058 | 18.3% |
| Precision | 0.857 | 0.087 | 10.2% |
| Recall | 0.199 | 0.049 | 24.6% |

**The paper should cite ROC-AUC 0.951 ± 0.011 and F1 0.317 ± 0.058 (n=5 seeds)** rather than any
single run's numbers (including §2-§4 above, which are one specific run within this
distribution). ROC-AUC is stable across seeds; F1/precision/recall vary more, which is expected
given only 143 crash-like test windows — a handful of predictions flipping moves these ratios
substantially.

## 12. Unseen-crash experiment — DaRUS held out entirely from training

The unseen-crash experiment (this is the most
important new result in this round of changes). `results/external-validation/unseen_crash_experiment.json`.
The experimental `.keras` weight file is retained only in the private archive pending a separate
derived-model redistribution decision; it is not the deployed model.

A separate model, trained on CARLA + road + fall + near-fall only (DaRUS fully excluded from
training/validation), evaluated against all 39 DaRUS sessions (234 windows) as a genuinely
unseen, externally-sourced test set:

| Signal | ROC-AUC | PR-AUC | Precision | Recall | F1 |
|---|---|---|---|---|---|
| Classifier, balanced threshold | **0.352** | 0.448 | 0.388 | 0.306 | 0.342 |
| Reconstruction, mean error | **0.868** | 0.889 | 0.718 | 0.870 | 0.787 |
| Reconstruction, peak error | **0.873** | 0.901 | 0.762 | 0.861 | 0.809 |

Detection latency (balanced threshold, real per-timestep DaRUS ground truth): mean 0.26s, median
0.30s, max 0.90s, 7 sessions detected.

**The supervised classifier's ROC-AUC collapses to 0.35 (worse than chance) on genuinely unseen
collision data — it does not generalize past the specific staged fall/near-fall and simulated
normal-riding patterns it was trained on. The unsupervised reconstruction branch generalizes far
better (ROC-AUC 0.87–0.87, F1 0.79–0.81).** This is the first empirical test of the hybrid
architecture's stated design rationale (reconstruction as "a generalization safety net for crash
types the classifier never saw a labeled example of," `system_understanding.md` §2) and confirms
it directly: the two branches have genuinely complementary failure modes, and this is the
strongest evidence in this report for why the hybrid architecture — not either component alone —
is the right design for a system that must handle a real crash it has never seen labeled data for.

**A note on per-hour rates for this experiment**: DaRUS's non_crash
sessions are short, edge-padded simulation snippets, not continuous riding — their total real
duration is only **0.0117 hours (≈42 seconds)**. Dividing any false-positive count by that
trivially produces numbers in the thousands-per-hour range (the window-level classifier rate
computes to 4,457–5,914/hr). **This is not a meaningful real-world rate and should not be cited
as one** — it's an artifact of the denominator, not evidence the model is unusually bad here; the
ROC-AUC/F1 numbers above are the meaningful results from this experiment. The one number computed
under the real deployed rule (event-level, 60s cooldown) is `deployed_alert_simulation.
classifier_only_balanced`: 9 false alert events over that same ~42 real seconds of non_crash
DaRUS data (session_recall 0.28 — expected, since this uses the classifier alone, whose
generalization is exactly what this experiment shows is poor) — included for completeness, not
as a citable rate, for the same denominator reason.

## 13. Deployment configuration synchronization

Previously, `deploy/config.yaml` hardcoded a stale
copy of the model thresholds (`classifier_prob: 0.9420394`, `recon_error: 8.4379210`) from an
older training run — the live model's actual calibrated thresholds
(`models/thresholds.json`: `0.9892255067825317` / `10.878735866546593`) had drifted out of sync
with what the deployment config claimed to use, which would have meant the numbers in §2-§6 above
did not actually describe what `deploy/crash_monitor.py` would do if run as-is.

`deploy/crash_monitor.py` now loads `classifier_prob`/`recon_error` directly from
`models/thresholds.json` at startup (`load_model_thresholds()`), logging the loaded values;
`deploy/config.yaml` no longer contains numeric copies of either, only a `thresholds_path`
pointer plus the deployment-policy values (`consecutive_windows`, `cooldown_seconds`) that aren't
retrained and so can't drift the same way. Re-running `scripts/train.py` regenerates
`thresholds.json`; the deployment config picks up the new values automatically. **As of this
report, deployment config and the trained model are synchronized by construction, not by manual
bookkeeping.**

## 14. Label-scarcity ablation (Round 3) — window-level, single-seed

Supporting artifact: `results/experiments/label_scarcity_experiment.json`,
`scripts/label_scarcity_experiment.py`. Tests whether Model A's joint hybrid training degrades
more gracefully than Model B's plain supervised training as labeled crash-like training windows
shrink from 100% to 10% (normal training windows held constant at every fraction; validation/test
splits full and unchanged). Single seed per fraction — see caveats below before treating this as
final.

| Crash-label fraction | Kept windows (sessions) | Model A classifier ROC-AUC / F1 | Model B ROC-AUC / F1 | Model A reconstruction ROC-AUC (control) |
|---|---|---|---|---|
| 100% | 895 (25) | 0.946 / 0.333 | 0.949 / 0.324 | 0.718 |
| 50% | 448 (25) | 0.944 / **0.438** | 0.945 / 0.272 | 0.680 |
| 25% | 224 (17) | 0.956 / 0.386 | **0.961 / 0.515** | 0.713 |
| 10% | 90 (13) | **0.904** / 0.343 | **0.953** / **0.469** | 0.687 |

**This does not confirm the "hybrid degrades more gracefully" hypothesis.** At the most extreme
scarcity level (10% labels), Model A's classifier head has the *lowest* ROC-AUC in the table
(0.904) while Model B has the *highest* (0.953); Model B's F1 also clearly wins at both 25% and
10%. Model A only wins on F1 at 50%, via a very different precision/recall tradeoff, not a clean
degradation-curve pattern. The reconstruction branch's own ROC-AUC stays roughly stable
(0.68–0.72) across all four fractions, exactly as expected from the control-check design (it
trains on the same, unaffected normal windows regardless of label fraction) — but this stability
does not carry over into the classifier head being more robust, and the naive hybrid OR rule adds
essentially nothing at any fraction (F1 within 0.002 of classifier-alone throughout).

**Caveats**: single seed per fraction (no variance estimate — Round 1's multi-seed run measured
F1 std ≈0.058 at 100% labels alone, plausibly larger at lower fractions); and session coverage
drops alongside window count at low fractions (13 of 25 original crash sessions represented at
10%), so part of the 10% result reflects losing entire crash-event *types* from training, not
purely fewer examples of the same types.

**Conclusion for the paper**: report as a negative/mixed result for the label-efficiency
hypothesis — on this architecture and dataset, the plain supervised classifier is not clearly less
robust to crash-label scarcity than the jointly-trained one, and at the most extreme scarcity
level tested was actually more robust. This is a legitimate, checked-not-assumed result. **Round 4
(§15) redoes this properly (session-level, 5 seeds) and confirms the same conclusion with much
better statistical grounding — read that section for the number to actually cite.**

## 15. Label-scarcity ablation (Round 4) — session-level, 5 seeds

Full writeup and the honest correction to the original design description:
Supporting artifact: `results/experiments/label_scarcity_session_level_experiment.json`,
`scripts/label_scarcity_session_level_experiment.py`. Refines §14 two ways: subsamples whole
crash-like **sessions** (not windows) from the train split, and repeats over `config.SEEDS` (5
seeds) instead of one — this is the number that should be cited, not §14's.

**Correction to the original design intent**: dropping a whole crash-like session also removes
the majority-"normal-relabeled" windows that session contained (fall/near-fall sessions are only
~30% positively-labeled to begin with; DaRUS crash sessions are mostly padding around a brief real
impact) — so total normal training windows shrink modestly alongside crash-session count (~17,825
at 100%, down to ~8-11% fewer at 10%), not held perfectly constant as originally planned. This is
disclosed rather than glossed over; it's arguably a *more* realistic "fewer crash recordings
available" scenario than surgically touching only positive-labeled windows, but the reconstruction
branch's stability below should be read as "comparatively stable," not "exactly invariant."

| Crash-session fraction | Sessions kept (of 25) | Model A classifier ROC-AUC | Model A classifier F1 | Model B ROC-AUC | Model B F1 | Model A reconstruction ROC-AUC (control) |
|---|---|---|---|---|---|---|
| 100% | 25 | 0.951 ± 0.011 | 0.317 ± 0.058 | 0.958 ± 0.014 | 0.339 ± 0.064 | 0.731 ± 0.010 |
| 50% | 12 | 0.929 ± 0.024 | 0.341 ± 0.093 | 0.932 ± 0.026 | **0.494 ± 0.057** | 0.713 ± 0.019 |
| 25% | 6 | 0.835 ± 0.104 | 0.278 ± 0.101 | 0.820 ± 0.128 | 0.294 ± 0.123 | 0.741 ± 0.012 |
| 10% | 2 | 0.789 ± 0.085 | 0.166 ± 0.080 | 0.799 ± 0.101 | 0.172 ± 0.078 | 0.726 ± 0.009 |

**Confirms §14's conclusion with much better statistical grounding: no evidence that joint hybrid
training makes the classifier more robust to crash-label scarcity than plain supervised training.**
At every fraction, Model B's mean ROC-AUC is equal to or higher than Model A's classifier head,
and the two are within roughly one standard deviation of each other throughout — there is no
fraction at which Model A shows a real advantage once properly averaged over 5 seeds. Notably,
§14's apparent Model-A win at 50% labels (F1 0.438 vs. 0.272, single seed) **does not replicate**
here — with 5 seeds, Model B's F1 at 50% (0.494 ± 0.057) is clearly *higher* than Model A's
(0.341 ± 0.093), the opposite result, confirming §14's single-seed pattern was substantially noise.

Both models degrade substantially and similarly as crash-session availability shrinks (ROC-AUC
~0.95 → ~0.79 going from 25 to 2 sessions, for both) — an expected, sensible finding on its own,
but with no sign the hybrid architecture cushions that drop better than a plain classifier. The
reconstruction branch stays in a comparatively narrow band throughout (0.71–0.74 ROC-AUC) versus
either classifier's ~0.79–0.96 swing — a meaningful, if not perfectly clean, confirmation that the
unsupervised signal is far less sensitive to crash-label availability than either classifier's
supervised signal.

**Conclusion for the paper**: if the literature review's scarce-label motivation needs
architectural support, the defensible claim is about the **reconstruction branch's own comparative
stability** under label scarcity (the unseen-crash experiment, §12, is the strongest evidence for
that) — not that joint training makes the shared classifier itself more label-efficient. That
specific hypothesis was tested twice (window-level single-seed, then session-level 5-seed) and
found no support either time.

## 16. Edge-device benchmark

`deploy/benchmark_device.py` — a self-contained script for measuring inference latency,
model-load time, CPU%/RSS memory, best-effort power draw, and behavior under concurrent CPU load
(a proxy for the drowsiness-detection module running alongside), meant to be run **on the actual
target device**, which is not available in the environment that produced every other number in
this document. Verified functional via a dev-machine smoke test (deleted afterward, since x86
desktop numbers would misrepresent Pi 4 behavior). **§7's
Raspberry Pi numbers remain explicitly projected/not-measured until this script is actually run
on a Pi and its `piResults/results/generated/pi_benchmark.json` output is folded in here.**

## 17. Extended false-alert evidence

Full writeup, including the duplicate-data finding and the vehicle-type caveat:
Supporting artifact: `results/external-validation/extended_false_alarm_evaluation.json`,
`data/extended_normal_road_raw/` (STRIDE dataset, Khandakar et al. 2024, CC BY 4.0 — 14 genuinely
new car-recorded pothole/speed-bump sessions after excluding sessions already duplicated in
`data/road/`). Evaluated with the already-deployed model, no retraining.

| | New data only (14 sessions) | Existing test-split evidence | **Combined** |
|---|---|---|---|
| Real duration | 0.290 h | 0.418 h | **0.708 h** |
| Distance | 4.096 km | n/a (no GPS) | 4.096 km |
| False alert events | 1 | 0 | **1** |
| False alerts/hour | 3.44 | 0.0 | **1.41** |
| False alerts/km | 0.244 | n/a | 0.244 |

**Reported as a strengthening of the evidence, not a regression**: nearly doubling the real
riding/driving duration surfaced one genuine false alert, replacing the previous unfalsifiable
"exactly zero so far" with an actual measured rate (1.41/hr, 0.244/km) that a reviewer can assess
statistically — and that rate is still low enough that, combined with the 30-second cancellation
window before any SMS sends, the residual real-world risk remains small. This is precisely what
the reviewer asked for: don't trust a zero from too little data — get more data and report
whatever it actually shows.

**Known gap, not silently dropped**: this dataset's own "hard braking / aggressive acceleration /
sharp turns" driving-behavior sessions were found to be duplicates of data already used in
training, so this specific extension could only add pothole/speed-bump
coverage. A second CC BY 4.0 candidate (Mendeley `10.17632/9vr83n7z5j`) was identified for that
remaining gap but its download endpoint could not be resolved in this session.

## 18. Attempts to make the hybrid model significantly beat supervised-only (Round 5)

Two techniques were tried on top of every
prior attempt (naive/tuned OR fusion, stacking, label scarcity) — neither produced a significant
win, reported honestly rather than reframed.

**Two-stage AE pretraining → joint fine-tuning** (`results/experiments/two_stage_pretraining_experiment.json`,
`scripts/two_stage_pretraining_experiment.py`, 5 seeds):

| Model | Encoder init | Reconstruction objective | ROC-AUC | F1 |
|---|---|---|---|---|
| B | random | no | 0.958 ± 0.014 | 0.339 ± 0.064 |
| A (current/deployed) | random | joint from scratch | 0.951 ± 0.011 | 0.317 ± 0.058 |
| A1 (pretrained → full fine-tune) | AE-pretrained | joint, immediately | 0.943 ± 0.020 | 0.377 ± 0.067 |
| A2 (pretrained → warmup → fine-tune) | AE-pretrained | joint, after classifier warmup | 0.947 ± 0.007 | 0.381 ± 0.023 |

ROC-AUC does not improve with pretraining (flat to slightly worse). F1 improves modestly for both
pretrained variants, and A2's F1 std is markedly tighter (0.023 vs. 0.058–0.067) — but per-seed
precision/recall pairs still swing widely (e.g. one seed at P=0.943/R=0.231, another at
P=0.240/R=0.818), so this is similar F1 via different tradeoffs, not a more behaviorally
consistent model. Not a statistically clear win at n=5 seeds, but a real-enough pattern to note.
**Conclusion: cold-start optimization interference does not appear to be the reason joint training
hasn't beaten supervised-only** — removing it via pretraining still didn't produce a clear win.

**Richer reconstruction features fed to the classifier**
(`results/experiments/recon_feature_ablation.json`, `scripts/recon_feature_ablation.py`, 5 seeds):

| `recon_feature_mode` | Features | ROC-AUC | F1 | PR-AUC |
|---|---|---|---|---|
| `none` | 0 | 0.951 ± 0.015 | 0.315 ± 0.052 | 0.487 ± 0.055 |
| `scalar` (current default) | 1 | 0.951 ± 0.011 | 0.317 ± 0.058 | 0.527 ± 0.050 |
| `mean_peak` | 2 | 0.915 ± 0.045 | 0.283 ± 0.108 | 0.374 ± 0.129 |
| `rich` | 12 | 0.945 ± 0.018 | 0.286 ± 0.092 | 0.412 ± 0.119 |

A clean negative result: `none` ≈ `scalar` (the reconstruction signal contributes essentially
nothing currently, confirmed a fourth separate way), and richer feature sets make things **worse**
— lower mean, much higher variance. More reconstruction-derived dimensions added noise, not
signal, to the classifier here. **Not recommended to pursue further on this architecture/dataset.**

**Overall**: no technique tried across this entire project — naive/tuned/stacked fusion, label
scarcity, two-stage pretraining, or richer reconstruction features — makes the jointly-trained
classifier significantly outperform the plain supervised one, in-distribution. The hybrid
architecture's demonstrated value remains where §12 found it: out-of-distribution generalization
(reconstruction ROC-AUC 0.87 vs. classifier ROC-AUC 0.35 on unseen DaRUS collision data), not
in-distribution classification accuracy.

## 19. Reproducibility archive

`results/reproducibility/reproducibility_manifest.json` (`scripts/freeze_reproducibility.py`) — regenerate any
time to re-verify the current run against the frozen dataset:

- **Dataset**: SHA-256 hashes of all 69 files under the five canonical local `data/` training
  inputs, 66 sessions, exact session-ID list per split.
- **Seeds**: `RANDOM_SEED=42` (data split, fixed), `SEEDS=[42,43,44,45,46]` (multi-seed
  experiment, §11).
- **Code**: git commit `41f100ce8cca511fa0ea04831d2ee55ef5ff955e` (note: this working directory
  was untracked in the enclosing repo as of this archive — treat the file hashes, not the commit
  alone, as the authoritative record of what dataset produced these numbers).
- **Thresholds**: full `models/thresholds.json` contents at archive time.
- **Package versions**: TensorFlow, NumPy, scikit-learn, as installed when this archive was
  generated.

If the canonical `data/` file hashes ever stop matching this manifest, every number in this document
should be treated as stale and regenerated.

## 20. Staged pretraining, reconstruction-feature, and loss-weighting experiments

A three-experiment staged plan used a success bar set *before* results existed (PR-AUC must move like 0.48→0.56/0.60,
not 0.48→0.49, consistently across seeds). Verdict: **not met** — this section's own data shows
Model B has the highest PR-AUC of every variant tried.

**Experiment 1 — Pretraining** (`results/experiments/exp1_pretraining_comparison.json`, test split, 5 seeds,
identical metric set for all four variants):

| Variant | ROC-AUC | PR-AUC | F1 | Precision | Recall | Recall@95%-spec | Event-level recall |
|---|---|---|---|---|---|---|---|
| **B (supervised-only)** | 0.958 ± 0.014 | **0.581 ± 0.080** | 0.339 ± 0.064 | 0.945 ± 0.036 | 0.208 ± 0.045 | 0.748 ± 0.081 | 0.92 ± 0.10 |
| A0 (cold-start hybrid, deployed) | 0.951 ± 0.011 | 0.527 ± 0.050 | 0.317 ± 0.058 | 0.857 ± 0.087 | 0.199 ± 0.049 | 0.737 ± 0.048 | 0.96 ± 0.08 |
| A1 (pretrained → full fine-tune) | 0.943 ± 0.020 | 0.449 ± 0.079 | 0.377 ± 0.067 | 0.530 ± 0.157 | 0.322 ± 0.085 | 0.664 ± 0.126 | 1.00 ± 0.00 |
| A2 (pretrained → warmup → fine-tune) | 0.947 ± 0.007 | 0.452 ± 0.033 | 0.381 ± 0.023 | 0.591 ± 0.268 | 0.400 ± 0.218 | 0.687 ± 0.030 | 1.00 ± 0.00 |

B has the highest PR-AUC of all four. Among the three hybrid candidates, cold-start **A0** — not
either pretrained variant — has the highest PR-AUC; pretraining trades PR-AUC/recall-at-specificity
for higher raw recall, a different operating point rather than a ranking-quality improvement.

**Experiment 2 — Reconstruction information**, on top of A2 (the better pretrained variant, used
to preserve the preregistered staged comparison even though A0 won Experiment 1 overall; see the result artifacts for
why): `results/experiments/exp2_reconstruction_features_pretrained.json`, 5 seeds:

| `recon_feature_mode` | Features | ROC-AUC | PR-AUC | F1 |
|---|---|---|---|---|
| `none` | 0 | 0.945 ± 0.007 | 0.443 ± 0.013 | 0.380 ± 0.029 |
| `scalar` (current default — winner) | 1 | 0.947 ± 0.007 | **0.452 ± 0.033** | 0.381 ± 0.023 |
| `mean_peak` | 2 | 0.949 ± 0.006 | 0.446 ± 0.029 | 0.374 ± 0.028 |
| `rich` | 12 | 0.946 ± 0.013 | 0.427 ± 0.061 | 0.352 ± 0.067 |

`none`≈`scalar` (indistinguishable), `rich` worst on both mean and variance — the fifth
independent confirmation that richer reconstruction features don't help this classifier.

**Experiment 3 — Task interaction (loss weighting)**, on A2 + `scalar`:
`results/experiments/exp3_loss_weighting.json`, 5 seeds:

| Variant | ROC-AUC | PR-AUC | F1 |
|---|---|---|---|
| `fixed_2to1` (current default — winner) | 0.947 ± 0.007 | **0.452 ± 0.033** | 0.381 ± 0.023 |
| `fixed_1to1` | 0.945 ± 0.007 | 0.439 ± 0.027 | 0.359 ± 0.025 |
| `staged_schedule` (λrec 1.0→0.5→0.2) | 0.944 ± 0.007 | 0.431 ± 0.024 | 0.340 ± 0.016 |

Gradient-conflict diagnostic (seed 42, `fixed_2to1`, cosine similarity between classification- and
reconstruction-loss gradients at the shared bottleneck): **+0.018 mean** (per-variable: −0.011,
+0.046) — essentially zero, not negative. No detected objective conflict at this checkpoint, which
argues against pursuing GradNorm/PCGrad for this architecture (there's no conflict for them to
resolve). Both alternative weightings underperform the existing 2:1 default.

**Overall**: 11 distinct hybrid configurations tried across all three experiments (1 cold-start +
2 pretraining strategies + 4 reconstruction-feature modes + 3 loss-weighting strategies, with
overlap), scoring PR-AUC 0.427–0.527 — every single one below Model B's 0.581. This is the sixth
technique tried across the whole project that fails to make the hybrid classifier significantly
beat plain supervised training in-distribution, now tested against the advisor's own
pre-registered success bar. See §12 for the hybrid architecture's actual demonstrated value
(out-of-distribution generalization).

## 21. Round 7 — genuinely external test set: electric scooter riding + controlled falls/collisions

A second, independent out-of-distribution
test (after §12's unseen-crash/DaRUS experiment), on a completely different dataset/vehicle/sensor
placement — electric scooter, phone-mounted on-board unit, never seen during training
(`scripts/external_test_scooter_dataset.py`, `results/external-validation/external_test_scooter_dataset.json`,
Sanchez-Iborra, Bernal-Escobedo & Santa 2025, CC BY 4.0). Evaluated with the already-deployed
model, Model B, and the exact deployed OR-fusion rule — no retraining, no threshold recalibration.

**Important finding before any evaluation**: the advisor's second-ranked dataset candidate
(Boubezoul et al. 2019, motorcycle fall/critical-events) was found to be byte-signature-identical
to this project's own `data/fall/`/`data/near-fall/` folders — already part of the frozen training
snapshot. It was not independent data and was therefore not used.

14 sessions (5 normal / 9 crash-like), 9,066 windows:

| Signal | Window ROC-AUC | Window PR-AUC | Event-level session recall (/9) | False alerts/hr (0.493h) |
|---|---|---|---|---|
| Model A — classifier alone | 0.774 | 0.278 | 0.667 | 8.11 |
| Model A — reconstruction alone | **0.826** | **0.333** | **0.889** | 6.08 |
| Model B — classifier alone | 0.739 | 0.230 | 0.222 | 4.05 |
| Hybrid OR-fusion (deployed, unchanged) | 0.541* | 0.147* | 0.889 | **14.19** |

*Degenerate single-operating-point AUC for a fixed binary decision — not comparable in resolution
to the other rows.

**Key findings**:
1. Reconstruction branch again the best generalizer (highest ROC-AUC/PR-AUC *and* highest
   event-level recall) — a second independent OOD test pointing the same direction as §12.
2. Model B generalizes markedly worse than Model A's classifier head here (0.222 vs. 0.667
   event-level recall) — the reverse of every in-distribution comparison in this project. One
   external dataset (n=9 crash sessions) isn't conclusive, but it's a real, honestly-reported
   asymmetry worth watching, not asserting as proven.
3. The deployed OR-fusion rule matches reconstruction-alone's recall but at more than double the
   false-alarm rate (14.19 vs. 6.08/hr) — OR-fusion is strictly worse than reconstruction alone on
   this dataset.
4. False-alert rate under real domain shift (4–14/hr) is far higher than the in-domain evidence
   (0/hr test split, 1.41/hr extended STRIDE data, §17) — any real-world false-alarm claim should
   be scoped to this project's own training distribution, not generalized further.

## 22. Round 8 — hierarchical decision policy, and a third external dataset

Supporting artifacts are stored under `results/experiments/` and `results/external-validation/`.

**Part 1 — hierarchical (classifier-primary, reconstruction-fallback) policy**
(`src/evaluate.py: apply_hierarchical_policy`/`tune_hierarchical_thresholds`,
`scripts/hierarchical_decision_policy.py`), all thresholds calibrated on validation only:

| Dataset | Policy | ROC-AUC | PR-AUC | F1 | Event-level recall |
|---|---|---|---|---|---|
| Test split | classifier alone | 0.946 | 0.539 | 0.333 | 1.0 |
| | tuned OR | 0.605 | 0.217 | **0.343** | 1.0 |
| | hierarchical | 0.562 | 0.099 | 0.208 | 0.8 |
| External scooter | reconstruction alone | **0.826** | **0.333** | 0.149 | **0.889** |
| | naive OR (deployed) | 0.541 | 0.147 | 0.155 | 0.889 |
| | hierarchical | 0.526 | 0.123 | 0.112 | 0.667 |

**Result: negative.** Hierarchical is dominated by simpler baselines on both held-out sets. Its
validation F1 (0.686) beats tuned-OR's (0.587), but that gain doesn't transfer to the test split
(0.208) or the scooter set — a clear overfitting signature from calibrating 4 free thresholds
against a ~4,700-window validation split, the same failure mode as Round 2's stacker and Round 6's
richer-reconstruction-features ablation. The underlying idea isn't refuted, just this specific
unregularized calibration.

**Part 2 — third external dataset**: the closest-in-kind candidate (Lee, Koo & Kim 2024, e-scooter
pre-impact falls, CC BY 4.0) has no locatable public data repository — surfaced to the user rather
than guessed at. Per the user's choice, **SimRa** (bicycle near-miss dataset, Berlin, CC BY-NC 4.0,
45 sampled sessions — 20 incident, 25 normal) was used instead, with two disclosed caveats: its
positive events are near-misses (not crashes), and its native sampling rate is ~4 Hz (measured
directly) — ~12x below this pipeline's target, and far below every other source used. See
`data/external_simra_bicycle_raw/ATTRIBUTION.md`.

`results/external-validation/external_test_simra_dataset.json`, 45 sessions, 156,617 windows — deployed operating
thresholds predict zero positives here (too conservative for this very different distribution), so
F1/precision/recall are uninformatively 0.000 across every policy. The threshold-independent
ranking metrics still tell a real, consistent story:

| Signal | Window ROC-AUC | Window PR-AUC |
|---|---|---|
| Model A — classifier alone | 0.465 | 0.131 |
| Model A — reconstruction alone | **0.673** | **0.194** |
| Model B — classifier alone | 0.443 | — |
| OR/hierarchical combinations | ~0.50 (chance) | ~0.14 |

**Reconstruction is again the best-ranking signal — a third independent dataset, domain, and
anomaly type pointing the same direction as DaRUS (§12) and the scooter dataset (§21)**, though
weaker and read as suggestive given the disclosed caveats, not equated with the first two.
