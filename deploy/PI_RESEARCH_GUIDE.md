# HelmX Pi/Helmet Hardware Research Guide

This is the single reference for running the deployed HelmX crash model on real Raspberry
Pi/helmet hardware and collecting every metric needed for the paper: isolated inference
benchmarking, sustained resource/thermal behavior, real streaming-pipeline latency, trigger
latency, a soak test, power (optional), a real-hardware replay validation against the offline
pipeline, and a quantization comparison. It also documents the exact JSON result schema to
produce.

**Nothing in this guide has been run on real hardware** — this development environment has no
Raspberry Pi, MPU6050, or GPIO attached. Two experiments (A1, A2) are implemented as ready-to-run
scripts and have been smoke-tested here as far as possible without real hardware (see each
section). The rest are given as clear, concrete instructions/snippets to adapt, because they need
sensors/GPIO this environment doesn't have. Report back whatever you get — including "X didn't
work as written" — the same honesty this whole project has been built on.

## 0. What changed to make this possible

`deploy/crash_monitor.py` was refactored (behavior-preserving — verified by tracing the new code
against the old line-by-line, and by a smoke test) to extract two reusable classes out of its
`main()` loop:

- **`WindowScorer`** — the exact per-sample buffering → per-window scoring path (gravity filter →
  window assembly → aux features → TFLite inference), split into `append(sample)` and
  `try_score()` so the real-time pacing sleep still happens in exactly the same place it always
  did.
- **`TriggerPolicy`** — the exact consecutive-window + cooldown confirmation rule, with an optional
  explicit `now=` timestamp so replayed/synthetic tests don't have to wait through real wall-clock
  cooldowns.

This means every experiment below that needs "the real pipeline" can `import crash_monitor` and
use these classes directly — not a reimplementation that could silently drift from what's actually
deployed. `mpu6050` and `gpiozero` imports are now lazy (fall back to `None`), so the module
imports cleanly even on a machine with no sensor/GPIO wired up yet — only `connect_sensor()` (which
needs a real MPU6050) raises if you actually call it.

`deploy/pi_research_suite/common.py` holds small shared utilities (`percentile_stats`,
`device_info`, `read_temp_c`/`read_throttled` via `vcgencmd`, `sample_process_resources`,
`save_json`) used by the two ready-made scripts and referenced in the snippets below.

## 1. Requirements

**Hardware**: Raspberry Pi (any model the deployed stack already targets), MPU6050 wired via I2C,
GPIO-connected buzzer/vibration motor (for A5), optionally a UPS/HAT with a fuel-gauge for power
(§7). A2/A3/A6 need nothing beyond the Pi itself; A4/A5 need the real MPU6050 (and GPIO for A5);
C/D need only the model files (no sensor needed — they replay recorded data).

**Software** (on the Pi):
```bash
cd Crash-Detection   # wherever this repo landed on the Pi
pip install -r deploy/requirements.txt      # tflite-runtime, numpy, pyserial, pyyaml,
                                             # mpu6050-raspberrypi, gpiozero, psutil
```
Raspberry Pi OS's pip is pre-configured to pull from [piwheels.org](https://www.piwheels.org/)
(prebuilt ARM wheels), so this is normally fast — no manual wheel-hunting needed. If you're
running Experiments C or D (which reuse the training-side `src/` package to load held-out
sessions and the Keras model for comparison), you also need the heavier root
`requirements.txt` — those two are the only experiments that need TensorFlow itself, not just
`tflite-runtime`; everything else in this guide runs with the lightweight `deploy/requirements.txt`
alone.

**Config**: `deploy/config.yaml` must point at real paths (`model_path`, `normalizer_path`,
`thresholds_path` — all already relative to the repo root) and have `gsm.recipient_number` set if
you exercise the full alert path in A5's optional full-countdown mode.

## 2. Running the deployed system itself

```bash
python deploy/crash_monitor.py
```
Logs to `logs/crash_monitor.log` (rotating, see `deploy/config.yaml: logging`) and to stdout. It
retries the MPU6050 connection indefinitely if not found — Ctrl+C to stop. This is what Experiments
A2, A3, A6 monitor while it runs, and what A4 instruments directly.

