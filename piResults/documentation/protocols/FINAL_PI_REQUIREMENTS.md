# HelmX IEEE Sensors Journal — Complete Final Raspberry Pi Evidence & Test Request

**Purpose:**  
This document is the consolidated, authoritative Raspberry Pi-side evidence/test checklist for the current HelmX IEEE Sensors Journal paper.

It combines:
- the previous `HelmX_Pi_Final_Test_Request`,
- the later reviewer-driven recommendations,
- additional Pi-side measurements identified after reviewing the harshest reviewer comments,
- and reproducibility/preservation requirements.

This document intentionally includes **everything useful that can be done with the existing HelmX Raspberry Pi + MPU6050 + integrated helmet hardware/software**, even if some items are optional.

## Scope Rule

### Included
Anything that can be done using the existing:
- Raspberry Pi 4,
- mounted MPU6050,
- existing HelmX helmet,
- existing GPS/GSM hardware,
- existing GPIO/local-alert hardware,
- existing software stack,
- existing model files,
- existing datasets/replays,
- Linux tools already installable/usable on the Pi,
- no additional external measurement instrument.

### Excluded from required/current Pi work
Do **not** delay the current paper for tests requiring new external equipment such as:
- inline electrical power meter,
- shaker table,
- reference accelerometer / reference IMU,
- impact rig,
- calibrated vibration source,
- destructive crash-test facility,
- external high-speed motion-capture instrumentation.

These remain future work.

---

# A. REQUIRED — FREEZE THE CURRENT PAPER CORRECTLY

## A1. Preserve the authoritative deployed artifacts exactly

Copy and archive the exact files used in the final live experiments:

- deployed crash-monitor code,
- `SampleStreamGuard`,
- causal EMA preprocessing implementation,
- frozen thresholds/config,
- INT8 TFLite model,
- FP16 model if used in comparison,
- Keras/floating-point reference model if needed,
- model-export scripts,
- TFLite calibration/export script,
- reproducibility manifest,
- dataset/split hashes already available,
- scheduler-profile raw outputs,
- 90-min soak outputs,
- 12-min physical processing-latency outputs,
- reduced-background outputs,
- movement-test outputs,
- controlled DaRUS-injection trigger outputs,
- system/service-state documentation,
- exact final Pi experiment scripts.

Do not overwrite old raw files.

Preserve failed/aborted runs too and label them clearly.

---

## A2. Create one final machine-readable experiment-condition inventory

Create:

`final_pi_validation/experiment_conditions.csv`

and/or:

`final_pi_validation/experiment_conditions.txt`

For every major campaign record:

1. 90-min sustained loaded soak  
2. earlier 20-min reduced-background run  
3. scheduler-profile loaded run  
4. scheduler-profile reduced-background run  
5. 12-min physical processing-latency run  
6. controlled trigger-injection run  
7. safe movement test  
8. every new run performed from this checklist  

For each campaign record:

- campaign name,
- date,
- start time,
- end time,
- duration,
- active HelmX services,
- stopped HelmX services,
- desktop/session state,
- VS Code / IDE presence,
- interactive development-tool presence,
- Rhasspy state,
- MQTT/Mosquitto state,
- BLE service state,
- VNC / Pi Connect state,
- camera processes if active,
- GSM/GPS processes if active,
- CPU governor,
- CPU frequency,
- TFLite thread count,
- Python version,
- TFLite Runtime version,
- OS version,
- kernel version,
- exact command used,
- git commit if available,
- archive/code hash,
- model SHA-256,
- threshold/config SHA-256.

---

# B. REQUIRED SENSOR-CONFIGURATION EVIDENCE

This is the highest-priority remaining Pi-side requirement.

## B1. Full MPU6050 register readback

Run a short script on the actual helmet/Pi configuration and save raw register values.

At minimum read:

- `0x19` — `SMPLRT_DIV`
- `0x1A` — `CONFIG` / `DLPF_CFG`
- `0x1B` — `GYRO_CONFIG` / `FS_SEL`
- `0x1C` — `ACCEL_CONFIG` / `AFS_SEL`

Also read and save if possible:

- `0x6B` — `PWR_MGMT_1`
- `0x23` — `FIFO_EN`
- `0x38` — `INT_ENABLE`
- `0x3A` — `INT_STATUS`
- `0x75` — `WHO_AM_I`
- any additional relevant user-control/FIFO register if easy,
- current I²C bus clock / baudrate from Pi configuration.

