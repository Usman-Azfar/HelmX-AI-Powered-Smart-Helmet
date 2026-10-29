# Filter-sensitivity provenance and second-detector study

Two items requested for manuscript Version 1.1:

1. locate the original per-cutoff filter-sensitivity outputs behind the restored table;
2. apply the same validation protocol to a second, simpler detector (offline only).

---

## 1. Original filter-sensitivity outputs (Section M1/M2)

The per-cutoff outputs exist and are in the Zenodo archive.

| Item | Value |
|---|---|
| File | `piResults/results/final-validation/ema_sensitivity/ema_sensitivity.csv` |
| Path inside the Zenodo zip | `HelmX_IEEE_Sensors_Reproducibility_v1.0.0/piResults/results/final-validation/ema_sensitivity/ema_sensitivity.csv` |
| Size / timestamp | 7,640 bytes, 2026-09-20 18:42 |
| SHA-256 | `5b16c0a9748762d7ee94422f2d86eddd18f27f6c69a5fece1016bf1966206757` |
| Generating code (also in the zip) | `deploy/pi_research_suite/exp_final_replay_analysis.py`, `sections_m_ema_and_butterworth()` |
| Content | 60 rows = 10 held-out test sessions × (EMA 0.1, 0.2, 0.3, 0.4, 0.5 Hz + causal 2nd-order Butterworth 0.3 Hz) |

The same SHA-256 was found in four places: the released zip, `piResults/`, `piResults2/final_pi_results/` (the original Pi output), and `Final Results/`.

**Per-cutoff aggregate, recomputed from the archived CSV.** These are frozen INT8 HelmX scores from causal replay, compared against the offline zero-phase reference.

| Cutoff | Classifier MAE (mean of sessions) | Classifier MAE (window-weighted) | Recon. MAE | Classifier corr.¹ | Decision flips (5,437 windows) | Sessions with same event outcome | Offline / causal events fired |
|---|---|---|---|---|---|---|---|
| EMA 0.1 Hz | 0.2725 | 0.0601 | 3.034 | 0.469 | 72 | 8/10 | 5 / 7 |
| EMA 0.2 Hz | 0.2084 | 0.0454 | 2.506 | 0.682 | 29 | 10/10 | 5 / 5 |
| **EMA 0.3 Hz (deployed)** | **0.1803** | **0.0408** | **2.286** | **0.759** | **21** | **10/10** | **5 / 5** |
| EMA 0.4 Hz | 0.1758 | 0.0374 | 2.240 | 0.776 | 12 | 9/10 | 5 / 4 |
| EMA 0.5 Hz | 0.1779 | 0.0372 | 2.171 | 0.777 | 10 | 9/10 | 5 / 4 |
| Causal Butterworth 0.3 Hz | 0.0481 | 0.0405 | 2.200 | 0.866 | 21 | 10/10 | 5 / 5 |

¹ The mean excludes `darus_crash_Iso_115_Out`, whose correlation is undefined because its score has zero variance.

Cross-checks against already-published numbers:
- The mean-of-sessions MAE (0.273 at 0.1 Hz; 0.176–0.180 at 0.3–0.5 Hz) matches `final-validation/README.txt` finding 4.
- The window-weighted 0.3 Hz value (0.0408) matches the Section C replay "mean probability difference 0.0408".

Event-level disagreements in the archived file:
- At 0.4 and 0.5 Hz, the causal pipeline **misses** the crash event in `fall_fall-in-a-leaning`.
- At 0.1 Hz it **adds** false events in `darus_non_crash_Pothole_5_Out` and `darus_non_crash_Randomstate_60_Out`.
- 0.2 Hz, 0.3 Hz and the causal Butterworth agree with the offline reference on all 10 sessions.

To reproduce from frozen code, run `deploy/pi_research_suite/exp_final_replay_analysis.py` with the data installed per `data/README.md`. This was not re-run in this pass because the archived output was found. Note that the script overwrites the archived file in place.

---

## 2. Second, simpler detector under the same protocol (offline)

