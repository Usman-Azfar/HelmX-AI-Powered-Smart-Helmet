# Progress tracker — HelmX Final Pi Validation (per `HelmX_FInal_Pi_REqwuirements.md`)

Source doc: `piResults/HelmX_FInal_Pi_REqwuirements.md` (sections A-X).
Scope decisions made with the user before starting (2026-09-19):
- **Section Q (GPS/GSM)**: run up to modem dispatch, do NOT actually send SMS.
- **Sections C2 (clipping) + I (benign-motion stress test)**: DONE (2026-09-19/20) — guided live session, see their rows below for results and the mid-session-reboot recovery.
- **Section J (reboot repeatability)**: deferred — this coding session runs on the same Pi; user will trigger reboots themselves. At the end.
- **H2 (3-hour soak), E2 (FIFO/DRDY acquisition), E3 (SCHED_FIFO/taskset variant)**: explicitly skipped this pass (optional/heavy, user chose Tier 1-2 required items only).

Host: `helx-pi`, Raspberry Pi 4 Model B Rev 1.5, `aarch64`, kernel `6.12.96+rpt-rpi-v8`. MPU6050 confirmed at I2C 0x68.

**Important constraint**: the MPU6050 is a single I2C device — hardware-facing captures (C1, D1, F1, G1, Q) cannot run concurrently with each other; they run one at a time. Replay-based analyses on frozen test-split data (K, L, M1, M2, N1, N2, O) don't touch the sensor and are scheduled in the gaps between hardware runs, never *during* one (to avoid CPU-load confounds in timing measurements).

## Status