Report both:

1. raw hexadecimal values,
2. decoded meaning.

Required decoded outputs:

- accelerometer full-scale range,
- gyroscope full-scale range,
- DLPF mode/bandwidth,
- configured sample-rate divider,
- device clock source,
- FIFO enabled/disabled,
- DATA_RDY interrupt enabled/disabled,
- I²C bus rate.

Preferred output:

`final_pi_validation/mpu_config/mpu6050_register_dump.txt`

`final_pi_validation/mpu_config/mpu6050_register_dump.json`

---

## B2. Verify the actual 50-Hz acquisition mechanism

Document exactly how live 50-Hz operation is produced.

State whether the current deployed code uses:

- `time.sleep`,
- monotonic deadline scheduling,
- busy wait,
- SMBus polling,
- FIFO drain,
- DATA_RDY interrupt,
- another mechanism.

Record:

- timestamp function used,
- where timestamp is captured relative to the I²C read,
- whether timestamps represent host/userspace read times or sensor-generated sample times,
- whether `alpha` in the EMA remains fixed when real `dt` varies,
- whether duplicate-like samples (`dt < 10 ms`) are accepted into windows or only counted,
- behavior after gaps,
- behavior after long interruptions,
- behavior after alert countdown/cooldown.

Preferred output:

`final_pi_validation/mpu_config/acquisition_method.txt`

---

# C. REQUIRED / HIGH-VALUE PHYSICAL SENSOR CHARACTERIZATION

## C1. Mounted stationary noise test

Use the fully assembled helmet with the MPU6050 in the exact deployed mount.

Duration:

- minimum 5 minutes,
- preferably 10 minutes.

Helmet condition:

- stationary,
- placed safely,
- no intentional movement.

Log both:

- raw int16 axes,
- converted physical units.

For each axis:

- `ax`
- `ay`
- `az`
- `gx`
- `gy`
- `gz`

Report:

- sample count,
- mean,
- standard deviation,
- RMS,
- min,
- max,
- peak-to-peak,
- p50,
- p95,
- p99,
- absolute maximum.

Also report:

- acceleration magnitude mean/std,
- gyroscope magnitude mean/std,
- stationary temperature if available,
- I²C failure count,
- timing-gap count,
- too-fast count,
- actual sample-interval statistics.

Preferred output:

`final_pi_validation/stationary_noise/stationary_noise_raw.csv`

`final_pi_validation/stationary_noise/stationary_noise_summary.txt`

---

## C2. Per-axis clipping / saturation check

During controlled safe helmet movement, log raw and converted per-axis data.

Scenarios:

- stationary,
- gentle rotation,
- repeated tilt,
- moderate controlled rotation,
- controlled shaking,
- controlled bump/tap,
- hand-carried walking-like motion,
- putting on/removing helmet if safe.

For every axis report:

- minimum raw int16,
- maximum raw int16,
- minimum converted value,
- maximum converted value,
- maximum absolute value,
- count of samples equal/near `-32768`,
- count of samples equal/near `32767`,
- percentage of samples within:
  - 99% of configured full scale,
  - 95% of configured full scale,
  - 90% of configured full scale.

Important:

- evaluate clipping **per axis**, not only vector magnitude,
- do not claim absence of clipping for real crashes,
- only state whether clipping was observed in the evaluated safe movement scenarios.

Preferred output:

`final_pi_validation/clipping/clipping_raw.csv`

`final_pi_validation/clipping/clipping_summary.txt`

---

# D. STREAM TIMING / TEMPORAL VALIDITY CHARACTERIZATION

## D1. Raw inter-sample interval characterization under several software loads

Run 10–15 minutes for each condition:

1. minimal/reduced background,
2. normal HelmX workload,
3. heavier interactive workload.

For each condition collect:

- total samples,
- achieved sample rate,
- mean `dt`,
- p50 `dt`,
- p95 `dt`,
- p99 `dt`,
- p99.9 `dt` if enough samples,
- max `dt`,
- `dt > 30 ms` gap count,
- gaps/min,
- `dt < 10 ms` count,
- too-fast/min,
- estimated dropped-equivalent samples,
- dropped-equivalent/min,
- I²C failures,
- reconnects,
- exceptions.

Also save the raw timestamp or `dt` series.

Preferred output:

`final_pi_validation/timing_loads/<condition>_dt.csv`