**Script:** `scripts/baseline_simple_detector.py`
**Outputs:** `results/experiments/baseline_simple_detector.json`, `results/experiments/baseline_filter_sensitivity.csv`

**No Raspberry Pi runs.** The study reuses the frozen pipeline unchanged:
- the same session split (seed 42), windowing (60/15) and canonical units;
- thresholds calibrated on validation only (F1-optimal, as `train.py`);
- the same metric functions;
- the deployed event rule: 3 consecutive windows, 60 s cooldown, real exposure hours;
- the same frozen external sets and loaders, with no retraining or recalibration;
- the same unseen-DaRUS protocol;
- the same causal-filter replay, using the deployed `CausalGravityFilter`.

**Detectors:**

| Name | Definition | Parameters |
|---|---|---|
| `accel_peak_rule` | peak \|a\| (gravity removed) in the 1.2 s window ≥ threshold | 1 (threshold 11.18 m/s²) |
| `gyro_peak_rule` | peak \|ω\| in the window ≥ threshold | 1 (threshold 9.22 °/s) |
| `logreg_7feat` | standardized logistic regression on 7 window statistics (accel/gyro magnitude mean, std and peak; peak jerk), trained on the train split, C = 1, class-balanced | 8 |

**Fidelity check.** HelmX is re-scored by the same code in this run. All 8 checks against the archived JSONs match exactly. These cover test F1, ROC-AUC and false alerts per hour; scooter and SimRa ROC-AUC and OR-rule event recall; and STRIDE false-alert events.

### 2a. Held-out test split
The split has 10 sessions, 5,437 windows (143 positive) and 0.418 h of normal riding.

| Detector | ROC-AUC | PR-AUC | F1 | Recall @95% spec. | Event recall (5 crash sessions) | False alert events | False alerts/h |
|---|---|---|---|---|---|---|---|
| HelmX classifier | 0.946 | 0.539 | 0.333 | 0.685 | 5/5 | 0 | 0.0 |
| HelmX deployed OR rule | — | — | 0.331 | — | 5/5 | 0 | 0.0 |
| accel_peak_rule | 0.661 | 0.131 | 0.107 | 0.182 | 4/5 | 12 | 28.7 |
| gyro_peak_rule | 0.432 | 0.022 | 0.051 | 0.000 | 5/5 | 28 | 67.0 |
| logreg_7feat | 0.830 | 0.156 | 0.152 | 0.245 | 4/5 | 7 | 16.8 |

- **Paired F1 difference against the HelmX classifier, with a session-clustered bootstrap.** This is the primary interval. Whole sessions are resampled with their windows kept intact, using 10,000 resamples. The bootstrap is stratified: 5 sessions containing crash-like windows and 5 all-normal sessions are resampled separately, so every resample has positives. The script is `scripts/session_bootstrap.py`, the output is `session_bootstrap.json`, and the per-window predictions are in `heldout_window_predictions.csv`.

  | Detector | F1 difference | 95% CI, session-clustered | 95% CI, window-level (superseded) |
  |---|---|---|---|
  | accel_peak_rule | −0.227 | **[−0.770, −0.052]** | [−0.296, −0.156] |
  | gyro_peak_rule | −0.283 | **[−0.944, +0.342]** | [−0.370, −0.191] |
  | logreg_7feat | −0.181 | **[−0.597, −0.035]** | [−0.253, −0.110] |
  | HelmX deployed OR rule | −0.002 | [−0.024, 0.000] | [−0.006, 0.000] |

  - **Interval width:** clustering by session widens the intervals 3–7×.
  - **Significance:** accel_peak_rule and logreg_7feat remain significantly worse than HelmX. In none of the 10,000 resamples does either reach HelmX's F1. gyro_peak_rule is **no longer significant**; it is at least as good as HelmX in 7.6% of resamples.
  - **Unstratified version** (all 10 sessions together; 10 of 10,000 resamples had no positives and were skipped): same conclusions. The CIs are [−0.851, −0.049], [−0.950, +0.441] and [−0.732, −0.034].
  - **HelmX's own F1** has a session-clustered 95% CI of [0.19, 0.95].
  - **Fragility:** with only 10 clusters the intervals are approximate. HelmX's advantage over logreg and accel-peak rests mainly on one session: in `near_fall_Acceleration On Curve` HelmX finds 11 TP, both baselines 0. It also rests on HelmX producing no false positives in the 5 all-normal sessions, where logreg_7feat has 57 and accel_peak_rule 171.
  - The earlier window-level intervals (2,000 resamples) were [−0.292, −0.156], [−0.370, −0.194] and [−0.250, −0.109]. They treated overlapping windows as independent and should no longer be cited.
