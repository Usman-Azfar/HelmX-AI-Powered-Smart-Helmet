# Progress tracker — HelmX IEEE Sensors Final Pi Test Protocol

**Purpose**: resumability. If this Pi reboots/shuts down mid-run, read this file first to see
exactly what's done, what's in-flight, and what's left — don't re-run completed steps.

Source protocol: `piResults/HelmX_IEEE_Sensors_Final_Pi_Test_Protocol.txt`
Raw output files land in: `piResults/newPiResults_raw/`
Final write-up: `piResults/newPiResults.md` (created once all experiments finish)

Started: 2026-09-09.

## Status

| Step | Status | Notes |
|---|---|---|
| Recon (sudo/perf/sysstat/i2c/services availability) | DONE | passwordless sudo OK; perf/sysstat not installed but available via apt; MPU6050 at 0x68 confirmed; loaded services identified (bluetooth, helmx-ble, mosquitto, rhasspy/helmx_assistant, wayvnc, wayvnc-control, rpi-connect, rpi-connect-wayvnc) |
| Verify existing 20,175-window deadline-miss figure | DONE | 14461 (w2_live3_soak_90min) + 3739 (w2_live3_soak_20min, reduced) + 1975 (w2_live2_pipeline) = 20175. Matches protocol claim exactly. |
| Install linux-perf + sysstat | DONE | both installed via apt, perf sanity-checked (system-wide + sched record both work with sudo) |
| Exp 1 — system info snapshot (01_system_info.txt) | DONE | `piResults/newPiResults_raw/01_system_info.txt` |
| Exp 1 — Condition A (LOADED) detector run + perf | **DONE** (22:34:13 PKT) | Clean run: 0 deadline misses, 0 I2C failures, 0 exceptions, 0 reconnects, 0 triggers. 2,696 windows scored, gap rate 449 gaps/20min. perf process/system stats + 10-min sched trace all captured successfully. Files: `newPiResults_raw/detector_loaded.json`, `perf_loaded_process.txt`, `perf_loaded_system.txt`, `sched_loaded_latency.txt`, `sched_loaded_timehist.txt` (194MB), `perf_loaded_sched.data` (576MB raw). |
| Exp 1 — Condition B (REDUCED) detector run + perf | **DONE** (22:56:56 PKT) | Clean run: 0 deadline misses, 0 I2C failures, 0 exceptions. 3,414 windows scored, gap rate 9.75/min (vs loaded's 22.45/min). All services restarted and verified back to original state. |
| Exp 1 — restart stopped services after Condition B | **DONE** | verified in `04_services_restarted_verification.txt` and a live re-check — all back to `active` (helmx_assistant briefly `activating`, matches its pre-experiment baseline state too) |
| Exp 1 — analysis script | **DONE** | `newPiResults_raw/analyze_experiment1.py` run successfully, output in `experiment1_analysis.json` |
| Exp 1 — full write-up | **DONE** | Section A of `newPiResults.md` fully written, including an important honest caveat: actual top scheduler-contention sources in both conditions were the desktop/VS Code/Claude-Code-agent stack, not the originally-targeted BLE/MQTT/rhasspy services — disclosed prominently rather than glossed over. Max-latency reduction (77.8%) closely replicates the manuscript's existing 78% figure — good corroborating evidence. |
| `newPiResults.md` draft | **All sections A-F written.** Remaining: Experiment 4 (deferred per user), README.md update, final pass/cleanup. |
| Exp 2 — power measurement | BLOCKED | no loggable USB-C power meter detected (lsusb shows no such device). Asked user; awaiting hardware or manual-reading instructions. |
| Exp 3 — deadline-miss statistical bound | DONE (computation only) | numbers verified above; just needs writing up in newPiResults.md, no new Pi run required per protocol |
| Exp 4 — physical movement smoke test | **DONE** | First attempt discarded (user confirmed no actual movement happened — live cues weren't clear enough). Re-run with explicit real-time "PHASE — NOW" chat cues timed to each phase boundary: 0 I2C errors, clear motion signature (gyro mag 7-20x higher in active phases vs. stationary). Valid data: `newPiResults_raw/4_6_movement_smoke_test_valid_run.json`; discarded attempt kept for transparency at `4_6_movement_smoke_test_DISCARDED_no_actual_movement.json`. Write-up done in Section D of `newPiResults.md`. |
| Section E — figures/typography/threshold corrections | NOT STARTED | needs the actual paper PDF/manuscript, which hasn't been located yet — ask user for its path |
| Section F — novelty framing writeup | PENDING | pure writing task, do during final newPiResults.md write-up |
| newPiResults.md (full writeup) | **DONE** | all sections A-F written; Experiments 2 and 4 documented as not-performed/deferred with clear reasons, not silently skipped |
| README.md update | **DONE** | both `Crash-Detection/README.md` and the mirrored `piResults/README.md` (kept identical, matching established convention — verified with `diff`) updated with a new "IEEE Sensors final validation protocol" paragraph summarizing this round |

## Key facts to not re-derive

- Host: `helx-pi`, Raspberry Pi 4, `aarch64`, Debian 12 bookworm, kernel `6.12.96+rpt-rpi-v8`.
- Passwordless sudo available.
- MPU6050 confirmed present at I2C address 0x68 (`sudo i2cdetect -y 1`).
- `.pi_research_venv/bin/python` has all deps needed (numpy, psutil, yaml, tflite_runtime) — use this interpreter for every pi_research_suite script.
- Best existing harness for Experiment 1's "primary application log": `deploy/pi_research_suite/exp_w2_live3_soak.py --duration-min N` — runs the real deployed pipeline (real MPU6050 → SampleStreamGuard → causal gravity filter → windowing → INT8 inference → TriggerPolicy) and writes a JSON report to `results/pi_research/w2_live3_soak.json` (rename immediately after each run, it overwrites by default) with everything the protocol asks for: per-window latency percentiles, deadline-miss counts, gap/invalidated-window telemetry (`stream_guard_telemetry`), reconnects, exceptions, triggers, CPU%/RSS, temperature, throttling.
- Loaded-condition services (currently running by default): `bluetooth.service`, `helmx-ble.service`, `mosquitto.service`, `rhasspy.service`, `helmx_assistant.service`, `wayvnc.service`, `wayvnc-control.service`, `rpi-connect.service`, `rpi-connect-wayvnc.service`.
- Reduced-condition service set (precedent from `piResults/mpu6050Results.md`'s prior "clean" run — reuse exactly, per protocol's "use the same reduced-background service set used previously"): stop `helmx-ble.service`, `mosquitto.service`, `rhasspy.service`, `helmx_assistant.service`, `wayvnc.service`, `wayvnc-control.service`, `rpi-connect.service`, `rpi-connect-wayvnc.service`. `bluetooth.service` (base bluez daemon) stays running in both conditions — not part of the stopped set previously either.
- Note: stopping `helmx-ble.service` also kills a GPIO pulse-timing subprocess (`libgpiod_pulsein64` on GPIO22, ~12% CPU) spawned by that script — expected, documented in mpu6050Results.md.

## Open questions — ANSWERED (2026-09-09)

1. Experiment 2 (power): **user chose "skip for now"** — no external loggable power meter
   available. Do NOT fabricate power numbers. `newPiResults.md` should mark this experiment as
   **not performed this round (missing hardware)**, not silently omitted.
2. Experiment 4 (physical movement smoke test): **user chose "later — proceed with everything
   else first."** Come back to this once user is ready to physically handle the device. Not
   blocking the rest of the protocol.
3. Section E (manuscript fixes): **manuscript located at `piResults/helmx_sensors.pdf`.** Read it
   (it's a PDF, use the Read tool's page-range support) and apply protocol section E's checks
   once the main experiment write-up is done.
