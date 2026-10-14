HelmX Final Pi Validation Campaign
====================================
Source requirements: piResults/HelmX_FInal_Pi_REqwuirements.md (sections A-X)
Started: 2026-09-19. Host: helx-pi, Raspberry Pi 4 Model B Rev 1.5, aarch64, kernel 6.12.96+rpt-rpi-v8.
See PROGRESS.md for the live per-section status table; this file summarizes findings as they land.

SCOPE AGREED WITH THE USER BEFORE STARTING
-------------------------------------------
- Section Q (GPS/GSM): run up to modem dispatch, do NOT actually send an SMS.
- Sections C2 (clipping) + I (benign-motion stress test): DONE (2026-09-19/20) via a
  live guided session, split across two script runs after an unplanned mid-session
  reboot (checkpointing preserved everything but the in-progress phase). See PROGRESS.md.
- Section J (reboot repeatability): deferred -- this coding session may itself be
  running on this Pi; user will trigger the actual reboots.
- H2 (3-hour soak), E2 (FIFO/DRDY acquisition), E3 (SCHED_FIFO/taskset variant):
  initially skipped (optional/heavy; user chose required + Tier 1-2 only), then
  scope was REOPENED 2026-09-20 and all four (plus E4, deployment-reduced-
  interactive) were run to completion -- see finding #15 below.
