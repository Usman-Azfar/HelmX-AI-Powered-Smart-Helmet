# HelmX Crash Detection — System Understanding

Internal reference document explaining how the complete system works, end to end: what each
piece does, why it's built this way, and how the pieces connect. This is the "read this to
actually understand the codebase" document — `README.md` is the public-facing summary,
`performance.md` is the numbers.

## 1. What the system does

A rider wears/mounts an MPU6050 IMU (accelerometer + gyroscope) on the motorcycle. A model
continuously watches the last ~1.2 seconds of motion, decides whether it looks like a crash, and
if so — after a few consecutive confirmations to avoid one bad reading triggering an alert —
starts a local buzzer/vibration alarm with a 30-second cancellation window. If the rider is
conscious and it wasn't a real crash, they cancel by voice (a separate voice-assistant module);
only if the window expires uncancelled does it send an SMS with the GPS location to an emergency
contact via a GSM module. See §8 for how the cancellation window is implemented and why it
exists.

Two parts:
1. **Offline**: build a dataset from several sources, train a model, calibrate decision
   thresholds, export it to a small on-device format. (`src/`, `scripts/`, the two notebooks.)
2. **Online**: run that exported model on a Raspberry Pi, reading the sensor continuously and
   sending an alert when it decides a crash happened. (`deploy/`.)

## 2. The core design decision: hybrid unsupervised + supervised

Two ways to catch a crash from sensor data:

- **Unsupervised (autoencoder)**: train a model to reconstruct *normal* riding. Anything it
  reconstructs badly is "not normal" — could be a crash, could be anything else unusual. Doesn't
  need labeled crash examples, but is a blunt instrument: it can't tell "bump in the road" from
  "actual crash," it can only tell "unusual from normal."
- **Supervised (classifier)**: train a model to directly recognize crash-like patterns from
  labeled examples. Sharper, but needs labeled crash data — and can only recognize patterns
  similar to what it was shown.

This system does both with one shared encoder (`src/model.py: build_model`):

```
seq (60, 6) ──▶ Conv1D encoder ──▶ bottleneck ──▶ decoder ──▶ reconstruction (60, 6)
                     │                                              │
                     │                                    per-window MSE vs input
                     │                                              │
                     ▼                                              ▼
              pooled embedding (64) ──┬── recon_error (1) ──┐
                                       │                     │
              aux stats (7) ──────────┴─────────────────────┴──▶ concat (72) ──▶ Dense(32) ──▶ crash_prob (1)
```

- The **decoder** only ever gets gradient signal from normal-labeled windows (`sample_weight`
  in `scripts/train.py`), so it specializes in reconstructing normal riding — a window it
  reconstructs badly is a genuine anomaly signal, independent of whether that anomaly type was
  ever labeled.
- The **classifier head** sees every labeled window, plus three extra signals: the pooled
  encoder embedding (what the network "sees" in general), `recon_error` (how anomalous the
  autoencoder found it), and 7 hand-engineered stats (`src/features.py`,
  `manifest._windows_for_session`): mean/std/peak accel magnitude, mean/std/peak gyro
  magnitude, and peak jerk. These engineered stats matter because the classifier's raw signal
  is often noisy on a small dataset — obvious physical quantities like "how hard did this hit"
  give it a shortcut that doesn't have to be learned from scratch by the conv layers.

At inference time (`deploy/crash_monitor.py`), a window is flagged if *either* `crash_prob`
crosses its threshold *or* `recon_error` crosses its own threshold — the classifier drives most
detections, the reconstruction path is a backstop for crash types the classifier never saw a
labeled example resembling.

## 3. Data pipeline (`src/`)

### 3.1 The problem this pipeline solves

Five very different data sources need to end up as directly comparable `(60, 6)` windows:
CARLA simulation output, real Android-phone sensor logs, staged fall/near-fall recordings from a
tab-separated export, and physics-simulated collision data from a research dataset. Each has a
different native sample rate, different units, different gravity conventions, and (for two of
the sources) file-level rather than per-timestamp crash labels.

### 3.2 Loading (`src/io_loaders.py`)

Each loader returns a list of `Session` objects — one per recording/scenario — with a
`pandas.DataFrame` of `[t, ax, ay, az, gx, gy, gz]` already resampled onto a uniform time grid
using the file's *own* real timestamps (`src/resampling.py`), never assumed row-order timing,
except for CARLA which genuinely has no timestamp column (`config.CARLA_ASSUMED_RATE_HZ`,
documented as an assumption).

- `load_carla()`: groups by driver (the `class` column), one session per driver.
- `load_road_folder()`: walks `data/road/`, pairs each `Accelerometer.csv`/`Gyroscope.csv`,
  and **time-aligns them independently** via `resample_two_streams` rather than truncating both
  to the same row count (the original bug this fixed: two separately-logged streams don't
  necessarily share a sample-for-sample correspondence). Skips `*-Copy1*` duplicate folders.
- `load_fall_like_folder()`: parses the tab-separated, latin1-encoded fall/near-fall exports.
- `load_darus()`: parses the DaRUS `.tab` files, keeps the real per-timestep `CrashLabelML`
  column as `Session.frame_labels`, and pads short traces (`_pad_centered`) so the sliding-window
  loop can actually see them — see §3.4.

### 3.3 Making sources comparable (`src/units.py`, `src/preprocess.py`)

