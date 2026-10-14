# Project status

Last reviewed: 2026-10-14.

## Status at a glance

| Area | Status | Evidence |
|---|---|---|
| Data and manifest validation | Implemented | subject/session leakage and path validation tests |
| UTA-RLDD preprocessing | Implemented and exercised locally | 60 subjects, 182 videos in the private corpus |
| MRL Eye pretraining | Implemented and exercised locally | subject-disjoint auxiliary evaluation |
| Temporal fusion training | Implemented and exercised locally | recovery, provenance, prediction, and audit artifacts |
| Calibration and metrics | Implemented | validation-only temperature scaling and class-wise metrics |
| ONNX export | Implemented | PyTorch/ONNX parity tests and local exported bundles |
| Partial INT8 quantization | Implemented | parity-gated operator selection |
| Causal event replay | Implemented and exercised locally | full-video replay and cached threshold frontier |
| Live camera application | Implemented | shared preprocessing/model/controller contracts |
| Raspberry Pi end-to-end benchmark | Not completed | target-device claim intentionally withheld |
| External confirmation | Not completed | fold 1 is consumed; DROZY remains locked and unaccessed |
| Safety certification | Out of scope | research prototype only |

## Retained model

The retained development baseline is the quality-gated MobileNetV3/physiology fusion network with
a categorical cross-entropy objective. Pooled out-of-fold development performance across UTA-RLDD
D2-D5 is macro-F1 0.64212 over 146 videos from 48 subjects.

No investigated challenger passed all frozen screening gates. This is a valid negative research
outcome: experiment records are retained instead of selecting a favorable fold or metric after the
fact.

## Unresolved limitations

1. UTA-RLDD labels apply to complete videos, so window labels are temporally noisy and no true
   drowsiness-onset delay can be measured.
2. Low vigilance is consistently the weakest class.
3. Development screening used seed 13; the planned five-seed confirmation was not authorized
   because no candidate passed the development gate.
4. The auxiliary eye, yawn, pose, and quality heads are present but intentionally unsupervised in
   current configurations.
5. Event sensitivity depends strongly on the acceptable false-alert policy.
6. Cross-domain and motorcycle-specific generalization has not been established.
7. Full end-to-end latency, thermals, and power have not been measured on target hardware.

## Appropriate claims

It is accurate to describe the repository as an implemented and tested research platform for
causal, quality-aware driver drowsiness experiments. It is also accurate to report the documented
development metrics with their dataset, split, seed, and label limitations.

It is not accurate to call the model state of the art, externally validated, production ready,
medically diagnostic, safety certified, or proven on a motorcycle deployment.

## Recommended next research milestone

The highest-value next milestone is not another unregistered architecture search. It is a frozen
external-confirmation study using data with stronger temporal annotation, followed by an
end-to-end benchmark on the intended camera and Raspberry Pi-class device. Any new model hypothesis
should be specified before inspecting locked data and should retain the existing baseline and
failure records.
