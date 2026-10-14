# HelmX Crash Detection — Paper 1 Final Raspberry Pi Data Collection Checklist
**Purpose:** exhaustive final checklist of every useful Raspberry Pi / deployment-side measurement that could strengthen Paper 1, including critical, recommended, optional, and low-priority items.

**Current status:** most non-MPU experiments are already complete. This checklist is intentionally broader than necessary so that, before hardware teardown, as much reproducible evidence as possible can be captured.

---

# 1. Priority legend

- **P0 — Critical / highest value:** materially strengthens the target-device deployment claim.
- **P1 — Strongly recommended:** improves reproducibility, robustness, reviewer confidence, or interpretation.
- **P2 — Useful optional:** useful for discussion, appendices, or supplementary material.
- **P3 — Low priority / completeness only:** not required, but worth collecting if cheap while the Pi is accessible.

---

# 2. Already completed — preserve all raw files

## P0 — A1 isolated INT8 inference benchmark — COMPLETE
Already measured:
- deployed INT8 TFLite model
- 100 warmups
- 1000 measured inferences × 5 repeats
- median, p95, p99, max latency
- throughput
- model load time
- comparison with 300 ms stride budget

Current headline:
- median ≈ 0.553 ms
- p95 ≈ 0.942 ms
- p99 ≈ 1.682 ms
- worst observed in A1 ≈ 21.76 ms
- 300 ms deployed stride budget

Preserve:
- `results/pi_research/a1_isolated_inference.json`
- exact script used
- console log/output if available

## P0 — A3 thermal stability — COMPLETE
Already measured under real INT8 inference at 300 ms cadence:
- 30-minute duration
- 6000 real TFLite inferences
- initial, mean, max and checkpoint temperatures
- `vcgencmd get_throttled`
- throttling = false

Current headline:
- mean ≈ 55.4°C
- max ≈ 61.3°C
- no throttling
- `get_throttled = 0x0`

Preserve:
- `results/pi_research/a3_thermal.json`
- sustained-load helper script
- thermal script
- console output

## P0 — Experiment C replay validation — COMPLETE
Already validated:
- 10 held-out test sessions
- 5437 windows
- offline zero-phase Butterworth preprocessing
- real-time causal EMA path
- same deployed INT8 model and thresholds
- window-level decision agreement
- event-level trigger agreement
- mean absolute crash-probability difference
- mean absolute reconstruction-error difference

Current headline:
- 99.61% window-level decision agreement
- 100% event-level agreement
- mean absolute crash-probability difference ≈ 0.0408
- mean absolute reconstruction-error difference ≈ 0.0383

Preserve:
- `results/pi_research/c_replay_validation.json`
- session-level breakdown
- exact script
- held-out manifest/split information

## P0 — A5 trigger policy + GPIO actuation — COMPLETE
Already measured:
- 36 crash-like sessions replayed
- 35/36 detected
- first-anomaly-to-confirmed-trigger latency
- median 0.6 s
- p95, min/max
- real GPIO18 acquisition and pulse

Current headline:
- 97.2% of replayed crash-like sessions triggered
- 0.6 s minimum/median confirmation floor
- real GPIO pulse path executed successfully

Important interpretation:
This is confirmation latency from first anomalous window to 3-consecutive-window trigger, not necessarily physical crash-onset-to-alarm latency.

## P1 — B power availability check + simple contention benchmark — COMPLETE
Already established:
- power telemetry unavailable because no fuel gauge / power monitor exposes `power_now`
- solo model timing
- synthetic competing CPU worker
- latency degradation under that worker

Important interpretation:
Do not equate the busy-loop worker with the real drowsiness workload.

## P0 — Experiment D quantization verification — COMPLETE
Already compared:
- Keras float32 reference
- FP16 TFLite
- INT8 TFLite
- model sizes
- latency
- mean absolute crash-probability difference
- agreement at 0.5
- agreement at actual deployed threshold 0.9892

Current headline:
- Keras: 792,902 bytes
- FP16: 133,920 bytes
- INT8: 83,568 bytes
- INT8 ≈ 9.5× smaller than Keras
- INT8 decision agreement vs Keras at deployed threshold: 99.89%
- FP16 agreement at deployed threshold: 100%
- one INT8 latency outlier ≈ 109.6 ms, still below 300 ms

Preserve:
- `results/pi_research/d_quantization_comparison.json`
- exact Keras/FP16/INT8 artifacts
- script
- thresholds JSON

---

# 3. Non-MPU experiments to run BEFORE shutting down the Pi

