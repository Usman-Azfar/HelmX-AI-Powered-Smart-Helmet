# Architecture

## Design goals

HelmX is designed around four constraints: causal operation, subject-independent evaluation,
graceful handling of poor input, and deployment on resource-constrained hardware. The architecture
keeps measurement, learned inference, and alert policy separate so each can be tested and audited.

## Processing pipeline

### 1. Face measurement

`MediaPipeFaceBackend` runs the MediaPipe Tasks FaceLandmarker in video mode. Landmark geometry is
computed in image-pixel space so eye-aspect ratio (EAR), mouth-aspect ratio (MAR), and pose
measurements do not mix normalized coordinates from unequal image dimensions.

The same observation also produces visual and physiological quality estimates. Missing or weak
landmarks do not become evidence of alertness; downstream code can suppress inference or enter the
`UNAVAILABLE` state.

### 2. Personal calibration and causal features

The runtime collects a neutral, forward-looking calibration sequence before prediction. Robust
personal baselines are fitted for eye, mouth, and pose measurements. `TemporalFeatureExtractor`
then maintains rolling history and emits 12 features:

- current and relative ocular state;
- PERCLOS and continuous closure duration;
- blink rate and blink-duration dynamics;
- current and relative mouth state;
- yawn-related dynamics;
- relative head-pose dynamics.

Feature computation is causal and uses timestamps rather than an assumed camera frame rate. A
minimum elapsed-time floor prevents unstable early blink-rate estimates.

### 3. Visual input

The configured visual region is converted to RGB, resized, normalized with ImageNet statistics,
and represented as `[batch, time, 3, height, width]`. Dual-eye experiments pack two square crops
along the width dimension; both eyes share the same encoder, and their embeddings are averaged so
left/right packing order cannot become a shortcut.

### 4. Multimodal temporal model

`QualityAwareTemporalNet` contains:

1. a MobileNetV3-Small visual encoder and projection;
2. a robust-scaled physiology projection;
3. a reliability gate over both embeddings and their measured qualities;
4. depthwise-separable causal residual temporal blocks with exponentially increasing dilation;
5. a three-class classification head.

The primary tensor contracts are:

| Input | Shape | Meaning |
|---|---|---|
| `frames` | `[B, T, 3, H, H]` or `[B, T, 3, H, 2H]` | face/eye imagery |
| `physiology` | `[B, T, 12]` | raw causal physiological features |
| `quality` | `[B, T, 2]` | visual and physiological reliability |
| `logits` | `[B, 3]` | alert, low-vigilance, drowsy scores |

The training-derived robust center and scale are stored in the checkpoint and exported graph.
Standardized physiology is clipped to a configured finite range before projection. Temperature
calibration is selected using validation data and embedded in the exported model.

Auxiliary eye-closure, yawn, head-pose, and quality heads exist in the representation but are
zero-weighted in the published configurations because the current primary manifests do not supply
independent targets for them. They must not be described as trained multi-task outputs.

### 5. Alert policy

`AlertController` converts calibrated drowsiness probability and quality into five states:

```text
UNAVAILABLE  ALERT  CAUTION  WARNING  CRITICAL
```

Transitions require probabilities to remain above or below configured thresholds for specified
elapsed durations. Separate enter/release thresholds provide hysteresis. Poor quality resets
detection timers and eventually enters `UNAVAILABLE`; warning audio is rate-limited by a cooldown.

Keeping this controller outside the neural network makes the sensitivity/false-alert trade-off an
explicit deployment policy instead of hiding it inside classifier metrics.

## Training and evaluation boundaries

Manifests are the boundary between preprocessing and model development. They identify dataset,
subject, session, path, label, and split. Validation rejects duplicates, missing paths, unsupported
labels, and subject leakage.

Training fits its physiology scaler on training rows only, records configuration and manifest
hashes, writes recovery checkpoints atomically, selects epochs on validation macro-F1, and fits
temperature on validation predictions. Test or locked external sets must not participate in those
decisions.

Window metrics alone are insufficient for deployment. The causal harness replays original videos
through neutral calibration, feature extraction, the exported ONNX model, and the same
`AlertController` used by the camera runtime. Replay traces can be cached and rescored to evaluate
alert policy without repeating video decoding or model inference.

## Deployment boundary

The supported export format is ONNX. `OnnxTemporalRunner` validates input/output names and runs the
model with bounded CPU threading. Quantization is deliberately limited to operators that pass the
configured probability and decision-parity gates; full convolution INT8 is not claimed.

The repository does not claim target-device performance until the complete camera-to-alert path is
benchmarked on the intended Raspberry Pi-class hardware.
