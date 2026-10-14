# Verification record

This page distinguishes current software verification, historical engineering measurements, and
research evidence. A passing software test does not establish deployment safety or external model
validity.

## Current software gate

Verified on 2026-10-14 using Windows, Python 3.11.9, PyTorch 2.13.0+cu130, ONNX Runtime 1.29.0,
and an NVIDIA GeForce GTX 1650 development GPU:

- 150 automated tests passed;
- Ruff lint passed;
- Ruff formatting passed after applying the current formatter;
- strict MyPy passed over 54 source files;
- `pip check` reported no broken requirements;
- `configs/default.yaml` passed schema and cross-field validation;
- CUDA was available in the reference environment.

The suite covers archive safety, augmentation, split leakage, robust scaling, sequence loading,
sampling, loss masking, training recovery, model contracts, state-machine timing, causal replay,
metrics, calibration, bootstrap intervals, failure audits, ONNX export parity, and quantization
gates.

## Historical model engineering benchmark

Measured on 2026-08-28 using the same GTX 1650-class development machine. The configured input was
one sequence of 24 RGB crops at 160 x 160, 12 physiology features, and two quality channels.
Timings exclude capture, landmark extraction, preprocessing, display, and alarm playback.

| Backend | Samples | Median | p95 | Mean |
|---|---:|---:|---:|---:|
| PyTorch CUDA FP32 | 50 | 16.185 ms | 21.320 ms | 15.349 ms |
| ONNX Runtime CPU, 2 threads | 30 | 37.905 ms | 43.168 ms | 38.525 ms |

These are workstation model-only measurements. They are not Raspberry Pi latency, throughput,
thermal, memory, or power claims.

## Export parity

The original default-model export check measured a maximum absolute PyTorch/ONNX probability
difference of `8.94e-08` and verified a dynamic batch of two. The later selected UTA pilot bundle
measured a maximum probability difference of `1.49e-07` across 12 real held-out windows with 100%
argmax agreement. Export tests remain part of the current automated suite.

## MRL Eye auxiliary evidence

The official MRL Eye archive produced 84,898 indexed images from 37 subject IDs assigned to five
deterministic, disjoint folds. On the held-out auxiliary eye-state fold:

| Metric | Result |
|---|---:|
| Images | 30,629 |
| Accuracy | 0.954879 |
| Macro-F1 | 0.954677 |
| ROC-AUC | 0.991147 |

This demonstrates eye-state pretraining behavior only. It is not driver-drowsiness accuracy.

## Partial INT8 engineering result

The frame-pilot export accepted partial `MatMul`/`Gemm` quantization on a balanced 100-sample
parity set:

- 100% argmax agreement;
- maximum probability error `0.026860`;
- mean probability error `0.002012`;
- FP32 bundle size 4,542,161 bytes;
- partial-INT8 bundle size 4,373,257 bytes.

Full convolution activation quantization was tested and rejected because it changed too many
validation decisions. Full INT8 acceleration therefore remains unverified and would require a new
quantization-aware-training study.

## Drowsiness evidence

The authoritative development metrics and experiment outcomes are in
`FINAL_RESULTS_SUMMARY.md`. In brief, the retained categorical quality-gated model reached pooled
D2-D5 video macro-F1 0.64212 over 146 videos from 48 subjects. Its event sensitivity ranges from
33.33% at zero observed false alerts/hour to 58.33% at 0.49 false alerts/hour on the documented
development replay.

UTA fold 1 is consumed by an earlier preregistered confirmation and cannot be called untouched.
DROZY remains unaccessed. Five-seed confirmation, cross-domain performance, motorcycle-domain
performance, and target-device measurements are still pending because no development challenger
passed the gate that would authorize them.

## Known verification gaps

- no Raspberry Pi end-to-end camera-to-alert benchmark;
- no eight-hour target-device soak test;
- no external DROZY confirmation;
- no consented in-helmet dataset evaluation;
- no independent landmark-error or subgroup fairness study;
- no safety, medical, automotive, or regulatory certification.