## P0 — 3.1 Full replay-paced software-pipeline benchmark
This is the highest-value remaining non-MPU experiment.

### Goal
Measure the complete deployed software path without physical I2C acquisition:

recorded raw IMU samples → unit conversion → causal gravity filtering → rolling buffer → 60×6 window formation → 7 auxiliary feature extraction → INT8 inference → threshold logic → TriggerPolicy

Run at the real cadence:
- 50 Hz input sampling
- 60-sample windows
- 15-sample stride
- one decision every 300 ms

### Recommended duration
- minimum: 10 minutes
- preferred: 15–30 minutes
- if convenient: enough held-out replay to exceed several thousand decision windows

### Record
- number of input samples
- number of generated windows
- per-window complete processing latency
- mean, SD, p50, p90, p95, p99, max
- number of processing cycles >300 ms
- deadline-miss rate
- windows/sec or cycles/sec
- skipped windows
- exceptions
- process restarts

### Simultaneous resource monitoring
Record every 1 s if possible:
- process CPU %
- system CPU %
- process RSS
- process VMS if easy
- total RAM used
- available RAM
- swap used
- CPU temperature
- throttling status
- CPU frequency
- load average

Suggested file:
`results/pi_research/a4_replay_streaming_pipeline.json`

Also save raw CSV/log, replay session names, command line, script version and git commit.

## P0 — 3.2 Repeat A1 once after all final package installs
Reason: Experiment D observed one 109.6 ms INT8 outlier. A fresh A1 run helps determine whether this was an isolated scheduling/runtime spike.

Run the same exact settings:
- 100 warmups
- 1000 measured inferences
- 5 repeats

Preserve old and new results. Suggested file:
`results/pi_research/a1_isolated_inference_repeat_final.json`

Compare:
- median
- p95
- p99
- max
- frequency of >5 ms, >10 ms, >50 ms, >100 ms events
- model load time
- throughput

## P0 — 3.3 Final reproducibility/environment capture
Capture raw hardware/software environment before shutdown.

### Hardware/OS
```bash
cat /proc/cpuinfo
uname -a
cat /etc/os-release
lscpu
free -h
df -h
```

### Raspberry Pi firmware/state
```bash
vcgencmd measure_temp
vcgencmd get_throttled
vcgencmd measure_clock arm
vcgencmd get_config int
vcgencmd get_mem arm
vcgencmd get_mem gpu
```

### CPU governor/frequency
```bash
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq
```

### Python environment
```bash
.pi_research_venv/bin/python --version
.pi_research_venv/bin/pip freeze
```

### Record specifically
- numpy
- scipy
- pandas
- scikit-learn
- tensorflow
- tflite-runtime
- psutil
- pyyaml
- pyserial
- gpiozero
- mpu6050-raspberrypi

### Runtime details
Record:
- Raspberry Pi model/revision
- RAM size reported
- aarch64 / 64-bit
- Raspberry Pi OS / Debian version
- kernel
- CPU core count
- TFLite Runtime version
- TensorFlow version
- whether XNNPACK delegate is active
- TFLite thread count if explicitly configured
- model input/output dtypes
- whether CPU affinity is set
- whether process priority/nice is set
- whether desktop GUI was active
- whether IDE/editor was open
- important systemd services running

### Cooling/power physical notes
Record manually:
- fan present
- fan type if known
- enclosure state during tests
- battery vs USB adapter during each benchmark
- supply voltage/current rating if known
- ambient room temperature if known
- helmet enclosure open/closed during tests

Save as:
`results/pi_research/pi_environment_final.txt`

## P1 — 3.4 Background-service inventory
Before shutdown capture what else was running:
```bash
ps aux --sort=-%cpu
ps aux --sort=-%mem
systemctl --type=service --state=running
top -b -n 1
```
Goal: document BLE, DHT22/MQ135 bridge, desktop, SSH, IDE, browser, etc.

## P1 — 3.5 CPU jitter / latency-tail characterization
Run a longer INT8 benchmark:
- 10,000 or 50,000 inferences
- save every latency
- count events >2, >5, >10, >25, >50, >100, >300 ms

Report:
- median
- p95
- p99
- p99.9 if sample size supports it
- max
- empirical deadline-miss rate

Suggested file:
`results/pi_research/a1_long_tail_latency.json`

## P1 — 3.6 Thread-count sensitivity
If easy, run INT8 with:
- 1 thread
- 2 threads
- 4 threads

Record latency distribution, throughput and CPU%.
Purpose: determine whether one thread is already sufficient and whether extra cores can remain free.