Two real bugs existed in the original version of this pipeline and are fixed here:

- **Gyro units**: CARLA and the Android road logs report rad/s; the fall/near-fall exports and
  the deployed MPU6050 library both report deg/s. `units.gyro_to_deg_per_s` converts everything
  to deg/s (the canonical unit, chosen because that's what the real sensor reports).
- **Accelerometer gravity convention**: CARLA's accelerometer includes gravity (~9.8 m/s²
  baseline on the vertical axis); the phone logs appear to already be gravity-compensated.
  Rather than trust that every source's convention is known and consistent,
  `units.remove_gravity` applies the *same* high-pass Butterworth filter (0.3Hz cutoff) to every
  source's accelerometer stream. A source that's already gravity-free passes through with only a
  minor edge transient; a source with gravity baked in gets it removed. This makes the pipeline
  robust to not knowing a new source's convention in advance.

`preprocess.canonicalize()` runs both, then `features.add_derived_columns` appends
`accel_mag`, `gyro_mag`, `jerk` — used both as engineered classifier inputs and as the
`severity` signal for weak-label refinement (§3.4).

### 3.4 Labeling (`src/manifest.py: _windows_for_session`)

Two labeling regimes, chosen automatically per session:

- **Real per-timestep ground truth** (`Session.frame_labels`, currently only `data/darus/`):
  a window is crash-like if it contains *any* labeled-positive instant. Not majority vote —
  DaRUS crash events are often only 1-3 resampled samples long, so requiring the majority of a
  60-sample window to be positive would systematically discard genuine crash windows.
- **No ground truth** (`data/near-fall/`, `data/fall/`, whole-file labels only): the file says
  "this recording contains a fall," but most of a fall recording is ordinary riding before/after
  the event. Training the classifier on that file-level label directly means feeding it a large
  fraction of mislabeled "crash" windows that actually look completely normal. Instead, only the
  top `config.ANOMALY_TOP_FRACTION` (30%) of windows *by peak accel magnitude within that
  session* keep the positive label; the rest get relabeled normal. This is a heuristic, not
  ground truth — documented as a limitation in `README.md`.

### 3.5 Splitting (`src/manifest.py: assign_splits`)

Splits happen at the **session** level (whole recordings), stratified by `(source, label)`, not
at the window level. The original version of this pipeline split after windowing, which let
windows from the same recording land in both train and validation — since adjacent windows
overlap (75% stride overlap) and come from the same few seconds of physical motion, that's
leakage: the model could partly "memorize" a recording rather than generalize.

### 3.6 The DaRUS padding problem (`src/io_loaders.py: _pad_centered`)

Worth explaining in detail because it's non-obvious. DaRUS crash traces are genuine
high-fidelity collision physics, but captured over 0.05–0.25 seconds at ~2000Hz — far shorter
than the 60-sample/1.2s window this whole pipeline is built around. Two problems, both real bugs
caught during development:

1. Naively resampling a 0.05s trace to 50Hz produces only 1-3 samples total — almost the entire
   trace collapses to nothing, discarding nearly all the signal.
2. If those few real samples are placed at one edge of a padded sequence, the sliding-window
   loop (`range(0, len(df) - window, stride)`) systematically never covers the last `window`
   samples — the real data would never appear in any window at all.

The fix: pad with edge-repeated values (a defensible stand-in for "ordinary riding around this
brief trace") on **both** sides, computed with correctly-spaced synthetic timestamps (not
duplicated ones — duplicate timestamps break `np.gradient`'s jerk calculation via division by
zero, a bug this pipeline hit and fixed), so the real data sits away from the boundary and
several overlapping stride-15 windows land on it.

## 4. Model training (`scripts/train.py`, `notebooks/crash-detection-model.ipynb`)

Standard Keras `fit()`, with two non-obvious pieces:

- **Per-output `sample_weight`**: the decoder only trains on normal windows
  (`recon_w = (y == 0)`), the classifier trains on everything with class-balanced weights
  (`compute_sample_weights` in `src/model.py`) so the (much rarer) crash windows aren't drowned
  out by the majority-normal class.
- **`recon_error` as a third model output with `loss_weight=0`**: Keras 3 requires every named
  output to appear in the loss dict; `recon_error` doesn't need its own loss (it's a convenience
  view into `reconstruction`'s error), so it's given a real loss function pointed at dummy
  all-zero targets and zeroed out via `loss_weights` — see the comment in `src/model.py` for
  why the more obvious `loss: None` approach doesn't work on this Keras version.

Early stopping monitors `val_crash_prob_auc` (the classifier's discriminative power on held-out
data), restoring the best-AUC checkpoint's weights.

## 5. Threshold calibration (`scripts/train.py`, `src/evaluate.py`)

Three thresholds are calibrated on the **validation** split (never the training data, never the
test data) and saved to `models/thresholds.json`:

- `classifier_prob_balanced`: maximizes F1 — the deployed default.
- `classifier_prob_moderate_recall` / `classifier_prob_high_recall`: recall-targeted
  alternatives (60% / 90% recall floors), for deployments that want to bias further toward
  "never miss a crash" even at the cost of more false alarms.
- `recon_error`: the 99th percentile of the reconstruction error on **normal** validation
  windows — anything beyond what normal riding produces 99% of the time.

## 6. Evaluation (`scripts/evaluate_model.py`, `scripts/full_metrics.py`, `notebooks/model-check.ipynb`)