## 3. The unified result schema

Every experiment below writes its own JSON under `piResults/results/generated/<name>.json`
(`common.ensure_results_dir()`/`common.save_json()` already do this for you in the two ready-made
scripts). Once you've run what you can, merge them by hand or with a two-line script into one file
matching (and extending) the schema you specified:

```json
{
  "device": {"model": null, "ram_gb": null, "os": null, "python": null, "tflite_runtime": null},
  "model": {"format": "int8", "size_bytes": null},
  "isolated_inference": {
    "runs": 1000, "mean_ms": null, "std_ms": null, "p50_ms": null,
    "p95_ms": null, "p99_ms": null, "max_ms": null, "throughput_windows_s": null,
    "load_time_ms": null
  },
  "streaming_pipeline": {
    "duration_minutes": null, "n_windows": null,
    "mean_preprocess_ms": null, "mean_windowing_ms": null, "mean_inference_ms": null,
    "mean_total_latency_ms": null, "p95_total_latency_ms": null, "p99_total_latency_ms": null,
    "missed_deadlines": null, "dropped_samples": null
  },
  "resources": {
    "cpu_mean_percent": null, "cpu_p95_percent": null, "cpu_max_percent": null,
    "ram_mean_mb": null, "ram_max_mb": null, "memory_leak_verdict": null,
    "temperature_start_c": null, "temperature_mean_c": null, "temperature_max_c": null,
    "temperature_at_10_20_30min_c": [null, null, null],
    "thermal_throttling_occurred": false
  },
  "trigger_latency": {
    "n_events_replayed": null, "n_detected": null,
    "mean_trigger_latency_s": null, "median_trigger_latency_s": null,
    "p95_trigger_latency_s": null, "min_s": null, "max_s": null
  },
  "replay_validation": {
    "sessions": null, "windows_compared": null,
    "window_decision_agreement": null, "event_decision_agreement": null,
    "mean_abs_crash_prob_diff": null, "mean_abs_recon_error_diff": null
  },
  "quantization_comparison": {
    "fp16": {"size_bytes": null, "median_ms": null, "p95_ms": null, "p99_ms": null},
    "int8": {"size_bytes": null, "median_ms": null, "p95_ms": null, "p99_ms": null},
    "classification_agreement_vs_keras": null
  },
  "stability": {
    "duration_hours": null, "process_failures": null, "restarts": null,
    "missed_inference_cycles": null, "max_scheduling_delay_ms": null
  },
  "power": {
    "available": false, "idle_w": null, "sensor_idle_w": null,
    "crash_active_w": null, "crash_plus_drowsiness_w": null, "incremental_crash_w": null
  }
}
```
Fields you can't measure (no fuel-gauge HAT, didn't run a given experiment yet) stay `null` —
report unavailable, never estimate, matching this project's existing convention
(`deploy/benchmark_device.py`'s power probe already does exactly this).

## A1. Isolated inference benchmark — **ready to run**

```bash
python deploy/pi_research_suite/exp_a1_isolated_inference.py
# optional: --warmup 100 --measured 1000 --repeats 5 --model models/helmx_crash_model_int8.tflite
```
Runs the deployed INT8 model with 100 warm-up + 1,000 measured inferences, 5 repeats, reporting
mean/median/p95/p99/max/std latency, throughput, and model load time — writes
`piResults/results/generated/a1_isolated_inference.json`. **Smoke-tested here** using the dev machine's
`tensorflow.lite.Interpreter` fallback (no `tflite_runtime` on this machine) against the real
deployed `.tflite` files — it runs end-to-end and produces sane numbers; only the *values* will
differ on real Pi hardware. The script prints the stride budget (300ms) next to the measured
latency so the "enormous headroom" comparison is immediate.

## A2. CPU/RAM under sustained operation — **ready to run**

```bash
python deploy/pi_research_suite/exp_a2_resource_usage.py --duration-min 15
```
Launches `deploy/crash_monitor.py` itself (needs the real MPU6050 wired up — it'll retry
connecting indefinitely otherwise) and samples process CPU%, system CPU%, process RSS, system RAM,
swap, and temperature every 1 second for the requested duration, then reports
mean/p95/max and an explicit memory-leak verdict (linear-fit slope of RSS over the run, plus a
first-quarter vs. last-quarter comparison). Use `--pid <pid>` to attach to an already-running
instance instead of launching a new one. Writes
`piResults/results/generated/a2_resource_usage.json`, including the raw per-second samples (so you can
plot the RSS trend directly for the paper, not just the summary numbers).

## A3. Thermal stability — instructions

No GPU/thermal hardware exists in this dev environment to test against, so this is given as a
short script to save and run directly on the Pi (uses the same `common.py` helpers as A1/A2):

```python
# save as deploy/pi_research_suite/exp_a3_thermal.py and run:
#   python deploy/pi_research_suite/exp_a3_thermal.py --duration-min 30 --interval-s 8
import argparse, time, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

p = argparse.ArgumentParser()
p.add_argument("--duration-min", type=float, default=30.0)
p.add_argument("--interval-s", type=float, default=8.0)
args = p.parse_args()

samples = []
start = time.monotonic()
deadline = start + args.duration_min * 60.0
checkpoints = {10: None, 20: None, 30: None}  # minutes -> temp_c
while time.monotonic() < deadline:
    elapsed_min = (time.monotonic() - start) / 60.0
    temp = common.read_temp_c()
    samples.append({"elapsed_min": elapsed_min, "temp_c": temp})
    for cp in list(checkpoints):
        if checkpoints[cp] is None and elapsed_min >= cp:
            checkpoints[cp] = temp
    time.sleep(args.interval_s)

temps = [s["temp_c"] for s in samples if s["temp_c"] is not None]
throttled = common.read_throttled()
report = {
    "device": common.device_info(),
    "duration_min_requested": args.duration_min,
    "n_samples": len(samples),
    "initial_temp_c": temps[0] if temps else None,
    "mean_temp_c": sum(temps) / len(temps) if temps else None,
    "max_temp_c": max(temps) if temps else None,
    "temp_at_checkpoints_c": checkpoints,
    "throttling_status": throttled,
    "thermal_throttling_occurred": bool(throttled and (
        throttled["currently_throttled"] or throttled["throttling_occurred"]
        or throttled["arm_freq_capped_now"] or throttled["arm_freq_capped_occurred"]
    )) if throttled else None,
    "raw_samples": samples,
}
common.save_json(report, "a3_thermal")
print(report["initial_temp_c"], report["mean_temp_c"], report["max_temp_c"], report["temp_at_checkpoints_c"])
print("Throttling occurred:", report["thermal_throttling_occurred"])
```
Run this **while `deploy/crash_monitor.py` is also running** (separate terminal/`&`) for a
meaningful "sustained inference" thermal reading — a 30-minute idle-Pi reading isn't the number the
paper needs. The important result per your own framing isn't "low temperature," it's **"sustained
inference causes no thermal throttling"** — report the `throttling_status` dict and the
`_occurred` flags honestly either way.

## A4. Real streaming pipeline latency — instructions

This measures the REAL path: MPU6050 read → `WindowScorer.append()` (gravity filter) →
`WindowScorer.try_score()` (windowing + TFLite inference) → decision, using the actual sensor, not
synthetic data.

```python
# save as deploy/pi_research_suite/exp_a4_streaming_pipeline.py, run on the Pi with the
# MPU6050 wired up:
#   python deploy/pi_research_suite/exp_a4_streaming_pipeline.py --n-windows 500
import argparse, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common
import crash_monitor as cm

p = argparse.ArgumentParser()
p.add_argument("--n-windows", type=int, default=500)
args = p.parse_args()

cfg = common.load_config()
model = cm.CrashModel(common.ROOT / cfg["model_path"], common.ROOT / cfg["normalizer_path"])
gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
scorer = cm.WindowScorer(cfg, model, gravity_filter)
import logging
sensor = cm.connect_sensor(cfg, logging.getLogger("a4"))

period = 1.0 / cfg["sensor"]["sample_rate_hz"]
records = []
next_tick = time.monotonic()
while len(records) < args.n_windows:
    next_tick += period
    sample = cm.read_sensor(sensor, logging.getLogger("a4"))
    if sample is None:
        continue
    preprocess_ms = scorer.append(sample)
    sleep_for = next_tick - time.monotonic()
    if sleep_for > 0:
        time.sleep(sleep_for)
    else:
        next_tick = time.monotonic()
    result = scorer.try_score()
    if result is None:
        continue
    records.append({
        "preprocess_ms": preprocess_ms,
        "windowing_ms": result["windowing_ms"],
        "inference_ms": result["inference_ms"],
        "total_ms": preprocess_ms + result["windowing_ms"] + result["inference_ms"],
    })

report = {
    "device": common.device_info(),
    "n_windows": len(records),
    "preprocess_ms": common.percentile_stats([r["preprocess_ms"] for r in records]),
    "windowing_plus_inference_ms": common.percentile_stats([r["windowing_ms"] + r["inference_ms"] for r in records]),
    "total_per_window_ms": common.percentile_stats([r["total_ms"] for r in records]),
    "stride_budget_ms": cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"] * 1000,
}
common.save_json(report, "a4_streaming_pipeline")
print(report["total_per_window_ms"])
```
This tells you whether the WHOLE embedded path — not just TFLite alone (A1 already covers that) —
stays inside the 300ms stride interval. Compare `total_per_window_ms.p95_ms`/`p99_ms` against
`stride_budget_ms`.

## A5. Trigger-to-local-alarm latency — instructions

Replays known crash windows (pull them from the canonical local `data/` inputs or the DaRUS/fall sessions —
see Experiment C below for exactly how to load them) through `WindowScorer` + `TriggerPolicy`
with **synthetic timestamps** (no real-time waiting needed — `TriggerPolicy.update(..., now=...)`
accepts an explicit clock), measuring wall-clock time from the first abnormal window to
`alarm.start()` actually firing:

```python
# sketch -- adapt with your own replayed-session loader (see Experiment C)
import time
import crash_monitor as cm

cfg = common.load_config()
model = cm.CrashModel(...)
alarm = cm.LocalAlarm(cfg["alarm"]["gpio_pin"], logger)
classifier_t, recon_t = cm.load_model_thresholds(cfg)
policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"], cfg["thresholds"]["cooldown_seconds"])

first_abnormal_wallclock = None
for window, aux in replayed_crash_windows:            # your real per-window stream for one session
    crash_prob, recon_error = model.predict(window, aux)
    t_now_wall = time.perf_counter()
    is_anomaly, triggered = policy.update(crash_prob, recon_error, now=time.monotonic())
    if is_anomaly and first_abnormal_wallclock is None:
        first_abnormal_wallclock = t_now_wall
    if triggered:
        t_trigger_wall = time.perf_counter()
        alarm.start()                                  # real GPIO pulse -- confirms it actually fires
        latency_s = t_trigger_wall - first_abnormal_wallclock
        alarm.stop()
        break
```
Run this once per replayed session (across several known-crash sessions), collect `latency_s` per
event, report count/success-rate/mean/median/p95/min/max. **Keep the GSM/SMS/30-second
cancellation countdown out of this measurement** — per your own framing, that's a separate, known,
fixed 30s (`countdown_seconds` in `deploy/config.yaml`) added on top of whatever this measures, not
part of "detection latency."

## A6. Sustained stability / soak test — instructions

Wrap A2's monitoring loop around a **supervisor** instead of a fixed duration: run
`deploy/crash_monitor.py` for 1-2 hours, restart it if it dies, and log every restart:

```python
# sketch -- extends exp_a2_resource_usage.py's launch-and-monitor pattern
import subprocess, time, sys
import common

restarts, failures = 0, 0
end = time.monotonic() + 2 * 3600  # 2 hours
samples = []
while time.monotonic() < end:
    proc = subprocess.Popen([sys.executable, str(common.DEPLOY_DIR / "crash_monitor.py")], cwd=str(common.ROOT))
    while proc.poll() is None and time.monotonic() < end:
        samples.append(common.sample_process_resources(__import__("psutil").Process(proc.pid)))
        time.sleep(1.0)
    if proc.poll() is not None and time.monotonic() < end:
        failures += 1
        restarts += 1
        print(f"Process died (exit {proc.returncode}) -- restarting ({restarts})")

report = {
    "duration_hours": 2.0, "process_failures": failures, "restarts": restarts,
    "cpu": common.summarize_series(samples, "process_cpu_percent"),
    "ram_mb": common.summarize_series(samples, "process_rss_mb"),
    "temperature_c": common.summarize_series(samples, "temperature_c"),
}
common.save_json(report, "a6_soak_test")
```
For "missed inference cycles"/"maximum scheduling delay": parse `logs/crash_monitor.log`'s
per-window `crash_prob=... streak=...` lines (one per successful window), diff consecutive
timestamps, and flag any gap noticeably larger than the expected stride interval
(`stride_samples / sample_rate_hz` seconds) as a missed/delayed cycle — report the largest such
gap as the max scheduling delay. **Only report the "ran N hours with zero failures" headline if
that's actually what happened** — this run either produces that clean result or it doesn't, and
either is useful data for the paper.

## B. Power (optional) — instructions

`deploy/benchmark_device.py: read_power_now_microwatts()` already exists and is reused as-is —
it returns `None` (never a fabricated number) if the Pi has no fuel-gauge HAT/UPS exposing
`/sys/class/power_supply/*/power_now` (a plain Pi 4 with no such add-on won't have this). If you
do have one:
```python
from pathlib import Path
import sys
sys.path.insert(0, "deploy")
from benchmark_device import read_power_now_microwatts

# Sample this at each of: Pi idle, Pi+sensors with crash AI disabled, crash detector
# active, (later) crash+drowsiness active -- a few seconds of averaged samples each --
# and derive incremental AI power as crash_active - sensor_idle, per your own formula.
print(read_power_now_microwatts())
```
If your hardware can't measure this reliably, leave the `power` block in the schema `null`/
`"available": false` — don't estimate.

## C. Replay validation on the real Pi — **the most important experiment**

This is the one place a real discrepancy would actually matter for the paper: `deploy/
crash_monitor.py` uses a **causal** gravity-removal approximation
(`CausalGravityFilter`, an exponential moving average), while the offline training/evaluation
pipeline (`src/units.py: remove_gravity`) uses a **zero-phase Butterworth filter** — genuinely
different filters, documented as a deliberate tradeoff, never before verified to agree in
practice.

**Approach**: load the exact held-out test sessions (and/or the external scooter sessions) the
same way every other evaluation script in this repo does, but instead of calling
`preprocess.canonicalize_all()` (which applies the OFFLINE filter), feed each session's **raw**
per-sample stream through the REAL `WindowScorer` (which applies the causal filter + the deployed
INT8 model), then compare against the already-computed offline predictions.

```python
# sketch -- run from the Pi (needs the full root requirements.txt, not just deploy/'s, since
# this reuses src/) or from a dev machine with a Pi's tflite_runtime substituted for
# tensorflow.lite -- the numerical comparison is identical either way; only wall-clock
# timing would differ, which this experiment isn't measuring.
import sys
sys.path.insert(0, ".")
sys.path.insert(0, "deploy")
from src import io_loaders, preprocess, manifest, units
import crash_monitor as cm
import common

cfg = common.load_config()
sessions = io_loaders.load_all_sessions()          # RAW, gravity still present
split_of = manifest.assign_splits(sessions)
test_sessions = [s for s in sessions if split_of.get(s.session_id) == "test"]

model = cm.CrashModel(common.ROOT / cfg["model_path"], common.ROOT / cfg["normalizer_path"])

agreements, prob_diffs, recon_diffs = [], [], []
for s in test_sessions:
    # Match what a real MPU6050 would hand read_sensor(): gyro in deg/s, accel raw-with-gravity.
    df = units.gyro_to_deg_per_s(s.df, s.gyro_in_deg_per_s)
    gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
    scorer = cm.WindowScorer(cfg, model, gravity_filter)
    for _, row in df.iterrows():
        scorer.append([row.ax, row.ay, row.az, row.gx, row.gy, row.gz])
        result = scorer.try_score()
        if result is not None:
            # ... compare result["crash_prob"]/["recon_error"] against the offline pipeline's
            # prediction for the matching window index (build the offline predictions the same
            # way scripts/full_metrics.py or scripts/evaluate_model.py already do, on the SAME
            # canonicalized session) ...
            pass

# report: mean(|prob_diff|), mean(|recon_diff|), window-level decision agreement rate,
# event-level (simulate_deployed_alerts-style) agreement rate.
```
**Ideally: near-100% decision agreement, small numerical differences from the two filters'
differing phase response.** If agreement is meaningfully lower than that, that is itself an
important, honestly-reportable finding — it would mean the causal-filter approximation
documented as a "deliberate tradeoff" actually changes real decisions, not just introduces
harmless phase lag. Report whatever you find.

## D. Quantization verification — instructions

Compare Keras, FP16 (`models/helmx_crash_model_fp16.tflite`), and INT8
(`models/helmx_crash_model_int8.tflite`) on the **same** windows (reuse the held-out test set,
loaded the normal offline way this time — this experiment is about the model artifact, not the
streaming pipeline, so the offline canonicalization is the right preprocessing to use here):

```python
import sys, time
sys.path.insert(0, ".")
sys.path.insert(0, "deploy")
import numpy as np, tensorflow as tf
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite
import common

# ... build X_seq, X_aux for the test split exactly as scripts/full_metrics.py does ...
keras_model = tf.keras.models.load_model("models/helmx_crash_model.keras")
keras_probs = keras_model.predict({"seq": X_seq, "aux": X_aux})["crash_prob"].ravel()

results = {}
for name, path in [("fp16", "models/helmx_crash_model_fp16.tflite"), ("int8", "models/helmx_crash_model_int8.tflite")]:
    interpreter = tflite.Interpreter(model_path=path)
    interpreter.allocate_tensors()
    runner = interpreter.get_signature_runner()
    times_ms, probs = [], []
    for i in range(len(X_seq)):
        t0 = time.perf_counter()
        out = runner(seq=X_seq[i:i+1].astype(np.float32), aux=X_aux[i:i+1].astype(np.float32))
        times_ms.append((time.perf_counter() - t0) * 1000)
        probs.append(float(out["crash_prob"][0, 0]))
    probs = np.array(probs)
    results[name] = {
        "size_bytes": __import__("os").path.getsize(path),
        **common.percentile_stats(times_ms),
        "mean_abs_diff_vs_keras": float(np.mean(np.abs(probs - keras_probs))),
        "classification_agreement_vs_keras": float(np.mean((probs >= 0.5) == (keras_probs >= 0.5))),
    }
common.save_json(results, "d_quantization_comparison")
```
Desktop numbers already show INT8 is smaller but not necessarily faster than FP16 on x86 — the
question this answers for the paper is **whether quantization materially changes predictions**,
not which is fastest (that's what A1's per-format runs would tell you if you run it once per
format with `--model`).

## Notes for whoever runs this

- Everything here reads `models/`/`deploy/config.yaml` as committed — don't recalibrate anything
  against data collected during these runs; every threshold stays exactly as deployed, matching
  every other experiment in this project.
- If any script errors out on the actual Pi in a way this guide didn't anticipate (missing
  package, a `mpu6050`/`gpiozero` API difference, a real GPIO wiring issue), that's expected —
  nothing here has touched real hardware. Fix forward and note what changed; don't silently paper
  over a real discrepancy.
- Merge whatever subset of the schema (§3) you actually collect into one file — partial, honest
  results are more useful than none, and every experiment here is independent of the others.