`final_pi_validation/timing_loads/timing_load_summary.csv`

---

## D2. Decision Coverage and Temporal Validity for every new live run

For every campaign report both:

### Temporal Validity
`V_T = N_scored / (N_scored + N_invalid)`

### Decision Coverage
Use the current paper definition based on nominal stride positions versus actually formed/scored decisions.

Report:

- nominal windows / nominal decision positions,
- scored windows,
- invalidated candidates,
- never-formed/suppressed decision positions,
- `V_T`,
- `C_D`.

Do not use `V_T` alone as if it were total decision coverage.

---

## D3. Contiguous valid-run distribution

For every **new** run, preserve enough per-sample timestamps to calculate contiguous valid runs directly.

Compute:

- number of uninterrupted valid-sample runs,
- run length in samples,
- run length in seconds,
- p50/p95/p99/max contiguous-run duration,
- fraction of time inside uninterrupted runs long enough for:
  - one 60-sample window,
  - one 75-sample interval if useful,
  - one 90-sample / 1.8-s three-window confirmation sequence.

Also compute empirical:

`P(valid 90-sample confirmation opportunity)`

under each tested condition.

This directly answers the reviewer concern about timing gaps potentially voiding confirmation sequences.

Preferred output:

`final_pi_validation/coverage/contiguous_valid_runs.csv`

`final_pi_validation/coverage/confirmation_survival_summary.txt`

---

# E. ACQUISITION-METHOD MITIGATION EXPERIMENT

This is the highest-value new Pi experiment after sensor register readback.

## E1. Baseline current polling condition

Run a matched 20-minute baseline with the current deployed acquisition method.

Collect:

- all timing metrics,
- `V_T`,
- `C_D`,
- contiguous-run statistics,
- p50/p95/p99/max `dt`,
- gaps/min,
- too-fast/min,
- dropped-equivalent samples/min,
- processing latency p50/p95/p99/max,
- I²C failures,
- CPU,
- RSS,
- temperature,
- scheduler data if possible.

---

## E2. FIFO or DATA_RDY acquisition condition

Implement **one** improved acquisition method without changing the trained model or decision thresholds:

Preferred:
- MPU6050 hardware FIFO, or
- DATA_RDY interrupt-paced acquisition.

Run the same duration and similar service state as E1.

Collect the same metrics.

Important:
- do not change the model,
- do not retune thresholds,
- preserve the current polling implementation,
- treat this as an acquisition-method comparison.

Preferred output:

`final_pi_validation/acquisition_compare/polling_baseline.*`

`final_pi_validation/acquisition_compare/fifo_or_drdy.*`

`final_pi_validation/acquisition_compare/acquisition_comparison.csv`

---

## E3. Optional scheduling-enhanced acquisition condition

If safe and straightforward, add a third condition:

- FIFO/DRDY or current poll loop,
- `SCHED_FIFO`/real-time scheduling via `chrt`,
- CPU affinity via `taskset`,
- optional isolated CPU if configuration is already available,
- reduced interactive background.

Record exact priority/CPU affinity values.

Run the same metrics.

This condition is optional but valuable because it helps separate:

- sensor acquisition method,
- userspace scheduling policy,
- background workload.

---

## E4. Optional deployment-realistic no-IDE/no-desktop stress reduction

If possible without reconfiguring the entire OS, run one 20-minute condition with:

- VS Code closed,
- interactive development tools closed,
- unnecessary desktop apps closed,
- only services required for HelmX deployment active.

Do not call this “headless” unless there is genuinely no desktop session.

Label it:

`deployment-reduced-interactive`

Report the same metrics.

---

# F. SCHEDULER-PROFILE REPLICATION

## F1. Repeat matched loaded vs reduced-background conditions

Run at least:

- 3 matched loaded runs,
- 3 matched reduced-background runs.

If practical, 5 matched pairs is better.

Duration:

- 20 minutes per run.

Keep protocol as identical as possible.

Collect:

- `perf sched latency`,
- mean scheduler/runqueue wait,
- p95/p99/max scheduler wait if extractable,
- `perf stat`,
- system-wide context switches,
- process-level context switches,
- CPU migrations,
- page faults,
- gaps/min,
- `V_T`,
- `C_D`,
- dropped-equivalent samples/min,
- p50/p95/p99/max processing latency,
- >300-ms exceedances,
- >stride-duration exceedances if useful,
- I²C failures,
- reconnects,
- exceptions,
- process CPU,
- total CPU,
- RSS,
- temperature,
- throttle state.

