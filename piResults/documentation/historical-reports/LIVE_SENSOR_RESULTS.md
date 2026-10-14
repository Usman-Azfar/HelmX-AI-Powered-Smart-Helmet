# MPU6050 Live-Sensor Results — HelmX Crash Detection, real Raspberry Pi 4 hardware

**Purpose:** every MPU-dependent test from `piResults/HelmX_Paper1_FINAL_Pi_Data_Collection_Checklist.md`
Section 4 (items 4.1–4.8), plus the matching W2-LIVE-1/2/3 items from
`HelmX_Paper1_Deployment_Weaknesses_Correction_Revalidation_Plan.md` Section 12. All of these were
previously **blocked** — `pin_connections.md` and `piResults/ResultsFromPi.md` (Parts 1–4) document an
exhaustive hardware diagnosis that found the MPU6050 not responding on I2C1 (`errno=121 EREMOTEIO` on
both possible addresses, everything else on the Pi's side checked out clean). Every non-MPU experiment
in that checklist is already complete — this file covers only what was blocked, now that the sensor is
detected.

**What changed:** `i2cdetect -y 1` now shows a device at `0x68` (this session, 2026-09-04) — the
physical fault (most likely power/GND per `pin_connections.md`'s ranked diagnosis) has been fixed since
that document was written. Documented as observed, not re-diagnosed further.

Same convention as `ResultsFromPi.md`: nothing here is estimated — a field is filled in only if a real
run on this hardware produced it; otherwise it's marked unavailable and why. Each experiment below is
documented immediately after it finished running, in the order run.

## Model understanding (context for interpreting every result below)

HelmX's crash detector is a **hybrid autoencoder + classifier** sharing one Conv1D encoder
(`src/model.py: build_model`), deployed on the Pi as an INT8 TFLite model
(`models/helmx_crash_model_int8.tflite`):

- Input: a `(60, 6)` window — 60 timesteps (1.2s at 50Hz) × 6 channels (ax, ay, az, gx, gy, gz) — plus 7
  hand-engineered aux stats (mean/std/peak accel magnitude, mean/std/peak gyro magnitude, peak jerk).
- Real-time path (`deploy/crash_monitor.py: main()`): MPU6050 read at 50Hz → `SampleStreamGuard`
  (timestamp-based gap/drop detector, added in the corrected-v2 revision — see
  `HelmX_Paper1_Deployment_Weaknesses_Correction_Revalidation_Plan.md`) → `CausalGravityFilter` (causal
  EMA approximation of the offline zero-phase Butterworth filter) → `WindowScorer` (60-sample window,
  15-sample stride, 7 aux features, INT8 inference) → `TriggerPolicy` (crash_prob > 0.9892 OR
  recon_error > 10.879, sustained for 3 consecutive windows, 60s cooldown) → `LocalAlarm` (real GPIO18
  pulse) → 30s voice-cancellable countdown → GSM SMS+GPS if uncancelled.
- This is the **corrected-v2** code (`deploy/crash_monitor.py`, `deploy/frozen_v1/` holds the pre-fix
  version) — includes `SampleStreamGuard` and `CrashAlertResult`, both added and regression-tested
  against synthetic/replayed data in `ResultsFromPi.md` Part 4, but never yet run against a real,
  physically connected sensor until this file.
- Deployed stride budget: 300ms per window (15-sample stride / 50Hz) — the number every latency result
  below should be compared against.

Full architecture/design rationale: `system_understanding.md`. Hardware diagnosis history:
`pin_connections.md`. Every non-MPU Pi experiment: `piResults/ResultsFromPi.md`.

## Environment (unchanged from `ResultsFromPi.md`)

Raspberry Pi 4 Model B Rev 1.5, 7.64GB RAM, Raspberry Pi OS / Debian 12 bookworm, aarch64. All commands
below run via `.pi_research_venv/bin/python` (the same venv used throughout `ResultsFromPi.md`, with
`--system-site-packages` so it inherits `mpu6050-raspberrypi`, `gpiozero`, etc.).

---

## Update — 1.5-hour soak, periodic documentation, README update

Per explicit instruction from the user: the ≥1h soak test (4.5/W2-LIVE-3) below is run for **1.5
hours**, documented **periodically during the run** (not only at the end), and `README.md` is updated
once every MPU-dependent item in this file is complete.

---

## 4.1 — Verify physical I2C detection — ✅ RAN — **MPU6050 now detected at 0x68**

```
i2cdetect -y 1
```

| Address | 0x00–0x67 | **0x68** | 0x69–0x7F |
|---|---|---|---|
| Result | all `--` (no response) | **`68`** | all `--` |

`ls /dev/i2c*` → `/dev/i2c-1` present, same device node used throughout the earlier (blocked) diagnosis.
This reverses the finding in `pin_connections.md` (`i2cdetect -y 1` there showed every address `--`,
with a full `EREMOTEIO`-based diagnosis narrowing the fault to physical power/GND/wiring between the
Pi's header and the MPU6050 board). The Pi-side configuration was never the problem (already confirmed
clean in that document: `dtparam=i2c_arm=on`, correct pin mux, correct permissions, no kernel I2C
errors) — nothing on the software side changed here; the sensor is simply now electrically present and
ACKing at its default address, consistent with "most likely: MPU6050 had no power / no GND" from that
document's ranked diagnosis.

**Immediate plausibility check** (`mpu6050-raspberrypi` library, 5 reads @ 5Hz, sensor stationary on the
desk at an angle, not flat):

| Read | Accel X | Accel Y | Accel Z | Gyro X | Gyro Y | Gyro Z |
|---|---|---|---|---|---|---|
| 1 | -3.953 | -8.734 | -2.274 | 0.374 | 1.985 | 0.076 |
| 2 | -3.898 | -8.691 | -2.267 | -0.076 | 1.763 | -0.534 |
| 3 | -3.936 | -8.736 | -2.286 | -0.252 | 1.847 | 0.672 |
| 4 | -3.974 | -8.715 | -2.222 | -0.489 | 2.053 | 1.176 |
| 5 | -3.936 | -8.727 | -2.263 | -0.573 | 2.588 | 1.397 |

Accel magnitude ≈ `sqrt(3.94² + 8.72² + 2.26²)` ≈ **9.84 m/s²** — matches Earth gravity (9.81 m/s²)
closely, consistent with a stationary sensor resting at a tilted (not flat) angle, splitting gravity
across all three axes rather than loading entirely onto Z. Gyro values are small (< 2.6 °/s) and noisy
around a nonzero bias, exactly the expected MEMS-gyro signature at rest (stationary "zero-rate" bias
plus noise, not literal zero). **Verdict: real, plausible physical data — this is a genuine, correctly
wired MPU6050, not a floating/garbage response.**

---

## 4.2 / W2-LIVE-1 — Live raw sensor validation + sample-interval characterization — ✅ RAN on real hardware (12 minutes)

```
.pi_research_venv/bin/python deploy/pi_research_suite/exp_w2_live1_sample_interval.py --duration-min 12
```

Reads the real MPU6050 **back-to-back, unpaced** (no artificial 50Hz throttling) for 12 minutes,
timestamping every read — this measures the sensor + `mpu6050-raspberrypi` library's own achievable
rate and I2C jitter, per the plan's literal W2-LIVE-1 spec ("timestamp every real MPU6050 read"), not
the deployed 50Hz-paced loop's timing (that's covered separately below by 4.4/W2-LIVE-2's `SampleStreamGuard`
telemetry). Full results: `results/pi_research/w2_live1_sample_interval.json`.

| Metric | Value |
|---|---|
| Duration | 12.0 min (720s) |
| Total reads | **108,892** |
| **Achieved rate (unpaced, back-to-back)** | **151.24 Hz** — ~3x the deployed 50Hz target, confirming the sensor/bus has comfortable headroom above what the deployed loop actually asks for |
| I2C read failures | **0** |
| Interval mean | 6.61 ms |
| Interval p50 | 5.91 ms |
| Interval p95 | 9.46 ms |
| Interval p99 | 12.41 ms |
| **Interval max** | **130.53 ms** |
| Gaps (>3x mean, i.e. >19.83ms) | 121 |
| Estimated dropped-equivalent samples over those gaps | 675 |
| Accel magnitude (stationary, first 2000 reads) | mean **9.826** (Earth gravity = 9.81 — matches closely) |

**Verdict — real hardware, zero I2C failures, occasional but bounded jitter.** Zero read exceptions
across 108,892 reads is a strong reliability signal on its own. The jitter distribution is right-skewed
(p50/mean both ~6ms, but p99 more than doubles to 12.4ms, and the single worst gap hit 130.5ms) —
consistent with the same kind of OS-scheduler-preemption tail this Pi showed throughout the CPU-only
benchmarks in `ResultsFromPi.md` (this Pi runs a full desktop session throughout every test in this
project), not evidence of an unstable I2C bus.

**What this means for the deployed `SampleStreamGuard` threshold** (`deploy/config.yaml:
sensor.timing_guard`, currently `max_dt_s=0.030` / 30ms, explicitly marked PROVISIONAL pending this
exact experiment): the deployed loop is **paced** at 50Hz (20ms nominal period, dominated by
`time.sleep`, not raw I2C latency), so this unpaced-rate number isn't a direct drop-in replacement for
that threshold — but it's informative context: even this experiment's single worst-case I2C stall
(130.5ms) is well above the current 30ms guard threshold and would correctly be flagged as a gap, and
the p99 (12.4ms) sits comfortably below it. The provisional 30ms threshold is not contradicted by this
data. The guard's actual paced-loop dt distribution is measured directly next, in 4.4/W2-LIVE-2.

---

## 4.3 / A2 — Active CPU/RAM under real live sensor operation — ✅ RAN on real hardware (15 minutes) — **previously blocked, now unblocked**

```
.pi_research_venv/bin/python deploy/pi_research_suite/exp_a2_resource_usage.py --duration-min 15
```

This is the **exact same script** `ResultsFromPi.md` Part 1 ran and found blocked: it launches the
real `deploy/crash_monitor.py` as a subprocess and monitors it. Previously, `connect_sensor()` retried
`mpu6050(0x68)` forever and the process never reached real inference — only the idle-retry-loop
resource footprint could be measured (preserved at
`results/pi_research/a2_resource_usage_idle_retry_blocked_v1.json` before this run overwrote
`a2_resource_usage.json`). This time the sensor connected immediately and `crash_monitor.py` ran its
real live loop for the full 15 minutes. Full results: `results/pi_research/a2_resource_usage.json`;
`logs/crash_monitor.log` has the real per-window/telemetry log lines from this exact run.

| Metric (897 samples @ 1s, real live sensor active) | This run (live) | Previous (idle retry-loop, blocked) |
|---|---|---|
| Process CPU | mean **2.72%**, p95 4.0%, max 8.0% | mean 0.175%, max 1.0% |
| Process RSS | flat **~47.9 MB** (min 47.64, max 47.92) | flat 45.98 MB |
| System CPU | mean 10.9%, p95 25.2%, max 70.9% | mean 27.8%, max 89.4% |
| System RAM used | ~2.10 GB / 7.64 GB | ~2.9 GB |
| Swap used | 0 MB | 0 MB |
| CPU temperature | mean **47.9°C**, p95 49.1°C, max 51.1°C | mean 55.7°C, max 58.4°C |
| Memory-leak verdict | **stable plateau** (slope ≈ +0.0065 MB/min) | stable plateau |

**Verdict: this is the real "sustained active inference" number the guide's schema always wanted, and
it was never measurable before now.** Real inference raises process CPU by roughly 15x over the idle
retry-loop baseline (0.175% → 2.72%) but is still trivial in absolute terms — a few percent of one
core. RSS is flat and stable (no leak) at a footprint (~47.9MB) barely above the idle-retry baseline
(~46.0MB), confirming the real per-window inference/windowing/preprocessing path adds negligible steady-
state memory. CPU temperature during this run was actually *lower* than the idle-retry baseline
(47.9°C vs. 55.7°C mean) — not a contradiction, just ambient/desktop-load variance between sessions
(consistent with `ResultsFromPi.md`'s repeated finding that this Pi's thermal baseline is ambient-
dominated, not compute-dominated; see its §3.49).

**A genuine, real finding surfaced by this run, not visible in any earlier (non-live) experiment**: the
corrected `SampleStreamGuard` **actually fired for real**, repeatedly, under real live sensor
conditions — something no synthetic/replay test could produce, since replay/A4 loops never have real
I2C read latency to be delayed by. Cumulative telemetry at the last logged checkpoint (`stream_telemetry`
in `logs/crash_monitor.log`, ~14.2 min into the run):

| Field | Value |
|---|---|
| Samples received | 44,878 |
| **Timing gaps flagged** | **113** over the full ~15 min run (~1 every 8s) |
| Suspected dropped samples (estimated) | 210 |
| Duplicate/too-fast reads | 110 |
| **Windows invalidated** (discarded due to a gap) | 112 |
| Windows scored | 2,620 |
| Sample-interval mean / p50 | 20.06ms / 19.99ms (very close to the ideal 20ms period — the paced loop tracks its target well on average) |
| Sample-interval p95 / p99 | 22.17ms / 23.20ms |
| **Max sample interval** | **117.8ms** |
| Real sensor I2C read failures (`Sensor read failed` in log) | **0** |

**Interpretation**: every one of the 113 flagged gaps was a **timing** anomaly (the loop's own real-
time pacing occasionally slipping — same OS-scheduler-preemption pattern documented throughout
`ResultsFromPi.md`, e.g. its A1-repeat 286.8ms outlier and 3.5's long-tail characterization — not a
raw I2C communication failure (zero `OSError`s from `read_sensor()` the entire run). This is exactly
the scenario `SampleStreamGuard` was built for (per
`HelmX_Paper1_Deployment_Weaknesses_Correction_Revalidation_Plan.md`): it correctly detected 112/113 of
these real timing slips and discarded the in-flight window rather than silently scoring a window that
spans a real gap — **the corrected-v2 fix is not just regression-tested against synthetic drops
anymore, it has now caught real ones, live, on this hardware.** ~4.3% of generated windows were
invalidated this way (112 of 2,620+112≈2,732 candidate windows) — a real, now-quantified cost of
running this Pi as an active desktop machine (VS Code, IDE) concurrently with the sensor loop; a
headless deployment image would very likely show a lower rate (consistent with `ResultsFromPi.md`'s
"headless vs. loaded" A1 comparison, where removing desktop/background load cut max latency 40x).

---

## 4.4 / W2-LIVE-2 — Live corrected end-to-end pipeline — ✅ RAN on real hardware (12 minutes)

```
.pi_research_venv/bin/python deploy/pi_research_suite/exp_w2_live2_pipeline.py --duration-min 12
```

The plan's exact ask: physical MPU → `SampleStreamGuard` → causal gravity filter → windowing → aux
features → INT8 inference → `TriggerPolicy`, using the real `deploy/crash_monitor.py` classes, driven
by a real live sensor at the real 50Hz-paced cadence (not a replay — this is the live counterpart to
`ResultsFromPi.md` 3.1's 15-minute *replay*-paced result). Sensor sat on the desk, occasionally
handled, during this run. Full results: `results/pi_research/w2_live2_pipeline.json`.

| Metric | Value |
|---|---|
| Duration | 12.0 min (as requested) |
| Input samples processed | **35,800** |
| Windows generated | **1,975** |
| Sensor read failures | **0** |
| Reconnects | **0** |
| Exceptions | **0** |
| **Per-window complete pipeline latency** — mean | 1.78ms |
| — median | 1.70ms |
| — p95 | 2.13ms |
| — p99 | 3.19ms |
| — max | 8.72ms |
| **Deadline misses (>300ms stride budget)** | **0 / 1,975 (0.0%)** |
| Achieved throughput | 2.74 windows/sec (target 3.33/s — running a touch behind target, entirely explained by the timing gaps below, each of which discards an in-flight window and restarts accumulation) |
| Triggers fired | 0 (expected — no crash-like motion during this run; the trigger path itself is exercised separately by 4.7 below) |
| Process CPU% | mean 2.34%, max 5.0% |
| System CPU% | mean 7.0%, max 50.3% (desktop/IDE background load, not this pipeline — same pattern throughout this whole project) |
| Process RSS | ~48.6MB (consistent with 4.3's ~47.9MB — this is the real steady-state live footprint) |
| CPU frequency | pinned at ~1800.44MHz (`force_turbo=1`, confirmed again) |
| Temperature | mean 47.5°C, max 50.1°C |
| **Thermal throttling** | **False** — `get_throttled=0x0` |

**`SampleStreamGuard` telemetry (the real paced-loop dt distribution this experiment exists to
measure, distinct from 4.2's unpaced back-to-back rate)**:

| Field | Value |
|---|---|
| Samples received | 35,800 |
| Timing gaps flagged | 123 (~1 every 5.9s) |
| Suspected dropped samples (estimated) | 296 |
| Duplicate/too-fast reads | 123 |
| Windows invalidated | 123 |
| Windows scored | 1,975 |
| Sample-interval mean / p50 | 20.11ms / 19.997ms |
| Sample-interval p95 / p99 | 21.70ms / 26.41ms |
| **Max sample interval** | **124.6ms** |
| `guard.observe()` overhead per call | mean 0.012ms, p99 0.048ms, max 1.33ms — confirms the guard itself adds negligible cost, as the correction plan predicted |

**Verdict: the complete real software path — not just inference, the whole physical-sensor-to-decision
chain — meets its real-time deadline with enormous headroom on real hardware.** Zero deadline misses
across 1,975 real windows, p99 latency (3.19ms) ~94x inside the 300ms budget, even the single worst
window (8.72ms) ~34x inside budget. This closely reproduces 4.3's independent finding of ~1 timing gap
every 6-8 seconds under this Pi's real desktop-session load, again with **zero raw I2C read failures**
— every flagged gap is a scheduling-timing anomaly the guard correctly caught and handled (discarded
in-flight window, no crash, no exception), not a sensor communication fault. Two independent live runs
(4.3 and this one) now agree closely on both the gap rate and its cause, which is stronger evidence
than either alone.

---

## 4.7 — Safe live trigger-path test (live sensor loop → scorer → TriggerPolicy → LocalAlarm) — ✅ RAN on real hardware

```
.pi_research_venv/bin/python deploy/pi_research_suite/exp_4_7_live_trigger_path.py
```

Per the checklist's own allowance for this item ("replay injection is acceptable if physical
triggering would be unsafe"): rather than a physical impact test, a real recorded DaRUS crash session
was injected into the **same live `WindowScorer`/`TriggerPolicy` objects** that had just processed real
live MPU6050 samples, safely exercising the full trigger path without a destructive test. Full results:
`results/pi_research/4_7_live_trigger_path.json`.

**Stage 1 — 3s real live baseline** (sensor sitting quietly on the desk): 4 real live windows scored, 0
anomalous, 0 triggered — matches expectation exactly (no crash-like motion, no false trigger).

**Stage 2 — safe replay injection**: `darus_crash_Iso_312_2_Out` (a real DaRUS collision-physics
session, label=1, 150 rows — the same session `ResultsFromPi.md`'s Experiment C found 100% window
agreement on) fed through the identical live scorer/policy instances (continuing from the real live
gravity-filter state established in Stage 1, not a fresh one):

| Metric | Value |
|---|---|
| Windows scored | 10 |
| Anomalous windows | 5 |
| **Trigger fired** | **Yes** — at injected sample index 111 |
| crash_prob at trigger | **0.9961** (threshold 0.9892) |
| recon_error at trigger | **19.44** (threshold 10.88) — both signals agree here |
| **Real GPIO18 pulse fired** | **Yes** — `LocalAlarm.start()`/`stop()` genuinely acquired and toggled GPIO18 via `gpiozero` |

**Stage 3 — 3s more real live sensor samples after injection** (post `scorer.clear()`, the same call
`main()` makes after a real alarm countdown): 4 more windows scored, **0 sensor read errors** — the
live sensor path resumes cleanly after the injected crash and the alarm event, exactly as `main()`'s
own real recovery logic is designed to do.

**Verdict: the complete real trigger path is now confirmed working end-to-end on real hardware with a
real sensor in the loop** — live MPU6050 samples flow correctly into the real `WindowScorer`, a real
recorded crash signature correctly crosses both the classifier and reconstruction thresholds and fires
the 3-consecutive-window `TriggerPolicy` rule, a real GPIO18 pulse actually fires (not the log-only
degraded path), and the live sensor loop resumes cleanly afterward with zero errors. This closes the
gap `ResultsFromPi.md`'s A5 left open: A5 confirmed the trigger logic and GPIO path work using synthetic
timestamps and no live sensor at all; this experiment confirms the same path works with a real,
physically connected MPU6050 actually in the loop before and after the injected event.

---

## 4.6 — Physical movement smoke test — ✅ RAN on real hardware, real human handling (rerun 2026-09-05)

```
.pi_research_venv/bin/python -u deploy/pi_research_suite/exp_4_6_movement_smoke_test.py
```

The user physically handled the sensor through 5 labeled phases while this script recorded live
readings — genuinely non-destructive (no drops, no impacts), per the checklist's own scope for this
item. This is a **rerun** of the original 4.6 run (both runs used the same script/phases; this run's
numbers supersede the original for reporting purposes, though both showed the same qualitative
pattern and zero errors). The assistant announced each phase's instruction and duration to the user
in real time from the script's own unbuffered phase-start log lines as it ran. Full results:
`results/pi_research/4_6_movement_smoke_test.json`.

| Phase | Duration | Reads | I2C errors | Accel mag mean | Accel mag max | Gyro mag mean | Gyro mag max |
|---|---|---|---|---|---|---|---|
| Stationary baseline | 15s | 550 | 0 | 9.84 | 9.99 | 2.46 | 4.50 |
| Gentle rotation | 20s | 747 | 0 | 9.87 | 13.29 | 16.79 | 183.02 |
| Tilt | 20s | 749 | 0 | 10.03 | 11.13 | 34.62 | 112.90 |
| Shake | 20s | 755 | 0 | 10.00 | 10.96 | 19.52 | **151.04** |
| Non-crash bump | 20s | 746 | 0 | 9.99 | 10.81 | 14.60 | 108.16 |
| **Total I2C errors, all phases** | | | **0** | | | | |

**Verdict: every phase again produced physically plausible, internally consistent signal shapes, with
zero I2C read errors under real physical handling of the sensor.** Accel magnitude stays anchored near
gravity (9.8–10.0 mean) throughout every phase, exactly as physically expected for handling dominated
by orientation/angular motion rather than large linear accelerations. This rerun's peak gyro reading
(183.0) actually occurred during **gentle_rotation**, not shake or bump as in the original run — a
reminder that these are hand-performed, unscripted-amplitude motions, so which phase produces the
single highest instantaneous spike varies run to run; what stays consistent across both runs is the
qualitative shape (stationary lowest, all four motion phases clearly elevated, all in a broadly
similar 100–200 gyro-magnitude-max band) and, most importantly, **zero I2C errors and zero implausible
readings in either run**, across 3,547 total reads this time (3,586 in the original). Combined, the two
independent runs (different day, different exact hand motion) now show this result is repeatable, not
a one-off.

---

## 4.5 / W2-LIVE-3 — ≥1h live corrected soak — ✅ RAN on real hardware (90 minutes, restarted 2026-09-05)

```
.pi_research_venv/bin/python -u deploy/pi_research_suite/exp_w2_live3_soak.py --duration-min 90 --checkpoint-every-min 5
```

Same live pipeline as 4.4/W2-LIVE-2 (real MPU6050 → `SampleStreamGuard` → causal gravity filter →
windowing → aux features → INT8 inference → `TriggerPolicy`), run continuously for **90 minutes**
per the user's explicit choice (exceeding the plan's ≥1h minimum), with a checkpoint logged every 5
minutes. This section is updated periodically as the run progresses, per the user's request, then
finalized with the full report once it completes.

**Restart note:** the first attempt at this run (started 2026-09-04) was interrupted mid-run by an
unplanned computer shutdown/restart before its first checkpoint printed — no partial data or JSON
report was produced by that attempt (the script only writes `results/pi_research/w2_live3_soak.json`
at clean completion), so nothing from it is salvageable or reported. All items 4.1–4.4, 4.6, 4.7 above
were already complete and unaffected by the restart (verified against their existing result files
after reboot); the MPU6050 was reconfirmed present at `0x68` via `i2cdetect -y 1` before restarting
this test. Relaunched **2026-09-05 11:21:24 PKT**, `setsid`+`nohup`+unbuffered (`-u`), stdout to
`logs/w2_live3_soak_run2.out`, decoupled from the launching shell so it survives independently of this
session (though not a second power loss — the loop below will document the current 5-minute
checkpoint that the internal log has reached at each ~10-minute check-in). Expected completion
**~12:51 PKT**.

**4.8 (P1, "only if convenient") is being covered opportunistically by this same run**, rather than as
a separate experiment: this Pi already runs `helmx-ble.service` (real BLE server,
`/home/helmx/bluetooth.py`, `Restart=always`), `helmx_assistant.service` (voice-assistant, rhasspy)
and `mosquitto.service` (MQTT broker) continuously in the background regardless of this test, so the
soak's deadline-miss rate below is already measured with those lightweight helmet services active
concurrently — no DHT22/MQ135 bridge service exists on this system to include. This is called out
explicitly in 4.8's own section once the soak finishes.

### Checkpoints (updated live as the run progresses)

| Elapsed | Samples | Windows | Triggers | Reconnects | Exceptions | Max temp (°C) |
|---|---|---|---|---|---|---|
| 5.0 min | 14,882 | 721 | 0 | 0 | 0 | 53.0 |
| 10.0 min | 29,768 | 1,519 | 0 | 0 | 0 | 53.0 |
| 15.0 min | 44,647 | 2,293 | 0 | 0 | 0 | 53.0 |
| 20.0 min | 59,536 | 3,104 | 0 | 0 | 0 | 53.0 |
| 25.0 min | 74,418 | 3,906 | 0 | 0 | 0 | 53.0 |
| 30.0 min | 89,298 | 4,718 | 0 | 0 | 0 | 53.0 |
| 35.0 min | 104,155 | 5,486 | 0 | 0 | 0 | 53.0 |
| 40.0 min | 119,056 | 6,305 | 0 | 0 | 0 | 53.0 |
| 45.0 min | 133,941 | 7,144 | 0 | 0 | 0 | 53.0 |
| 50.0 min | 148,804 | 7,977 | 0 | 0 | 0 | 53.0 |
| 55.0 min | 163,665 | 8,819 | 0 | 0 | 0 | 53.0 |
| 60.0 min | 178,553 | 9,613 | 0 | 0 | 0 | 53.0 |
| 65.0 min | 193,439 | 10,433 | 0 | 0 | 0 | 53.0 |
| 70.0 min | 208,356 | 11,267 | 0 | 0 | 0 | 53.0 |
| 75.0 min | 223,241 | 12,088 | 0 | 0 | 0 | 53.0 |
| 80.0 min | 238,096 | 12,834 | 0 | 0 | 0 | 53.0 |
| 85.0 min | 252,982 | 13,663 | 0 | 0 | 0 | 53.0 |
| **90.0 min (final)** | **267,891** | **14,461** | **0** | **0** | **0** | **53.0** |

Full results: `results/pi_research/w2_live3_soak_90min.json`. Actual run duration: 90.0005 min (the
tiny excess is the loop's own `while time.monotonic() < deadline` overrun on its last iteration,
negligible). Note: the script always writes to the same `results/pi_research/w2_live3_soak.json`
path regardless of duration, and the follow-up 20-minute run below overwrote it — this file was
saved under its own name (`w2_live3_soak_90min.json`) afterward, reconstructed from the complete
stdout summary this run printed to `logs/w2_live3_soak_run2.out` (every field except the raw
per-second `raw_resource_samples` time series, which was not preserved; the aggregate resource
stats used throughout this section are unaffected).

### Final summary

| Metric | Value |
|---|---|
| Duration (requested / actual) | 90.0 min / 90.0005 min |
| Input samples processed | **267,891** |
| Windows generated | **14,461** |
| Triggers fired | 0 (expected — no crash-like motion; sensor sat quietly for the full 90 min) |
| Sensor read failures | **0** |
| Reconnects | **0** |
| Exceptions | **0** |
| **Per-window pipeline latency** — mean / median | 1.80ms / 1.68ms |
| — p95 / p99 | 2.21ms / 3.25ms |
| — max | 82.86ms |
| **Deadline misses (>300ms stride budget)** | **0 / 14,461 (0.0%)** |
| Achieved throughput | 2.68 windows/sec (target 3.33/s, same gap-driven shortfall pattern as 4.3/4.4) |
| Process CPU% | mean 2.35%, p95 3.9%, max 9.9% |
| System CPU% | mean 8.0%, p95 18.8%, max 94.2% (desktop/IDE background load) |
| Process RSS | mean 49.75MB, min 47.07MB, max 51.58MB |
| System RAM used | mean ~2.04GB / 7.64GB |
| Swap used | 0 MB throughout |
| CPU frequency | pinned ~1800.44MHz (`force_turbo=1`) |
| Temperature | mean 47.6°C, p95 49.1°C, **max 53.0°C** |
| **Thermal throttling** | **False** — `get_throttled=0x0`, no under-voltage/freq-cap ever flagged |
| **Memory-leak check** | slope **+0.041 MB/min**, first-quarter mean 48.37MB → last-quarter mean 51.09MB → **verdict: stable plateau** |

**`SampleStreamGuard` telemetry (full 90-minute run)**:

| Field | Value |
|---|---|
| Samples received | 267,891 |
| Timing gaps flagged | 1,076 (~1 every 5.0s) |
| Suspected dropped samples (estimated) | 2,928 |
| Duplicate/too-fast reads | 1,009 |
| Windows invalidated | 1,076 |
| Windows scored | 14,461 |
| Sample-interval mean / p50 | 20.16ms / 20.00ms |
| Sample-interval p95 / p99 | 21.73ms / 26.39ms |
| **Max sample interval** | **287.0ms** |

**Verdict: the corrected-v2 live pipeline ran for the full 1.5 hours against a real, physically
connected MPU6050 with zero deadline misses, zero sensor read failures, zero reconnects, zero
exceptions, and no memory leak.** Across 14,461 real windows the worst single window (82.86ms) still
landed **~3.6x inside** the 300ms stride budget, and p99 (3.25ms) sits ~92x inside it — this is the
same enormous headroom 4.4's 12-minute run showed, now confirmed to hold over 7.5x the duration. The
one number that moved meaningfully versus the shorter live runs is the worst-case single-sample I2C/
scheduling stall: 287.0ms here vs. 124.6ms (4.4, 12 min) and 130.5ms (4.2, unpaced 12 min) — expected,
since a longer run gives the OS scheduler more opportunities to produce a rare long tail (the same
"longer run surfaces rarer, larger outliers" pattern `ResultsFromPi.md` documented repeatedly for
CPU-only benchmarks); it remains **well below** `SampleStreamGuard`'s `long_gap_reset_s=1.0s` reset
threshold, so it was correctly flagged and the in-flight window discarded without ever forcing a full
gravity-filter reset. The gap rate (1,076 over 90 min, ~1 every 5s) is consistent with — actually
somewhat more frequent than — 4.3's ~1/8s and 4.4's ~1/6s, plausibly reflecting additional desktop/
background load accumulated over a much longer wall-clock window (this Pi ran its full desktop session
throughout, per the project's standing caveat) rather than any degradation in the sensor or pipeline
itself, since **zero** of those gaps were raw I2C read failures (`n_sensor_read_failures=0`) — every
one was `SampleStreamGuard` correctly catching a timing slip, exactly as designed. RSS grew from a
~48.4MB first-quarter mean to a ~51.1MB last-quarter mean (+0.041 MB/min) — small enough in absolute
terms (2.7MB over 90 minutes) and non-accelerating enough that `common.py`'s own linear-slope
classifier still calls it a **stable plateau**, not a leak; extrapolated linearly this would add
under 4MB/hour, not a practical concern for a deployed helmet running far shorter continuous sessions.
Thermal behavior stayed unremarkable throughout — max 53.0°C, no throttling flag ever set — consistent
with every other live/replay result in this project on this Pi (`force_turbo=1`, ambient-dominated, not
compute-dominated). **This closes 4.5/W2-LIVE-3: the plan's ≥1h soak requirement is met with a 90-
minute real-hardware run, at 1.5x its minimum duration, with no failure mode of any kind observed.**

---

## 4.8 — Live crash detector with lightweight background helmet services — ✅ COVERED (opportunistically, via 4.5's run)

Per the checklist, this item is explicitly **P1 / "only if convenient"**: measure the effect of BLE,
a DHT22/MQ135 bridge, and other existing lightweight services on deadline satisfaction. Rather than
building a separate dedicated experiment, this Pi already runs several such services continuously as
systemd units regardless of any test being run, so 4.5's 90-minute soak above was **not** run in
isolation — it ran with this real background load present the entire time:

| Service | Role | State throughout the 90-minute soak |
|---|---|---|
| `helmx-ble.service` | Real BLE server (`/home/helmx/bluetooth.py`), `Restart=always` | `active` / `enabled` — running continuously |
| `helmx_assistant.service` | HelmX Python voice assistant (`/home/helmx/helmx_assistant.py`) | **Continuously restart-looping** — exits cleanly (`status=0/SUCCESS`) and is relaunched by systemd every ~5s (`RestartUSec=5s`, `Restart=always`); confirmed still cycling at the moment this soak finished. This is the service's existing steady-state behavior on this system, not something triggered by this test |
| `mosquitto.service` | MQTT broker | `active` / `enabled` — running continuously |
| `rhasspy.service` | Voice-assistant backend (separate from `helmx_assistant.service`) | `active` / `enabled` — running continuously |

No DHT22/MQ135 sensor-bridge service exists on this system, so that specific pairing from the
checklist's wording isn't applicable here — the closest real equivalent available is the combination
above (BLE + voice assistant + MQTT + rhasspy).

**Result: 4.5's headline numbers already answer 4.8's question.** With all four services above active
the entire time — including one of them (`helmx_assistant.service`) launching a fresh Python process
roughly every 5 seconds for the full 90 minutes, arguably a *more* demanding concurrent-load scenario
than a steady-state BLE/MQTT bridge — the soak still produced **0/14,461 (0.0%) deadline misses**,
**0** sensor read failures, **0** reconnects, and **0** exceptions, with per-window p99 latency
(3.25ms) still ~92x inside the 300ms stride budget. **Verdict: existing lightweight helmet background
services (BLE server, MQTT broker, voice-assistant processes, including one that restarts every ~5s)
do not measurably threaten the crash-detection pipeline's real-time deadline** — the same enormous
latency headroom seen in every other live experiment in this file absorbs this additional real
background load without any observed degradation. This closes every MPU-dependent item (4.1–4.8) in
this file.

---

## Follow-up — clean-background-load comparison test (2026-09-05)

Per `piResults/My only strongly recommended remain.txt` (the user's own strongest-recommended
remaining test): rather than another long soak, run the **same live pipeline** for 15–30 minutes
under deliberately **reduced background load**, to test whether the loaded 90-minute soak's timing
gaps are explained by Linux/background-process scheduling contention rather than the MPU6050/I2C
path itself being unreliable.

**Before starting**, every non-essential background process/service was stopped — everything except
VS Code and this Claude Code session itself (kept running per explicit user instruction, so this is
a *reduced*-load run, not a zero-background-load one):

| Stopped | What it was |
|---|---|
| `helmx_assistant.service` | Voice-assistant process, previously restart-looping every ~5s |
| `helmx-ble.service` | Real BLE server (`/home/helmx/bluetooth.py`) — stopping it also killed a GPIO-based pulse-timing sensor-read subprocess (`libgpiod_pulsein64` on GPIO22, ~12% CPU) that turned out to be spawned by this same script, not a separate service |
| `mosquitto.service` | MQTT broker |
| `rhasspy.service` | Voice-assistant backend |
| `wayvnc.service`, `wayvnc-control.service` | VNC remote-desktop server |
| `rpi-connect.service`, `rpi-connect-wayvnc.service` (user-level) | Raspberry Pi Connect remote access/screen-share |

```
.pi_research_venv/bin/python -u deploy/pi_research_suite/exp_w2_live3_soak.py --duration-min 20 --checkpoint-every-min 5
```

Ran 2026-09-05 13:16:39–13:36:39 PKT, exact same script/pipeline as the loaded 90-minute soak (4.5
above). Full results: `results/pi_research/w2_live3_soak_20min.json` (a copy of
`results/pi_research/w2_live3_soak.json`, which this run overwrote — the 90-min run's copy was
recovered separately as `results/pi_research/w2_live3_soak_90min.json`, see 4.5 above; this run's
numbers are also reproduced in the table below).

### The comparison the recommendation asked for

| Metric | Loaded 90-min (4.5) | Clean-background 20-min | Change |
|---|---|---|---|
| Timing gaps / minute | **11.96** (1,076 / 90.0 min) | **4.20** (84 / 20.0 min) | **-65%** |
| Invalidated-window % | **6.93%** (1,076 / 15,537) | **2.20%** (84 / 3,823) | **-68%** |
| Windows/sec achieved | 2.68 | **3.12** | +16%, much closer to target |
| Target windows/sec | 3.33 | 3.33 | — |
| Deadline misses (>300ms) | 0 | 0 | no change (already perfect) |
| I2C read failures | 0 | 0 | no change (already perfect) |
| Sample-interval mean/p50 | 20.16 / 20.00ms | 20.00 / 20.00ms | ~unchanged |
| Sample-interval p95/p99 | 21.73 / 26.39ms | 21.68 / 26.54ms | ~unchanged |
| **Max sample interval** | **287.0ms** | **52.3ms** | **-82%**, and now far below the 1.0s gravity-filter-reset threshold |
| Per-window latency p99 / max | 3.25 / 82.86ms | 3.49 / **18.39ms** | p99 unchanged; worst-case window latency **-78%** |
| Process CPU mean / max | 2.35% / 9.9% | 2.37% / 40.6%* | mean unchanged |
| Temperature mean / max | 47.6°C / 53.0°C | 48.1°C / 54.0°C | ~unchanged (ambient-dominated, as expected) |
| Process RSS mean | 49.75MB | 48.28MB | ~unchanged |
| Memory-leak verdict | stable plateau | stable plateau | same |

*The clean run's one 40.6% CPU sample is a single brief spike (p95 stayed at a normal 3.9%) —
plausibly a one-off OS/systemd moment right around the service-stop transition, not a sustained
change; not treated as a meaningful finding on its own.

**Verdict: background process load explains most, but not all, of the loaded soak's timing-gap
rate — a real, quantified, honest result, not a clean "solved."** Both the gap rate and the
invalidated-window percentage dropped by roughly two-thirds under reduced load, achieved throughput
climbed from 80% to 94% of the 3.33 windows/sec target, and — most tellingly — the single worst-case
sample-interval stall dropped from 287.0ms to 52.3ms, an 82% reduction that puts this run's absolute
worst moment closer to 4.2/4.4's shorter live runs (124–131ms) than to the loaded 90-minute soak's
outlier. This is consistent with the recommendation's hypothesis: **the MPU6050/I2C path itself was
never the problem** (0 I2C failures in both runs, 0 deadline misses in both runs) — a meaningful share
of the timing gaps came from Linux scheduler contention against this Pi's background
services/processes, not sensor unreliability. At the same time, the gap rate did **not** drop to
zero (84 gaps still occurred in 20 minutes, 4.20/min) — with VS Code and this Claude Code session
deliberately still running (per explicit instruction, so this is not a true zero-background
baseline), some residual gap rate persists even under substantially reduced load, whether from VS
Code's own footprint, unavoidable general-purpose-Linux-desktop scheduling noise, or a smaller
genuine I2C/timing contribution that a fully headless deployment image would need to characterize
separately. **The honest reading: reduced background load is a large, real contributor to the gap
rate (roughly two-thirds of it, by this comparison), not the sole explanation for all of it** —
this mirrors the project's earlier CPU-only loaded-vs-reduced-background latency finding
(`ResultsFromPi.md`), now confirmed to hold for the real live-sensor pipeline as well. Either way,
the deployed pipeline's actual safety-relevant numbers — deadline misses and I2C failures — were
**zero in both conditions**, so this result refines the explanation for a secondary metric
(timing-gap rate) rather than changing any conclusion about deployment readiness.

**Services restarted immediately after this test** (`helmx_assistant.service`, `helmx-ble.service`,
`mosquitto.service`, `rhasspy.service`, `wayvnc.service`, `wayvnc-control.service`,
`rpi-connect.service`, `rpi-connect-wayvnc.service`) — the user's normal desktop/BLE/remote-access
environment was restored once data collection finished; none of the environment changes made for
this test are permanent.

---