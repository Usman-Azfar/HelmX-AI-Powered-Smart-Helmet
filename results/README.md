# HelmX Results

This directory is the public, review-ready result package for HelmX. It separates headline model
metrics, controlled experiments, external validation, figures, and reproducibility metadata while
preserving the full numerical outputs behind the claims in the project documentation. Physical
device measurements and Pi-specific analyses are maintained separately in [`piResults/`](../piResults/).

The results are reported as research evidence, not as certification of a safety-critical product.
The system has not been validated on naturally occurring, unstaged motorcycle crashes.

## Headline results

### Held-out test split

The frozen test split contains 5,437 overlapping windows from ten recording sessions: 5,294
normal windows and 143 crash-like windows. Thresholds were selected on the validation split, not
on this test split.

| Signal / operating point | ROC-AUC | PR-AUC | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Classifier, balanced deployment threshold | 0.946 | 0.539 | 0.935 | 0.203 | 0.333 |
| Reconstruction error | 0.718 | 0.125 | 0.800 | 0.084 | 0.152 |
| Hybrid OR rule | — | — | 0.906 | 0.203 | 0.331 |

The low window-level recall should not be confused with event-level behavior. With the deployed
three-consecutive-window confirmation and 60-second cooldown, the balanced classifier detected all
five crash-like test sessions and produced zero alert events in five normal sessions covering
0.418 hours. That exposure is too short to establish a universal zero-false-alert rate.

Primary artifacts:

- [`test_metrics.json`](metrics/test_metrics.json)
- [`full_metrics.json`](metrics/full_metrics.json)
- [`seed_variance.json`](metrics/seed_variance.json)
- [`classifier_roc_pr.png`](figures/classifier_roc_pr.png)
- [`classifier_only_balanced_confusion_matrix.png`](figures/classifier_only_balanced_confusion_matrix.png)

### Robustness and generalization

The project deliberately includes negative results and out-of-distribution tests:

| Experiment | Main finding |
|---|---|
| Five-seed comparison | Classifier ROC-AUC was 0.951 ± 0.011 for the deployed hybrid model's classifier head. |
| Supervised-only Model B | In-distribution performance was approximately equal to, and on PR-AUC somewhat stronger than, hybrid variants. |
| DaRUS entirely unseen during training | Classifier ROC-AUC fell to about 0.35; reconstruction ROC-AUC reached about 0.87. |
| External scooter dataset | Reconstruction generalized best, but domain-shift false-alert rates were materially higher than on the original split. |
| Extended normal-road evaluation | One false alert over 0.708 hours, equivalent to 1.41 alerts/hour for that limited evidence set. |
| Hierarchical four-threshold policy | Improved validation F1 but degraded held-out performance, consistent with overfitting. |

See [`external-validation/`](external-validation/) and [`experiments/`](experiments/) for the
complete machine-readable results.

### Raspberry Pi 4 deployment

The deployed INT8 pipeline was tested on a Raspberry Pi 4 Model B with a physical MPU6050.

| Measurement | Result |
|---|---:|
| Long live soak | 180 minutes |
| Samples processed | 539,981 |
| Windows scored | 33,734 |
| Pipeline latency, p99 / maximum | 3.03 ms / 11.04 ms |
| Decision stride budget | 300 ms |
| Deadline misses | 0 |
| Sensor read failures / reconnects / exceptions | 0 / 0 / 0 |
| Maximum temperature | 55.0 °C |
| Thermal throttling | None observed |
| Offline-vs-streaming agreement | 99.61% per window; 100% per session |
| INT8-vs-Keras agreement at deployed threshold | 99.89% |

The soak used the then-evaluated 30 ms stream-gap threshold; the later deployment configuration
uses 60 ms. The raw artifact records the exact evaluated configuration, and the concise summary
calls out this distinction explicitly.

Primary artifacts:

- [`w2_live3_soak_summary.json`](../piResults/results/foundational/current/w2_live3_soak_summary.json)
- [`c_replay_validation.json`](../piResults/results/foundational/current/c_replay_validation.json)
- [`d_quantization_comparison.json`](../piResults/results/foundational/current/d_quantization_comparison.json)
- [`a1_isolated_inference.json`](../piResults/results/foundational/current/a1_isolated_inference.json)
- [`Raspberry Pi result package`](../piResults/README.md)

## Directory guide

| Directory | Contents |
|---|---|
| [`metrics/`](metrics/) | Core held-out metrics, model baselines, export footprint, and multi-seed variance. |
| [`figures/`](figures/) | Confusion matrices and ROC/precision-recall plots generated from the frozen evaluation. |
| [`experiments/`](experiments/) | Architecture, pretraining, loss-weighting, label-scarcity, feature, and policy ablations. |
| [`external-validation/`](external-validation/) | Unseen-crash, external scooter, SimRa, and extended false-alarm evaluations. |
| [`reproducibility/`](reproducibility/) | Dataset hashes, split assignments, seed, thresholds, and source revision metadata. |

Raspberry Pi hardware evidence is organized independently under [`piResults/`](../piResults/) so
model-development results and device-validation results have unambiguous ownership.

## Reading the evidence correctly

- A positive model window is not an SMS. Three consecutive positive windows start a local alarm;
  the rider then has 30 seconds to cancel before GPS/GSM escalation.
- Window-level metrics and event-level alert rates answer different questions. Overlapping windows
  must not be counted as independent real-world alerts.
- Zero observed events over a short exposure does not prove a zero underlying event rate.
- External-domain results are intentionally retained even when they are worse than the original
  test result.
- The reconstruction branch did not materially improve the in-distribution classifier, but it was
  substantially more robust in the project's two out-of-distribution crash evaluations.
- GPS/GSM delivery has not received the same completed physical smoke-test coverage as the sensor,
  model, decision policy, and GPIO path.

## Provenance

The JSON files are generated experiment outputs. The authoritative narrative interpretation is in
[`performance.md`](../performance.md), while implementation details are documented in
[`system_understanding.md`](../system_understanding.md). Dataset redistribution and derived-model
licensing constraints are described in [`DATA_LICENSES.md`](../DATA_LICENSES.md).

The original uncurated folder is retained locally as `results2/` and excluded from Git. Public
artifacts remove machine-specific absolute paths where those paths have no scientific meaning.
See [`PUBLICATION_NOTES.md`](PUBLICATION_NOTES.md) for the exact exclusion policy.

