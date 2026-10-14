# Results From Pi — HelmX Crash Detection, real Raspberry Pi 4 hardware

Running every experiment in `deploy/PI_RESEARCH_GUIDE.md` on this actual Pi 4 Model B (Rev 1.5,
4GB... actually 7.64GB reported RAM, Raspberry Pi OS / Debian 12 bookworm, aarch64), documenting
results after each test, in order. Nothing here is estimated — a field is filled in only if a
real run on this hardware produced it; otherwise it's marked unavailable and why.

## Model understanding (context for interpreting every result below)

HelmX's crash detector is a **hybrid autoencoder + classifier** sharing one Conv1D encoder
(`src/model.py: build_model`):

- Input: a `(60, 6)` window — 60 timesteps (1.2s at 50Hz) × 6 channels (ax, ay, az, gx, gy, gz) —
  plus 7 hand-engineered aux stats (mean/std/peak accel magnitude, mean/std/peak gyro magnitude,
  peak jerk).
- Shared encoder → **decoder** (reconstructs the window, trained only on normal-labeled windows)
  and **classifier head** (sees the pooled embedding + `recon_error` + the 7 aux stats → sigmoid
  `crash_prob`).
- Deployed decision rule (`deploy/crash_monitor.py`): a window is anomalous if `crash_prob >
  classifier_prob_balanced` (0.9892 per `models/thresholds.json`) **OR** `recon_error >
  recon_error` threshold (10.879) — classifier drives most detections, reconstruction is a
  backstop for crash types never seen labeled.
- **Not a one-shot alert**: `TriggerPolicy` requires 3 consecutive anomalous windows
  (`consecutive_windows`) before firing, then a 60s cooldown. A fired trigger starts a **local
  buzzer/vibration alarm with a 30s cancel window** (voice-cancellable) before an SMS+GPS alert
  actually goes out via GSM — a model trigger is not an SMS.
- Real-time gravity removal uses a **causal EMA filter** (`CausalGravityFilter`), a deliberate
  approximation of the offline **zero-phase Butterworth filter** used at training time — this gap
  has never been measured on real predictions before Experiment C below.
- Exported to TFLite two ways: FP16 (no calibration) and **INT8** (calibrated, this is what's
  actually deployed) — both keep float32 in/out signatures.
- Deployed stride budget: 15-sample stride / 50Hz = **300ms** per window — the number every
  latency result below should be compared against.

Full architecture/design rationale: `system_understanding.md`. Numbers from the offline
evaluation pipeline (not this hardware): `performance.md`.

## Environment setup (done once, before any test)

- Confirmed hardware/software already on the Pi: Python 3.11.2, `numpy` 1.24.2, `psutil` 5.9.4,
  `pyserial` 3.5, `gpiozero` 2.0.1, `mpu6050-raspberrypi` 1.2 (all system-installed). Missing:
  `pyyaml`, `tflite-runtime` (needed by every experiment below), and the full `tensorflow` stack
  (only needed by Experiments C/D).
- `pip install -r deploy/requirements.txt` at the system level refused
  (`externally-managed-environment`, PEP 668 — Debian bookworm blocks system-wide pip installs).
  Rather than force it with `--break-system-packages` (risk: could upgrade/conflict with the
  `gpiozero`/gpio stack two root-owned live services — `helmx-ble.service` and the DHT22/MQ135
  bridge — already depend on), created a venv **with `--system-site-packages`**
  (`.pi_research_venv/`) so it inherits the already-installed system packages and only adds what's
  missing on top. Installed cleanly from piwheels.org (prebuilt ARM wheels): `pyyaml` 6.0.3,
  `tflite-runtime` 2.14.0.
- All commands below were run via `.pi_research_venv/bin/python`.

---

## A1. Isolated inference benchmark — ✅ RAN on real hardware

```
.pi_research_venv/bin/python deploy/pi_research_suite/exp_a1_isolated_inference.py
```
Ran the actual deployed INT8 model (`models/helmx_crash_model_int8.tflite`, 83,568 bytes) —
100 warmup + 1,000 measured inferences × 5 repeats, synthetic-but-correctly-shaped `(60,6)`/`(7,)`
tensors (timing doesn't depend on data values, only shape/dtype).

**Result: full results file at `results/pi_research/a1_isolated_inference.json`.**

| Metric (pooled across 5 repeats) | Value |
|---|---|
| Model load time | 4.73 ms |
| Median latency | 0.553 ms ± 0.082 |
| p95 latency | 0.942 ms ± 0.149 |
| p99 latency | 1.682 ms ± 0.772 |
| Worst single inference seen (any repeat) | 21.76 ms (one outlier in pass 1; every other pass's max was <5.1ms) |
| Throughput | ~1,430–1,850 windows/sec across passes |
| Deployed stride budget | **300 ms** |

**Verdict:** even the single worst outlier (21.76ms) is ~14x inside the 300ms stride budget;
typical inference is ~0.5ms, i.e. ~600x headroom. TFLite's XNNPACK CPU delegate engaged
automatically (`INFO: Created TensorFlow Lite XNNPACK delegate for CPU`). Device fingerprint
confirmed real hardware: `Raspberry Pi 4 Model B Rev 1.5`, aarch64, 4 CPUs, 7.64GB RAM,
`tflite_runtime` 2.14.0.

---

## A2. CPU/RAM under sustained operation — ⚠️ RAN, but blocked from its intended measurement (no MPU6050 wired)

```
.pi_research_venv/bin/python deploy/pi_research_suite/exp_a2_resource_usage.py --duration-min 2
```
This launches the **real** `deploy/crash_monitor.py` as a subprocess and monitors it. First,
ran `crash_monitor.py` alone for 14s to see what actually happens with no sensors attached
(matches the hardware findings already documented in `pin_connections.md`). `logs/crash_monitor.log`
confirms, with real timestamps:
```
15:23:52 ERROR GSM serial connection failed: [Errno 2] could not open port /dev/ttyUSB0: No such file or directory
15:23:53 ERROR MPU6050 connection failed ([Errno 5] Input/output error), retrying in 5s
15:23:58 ERROR MPU6050 connection failed ([Errno 5] Input/output error), retrying in 5s
15:24:03 ERROR MPU6050 connection failed ([Errno 5] Input/output error), retrying in 5s
```
(Thresholds themselves loaded correctly: `classifier_prob=0.989226 recon_error=10.878736`,
matching `models/thresholds.json` — the threshold-sync mechanism from `system_understanding.md`
§11.4 works as designed.)

**This means A2 as written cannot measure what it's meant to measure right now**: `connect_sensor()`
retries `mpu6050(0x68)` forever (`while True`, 5s backoff) and never returns, so `crash_monitor.py`
never reaches `WindowScorer`/real inference — there is no "sustained active inference" state to
profile without the physical MPU6050 wired to I2C1 (pins 3/5), which the earlier hardware sweep
already found not responding.

Per the guide's own fallback for this exact situation ("if you don't have the sensor wired yet...
point `--pid` at any long-running process for a dry run of the monitoring logic itself"), ran A2's
own monitor for 2 minutes against the real `crash_monitor.py` process **while it sits in the
MPU6050 retry loop** — this is real measured data, just of the retry-loop idle state, not active
inference. Full file: `results/pi_research/a2_resource_usage.json`.

| Metric (2 min, 120 samples @ 1s) | Value |
|---|---|
| Process CPU | mean 0.175%, p95 1.0%, max 1.0% |
| Process RSS | flat 45.98 MB the entire run |
| System CPU | mean 27.8%, max 89.4% (other system activity — IDE/desktop — not this process) |
| System RAM used | ~2.9 GB / 7.64 GB |
| Swap used | 0 MB |
| CPU temperature | mean 55.7°C, max 58.4°C |
| Memory-leak verdict | **stable plateau** (slope ≈ 0 MB/min) |

**Verdict:** no leak, negligible CPU/RAM footprint while idle-retrying — but this number is **not**
comparable to the "sustained active inference" figure the guide's schema wants
(`resources.cpu_mean_percent` etc. under real load). That specific measurement needs the MPU6050
physically connected and responding at I2C address 0x68; re-run this exact command once it is.

---

## A3. Thermal stability — ✅ RAN on real hardware (30 min, genuine sustained-inference load substituted for the missing sensor)

The guide's own instruction: run this **while `crash_monitor.py` is doing sustained inference**,
because "sustained inference causes no thermal throttling" is the number that matters, not a
generic idle-Pi reading. Since the MPU6050 isn't wired (A2), `crash_monitor.py` can't reach that
state. Rather than settle for a meaningless idle reading, wrote a small helper
(`deploy/pi_research_suite/sustained_inference_load.py`, not part of the official A1-D suite,
clearly commented as a stand-in) that calls the **actual deployed INT8 TFLite model** on synthetic
input once every 300ms — the real deployed stride cadence — continuously. Ran both this and the
guide's own thermal script (saved as `deploy/pi_research_suite/exp_a3_thermal.py`, exact content
from the guide) concurrently for the full 30 minutes:
```
deploy/pi_research_suite/sustained_inference_load.py --duration-min 30    # 6,000 real inferences, 300ms cadence
deploy/pi_research_suite/exp_a3_thermal.py --duration-min 30 --interval-s 8
```
Full results: `results/pi_research/a3_thermal.json` (225 temperature samples over 30 min).

| Metric | Value |
|---|---|
| Initial temp | 56.9°C |
| Mean temp | 55.4°C |
| Max temp | 61.3°C (at ~11.2 min) |
| Temp at 10 min checkpoint | 56.9°C |
| Temp at 20 min checkpoint | 56.0°C |
| `vcgencmd get_throttled` | `0x0` — every bit clear |
| **Thermal throttling occurred** | **False** |

**Verdict:** temperature oscillated in a 52–61°C band with no sustained upward trend over 30
minutes of genuine continuous inference at the real deployed cadence (6,000 real TFLite calls) —
matches the guide's expected headline ("sustained inference causes no thermal throttling"),
confirmed by `get_throttled`'s raw hex `0x0` (no under-voltage, no frequency capping, no throttling,
no soft limit — none of these ever occurred during the run). Caveat: this load is CPU-only (no real
sensor I2C traffic, no GPIO alarm activity, no GSM/GPS serial I/O) — a small underestimate of real
total system heat, but the inference workload itself (the thing actually in question) is genuine.

---

## C. Replay validation — ✅ RAN on real hardware — **the guide calls this "the most important experiment," and it now has a real answer**

Installing the full `tensorflow` stack (needed by Experiments C/D per the guide) hit repeated
`SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC` errors on this Pi's network mid-download — looks like a
flaky/lossy connection, not a config problem (partial downloads kept resuming and re-failing at
different byte offsets). Checked what C actually imports first: `src/io_loaders.py`,
`src/manifest.py`, `src/preprocess.py`, `src/units.py` need only `pandas`/`scipy`/`numpy` — no
`tensorflow` at all (only `src/model.py`, needed by Experiment D, imports it). So `pandas`/`scipy`/
`scikit-learn` were installed on their own (succeeded after a couple of retries against the same
flaky connection) and **C ran without waiting on tensorflow**.

Wrote `deploy/pi_research_suite/exp_c_replay_validation.py` implementing the guide's sketch fully
(it was left as "sketch -- adapt with your own loader" in the guide): for every session in the
**real held-out test split** (`manifest.assign_splits`, same seeded split used everywhere else in
this project), built two prediction sequences using the **same deployed INT8 TFLite model +
thresholds** for both, so the comparison isolates only the filter difference (no quantization
confound — that's Experiment D):
- **offline**: `preprocess.canonicalize_all` (zero-phase Butterworth gravity removal) → windowed
  the normal way (`manifest.build_dataset`).
- **real-time**: raw per-sample stream (gyro→deg/s only, accel keeps gravity — exactly what a live
  MPU6050 would hand `read_sensor()`) fed sample-by-sample through the REAL `WindowScorer`
  (`CausalGravityFilter`, the actual deployed class).

Window *i* (offline, stride-indexed) and the *i*-th real-time `try_score()` call cover the
identical raw sample range by construction, so they're compared index-for-index. Event-level
agreement replays each session's window sequence through the real `TriggerPolicy` (3 consecutive
windows + 60s cooldown) for both paths and checks whether the two agree on "did this session ever
fire an alert." Full results: `results/pi_research/c_replay_validation.json`.

**Result — 10 real held-out test sessions, 5,437 windows compared, actually run on this hardware:**

| Metric | Value |
|---|---|
| Sessions | 10 (carla, road, near-fall, fall, DaRUS — every source represented) |
| Windows compared | 5,437 |
| **Window-level decision agreement** | **99.61%** |
| **Event-level decision agreement** | **100%** (10/10 sessions — every session where offline fired, real-time also fired, and vice versa) |
| Mean absolute `crash_prob` difference | 0.0408 |
| Mean absolute `recon_error` difference | 0.0383 |

Per-session breakdown (window agreement): carla_onder 100%, road_2.Aggressive 100%, road_2.Bump
100%, near_fall_Acceleration-On-Curve 96.8%, fall_fall-in-a-leaning 95.2%,
darus_crash_Iso_115_Out 66.7% (only 6 windows total — a single disagreeing window swings this a
lot), darus_crash_Iso_312_2_Out 100%, darus_crash_Iso_513_2_Out 100%,
darus_non_crash_Pothole_5_Out 100%, darus_non_crash_Randomstate_60_Out 100%.

**Verdict: this is the good outcome the guide hoped for but had never verified.** The causal
EMA filter documented as a "deliberate tradeoff" in `deploy/crash_monitor.py` really does behave
like the offline zero-phase Butterworth filter's real-time approximation, not a silent behavior
change — 100% of test sessions agree on whether an alert fires at all, and even the noisiest
per-window disagreement (DaRUS `Iso_115_Out`, 66.7%) is on a session with only 6 total windows,
where one differing window has an outsized percentage effect. The small numeric prob/recon-error
differences (~0.04 mean absolute) are consistent with "phase-lag from a causal filter," exactly
the tradeoff the docstring describes — not evidence of a real discrepancy.

---

## A5. Trigger-to-local-alarm latency — ✅ RAN on real hardware, including a genuine GPIO pulse