`evaluate_model.py` produces the day-to-day ablation (reconstruction-only vs. classifier-only at
each operating point vs. the hybrid OR-rule) plus a **deployed-alert simulation**
(`evaluate.simulate_deployed_alerts`) that replays the actual 3-consecutive-window + cooldown
rule session-by-session, because raw window-level false-positive rate wildly overstates how many
SMS messages the deployed device would actually send.

`full_metrics.py` computes the complete metrics suite (confusion matrix, accuracy, precision,
recall/specificity, F1/F2, balanced accuracy, MCC, ROC/PR-AUC, reconstruction MSE/RMSE/MAE,
reconstruction-error distribution by class, real detection latency from the DaRUS ground-truth
sessions, and inference benchmarks) for both train and test splits — this is what
`performance.md` is built from.

## 7. Edge export (`src/export.py`, `scripts/export_model.py`)

Converts the trained Keras model to TFLite via a **SavedModel export first**
(`model.export(tmp_dir)` then `TFLiteConverter.from_saved_model`), not the more obvious
`TFLiteConverter.from_keras_model` path — the direct path crashes the MLIR converter on this
TensorFlow/Keras 3 combination (`BatchNormalization` emits a `Cast` op the converter can't
type-infer). Two variants are produced: float16 (no calibration data needed) and int8
(calibrated against a sample of real normalized validation windows,
`export._representative_dataset`). Both keep float32 input/output signatures (no
`inference_input_type`/`inference_output_type` override), so `deploy/crash_monitor.py` never has
to do manual quantization/dequantization — it just calls the TFLite signature runner with plain
float32 arrays.

## 8. Real-time deployment (`deploy/crash_monitor.py`)

Runs as a continuous loop, not a one-shot script:

- **A model trigger is not an SMS — it's the start of a cancellable local alarm.**
  `handle_suspected_crash()` is what actually runs when the consecutive-window rule fires: it
  starts `LocalAlarm` (a buzzer or vibration motor on a GPIO pin, `DigitalOutputDevice` from
  `gpiozero`) and blocks for `alarm.countdown_seconds` (default 30s), polling
  `CancellationListener` every 0.2s. Only if that window expires without a cancellation does it
  fetch a GPS fix and send the SMS. This exists because a model that's ~71% precise at its
  deployed operating point (§3, `performance.md`) sending an SMS on every trigger would mean
  roughly 3 in 10 alerts go to an emergency contact for nothing — the cancellation window turns
  those into a two-second buzz the rider dismisses, and only escalates to a real message when
  either the rider is unresponsive (the actual crash case) or doesn't intervene.
- **The voice-assistant cancellation interface is a single file**, deliberately: `CancellationListener`
  just checks whether `alarm.cancel_signal_file` (default `/tmp/helmx_cancel_alert`) exists, and
  deletes it once consumed so a stale cancellation can't silently suppress a later, unrelated
  trigger. The voice-assistant module (built separately, outside this repo) only needs to
  create/touch that file when it recognizes the cancel phrase — no shared code, no socket
  server, no dependency in either direction. `LocalAlarm` degrades to a log-only no-op if
  `gpiozero`/GPIO access isn't available (e.g. running this off a Pi for testing), so the rest of
  the loop still runs.
- **The sensor buffer is dropped after a countdown**, not just resumed. `handle_suspected_crash`
  blocks the main loop for up to 30s, so `buffer` (the last `window_samples` readings) goes
  stale — it's a real time gap, not continuous motion. `main()` calls `buffer.clear()` and resets
  `new_samples`/`next_tick` right after, so the model doesn't score a window that silently spans
  the gap; the next real detection only happens once the buffer has refilled with `window_samples`
  contiguous post-countdown readings.
- **Sensor read failures** trigger a reconnect loop rather than crashing the process.
- **Gravity removal** in real time uses a *causal* approximation
  (`CausalGravityFilter`, an EMA-based high-pass) of the offline zero-phase Butterworth filter
  used at training time — the offline filter is non-causal (it needs future samples), which
  isn't available in a streaming loop. Same cutoff frequency, small phase-lag tradeoff,
  documented in the class docstring.
- **GPS acquisition** has a timeout; on timeout the SMS still sends with "location unavailable"
  rather than blocking indefinitely waiting for a fix.
- **GSM AT commands are verified**, not fire-and-forget: `GsmModule._read_response` actually
  reads the modem's reply and checks for `OK` before declaring an SMS sent.
- **An alert doesn't stop monitoring.** The original version of this script `break`-ed out of
  the loop after the first alert, permanently ending the safety monitoring for the rest of the
  ride. This version starts a cooldown instead, so it keeps watching for a second, independent
  event.
- **The model interface is the TFLite signature-runner API** (keyed by the `seq`/`aux` input
  names and `crash_prob`/`recon_error` output names from `src/model.py`), not raw tensor
  indices — indices shift between TF versions and quantization modes, names don't.

## 9. Known gaps (see also `README.md` → Known limitations, `performance.md` for numbers)

- Weight initialization and data shuffling are now fully seeded per-run (`scripts/train.py:
  _seed_everything`), but TensorFlow op-level nondeterminism means metrics still shift somewhat
  between retrains even at a fixed seed. Rather than treat any single run's numbers as exact, or
  chase full bit-exact determinism (which would also just hide real variance, not eliminate the
  underlying small-dataset instability), §10.3 below trains 5 different seeds and reports mean ±
  std — the story (balanced operating point ≈ high-recall's session recall, far fewer false
  alarms) has reproduced consistently across those seeds, but treat `performance.md`'s single-run
  table as one draw from that distribution, not a permanent fact.
