# Figure captions (IEEE style) — MPU6050 real-hardware results

All figures: 300 DPI PNG + vector PDF, Liberation Serif (Times New Roman-metric-compatible),
single- or double-column IEEE width, Okabe–Ito colorblind-safe palette — same conventions as
`piResults/figures/`. Source data: `results/pi_research/*.json`; generating script:
`deploy/pi_research_suite/generate_mpu6050_figures.py`. Underlying experiments and full narrative:
`piResults/mpu6050Results.md` (checklist items 4.1–4.8 / W2-LIVE-1/2/3). Two panels (Fig. M1b,
Fig. M3, both the 4.3 series) use numbers transcribed from `logs/crash_monitor.log` at collection
time, since that particular run predates a dedicated JSON output — noted in the script and here.

**Fig. M1.** `figM1_sample_interval_characterization` — MPU6050 read-timing characterization in
two regimes: (a) unpaced, back-to-back reads (4.2/W2-LIVE-1, n=108,892, 12 min) showing the
sensor+I2C bus's own achievable rate (151.2 Hz) with zero read failures; (b) paced dt distribution
(mean/p99/max, log scale) at the deployed 50 Hz target across four independent real live-pipeline
runs (4.3, 4.4, 4.5-loaded, 4.5-clean), all comfortably inside the 1 s gravity-filter reset
threshold (dotted line). Confirms the sensor has ample headroom above the deployed pacing
requirement in every condition tested.

**Fig. M2.** `figM2_resource_usage_idle_vs_active` — Process CPU, memory (RSS), and CPU
temperature: idle sensor-retry loop (pre-fix, MPU6050 not yet detected) versus real sustained
active inference with the sensor connected (4.3, 15 min). Real inference raises process CPU
~15× over the idle baseline but stays under 3% of one core; RSS is flat and stable in both
conditions (no leak); temperature is lower during active inference, consistent with ambient- not
compute-dominated thermal behavior documented throughout this project.

**Fig. M3.** `figM3_stream_guard_gap_rate` — `SampleStreamGuard` flagged-gap rate (per minute) and
invalidated-window percentage across four real live runs, none of which had any raw I2C read
failure. The clean-background run (4.5-clean, non-essential services stopped) shows both metrics
drop by roughly two-thirds relative to the loaded 90-minute soak (4.5), isolating Linux scheduler
contention — not sensor/I2C reliability — as the dominant driver of timing gaps.

**Fig. M4.** `figM4_live_pipeline_latency_headroom` — Per-window, complete real-sensor-to-decision
pipeline latency (median/p95/p99/max; log scale) for the three live runs with dedicated per-window
telemetry (4.4, 4.5-loaded, 4.5-clean; n=20,175 windows combined) against the deployed 300 ms
stride budget (dashed line). Zero deadline misses across every window in every run; even the
single worst observed window (82.9 ms, during the 90-minute loaded soak) lands ~3.6× inside
budget.

**Fig. M5.** `figM5_soak_90min_timeline` — Cumulative windows scored and maximum CPU temperature
over the full 90-minute live soak (4.5/W2-LIVE-3), checkpointed every 5 minutes. Throughput
accumulates linearly (no stalls or restarts) and temperature stays flat and far below the Pi 4's
80 °C soft-throttle limit for the entire run (0 deadline misses, 0 I2C failures, 0 exceptions, no
memory leak).

**Fig. M6.** `figM6_movement_smoke_test` — Acceleration and angular-rate magnitude (mean, max) by
labeled phase during real physical handling of the sensor (4.6, n=3,547 reads, 0 I2C errors, no
drops/impacts). Acceleration stays anchored near 1 g across all phases (orientation/angular motion
dominates over linear acceleration, as physically expected); gyro magnitude is clearly elevated in
every motion phase relative to the stationary baseline, with the single highest instantaneous
spike occurring during gentle rotation in this run.

**Fig. M7.** `figM7_live_trigger_validation` — `crash_prob` and `recon_error` for the 10 windows of
a real recorded DaRUS crash session safely injected into the live `WindowScorer`/`TriggerPolicy`
instances immediately following real live baseline sensor windows (4.7). Both signals cross their
deployed decision thresholds (dashed lines) together at the same window, and the 3-consecutive-
window `TriggerPolicy` rule correctly fires at injected index 111 (`crash_prob`=0.9961,
`recon_error`=19.44), after which a real GPIO18 alarm pulse was confirmed to fire.