## P1 — 3.7 CPU-governor sensitivity
If safe and convenient, compare current governor with `performance`.
Record latency, temperature and CPU frequency.
Do not change governor if it risks disturbing the system.

## P1 — 3.8 Cold-start / warm-start model timing
Repeat 10–20 times:
- process startup → model loaded
- model load time
- first inference
- steady-state inference

Useful for service-restart claims.

## P1 — 3.9 Process restart test
Kill/restart the crash process under replay/bypass mode.
Measure:
- restart time
- model reload time
- memory cleanup
- threshold reload correctness
- repeated restart errors

## P1 — 3.10 Threshold/config integrity snapshot
Save:
- `models/thresholds.json`
- deployed YAML/config files
- classifier threshold
- reconstruction threshold
- window size
- stride
- sampling rate
- consecutive-window count
- cooldown
- cancel-window duration

Also save model hashes:
```bash
sha256sum models/*
```

## P1 — 3.11 Model artifact metadata
For `.keras`, FP16 TFLite and INT8 TFLite record:
- size
- SHA256
- modification time
- export TensorFlow/TFLite version
- input shapes
- output names
- quantization metadata
- input dtype
- output dtype

## P1 — 3.12 TFLite delegate/operator behavior
Preserve startup output showing XNNPACK delegate activation.
If possible capture:
- interpreter thread count
- allocated tensor details
- operator list
- any non-delegated ops

## P2 — 3.13 Background-load levels
Optional synthetic stress:
- 0 busy workers
- 1 worker
- 2 workers
- 3 workers

Record crash latency distributions.
Do not claim equivalence to real drowsiness concurrency.

## P2 — 3.14 Memory-pressure benchmark
If safe, apply controlled moderate RAM pressure and record latency, RSS, swap and stability.

## P2 — 3.15 I/O-pressure benchmark
Optional SSD/logging/file-copy load while inference runs. Record tail-latency changes.

## P2 — 3.16 Network-load benchmark
Optional local network traffic while inference runs. Record latency tails.

## P2 — 3.17 Logging-overhead comparison
Compare normal logging, verbose logging and minimized logging.
Record latency, CPU and I/O.

## P2 — 3.18 Malformed-input robustness
Replay software edge cases:
- NaNs
- missing sample
- duplicated sample
- extreme accel
- extreme gyro
- constant signal
- zero signal
- sensor saturation
- short stream
- delayed stream

Record safe failure/recovery. Do not treat as accuracy evidence.

## P2 — 3.19 Sampling-jitter simulation
Replay with:
- exact 20 ms spacing
- ±2 ms jitter
- ±5 ms jitter
- occasional delayed sample
- occasional skipped sample

Measure buffer/trigger behavior.

## P2 — 3.20 Dropped-sample simulation
Simulate sparse and burst drops. Record whether buffering recovers, decisions remain stable, and missing data are detected/logged.

## P2 — 3.21 Replay repeatability/determinism
Replay identical sessions multiple times and compare crash_prob, recon_error, binary decisions and trigger times.

## P2 — 3.22 FP16 vs INT8 event-level agreement
Run both through TriggerPolicy and compare:
- event-level alerts
- trigger times
- missed events
- extra events

## P2 — 3.23 Threshold-margin analysis
Count held-out windows within ±0.001, ±0.005, ±0.01 and ±0.05 of the deployed classifier threshold. Useful for explaining why INT8 drift rarely changes the deployed decision.

## P2 — 3.24 Reconstruction-error quantization comparison
Compare Keras/FP16/INT8 reconstruction-error differences and threshold-crossing agreement, because the deployed decision uses classifier OR reconstruction.

## P2 — 3.25 OR-rule branch contribution
Count:
- classifier-only positives
- reconstruction-only positives
- both
- neither

At event level count events detected/rescued by each branch and false positives attributable to each branch.

## P2 — 3.26 Detailed causal-filter comparison
Beyond binary agreement:
- correlation
- difference distribution
- max absolute difference
- source-specific differences
- class-specific differences

## P2 — 3.27 Causal-filter state-reset test
Check cold start, session reset and long-gap behavior for transients.

## P2 — 3.28 Startup grace-period behavior
Measure:
- time until first valid decision
- whether partial windows are ignored
- whether any alert can occur before a full window exists

## P2 — 3.29 Cooldown logic replay
Test two events separated by <60 s and >60 s. Confirm suppression/resumption behavior.

## P2 — 3.30 Cancel-window software logic
Without GSM, test cancel-before-30-s vs no-cancel behavior and verify emergency stage suppression.