- The supervised classifier does not generalize to crash mechanisms outside its training
  distribution — §10.4's unseen-crash experiment quantifies this directly (ROC-AUC 0.35, worse
  than chance, when DaRUS is fully held out of training). This was previously a theoretical
  concern (see the hybrid architecture's design rationale in §2); it's now a measured limitation.
- No data from a real, unstaged motorcycle crash exists anywhere in this pipeline — everything
  is either simulated (CARLA, DaRUS) or staged (fall/near-fall maneuvers performed by a
  stuntman/professional riders). This is a real, unresolved sim/staged-to-real gap.
- The physical mounting orientation of the MPU6050 relative to the motorcycle isn't calibrated
  or auto-detected — `ax/ay/az` are used directly rather than rotated into a gravity-aligned or
  motorcycle-aligned frame. `accel_mag`/`gyro_mag` (used as engineered features) are
  orientation-invariant, which partially compensates, but the raw 6-channel sequence input to
  the encoder is not.

## 10. Reconstruction, baseline, variance, and unseen-crash experiments

Full results and interpretation are in `performance.md` §8-12. Additional design notes follow.

### 10.1 Peak-over-window reconstruction error (`src/evaluate.py: peak_reconstruction_error`)

The model's built-in `recon_error` output (`ReconstructionError` layer, §2) averages per-timestep
squared error over all 60 timesteps *and* is baked into the graph (used as a classifier-head
input, so it can't change without retraining). `peak_reconstruction_error` is a separate,
post-hoc NumPy function computed from the already-available `reconstruction` output: per-timestep
mean-over-channel squared error, then `max` over the 60 timesteps. Because it's post-hoc, it can
be computed for any already-trained model (including Model C, §10.2) without touching the graph
or retraining — deliberately kept out of the model architecture to avoid adding another moving
part to item 4's frozen/retrained pipeline.

### 10.2 Model C (`src/model.py: build_autoencoder_only_model`, `scripts/train_model_c.py`)

Structurally identical encoder/decoder to `build_model()`'s reconstruction branch (same layer
sizes, same `_windowed_mse` loss), but as a standalone `Model(seq_in, decoded)` — no aux input,
no classifier head, no `recon_error` output, single-output `compile()`. Trained with plain
`model.fit(X, X)` on normal-only windows (no sample_weight machinery needed, since there's no
second head competing for gradient). This isolation is the whole point of the experiment: any
difference between Model C's reconstruction quality and the hybrid model's reconstruction branch
comes purely from the classifier head's gradient competing for the shared encoder's capacity in
the hybrid model.

### 10.3 Multi-seed training (`config.SEEDS`, `scripts/train.py: train_one`, `scripts/train_multi_seed.py`)

`scripts/train.py` was refactored so all of the actual training logic lives in
`train_one(seed, sessions=None, split_of=None)`, called once by `main()` (seed=`config.RANDOM_SEED`,
saved as the deployed model) and in a loop by `train_multi_seed.py`. The critical invariant: `seed`
only reaches `_seed_everything()` (Python/NumPy/TF RNGs) — the data split is computed from
`config.RANDOM_SEED` regardless of `seed`, and `train_multi_seed.py` explicitly computes
`sessions`/`split_of` once and passes them into every call, so there's no way for the multi-seed
loop to accidentally vary the split. Each seed gets its own validation-calibrated threshold
(same procedure as `main()`), then all 5 are evaluated on the one fixed test split for the mean/std
table.

### 10.4 Unseen-crash experiment (`scripts/unseen_crash_experiment.py`)

Deliberately does not touch `assign_splits()`'s normal behavior. Filters `sessions` by
`source != "darus"` before calling `assign_splits()` (so DaRUS never enters that function at all,
rather than being included then discarded — avoids perturbing the stratified proportions for the
non-DaRUS sources), trains via the same `train_one()` used everywhere else, then builds a second
`Dataset` from the DaRUS sessions using a synthetic `split_of` that maps every DaRUS session to
`"unseen"` (so `manifest.build_dataset` windows all of it, no train/val/test subdivision — every
DaRUS window is test data here). The resulting model is saved under `results/`, not `models/`,
specifically so nothing in `deploy/` or the main evaluation scripts could ever accidentally load
it as the real model.

## 11. Supervised baseline and deployment synchronization

Full results and interpretation are in `performance.md` §8-14. Additional design notes follow.

### 11.1 Model B (`src/model.py: build_classifier_only_model`, `scripts/train_model_b.py`)

Structurally the encoder/bottleneck/pooling half of `build_model()`'s classification path
(identical layer sizes), but as its own `Model({"seq", "aux"}, {"crash_prob"})` — no decoder
layers exist at all, not merely an ignored branch, so there's no reconstruction loss competing
for the shared encoder's gradient during training. The only structural difference from Model A's
classifier head is the absence of the `recon_error` input feature (nothing to compute it from).
Compiling a single-output dict model like this makes Keras name its metrics unprefixed (`"auc"`,
not `"crash_prob_auc"` the way Model A's multi-output dict does) — `EarlyStopping` here monitors
`"val_auc"`, not `"val_crash_prob_auc"`.

### 11.2 Real exposure-time and cooldown correction (`src/evaluate.py`)

`normal_session_hours()` sums `len(session.df) / TARGET_RATE_HZ` over each split's
session-level-normal sessions — the session's actual resampled sample count, independent of how
many overlapping windows the sliding-window loop later carves out of it. This replaced
`n_normal_windows * window_seconds`, which implicitly assumed windows don't overlap; with a
60-sample window and 15-sample stride (75% overlap), that assumption overstated real exposure by
about 4x. `simulate_deployed_alerts()` also now derives its cooldown in *windows* from a real
`cooldown_seconds` (default 60.0, matching `deploy/config.yaml`) and `stride_seconds`, rather than
a fixed `cooldown_windows=4` placeholder that corresponded to only ~1.2 real seconds — nowhere
close to the actual deployed 60-second cooldown. The window-level diagnostic fields in
`summarize_predictions()`/`full_classification_metrics()` were renamed
`window_level_trigger_rate_per_hour` specifically so the field name itself signals "not a real
alert rate" — only `simulate_deployed_alerts()`'s event-level `false_alerts_per_hour` should be
cited as a real rate.

### 11.3 Denoising Model C (`src/model.py: build_autoencoder_only_model(denoising_noise_std=...)`)

`layers.GaussianNoise(stddev)` inserted immediately after the input layer, before the first
Conv1D. Keras's `GaussianNoise` only adds noise when the layer's `training` flag is `True` (i.e.
during `model.fit()`), and is a no-op during `model.predict()`/`model.evaluate()` — so nothing
downstream (thresholding, evaluation, `deploy/`-side inference) needs to know or care that the
model was trained this way. The reconstruction target is always the clean window; only the
encoder's input is corrupted during training. `scripts/train_model_c.py` trains both
`denoising_noise_std=0.0` (plain) and `denoising_noise_std=0.25` (denoising) and reports both,
rather than assuming the denoising variant wins.

### 11.4 Deployment threshold sync (`deploy/crash_monitor.py: load_model_thresholds`)

`deploy/config.yaml` previously hardcoded numeric copies of `classifier_prob`/`recon_error` that
were only ever correct for whichever model was current at the time someone last hand-copied them
in — a silent drift risk every time `scripts/train.py` is re-run. `load_model_thresholds(cfg)`
reads `models/thresholds.json` directly at startup (path configurable via `cfg["thresholds_path"]`,
defaulting to `models/thresholds.json`) and returns `(classifier_prob, recon_error)`; `main()`
logs the loaded values so a deployment log always states which thresholds it's actually running
with. `consecutive_windows`/`cooldown_seconds` remain in `config.yaml` since they're deployment
policy, not something `scripts/train.py` calibrates.

## 12. Label scarcity, edge benchmarking, and extended false-alert evaluation

Full results and interpretation are in `performance.md` §14-16.

### 12.1 Session-level label-scarcity, 5 seeds (`scripts/label_scarcity_session_level_experiment.py`)

Refines Round 3's window-level version two ways: subsamples whole crash-like **sessions** from
the train split (not individual windows), and repeats over `config.SEEDS` instead of one seed.
Implemented via `build_reduced_split()`, which remaps a dropped session's `split_of` entry from
`"train"` to a throwaway name (`"excluded_by_label_scarcity"`) and lets the existing
`manifest.build_dataset()` do the actual filtering — no hand-rolled dataset concatenation, unlike
Round 3's approach, which built the reduced dataset directly from window-index masks (necessary
there since it operated below the session level). Within one seed, a single permutation of the
train-split crash sessions is generated once, and each fraction takes a prefix of it, so the
100%→50%→25%→10% points are strict nested subsets within a seed (though independent across seeds).

### 12.2 Edge-device benchmark (`deploy/benchmark_device.py`)

Deliberately standalone, matching `deploy/crash_monitor.py`'s existing convention of not
importing the training-side `src/` package — only `tflite_runtime`/`tensorflow.lite`, `numpy`,
`psutil`, and `pyyaml`. Benchmarks against synthetic random windows (right shape/dtype, not real
sensor data) since this measures compute/resource cost, not detection accuracy, and doing it this
way means the script also runs standalone with no MPU6050 wired up yet. The concurrent-load proxy
(`ConcurrentLoad`, busy-loop worker processes) is explicitly documented as a proxy for "another
always-on workload" (e.g. drowsiness detection), not that module's actual code, which this repo
doesn't have. Power draw is read from sysfs (`/sys/class/power_supply/*/power_now` or
`voltage_now × current_now`) and reports `None` rather than a guess when no fuel-gauge hardware is
present — the common case on a bare Pi 4 with no UPS/monitoring HAT.

