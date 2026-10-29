# M1/M2 — EMA cutoff sensitivity and causal Butterworth comparison (original output)

`ema_sensitivity.csv` is the original per-cutoff output of Sections M1/M2. It was produced on 2026-09-20 by `deploy/pi_research_suite/exp_final_replay_analysis.py`, `sections_m_ema_and_butterworth()`. A copy of that script is also kept in `piResults/experiments/core/`.

- **Rows:** 60, covering the 10 held-out test sessions × 6 filter variants (causal EMA at 0.1, 0.2, 0.3, 0.4 and 0.5 Hz, plus a causal 2nd-order Butterworth at 0.3 Hz).
- **Scores:** frozen INT8 HelmX, causal replay vs the offline zero-phase reference.
- **SHA-256:** `5b16c0a9748762d7ee94422f2d86eddd18f27f6c69a5fece1016bf1966206757`. Identical in the v1.0.0 Zenodo archive, `piResults2/final_pi_results/` (original Pi output) and `Final Results/`.

## Per-cutoff aggregate (recomputed from this CSV, 2026-10-28)

| Cutoff | Classifier MAE, session mean | Classifier MAE, window-weighted | Recon. MAE | Classifier corr.¹ | Decision flips (5,437 windows) | Same event outcome | Offline / causal events |
|---|---|---|---|---|---|---|---|
| EMA 0.1 Hz | 0.2725 | 0.0601 | 3.034 | 0.469 | 72 | 8/10 | 5 / 7 |
| EMA 0.2 Hz | 0.2084 | 0.0454 | 2.506 | 0.682 | 29 | 10/10 | 5 / 5 |
| **EMA 0.3 Hz (deployed)** | **0.1803** | **0.0408** | **2.286** | **0.759** | **21** | **10/10** | **5 / 5** |
| EMA 0.4 Hz | 0.1758 | 0.0374 | 2.240 | 0.776 | 12 | 9/10 | 5 / 4 |
| EMA 0.5 Hz | 0.1779 | 0.0372 | 2.171 | 0.777 | 10 | 9/10 | 5 / 4 |
| Causal Butterworth 0.3 Hz | 0.0481 | 0.0405 | 2.200 | 0.866 | 21 | 10/10 | 5 / 5 |

¹ The mean excludes `darus_crash_Iso_115_Out`, whose correlation is undefined (zero variance).

**Event-level disagreements**
- At 0.4 and 0.5 Hz, the causal pipeline misses the `fall_fall-in-a-leaning` crash event.
- At 0.1 Hz it adds false events in `darus_non_crash_Pothole_5_Out` and `darus_non_crash_Randomstate_60_Out`.

**Consistency with earlier reports**
- The session-mean values match `../README.txt` finding 4.
- The window-weighted 0.3 Hz value matches the Section C replay mean probability difference (0.0408).

The same protocol applied to three simple non-neural detectors is in `results/experiments/BASELINE_AND_FILTER_SENSITIVITY.md` §2d (`baseline_filter_sensitivity.csv`). For the learned baseline, 0.3 Hz is also on the flat part of the curve, and the higher cutoffs lose the same `fall-in-a-leaning` event.