## P2 — 3.31 Alarm failure fallback
Simulate inability to acquire GPIO18 and confirm degraded/log-only behavior without crashing the service.

## P2 — 3.32 GSM/GPS failure-path behavior
Verify missing GSM/GPS errors do not terminate classification and retry/backoff works.

## P2 — 3.33 Timestamp/timer validation
Record system time, timezone, monotonic-timer usage and wall-clock logging behavior.

## P2 — 3.34 NTP/clock snapshot
```bash
timedatectl
```

## P2 — 3.35 Storage state
```bash
lsblk
df -h
swapon --show
```
Record SSD capacity/model if known, root usage and swap state.

## P2 — 3.36 Safe storage-I/O benchmark
Optional, non-destructive only.

## P2 — 3.37 Fan/cooling behavior
Record fan policy, trigger temperature if controlled, or state that fan is always on.

## P2 — 3.38 Ambient temperature
Record room temperature if possible. If DHT22 is used, call it approximate unless calibrated.

## P2 — 3.39 Power-source state
Record battery vs USB-C, supply rating, battery state if known and undervoltage flags.

## P3 — 3.40 Boot time
Measure power-on → OS ready → crash service ready → first possible decision.

## P3 — 3.41 Service enablement/restart policy
Save relevant `systemctl` status and service file fields such as `Restart=` and `RestartSec=`.

## P3 — 3.42 Journal logs
Export crash-service journal logs.

## P3 — 3.43 Kernel logs
Capture `dmesg` for undervoltage, I2C, USB, thermal and filesystem events.

## P3 — 3.44 CPU affinity snapshot
Use `taskset -cp <PID>` if applicable.

## P3 — 3.45 Process priority snapshot
Use `ps -o pid,ni,pri,rtprio,cmd -p <PID>`.

## P3 — 3.46 File-descriptor stability
During replay/soak track `/proc/<PID>/fd` count.

## P3 — 3.47 Thread-count stability
Track `ps -o nlwp= -p <PID>`.

## P3 — 3.48 Python heap/GC growth
Only if convenient or leak suspected.

## P3 — 3.49 Thermal recovery after load
Optional 10–15 min cooldown curve.

## P3 — 3.50 Restart-after-failure resilience
Test SIGTERM/SIGKILL and systemd restart behavior if safe.

---

# 4. MPU-dependent experiments to run AFTER hardware troubleshooting

## P0 — 4.1 Verify physical I2C detection
```bash
i2cdetect -y 1
ls /dev/i2c*
```
Expected MPU address: `0x68` or `0x69`.
Also verify I2C enabled, SDA/SCL, 3.3 V, GND and AD0 state.

## P0 — 4.2 Live raw sensor validation
Once detected:
- read all 6 axes continuously
- confirm plausible stationary and moving values
- measure achieved sample rate
- sampling-interval distribution
- missed reads
- I2C errors

## P0 — 4.3 A2 active CPU/RAM
Run real `crash_monitor.py` with live MPU.
Minimum 10–15 min; preferred 30 min.
Record process/system CPU, RSS, RAM, swap, temperature, inference count and sensor errors.

## P0 — 4.4 A4 true live streaming pipeline
Measure:
sensor read → preprocessing → windowing → features → INT8 inference → thresholds → policy

Record:
- p50/p95/p99/max end-to-end processing latency
- number >300 ms
- deadline-miss rate
- achieved sample rate
- dropped/missed samples
- CPU/RAM
- temperature
- throttling

## P0 — 4.5 A6 sustained live soak
Minimum recommended: 1 hour. Preferred: 2 hours.
Record samples, windows, inferences, missed deadlines, sensor errors, restarts, RSS drift, CPU, max temp and throttling.

## P1 — 4.6 Physical movement smoke test
Stationary baseline, gentle rotation, tilt, shake and non-crash bump. Confirm plausible signals and no unexpected failures. Do not perform unsafe impact tests.

## P1 — 4.7 Safe live trigger-path test
If possible without destructive impact, validate live sensor loop → scorer → TriggerPolicy → LocalAlarm. Replay injection is acceptable if physical triggering would be unsafe.

## P1 — 4.8 Live crash detector with lightweight background helmet services
Only if convenient. Measure effect of BLE, DHT22/MQ135 bridge and other existing lightweight services on deadline satisfaction.

---

# 5. Offline/laptop-side Paper 1 material to preserve