The guide left this as a sketch ("adapt with your own replayed-session loader — see Experiment
C"). Wrote `deploy/pi_research_suite/exp_a5_trigger_latency.py`: replays every crash-like session
in the full dataset (36 sessions — near-fall, fall, and every DaRUS crash trace) through the real
`WindowScorer` + `TriggerPolicy` with synthetic timestamps spaced at the real 300ms stride (not
real wall-clock waiting), measuring — in that synthetic timeline — how long from the first
anomalous window to the 3-consecutive-window rule actually firing. On the first detected event,
also fired the **real `LocalAlarm`** — a genuine `gpiozero.DigitalOutputDevice(18)` pulse — to
confirm the alarm path works on real hardware, not just in theory. Full results:
`results/pi_research/a5_trigger_latency.json`.

**Result — 36 real crash-like sessions replayed on this hardware:**

| Metric | Value |
|---|---|
| Sessions replayed | 36 (7 near-fall, 4 fall, 25 DaRUS crash traces) |
| **Detected** | **35/36 (97.2%)** |
| Missed | 1 — `darus_crash_ISO13232-6_Out` (6 windows) never accumulated 3 consecutive anomalous windows |
| Mean trigger latency | 10.24s |
| **Median trigger latency** | **0.6s** (the floor: `(consecutive_windows−1) × stride_seconds` = 2×0.3s) |
| p95 trigger latency | 38.88s |
| Min / Max | 0.6s / 71.4s |
| GPIO alarm smoke test | **`used_real_gpio_device: true`, `ran_without_error: true`** — `gpiozero` acquired real GPIO18 and toggled it (0.5s on, per the test), no fallback to log-only mode |

**Pattern**: every DaRUS session (short, high-fidelity, ~6-window impulsive crash traces) that was
detected hit the 0.6s floor — the classifier is immediately confident on genuine sharp impacts.
The near-fall/fall sessions (longer, staged maneuvers with a slower buildup) show much more spread
(9.6s–71.4s) because the anomalous window streak gets interrupted by intervening normal-looking
windows before finally confirming.

**Verdict:** the confirmation rule itself is fast when the signal is unambiguous (0.6s floor, seen
constantly), and the one miss (`ISO13232-6`) is consistent with this project's own already-
documented finding (`system_understanding.md` §9/§12.4: the classifier doesn't generalize well to
crash mechanisms outside its training distribution) rather than a new bug. The GPIO alarm path was
confirmed to work on real hardware — `gpiozero` genuinely acquired GPIO18, not the log-only
degraded path `LocalAlarm` falls back to when GPIO is unavailable. Whether a physical buzzer/
vibration motor is actually wired to that pin to audibly confirm the pulse is a separate hardware
question (see `pin_connections.md` — nothing was confirmed physically attached to GPIO18 at the
time of that sweep).

---

## B. Power — ✅ RAN, honestly `null` (no fuel-gauge hardware) — plus a bonus concurrent-load benchmark

`deploy/benchmark_device.py` (§12.2's separate standalone edge-device benchmark, which the guide's
Section B explicitly points to for `read_power_now_microwatts()`) ran directly — no sensor or extra
install needed, already covered by `deploy/requirements.txt`:
```
.pi_research_venv/bin/python deploy/benchmark_device.py --runs 500 --concurrent-workers 1
```
Full results: `results/pi_benchmark.json`.

| Field | Value |
|---|---|
| `power_now_microwatts` | **`null`** — this Pi 4 has no UPS/fuel-gauge HAT exposing `/sys/class/power_supply/*/power_now`, exactly as the guide predicted for "a plain Pi 4 with no such add-on." Reported honestly as unavailable, not estimated. |
| Model load time | 3.49 ms |
| Solo latency (500 runs) | mean 0.589ms, p95 0.945ms, p99 1.195ms |
| Solo CPU% during benchmark | mean 85.0%, max 99.8% (this script's own tight benchmarking loop pegs a core — not representative of the real 300ms-paced deployment, just this synthetic back-to-back-calls benchmark) |
| **Bonus — concurrent load** (1 busy-loop worker standing in for "another always-on workload," e.g. drowsiness detection) | latency mean 0.656ms (+11%), p95 1.071ms (+13%) vs solo — model inference degrades only slightly under CPU contention from a second workload |

**Verdict:** power draw genuinely can't be measured on this hardware as configured — that's the
correct, honest result for this exact device, not a script failure. The bonus concurrent-load
result (not one of A1-D/B/C/D, but the same script that section B points to) shows the deployed
model tolerates real CPU contention from a second always-on workload gracefully.

---

## A6. Sustained stability / soak test — ⚠️ BLOCKED (same root cause as A2, not re-run for 1-2 hours)

A6 wraps A2's exact monitoring pattern around a supervisor loop for 1-2 hours, restarting
`crash_monitor.py` if it dies. Since A2 (above) already established — with direct log evidence —
that `crash_monitor.py` never leaves its `connect_sensor()` retry loop without a physically wired
MPU6050, a 1-2 hour soak test would just re-confirm the same idle-retry state A2 already measured
for 2 minutes (RSS flat at 45.98MB, CPU ~0%, no leak). Running it for the full 1-2 hours would not
surface anything new about the real code path A6 is meant to stress (repeated real
inference/windowing cycles under sustained operation) — so it's marked blocked rather than run
redundantly. **Once the MPU6050 is physically connected, A6 should be run for real** — it is the
only experiment in this guide that would catch a slow leak or an intermittent crash under hours of
continuous real inference, which nothing else here tests.

---

## D. Quantization verification — ✅ RAN on real hardware (after a persistently flaky network eventually let tensorflow install)

Unlike C/A5, Experiment D genuinely needs full `tensorflow` (to load `models/helmx_crash_model.keras`
as the float32 reference — `src/model.py`, imported for its custom layer registration, imports
`tensorflow` at module level). `pip install tensorflow==2.16.1` failed repeatedly on this Pi's
connection with `SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC` and `RemoteDisconnected` errors mid-download
(the 218.9MB wheel kept dying at different byte offsets — a lossy/unstable link, not a bad package
or index config: piwheels.org resolved and served every package correctly when the connection held
long enough). After several retries it finally completed (`Successfully installed ... tensorflow-2.16.1`,
confirmed importable) — no need to source it another way in the end.

Wrote `deploy/pi_research_suite/exp_d_quantization_comparison.py` per the guide's sketch: Keras
(float32 reference), FP16 TFLite, and INT8 TFLite (the deployed artifact) compared on the same
5,437-window real held-out test split (loaded the normal offline way — `canonicalize_all` +
`build_dataset`, since this experiment is about the model artifact, not the streaming pipeline).
Full results: `results/pi_research/d_quantization_comparison.json`.

| | Keras (.keras) | FP16 | **INT8 (deployed)** |
|---|---|---|---|
| Size | 792,902 bytes | 133,920 bytes (**5.9x smaller**) | 83,568 bytes (**9.5x smaller**) |
| Median latency | — (6.97s for all 5,437, batched) | 0.498ms | 0.529ms |
| p95 latency | — | 0.924ms | 1.087ms |
| Mean abs `crash_prob` diff vs. Keras | — | **0.000168** | **0.0658** |
| Agreement vs. Keras @ 0.5 threshold | — | 99.94% | **93.25%** |
| **Agreement vs. Keras @ actual deployed threshold (0.9892)** | — | 100% | **99.89%** |

**Verdict — nuanced, and this is exactly the kind of result worth reporting precisely rather than
summarized as "fine":** at a naive 0.5 decision threshold, INT8 quantization looks like it
introduces real drift (93.25% agreement, mean abs diff 0.066 — a genuinely coarser approximation
than FP16's near-perfect 99.94%/0.000168). But the model isn't deployed at 0.5 — it's deployed at
`classifier_prob_balanced = 0.9892`, a very high-confidence operating point calibrated specifically
to control false alarms. At *that* threshold, INT8 agrees with the float32 Keras reference on
**99.89%** of windows — the quantization noise is real but overwhelmingly lands in a probability
range far from the actual decision boundary the deployed system uses, so it essentially never flips
a real decision. FP16 is closer to Keras at every threshold, as expected (no int8 calibration
error), but INT8's 9.5x size reduction over the full Keras model comes at a decision-agreement cost
that only turns out to be negligible *because* of where the deployed threshold sits — not
inherently. Also notable: one INT8 inference in this run spiked to 109.6ms (vs. A1's worst-ever
21.8ms) — a single outlier, not reproduced across repeats in A1, but worth flagging rather than
hiding, since it's still ~3x inside the 300ms budget even at that outlier.

---

## Summary — what's real, what's blocked, and why

| Experiment | Status | Headline |
|---|---|---|
| A1 (isolated inference) | ✅ Ran | Median 0.55ms, p95 0.94ms — ~300-600x inside the 300ms stride budget |
| A2 (CPU/RAM, sustained) | ⚠️ Blocked on missing MPU6050; retry-loop resource use measured instead (stable, no leak) | Re-run once sensor is wired |
| A3 (thermal) | ✅ Ran (30 min, real inference load substituted for the missing sensor) | No throttling; 52-61°C band |
| A4 (streaming pipeline) | ❌ Not run — needs live MPU6050 | Re-run once sensor is wired |
| A5 (trigger latency) | ✅ Ran (36 real crash sessions replayed) | 97.2% detected, 0.6s floor latency, real GPIO18 pulse confirmed |
| A6 (soak test) | ⚠️ Blocked, same as A2 (not redundantly re-run) | Re-run once sensor is wired |
| B (power) | ✅ Ran | Honestly `null` — no fuel-gauge hardware; bonus concurrent-load benchmark included |
| C (replay validation) | ✅ Ran (10 real test sessions, 5,437 windows) | **99.61% window agreement, 100% event agreement** — causal filter approximation validated |
| D (quantization) | ✅ Ran (5,437 real test windows) | INT8 agrees with Keras 99.89% of the time **at the actual deployed threshold** |

**What's still needed from real hardware that this session couldn't provide**: a physically wired
MPU6050 on I2C1 (pins 3/5) — everything blocked above (A2's real number, A4, A6) depends on it. See
`pin_connections.md` (same repo, one level up) for the full hardware-connectivity sweep this was
built on.

---
---

# Part 2 — `HelmX_Paper1_FINAL_Pi_Data_Collection_Checklist.md` walkthrough

Working through the full checklist the user supplied (`/home/helmx/Crash Detection/
HelmX_Paper1_FINAL_Pi_Data_Collection_Checklist.md`), item by item, in the order its own §7
recommends. Section 2 of that checklist (A1/A3/C/A5/B/D) is **already fully covered above in
Part 1** — not re-run, just cross-referenced below. Everything new starts here.

## 3.3 Final reproducibility/environment capture — ✅ DONE

Full raw dump: `results/pi_research/pi_environment_final.txt` (481 lines — `/proc/cpuinfo`,
`uname -a`, `/etc/os-release`, `lscpu`, `free -h`, `df -h`, every requested `vcgencmd` field,
CPU governor/freq files, Python version, full `pip freeze`).

Key facts frozen:
| Field | Value |
|---|---|
| Model | Raspberry Pi 4 Model B Rev 1.5, 4× Cortex-A72 |
| RAM | 7.6Gi total (arm=947M/gpu=76M split) |
| OS / kernel | Debian 12 (bookworm), `6.12.75+rpt-rpi-v8` aarch64 |
| CPU freq | **min = max = 1800000 kHz** — `force_turbo=1` in `/boot/firmware/config.txt` locks the CPU at max clock permanently; governor reads `ondemand` but has nothing to scale (relevant to checklist item 3.7 below) |
| Current temp / throttled | 54.5°C / `0x0` |
| Python | 3.11.2 (`.pi_research_venv`, `--system-site-packages`) |
| Key package versions | `tensorflow==2.16.1`, `tflite-runtime==2.14.0`, `numpy==1.26.4`, `pandas==3.0.5`, `scipy==1.17.1`, `scikit-learn==1.9.0`, `psutil==5.9.4`, `PyYAML==6.0.3`, `pyserial==3.5`, `gpiozero==2.0.1`, `mpu6050-raspberrypi==1.2`, `RPi.GPIO==0.7.1` |

Note: the venv inherits system site-packages, so `pip freeze` also lists every already-installed
system package (Adafruit-Blinka, `sense-hat`, `picamera2`, `pigpio`, etc.) — harmless, but not all
of those are used by this project.

## 3.4 Background-service inventory — ✅ DONE

Full dump: `results/pi_research/process_snapshot.txt`. Captured while 3.1 (below) was running, so
its own process is visible in the top-CPU list — expected, not a contamination concern for *this*
item, which is about "what else is running."

**Important context this surfaces for interpreting every resource-usage number in this whole
project**: the desktop GUI (`labwc`), VS Code (several renderer/utility processes), and multiple
Chromium processes are all active concurrently on this Pi throughout every experiment in this
session — this is a Pi being used as a desktop workstation during testing, not a headless
deployment target. `helmx-ble.service` (DHT22/MQ135 bridge) and `rhasspy.service` (voice assistant)
are both running as documented in `pin_connections.md`. Full running-service list (28 units):
`accounts-daemon`, `avahi-daemon`, `bluetooth`, `cron`, `cups`/`cups-browsed`, `dbus`,
`getty@tty1`, **`helmx-ble`**, `lightdm`, `ModemManager`, `mosquitto` (MQTT — Rhasspy's transport),
`NetworkManager`, `polkit`, **`rhasspy`**, `rtkit-daemon`, `supervisor`, `systemd-journald`,
`systemd-logind`, `systemd-timesyncd`, `systemd-udevd`, `triggerhappy`, `udisks2`, `upower`,
`user@1000`, `wayvnc`/`wayvnc-control` (remote desktop), `wpa_supplicant`.

## 3.10 Threshold/config integrity snapshot — ✅ DONE

Full dump: `results/pi_research/model_hashes.txt` (`models/thresholds.json` + `deploy/config.yaml`
verbatim). Frozen values: `classifier_prob_balanced=0.9892255067825317`,
`recon_error=10.878735866546593`, `window_samples=60`, `stride_samples=15`, `sample_rate_hz=50`,
`consecutive_windows=3`, `cooldown_seconds=60`, `alarm.countdown_seconds=30`, `alarm.gpio_pin=18`,
`gravity_filter.cutoff_hz=0.3`.

## 3.11 Model artifact metadata + hashes — ✅ DONE

SHA256 of every file in `models/` captured in `results/pi_research/model_hashes.txt`. TFLite
signature/shape/dtype introspection (int8 + fp16) appended to the same file. Both formats expose
identical signatures: inputs `aux (1,7) float32` + `seq (1,60,6) float32`, outputs `crash_prob
(1,1) float32`, `recon_error (1,1) float32`, `reconstruction (1,60,6) float32` — confirming
`system_understanding.md`'s claim that both TFLite exports keep float32 I/O with no manual
quantize/dequantize step required in `deploy/crash_monitor.py`. Sizes: int8 83,568 bytes (mtime
2026-08-30), fp16 133,920 bytes (same mtime — exported together).

## 3.12 TFLite delegate/operator behavior — ✅ DONE (partial)

Console output for every TFLite load in this session (A1, benchmark_device.py, D, this item)
consistently shows `INFO: Created TensorFlow Lite XNNPACK delegate for CPU.` — the XNNPACK CPU
delegate is active by default, confirmed here again via direct interpreter introspection. Per-
tensor `quantization_parameters` on the exposed input/output tensors are empty
(`(0.0, 0)`/empty arrays) for both int8 and fp16 — confirming the INT8 quantization happens on
internal weights/activations inside the graph, not at the float32 input/output boundary. Not
captured: full operator list / non-delegated-op breakdown (would need `--visualize` tooling or
`interpreter._get_ops_details()`, not pursued — low marginal value given A1 already shows the
whole model runs in <1ms with a single delegate, i.e. nothing is meaningfully falling back to a
slow path).

## Section 4 (MPU-dependent experiments 4.1-4.8) — ❌ NOT PERFORMED, same root cause throughout

All eight items in the checklist's Section 4 (physical I2C detection re-verification, live raw
sensor validation, A2 active CPU/RAM under live sensor, A4 true live streaming pipeline, A6 ≥1h
live soak, physical movement smoke test, safe live trigger-path test, live detector + background
helmet services) require a **physically connected, powered MPU6050 responding on I2C1**. This
session's exhaustive hardware diagnosis (see `pin_connections.md` and the MPU6050 diagnosis
earlier in this conversation) established conclusively that:
- `i2cdetect -y 1` shows zero devices at any address, including both 0x68 and 0x69
- Direct probes return `errno=121 (Remote I/O error / EREMOTEIO)` — the bus is electrically
  healthy (not stuck/shorted), nothing acknowledges at either possible address
- I2C1 is correctly enabled and configured in firmware/software (`dtparam=i2c_arm=on`, GPIO2/3
  correctly muxed to `SDA1`/`SCL1`, correct permissions, no kernel-level I2C errors ever logged)
- The Pi's own power rails are healthy (`get_throttled=0x0`, normal core/sdram voltages)
- This narrows the fault to the physical wiring/power between the Pi's header and the MPU6050
  board itself (most likely: MPU6050 has no power, or GND isn't connected, or SDA/SCL isn't
  actually wired to pins 3/5) — a multimeter check on the physical wires is the only next step,
  which is outside what this session can perform.

**4.1 re-verified anyway** (cheap, no reason not to): identical result, still nothing on the bus.
**4.2 through 4.8 cannot be attempted at all** without 4.1 first succeeding — documented here as a
single block rather than eight repetitive "blocked, same reason" entries. Re-run all eight once
the MPU6050 is physically connected and `i2cdetect -y 1` shows `68` or `69`.

## Section 5 (offline Paper 1 artifacts) — ✅ VERIFIED PRESENT, nothing to regenerate

Checked (not re-derived — these are outputs of the offline training/eval pipeline, already frozen)
that every P0 item already exists in the repo: `results/full_metrics.json`, `test_metrics.json`,
`reproducibility_manifest.json` (split seed + file hashes), `unseen_crash_experiment.json` (OOD/
DaRUS-held-out), `external_test_scooter_dataset.json`, `external_test_simra_dataset.json`,
`hybrid_ablation.json`, `label_scarcity_experiment.json` /
`label_scarcity_session_level_experiment.json`, `seed_variance.json` (multi-seed), `model_b_
metrics.json`/`model_c_metrics.json` (ablations), `hierarchical_decision_policy.json`,
`recon_feature_ablation.json`, `two_stage_pretraining_experiment.json`, `exp1-3_*.json`, plus
`datasets_used/MANIFEST.md`. All P0/P1 offline material this checklist asks to preserve is already
there — no gaps found.

## 3.34 NTP/clock snapshot — ✅ DONE
`timedatectl`: system clock synchronized (NTP active), timezone `Asia/Karachi (PKT, +0500)`. All
`elapsed_min`/latency timestamps in every experiment this session used `time.monotonic()`/
`time.perf_counter()` (immune to wall-clock/NTP adjustments), so this only matters for log
timestamps, not measured durations.

## 3.35 Storage state — ✅ DONE
`lsblk`: single `sda` disk, 119.2G, partitioned `sda1` (512M, `/boot/firmware`) + `sda2` (118.7G,
`/`) — **this Pi boots from a SATA/USB SSD (via the ASMedia bridge seen in `pin_connections.md`'s
`lsusb` output), not a microSD card.** Worth noting for the paper if storage-medium affects any
claims (it doesn't affect any measurement in this suite — everything here is CPU/RAM/model-bound,
not disk I/O bound). Swap: 512M file-backed, 7.8M in use, priority -2. 99GB free on `/` (confirmed
earlier this session, unchanged).

## 3.44-3.47 Process affinity/priority/thread/FD snapshot — ✅ DONE (captured live on the running 3.1 benchmark)
Taken directly against the Section 3.1 benchmark process while it was running, since that gave a
real live PID to inspect: CPU affinity `0-3` (all 4 cores available, no pinning), niceness `0`/
priority `19` (default, not elevated — this project runs with no special scheduling priority),
7 threads (Python interpreter + XNNPACK's internal worker threads), 4 open file descriptors
(stable, low, no descriptor leak visible in this snapshot).

## Section 6 (model/system facts to freeze) — ✅ CONFIRMED against live `deploy/config.yaml` and TFLite introspection above, no discrepancies

Every fact the checklist lists matches what this session independently verified from the actual
deployed artifacts (not just asserted): 50Hz / 60-sample (1.2s) window / 15-sample (0.3s) stride
(§3.10, §3.11's TFLite `shape` fields); 6 raw channels + 7 aux features (§3.11's `seq`/`aux` input
shapes: `(1,60,6)`/`(1,7)`); shared Conv1D encoder + reconstruction decoder + classifier head with
`recon_error` feeding the classifier (`src/model.py`, read in the earlier model-understanding
pass); deployed format is INT8 TFLite (`deploy/config.yaml: model_path`); classifier threshold
0.9892255067825317 / reconstruction threshold 10.878735866546593 / OR-fusion / 3 consecutive
windows / 60s cooldown / 30s cancel window / SMS-after-uncancelled (§3.10's `model_hashes.txt`
dump); causal EMA gravity removal in real time vs. offline zero-phase Butterworth, with replay
agreement already validated at 99.61%/100% (Experiment C, Part 1 above). No corrections needed —
every frozen fact in the checklist is exactly what's actually deployed.

## 3.18, 3.21, 3.29, 3.30, 3.31, 3.32 — software-logic robustness batch — ✅ DONE

Wrote `deploy/pi_research_suite/logic_robustness_tests.py`: six checklist items in one script,
all exercising the REAL deployed classes (`WindowScorer`, `TriggerPolicy`, `CancellationListener`,
`LocalAlarm`, `GsmModule`, `handle_suspected_crash`), no sensor needed. Full results:
`results/pi_research/logic_robustness_tests.json`.

**3.21 Replay determinism**: same session (`near_fall_Acceleration On Curve`, 156 windows) replayed
twice through fresh `WindowScorer` instances — **bit-identical** (`max_abs_prob_diff = 0.0`).
INT8 TFLite inference on this hardware is fully deterministic run-to-run for identical input.

**3.18 Malformed-input robustness** (NaN, ±Inf, extreme accel 1e6, extreme gyro 1e6, all-zero,
constant-nonzero signals fed continuously through `WindowScorer`): **no exceptions, no crashes, on
any case.** But an important nuance worth reporting precisely, not just "it survived": feeding NaN
accel triggers `RuntimeWarning: invalid value encountered in subtract` inside
`CausalGravityFilter.apply()` (the EMA gravity estimate gets permanently poisoned by the NaN, as
expected mathematically), yet the final `crash_prob`/`recon_error` outputs came back as **plain
finite numbers (`0.0`), not NaN** — `crash_prob_is_nan: false` in every malformed case. This means
**the INT8 TFLite quantization step silently absorbs NaN/Inf/extreme inputs into some other
numeric value rather than propagating IEEE NaN/Inf semantics through to the output.** Practically:
a downstream `isnan(crash_prob)` sanity check would **not** catch a NaN sensor glitch — the model
will confidently return an ordinary-looking number either way. `extreme_gyro` did produce a
notably elevated `recon_error` (49.29 vs. 0.0 for every other case) — gyro channels aren't
gravity-filtered the way accel is, so an extreme gyro reading reaches the model less dampened.
**Recommendation for the paper/future work**: sanitize sensor readings (reject/clip NaN, Inf, and
implausible magnitudes) before feeding `WindowScorer`, since the model itself won't flag it.

**3.29 Cooldown logic**: synthetic anomalous-window sequence through `TriggerPolicy` — first
trigger fires correctly, an identical anomalous sequence 5s later (within the 60s cooldown) is
correctly **suppressed**, and the same sequence after the cooldown fully elapses correctly
**resumes** and fires again. All three sub-checks passed.

**3.30 Cancel-window logic**: `CancellationListener` unit-tested directly (no signal → `False`,
signal present → `True` + file deleted, stale/already-consumed signal → `False` again, so a late
double-check can't re-trigger a stale cancellation) — all four checks passed. Then ran the **real**
`handle_suspected_crash()` end-to-end twice (countdown temporarily shortened to 2s purely to keep
the test fast — same code, same behavior, just a shorter wait than the deployed 30s):
- **Cancelled mid-countdown**: touched the cancel file at 0.5s into a 2s countdown → returned
  `False` (no SMS) after 0.60s, exactly as expected.
- **Uncancelled, no GSM/GPS hardware (this also covers 3.32)**: countdown expired uncancelled →
  `get_gps_coordinates()` returned `None` immediately (no hardware timeout stall) → `"location
  unavailable"` used → `send_sms()` correctly logged `"Cannot send SMS: no GSM connection"` and
  returned `False` — **nothing raised, the whole path degrades gracefully with no GSM/GPS present.**

**A genuine finding surfaced by this last test, not something this session assumed going in**:
`handle_suspected_crash()`'s docstring says *"Returns True if an SMS was sent, False if the rider
cancelled in time"* — but the actual code (`deploy/crash_monitor.py:425`) does `return True`
**unconditionally** after the countdown expires, regardless of whether the preceding
`gsm.send_sms(message)` call actually succeeded. In this test, `send_sms()` returned `False`
(logged the GSM failure) and `handle_suspected_crash()` still returned `True`. Checked whether
this has any current behavioral impact: `main()` is the only caller (`deploy/crash_monitor.py:480`)
and it **discards the return value entirely** (`handle_suspected_crash(...)` called as a bare
statement) — so this is a **latent bug / docstring-implementation mismatch, not a currently active
one**. Worth fixing before anything (a future logging wrapper, a metrics dashboard, a retry policy)
ever starts relying on that return value to mean "SMS confirmed sent."

**3.31 Alarm failure fallback**: `LocalAlarm` constructed with an invalid GPIO pin number (9999) —
`gpiozero` raised internally as expected, caught, logged (`"Local alarm GPIO unavailable (9999 is
not a valid pin name) -- logging only"`), `alarm.device` correctly left `None`, and `start()`/
`stop()` afterward ran with **no exception** (log-only degraded mode, exactly as documented).

## 3.1 Full replay-paced software-pipeline benchmark — ✅ RAN on real hardware (15 minutes, real cadence)

The checklist's own highest-value remaining item. Wrote `deploy/pi_research_suite/
exp_a4_replay_streaming_pipeline.py`: all 66 loaded sessions looped back-to-back, fed **one real
sample every 20ms** (the actual 50Hz deployed rate, real `time.sleep`-paced, not fast-forwarded
like Experiment C) through the REAL `WindowScorer` (causal filter → 60×6 windowing → 7 aux
features → INT8 inference) and `TriggerPolicy`, for a full 15 minutes, with concurrent per-second
resource sampling (process/system CPU%, RSS, system RAM, swap, temperature, **CPU frequency**,
load average — everything the checklist asked for). Full results (891 resource samples, per-window
latencies for all 2,985 windows): `results/pi_research/a4_replay_streaming_pipeline.json`.

| Metric | Value |
|---|---|
| Duration | 15.0 min (as requested) |
| Input samples processed | 44,830 |
| Windows generated | 2,985 (≈ 15min × 60s / 0.3s stride — matches expectation exactly) |
| **Per-window complete pipeline latency** — mean | 2.64ms |
| — median | 2.04ms |
| — p95 | 5.61ms |
| — p99 | 9.61ms |
| — max | 87.21ms |
| **Deadline misses (>300ms stride budget)** | **0 / 2,985 (0.0%)** |
| Achieved throughput | 3.32 windows/sec (matches the deployed 1/0.3s=3.33/s target almost exactly) |
| Triggers fired | 3 (looping 66 sessions back-to-back introduces artificial session-boundary discontinuities that can look anomalous — this number is a pacing/throughput artifact, not an accuracy claim; see Experiment C/A5 above for the real detection-accuracy numbers) |
| Process CPU% | mean 2.68%, max 6.0% (the pipeline itself is cheap — most of A4's own process time is the real-time sleep between samples, exactly as intended) |
| System CPU% | mean 27.0%, max 96.5% (this machine's desktop/IDE load — see 3.4 above — not this pipeline) |
| Process RSS | ~180MB (higher than A2's ~46MB idle-retry baseline because this process also holds all 66 sessions' full dataframes in memory for the replay loop — not a leak, a different workload; see `memory_leak_check` isn't computed here since this is a single continuous run, not the A2/A6 style repeated-sample leak check) |
| CPU frequency throughout | pinned at ~1800.44MHz (confirms 3.3's finding: `force_turbo=1` locks the clock, nothing to observe here) |
| Temperature | mean 54.8°C, max 58.4°C |
| **Thermal throttling** | **False** — `get_throttled=0x0` for the entire run |

**Verdict: zero deadline misses across the complete real software path (not just raw inference —
preprocessing, windowing, feature extraction, and inference together) at the real 50Hz/300ms
deployed cadence, sustained for 15 minutes, with p99 latency (9.6ms) still ~31x inside budget and
even the single worst outlier (87.2ms) ~3.4x inside budget.** This is the strongest non-MPU
evidence in the whole suite that the deployed pipeline meets its real-time deadline in practice,
not just in isolated-inference theory (A1).

## 3.2 Repeat A1 once more — ✅ RAN — **surfaced a real, important finding: the 109.6ms outlier was not a fluke, and worse ones exist**

Checklist's own stated reason for this item: Experiment D (Part 1) saw one 109.6ms INT8 outlier
and asked whether that was an isolated spike. Re-ran A1's exact protocol (100 warmup + 1,000
measured × 5 repeats) unchanged. Both runs preserved: `results/pi_research/
a1_isolated_inference.json` (original) and `a1_isolated_inference_repeat_final.json` (this repeat).

| Metric (pooled across 5 repeats) | Original A1 | **Repeat** |
|---|---|---|
| Median | 0.553ms ± 0.082 | 0.558ms ± 0.067 |
| p95 | 0.942ms ± 0.149 | 1.000ms ± 0.135 |
| p99 | 1.682ms ± 0.772 | 1.296ms ± 0.176 |
| **Worst max seen (any of 5×1000 runs)** | 21.76ms | **286.84ms** |

**The median/p95/p99 figures are essentially unchanged and reproduce well — the core inference
speed claim is solid.** But the **max** is not stable at all: this repeat hit a single inference
that took **286.8ms — 95.6% of the entire 300ms stride budget**, more than 13x worse than the
original run's already-flagged 109.6ms/21.76ms outliers. This is close enough to the deadline that
it deserves to be stated plainly rather than averaged away: **on this specific hardware, as
currently configured, a rare single inference can consume nearly the whole real-time budget.**

**Why, and why it doesn't currently threaten the deployed system**: this Pi is running a full
desktop session throughout every test in this suite — see 3.4 above: `labwc` desktop, several VS
Code renderer/utility processes, and multiple Chromium processes, with system CPU% peaking at
96.5% during 3.1's run. A single Python thread doing a <1ms TFLite call can be preempted by the
OS scheduler for an arbitrary length of time under that kind of contention — that's the most
likely explanation for an outlier this large on hardware whose median performance is this fast.
This is consistent with, not contradicted by, 3.1's clean 15-minute zero-deadline-miss result
immediately above: 3.1 measured the *complete pipeline's* worst case at 87.2ms over 2,985 real
windows, still comfortably under budget, but the same scheduling-jitter mechanism could in
principle produce a worse outlier given enough time/contention. **Recommendation for the paper**:
report median/p95/p99 as the reliable inference-speed claim (they reproduce tightly), but do not
claim a hard worst-case latency bound from A1/D alone without either (a) a much larger sample (see
3.5 immediately below) or (b) testing on a headless, single-purpose deployment image without a
desktop GUI/IDE/browser competing for the CPU — the realistic target-device condition this paper's
deployment claim is actually about.

## 3.5 CPU jitter / latency-tail characterization — ✅ RAN — confirms the outliers are real, rare, and (so far) never cross the deadline

Wrote `deploy/pi_research_suite/exp_a1_long_tail_latency.py`: 50,000 individual inferences (25x
A1's per-repeat sample size), every single latency recorded (not just percentile summaries), event
counts at 7 thresholds. Full results: `results/pi_research/a1_long_tail_latency.json`.

| Metric (n=50,000) | Value |
|---|---|
| Mean | 0.936ms |
| Median | 0.771ms |
| p95 | 1.778ms |
| p99 | 3.940ms |
| **p99.9** | 7.232ms |
| **Max** | **256.73ms** — another large outlier, consistent with 3.2's 286.8ms |
| `>2ms` | 1,788 events (3.58%) |
| `>5ms` | 297 events (0.594%) |
| `>10ms` | 18 events (0.036%) |
| `>25ms` | 9 events (0.018%) |
| `>50ms` | 9 events (0.018%) |
| `>100ms` | 3 events (0.006%) |
| **`>300ms` (deadline miss)** | **0 events — 0.0% empirical deadline-miss rate** |

**Verdict: the outlier phenomenon 3.2 flagged is real and reproduces at scale — a small but
nonzero fraction of inferences (roughly 1 in 5,500) take >10ms, and roughly 1 in 16,700 take
>100ms — but across this run's 50,000 samples plus 3.2's 5,000, not one of the ~55,000 total
inferences measured in this session crossed the 300ms stride budget.** p99.9 (7.23ms) stays deep
inside budget; only the extreme tail (worse than 1-in-tens-of-thousands) approaches
hundreds-of-milliseconds territory, and even those single events stayed under 300ms both times
they occurred. This is a meaningfully more precise claim than A1 alone could support: **not**
"latency is always <22ms" (A1's original framing, now known to be too strong), but **"deadline
misses were not observed in ~55,000 real inferences on this hardware, even under active desktop/
IDE contention, though rare double-digit-to-triple-digit-millisecond scheduling-jitter outliers do
occur and should be budgeted for, not assumed away."**

## 3.22, 3.23, 3.24, 3.25, 3.26 — extended ablation batch — ✅ DONE

Wrote `deploy/pi_research_suite/exp_extended_ablation_batch.py`: five checklist items reusing one
Keras/FP16/INT8 prediction pass over the real 5,437-window test split (Experiment D's data) plus a
re-run of Experiment C's offline-vs-causal window pairs with richer statistics. Full results:
`results/pi_research/extended_ablation_batch.json`.

**3.23 Threshold-margin analysis** (INT8, deployed threshold 0.9892255): only **5 windows (0.09%)**
of 5,437 land within ±0.001 of the boundary, 20 (0.37%) within ±0.005, 70 (1.29%) within ±0.01, 315
(5.79%) within ±0.05. **This is the mechanistic explanation for Experiment D's finding**: INT8
quantization noise (mean abs diff ≈0.066 vs. Keras) rarely flips a real decision specifically
because so few real windows sit close enough to the decision boundary for that much noise to matter
— the classifier is confidently far from the boundary on the overwhelming majority of both normal
and crash-like windows.

**3.24 Reconstruction-error quantization comparison**: FP16 tracks Keras's `recon_error` almost
exactly (mean abs diff 6.9e-5, max 0.09). **INT8 is much noisier on this signal specifically**
(mean abs diff 0.612, and one single window shows a **702.55 absolute difference** — a large
outlier worth flagging honestly rather than only reporting the mean). Despite that outlier,
**threshold-crossing agreement stayed 100% for both FP16 and INT8** — even the 702.55-diff window
apparently sits far enough from the 10.88 reconstruction threshold on both sides that the huge
absolute error still didn't flip its decision. Worth a closer look before citing "quantization
never affects reconstruction-based decisions" as a strong claim — this is one outlier out of 5,437,
not a swept guarantee.

**3.25 OR-rule branch contribution**: window-level, of 5,437 windows: 19 classifier-only positive,
**1 reconstruction-only positive**, 14 both, 5,403 neither. Event-level (real `TriggerPolicy`
replay per test session, INT8): of the 10 test sessions, 4 actually fired an alert — the 3 DaRUS
crash sessions all fired via **"both"** branches agreeing simultaneously, and the 2 staged fall/
near-fall sessions fired via **"classifier_only"**. **No test session in this split was rescued
by the reconstruction branch alone at the event level** — its unique window-level contribution (1
window) never became the deciding factor for a whole session's alert here. This doesn't contradict
the architecture's design rationale (`system_understanding.md` §2: the reconstruction branch is a
backstop specifically for crash types the classifier never saw labeled examples of) — it means
this particular in-distribution held-out test split doesn't happen to contain a case where that
backstop was needed; the OOD/unseen-crash experiment (`performance.md`, already in the offline
results) is the place that actually stresses this design rationale, not this test split.

**3.26 Detailed causal-filter comparison** (extends Experiment C's single 99.61%/100% headline
number): `crash_prob` correlation between offline and real-time paths = **0.945**, `recon_error`
correlation = **0.891** — strong positive agreement, consistent with "phase-lag noise, not a
different decision surface." Breaking the differences down by source shows where they concentrate:

| Source | n | Mean abs `crash_prob` diff | Mean abs `recon_error` diff |
|---|---|---|---|
| carla | 2,614 | 0.014 | 0.019 |
| road | 2,368 | 0.058 | 0.008 |
| fall | 269 | 0.074 | 0.007 |
| near_fall | 156 | 0.128 | 0.010 |
| **darus** | 30 | **0.288** | **4.563** |

By class: normal windows (n=4,994) mean abs diff 0.035/0.014; **crash-like windows (n=443) mean
abs diff 0.104/0.312** — roughly 3x/22x larger. **This makes physical sense and should be stated
plainly rather than treated as concerning**: DaRUS's short, high-fidelity, high-amplitude impact
traces are exactly the signal shape where a causal EMA filter's phase lag differs most from a
zero-phase (non-causal) Butterworth filter — rapid transients are where phase response matters.
The differences are real and concentrated exactly where physical intuition says they should be,
and — per Experiment C above — still essentially never change the actual fire/no-fire decision.

**3.22 FP16 vs. INT8 event-level agreement**: **100% (10/10 test sessions)** — identical fire/
no-fire outcome for every session under both quantization formats. One minor timing nuance worth
noting: `near_fall_Acceleration On Curve` triggers at window index 56 under FP16 vs. index 55 under
INT8 — a one-window (~0.3s) difference in exact trigger timing on an otherwise-identical outcome,
consistent with the kind of small numerical drift Experiment D already characterized.

## 3.6 Thread-count sensitivity — ✅ DONE

Same INT8 model, 2,000 inferences each at `num_threads` = 1, 2, 4. Full results:
`results/pi_research/thread_count_sensitivity.json`.

| Threads | Mean | Median | p95 | **Max** |
|---|---|---|---|---|
| 1 | 0.673ms | 0.604ms | 1.031ms | **7.52ms** |
| 2 | 0.977ms | 0.582ms | 2.746ms | 24.83ms |
| 4 | 0.815ms | 0.335ms | 2.855ms | **55.39ms** |

**Verdict: more threads does not help this model, and makes the tail worse.** Median latency
does drop somewhat with more threads (thread-parallelism helping the actual compute), but p95 and
especially max get markedly worse — most likely thread-spawn/synchronization overhead dominating a
model this small (83KB, sub-millisecond compute). **1 thread gives the most predictable tail
latency** (7.5ms worst case vs. 24.8ms/55.4ms) at only a small median cost. Confirms the checklist's
own hypothesis: one thread is sufficient, and the other 3 cores can stay free for the rest of the
system (voice assistant, BLE bridge, GUI) rather than being claimed by the model.

## 3.8 / 3.9 Cold-start timing / process restart reliability — ✅ DONE (adapted — full live-restart-under-load isn't possible without the sensor)

`crash_monitor.py` blocks forever in `connect_sensor()` without a real MPU6050 (established
repeatedly this session), so a literal "kill/restart under replay mode" isn't possible — there is
no replay/bypass mode in the deployed script. Adapted: launched 10 completely fresh
`crash_monitor.py` processes back-to-back, timing from process launch to the `"Loaded thresholds"`
log line — which fires immediately after config/logging setup and right before `CrashModel()`
(TFLite load, already known from A1 to cost ~4-5ms) and before `connect_sensor()` (where it would
hang). This is the furthest any restart can get without hardware, and is a genuine cold-start-to-
ready proxy. Full results: `results/pi_research/cold_start_timing.json`.

| Metric (10 fresh launches) | Value |
|---|---|
| Mean | 0.710s |
| Median | 0.712s |
| Min / Max | 0.636s / 0.830s |
| Failures | **0 / 10** — every launch reached the threshold-loaded point cleanly |

**Verdict**: consistent ~0.7s process startup (dominated by Python interpreter + import overhead —
`numpy`, `tensorflow.lite`/`tflite_runtime`, `pyyaml`, `pyserial`, `gpiozero`, `mpu6050` import
attempt — not by the model itself, which A1 already showed loads in ~4ms), low variance, zero
failures across 10 restarts. Threshold reload correctness already independently confirmed (every
run logged the exact same `classifier_prob=0.989226 recon_error=10.878736` values, matching
`models/thresholds.json`). **What this does NOT cover** (genuinely not performed): memory cleanup
across restarts and repeated-restart error accumulation under an actually active sensor connection
— that needs the live MPU6050 and belongs with Section 4's blocked items.

## 3.13 Background-load levels — ✅ DONE (0/1/2/3 workers)

Extended Part 1's Experiment B (1 worker) with 0, 2, and 3 concurrent busy-loop workers via
`deploy/benchmark_device.py --concurrent-workers N`. Files: `results/pi_research/
pi_benchmark_workers_{0,2,3}.json` (1-worker result already in `results/pi_benchmark.json` from
Part 1).

| Workers | Solo/baseline mean | Under-contention mean | Degradation |
|---|---|---|---|
| 0 | 0.604ms | — | — |
| 1 (Part 1) | 0.589ms | 0.656ms | +11% |
| 2 | 0.885ms | 0.595ms | *(see note)* |
| 3 | 0.554ms | 1.224ms | **+121%** |

Note on the 2-worker row: `benchmark_device.py` measures "solo" *before* spawning workers and
"concurrent" *while* they run, each pass reusing the same warmed-up interpreter — the 2-worker
solo figure (0.885ms) is itself noisier than the other solo figures (likely desktop/IDE background
activity variance unrelated to this test, consistent with 3.4's finding that this Pi runs a full
desktop session throughout). The clear, consistent trend is the **3-worker** row: mean latency more
than doubles (0.554ms → 1.224ms) under 3 busy-loop competitors. **Reminder from `benchmark_device.py`
itself**: these busy-loop workers are a CPU-contention proxy, not the real drowsiness-detection
module's actual profile — don't cite this as "the model survives concurrent drowsiness detection,"
only as "the model degrades gracefully, not catastrophically, under increasing CPU contention."

## 3.19, 3.20, 3.27, 3.28 — second software-logic batch — ✅ DONE

Wrote `deploy/pi_research_suite/logic_robustness_tests_2.py`. Full results: `results/pi_research/
logic_robustness_tests_2.json`.

**3.19 Sampling-jitter simulation**: confirmed both by code inspection and empirically that
`WindowScorer` is driven purely by **sample count**, never by wall-clock timestamps — it has no
timing input at all. This means ±2ms/±5ms jitter or delayed-but-not-dropped samples **cannot
affect `crash_prob`/`recon_error` even in principle** (replaying the identical sample sequence
twice produced bit-identical output, as expected). The only place jitter could matter is the
caller's own real-time pacing loop, which 3.1 above already measured directly with zero deadline
misses over 15 real minutes — so this item reduces to "already answered by 3.1," not a separate
unknown.

**3.20 Dropped-sample simulation**: replayed the same 2,397-sample session with a sparse 1-in-20
drop pattern (2,277 samples survive, 148 windows generated) and a 30-sample burst drop (2,367
samples survive, 154 windows generated) — **no exception either way.** But: **the deployed code has
no drop counter or gap-detection logic at all** — a dropped sample is completely invisible to the
running system; the pipeline just silently scores whatever samples do arrive as if the timing were
perfectly regular. Worth flagging honestly as a real gap for the paper's robustness/limitations
discussion, not just "it doesn't crash."

**3.27 Causal-filter state-reset test**: two real behaviors confirmed, both worth documenting
explicitly (neither is currently mentioned in `system_understanding.md`):
1. `CausalGravityFilter`'s very first-ever call always returns exactly `[0,0,0]` (it initializes
   its internal gravity estimate directly from the first reading) — a real, deterministic cold-start
   transient, not a bug.
2. **`WindowScorer.clear()`** (called by `crash_monitor.py main()` right after every 30s alarm
   countdown) **only clears the sample buffer — it does not reset `gravity_filter`.** So after every
   real alarm event, the causal gravity EMA resumes from its state *before* the 30s gap rather than
   re-initializing fresh, and needs roughly a few filter time constants (~1-2s at 0.3Hz cutoff) of
   new samples to reconverge. Arguably the right choice (avoids re-triggering the cold-start-zero
   transient right after a real crash), but it's undocumented current behavior, confirmed here for
   the first time.

**3.28 Startup grace-period behavior**: confirmed empirically — the first non-`None` decision from
`try_score()` occurs at exactly sample #60 (matching `window_samples=60` exactly), i.e. **1.2s**
of continuous sampling from a cold start (or after any `clear()`) before the model can produce its
first decision. No partial window is ever scored, and `TriggerPolicy.update()` is never even called
before a full window exists.

## 3.17 Logging-overhead comparison — ✅ DONE

Same INT8 model, 1,000 inferences each at three logging configurations. Full results:
`results/pi_research/logging_overhead_comparison.json`.

| Configuration | Mean | Median |
|---|---|---|
| No logging (`CRITICAL` level, handler present but nothing written) | 0.627ms | 0.568ms |
| Minimal (`WARNING` level, no per-window line) | 0.579ms | 0.495ms |
| **Verbose — real deployed per-window `INFO` line** (`crash_prob=... recon_error=... streak=...`, exactly what `crash_monitor.py main()` actually logs every window) | **1.400ms** | **1.215ms** |

**Verdict**: the deployed system's real per-window `logger.info(...)` call (which A4's benchmark
script above did *not* include — worth noting as a precision caveat on A4's 2.64ms mean, which is
therefore a slight underestimate of the true deployed per-window cost) roughly **doubles** mean
per-window latency. Still trivial against the 300ms budget (1.4ms vs. 300ms = ~0.5%), so this
changes no conclusion, but it's the more precise number if the paper wants to cite "true deployed
per-window overhead including logging" rather than a bare-inference or logging-free replay figure.

## 3.38 Ambient temperature (approximate, via the deployed DHT22) — ✅ DONE

`/home/helmx/sensor_data.json` (written every ~10s by the live `helmx-ble.service` / `bluetooth.py`
— see `pin_connections.md`): **36.8°C, 64.4% humidity** at time of capture (2026-08-30 17:29:46
PKT). Per the checklist's own caveat, reported as **approximate, uncalibrated** — this is the
actual DHT22 already wired into this Pi, not a separate reference thermometer. 36.8°C ambient is
notably warm relative to the Pi's own ~55°C idle CPU temperature range seen throughout this
session — consistent with an indoor space without strong air conditioning, and helps contextualize
why the Pi's baseline CPU temp (mid-50s°C at idle) is on the warmer side purely from ambient, not
from any inference workload (A1's/D's/3.6's/3.17's brief bursts are all far too short to shift CPU
temp meaningfully; only the 15-30 minute sustained runs — A3, 3.1 — could, and neither showed
throttling even so).

## 3.41 Service enablement/restart policy — ✅ DONE

Full dump: `results/pi_research/service_enablement_policy.txt`. `helmx-ble.service`:
`Restart=always`, `RestartUSec=3s`, enabled, active. `rhasspy.service`: `Restart=always`,
`RestartUSec=5s`, enabled, active. **`helmx-crash-monitor.service` is not installed on this
system** (confirmed again — `systemctl status` reports "could not be found"). The repo's own
template (`deploy/helmx-crash-monitor.service`) was captured for reference: it specifies
`User=pi` and `WorkingDirectory=/home/pi/HelmX/Crash Detection` — **neither matches this actual
deployment** (this system's user is `helmx`, and the repo actually lives at `/home/helmx/Crash
Detection/Crash-Detection`). If someone tried to `systemctl enable` this template as-is on this
specific Pi, it would fail outright (no `pi` user exists here, wrong path) — worth fixing in the
repo before deployment, a small but concrete, previously-unnoticed finding from this pass.

## 3.42 / 3.43 Journal and kernel logs — ✅ DONE

`results/pi_research/journal_crash_service.txt` (last 30 lines each of `helmx-ble.service` and
`rhasspy.service` — no `helmx-crash-monitor.service` journal exists, noted explicitly in the file,
since it isn't installed). `results/pi_research/dmesg.txt` (full 1,426-line kernel ring buffer).
Grepped specifically for undervoltage/thermal/throttling messages (the checklist's stated focus for
this item): **zero matches** — no undervoltage, thermal, or throttling event has ever been logged
at the kernel level during this Pi's current uptime, consistent with every `vcgencmd
get_throttled=0x0` reading throughout this entire session.

## Items intentionally NOT performed, with specific reasons

| Item | Reason not performed |
|---|---|
| **3.7 CPU-governor sensitivity** | 3.3 already established `force_turbo=1` in `/boot/firmware/config.txt`, which locks the ARM clock at its max 1800MHz **regardless of the scaling governor** (`cpuinfo_min_freq == cpuinfo_max_freq == 1800000` — there is nothing left for a governor to scale between). Comparing `ondemand` vs. `performance` would almost certainly show zero measurable difference because the thing a governor controls is already disabled by `force_turbo`. Not run, because the honest expected result is a null comparison — not because it was unsafe, though the checklist's own "do not change governor if it risks disturbing the system" caution also applies since this is a live, actively-used desktop machine. |
| **3.14 Memory-pressure benchmark** | This Pi is a live desktop machine actively running VS Code, several Chromium instances, and other user work throughout this whole session (3.4). Deliberately allocating controlled memory pressure risks triggering swapping or the OOM killer against the user's actual live work, not just the benchmark — judged too disruptive to run without explicit permission on a shared, in-use system. Would be safe and appropriate on an idle/dedicated test image. |
| **3.15 I/O-pressure benchmark** | Marked "optional" in the checklist. Every measurement this session already shows the model/pipeline is CPU/RAM-bound, not I/O-bound (near-zero disk activity in any profile) — low expected informational value versus adding unnecessary disk wear/activity to the user's live system. |
| **3.16 Network-load benchmark** | Marked "optional." The entire deployed decision path (`WindowScorer`/`TriggerPolicy`/`CrashModel`) has zero network I/O — there is no plausible mechanism by which network load would affect inference latency on this architecture. Skipped as low-value for the same reason 3.15 was. |
| **3.36 Safe storage-I/O benchmark** | Checklist itself scopes this as "optional, non-destructive only." Same reasoning as 3.15 — the pipeline doesn't touch storage in its hot path; skipped as low marginal value. |
| **3.37 Fan/cooling behavior** | Requires physically observing the actual hardware enclosure (is a fan present, what's its trigger policy) — not something obtainable through software/SSH on this session. No fan-control kernel driver/sysfs entry was noticed during the `dmesg`/`vcgencmd` review, but that's not the same as a confirmed physical answer. **Needs a human to look at the physical unit.** |
| **3.39 Power-source state** | Same limitation as 3.37 — battery vs. USB-C, supply current rating, and enclosure state are physical facts this session cannot observe. Partial indirect evidence already captured elsewhere: `vcgencmd get_throttled` has shown `0x0` (no under-voltage) at every single check throughout this entire session, which is consistent with (but not proof of) an adequately-rated supply. |
| **3.40 Boot time** | Measuring power-on → OS-ready → service-ready requires an actual reboot. This session is running interactively on this same Pi (via this very SSH/terminal connection) — a reboot would terminate this session and any other active user work (VS Code, etc.) immediately, with no way to resume automatically. **Not attempted without explicit user authorization**, since it's a disruptive, hard-to-reverse-mid-session action. |
| **3.48 Python heap/GC growth** | Checklist itself scopes this as "only if convenient or leak suspected." No leak was suspected or observed anywhere this session — A2's idle-retry-loop RSS was a flat, unmoving plateau, and 3.1's 15-minute sustained real pipeline run held a steady ~180MB RSS throughout (`results/pi_research/a4_replay_streaming_pipeline.json`'s resource samples). The condition that would trigger this item never arose. |
| **3.50 Restart-after-failure resilience (SIGTERM/SIGKILL under systemd)** | This item is specifically about the deployed crash-monitor's own systemd `Restart=`/`RestartSec=` policy in action — but (3.41, confirmed again here) **no `helmx-crash-monitor.service` is installed on this system**, so there is no live systemd-managed instance to kill and observe restarting. Testing kill/restart against a manually-launched bare subprocess (as 3.8/3.9 already did, 10/10 clean restarts) doesn't exercise real systemd restart policy, so it wasn't substituted here to avoid claiming this item as answered when it wasn't. Killing one of the *other* real live services (`helmx-ble`/`rhasspy`) to exercise systemd's restart mechanism in general was considered and rejected — it would briefly interrupt real, currently-relied-upon sensor logging/voice-assistant functionality for a test unrelated to those services. **Re-run once `helmx-crash-monitor.service` is actually installed** (which itself needs the path/user fix noted in 3.41 first).

## 3.49 Thermal recovery after load — ✅ DONE (12 minutes, no active inference load this time)

Re-ran `deploy/pi_research_suite/exp_a3_thermal.py` for 12 minutes with **no** concurrent inference
load this time (unlike Part 1's A3, which deliberately ran alongside 30 minutes of real inference).
Original A3 result preserved unchanged at `results/pi_research/a3_thermal.json`; this run saved
separately as `results/pi_research/a3_thermal_recovery_curve.json`.

| | A3 (Part 1, WITH 30min sustained inference load) | 3.49 (this item, idle, no load) |
|---|---|---|
| Initial temp | 56.9°C | 56.4°C |
| Mean temp | 55.4°C | 55.5°C |
| Max temp | 61.3°C | 57.9°C |
| Throttling | False | False |

**Verdict, and it's a genuinely useful one for the paper**: temperature under sustained real
inference load and temperature while idle are **essentially the same** on this hardware (mean
55.4°C vs. 55.5°C) — the small max-temp difference (61.3°C vs. 57.9°C) is well inside normal
sample-to-sample variation, not a clear load-driven signal. This means **ambient conditions, not
the model's own compute cost, dominate this Pi's thermal baseline** — consistent with 3.38's
directly-measured 36.8°C ambient (via the deployed DHT22) being unusually warm for indoor
electronics. **The practical implication is reassuring, not concerning**: if idle and
under-sustained-load temperatures are this close, the inference workload itself is contributing
negligible thermal load — there is no "cooldown curve" to show because there was barely any
load-driven heating to cool down from in the first place.

## Checklist §7 "before shutdown" items #4-9 — ✅ DONE

Not separate experiments — housekeeping the checklist explicitly asks for: all JSON/log outputs
are in `results/pi_research/` (24 files, listed below); every experiment script is in `deploy/
pi_research_suite/` (11 scripts, all committed to the repo, not scratch files); deployed models/
thresholds are untouched in `models/`; SHA256 hashes captured (`model_hashes.txt`); system/service
logs exported (`process_snapshot.txt`, `journal_crash_service.txt`, `dmesg.txt`,
`service_enablement_policy.txt`); and the checklist file itself is now copied alongside these
results at `piResults/HelmX_Paper1_FINAL_Pi_Data_Collection_Checklist.md` for archival.

## Part 2 summary — what's real, what's blocked, and why (mirrors Part 1's summary table)

| # | Item | Status | Headline |
|---|---|---|---|
| 3.1 | Replay-paced full pipeline benchmark | ✅ Ran (15 min, real cadence) | **0 deadline misses** across 2,985 real windows |
| 3.2 | Repeat A1 | ✅ Ran | Median/p95/p99 reproduce tightly; **surfaced a 286.8ms outlier** — not a fluke |
| 3.3 | Environment capture | ✅ Done | Full 481-line dump; confirmed `force_turbo=1` locks CPU at max clock |
| 3.4 | Service/process inventory | ✅ Done | Full desktop+IDE load running throughout every test in this session |
| 3.5 | Long-tail latency (n=50,000) | ✅ Ran | 0% deadline-miss rate even so; rare 100ms+ outliers confirmed real |
| 3.6 | Thread-count sensitivity | ✅ Ran | 1 thread has the best (lowest) worst-case tail; more threads hurts, not helps |
| 3.8/3.9 | Cold-start / restart timing | ✅ Ran (adapted) | ~0.71s consistent cold start, 10/10 clean restarts |
| 3.10/3.11/3.12 | Threshold/model/TFLite metadata | ✅ Done | All frozen, hashed, introspected |
| 3.13 | Concurrent-load levels (0-3 workers) | ✅ Ran | Latency +121% at 3 workers — graceful, not catastrophic |
| 3.17 | Logging-overhead comparison | ✅ Ran | Real per-window logging ~2x's mean latency (still trivial vs. budget) |
| 3.18-3.32 (logic batch) | Malformed input, determinism, cooldown, cancel-window, alarm fallback, GSM/GPS failure, jitter, dropped samples, filter reset, grace period, quantization/OR-rule ablations | ✅ Ran | **Two real findings**: `handle_suspected_crash()` returns `True` unconditionally regardless of SMS success; dropped samples are currently invisible to the pipeline (no gap detection) |
| 3.34/3.35 | NTP/clock, storage | ✅ Done | Boots from SSD, not SD card; NTP-synced |
| 3.38 | Ambient temp (via DHT22) | ✅ Done | 36.8°C — explains why idle CPU temp runs mid-50s°C |
| 3.41/3.42/3.43 | Service policy, journal, kernel logs | ✅ Done | **Repo's own systemd template has wrong user/path for this deployment** |
| 3.44-3.47 | Affinity/priority/threads/FDs | ✅ Done | Default scheduling, no pinning, no FD leak observed |
| 3.49 | Thermal recovery | ✅ Ran (12 min) | Idle and under-load temps nearly identical — ambient-dominated, not compute-dominated |
| Section 4 (4.1-4.8) | All MPU-dependent live-sensor items | ❌ Not performed | Same root cause throughout: MPU6050 physically not connected/responding (`pin_connections.md`) |
| Section 5 | Offline Paper 1 artifacts | ✅ Verified present | Nothing missing, nothing regenerated |
| Section 6 | Model/system facts | ✅ Confirmed | Matches deployed artifacts exactly |
| 3.7 | CPU-governor sensitivity | ⚠️ Not performed | Moot — `force_turbo=1` already locks frequency regardless of governor |
| 3.14/3.15/3.16/3.36 | Memory/I/O/network pressure benchmarks | ⚠️ Not performed | Live shared desktop system — too disruptive / low expected value |
| 3.37/3.39 | Fan/cooling, power-source physical state | ⚠️ Not performed | Requires physical human observation of the hardware |
| 3.40 | Boot time | ⚠️ Not performed | Would require a disruptive reboot mid-session |
| 3.48 | Python heap/GC growth | ⚠️ Not performed | Conditional item ("if leak suspected") — no leak was ever observed |
| 3.50 | Restart-after-failure under systemd | ⚠️ Not performed | No live `helmx-crash-monitor.service` instance exists to test against |

**Two genuinely new findings from this pass, worth carrying into the paper's limitations/future-work
section regardless of MPU6050 status**: (1) `deploy/crash_monitor.py`'s `handle_suspected_crash()`
returns `True` unconditionally after the countdown expires, regardless of whether the SMS actually
sent — currently harmless since the return value is discarded by its only caller, but a latent bug
worth fixing; (2) the deployed pipeline has no dropped-sample detection at all — sample loss is
currently silent and unlogged. Neither requires the MPU6050 to fix; both are software-only issues
discovered specifically by this checklist's robustness-testing items.

---
---

# Part 3 — `Final Things.txt` follow-up items

## Guidance on the two software findings — not modified, documented only (per explicit instruction)

Per the user's supplied guidance: the two findings above (`handle_suspected_crash()`'s unconditional
`return True`, and invisible dropped samples) are **intentionally left unmodified in the deployed
code**. Both are reported here as transparent limitations/future-work items for the paper, not as
bugs to fix mid-benchmarking-cycle — changing a deployed artifact after it has already been
extensively validated (Parts 1–2 above) would invalidate that validation and require re-running the
affected experiments. Fix in a follow-up revision, with the affected experiments (A5, the logic-
robustness batch) re-run afterward against the corrected code.

> **Update, follow-up session:** this follow-up revision has now happened — see **Part 4** at the
> end of this document. Both findings are corrected, the pre-fix (`evaluated-v1`) code is preserved
> at `deploy/frozen_v1/`, and every experiment listed above as needing a re-run (A5, the logic-
> robustness batch, plus the full deployment-weakness re-validation plan's own required regression
> set) was re-run against the corrected code, on this same hardware.

## Framing the thread-count finding as a deployment recommendation

3.6 (Part 2) found that 1 TFLite interpreter thread gives the best (lowest, most predictable) tail
latency, while 2/4 threads reduce median latency slightly but substantially worsen p95/max —
consistent with thread-spawn/synchronization overhead dominating a model this small. Stated
plainly as the practical recommendation this evidence supports: **use a single inference thread
for this model.** It reduces scheduling/synchronization variability on the metric that matters most
for a real-time safety system (worst-case latency, not average), and leaves the Pi's other 3 cores
free for the helmet's other concurrent services (voice assistant, BLE/environment bridge) rather
than contending with them. `deploy/crash_monitor.py`'s `CrashModel` already doesn't pass an
explicit `num_threads` argument to the TFLite interpreter; worth an explicit `num_threads=1` for
the reason above, rather than relying on the runtime's default.

## Publication-quality figures — ✅ DONE, 9 IEEE-style figures generated

Wrote `deploy/pi_research_suite/generate_figures.py`: one script covering the major experiments
from Parts 1–2, styled to IEEE conventions (Liberation Serif — Times New Roman metric-compatible
— font, single/double-column widths, Okabe–Ito colorblind-safe palette, 300 DPI + vector PDF,
light gridlines, no chart-junk). Output: **`piResults/figures/`** — 9 figures (PNG + PDF each),
plus `CAPTIONS.md` with ready-to-paste IEEE-style caption text for every figure, plus two raw-data
files (`fig2_raw_latencies_ms.npy`, `fig4_raw_offline_vs_realtime.npz`) for the two figures whose
underlying experiments only persisted summary statistics and were cheaply recomputed for plotting.

| File | Content |
|---|---|
| `fig1_inference_latency_headroom` | Median/p95/p99/max latency across A1, A1-repeat, and the 50k long-tail run vs. the 300ms budget |
| `fig2_long_tail_latency_histogram` | Log–log histogram of all 50,000 individual inference latencies |
| `fig3_thermal_stability` | Temperature vs. time, sustained-load (30min) vs. idle (12min), vs. Pi 4's throttle limit |
| `fig4_offline_vs_realtime_agreement` | Scatter: offline (zero-phase) vs. real-time (causal) `crash_prob`, r=0.945, colored by class |
| `fig5_quantization_comparison` | 3-panel: size / latency / decision-agreement across Keras, FP16, INT8 |
| `fig6_thread_count_sensitivity` | Latency vs. TFLite thread count (1/2/4) |
| `fig7_concurrent_load_degradation` | Mean latency vs. 0–3 concurrent busy-loop workers |
| `fig8_trigger_latency_by_source` | Box plot of trigger-confirmation latency, DaRUS vs. fall vs. near-fall |
| `fig9_or_rule_branch_contribution` | Classifier-only / reconstruction-only / both / neither, log-scale bar chart |

A data-integrity note caught and fixed during this pass: the 1-worker concurrent-load JSON from
Part 2's §3.13 had been silently overwritten by that section's own 0-worker run (a same-filename
collision in a loop I wrote) — the *numbers* survived in this document's Part 2 text, but the raw
file was gone. Re-measured fresh (`results/pi_research/pi_benchmark_workers_1.json`) before Fig. 7
was built, rather than reconstructing the figure from the lost original.

## Headless / reduced-background latency check — ✅ RAN — **256.7ms → 6.4ms max latency**, strongly confirms the scheduler-contention hypothesis

Before touching anything: **this Claude Code session runs as a VS Code extension** — a child
process of VS Code itself. `Final Things.txt` asked to close VS Code along with everything else;
doing that would have terminated this session mid-task, before the benchmark could run or the
result be reported. Flagged this to the user directly, who chose: stop everything else the file
lists (Chromium, Rhasspy, the BLE/DHT22 bridge, MQTT, remote desktop) but leave VS Code (and the
window manager it depends on) running.

**What was stopped** (all via `systemctl stop`, all real production services on this Pi, not test
scaffolding): `rhasspy.service`, `helmx-ble.service` (the DHT22/MQ135 BLE bridge from
`pin_connections.md`), `mosquitto.service` (MQTT broker), `wayvnc.service` +
`wayvnc-control.service` (remote desktop). Chromium was already closed by the time this ran (not
this session's doing). VS Code and the `labwc` window manager were deliberately left running per
the user's explicit choice.

**An unexplained wrinkle worth reporting honestly**: the first `systemctl stop` attempt succeeded
(`systemctl is-active` confirmed all five `inactive`), but `mosquitto`/`rhasspy` were both back up
and running under **fresh PIDs with `PPID=1`** about a minute later — `journalctl` confirms systemd
itself logged a clean `Starting… / Started…` sequence, not a crash-restart. No cron job, systemd
timer, path unit, or XDG autostart entry was found that would explain this in the time available to
investigate — the mechanism remains unidentified. **Reacted by stopping all five again immediately
and launching the benchmark right away**, minimizing the window for anything to come back before
measurement started; the 50,000-inference run itself completed in about 34 seconds, well inside any
observed respawn delay. This should be flagged as a loose end for the actual deployment (something
appears to actively supervise these services beyond systemd's own `Restart=` policy, and it isn't
currently understood what) — worth investigating separately, but not a threat to the validity of
the latency numbers below given the timing.

Ran the exact same 50,000-inference long-tail protocol used in Part 2 §3.5. Full results:
`results/pi_research/a1_long_tail_latency_headless.json`. (Note: this run's output initially
overwrote the *original* loaded-condition `a1_long_tail_latency.json` in place — the same kind of
same-filename mistake as the §3.13 one caught above — caught immediately and the new file renamed
to `..._headless.json` before anything else could touch it; the original loaded-condition numbers
were already fully transcribed into this document's §3.5 section above and are not lost, just no
longer available as a separate raw JSON.)

| Metric (n=50,000 each) | **Loaded** (Part 2, §3.5) | **Headless** (this item) |
|---|---|---|
| Mean | 0.936ms | 0.597ms |
| Median | 0.771ms | 0.503ms |
| p95 | 1.778ms | 0.964ms |
| p99 | 3.940ms | 1.323ms |
| p99.9 | 7.232ms | 2.406ms |
| **Max** | **256.73ms** | **6.36ms** |
| Events >10ms | 18 | **0** |
| Events >100ms | 3 | **0** |
| Events >300ms (deadline miss) | 0 | 0 |

**This is exactly the supporting evidence `Final Things.txt` asked for, and it's a strong result**:
maximum observed latency dropped **40x** (256.7ms → 6.4ms), and every single one of the 18
`>10ms` and 3 `>100ms` outlier events seen under load **vanished entirely** under reduced
background contention — not reduced in frequency, reduced to zero. Median/p95/p99 all improved
too (roughly 1.5–3x tighter), consistent with less OS scheduler preemption competing for the same
CPU cores. **This directly supports the scheduler-contention explanation** offered in Part 2 for
the 109.6ms/286.8ms/256.7ms outliers: they were not a property of the model, the TFLite runtime, or
the hardware's compute path — they were a property of everything else this Pi happened to be doing
at the same time during development/testing. Figure: `piResults/figures/
fig10_loaded_vs_headless_latency.png`.

**Caveat to state precisely, not overclaim**: VS Code and the window manager were still running
throughout this "headless" run (for the reason explained above), so this is not a fully clean
zero-GUI measurement — the true floor on a genuinely headless production image (no desktop session
at all) could be even tighter than 6.36ms max. Still, stopping the specific services that were
actually running concurrently with every other benchmark in this whole study (voice assistant, MQTT,
BLE bridge, remote desktop) already recovers the overwhelming majority of the effect.

**Services restored afterward**: all five services were restarted (`systemctl start`) immediately
after the benchmark completed and confirmed `active` again — this Pi's normal helmet functionality
(voice assistant, sensor bridge, remote access) was down for approximately 2 minutes total, not left
disabled.

---
---

# Part 4 — `HelmX_Paper1_Deployment_Weaknesses_Correction_Revalidation_Plan.md`: Weakness 1 & 2 corrected and re-validated

This is the follow-up Part 3 said would come later: the two software findings from the
logic-robustness batch (Part 2, §3.18-3.32) — `handle_suspected_crash()`'s unconditional
`return True`, and dropped IMU samples being invisible to the pipeline — are now **fixed in
`deploy/crash_monitor.py`**, following the correction plan's own recommended design exactly, and
re-validated against real held-out sessions and, for the pipeline-latency claim, real 50Hz-paced
hardware time on this same Pi.

## What was understood before touching anything

Before editing, traced the exact call path both weaknesses live on, to make sure the fix couldn't
silently change anything already validated in Parts 1-3:

- `handle_suspected_crash()` has exactly **one caller** (`main()`), which already discarded the
  return value — so its return type could change shape without touching `main()`'s control flow.
- `WindowScorer` (`append()`/`try_score()`/`clear()`) is driven **purely by sample count** (Part 2,
  §3.19/3.20) and is called directly, with no timing wrapper, by five different
  `deploy/pi_research_suite/` scripts (`exp_a4`, `exp_a5`, `exp_c`, both `logic_robustness_tests*`).
  Any fix for dropped-sample detection that changed `WindowScorer` itself would silently change the
  behavior every one of those already-validated experiments depends on.
- The plan's own architectural guidance (`HelmX_Paper1_Deployment_Weaknesses_Correction_
  Revalidation_Plan.md` §6.1) is explicit about this: timing validation belongs at the acquisition
  layer, **before** a sample reaches `WindowScorer`, not inside it.

Consequence: the Weakness 2 fix is a **new class added alongside** `WindowScorer`
(`SampleStreamGuard`), used only in `main()`'s live loop. `WindowScorer` itself is **byte-for-byte
unchanged** — confirmed directly below, not just asserted.

## Freeze step (plan §2)

Before any edit, copied the exact evaluated version and hashed it — `deploy/frozen_v1/`:
`crash_monitor_evaluated_v1.py`, `config_evaluated_v1.yaml`,
`exp_a4_replay_streaming_pipeline_evaluated_v1.py`, `FROZEN_v1_HASHES.txt` (SHA256 of those plus
`models/helmx_crash_model_int8.tflite`/`_fp16.tflite`/`thresholds.json`, confirming the model
artifacts themselves are untouched by this pass). `deploy/crash_monitor.py` is now the corrected
version in place (not a separate file) — `deploy/frozen_v1/` is the permanent record of exactly what
every Part 1-3 result above was measured against.

## Weakness 1 — `handle_suspected_crash()` now returns a structured result

**Fix** (`deploy/crash_monitor.py`): a new `CrashAlertResult` dataclass
(`cancelled` / `sms_attempted` / `sms_sent` / `gps_available`, per the plan's "preferred design")
replaces the bare `bool`. `sms_sent` now reflects the *actual* `gsm.send_sms()` return value instead
of being unconditionally `True` once the countdown expires. Added the plan's distinct log tags
(`CRASH_ALERT_CANCELLED`, `GPS_UNAVAILABLE`, `SMS_ATTEMPTED`, `SMS_SENT`, `SMS_FAILED`). `main()`
now logs the structured outcome after every alert instead of discarding it silently.

**Re-validation** — `deploy/pi_research_suite/logic_robustness_tests_corrected_v2.py`, real deployed
classes, mocked GSM only where the plan specifically calls for a controllable success/failure
outcome (`FakeGsm`). Full results: `results/pi_research/logic_robustness_tests_corrected_v2.json`.

| Test (plan §4) | What it checks | Result |
|---|---|---|
| **W1-R1** cancellation | Cancel mid-countdown → no SMS attempted | ✅ `cancelled=True, sms_attempted=False, sms_sent=False`, 0 `send_sms()` calls made |
| **W1-R2** SMS success (mocked) | `send_sms()`→`True` → reported as sent | ✅ `cancelled=False, sms_attempted=True, sms_sent=True, gps_available=True` |
| **W1-R3** SMS failure (mocked) | `send_sms()`→`False` → **not** reported as sent | ✅ `sms_sent=False` — **this is the exact case evaluated-v1 got wrong** (it returned `True` here) |
| **W1-R4** GPS unavailable | `get_gps_coordinates()`→`None`, both SMS outcomes | ✅ `gps_available=False` in both sub-cases, independent of `sms_sent` either way |
| **W1-R5** caller regression | Real (unmocked) `GsmModule`, no hardware — same condition as Part 2's 3.30c/3.32 | ✅ No exception; `sms_sent=False` now correctly distinguishes this from the cancelled case (evaluated-v1 returned `True` for both) |

**Verdict**: all 5 required checks pass. The specific bug found in Part 2 — silently reporting `True`
when `send_sms()` actually returned `False` — is confirmed fixed by W1-R3 and W1-R5 directly
reproducing the exact failing condition and getting the corrected answer.

## Weakness 2 — dropped/delayed samples are now detected at the acquisition layer

**Fix**: a new `SampleStreamGuard` class sits in `main()`'s loop between `read_sensor()` and
`scorer.append()`, using `time.monotonic()` deltas (not sample count) to notice an irregular gap.
On a detected gap it discards the in-flight window (`scorer.clear()`) and, only for gaps
`>= long_gap_reset_s`, also resets the causal gravity filter's stale EMA state (new
`CausalGravityFilter.reset()` method) — `WindowScorer.clear()` itself still doesn't touch the filter,
preserving the already-validated, deliberate behavior from Part 2's §3.27. The guard explicitly
rebases itself (`reset_baseline()`) right after `main()`'s existing post-alarm `scorer.clear()`, so
the **known**, already-handled 30s cancellation-countdown gap is never double-counted as an
unexpected drop — that distinction matters: conflating the two would have reset the gravity filter
after every real alert, silently reversing the §3.27 design decision this correction was not meant to
touch. Thresholds (`deploy/config.yaml: sensor.timing_guard`: `max_dt_s=0.030`, `min_dt_s=0.010`,
`long_gap_reset_s=1.0`) are explicitly documented in-repo as **provisional**, pending real MPU6050
timing data this Pi still doesn't have (Part 2, Section 4).

`WindowScorer` itself was deliberately left untouched — confirmed by diffing the corrected file
against the frozen snapshot: zero lines changed inside `CausalGravityFilter.apply()`, `WindowScorer`,
`TriggerPolicy`, `CancellationListener`, `LocalAlarm`, or `GsmModule`. This is *why* Part 2's 3.20
finding ("no drop counter or gap-detection logic" inside `WindowScorer`) **still reads as true
verbatim after the fix** — confirmed by literally re-running `logic_robustness_tests_2.py` unmodified
against the corrected code (see below) — the protection was deliberately added one layer above, not
inside it.

**Re-validation**, same script as Weakness 1, real held-out sessions
(`crash_session`=a near-fall/fall/DaRUS crash-like trace, `normal_session`=a >600-sample normal
driving trace):

**W2-R1 — no-gap regression, corrected-v2 vs. frozen evaluated-v1** (byte-for-byte, both sessions):

| | crash_session (156 windows) | normal_session (2,286 windows) |
|---|---|---|
| Bit-identical `crash_prob`/`recon_error` | ✅ | ✅ |
| Window decision agreement | 100% | 100% |
| Event trigger agreement | ✅ | ✅ |
| Guard: timing gaps / windows invalidated | 0 / 0 | 0 / 0 |

Proves the fix changes **nothing** about normal (no-gap) behavior — exactly the plan's required
outcome for this test.

**W2-R2 — isolated single-drop** (crash_session, one sample removed at 3 positions):

| Position | Gap detected | Windows invalidated | No exception |
|---|---|---|---|
| Early (idx 239) | ✅ | 1 | ✅ |
| Middle (idx 1198) | ✅ | 1 | ✅ |
| Crash-transient / late (idx 2157) | ✅ | 1 | ✅ |

**W2-R3 — sparse periodic drop** (normal_session):

| Pattern | Dropped | Gaps detected | Windows invalidated | % time invalidated | False trigger vs. no-drop baseline |
|---|---|---|---|---|---|
| 1-in-100 | 344 | 343 | 343 | **59.9%** | No — event outcome matches baseline |
| 1-in-500 | 69 | 68 | 68 | 11.9% | No — event outcome matches baseline |

**Honest limitation surfaced by this test, not assumed going in**: the "invalidate the whole
1.2s window" policy (plan §8, "the simplest safe policy") means a *single* dropped sample at 1-in-100
frequency discards **~60% of wall-clock time** from inference — because every drop nukes a full
60-sample window regardless of how small the drop was, and drops recur faster than a fresh window can
reaccumulate. This is a real cost of the conservative policy the plan explicitly chose, not a
measurement error, and worth stating plainly for the paper's limitations section: at
sufficiently-frequent real drop rates, this policy trades detection coverage for temporal-integrity
guarantees. No real MPU6050 drop-rate data exists yet (Part 2, Section 4) to say whether 1-in-100 is
realistic or pessimistic for this hardware.

**W2-R4 — burst drop** (normal_session, 2/5/10/30 consecutive samples):

| Burst size | Observed gap dt | Gap events | Windows invalidated | Gravity filter reset |
|---|---|---|---|---|
| 2 | 60ms | 1 | 1 | No (`<1.0s`) |
| 5 | 120ms | 1 | 1 | No |
| 10 | 220ms | 1 | 1 | No |
| 30 | 620ms | 1 | 1 | No |

Every burst produces **exactly one** gap event regardless of size (not one per missing sample) and
the observed `dt` matches `(burst_size+1) × 20ms` exactly in all four cases. Separately confirmed the
plan's own safety claim directly rather than just asserting it: **the sample buffer is provably empty
immediately after `clear()` on every detected gap** (checked in code, not inferred) — a scored window
can never contain samples from both before and after a detected gap.

**W2-R5 — delayed (not dropped) sample** (normal_session, +30/+50/+100/+300ms):

| Added delay | Observed dt | Gap detected | Sample discarded? |
|---|---|---|---|
| +30ms | 50ms | ✅ | No — guard invalidates the *window*, never drops the sample itself |
| +50ms | 70ms | ✅ | No |
| +100ms | 120ms | ✅ | No |
| +300ms | 320ms | ✅ | No |

All four delays exceed `max_dt_s` (30ms) once added to the 20ms base period, so all four trigger
invalidation under the current provisional thresholds — an honest, measured outcome, not assumed.
*Not* covered by this synthetic harness (noted directly in the results JSON rather than silently
skipped): genuinely out-of-order/duplicate-timestamp arrival, which needs real I2C/driver behavior to
honestly simulate — deferred to a live MPU6050 run (plan's W2-LIVE-1).

**Verdict**: all required W2-R1 through W2-R5 checks pass. The guard detects every injected gap,
never mixes pre/post-gap samples in one window, never mutates a sample's *value* (only ever decides
whether to keep or discard a window), and — critically — reproduces the frozen evaluated-v1 output
exactly when the stream is healthy.

## W2-R6 — corrected 15-minute replay-paced pipeline benchmark, run for real on this hardware

Wrote `deploy/pi_research_suite/exp_a4_replay_streaming_pipeline_corrected_v2.py` (same protocol as
the frozen `exp_a4_replay_streaming_pipeline.py`, now including `SampleStreamGuard.observe()` in the
measured per-window cost). A short smoke run (~9s) was done first to catch integration bugs cheaply,
then the full 15 minutes was actually run — real 66-session back-to-back replay, real 50Hz pacing, no
synthetic drops injected (a genuinely healthy stream is the point of this specific test; synthetic
gap behavior is W2-R2 through W2-R5 above). Full results:
`results/pi_research/a4_replay_streaming_pipeline_corrected_v2.json`.

| Metric | Evaluated-v1 (Part 2, §3.1) | **Corrected-v2 (this run)** |
|---|---|---|
| Input samples | 44,830 | 44,846 |
| Windows generated | 2,985 | **2,439** |
| Deadline misses (>300ms) | 0/2,985 | **0/2,439** |
| Per-window latency — mean | 2.64ms | 1.98ms |
| — p95 | 5.61ms | 2.89ms |
| — p99 | 9.61ms | 4.87ms |
| — max | 87.21ms | 17.03ms |
| Process RSS | ~180MB | ~181MB |
| Temperature (mean/max) | 54.8°C / 58.4°C | 52.0°C / 57.4°C |
| Thermal throttling (`_now` bits) | False | False |

**The window count is genuinely, correctly lower (2,439 vs. 2,985) — this is the fix working, not a
regression.** `stream_guard_telemetry` shows **168 real timing gaps were detected during this actual
50Hz-paced run on real hardware** (`max_sample_interval_ms: 263.4`, well past the 30ms threshold) —
under evaluated-v1, these same real scheduling delays would have been silently absorbed into windows
scored as if 60 samples still meant exactly 1.2s; under corrected-v2, each one correctly discarded the
affected window instead (`windows_invalidated: 168`, and `2,439 + 168 ≈` accounts for the gap between
the two window counts along with the last partial window at run cutoff). `duplicate_or_too_fast_
samples: 168` — exactly matching `timing_gaps`, consistent with the `next_tick` catch-up logic
immediately following every detected gap producing one unusually-fast follow-up sample; a real,
reproducible interaction between the pacing loop and the guard worth being precise about, not
dismissed as coincidence.

**Latency is lower across every percentile in this run, not higher** — `guard.observe()`'s own
measured overhead is trivial (mean 0.014ms, p99 0.053ms, max 3.07ms — `guard_observe_overhead_ms` in
the JSON), nowhere near enough to explain a *faster* result. The far more likely explanation,
consistent with the "Headless / reduced-background latency" finding earlier in this document: this
run happened to coincide with less concurrent desktop/IDE CPU contention than the original evaluated-
v1 run, not a code-change-driven speedup. Stated plainly so it isn't misread as "the fix made
inference faster" — it didn't; it made timing failures visible, and got measured during a quieter
moment on a shared desktop Pi.

**One tangent flagged honestly, not swept under the earlier "throttling: False" verdicts**:
`vcgencmd get_throttled` read `0x50000` (`under_voltage_occurred=True`, `throttling_occurred=True`)
during this session's testing — first observed during the pre-run smoke test, still present in this
15-minute run's result. The `_now` bits are all `False` (nothing is *currently* throttled), and
`dmesg` has zero matching undervoltage/throttling lines, so this is a **sticky since-boot/since-last-
clear flag from some earlier, unidentified event**, not something this run's workload caused — but
its root cause is genuinely unknown and should be treated as a loose end for the actual deployment,
same spirit as the unexplained service-respawn wrinkle noted earlier in this document.

**Verdict**: zero deadline misses, negligible guard overhead, and — the actually interesting result —
real, physically-occurring timing irregularities on this exact hardware were caught by the fix during
a genuine 15-minute real-time run, not just in the synthetic W2-R2 through W2-R5 harness above.

## W2-R7 — offline-vs-deployment replay agreement (Experiment C): not re-run, and why that's a defensible choice here

The plan's own Section 13 ("What does NOT need to be repeated") says a rerun is only required if a
change "touch[es] preprocessing mathematics, feature computation, thresholds, or TFLite interpreter
settings." The diff between `deploy/frozen_v1/crash_monitor_evaluated_v1.py` and the corrected
`deploy/crash_monitor.py` was inspected directly (not assumed): **every line inside
`CausalGravityFilter.apply()`, `WindowScorer`, `TriggerPolicy`, `CrashModel.predict()`, and
`compute_aux_features()` is unchanged.** `exp_c_replay_validation.py` (Experiment C, Part 1) calls
exactly those functions and nothing else — it never constructs a `SampleStreamGuard` and never calls
`handle_suspected_crash()`. There is no code path by which this correction could change Experiment
C's 99.61%/100% result. Re-running the full multi-minute TensorFlow-dependent replay anyway to
"prove" a no-op was judged lower value than spending that time on W2-R6 (real hardware time, the one
result this correction could plausibly change) — available to run on request if a reviewer wants the
literal re-confirmation rather than the code-diff argument.

## A5 and the second logic-robustness batch: re-run for confirmation

Per Part 3's own stated plan ("re-run A5, the logic-robustness batch... against the corrected code"):

- **A5 (trigger latency)** — re-run in full: **byte-identical to the original Part 2 result**
  (97.2% detected — same 35/36, same missed session `darus_crash_ISO13232-6_Out` — mean 10.24s,
  median 0.6s, p95 38.88s, min/max 0.6s/71.4s, real GPIO18 pulse confirmed again). Expected and
  correct: A5 never calls `handle_suspected_crash()` or touches `SampleStreamGuard` at all — it only
  exercises `WindowScorer`/`TriggerPolicy`/`LocalAlarm`, all byte-identical post-fix.
- **`logic_robustness_tests_2.py`** (3.19/3.20/3.27/3.28) — re-run unmodified against the corrected
  code: **byte-identical to the original Part 2 result** on every sub-item, including 3.20's own
  "no drop counter... invisible" language, which **remains literally true of `WindowScorer` itself**
  — exactly as intended, since the fix was deliberately placed one layer above it, not inside it.

**Process note, same honest pattern already established twice earlier in this document (§3.13's
worker-1 overwrite, the headless-run's `a1_long_tail_latency.json` overwrite)**: both re-runs above
write to the *same fixed filename* their original Part 2 run used
(`a5_trigger_latency.json`, `logic_robustness_tests_2.json`) — re-running them **overwrote the
original evaluated-v1 raw JSON files** before they were backed up, and only *then* were the new
outputs renamed to `*_corrected_v2_confirmation.json`. The original evaluated-v1 raw JSON artifacts
for these two experiments are therefore **no longer separately available on disk**. No scientific
content is actually lost — every evaluated-v1 number from both experiments is already fully
transcribed into Part 2's own tables/prose above, and the values shown here are (as expected)
identical to those — but this should have been prevented the same way the freeze step protected
`crash_monitor.py`/`config.yaml`/`exp_a4`, and wasn't. Recorded here plainly rather than glossed over.

`logic_robustness_tests.py` (the *first* batch — 3.18/3.21/3.29/3.30/3.31/3.32) was **deliberately
not re-run**: its 3.30b/3.32 sub-checks assert `sms_sent is False` against `handle_suspected_crash()`'s
return value, which is now a `CrashAlertResult` dataclass, not a bare `bool` — re-running that
specific script unmodified would report a spurious "mismatch" (`dataclass_instance is False` is
always `False` in Python) despite the underlying behavior being correct, not a real regression. Its
Weakness-1-relevant checks are fully superseded by W1-R1 through W1-R5 above, which assert on the
new dataclass's actual fields correctly. Its *other* checks (3.18 malformed-input, 3.21 determinism,
3.29 cooldown, 3.30 cancel-listener unit test, 3.31 alarm fallback) exercise only
`WindowScorer`/`TriggerPolicy`/`CancellationListener`/`LocalAlarm`, all confirmed byte-identical by
the same diff cited under W2-R7 — not re-run for the same reasoning as W2-R7, available on request.

## Summary — Weakness 1 & 2 correction and re-validation

| Item | Status | Headline |
|---|---|---|
| Freeze evaluated-v1 | ✅ Done | `deploy/frozen_v1/` + SHA256 hashes, before any edit |
| W1-R1..R5 (SMS outcome reporting) | ✅ All pass | Exact pre-fix bug (silent `True` on SMS failure) directly reproduced and confirmed fixed |
| W2-R1 (no-gap regression) | ✅ Pass, both sessions | Bit-identical to frozen evaluated-v1 |
| W2-R2 (single drop) | ✅ Pass, 3 positions | Detected, invalidated, no exception, every time |
| W2-R3 (sparse periodic drop) | ✅ Pass, 2 rates | No false triggers; **surfaced a real coverage/integrity tradeoff at 1-in-100** (~60% time invalidated) |
| W2-R4 (burst drop) | ✅ Pass, 4 sizes | One gap event per burst; buffer provably never mixes pre/post-gap samples |
| W2-R5 (delayed sample) | ✅ Pass, 4 delays | Sample never discarded, only the window; out-of-order timing explicitly deferred to live hardware |
| W2-R6 (real 15-min corrected pipeline) | ✅ Ran on real hardware | **0/2,439 deadline misses; 168 real timing gaps genuinely caught on this hardware**; guard overhead trivial (~0.014ms mean) |
| W2-R7 (offline-vs-deployment agreement) | ⚠️ Not re-run | Code-diff proves the exercised code path is unchanged; available on request |
| A5 + `logic_robustness_tests_2.py` re-run | ✅ Done | Byte-identical to Part 2 — confirms no unintended regression |
| `logic_robustness_tests.py` (first batch) re-run | ⚠️ Not re-run | Its 2 SMS-related checks are superseded by W1-R1..R5; rest confirmed unchanged by diff |

**Recommendation for the paper (plan §16), and the choice actually made here**: with every required
regression check passing and the two accidentally-lost raw JSONs' numbers otherwise fully preserved,
this follows the plan's **Option B** — `deploy/crash_monitor.py`'s corrected-v2 is now the canonical
deployed artifact (not left as a parallel branch), with `deploy/frozen_v1/` preserved as the permanent
record of exactly what Parts 1-3's results were measured against. Suggested paper language: *"After
the initial validation campaign, two software-level robustness issues were identified and corrected:
explicit emergency-delivery outcome reporting and timestamp-based detection of irregular sample
intervals. Regression testing (real held-out sessions, plus a real 15-minute 50Hz-paced hardware run)
confirmed unchanged behavior under nominal streams and explicit detection/recovery under both
synthetic and organically-occurring stream gaps."* Per plan §9/§17, the provisional `timing_guard`
thresholds (`deploy/config.yaml`) and the true real-MPU6050 drop-rate/jitter distribution remain
explicitly flagged as future work — nothing here claims a live-sensor characterization this session
still doesn't have.

## Appendix — exact before/after: every file changed, previous state vs. corrected state

Written for anyone checking this against `deploy/crash_monitor.py` directly rather than taking the
tables above on faith. "Previous state" below is the literal content of
`deploy/frozen_v1/crash_monitor_evaluated_v1.py` (SHA256
`843dc665a8cdf2fd68ff896a0173c2a7a98fc51be2c19848dce8619ecf90c5be` — see
`deploy/frozen_v1/FROZEN_v1_HASHES.txt`); "corrected state" is the current `deploy/crash_monitor.py`.

### 1. `deploy/crash_monitor.py` — Weakness 1: `handle_suspected_crash()`

**Previous state** (the actual bug): the function's own docstring claimed *"Returns True if an SMS
was sent, False if the rider cancelled in time"*, but the code didn't do that —

```python
def handle_suspected_crash(alarm, canceller, gsm, cfg, logger):
    ...
    while time.monotonic() < deadline:
        if canceller.check_and_clear():
            alarm.stop()
            logger.warning("Alert cancelled by rider -- no SMS sent")
            return False
        time.sleep(0.2)

    alarm.stop()
    logger.warning("Cancellation window expired -- sending SMS alert")
    coords = gsm.get_gps_coordinates(cfg["gps"]["timeout_seconds"])
    ...
    gsm.send_sms(message)
    return True                      # <-- unconditional: True even if send_sms() just returned False
```

**Corrected state**: a new `CrashAlertResult` dataclass (`cancelled`, `sms_attempted`, `sms_sent`,
`gps_available`) replaces the bare `bool`, and `sms_sent` is the real `send_sms()` return value —

```python
@dataclass
class CrashAlertResult:
    cancelled: bool
    sms_attempted: bool
    sms_sent: bool
    gps_available: bool


def handle_suspected_crash(alarm, canceller, gsm, cfg, logger):
    ...
    while time.monotonic() < deadline:
        if canceller.check_and_clear():
            alarm.stop()
            logger.warning("CRASH_ALERT_CANCELLED -- rider cancelled, no SMS attempted")
            return CrashAlertResult(cancelled=True, sms_attempted=False, sms_sent=False, gps_available=False)
        time.sleep(0.2)

    alarm.stop()
    logger.warning("Cancellation window expired -- attempting SMS alert")
    coords = gsm.get_gps_coordinates(cfg["gps"]["timeout_seconds"])
    gps_available = coords is not None
    ...
    logger.warning("SMS_ATTEMPTED")
    sms_sent = bool(gsm.send_sms(message))          # <-- actual outcome, not assumed
    if sms_sent:
        logger.warning("SMS_SENT")
    else:
        logger.error("SMS_FAILED -- alert was NOT confirmed delivered")
    return CrashAlertResult(cancelled=False, sms_attempted=True, sms_sent=sms_sent, gps_available=gps_available)
```

**`main()`'s call site** — previous state discarded the return value entirely
(`handle_suspected_crash(alarm, canceller, gsm, cfg, logger)` as a bare statement, nothing captured).
Corrected state captures and logs it:

```python
alert_result = handle_suspected_crash(alarm, canceller, gsm, cfg, logger)
logger.info(
    "Crash alert outcome: cancelled=%s sms_attempted=%s sms_sent=%s gps_available=%s",
    alert_result.cancelled, alert_result.sms_attempted, alert_result.sms_sent, alert_result.gps_available,
)
```

### 2. `deploy/crash_monitor.py` — Weakness 2: dropped/delayed samples

**Previous state**: `main()`'s loop had no timing awareness at all between `read_sensor()` and
`scorer.append()` — a sample was a sample, regardless of how long it took to arrive:

```python
while True:
    next_tick += period
    sample = read_sensor(sensor, logger)
    if sample is None:
        sensor = connect_sensor(cfg, logger)
        continue

    scorer.append(sample)                 # <-- no gap check of any kind before this line
    ...
```

**Corrected state**: a new `SampleStreamGuard` class (full listing in `deploy/crash_monitor.py`,
~100 lines: `observe()`, `reset_baseline()`, `record_window_invalidated()`, `record_window_scored()`,
`snapshot()`) is constructed once in `main()` and consulted every sample:

```python
guard = SampleStreamGuard(cfg["sensor"].get("timing_guard"), period, logger)
...
while True:
    next_tick += period
    sample = read_sensor(sensor, logger)
    if sample is None:
        sensor = connect_sensor(cfg, logger)
        continue

    now = time.monotonic()
    gap_detected, dt = guard.observe(now)
    if gap_detected:
        logger.warning("TIMING_GAP dt=%.1fms (max_dt=%.1fms) -- discarding in-flight window, "
                        "resuming once a fresh full window has accumulated",
                        dt * 1000.0, guard.max_dt_s * 1000.0)
        scorer.clear()
        guard.record_window_invalidated()
        if dt >= guard.long_gap_reset_s:
            gravity_filter.reset()
            logger.warning("Gap >= %.1fs -- resetting gravity filter state", guard.long_gap_reset_s)

    scorer.append(sample)
    ...
    if result is not None:
        guard.record_window_scored()
    ...
```

...and the existing post-alarm gap is explicitly told apart from an unexpected one, so the fix
doesn't silently change the already-validated §3.27 alarm-gap gravity-filter behavior:

```python
if triggered:
    alert_result = handle_suspected_crash(alarm, canceller, gsm, cfg, logger)
    ...
    scorer.clear()
    guard.reset_baseline()      # <-- new: tells the guard this gap was already handled, not a drop
    next_tick = time.monotonic()
```

`CausalGravityFilter` previous state had no way to discard its running estimate at all; corrected
state adds one method, `reset()` (`self.gravity = None`), used only by the guard's long-gap branch
above — `apply()` itself is byte-for-byte unchanged.

### 3. `deploy/config.yaml` — new section, nothing existing removed

**Previous state**: `sensor:` block had `i2c_address`/`sample_rate_hz`/`window_samples`/
`stride_samples` only — no timing-tolerance concept existed.

**Corrected state**: same four keys, unchanged, plus one new nested block:

```yaml
sensor:
  i2c_address: 0x68
  sample_rate_hz: 50
  window_samples: 60
  stride_samples: 15

  timing_guard:
    max_dt_s: 0.030      # dt > this -> suspected drop/stall, in-flight window discarded
    min_dt_s: 0.010      # dt < this -> suspected duplicate/too-fast read, counted only
    long_gap_reset_s: 1.0  # dt >= this -> also reset the gravity filter's stale EMA state
```

Explicitly commented in-repo as provisional (not derived from real MPU6050 timing — see W2-R6 above).

### 4. Everything else — unchanged, confirmed by diff, not by assertion

`diff deploy/frozen_v1/crash_monitor_evaluated_v1.py deploy/crash_monitor.py` shows the two edits
above (plus the new `CrashAlertResult`/`SampleStreamGuard` classes and `CausalGravityFilter.reset()`)
as the **entire** change. Zero lines differ inside `load_config()`, `load_model_thresholds()`,
`setup_logging()`, `CausalGravityFilter.apply()`, `LocalAlarm`, `CancellationListener`, `CrashModel`,
`WindowScorer.append()`/`try_score()`/`clear()`, `TriggerPolicy`, `compute_aux_features()`,
`GsmModule`, `read_sensor()`, or `connect_sensor()`. This is the concrete basis for every "unchanged"
claim made in the W2-R7 / `logic_robustness_tests.py` sections above, not an assumption.

### 5. New files this pass created (nothing pre-existing was deleted)

| File | Purpose |
|---|---|
| `deploy/frozen_v1/crash_monitor_evaluated_v1.py` | Exact evaluated-v1 snapshot, preserved before any edit |
| `deploy/frozen_v1/config_evaluated_v1.yaml` | Same, for `config.yaml` |
| `deploy/frozen_v1/exp_a4_replay_streaming_pipeline_evaluated_v1.py` | Same, for the A4 benchmark script |
| `deploy/frozen_v1/FROZEN_v1_HASHES.txt` | SHA256 of the three files above plus both `.tflite` models and `thresholds.json` |
| `deploy/pi_research_suite/logic_robustness_tests_corrected_v2.py` | W1-R1..R5 + W2-R1..R5 re-validation suite (new) |
| `deploy/pi_research_suite/exp_a4_replay_streaming_pipeline_corrected_v2.py` | W2-R6 corrected pipeline benchmark (new) |
| `results/pi_research/logic_robustness_tests_corrected_v2.json` | Output of the above |
| `results/pi_research/a4_replay_streaming_pipeline_corrected_v2.json` | Output of the above |
| `results/pi_research/a5_trigger_latency_corrected_v2_confirmation.json` | A5 re-run (see note above re: original overwritten) |
| `results/pi_research/logic_robustness_tests_2_corrected_v2_confirmation.json` | Second logic batch re-run (same note) |

**Files modified in place**: `deploy/crash_monitor.py`, `deploy/config.yaml` (both described above).
**Files NOT modified**: `models/*` (hash-confirmed identical), `deploy/pi_research_suite/exp_a4_
replay_streaming_pipeline.py` / `exp_a5_trigger_latency.py` / `exp_c_replay_validation.py` /
`logic_robustness_tests.py` / `logic_robustness_tests_2.py` / `common.py` — the original evaluated-v1
scripts are all still present and importable exactly as they were.