- Section R (runtime/GC characterization): folded into E2's script as extra
  fields on the same resource-sample stream (the doc asks for R "during
  selected runs," not as a standalone run) -- covered by finding #15.

FINDINGS SO FAR (most reviewer-relevant first)
-------------------------------------------------

1. MPU6050 WHO_AM_I reads 0x70, not the datasheet's 0x68 (Section B1).
   Register dump on this exact deployed sensor: WHO_AM_I = 0x70. This is the
   value associated with the MPU6500/ICM-2060x family, not a stock MPU6050 --
   the physically mounted "MPU6050" breakout may actually carry different (but
   likely pin/register-compatible) silicon. Everything else read back as expected
   (FIFO/interrupt off, accel +/-2g, gyro +/-250dps -- see mpu_config/). Worth a
   one-line manuscript disclosure; does not appear to affect any existing result
   since every prior experiment used this same physical device throughout.

2. No on-chip anti-aliasing: DLPF is OFF (Section B1+B2). SMPLRT_DIV=0,
   CONFIG(DLPF_CFG)=0 -- the sensor's internal output is a raw, unfiltered 8kHz;
   the deployed 50Hz rate exists ENTIRELY in the host-side Python pacing loop
   (monotonic deadline scheduling over blocking SMBus reads, not FIFO/interrupt-
   paced -- see mpu_config/acquisition_method.txt for the full mechanism
   breakdown). No hardware guarantee that two 20ms-apart host reads are evenly-
   spaced, physically distinct samples.

3. The deployed causal EMA gravity filter has substantially more error than a
   same-order causal Butterworth would (Section M2, NEW finding). Comparing
   three filters against the fixed offline zero-phase-Butterworth reference on
   all 10 test sessions: the deployed causal EMA at 0.3Hz has classifier MAE
   0.180 vs. the offline reference; a causal 2nd-order Butterworth at the SAME
   0.3Hz corner has MAE only 0.048 -- ~3.7x closer to the reference. This
   isolates the EMA's own approximation error from the unavoidable "any causal
   filter differs from a zero-phase one" effect -- most of the EMA's disagreement
   with the offline reference is the EMA choice specifically, not causality
   itself. See ema_sensitivity/ and filter_identity/ for full data +
   frequency-response curves.

4. EMA cutoff sensitivity (Section M1): classifier MAE vs. offline reference is
   fairly flat from 0.3-0.5Hz (0.176-0.180) but clearly worse at 0.1Hz (0.273) --
   the deployed 0.3Hz choice is not on a steep part of this curve, so it isn't
   unusually fragile to a small cutoff mis-tuning, but a much lower cutoff would
   measurably hurt fidelity. At the deployed 0.3Hz cutoff, per-session decision
   flip counts (causal vs. offline) are mostly 0, but two sessions show 5 and 13
   flipped windows out of ~hundreds -- see ema_sensitivity/ema_sensitivity.csv.

5. Causal-vs-offline disagreement concentrates heavily on crash-like windows
   (Section N1, NEW finding, class-stratified for the first time). Per-window
   agreement between the causal EMA(0.3Hz) pipeline and the offline zero-phase
   reference: 99.9% on normal windows (5288/5294 unchanged) vs only 88.8% on
   crash-like windows (102/143 unchanged, 16 flipped in one direction or the
   other). This makes sense (crash-like windows contain the fast transients
   the causal filter's phase lag most affects) but had never been measured
   class-stratified before this pass -- worth citing precisely rather than
   the previous session-level-only agreement figure.

6. INT8 quantization similarly disagrees more on crash-like windows (Section
   N2): 95.8% classifier-decision agreement with Keras on crash-like windows vs.
   100% on normal windows. Smaller effect than #5 but the same direction.

7. The known "702.55" INT8 reconstruction-error outlier is now fully identified
   (Section K): test-split window index 5410, session darus_crash_Iso_115_Out,
   a genuine crash-like window (not spurious/normal). Keras/FP16 recon_error
   751.84 vs. INT8's 49.29. Despite the huge absolute gap, all three model
   representations (Keras/FP16/INT8) still cross BOTH the classifier and
   reconstruction thresholds on this window -- the OR-rule decision is
   unaffected. Full tensor-level trace (per-layer min/max/saturation counts,
   preserve_all_tensors) in int8_outlier/int8_outlier_tensors.json for anyone
   who wants to localize exactly which op's quantization drives this.

8. Frozen detector branch attribution verified byte-exact against the doc's
   cited figures (Section O): classifier-only=19, reconstruction-only=1, both=14,
   neither=5403 (of 5437 test windows) -- confirms these numbers are still
   correct and traceable to results/pi_research/extended_ablation_batch.json.

9. Timing-load characterization (Section D1): 0 I2C failures and 0 timing gaps
   (>30ms) in all 3 conditions (minimal background / normal HelmX workload /
   heavier interactive workload w/ stress-ng --cpu 4 on this 4-core Pi), but
   jitter clearly increases under heavy CPU load even without crossing the gap
   threshold: p99 interval 2.30-2.87ms -> 5.37ms, max interval <12ms -> 27.82ms
   under stress-ng. These captures are deliberately UNPACED (back-to-back reads,
   ~520-555Hz achieved), matching this project's established convention from
   exp_w2_live1_sample_interval.py (raw sensor/library characterization is kept
   separate from the deployed 50Hz-PACED pipeline, which E1/F1/G1 cover) --
   because of this, D1's own V_T/C_D come out trivially 1.0 (no gaps possible
   at this read rate) and are not the interesting number here; see item 10.

10. V_T / Decision Coverage (Sections D2/D3) are only meaningful on the PACED
    pipeline, not D1's unpaced captures (see #9) -- computed by literally
    replaying each run's captured dt sequence through the real deployed
    SampleStreamGuard+WindowScorer state machine (not a separately-maintained
    formula). A smoke-test 1-minute paced run gave V_T=0.935, C_D=0.802,
    P(valid 90-sample confirmation opportunity)=0.664 -- genuinely informative
    numbers. The full F1 scheduler-repeat runs (paced, real gaps under measured
    load) are the primary source for this going forward; see coverage/ once
    those land.

SECTIONS SATISFIED BY PRESERVING EXISTING DATA RATHER THAN RERUNNING
-----------------------------------------------------------------------
- G1 (live processing-latency run) + G2 (guard overhead): results/pi_research/
  w2_live2_pipeline.json (2026-09-04, 12-min live run) already reports every
  field asked for (samples, scored/invalid windows, latency percentiles, guard
  overhead percentiles, CPU/RSS/temp) -- not rerun.
- G3 (TFLite thread-count sensitivity): results/pi_research/
  thread_count_sensitivity.json (2026-08-30, 1/2/4 threads) already covers this.
- H1 (90-min soak): results/pi_research/w2_live3_soak_90min.json, preserved,
  not rerun per the doc's own "do not rerun unless desired" instruction.
- E1 (baseline polling condition): satisfied by the preserved G1 run above plus
  F1's "loaded" condition runs (same deployed polling acquisition, matched
  duration) -- no separate standalone E1 capture, since E2 (its comparison
  partner) was explicitly skipped this pass.