## P0
Preserve final:
- train/validation/test manifests
- source/session grouping
- split seed
- preprocessing settings
- normalization/scaler parameters
- final thresholds
- final selected architecture config
- model checkpoints
- final metric tables
- ROC/PR values
- event-level metrics
- OOD results
- DaRUS results
- external scooter results
- SimRa results if retained
- ablations
- failure cases
- negative results

## P1
Preserve:
- training curves
- early-stopping epoch
- random seeds
- package environment
- training hardware
- training duration
- laptop inference metrics if already available
- parameter count
- FLOPs/MACs if available
- input-feature definitions
- auxiliary-feature definitions

---

# 6. Important model/system facts to freeze in machine-readable form

## Sampling/windowing
- 50 Hz
- window length 60 samples
- window duration 1.2 s
- stride 15 samples
- stride duration 0.3 s

## Input
6 IMU channels:
- ax, ay, az
- gx, gy, gz

7 auxiliary features:
- mean accel magnitude
- std accel magnitude
- peak accel magnitude
- mean gyro magnitude
- std gyro magnitude
- peak gyro magnitude
- peak jerk

## Model
- shared Conv1D encoder
- reconstruction decoder
- classifier head
- reconstruction error used by classifier head
- deployed INT8 TFLite

## Decision
- classifier threshold ≈ 0.989226
- reconstruction threshold ≈ 10.878736
- OR fusion
- 3 consecutive anomalous windows
- cooldown 60 s
- local alert
- cancel window 30 s
- SMS/GPS after uncancelled alarm

## Real-time preprocessing
- causal EMA gravity removal
- offline reference uses zero-phase Butterworth
- replay agreement validated

---

# 7. Final recommended before-shutdown order

## MUST DO
1. replay-paced full software-pipeline benchmark
2. repeat A1 once
3. capture final hardware/software environment
4. copy all JSON/CSV/log outputs
5. copy all experiment scripts
6. copy deployed models and thresholds
7. save SHA256 hashes
8. export relevant system/service logs
9. save this checklist with the repository/results

## STRONGLY RECOMMENDED IF TIME
10. long-tail inference run
11. process/background-service snapshot
12. thread-count sensitivity
13. startup/restart timing
14. event-level FP16/INT8 agreement
15. OR-rule branch contribution

## OPTIONAL IF STILL CONVENIENT
16. controlled CPU-load levels
17. sampling-jitter replay
18. dropped-sample simulation
19. cooldown/cancel logic tests
20. fault-path tests
21. storage/network/logging pressure checks
22. boot/service-restart data
23. fan/ambient/power-source notes

Then shut down and troubleshoot the MPU6050 physically.

---

# 8. What can still be published if MPU remains unavailable

Paper 1 can still report:
- real Pi 4 INT8 inference latency
- latency-tail distribution
- 300 ms inference deadline headroom
- 30-min thermal stability
- no observed thermal throttling
- offline-vs-causal deployment replay agreement
- event-level trigger agreement
- trigger-policy timing behavior
- real GPIO actuation
- quantization size/latency/agreement trade-off
- synthetic CPU-contention robustness
- replay-paced complete software-pipeline timing if collected
- explicit limitation that live I2C acquisition and long-duration full-stream testing were unavailable

Do NOT claim:
- full live MPU-to-alert timing
- live active CPU/RAM
- live sensor sampling reliability
- full live soak stability
unless actually measured.

---

# 9. Recommended final results-package structure

```text
results/
  pi_research/
    a1_isolated_inference.json
    a1_isolated_inference_repeat_final.json
    a1_long_tail_latency.json
    a2_resource_usage.json
    a3_thermal.json
    a4_replay_streaming_pipeline.json
    a5_trigger_latency.json
    a6_soak.json
    c_replay_validation.json
    d_quantization_comparison.json
    pi_environment_final.txt
    process_snapshot.txt
    systemd_services.txt
    dmesg.txt
    journal_crash_service.txt
    model_hashes.txt
    pip_freeze.txt
    raw_latency_csvs/
    logs/
```

Keep unavailable fields as `null`, `not_available`, or explicit text. Never estimate missing measurements.

---

# 10. Stop rule for Paper 1 Pi work

## Minimum complete without live MPU
- A1 complete
- A3 complete
- C complete
- A5 complete
- D complete
- replay-paced full software pipeline complete
- environment/reproducibility dump complete
- all raw files preserved

## Ideal complete with recovered MPU
plus:
- live sensor sampling validated
- A2 active resources complete
- A4 live end-to-end processing complete
- A6 ≥1 h live soak complete

Everything beyond that is supplementary rather than essential.
