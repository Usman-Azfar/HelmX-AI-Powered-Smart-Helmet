# Experiment Coverage Matrix

The complete narrative test catalogue is in
[`results/COMPLETE_RESULTS.md`](../results/COMPLETE_RESULTS.md). This matrix verifies that each
campaign represented there has both a public result location and, where available, its scripts.

| Campaign | Test identifiers / scope | Public results | Scripts |
|---|---|---|---|
| Foundational compute and replay | A1-A5, B-D, pipeline, thermal, logging, robustness, revalidation | `results/foundational/` | `experiments/core/` |
| Physical live sensor | 4.1-4.8, W2-LIVE-1/2/3, motion, trigger, high-range follow-up | `results/foundational/`, `results/final-validation/` | `experiments/core/`, `experiments/final-validation/` |
| Final validation | A-R | `results/final-validation/` | `experiments/final-validation/`, `experiments/scheduler-study/` |
| Acquisition and sensor closure | A1, B1-B5, C1-C4 | `results/final-closure/01_*` through `08_*` | `experiments/closure/` |
| OS, scheduler, and acquisition modes | D1-D4, E1-E3, F1-F2, H1-H2, I1-I2, J1-J3, K1-K2 | Corresponding `results/final-closure/` named directories | `experiments/closure/`, `experiments/scheduler-study/` |
| Model and fidelity closure | L1-L10 | `results/final-closure/model_L1/` through `model_L10/` | `experiments/closure/` |
| Provenance closure | M1-M4 | `results/final-closure/provenance_M1/` through `provenance_M4/` | `experiments/closure/` |
| Presentation artifacts | N1-N5 | `results/final-closure/presentation_N1/` through `presentation_N5_high_range/`; `figures/final-closure/` | `experiments/closure/` |
| GPIO and trace timing | O1, O2/G | `results/final-closure/gpio_O1/`, `gpio_G_O2/` | `experiments/closure/`, `experiments/core/` |
| Communications | P | `results/final-validation/gps_gsm_optional/`; documented as not performed | `experiments/final-validation/` |
| Review and publication status | Q1-Q4 | `results/final-closure/status_reconciliation/`, `documentation/status/` | `experiments/closure/` |

The report also includes failed, interrupted, discarded, and superseded attempts; their records are
retained in the relevant campaign directories or historical documentation rather than presented as
successful evidence.