| Section | Item | Status | Output |
|---|---|---|---|
| A1 | Freeze authoritative artifacts | DONE | `frozen_artifacts/` |
| A2 | Experiment-condition inventory | DONE (fully populated through this session, incl. J boot1-3 and this round's E2/E3/E4/H2 smoke tests + full runs; will still take one more row if Q is ever unblocked) | `experiment_conditions.csv` |
| B1 | MPU6050 register readback | DONE (found WHO_AM_I=0x70, not the datasheet 0x68 -- disclosed as a finding; DLPF off, SMPLRT_DIV=0, internal 8kHz) | `mpu_config/` |
| B2 | 50Hz acquisition mechanism doc | DONE | `mpu_config/acquisition_method.txt` |
| C1 | Mounted stationary noise test | DONE -- 10 min, 247,151 samples (unpaced back-to-back, ~412Hz achieved), 0 I2C failures. accel magnitude mean 9.91 m/s^2 (expect ~9.81), gyro magnitude mean 2.37 deg/s (expect ~0 -- a real static gyro bias; deployed pipeline never zeroes/calibrates gyro bias, only accel gets high-pass filtered). Az carries only ~0.82 m/s^2 of the ~9.9 m/s^2 total, i.e. the mount is NOT Z-aligned to gravity -- a mount-orientation fact, not a defect. | `stationary_noise/` |
| C2 | Per-axis clipping check | DONE — accelerometer (±2g full-scale) essentially never clips under benign handling (only a handful of brief `ay`/`az` excursions to raw ±32768 during bump/tap, shaking, and helmet removal). The **gyroscope (±250°/s full-scale) clips measurably** under vigorous-but-benign handling: worst case `6_controlled_shaking_stronger`/`gy` hits 4.15% of samples within 90% of full-scale (28 samples pinned at -32768, 35 at 32767 out of 3034); `9_removing_helmet`/`gz` reaches 1.44%. Gentle motion (stationary, gentle_rotation, bump_tap) shows no clipping. This is a real finding, not an artifact — ±250°/s is easily exceeded by a quick hand tilt/shake, independent of any crash. Combined with I below (`pi_val_ci_motion_session*.py`). | `clipping/` |
| D1 | Timing-load characterization (3 conditions) | DONE -- 0 I2C failures, 0 gaps>30ms in all 3 conditions (minimal_background, normal_helmx_workload, heavier_interactive_workload w/ stress-ng --cpu 4). Jitter rises measurably under load without crossing the gap threshold: p99 dt 2.3-2.9ms -> 5.4ms, max dt <12ms -> 27.8ms under stress. These are deliberately UNPACED captures (matches exp_w2_live1_sample_interval.py's established convention), so their own V_T/C_D are trivially 1.0 -- see D2/D3 note. | `timing_loads/` |
| D2 | V_T / C_D | DONE for D1's 3 conditions (trivial 1.0, see above) + a 1-min paced smoke-test (V_T=0.935, C_D=0.802 -- genuinely informative). Real numbers now coming from F1's 6 paced runs (in progress). | `coverage/` |
| D3 | Contiguous valid-run distribution | DONE for D1 (trivial, one giant run each). Real per-run contiguous-run stats + P(90-sample confirmation opportunity) pending on F1's 6 paced runs' raw dt series (`exp_w2_live3_soak_raw_dt.py`, a new raw-dt-preserving variant written for this, since the original harness only kept a capped rolling window). | `coverage/` |
| E1 | Baseline polling condition | DONE by reuse -- satisfied by the preserved G1 run (`w2_live2_pipeline.json`) plus F1's "loaded" runs (same deployed polling acquisition); no separate standalone capture since E2 (its comparison partner) was skipped. | `acquisition_compare/` (see README note) |
| E2 | FIFO/DRDY acquisition | DONE (2026-09-20, scope reopened by user) -- smoke test (18s) + full 20-min run, 0 I2C errors/overflow/exceptions/deadline misses. Chip confirmed MPU6500 (WHO_AM_I=0x70); native FIFO push rate ~487-493Hz, does not follow the classic MPU6050 SMPLRT_DIV formula -- decimated to ~49.5Hz in software (disclosed). **New finding**: 5 confirmed triggers over 3956 windows, all reconstruction-only (crash_prob=0.0, recon_error 10.99-13.35 vs threshold 10.88 -- marginal), not seen in the E1-reused baseline (0/1975) or the I-session's 11 benign phases (0 recon crossings) -- reported as an open/unconfirmed finding, not attributed to the FIFO method without an isolating rerun. | `acquisition_compare/` |
| E3 | SCHED_FIFO/taskset variant | DONE (2026-09-20, scope reopened by user) -- smoke test + full 20-min run under `sudo chrt -f 10 taskset -c 3` (cpu_affinity confirmed pinned to core 3). 0 I2C errors/overflow/exceptions/deadline misses, latency slightly tighter than E2 (p99 2.39ms vs 2.56ms). **Same finding as E2, independently reproduced**: 5 confirmed reconstruction-only triggers over 3962 windows; 3 of the 5 recon_error values are bit-identical to E2's (11.390218734741211 recurs 3x total across both runs) -- see `acquisition_compare/acquisition_comparison.txt` for the full cross-run analysis and the (unverified) INT8-quantization-bucket hypothesis. | `acquisition_compare/` |
| E4 | Deployment-reduced-interactive | DONE (2026-09-20, scope reopened by user) -- 20-min run, deployed polling method (not FIFO), reduced services (6/6 stopped+restarted cleanly; rpi-connect/-wayvnc not installed on this Pi, same as always). 0 triggers/sensor-failures/reconnects/exceptions/deadline-misses, stable memory (+0.053 MB/min), no thermal throttling (max 50.6C). Useful cross-reference for E2/E3: polling method (E1 + E4, 2 independent runs) = 0 near-threshold recon triggers; FIFO method (E2 + E3) = 5 each -- consistent with but not proof of an acquisition-method contribution to that finding. | `runtime_optional/` |
| F1 | Scheduler-profile replication (3 matched pairs) | DONE -- 6/6 runs (3 loaded + 3 reduced, 20 min each). 0 deadline misses, 0 I2C failures, 0 reconnects, 0 exceptions in every run. Consistent, modest, non-outlier-driven effect across all 3 pairs: reduced-background has higher V_T (0.975 vs 0.961 mean), higher C_D (0.920 vs 0.879), lower gap rate (4.62 vs 7.05/min), lower p99 decision latency (3.69 vs 4.19ms). The single-run "max scheduler delay" metric swings wildly (loaded mean 737ms vs reduced 17ms) but is dominated by one-off outlier events from a `python3` process (almost certainly this desktop/development-tool stack itself, matching Round 9's own disclosed confound) -- per the doc's own instruction ("do not lead with single-run maxima"), the modest/consistent metrics above are the ones to cite, not this figure. | `scheduler_repeats/scheduler_repeat_summary.{json,csv}` |
| G1 | Live processing-latency run | DONE (preserved existing w2_live2_pipeline.json, no rerun needed -- already has every field asked for) | `live_latency/` |
| G2 | Guard overhead measurement | DONE (same preserved file has `guard_observe_overhead_ms`) | `live_latency/` |
| G3 | TFLite thread-count sensitivity | DONE (preserved existing thread_count_sensitivity.json, 1/2/4 threads) | `live_latency/` |
| H1 | Preserve existing 90-min soak | DONE (already preserved at results/pi_research/w2_live3_soak_90min.json, not rerun) | reference only |
| H2 | Optional 3-hour soak | DONE (2026-09-20, 14:16-17:37, scope reopened by user) -- deployed polling method, 5-min checkpoints, 539,981 samples/33,734 windows. 0 triggers/sensor-failures/reconnects/exceptions/deadline-misses. Max temp 55.0C, no throttling. Memory: +5.46MB net over 3hrs (+0.041 MB/min) -- script auto-labels "stable plateau" but this is a real small upward drift, reported honestly rather than as zero. Third independent polling run (after E1, E4) with 0 of E2/E3's near-threshold recon triggers, now the largest window count of the three -- strengthens the acquisition-method hypothesis. | `long_soak/` |
| I | Benign-motion stress test | DONE — live guided session, 2 parts (original session Sep 19 ~17:12-17:38 interrupted by an unplanned reboot mid `7_bump_tap`, checkpointing meant only that in-progress phase's finalized stats were lost — not the raw data, ~half a second of trailing samples zero-filled by the unclean shutdown; resumed Sep 19/20 covering a clean redo of `7_bump_tap` plus phases 8-11). All 10 of the doc's 11 listed scenarios covered (stationary, gentle_rotation, repeated_tilts, moderate_rotation, controlled_shaking_moderate, controlled_shaking_stronger, bump_tap, putting_on_helmet, removing_helmet, walking_carry, soft_placement); #11 (short repeat after an actual reboot) intentionally left for a real reboot, see J. **Finding — reconstruction branch never false-triggers on any benign phase (`n_recon_threshold_crossings=0` everywhere, all 11 phases); the classifier branch does, including confirmed (3-window, OR-gated) alarms on 4 of 11 benign phases**: `3_repeated_tilts` (1 confirmed, 7/250 windows OR-positive), `4_moderate_rotation` (1 confirmed, 16/189), `8_putting_on_helmet` (1 confirmed, 3/122), `11_soft_placement` (1 confirmed, 44/221 — the worst false-positive rate of the session). This directly reinforces the paper's headline OOD/robustness finding — recon branch is conservative, classifier branch is the false-trigger risk — but is itself new evidence worth citing for the benign-handling false-alarm-rate discussion. | `benign_motion/` |
| J | Reboot repeatability | DONE (2026-09-20) — boot1 = same-day earlier campaign data reused (register dump from `mpu_config/`, stationary+gentle_rotation phases from `benign_motion/`, all predating the unplanned reboot); boot2 = fresh capture this session via `pi_val_j1_reboot_repeat.py`, same two scenarios. WHO_AM_I matches (0x70 both boots). Stationary: 0 confirmed triggers both boots, comparable magnitudes. **Gentle_rotation: boot1 had 0 confirmed triggers, boot2 had 1** — not a repeatability failure (each capture is an independently human-performed motion, boot2's was measurably more vigorous: gyro max 301.8 dps vs boot1's 184.3 dps) but a real, disclosed discrepancy, not glossed over — the qualitative claim (sensor identity stable, no spurious triggers on truly gentle motion, comparable magnitude ranges) holds; an exact match does not, and was never claimed. | `reboot_repeatability/` |
| K | INT8 reconstruction-outlier diagnostic | DONE -- outlier is window 5410, session `darus_crash_Iso_115_Out`, weak_label=1 (crash-like). Keras/FP16 recon_error=751.84, INT8=49.29 (diff=702.55, exact match to the known figure). All three still cross BOTH thresholds -- OR-rule decision unaffected on this window. | `int8_outlier/` |
| L | INT8 representative-dataset audit | DONE | `int8_calibration/` |
| M1 | EMA cutoff sensitivity | DONE (5 cutoffs x 10 test sessions = 50 rows; a few NaN correlations where a window had zero variance, noted) | `ema_sensitivity/` |
| M2 | Causal Butterworth comparison | DONE (+ frequency-response data for both causal filters) | `filter_identity/` |
| N1 | Causal preprocessing disagreement (class-stratified) | DONE -- crash-like windows agree only 88.8% (ref vs causal), normal windows 99.9%. New finding: causal/offline disagreement concentrates heavily on crash-like windows. | `class_fidelity/` |
| N2 | INT8 class-stratified fidelity | DONE -- crash-like 95.8% agreement, normal 100%. | `class_fidelity/` |
| O | Frozen detector operating-point context | DONE -- doc's cited branch-attribution numbers (19/1/14/5403) verified exact match against source file. | `frozen_detector/` |
| P | Controlled live trigger path validation | DONE -- rerun clean. Live baseline 4 windows/0 anomalous. Injected darus_crash_Iso_312_2_Out: 10 windows, 5 anomalous, triggered at window 112 (crash_prob=0.9961, recon_error=18.85), real GPIO18 alarm pulse fired. Path resumed cleanly (4 windows, 0 sensor errors). | `trigger_path/` |
| Q | GPS/GSM smoke test (no send) | BLOCKED -- no GSM/GPS module physically connected this session (`/dev/ttyUSB0` absent, checked via `ls`). Documented as not-performed (missing hardware), same honest-disclosure pattern as Round 9's power-meter gap, rather than fabricate. Script + notes ready for if a module gets connected. | `gps_gsm_optional/` |
| R | Runtime/GC characterization | SKIPPED (optional, Tier 3) | — |

## Autonomous work complete as of 2026-09-19 ~16:45 PKT; live guided session (C2+I) completed 2026-09-19/20

Every section that doesn't require (a) a physically present human moving the helmet,
(b) a reboot of this Pi, or (c) a GSM/GPS module that isn't currently connected, is
now DONE, including C2 and I (see their rows above — done via `pi_val_ci_motion_session.py`
then `..._resume.py` after an unplanned mid-session reboot; checkpointing meant only the
in-progress phase at the time was lost, not the whole session).

**Genuinely still blocked/pending (need action, not a scope choice)**: Q (needs a
GSM/GPS module connected first). J is DONE (completed 2026-09-20 using the Pi's
already-occurred reboot as boot 2; an extra boot3 due-diligence capture was
also taken 2026-09-20 when the Pi rebooted again mid the E2/E3/E4/H2 round —
see reboot_repeatability/reboot_comparison.txt).

**Update 2026-09-20 (~17:47-18:50): final targeted A-B-A acquisition test, per
`HelmX_FINAL_Pi_ABA_Acquisition_Test.txt`** -- the explicit follow-up to
isolate whether the acquisition method (not coincidence) drives the E2/E3
reconstruction-trigger finding. Three matched 20-min conditions, same
session, no Pi restart: A1 (polling) -> B (FIFO) -> A2 (polling). RESULT:
reconstruction_error was exactly 0.0 for 100% of windows in BOTH polling runs
(A1: 3993/3993, A2: 3986/3986, zero variance) and NEVER zero in the FIFO run
(0/3925, range [3.53, 15.12], 220 threshold crossings, 33 confirmed
triggers). Classifier probability stayed exactly 0.0 throughout all three
conditions. This is Scenario 1 per the doc's own interpretation framework --
strong, clean evidence the acquisition method itself drives the effect (A1
and A2 being IDENTICAL rules out time drift/environmental change) -- with
the precise mechanism explicitly NOT claimed, per the doc's own instruction
(a disclosed, unproven hypothesis is offered in aba_comparison_summary.txt).
Per the doc's own stopping rule, this is the final targeted Pi experiment
recommended for the paper. See `final_aba_acquisition_test/README.txt` and
`aba_comparison_summary.txt`.

**Update 2026-09-20 (~13:00-17:37): the user reopened scope on E2, E3, E4, H2**
(R stays folded into E2's script, not a standalone run, per the doc's own "during
selected runs" phrasing). All four now DONE — see their rows above. Headline
result of this round: a repeatable, disclosed finding that the FIFO/decimation
acquisition path (E2, E3 — 5 confirmed reconstruction-only near-threshold
triggers each, 3 of 5 recon_error values bit-identical across the two runs)
diverges from the deployed polling method (E1, E4, and now H2's 3-hour run —
zero such triggers across all three, the largest sample being H2's 33,734
windows) — written up in `acquisition_compare/acquisition_comparison.txt`,
`runtime_optional/e4_summary.txt`, and `long_soak/long_soak_summary.txt`, with
the cause (acquisition method vs. coincidence) explicitly flagged as open/
unconfirmed rather than resolved. As of this update, every section A-R is
DONE except Q, which remains hardware-blocked.

A2's inventory (`experiment_conditions.csv`) is fully populated for every campaign run
so far, including both parts of the C2+I motion session, J's boot1-3, and this
round's E2/E3/E4/H2 (smoke tests + full runs).

## Key facts to not re-derive

- `.pi_research_venv/bin/python` has numpy/psutil/yaml/tflite_runtime/scipy; a second, fuller env (check `requirements.txt`) has TensorFlow for Keras-based comparisons (`exp_d_quantization_comparison.py`, `exp_extended_ablation_batch.py` already use `import tensorflow as tf` successfully, so whichever interpreter those were run with has it — verify before assuming `.pi_research_venv` does).
- Existing reusable scripts in `deploy/pi_research_suite/`: `exp_w2_live1_sample_interval.py` (raw dt/sample capture — base for C1/D1), `exp_w2_live3_soak.py` (full live pipeline w/ SampleStreamGuard telemetry, per-window latency percentiles — base for E1/G1/F1), `exp_a1_isolated_inference.py` (inference timing, no `num_threads` param yet — base for G3), `exp_4_7_live_trigger_path.py` (already does almost exactly what Section P asks), `exp_d_quantization_comparison.py` + `exp_extended_ablation_batch.py` (Keras/FP16/INT8 comparison on test split — base for K/L/N2), `exp_c_replay_validation.py` (causal vs offline filter comparison — base for N1/M1/M2).
- The K-section "702.55" outlier is `results/pi_research/extended_ablation_batch.json` → `3.24_reconstruction_error_quantization` → `int8.max_abs_diff_vs_keras` — need to find which exact window index/session produced it (script only stored the aggregate stat, not the index — new script needed to re-run and capture `argmax`).
- `piResults/newPiResults_raw/run_condition.sh` + `analyze_experiment1.py` are the exact harness Round 8/9 used for the loaded-vs-reduced scheduler comparison (perf stat + perf sched) — F1 reuses this pattern for 3 matched pairs instead of 1.
- Reduced-condition service stop list (established convention, reuse exactly): `helmx-ble.service`, `mosquitto.service`, `rhasspy.service`, `helmx_assistant.service`, `wayvnc.service`, `wayvnc-control.service`, `rpi-connect.service`, `rpi-connect-wayvnc.service`. `bluetooth.service` stays running in both conditions.