Report run-to-run:

- mean,
- standard deviation,
- median,
- range,
- preferably confidence intervals for stable metrics if appropriate.

Emphasize:

- gap rate,
- `C_D`,
- p99,
- scheduler wait distributions.

Do not lead with single-run maxima.

Preferred output:

`final_pi_validation/scheduler_repeats/run01_loaded.*`

`final_pi_validation/scheduler_repeats/run01_reduced.*`

...

`final_pi_validation/scheduler_repeats/scheduler_repeat_summary.csv`

---

# G. LIVE PIPELINE / LATENCY CHARACTERIZATION

## G1. Physical processing-latency run

Repeat or preserve a live MPU6050 processing-latency run.

Clearly define latency as:

**window completion / final required sample available → operational decision produced**

Do not call this physical crash-onset-to-alert latency.

Report:

- samples,
- scored windows,
- invalid windows,
- p50 latency,
- p95,
- p99,
- p99.9 if useful,
- max,
- >20 ms,
- >50 ms,
- >100 ms,
- >300 ms,
- CPU,
- RSS,
- temperature,
- throttle state.

Preferred output:

`final_pi_validation/live_latency/live_processing_latency.json`

---

## G2. Guard overhead measurement

Measure and preserve:

- mean guard overhead,
- p95,
- p99,
- max.

This confirms timestamp integrity monitoring remains computationally negligible.

---

## G3. TFLite thread-count sensitivity

If not already fully preserved, run:

- 1 thread,
- 2 threads,
- 4 threads.

Use enough inferences for stable tails.

Report:

- mean,
- p50,
- p95,
- p99,
- max,
- throughput,
- CPU,
- RSS if easy.

Primary question:

Which thread count gives the best tail predictability?

---

# H. LONG-RUN STABILITY

## H1. Existing 90-min soak — preserve exact raw outputs

Keep all raw 90-min results.

Do not rerun unless desired.

---

## H2. Optional longer 3-hour soak

If convenient, perform one 3-hour fully assembled helmet run.

6 hours is unnecessary unless very easy.

Collect:

- sample count,
- scored windows,
- nominal windows,
- invalid candidates,
- never-formed decision positions,
- `V_T`,
- `C_D`,
- timing gaps,
- dropped-equivalent samples,
- too-fast events,
- p50/p95/p99/max `dt`,
- p50/p95/p99/max processing latency,
- >300-ms deadline misses,
- I²C failures,
- reconnects,
- exceptions,
- CPU mean/p95/max,
- RSS min/mean/max,
- temperature mean/p95/max,
- thermal throttle state,
- trigger count,
- memory drift over time,
- gap rate over time,
- `C_D` over time,
- latency tails over time.

Preferred output:

`final_pi_validation/long_soak/long_soak_raw.*`

`final_pi_validation/long_soak/long_soak_summary.txt`

---

# I. SAFE BENIGN-MOTION FALSE-TRIGGER STRESS TEST

Using the fully assembled helmet only.

Safe scenarios:

1. stationary,
2. putting on helmet,
3. removing helmet,
4. gentle head-like rotation,
5. repeated tilts,
6. hand-carried walking-like motion,
7. moderate controlled shaking,
8. stronger but safe controlled shaking,
9. soft placement on seat/table,
10. controlled shell bump/tap,
11. short repeated sequence after reboot if possible.

For each scenario record:

- duration,
- sample count,
- scored windows,
- timing gaps,
- invalid fraction,
- `V_T`,
- `C_D`,
- maximum classifier score,
- maximum reconstruction error,
- number of classifier-threshold crossings,
- number of reconstruction-threshold crossings,
- number of OR-positive windows,
- number of 3-window confirmed triggers,
- per-axis extrema,
- raw clipping counts.

Important:
- these do not reproduce motorcycle vibration,
- these do not reproduce crashes,
- report only benign-handling behavior.

Preferred output:

`final_pi_validation/benign_motion/benign_motion_stress.csv`

`final_pi_validation/benign_motion/benign_motion_notes.txt`

---

# J. REBOOT / REASSEMBLY REPEATABILITY

## J1. Separate boot-cycle repeatability

Run the same short movement sequence after at least two separate boot cycles.

Record:

- register dump after each boot,
- stationary bias/noise,
- peak accel/gyro,
- classifier max,
- reconstruction max,
- trigger status,
- timing metrics,
- service state.