11. F1 scheduler-profile replication, 3 matched pairs (Round 9 had only 1).
    0 deadline misses / I2C failures / reconnects / exceptions across all 6
    runs. Consistent, modest, non-outlier-driven effect: reduced-background
    has higher V_T (0.975 vs 0.961 mean), higher C_D (0.920 vs 0.879), lower
    gap rate (4.62 vs 7.05/min), lower p99 decision latency (3.69 vs 4.19ms) --
    all consistent in direction across every one of the 3 independent pairs.
    The "max scheduler delay" figure swings wildly (loaded mean 737ms vs
    reduced 17ms) but that's one-off outlier events from a python3 process
    (almost certainly this desktop/coding-agent stack, matching Round 9's own
    disclosed confound) -- per the doc's own instruction ("do not lead with
    single-run maxima"), cite the modest/consistent metrics above, not this.
    See scheduler_repeats/scheduler_repeat_summary.{json,csv}.

12. Section P rerun (controlled trigger-path validation): clean. Injected a
    real recorded DaRUS crash session (darus_crash_Iso_312_2_Out) through the
    live sensor's real WindowScorer/TriggerPolicy -- triggered at window 112,
    real GPIO18 alarm pulse fired, path resumed cleanly afterward with 0
    sensor errors. See trigger_path/.

13. Benign-motion false-trigger behavior differs sharply between the two branches
    (Sections C2+I, NEW finding, live guided session 2026-09-19/20). Across all
    11 benign scenarios (stationary, putting on/removing the helmet, gentle
    rotation, repeated tilts, moderate rotation, moderate/stronger controlled
    shaking, controlled bump/tap, walking-carry, soft placement): the
    RECONSTRUCTION branch never crosses its threshold on any benign phase
    (0/11). The CLASSIFIER branch does, including full 3-window OR-gated
    CONFIRMED alarms on 4/11 phases -- repeated_tilts (1 confirmed, 7/250
    windows OR-positive), moderate_rotation (1 confirmed, 16/189),
    putting_on_helmet (1 confirmed, 3/122), and soft_placement (1 confirmed,
    44/221 -- the worst rate of the session). This is independent, live-hardware
    evidence for the same asymmetry the offline OOD results already show
    (reconstruction branch generalizes/stays conservative; classifier branch is
    the false-positive risk) -- now demonstrated as a false-ALARM-rate result on
    real benign handling, not just an OOD-detection result. Per-axis clipping
    (C2, same session): accelerometer (+/-2g) essentially never clips under
    benign handling; the gyroscope (+/-250dps) clips measurably under vigorous
    handling -- up to 4.15% of samples in controlled_shaking_stronger/gy (28
    samples pinned at raw -32768, 35 at 32767 of 3034). See clipping/ and
    benign_motion/ (identical phase_*.json pairs in both).

    Session note: the original run was killed mid-phase-7 (bump_tap) by an
    unplanned Pi reboot; the checkpoint-per-phase design (added after an
    earlier run lost everything to a reboot) meant only that one phase's
    finalized stats were lost, plus <1s of trailing raw samples zero-filled by
    the unclean shutdown -- phases 1-6 were untouched. Resumed cleanly
    afterward (redid bump/tap, then phases 8-11) via
    pi_val_ci_motion_session_resume.py, a copy of the original script pointed
    at a separate raw CSV so the first session's raw data was never at risk of
    being overwritten. 0 I2C errors in the resumed session.

