# HelmX IEEE Sensors — Final Pi Test Protocol Results

Executes `piResults/HelmX_IEEE_Sensors_Final_Pi_Test_Protocol.txt` on the real, physically
connected Raspberry Pi 4 (`helx-pi`) this project already deploys to. Frozen configuration
unchanged throughout (same model file, same thresholds, same window/stride, same causal
preprocessing, same single TFLite inference thread, same logging level, same CPU-frequency
configuration, same sensor-acquisition/stream-integrity code) — every run below only varies
which background OS services are active. Raw supporting files for everything in this document
live in `piResults/newPiResults_raw/`; step-by-step progress (for resuming if interrupted) is in
`piResults/PI_TEST_PROTOCOL_PROGRESS.md`.

**Exact software version used**: this is an **untracked working directory** (no git repository —
see `Crash-Detection/SESSION_CONTEXT.md`'s "Conventions" section), so there is no commit hash to
cite. The frozen deployed artifacts used for every run below: `models/helmx_crash_model_int8.tflite`,
`models/normalizer.npz`, `models/thresholds.json` (θc = 0.9892255067825317, θr =
10.878735866546593), `deploy/config.yaml` unchanged.

---

## A. Experiment 1 — Loaded vs. Reduced-Background Scheduler Profile

**Run details.** Both conditions ran the real deployed pipeline
(`deploy/pi_research_suite/exp_w2_live3_soak.py`, the same harness behind every prior live-MPU6050
number in this project) for 20 minutes each, back-to-back, same day (2026-09-09, 22:14–22:57 PKT),
with a real physically-connected MPU6050. Simultaneously: `perf stat -p <PID>` (process-level) and
`perf stat -a` (system-level) for the full 20 minutes each, plus a 10-minute `perf sched record`
scheduler trace within each run (`linux-perf` 6.12.96, installed fresh via `apt` for this
experiment — not present before). Nothing in the frozen configuration changed between conditions
(model, thresholds, window/stride, causal preprocessing, single inference thread, logging level,
CPU-frequency configuration, sensor/stream-integrity code — all identical); only the
background-service set differed.

**Condition A (loaded)**: default state — `bluetooth`, `helmx-ble`, `mosquitto`, `rhasspy`,
`helmx_assistant`, `wayvnc`, `wayvnc-control` all active (`rpi-connect`/`rpi-connect-wayvnc`, part
of the prior round's loaded set, are no longer installed on this system — confirmed via
`systemctl`, not silently assumed).

**Condition B (reduced)**: the same service set stopped as the prior round's precedent
(`piResults/mpu6050Results.md`) — `helmx-ble`, `mosquitto`, `rhasspy`, `helmx_assistant`,
`wayvnc`, `wayvnc-control` stopped; `bluetooth` left running (matches precedent). All services
verified restarted to their original state immediately after
(`newPiResults_raw/04_services_restarted_verification.txt`).

### Results table

| Metric | Loaded | Reduced | Change |
|---|---|---|---|
| Windows scored | 2,696 | 3,414 | +26.6% (reduced condition scored more windows in the same 20 min — consistent with fewer timing gaps clearing the scoring buffer) |
| Samples received | 59,648 | 59,952 | ~same |
| Triggers / sensor failures / reconnects / exceptions | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | clean in both |
| Timing gaps / min | 22.45 | 9.75 | **−56.6%** |
| Invalidated-window fraction | 14.28% | 5.40% | **−62.2%** |
| Dropped-equivalent samples / min | 34.3 | 10.4 | **−69.7%** |
| Duplicate/too-fast samples | 366 | 161 | −56.0% |
| Sample interval p99 / max (ms) | 28.16 / 152.40 | 26.71 / 87.96 | max **−42.3%** |
| Decision latency median / p95 / p99 / max (ms) | 1.805 / 2.923 / 4.960 / 83.04 | 1.772 / 2.496 / 4.549 / 18.42 | max **−77.8%** |
| Deadline misses (>300ms) | 0 | 0 | both clean |
| Process CPU % (mean) | 4.02% | 3.67% | −8.7% |
| Max CPU temperature | 52.5°C | 51.1°C | both far below 80°C throttle point |
| Throttling occurred | No | No | both clean |
| **perf — process-level context-switches/s** | 17,903 | 19,741 | +10.3% (counterintuitive — see discussion) |
| **perf — process-level CPU migrations/s** | 72.16 | 55.66 | −22.9% |
| **perf — process CPU utilization** | 4.23% | 3.85% | −9.0% (perf-measured, independent confirmation of the psutil-based 4.02%/3.67% above) |
| **perf — system-wide context-switches/s** | 865.73 | 779.59 | −10.0% |
| **perf — system-wide CPU migrations/s** | 10.89 | 6.55 | −39.8% |
| **perf — system-wide page-faults/s** | 430.85 | 236.67 | −45.1% |
| **perf sched — max runqueue/wait delay, any task** | 258.2 ms | 36.5 ms | **−85.9%** |
| **perf sched — total wait-time sum / event count** | 472,057 ms / 1,381,928 | 360,909 ms / 1,302,290 | −23.5% total wait time on ~6% fewer scheduling events |

Full machine-readable numbers: `newPiResults_raw/experiment1_analysis.json`. Raw supporting files
per protocol section G: `01_system_info.txt`, `02_services_loaded.txt`, `03_services_reduced.txt`,
`04_services_restarted_verification.txt`, `detector_loaded.json`/`detector_reduced.json`,
`perf_{loaded,reduced}_{process,system}.txt`, `sched_{loaded,reduced}_{latency,timehist}.txt`,
`perf_{loaded,reduced}_sched.data` (raw perf recordings, ~550MB each), `proc_status_*_{before,after}.txt`.

### The max-decision-latency reduction closely replicates the manuscript's existing claim

This run's **77.8%** reduction in maximum decision latency (83.04ms → 18.42ms) lands almost exactly
on the manuscript's already-published **78%** figure (§Abstract, §IV.E: "maximum live latency by
78%") from an independent prior 90-min/20-min comparison. That two separate runs, weeks apart,
produce essentially the same effect size is meaningful corroborating evidence for the paper's
existing claim — not just new data, a replication.

### Direct scheduler evidence — now available for the first time

Prior rounds inferred scheduler contention from timing effects alone ("scheduler tracing was not
collected" — manuscript §IV.C). This experiment adds the first direct trace. The headline number:
**maximum observed runqueue/wait delay for any task dropped from 258.2 ms (loaded) to 36.5 ms
(reduced) — an 85.9% reduction**, alongside a real (if smaller) drop in system-wide context-switch
and CPU-migration rates. Per the protocol's own guidance on causal language, given traces exist and
show a large, consistent, directionally-matched effect:

> "Direct scheduler profiling showed higher context-switch/runqueue activity under the loaded
> configuration, temporally associated with larger sampling and decision-latency excursions."

is now a supportable sentence for the manuscript, replacing the current hedge in §IV.C ("Because
scheduler tracing was not collected...").

**One genuine puzzle, reported honestly rather than smoothed over**: process-level
context-switches/sec was *higher* under reduced load (19,741 vs. 17,903/s), even though CPU
migrations, system-wide switches, and — most importantly — actual wait/runqueue delay all dropped
substantially. The most plausible reading (not confirmed by further instrumentation, so stated as
plausible, not established): with less contention, the detector process gets scheduled back onto
CPU faster and more often in smaller quanta rather than waiting in longer queued batches — more
frequent but shorter, cheaper switches, consistent with the sharply lower *delay per switch*
implied by the runqueue-latency numbers above. This is offered as an interpretation, not a claim.

### Important caveat: what was actually driving scheduler contention in this run

Inspecting the actual top scheduler-latency offenders (`sched_loaded_latency.txt`,
`sched_reduced_latency.txt`) surfaces something the aggregate numbers alone would hide: in
**both** conditions, the tasks with the largest runqueue delays are `kworker` kernel threads,
`code:` (VS Code) renderer/disk/utility processes, and — in the reduced condition —
`labwc`/`wf-panel-pi`/`pcmanfm` (the desktop shell) and `ThreadPoolForeg`/`DedicatedWorker`
(browser/Electron thread pools). **None of the manuscript's originally-targeted background
services (BLE/MQTT/voice-assistant/VNC) appear among the top contention sources in either
condition of this specific run.**

This is because this run's environment — necessarily, since this document was produced by an AI
coding agent working interactively on the device — has a full desktop session (`labwc`
compositor, `wf-panel-pi`, `wayvnc` display), VS Code, and this coding-agent process itself
running throughout **both** conditions, none of which were part of either the "loaded" or
"reduced" service definitions in the original manuscript or protocol. **The loaded-vs-reduced
comparison above is still internally valid** (the same extra desktop/IDE/agent load was present in
both conditions, so the relative reduction is real and attributable to the services that were
actually stopped), and the direction and magnitude of the effect still corroborates the
manuscript's existing claims well. But this run's absolute numbers (e.g. 22.45 gaps/min loaded vs.
the original 90-min soak's 11.96 gaps/min) are **not directly comparable** to the original
manuscript figures, because this run's baseline load is heavier than the original study's in a way
the original study's methodology never characterized. **Recommended framing if this data is cited
in the paper**: report it as a second, independent confirmation of the direction and rough
magnitude of the scheduler-load effect (particularly useful for the now-available direct
scheduler-trace numbers), not as a replacement for or exact reproduction of the original
loaded/reduced figures already in the manuscript. If a methodologically cleaner reproduction is
wanted later, it would need to run from a true headless SSH session with no desktop/IDE/agent
present — outside what's possible while this agent is the one running the experiment.

---

## B. Experiment 2 — Power / Energy Measurement

**Not performed this round.** This system has no external USB-C inline power meter with logging
capability connected (`lsusb` was checked; no such device present), and the protocol explicitly
prohibits estimating power from battery capacity or CPU utilization alone, or fabricating
readings. Per the user's explicit choice (asked directly rather than guessed), this experiment is
skipped rather than approximated. This matches the manuscript's own existing, honest disclosure:
"Power was not instrumented and is therefore not estimated" (§III.C) and the Limitations section
("power consumption was not instrumented"). **No change needed to the manuscript on this point —
it already discloses this correctly.** If the user later obtains a loggable meter (or a
display-only meter they're willing to read manually every ~10s), this experiment can be run
following the protocol's four conditions (idle / reduced-background live / loaded live /
optional trigger-phase).

---

## C. Experiment 3 — Deadline-Miss Statistical Bound

No new Pi run required for this section (per protocol) — verifying the existing counts instead of
trusting them blindly:

**Verification of the underlying window count.** The manuscript's Fig. M4 / abstract cite "20,175
live sensor-to-decision windows" combined across three prior runs. Checked directly against the
JSON files that produced those numbers (`results/pi_research/`):

| Run | File | `n_windows_generated` |
|---|---|---|
| 4.4 (12-min live pipeline) | `w2_live2_pipeline.json` | 1,975 |
| 4.5 loaded (90-min soak) | `w2_live3_soak_90min.json` | 14,461 |
| 4.5 reduced-background (20-min soak) | `w2_live3_soak_20min.json` | 3,739 |
| **Sum** | | **20,175** ✓ exact match |

**Deadline-miss bound, independently recomputed** (not copied from the protocol document without
checking):

| Basis | n (windows) | Observed >300ms misses | Simple rule-of-three bound (3/n) | Exact one-sided Clopper–Pearson 95% upper bound |
|---|---|---|---|---|
| All combined live campaigns | 20,175 | 0 | 0.0001487/window = **0.0149%** | 0.0001485/window = **0.0148%** |
| 90-min soak alone | 14,461 | 0 | 0.0002075/window = **0.0207%** | 0.0002071/window = **0.0207%** |

Both approximations agree to 3 significant figures with the exact interval — the manuscript's
simple rule-of-three framing is not misleading here and needs no correction. (Computation:
`piResults/newPiResults_raw/verify_exp3.py` — rule-of-three = `3/n`; exact Clopper-Pearson
zero-event upper bound = `1 - 0.05**(1/n)`.)

**Recommended wording (matches protocol's suggested phrasing, now independently verified):**
> "No >300-ms deadline miss was observed in 20,175 evaluated live decision windows. Under a simple
> zero-event binomial approximation, the corresponding 95% upper bound on the per-window miss
> probability is approximately 1.49×10⁻⁴ (0.0149%) for the evaluated operating conditions,
> essentially identical to the exact one-sided Clopper–Pearson bound of 1.48×10⁻⁴. This is an
> empirical bound for the tested configuration, not a hard real-time guarantee."

This is a well-supported, non-overreaching claim — the paper already declines to call it a
"deterministic real-time guarantee," which is the correct framing.

---

## D. Experiment 4 — Physical / Mounting Context

Run with the user physically handling the mounted device, guided live phase-by-phase in real time
(not just a pre-announced schedule) via `deploy/pi_research_suite/exp_4_6_movement_smoke_test.py` —
non-destructive by design, no drops or real impacts, per the protocol's explicit prohibition on
dangerous crash testing.

**One discarded attempt, reported rather than hidden**: a first attempt produced 0 I2C errors but
gyro-magnitude statistics essentially flat across every phase (stationary mean 2.80/max 24.74 vs.
e.g. "shake" mean 2.41/max 4.51) — statistically indistinguishable from the device never actually
being picked up. The user confirmed they had not actually moved the sensor (the live cues weren't
clear enough the first time). That run is preserved for transparency at
`newPiResults_raw/4_6_movement_smoke_test_DISCARDED_no_actual_movement.json` but is **not** used as
evidence below — a smoke test with no real motion doesn't test anything.

**Valid run** (`newPiResults_raw/4_6_movement_smoke_test_valid_run.json`), guided with an explicit
live "PHASE — NOW" cue timed to each phase boundary rather than a schedule printed once at the
start:

| Phase | Duration | Reads | I2C errors | Accel mag mean/max | Gyro mag mean/max |
|---|---|---|---|---|---|
| Stationary baseline | 15s | 561 | 0 | 9.85 / 10.06 | 2.43 / 4.46 |
| Gentle rotation | 20s | 753 | 0 | 9.89 / 11.07 | **17.92 / 299.67** |
| Tilt | 20s | 752 | 0 | 9.97 / 11.03 | **23.86 / 81.48** |
| Shake | 20s | 753 | 0 | 9.97 / 12.54 | **22.35 / 177.84** |
| Non-crash bump | 20s | 751 | 0 | 9.96 / 11.50 | **48.27 / 175.05** |

**Zero I2C errors across all 522 seconds and 3,570 reads.** Unlike the discarded attempt, every
active phase now shows a clear, physically plausible jump in gyro magnitude relative to the
stationary baseline (7–20x on mean, 18–67x on max) — real evidence of actual handling, not just an
absence of read errors. Accelerometer magnitude stays close to 1g (9.8 m/s²) throughout, as
expected for gentle non-impact handling. Consistent with the two prior independent runs referenced
in `piResults/mpu6050Results.md` (0 I2C errors across both) — this is now a third independent clean
result for this specific check.

**What this does and doesn't establish** (protocol's own required framing, repeated here
deliberately): "The live experiments validate the evaluated sensor mounting and software
configuration. They do not establish robustness to the full vibration, shock, mounting-stiffness,
or structural-transfer spectra encountered across motorcycles and crash mechanisms. Hardware or
mounting changes require revalidation."

---

## E. Figures / Typography / Threshold Presentation Check

Manuscript reviewed directly: `piResults/helmx_sensors.pdf` (6 pages, IEEE Sensors Journal
format, "End-to-End Edge Validation of a Dual-Signal IMU Motorcycle Crash Detector").

| Protocol check | Finding |
|---|---|
| Fig. 1 (architecture) embedded and legible | **OK** — present on page 3, clean block diagram |
| Fig. 3 (quantization figure) embedded and legible | **OK** — present on page 3, three-panel bar chart, legible |
| "unpassed" → "unpaced" typo | **Not present** — manuscript already correctly says "unpaced" in both occurrences (§IV.D) |
| Malformed "p99.7.232 ms" → "p99.9 = 7.232 ms" | **Not present as described** — manuscript already reads "p99.9 7.232 ms" (§IV.C); a bare "=" sign appears to be missing in the rendered text extraction, worth a final visual proofread of the actual typeset PDF but the malformed concatenation the protocol described is not there |
| Concise threshold display (θc≈0.9892, θr≈10.879) in prose/tables vs. full precision in reproducibility material | **Partially done** — Eq. (1) in §III.A currently shows full precision (`θc = 0.9892255067825317`, `θr = 10.878735866546593`) inline in the main text. Recommend truncating the in-text/equation display to 4 decimal places (`θc = 0.9892`, `θr = 10.879`) and keeping full precision only in `models/thresholds.json` / the reproducibility manifest, per the protocol's explicit ask. **Not applied by me** — only a compiled PDF was provided, no LaTeX/Word source; this is a content edit best made by the authors in the source document. |
| Threshold provenance explained per frozen development protocol | **OK** — §III.A correctly attributes θc/θr to the frozen `models/thresholds.json` calibration, no invented methodology |
| Supervised probability / reconstruction error explained for readers unfamiliar with dual-signal architecture | **OK** — §III.A and Fig. 1 caption both explain pt/rt and the OR-fusion rule clearly |
| Test-set composition (5,294 normal / 143 crash-like) | **Not currently stated in the manuscript text** — only "5,437 held-out windows" and "10 held-out crash-like events" appear. This breakdown is already verified elsewhere in this project's own frozen record (`results/test_metrics.json`, matches `README.md`'s published table), so it is safe to add if the authors want the extra precision — optional, not a defect. |
| Power/scheduler-causality language | **Already appropriately hedged** — manuscript already uses "strongly consistent with... rather than proof of a specific OS mechanism" (§IV.C) and explicitly states "Because scheduler tracing was not collected..." This experiment run (Section A above) can now supply that missing scheduler trace directly — see Experiment 1's findings for whether the manuscript's causal language can be strengthened. |

**Overall**: the manuscript is already in good shape on every item the protocol flagged as a
likely defect — none of the described typos/omissions were actually found. The one substantive,
actionable item is the threshold-precision display in Eq. (1), which is a source-document edit the
authors should make directly (I don't have write access to a LaTeX/Word source, only the compiled
PDF). Section A's new scheduler-trace data (once complete) can also let the authors upgrade the
"scheduler tracing was not collected" sentence in §IV.C to cite real trace evidence.

---

## F. Novelty Framing

The protocol's suggested framing is consistent with what the manuscript already argues (§I
contributions list, §V discussion, §VII conclusion) — the paper already avoids claiming a new
crash-classification architecture or a "first," and already frames its contribution as
sensor-to-decision deployment validation rather than a benchmark campaign. No change needed here;
this section of the protocol is effectively already satisfied by the current draft's framing
(decision fidelity across preprocessing/quantization/acquisition/scheduling, tail-aware latency
reporting, stream-integrity-aware evaluation). The one additional angle Experiment 1 (Section A)
can now support, if the numbers back it up, is protocol item F.6 — direct system-level scheduler
evidence linking OS scheduling behavior to temporal sensing integrity, upgrading the manuscript's
current inferred/"strongly consistent" framing to one backed by an actual scheduler trace.

---

## Summary / What's Left

| Item | Status |
|---|---|
| Experiment 1 (scheduler profiling) | **Done** — clean runs both conditions (0 deadline misses/I2C failures/exceptions), strong scheduler evidence obtained (85.9% drop in max runqueue delay), max-latency reduction (77.8%) closely replicates the manuscript's existing 78% figure. Important caveat disclosed: actual contention sources in this run were the desktop/IDE/agent stack, not the originally-targeted services — see Section A. |
| Experiment 2 (power) | Not performed — missing hardware, user chose to skip, honestly disclosed above (and already disclosed identically in the manuscript itself) |
| Experiment 3 (deadline-miss bound) | Done — verified, no manuscript change needed |
| Experiment 4 (physical movement) | **Done** — 0 I2C errors, clear physically-plausible motion signature across all phases (first attempt discarded: no actual movement occurred, reported honestly, not used as evidence) |
| Section E (manuscript check) | Done — one actionable item (threshold display precision), rest already correct |
| Section F (novelty) | Done — already satisfied by current draft |