Purpose:

Show that the mounted sensor + software pipeline restarts consistently.

Preferred output:

`final_pi_validation/reboot_repeatability/boot1.*`

`final_pi_validation/reboot_repeatability/boot2.*`

`final_pi_validation/reboot_repeatability/reboot_comparison.txt`

---

# K. INT8 RECONSTRUCTION-OUTLIER DIAGNOSTIC

This is high-value and should be done if technically feasible.

Identify the exact held-out window responsible for the reported absolute reconstruction deviation of ~702.55.

For that exact window capture:

## Reference outputs
- Keras classifier probability,
- Keras reconstruction error,
- FP16 TFLite classifier probability,
- FP16 TFLite reconstruction error,
- INT8 TFLite classifier probability,
- INT8 TFLite reconstruction error.

## Operational decisions
For each model representation report:

- classifier threshold crossing,
- reconstruction threshold crossing,
- OR-rule outcome.

## Input characterization
Report:

- 60×6 normalized tensor min/max,
- per-channel min/max,
- raw/physical amplitude if reconstructable,
- seven auxiliary scalar values.

## Quantization characterization
Report:

- input tensor quantization scale,
- input zero-point,
- output scales/zero-points,
- relevant internal tensor scales/zero-points if accessible,
- counts of values hitting int8 `-128`,
- counts hitting int8 `127`,
- any clipping/saturation evidence.

## Preserve-all-tensors trace
If feasible:

Use TFLite `experimental_preserve_all_tensors` or equivalent.

For each layer/operator:

- tensor name,
- dtype,
- quantization parameters,
- min,
- max,
- mean,
- number at int8 min/max.

Identify the first layer/operator where the INT8 path materially diverges from floating point if possible.

Do not guess the cause if no clear mechanism is proven.

Preferred output:

`final_pi_validation/int8_outlier/int8_outlier_summary.txt`

`final_pi_validation/int8_outlier/int8_outlier_tensors.npz`

`final_pi_validation/int8_outlier/tflite_tensor_quantization.txt`

---

# L. INT8 REPRESENTATIVE-DATASET AUDIT

Using the exact export/calibration code used for the deployed INT8 model:

Reconstruct the 200 validation windows selected with deterministic seed 42.

Report:

- exact selected indices/session IDs if available,
- number of normal vs crash-like weak labels,
- parent-session composition,
- source/domain composition,
- per-channel normalized min/max,
- physical amplitude min/max if reconstructable,
- acceleration magnitude range,
- gyroscope magnitude range,
- peak jerk range,
- comparison with the full validation-set ranges,
- whether the INT8 outlier input falls inside or outside representative-data ranges.

This does not require new hardware.

Preferred output:

`final_pi_validation/int8_calibration/representative_dataset_summary.csv`

`final_pi_validation/int8_calibration/representative_dataset_notes.txt`

---

# M. CAUSAL FILTER / PREPROCESSING ANALYSIS ON THE PI

These can also be done on desktop, but may be run on the Pi if convenient.

## M1. EMA cutoff sensitivity

Replay the frozen held-out set using causal EMA cutoffs:

- 0.1 Hz
- 0.2 Hz
- 0.3 Hz deployed
- 0.4 Hz
- 0.5 Hz

Do not retune model thresholds.

For each cutoff report:

- window decision fidelity vs offline reference,
- classifier MAE,
- reconstruction MAE,
- classifier correlation,
- reconstruction correlation,
- event/session trigger agreement,
- number of decision flips,
- normal-session agreement,
- anomaly-session agreement if available.

Preferred output:

`final_pi_validation/ema_sensitivity/ema_sensitivity.csv`

---

## M2. Same-order causal Butterworth comparison

Reviewer-driven optional analysis.

Compare:

1. existing offline zero-phase 2nd-order Butterworth reference,
2. deployed first-order causal EMA,
3. causal 2nd-order Butterworth with same nominal 0.3-Hz corner.

Report:

- magnitude-response values/plot data,
- phase/group-delay information,
- `F_D`,
- classifier MAE,
- reconstruction MAE,
- event/session agreement,
- decision-flip counts.

Purpose:

Separate:
- deployment choice as actually implemented,
from
- the narrower effect of causality using a same-order filter family.

Do not replace the deployed EMA unless evidence requires it.

Preferred output:

`final_pi_validation/filter_identity/filter_comparison.csv`