- **At the high-recall (0.90) operating point**, every baseline reaches 5/5 event recall, but with 14–28 false alert events (33.5–67.0 per hour).
- **The OR rule's ROC/PR are not reported.** It is a binary decision, so its ROC/PR values (0.601/0.205 in the JSON) are not comparable with the score-based rows.

**Results by label source.** These control for label circularity: outside DaRUS, positive windows are the top 30% by peak |a| within each session, which is `accel_peak_rule`'s own score.

| Detector | DaRUS only (30 windows, 12 with true impact labels): ROC-AUC / F1 / spec. | Excluding DaRUS (5,407 windows): ROC-AUC / F1 / spec. |
|---|---|---|
| HelmX classifier | 0.926 / 0.923 / 0.889 | 0.942 / 0.230 / 1.000 |
| accel_peak_rule | 0.981 / 0.585 / 0.056 | 0.632 / 0.041 / 0.970 |
| gyro_peak_rule | 1.000 / 0.667 / 0.333 | 0.399 / 0.046 / 0.095 |
| logreg_7feat | 0.944 / 0.585 / 0.056 | 0.817 / 0.055 / 0.991 |

On the 30 DaRUS windows, the simple rules rank windows as well as HelmX or better (ROC-AUC 0.94–1.00). However, at thresholds calibrated on validation they flag nearly every DaRUS non-crash window (specificity 0.06–0.33). The DaRUS stratum is very small.

### 2b. Frozen external sets (no retraining, no recalibration)

| Set | Detector | ROC-AUC | Event recall | False alert events | False alerts/h | False alerts/km |
|---|---|---|---|---|---|---|
| STRIDE (14 normal sessions, 0.290 h, 4.1 km) | HelmX classifier | — | — | 1 | 3.44 | 0.24 |
| | accel_peak_rule | — | — | 2 | 6.89 | 0.49 |
| | gyro_peak_rule | — | — | 26 | 89.6 | 6.35 |
| | logreg_7feat | — | — | 1 | 3.44 | 0.24 |
| Scooter (9 crash / 5 normal, 0.493 h) | HelmX classifier | 0.774 | 6/9 | 4 | 8.1 | — |
| | HelmX OR rule | — | 8/9 | 7 | 14.2 | — |
| | accel_peak_rule | 0.838 | 9/9 | 14 | 28.4 | — |
| | gyro_peak_rule | 0.698 | 9/9 | 25 | 50.7 | — |
| | logreg_7feat | 0.767 | 9/9 | 15 | 30.4 | — |
| SimRa (20 near-miss / 25 normal, 7.01 h, ~4 Hz native) | HelmX classifier | 0.465 | 0/20 | 16 | 2.28 | — |
| | HelmX OR rule | — | 0/20 | 16 | 2.28 | — |
| | accel_peak_rule | 0.724 | 0/20 | 6 | 0.86 | — |
| | gyro_peak_rule | 0.618 | 17/20 | 355 | 50.6 | — |
| | logreg_7feat | 0.408 | 0/20 | 7 | 1.00 | — |

### 2c. Unseen-DaRUS protocol
The baselines are retrained without DaRUS and tested on all 39 DaRUS sessions (25 crash, 14 non-crash).

