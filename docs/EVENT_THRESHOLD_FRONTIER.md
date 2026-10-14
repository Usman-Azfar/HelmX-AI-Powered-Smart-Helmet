# Event-level sensitivity/false-alarm operating-point frontier

Measured 2026-09-22 against the frozen D2 categorical checkpoint
(`runs/uta-multifold-screen/d2/categorical/seed-13/best.pt`, exported to
`artifacts/models/helmx_d2_categorical_seed13.onnx`) using the same fold-2 validation video set
already used for the original pilot's threshold tuning (`data/processed/uta-rldd-validation-videos.csv`,
36 videos, 12 validation-only subjects, balanced 12 alert / 12 low-vigilance / 12 drowsy). The causal
inference-trace cache is `runs/uta-multifold-screen/d2/categorical/seed-13/event_cache`. This
addresses the gap noted in `LABEL_CONFIDENCE_WEIGHTING_HYPOTHESIS.md`: the previously reported
16.67%/33.33% sensitivity figures were the *original pilot* checkpoint's numbers, never re-measured
against the current best (D2-D5 categorical) checkpoint family. Re-running the raw-video causal
replay against this checkpoint reproduces the same 16.67% raw / 33.33% zero-false-alarm-tuned
sensitivity, confirming the low event-level sensitivity is not specific to the older, weaker pilot
checkpoint.

## Method

`helmx-drowsiness tune-event-thresholds` was run against the existing cache with the historical scan
range (`warning_probability` in [0.40, 0.72], step 0.02, `warning_seconds` fixed at 2.0, the
preregistered release/caution/critical offsets preserved -- one degree of freedom, exactly as in the
original pilot tuning). Full report:
`runs/uta-multifold-screen/d2/categorical/seed-13/event_threshold_frontier.json`, SHA-256
`078615F96A9EC4FB34A77D763B00A15FA70BC64DFA18D09FA82A3B21F1C4C498`.

The built-in selection criterion (as used for the pilot) requires *zero* observed validation
false-alert events, which is what produces the 33.33% headline figure. The tool records every
scanned operating point, not only the zero-false-alarm one, so the full sensitivity/false-alarm
trade-off can be read directly from `candidates` in that report without any retraining or code
change.

## Frontier (17 scanned operating points, all at warning_seconds=2.0)

| False-alert-event budget (validation) | Best sensitivity | Detected/true events | False alerts/hour | warning_probability |
|---|---|---|---|---|
| 0 (current default) | 33.33% | 4/12 | 0.000 | 0.66 |
| <=1 | **58.33%** | 7/12 | 0.490 | 0.62 |
| <=2 | 58.33% | 7/12 | 0.490 | 0.62 |
| <=5 | 66.67% | 8/12 | 2.451 | 0.58 |
| unconstrained | 100.00% | 12/12 | 3.922 | 0.42 |

## Interpretation

Allowing one false-alert event across the 2.040 alert-video hours in this validation set (0.49 false
alerts/hour, i.e. roughly one false alert per two hours of alert driving) raises sensitivity from
33.33% to 58.33% -- a larger gain than any of the nine rejected training-time candidates produced,
and it requires no retraining: it is a different, still validation-only-selected point on the same
model's existing operating curve. This is consistent with the root-cause diagnosis in
`LABEL_CONFIDENCE_WEIGHTING_HYPOTHESIS.md` and the earlier failure audits: the bottleneck is the
threshold policy interacting with a weak per-window probability signal, not model capacity, and a
zero-false-alarm requirement on this dataset is a very strong constraint relative to what the
underlying classifier can support.

This frontier is reported, not prescribed: choosing an operating point is a product/safety decision
(false alarms have a real cost to rider trust) as much as a modeling one, and belongs in the thesis
as an honest trade-off curve rather than a single cherry-picked number. It has not been re-verified
against fold 1 or DROZY; like the rest of the D2-D5 development-only work, it remains a development
validation-set measurement only.