14. Reboot/reassembly repeatability (Section J1, DONE 2026-09-20). Boot 1 =
    same-day earlier campaign data reused (register dump, stationary +
    gentle_rotation phases, all predating the unplanned reboot). Boot 2 =
    fresh capture this session (pi_val_j1_reboot_repeat.py), same two
    scenarios. WHO_AM_I matches across boots (0x70). Stationary: 0 confirmed
    triggers both boots, comparable magnitude ranges. Gentle_rotation: boot1
    had 0 confirmed triggers, boot2 had 1 -- disclosed as a real discrepancy,
    not smoothed over: boot2's human-performed rotation was measurably more
    vigorous (gyro max 301.8 dps vs boot1's 184.3 dps), so this reads as
    motion-intensity variance between two independently-performed "gentle"
    repeats, not sensor/pipeline non-repeatability. The qualitative
    repeatability claim (stable sensor identity, no spurious triggers on
    truly gentle motion, comparable magnitude ranges) holds; bit-identical
    output was never the claim. See reboot_repeatability/reboot_comparison.txt.

15. FIFO/decimation acquisition path shows a repeatable, disclosed but
    UNCONFIRMED divergence from the deployed polling method (Sections E2, E3,
    E4, H2, NEW finding, scope reopened 2026-09-20). Two independent 20-min
    FIFO-based runs (E2: plain FIFO; E3: FIFO + SCHED_FIFO/taskset) each
    produced 5 confirmed (3-window OR-gated) triggers -- every one
    reconstruction-only (crash_prob=0.0 always), recon_error in [10.99, 13.35]
    against the deployed threshold of 10.8787 (1-23% over, i.e. marginal, not
    remotely comparable to a real crash's ~751 recon_error per finding #7).
    Three of the five recon_error values are BIT-IDENTICAL to float64
    precision between the two independent runs (11.390218734741211 recurs 3x
    total) -- a real repeatable pattern, not noise. By contrast, three
    independent runs on the deployed POLLING method under equally idle
    conditions -- E1 (1975 windows), E4 (3881 windows, reduced-interactive),
    and H2 (33,734 windows over 3 hours) -- show ZERO such crossings between
    them. Leading hypothesis (explicitly NOT verified): idle/stationary input
    is near-constant, and the INT8-quantized model maps it to a small finite
    set of output buckets, one of which sits just above threshold; whether
    the FIFO/decimation acquisition path is itself a contributing factor (vs.
    coincidence) has not been isolated and would need a same-duration polling
    rerun under identical conditions. See acquisition_compare/
    acquisition_comparison.txt, runtime_optional/e4_summary.txt, and
    long_soak/long_soak_summary.txt for the full cross-run analysis.
    H2 also gave a real (if small) memory-drift number worth citing precisely
    rather than accepting the harness's own "stable plateau" label at face
    value: +5.46 MB net over 3 hours (+0.041 MB/min) -- small enough not to be
    alarming over this duration, not proof of zero drift over longer runs.

16. An extra (third) reboot-cycle capture, "boot3" (2026-09-20), taken when the
    Pi rebooted again mid the E2/E3/E4/H2 round -- not a reopening of Section
    J itself (already satisfied by boot1/boot2), captured as due diligence
    before resuming. Register dump + 60s stationary phase only (non-
    interactive). Matched boot1/boot2 on every field: WHO_AM_I=0x70, ~9.9 m/s^2
    accel magnitude, ~2.4-2.5 deg/s static gyro bias, 0 I2C errors, 0 triggers.
    See reboot_repeatability/reboot_comparison.txt.

17. FINAL TARGETED TEST -- matched A-B-A acquisition-method isolation
    (2026-09-20, per HelmX_FINAL_Pi_ABA_Acquisition_Test.txt, the explicit
    follow-up recommended by finding #15 above). Three 20-min conditions,
    same session, no Pi restart, everything else held constant: A1
    (polling) -> B (FIFO) -> A2 (polling). RESULT, the clearest finding of
    this entire campaign: reconstruction_error was EXACTLY 0.0 for 100% of
    windows in BOTH polling runs (A1: 3993/3993, A2: 3986/3986 -- zero
    variance, not just low) and NEVER zero across any of B's 3925 windows
    (56 distinct values spanning [3.53, 15.12], 220 threshold crossings,
    33 confirmed triggers). Classifier probability was exactly 0.0 in all
    three conditions throughout -- purely a reconstruction-branch effect.
    A1 and A2 being IDENTICAL (not just similar) rules out time drift or
    gradual environmental/thermal change as the explanation. This is
    Scenario 1 of the doc's own interpretation framework: strong evidence
    the acquisition method itself drives the effect. The precise mechanism
    is explicitly NOT claimed (per the doc's own instruction) -- a
    disclosed, unproven hypothesis (raw ADC readings may repeat bit-exactly
    under true stillness at the polling path's single-shot 20ms cadence,
    while FIFO's higher native sampling rate preserves genuine sensor noise
    that survives decimation) is offered in
    final_aba_acquisition_test/aba_comparison_summary.txt, along with
    explicit claim limits (does not establish FIFO is unsafe, polling is
    superior, or any real-road conclusion). PER THE DOC'S OWN STOPPING RULE,
    this is the final targeted Pi experiment recommended for the current
    paper -- remaining work moves to manuscript/analysis, not more Pi tests.

STILL OPEN -- everything below needs a hardware decision
-------------------------------------------------------------------------------------------
- Q (GPS/GSM smoke test): BLOCKED, no GSM/GPS module currently connected
  (/dev/ttyUSB0 absent). Documented rather than faked -- see
  gps_gsm_optional/gps_gsm_smoke_test_notes.txt. Script ready
  (pi_val_q_gps_gsm_smoke_test.py) if a module gets connected. NOTE: Q is a
  Tier 3/optional item (Section U, #19) -- it is NOT one of Section X's 10
  "final stopping rule" requirements, all 10 of which are already satisfied
  (see below). Its absence does not block calling this campaign sufficient
  for the paper.
- A2 (experiment_conditions.csv): fully populated for every campaign run
  through this session (J boot1-3, and this round's E2/E3/E4/H2 smoke tests +
  full runs) -- would take one more row only if Q is ever unblocked.

C2, I, J, E2/E3/E4/H2/R, and now the final A-B-A acquisition-isolation test
are all DONE. Remaining: Q only (hardware-blocked, and optional per the
doc's own priority tiers). Per HelmX_FINAL_Pi_ABA_Acquisition_Test.txt's own
stopping rule, no further Pi experiments are recommended for the current
paper.

SECTION X "FINAL STOPPING RULE" CHECK -- all 10 items satisfied
-------------------------------------------------------------------------------------------
1. exact MPU6050 configuration -- B1 (mpu_config/)
2. clear acquisition/timestamp mechanism -- B2 (mpu_config/acquisition_method.txt)
3. stationary-noise + safe per-axis clipping evidence -- C1/C2 (stationary_noise/, clipping/)
4. preserved raw timestamp data for new runs -- D1-D3 (timing_loads/, coverage/)
5. acquisition-method comparison (polling vs FIFO/DRDY) -- E1/E2, now also E3/E4 (acquisition_compare/)
6. replicated scheduler comparison -- F1, 6/6 matched pairs (scheduler_repeats/)
7. class-stratified deployment fidelity -- N1/N2 (class_fidelity/)
8. clarified V_T + C_D -- D2/D3 (coverage/)
9. INT8 outlier/calibration characterization -- K/L (int8_outlier/, int8_calibration/)
10. frozen reproducibility archive -- A1 (frozen_artifacts/)
Per the doc's own stopping rule, the Pi-side campaign is sufficient for the
current paper as-is; nothing further is required unless a reviewer asks for a
new study, or Q's hardware (a GSM/GPS module) becomes available.

Raw scripts written for this campaign, in deploy/pi_research_suite/:
  pi_val_b1_register_dump.py, pi_val_c1_stationary_noise.py,
  pi_val_d1_timing_loads.py, pi_val_d2d3_coverage.py,
  pi_val_q_gps_gsm_smoke_test.py, exp_final_replay_analysis.py (K/L/M/N/O),
  exp_w2_live3_soak_raw_dt.py (F1's raw-dt-preserving soak variant).