`final_pi_validation/filter_identity/filter_response_data.csv`

---

# N. CLASS-STRATIFIED DEPLOYMENT FIDELITY

This is important but mainly uses frozen replay data.

## N1. Causal preprocessing disagreement table

For the 5,437 held-out windows, produce paired reference vs causal decisions with the original weak window labels retained.

Report separately for:

- 5,294 normal windows,
- 143 crash-like windows.

Provide:

- reference negative → transformed negative,
- reference negative → transformed positive,
- reference positive → transformed negative,
- reference positive → transformed positive.

Also report:

- class-specific decision agreement,
- number of flipped crash-like windows,
- number of flipped normal windows,
- whether any flip changed a 3-window event trigger.

---

## N2. INT8 class-stratified decision fidelity

Repeat the same analysis for:

- floating/Keras reference vs INT8 at the actual deployed classifier threshold,
- reconstruction threshold if pairwise values are available,
- final OR decision if possible.

Preferred output:

`final_pi_validation/class_fidelity/class_stratified_fidelity.csv`

`final_pi_validation/class_fidelity/class_stratified_fidelity.txt`

---

# O. FROZEN DETECTOR OPERATING-POINT CONTEXT

Preserve/export the already-known deployed test-set performance.

At minimum:

- precision,
- recall,
- F1,
- TP,
- FP,
- TN,
- FN,
- positive-window rate.

Also preserve dual-signal branch attribution:

- classifier-only positives,
- reconstruction-only positives,
- both,
- neither.

Current known values should be verified from source files before freezing:

- OR precision ≈ 0.906,
- OR recall ≈ 0.203,
- OR F1 ≈ 0.331,
- classifier-only = 19,
- reconstruction-only = 1,
- both = 14,
- neither = 5,403.

Preferred output:

`final_pi_validation/frozen_detector/frozen_detector_context.txt`

---

# P. CONTROLLED LIVE TRIGGER PATH VALIDATION

Preserve or rerun if necessary.

Procedure:

- live physical MPU6050 baseline,
- controlled DaRUS trace injection into scorer,
- actual threshold logic,
- 3-window confirmation,
- real GPIO18 actuation,
- return to live sensor.

Record timestamps for:

- first injected sample,
- first anomalous scored window,
- second anomalous window,
- third anomalous window,
- confirmed trigger,
- GPIO activation,
- GPIO deactivation,
- live sensor resume.

Report:

- classifier values,
- reconstruction values,
- OR decisions,
- sensor errors before/after,
- processing latency.

Important:
- label this controlled trace injection,
- do not call it a physical crash.

Preferred output:

`final_pi_validation/trigger_path/trigger_path.csv`

---

# Q. OPTIONAL GPS/GSM INTEGRATION SMOKE TEST

This uses existing integrated hardware and therefore can be included without external equipment.

Run 5–10 controlled tests:

- trigger,
- local alert,
- cancellation timer,
- GPS status,
- GPS fix/no-fix,
- SIM800L SMS attempt,
- modem response,
- SMS received if manually verifiable.

Timestamp:

- trigger,
- cancellation start,
- cancellation expiry,
- GPS request,
- GPS fix,
- SMS request,
- modem acceptance,
- reception if verified.

Report:

- fix success count,
- no-fix count,
- time to fix where available,
- SMS attempt count,
- modem-accepted count,
- received count if checked.

Important:
- system-context evidence only,
- do not claim network reliability from 5–10 trials.

Preferred output:

`final_pi_validation/gps_gsm_optional/gps_gsm_smoke_test.csv`

---

# R. OPTIONAL SYSTEM-PROCESS / PYTHON RUNTIME CHARACTERIZATION

Useful if easy.

During selected runs record:

- Python garbage-collection events if instrumentable,
- process scheduling priority,
- thread count,
- CPU affinity,
- per-process CPU,
- page faults,
- involuntary/voluntary context switches,
- memory growth,
- any log-write bursts.

Purpose:

Help explain rare latency tails without over-attributing them.

Do not delay the paper if this is difficult.

---

# S. FINAL FILE STRUCTURE

Use one folder:

`final_pi_validation/`

Recommended structure:

```text
final_pi_validation/
  README.txt
  experiment_conditions.csv

  frozen_artifacts/
  mpu_config/
  stationary_noise/
  clipping/
  timing_loads/
  coverage/
  acquisition_compare/
  scheduler_repeats/
  live_latency/
  long_soak/
  benign_motion/
  reboot_repeatability/
  int8_outlier/
  int8_calibration/
  ema_sensitivity/
  filter_identity/
  class_fidelity/
  frozen_detector/
  trigger_path/
  gps_gsm_optional/
  runtime_optional/
```

---

# T. REQUIRED METADATA FOR EVERY NEW RUN

Every new experiment folder/file should preserve:

- experiment name,
- exact command,
- date/time,
- duration,
- Pi serial/host identifier if appropriate,
- OS,
- kernel,
- Python version,
- TFLite Runtime version,
- code hash,
- model hash,
- threshold/config hash,
- MPU6050 register dump,
- service state,
- CPU governor/frequency,
- TFLite thread count,
- desktop/IDE state,
- scheduler policy,
- CPU affinity,
- acquisition mode,
- raw log filename.

---

# U. PRIORITY ORDER

If time is limited, perform in this order.

## Tier 1 — Highest priority
1. Full MPU6050 register/configuration readback.
2. Document exact 50-Hz acquisition/timestamp mechanism.
3. Mounted stationary-noise test.
4. Per-axis clipping/saturation check.
5. Preserve raw timestamps for all new runs.
6. Polling vs FIFO/DRDY acquisition comparison.
7. Exact class-stratified causal and INT8 fidelity from frozen replay data.
8. Add `C_D` and contiguous-valid-run/confirmation-survival analysis.

## Tier 2 — Strong reviewer-response value
9. Three matched scheduler loaded/reduced repetitions.
10. INT8 outlier tensor-level diagnostic.
11. INT8 representative calibration-set audit.
12. EMA cutoff sensitivity.
13. Same-order causal Butterworth comparison.
14. Benign-motion false-trigger stress test.

## Tier 3 — Strong optional evidence
15. 3-hour soak.
16. Deployment-reduced-interactive/no-IDE condition.
17. Scheduling-enhanced acquisition condition (`SCHED_FIFO` / CPU affinity).
18. Reboot repeatability.
19. GPS/GSM integration smoke test.
20. Additional runtime/GC/process characterization.

---

# V. ITEMS THAT DO NOT NEED NEW EXTERNAL EQUIPMENT BUT SHOULD NOT BECOME CLAIMS THEY CANNOT SUPPORT

Even after completing every test above:

- do not claim real-road false-alert reliability without real riding data,
- do not claim natural crash sensitivity,
- do not claim helmet mechanical transfer function,
- do not claim anti-alias rejection beyond what the actual configured DLPF and sampling path support,
- do not claim electrical power/battery life without direct electrical measurement,
- do not claim GPS/GSM network reliability from a small smoke test,
- do not claim hard real-time guarantees from zero observed deadline misses,
- do not claim universal portability of the numerical results,
- do not claim absence of crash-time sensor saturation unless crash-like physical excitation has actually been measured,
- do not call controlled DaRUS injection a physical crash.

---

# W. EXPLICITLY EXCLUDED — EXTERNAL EQUIPMENT / FUTURE STUDIES

Do not delay the current paper for:

- electrical power meter testing,
- shaker-table transfer-function characterization,
- co-located reference IMU,
- calibrated anti-alias vibration injection,
- destructive helmet crash testing,
- public-road deliberate crash testing,
- instrumented impact rig,
- PREEMPT_RT kernel study if substantial system reconfiguration is required,
- Cortex-M / FreeRTOS / Zephyr port,
- large-scale real-road riding campaign.

These are legitimate future studies.

---

# X. FINAL STOPPING RULE

The Pi-side campaign is more than sufficient for the current IEEE Sensors Journal paper once the following are available:

1. exact MPU6050 configuration,
2. clear acquisition/timestamp mechanism,
3. stationary-noise + safe per-axis clipping evidence,
4. preserved raw timestamp data for new runs,
5. one acquisition-method comparison (polling vs FIFO/DRDY) if technically feasible,
6. replicated scheduler comparison if feasible,
7. class-stratified deployment fidelity,
8. clarified `V_T` + `C_D`,
9. INT8 outlier/calibration characterization if feasible,
10. frozen reproducibility archive.

After that, stop expanding the Pi experiment set unless a reviewer specifically requests a new study.

The objective is not to make HelmX experimentally infinite.  
The objective is to make every claim in the current Sensors paper directly traceable to measured, reproducible evidence.
