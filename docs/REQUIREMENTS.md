# Requirements and verification status

"Implemented" means the repository contains the behavior and automated software tests.
"Evaluated" means it has been exercised against the documented local research data. "Validated"
is reserved for frozen external evidence or target-hardware measurements. These terms are not
interchangeable.

## Functional requirements

| ID | Requirement | Current status | Remaining evidence |
|---|---|---|---|
| FR-01 | Timestamped camera capture independent of reported FPS | Implemented | target-camera endurance test |
| FR-02 | Face tracking with explicit obstruction state | Implemented | visor, eyewear, pose, day/night study |
| FR-03 | Pixel-space EAR, MAR, and head pose | Implemented and tested | landmark annotation study |
| FR-04 | Per-rider neutral calibration | Implemented and tested | repeatability study |
| FR-05 | Causal blink, PERCLOS, closure, mouth, pose, and validity features | Implemented and tested | behavior annotation comparison |
| FR-06 | Three-stage temporal classification | Implemented and development-evaluated | locked external confirmation |
| FR-07 | Quality-aware appearance/physiology fusion | Implemented and ablated | cross-domain missing-modality study |
| FR-08 | Elapsed-time persistence, hysteresis, release, and cooldown | Implemented and event-evaluated | target-context acceptance study |
| FR-09 | Explicit unavailable-monitoring state | Implemented and tested | physical obstruction test |
| FR-10 | Non-blocking cross-platform alarm path | Implemented | target operating-system test |
| FR-11 | Named ONNX export and portable inference | Implemented and parity-tested | target-device benchmark |
| FR-12 | Local inference without default video retention | Implemented by design | deployment privacy review |
| FR-13 | Mobile, LED, or vibration integration | Not implemented | interface and hardware definition |

## Research requirements

| ID | Requirement | Status |
|---|---|---|
| RR-01 | Subject/session leakage rejection and audited split provenance | Implemented |
| RR-02 | Preserve configs, seeds, manifests, checkpoints, predictions, and hashes | Implemented for local runs |
| RR-03 | Compare declared architecture/training alternatives under frozen gates | Completed for 14 candidates |
| RR-04 | Five seeds with subject-clustered intervals | Not reached; development gate did not authorize confirmation |
| RR-05 | Untouched external confirmation | Not completed |
| RR-06 | Failure analysis and negative-result retention | Implemented and documented |
| RR-07 | Macro-F1, balanced accuracy, MCC, class-wise and ranking metrics | Implemented |
| RR-08 | Calibration and validation-only threshold selection | Implemented |
| RR-09 | Event sensitivity, false alerts/hour, unavailable time, and within-clip timing | Implemented |
| RR-10 | FP32/INT8 size, RAM, latency, power, and thermals on target hardware | Partially implemented; hardware evidence pending |

## Engineering targets, not achieved claims

- Raspberry Pi p95 end-to-end latency below 150 ms at the configured sampling rate.
- Monitoring availability above 95% in every declared supported condition.
- Frozen external-set ECE below 0.05 after validation-only calibration.
- A preregistered sensitivity target at fewer than one false alert per operating hour.
- An eight-hour target-device soak test with bounded memory and clean resource release.

## Evidence still required for deployment claims

1. Confirmation on a locked, appropriately licensed external dataset.
2. A consented in-helmet RGB/IR dataset for motorcycle-specific claims.
3. Multi-seed confirmation of any model that first passes development screening.
4. Demographic, illumination, eyewear, occlusion, and camera-placement subgroup analysis.
5. End-to-end latency, memory, temperature, power, and endurance measurements on target hardware.
6. Human-factors evaluation of alert thresholds and modalities.
7. Independent safety, privacy, and security review before operational use.