| Detector | ROC-AUC | PR-AUC | Event recall | Non-crash sessions with ≥1 alert |
|---|---|---|---|---|
| HelmX classifier (archived) | 0.352 | 0.448 | 7/25 (0.28) | 9 alert events² |
| HelmX reconstruction branch (archived) | 0.868 | 0.889 | — | — |
| accel_peak_rule | 0.870 | 0.905 | 24/25 | 14/14 |
| gyro_peak_rule | 0.934 | 0.952 | 25/25 | 14/14 |
| logreg_7feat | 0.800 | 0.739 | 25/25 | 14/14 |

² The archived JSON reports alert events, not sessions.

Per-hour rates are not meaningful here: DaRUS non-crash sessions are short padded snippets totalling 0.012 h. HelmX's archived run shows 771/h for the same reason, and every baseline shows 1,200/h.

### 2d. Causal-filter sensitivity (M1/M2 protocol, 10 test sessions)

| Detector | Cutoff | Window-weighted score MAE / threshold | Decision flips | Sessions with same event outcome |
|---|---|---|---|---|
| accel_peak_rule | EMA 0.1 / 0.2 / **0.3** / 0.4 / 0.5 Hz | 0.076 / 0.053 / **0.044** / 0.042 / 0.044 | 158 / 60 / **56** / 45 / 55 | 10/10 at every cutoff |
| | causal Butterworth 0.3 Hz | 0.051 | 77 | 10/10 |
| logreg_7feat | EMA 0.1 / 0.2 / **0.3** / 0.4 / 0.5 Hz | 0.044 / 0.026 / **0.019** / 0.017 / 0.016 | 31 / 14 / **11** / 13 / 17 | 8 / 10 / **10** / 9 / 9 (of 10) |
| | causal Butterworth 0.3 Hz | 0.019 | 15 | 9/10 |
| gyro_peak_rule | all cutoffs | 0 (gyro is not filtered) | 0 | 10/10 (control) |

`logreg_7feat` shows the same event-level pattern as HelmX:
- At 0.1 Hz, the causal pipeline adds false events, in `carla_onder` and `near_fall_Acceleration On Curve`.
- At 0.4 and 0.5 Hz, and with the causal Butterworth, it misses the `fall_fall-in-a-leaning` crash.

The unweighted session mean for `accel_peak_rule` (in the JSON, about 0.9× threshold) is dominated by two 6-window DaRUS crash sessions with impact peaks of hundreds of m/s². Use the window-weighted value instead.

### Interpretation for the paper
- **The protocol runs on a second detector without modification.** It separates operating points that window metrics alone do not. For example, on the test split `logreg_7feat` has ROC-AUC 0.83 but 16.8 false alerts/h under the deployed rule, while HelmX has 0.
- **On the in-distribution test split, HelmX beats every simple baseline** at the deployed operating point. Under the session-clustered bootstrap, the gap is significant for logreg_7feat and accel_peak_rule but not for gyro_peak_rule, and with 10 sessions all intervals are wide.
- **On out-of-distribution sets, the simple rules generalize better than the HelmX classifier.** This holds for scooter, unseen DaRUS and SimRa ROC-AUC. It does not hold for STRIDE false alerts per km, where `logreg_7feat` equals HelmX. This parallels the paper's existing reconstruction-branch finding, and it is a result the paper should report rather than leave out.
- **The filter-cutoff conclusions are not specific to the HelmX network.** For the learned baseline, 0.3 Hz is also on the flat part of the curve, 0.1 Hz is clearly worse, and higher cutoffs and the causal Butterworth cost the same `fall-in-a-leaning` event.

### Caveats
- Single split and small test set (5 crash and 5 normal sessions). Confidence intervals are session-clustered, but 10 clusters remain few.
- Outside DaRUS, labels come from the peak-|a| heuristic, which makes `accel_peak_rule` partly circular there.
- The baselines use the deployed (per-sample) jerk definition consistently, so they do not share HelmX's documented training/runtime jerk-scale mismatch. That mismatch is quantified in closure test L11 (`piResults/results/final-closure/model_L11_jerk_isolation/`).
- No hardware latency or memory measurements for the baselines. These rules are trivially cheaper than the network, but that is not measured here.