### 12.3 Extended false-alarm evaluation (`scripts/extended_false_alarm_evaluation.py`)

A standalone loader (reuses `src/resampling.py: resample_two_streams`, builds
`src.io_loaders.Session` objects directly) for the new STRIDE dataset sessions, deliberately kept
out of `src/io_loaders.py: load_all_sessions()` so this evaluation-only data can never be pulled
into the five canonical training-source directories under `data/`. Distance is computed by trapezoidal
integration of the `Location.csv` `speed` column over `seconds_elapsed` (`np.trapz`), not
haversine distance between consecutive GPS fixes — deliberately, since integrating a reported
speed is more robust to GPS position jitter over short, low-speed road-anomaly recordings (a few
noisy lat/lon fixes a few meters apart can produce a wildly wrong haversine distance at low
speed, whereas the device's own speed estimate is already smoothed). The already-deployed
model/normalizer/thresholds are loaded as-is (`tf.keras.models.load_model` on
`helmx_crash_model.keras`, same custom-layer registration side effect via
`from src import model as model_lib` as every other evaluation script) — no retraining occurs
anywhere in this script.

**Important methodological note:** before using any of
this new dataset, its 23 session folders were checked byte-for-byte against `data/road/`'s
existing 9 folders (row counts + first-row values, not just folder names) — 6 "Driving Behaviour"
sessions and 3 "Road Anomalies" sessions turned out to be identical to sessions already in
`data/road/`. This is why `scripts/extended_false_alarm_evaluation.py` only loads
`Road Anomalies/{3-9}. Bump` and `{11-17}. Pothole` — the other 9 folders of the original 23 were
deliberately never copied into `data/extended_normal_road_raw/` at all, to make it structurally
impossible for a future run to accidentally double-count them.

## 13. Round 5: attempts to close the Model A/Model B gap (all inconclusive/negative)

Full results and interpretation are in `performance.md` §18.

### 13.1 Shared, explicit layer names (`src/model.py`)

`build_model()`, `build_classifier_only_model()`, and `build_autoencoder_only_model()` all now
name their encoder/decoder layers identically (`enc_conv1`, `enc_bn1`, `enc_conv2`, `enc_bn2`,
`bottleneck`, `dec_conv1`, `dec_conv2`, `reconstruction`) instead of relying on Keras's
auto-generated names, which are assigned in creation order *within a process* — building two
models in sequence in the same Python session shifts the second model's auto-names, so they'd
silently stop lining up between, say, a Model C instance and a `build_model()` instance built
afterward. `transfer_shared_weights(source_model, target_model)` copies weights layer-by-layer by
these names, skipping (not erroring on) any name missing from either model, so the same call works
whether the source is an autoencoder (has decoder layers) or the target is `build_classifier_only_model`
(has no decoder layers to receive them).

### 13.2 Two-stage training (`scripts/train.py`, `scripts/train_model_c.py: pretrain_autoencoder`)

`train_hybrid_from_datasets()` gained a `model=` parameter: pass an already-built (and, for the A1
variant, already weight-transferred) model instead of letting it call `build_model()` itself. This
is a minimal, backward-compatible change — every existing caller that doesn't pass `model=`
behaves identically to before. `train_hybrid_two_stage_warmup()` is a separate function (not a
`train_hybrid_from_datasets()` mode) because its training loop genuinely differs: two `model.fit()`
calls with a `trainable` flag flip and a `model.compile()` (new optimizer/learning rate) in
between, not one `fit()` call with different arguments. `calibrate_thresholds()` was factored out
of `train_hybrid_from_datasets()` specifically so this second function didn't have to duplicate
that logic.

### 13.3 `ReconstructionFeatures` layer (`src/model.py`)

Computed inside the graph from `(seq, decoded)`, not as a post-hoc NumPy feature the way
`evaluate.py: peak_reconstruction_error` is — the whole point of this ablation was testing whether
a *trainable, end-to-end* richer signal helps, as opposed to the post-hoc sklearn stacking already
tried (Round 2) and found to overfit. `feature_set="mean_peak"` and `"rich"` share the same
`per_timestep_mean` computation; `"mean_peak"` just returns early with 2 of what would otherwise be
intermediate values for `"rich"`'s fuller 12-feature vector, rather than being two independent code
paths. `window_len = seq.shape[1]` is read as a **static** Python int (the window dimension is
fixed at graph-build time, `config.WINDOW_SAMPLES`), not `tf.shape` -- deliberately, both for
simplicity and because this codebase has already hit real TFLite-conversion issues with certain
dynamic-shape/op patterns (`src/export.py`'s SavedModel-first workaround, documented in §7); a
static slice avoids reintroducing that risk, though this ablation's models were never exported to
TFLite (the result didn't warrant it).

## 14. Round 6: a stricter, advisor-defined staged experiment (also inconclusive/negative)

Full results and interpretation are in `performance.md` §20. The three-experiment staged plan
used an explicit, preregistered success bar (PR-AUC must move like 0.48→0.56/0.60, not 0.48→0.49, consistently
across seeds) -- the point being to prevent post-hoc goalpost-moving on whatever the numbers turn
out to be.

### 14.1 A shared metric helper, not three independent implementations

`src/evaluate.py: recall_at_specificity()` and `scripts/experiment_common.py: evaluate_variant()`
exist specifically because Round 5's version of this same B/A0/A1/A2 comparison pulled B/A0's
numbers from one script (`label_scarcity_session_level_experiment.py`) and A1/A2's from another
(`two_stage_pretraining_experiment.py`) -- neither computed PR-AUC or recall-at-specificity for
the other's variants, so the "comparison" wasn't actually scoring all four variants the same way.
`evaluate_variant()` is called identically by all three of this round's new scripts
(`exp1_pretraining_comparison.py`, `exp2_reconstruction_features_pretrained.py`,
`exp3_loss_weighting.py`), so no two rows in any of this round's tables can have silently drifted
metric definitions.

### 14.2 A Keras 3 constraint discovered via smoke test: no recompiling mid-`fit()`

Experiment 3's staged loss-weighting schedule (λrec tapering 1.0→0.5→0.2 over training) was first
implemented as a `tf.keras.callbacks.Callback` that called `model.compile()` from
`on_epoch_begin()` whenever the schedule crossed a boundary -- the natural way to express "change
this hyperparameter partway through training" as a callback. A 2-epoch smoke test of every new
code path (run deliberately *before* committing to the full 5-seed/~50-run job, given how much
compute this round would use) caught that this crashes on the very next training step
(`'NoneType' object is not callable` -- Keras 3's cached `train_function` doesn't survive a
recompile issued mid-`fit()`). Fixed by restructuring the staged schedule into
`scripts/train.py: _staged_finetune()`, which runs **one separate `model.fit()` call per schedule
stage**, recompiling only *between* calls -- exactly the pattern `train_hybrid_two_stage_warmup()`
already used for its own warmup→fine-tune transition, just applied at two boundaries instead of
one. `train_hybrid_two_stage_warmup()` gained `recon_weight` (static override) and
`loss_weight_schedule` (routes to `_staged_finetune`) parameters; both default to the original
hardcoded 2:1 behavior, so every existing caller (Round 5's scripts) is unaffected.

### 14.3 The gradient-conflict diagnostic

`scripts/exp3_loss_weighting.py: _gradient_conflict_diagnostic()` runs two separate
`tf.GradientTape` passes on one training batch -- one for the classification loss, one for the
reconstruction loss -- and takes the cosine similarity of the resulting gradients at the shared
`bottleneck` layer's trainable variables. This operationalizes the advisor's own suggested
diagnostic ("measure gradient cosine similarity... if it is frequently negative, you have direct
evidence of objective conflict") as a cheap one-batch check rather than a full GradNorm/PCGrad
implementation; the heavier gradient-balancing methods were outside this experiment's scope.
Result: **+0.018 mean cosine
similarity** -- not negative, meaning no detected conflict at this checkpoint, which is itself
evidence against investing in PCGrad/GradNorm for this architecture.

### 14.4 The result, and why it's a stronger negative than Round 5's

Experiment 1's fresh 5-seed run of B/A0/A1/A2 -- now scored on PR-AUC for every variant, which
Round 5 never computed for B or A0 -- found **B has the highest PR-AUC of all four** (0.581 vs.
0.427-0.527 for every hybrid configuration tried across all three experiments). This sharpens
Round 5's finding rather than repeating it: previously the comparison leaned on ROC-AUC and F1
alone, where the gap between B and the hybrid variants looked small; PR-AUC (the metric the
advisor specifically asked for because of class imbalance) shows a clearer, wider gap in B's
favor. The experiment therefore did not meet its preregistered success criteria.

## 15. Round 7: a genuinely external test set, and a duplicate-data catch made before evaluating anything

Full results and interpretation are in `performance.md` §21.

### 15.1 Verifying dataset independence *before* spending any effort on it

The advisor named two external candidate datasets by DOI. Before downloading either, both were
checked via Crossref/Zenodo/PMC metadata (not assumed from memory or the advisor's description
alone). The first (Zenodo `jsanta-upct/scooter-riding`, resolved via the article DOI's Crossref
`is-supplemented-by` relation — a more reliable path than guessing a Zenodo search query, which in
practice returned mostly irrelevant hits for free-text queries against Zenodo's search API) checked
out as genuinely new. The second, motorcycle-specific candidate did not: its documented sampling
rate (1000 Hz), column names/units (`Ax/Ay/Az(m/s²)`, `Rx/Ry/Rz(°/s)`), and scenario names (curve/
leaning/roundabout/slippery-road falls, near-fall extreme maneuvers) matched this project's own
`data/fall/`/`data/near-fall/` folders exactly — confirmed by direct file inspection (`head`/`wc
-l` on both), not merely a name-based guess. This is the same discipline Round 4 applied to STRIDE,
now applied *before* any download rather than after — cheaper, and avoids ever needing to explain
away a spuriously good "external" result later.

### 15.2 A second Android sensor-CSV format, requiring a genuinely new (not reused) loader

`scripts/external_test_scooter_dataset.py: load_external_scooter_sessions()` cannot reuse
`src/io_loaders.py: load_road_folder()` even though both read `Accelerometer.csv`/`Gyroscope.csv`
pairs, because the column layout differs: `load_road_folder` expects `seconds_elapsed,x,y,z`
(one Android sensor-logging app's convention, already used by `data/road/` and Round 4's STRIDE
data), while this dataset uses `Timestamp,Milliseconds,X,Y,Z` from a different logging app. The
`Milliseconds` column was verified (by inspecting rows spanning a `Timestamp` second-boundary) to
be monotonically increasing elapsed milliseconds across the *entire* file, not a per-second
counter that resets — so `Milliseconds / 1000.0` is used directly as the time axis into the
existing `resample_two_streams()`, with no new resampling logic needed, just a new column-mapping
front end.

### 15.3 Reusing Round 6's `evaluate_variant` for a fourth, different kind of experiment

This is the first script to score a **fixed binary decision rule** (the deployed
`crash_prob > t1 OR recon_error > t2` OR-fusion) with `experiment_common.evaluate_variant()`,
which was designed for continuous scores. The trick: `_binary_rule_metrics()` passes the boolean
decision itself as if it were a continuous score with a fixed `threshold=0.5`, which reproduces
the identical confusion matrix `evaluate.full_classification_metrics` would compute from the
decision directly. The resulting ROC-AUC/PR-AUC values from this row are real but degenerate
(computed from a single operating point, i.e. a two-segment curve) — documented explicitly in
both the saved JSON and `performance.md`, so
a future reader doesn't mistake it for a continuous-score AUC of comparable resolution to the
other rows in the same table.

### 15.4 What the result adds to the project's understanding

Two independent out-of-distribution tests now exist (§12's unseen-crash/DaRUS experiment and this
one), and both point the same direction: the reconstruction branch generalizes better than either
classifier under real distribution shift. This round adds a new wrinkle neither previous
in-distribution experiment (Rounds 2-6) surfaced: Model A's classifier head clearly outperforms
Model B under this specific distribution shift (event-level recall 0.667 vs. 0.222), even though
every in-distribution comparison found them statistically indistinguishable-to-B-favored. Reported
as a real but not-yet-conclusive asymmetry (n=9 crash sessions, no seed variance possible for a
single external evaluation of the already-deployed model) rather than either oversold or omitted.

## 16. Round 8: a hierarchical decision policy (negative), and a third external dataset

Full results and interpretation are in `performance.md` §22.

### 16.1 Why the hierarchical policy is a structural superset of tuned-OR, not just a rename

`src/evaluate.py: apply_hierarchical_policy` partitions windows by classifier confidence into three
zones (confident-crash, confident-normal, ambiguous) and only lets reconstruction override the
classifier in the latter two, at two independently-calibrated thresholds. This matters because a
naive two-threshold "primary classifier, always-on fallback" is *set-theoretically identical* to a
plain OR rule (`A OR B` doesn't care about "primary" vs. "fallback" framing) — the only way to make
a genuinely different decision surface without blending scores (already tried and found to overfit
in Round 2's stacking ablation) is to make the fallback's *threshold* depend on classifier
confidence, which is exactly what the confident-normal-vs-ambiguous split does. Setting
`t_low == t_high` collapses the three zones to two and reduces the whole thing to exactly
`tune_hybrid_or_thresholds`'s rule — so `tune_hierarchical_thresholds`'s search space strictly
contains tuned-OR's, meaning it can never score *worse* than tuned-OR on the same validation
objective (confirmed: 0.686 vs. 0.587 validation F1) — the informative comparison is what happens
on data the search never saw, not on validation itself.

### 16.2 The overfitting diagnosis, and why it isn't a implementation bug

Test-split F1 dropped from tuned-OR's 0.343 to hierarchical's 0.208, and event-level recall from
1.0 to 0.8 — a real generalization failure, not a bug in the code. The calibrated `t_high` landed
at (numerically indistinguishable from) 1.0, meaning the "confident-crash" zone that gets accepted
directly by the classifier is nearly empty: most genuine crash windows instead get routed through
the ambiguous zone, decided by `t_recon_ambiguous` (calibrated to 1.001, just above the
reconstruction-error floor) rather than accepted outright. That configuration happens to score very
well on the *particular* ~4,700-window validation split (few normal windows land in that same
ambiguous band there), but the same threshold structure doesn't reproduce the pattern on the test
split or the external scooter set. This is the third time this exact failure mode has appeared in
this project at three different levels — Round 2's stacked meta-classifier (a learned combination),
Round 6's richer reconstruction-features (more input dimensions), and now this hand-designed
4-threshold rule (more calibration degrees of freedom) — all three add flexibility on top of the
same two underlying signals, and all three overfit the same modest (~4,700-window, low-positive-
count) validation split rather than generalizing.

### 16.3 A second dead-end search, surfaced rather than worked around

Looking for a third external two-wheeler dataset, the closest domain/kind match to the Round 7
scooter dataset — Lee, Koo & Kim (2024), e-scooter pre-impact falls, CC BY 4.0 per Crossref — could
not be traced to any actual public data repository (MDPI's article page blocks automated fetches
with a 403; no Crossref relation, GitHub, or Zenodo link surfaced after several search attempts).
Per this project's established practice (Round 4's Mendeley dead-end, handled the same way), this
was explicitly documented rather than substituted silently or pursued
indefinitely. The study proceeded with a confirmed-accessible but qualitatively different
alternative, SimRa.

### 16.4 A genuinely different file format, and an important measured (not assumed) caveat

`scripts/external_test_simra_dataset.py: _parse_ride_file` handles SimRa's two-section-per-file
layout (incident annotations, a `=====` separator, then the ride's own CSV) with a custom parser —
neither of the two Android sensor-CSV loaders already in this project (`load_road_folder`'s
`seconds_elapsed,x,y,z` format, or Round 7's `Timestamp,Milliseconds,X,Y,Z` format) applies, since
SimRa logs accelerometer *and* gyroscope in the *same* row/timestamp rather than two separate
files needing `resample_two_streams` — a single `resample_uniform` call suffices here. Before
trusting this data for anything, its native sampling rate was **measured directly** (median
inter-sample gap across a full ride file, not assumed from the README): ~4 Hz, confirmed
consistent across multiple files — far below this pipeline's 50 Hz target and every other source.
This is disclosed as prominently as the near-miss-vs-crash semantic gap, not treated as a minor
footnote, because it directly bears on how much weight the resulting numbers should carry.
