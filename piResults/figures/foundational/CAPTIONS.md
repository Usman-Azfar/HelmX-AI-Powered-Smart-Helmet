# Figure captions (IEEE style)

All figures: 300 DPI PNG + vector PDF, Liberation Serif (Times New Roman-metric-compatible),
single- or double-column IEEE width, Okabe–Ito colorblind-safe palette. Source data for every
figure is in `results/pi_research/`; generating script: `deploy/pi_research_suite/
generate_figures.py`. Two figures recompute their own raw arrays at generation time (noted below)
since the underlying experiment scripts only persisted summary statistics.

**Fig. 1.** `fig1_inference_latency_headroom` — INT8 TFLite per-inference latency (median, p95,
p99, max; log scale) for three independent measurement passes (original A1, a repeat of A1, and a
50,000-sample long-tail run) against the deployed 300 ms stride budget (dashed line). Demonstrates
that typical latency sits 2–3 orders of magnitude below budget, while flagging that rare outliers
approach the budget more closely than a single pass alone would suggest.

**Fig. 2.** `fig2_long_tail_latency_histogram` — Distribution of 50,000 individual INT8 inference
latencies (log–log histogram) with reference lines at 10 ms, 100 ms, and the 300 ms deployment
budget. p99 and maximum latency annotated. Raw latencies recomputed at figure-generation time
(`fig2_raw_latencies_ms.npy`, saved alongside).

**Fig. 3.** `fig3_thermal_stability` — Raspberry Pi 4 CPU temperature over time under sustained
INT8 inference at the deployed cadence (300 ms/window, 30 min) versus idle with no inference load
(12 min), against the Pi 4's documented soft-throttle temperature. No throttling event
(`vcgencmd get_throttled`) occurred in either condition.

**Fig. 4.** `fig4_offline_vs_realtime_agreement` — Per-window classifier probability (`crash_prob`)
under the offline zero-phase Butterworth gravity filter (training-time preprocessing) versus the
real-time causal EMA filter (`CausalGravityFilter`, the deployed approximation), held-out test
split (10 sessions, 5,437 windows; Pearson r annotated). Dashed gray lines mark the deployed
decision threshold on each axis; the identity line marks perfect agreement. Raw arrays recomputed
at figure-generation time (`fig4_raw_offline_vs_realtime.npz`, saved alongside).

**Fig. 5.** `fig5_quantization_comparison` — Keras (float32) vs. FP16 vs. INT8 (deployed) TFLite
export comparison on the same held-out test windows: (a) model artifact size; (b) per-inference
latency (median, p95); (c) classification agreement with the float32 Keras reference, evaluated
both at a neutral 0.5 probability threshold and at the model's actual deployed decision threshold.

**Fig. 6.** `fig6_thread_count_sensitivity` — INT8 TFLite inference latency (median, p95, max; log
scale) as a function of the interpreter's configured thread count (1, 2, 4; n=2,000 inferences
each). More threads reduce median latency slightly but substantially worsen tail latency for this
model size.

**Fig. 7.** `fig7_concurrent_load_degradation` — Mean INT8 inference latency under 0–3 concurrent
CPU-bound busy-loop worker processes, simulating contention from another always-on workload (e.g.,
a co-located driver-monitoring task). Not a substitute for profiling the real concurrent workload's
own CPU profile.

**Fig. 8.** `fig8_trigger_latency_by_source` — Distribution (box plot, symlog y-axis) of
first-anomalous-window-to-confirmed-trigger latency for 35 successfully detected crash-like
replayed sessions (of 36 total), grouped by data source. DaRUS crash-impact traces confirm at the
theoretical minimum (2 × stride = 0.6 s); staged fall/near-fall maneuvers show a longer, more
variable confirmation time due to a slower anomaly buildup.

**Fig. 9.** `fig9_or_rule_branch_contribution` — Number of held-out test windows (n=5,437, log
scale) for which each branch of the deployed OR-fusion decision rule (classifier threshold,
reconstruction-error threshold) independently or jointly exceeded its threshold.

**Fig. 10.** `fig10_loaded_vs_headless_latency` — INT8 inference latency (median, p95, p99, max;
log scale; n=50,000 each) measured under two background-load conditions on the same physical
device: "loaded" (full desktop session, IDE, and every helmet background service running
concurrently) versus "headless" (voice assistant, MQTT broker, BLE/environment sensor bridge, and
remote-desktop services stopped; window manager and IDE left running). Maximum observed latency
fell from 256.7 ms to 6.4 ms under reduced background load, supporting a scheduler-contention
explanation for the rare large-latency outliers observed elsewhere in this study.
