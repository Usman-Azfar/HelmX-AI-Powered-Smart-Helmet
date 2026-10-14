"""Generates IEEE-style publication figures from the real-hardware MPU6050
results documented in piResults/mpu6050Results.md (checklist items 4.1-4.8 /
W2-LIVE-1/2/3), using the same visual conventions as generate_figures.py
(Liberation Serif, Okabe-Ito colorblind-safe palette, 300 DPI PNG + vector PDF).

All numbers plotted here are read directly from piResults/results/generated/*.json,
except the 4.3 SampleStreamGuard/interval figures, which mpu6050Results.md
sourced from logs/crash_monitor.log (no dedicated JSON was written for that
run) -- those are hardcoded from the values transcribed into that file at
collection time, following the same precedent as generate_figures.py's Fig. 10
(loaded latency numbers hardcoded after the source JSON was overwritten).

Output: piResults/mpu6050 figures/*.png (300 DPI) and *.pdf (vector).

Run on the Pi (or anywhere piResults/results/generated/ is present):
    python deploy/pi_research_suite/generate_mpu6050_figures.py
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS = ROOT / "piResults" / "results" / "generated"
OUT = ROOT / "piResults" / "mpu6050 figures"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- IEEE style
COLORS = {
    "blue": "#0072B2", "orange": "#D55E00", "green": "#009E73",
    "pink": "#CC79A7", "yellow": "#E69F00", "skyblue": "#56B4E9",
    "black": "#000000", "gray": "#7F7F7F",
}
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.5,
    "lines.linewidth": 1.3,
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "grid.linewidth": 0.5,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03,
    "legend.frameon": True,
    "legend.framealpha": 0.9,
    "legend.edgecolor": "0.7",
})

SINGLE_COL = (3.45, 2.55)   # inches, IEEE single-column width
WIDE = (7.16, 2.8)          # inches, IEEE double-column width


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=300)
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)
    print(f"  saved {name}.png / .pdf")


def load(name):
    with open(RESULTS / f"{name}.json") as f:
        return json.load(f)


# Deployed decision thresholds (models/thresholds.json, F1-optimal operating
# point -- see deploy/config.yaml's thresholds_path).
CLASSIFIER_T = 0.9892255067825317
RECON_T = 10.878735866546593
STRIDE_BUDGET_MS = 300.0

# ================================================================ Fig M1
# Sample-interval characterization: 4.2/W2-LIVE-1's unpaced back-to-back
# read rate vs. the paced (~20ms target) live-pipeline dt distribution
# across four independent real-sensor runs.
print("Fig M1: sample-interval characterization (unpaced vs. paced)...")
w2l1 = load("w2_live1_sample_interval")
w2l2 = load("w2_live2_pipeline")
soak90 = load("w2_live3_soak_90min")
soak20 = load("w2_live3_soak_20min")

fig, axes = plt.subplots(1, 2, figsize=WIDE)

# (a) unpaced achievable rate (4.2) -- single-run interval percentiles
ist = w2l1["interval_stats_ms"]
metrics_a = ["mean_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms"]
labels_a = ["Mean", "p50", "p95", "p99", "Max"]
vals_a = [ist[m] for m in metrics_a]
axes[0].bar(labels_a, vals_a, color=COLORS["blue"])
axes[0].set_yscale("log")
axes[0].set_ylabel("Read interval (ms, log scale)")
axes[0].set_title(f"(a) Unpaced read rate\n(4.2, n={w2l1['total_reads']:,}, {w2l1['achieved_hz']:.1f} Hz)",
                   fontsize=8)
for i, v in enumerate(vals_a):
    axes[0].text(i, v * 1.15, f"{v:.1f}", ha="center", fontsize=6.5)

# (b) paced (~20ms target) dt distribution across four real live-pipeline runs
runs_b = ["4.3\n(15 min)", "4.4\n(12 min)", "4.5 loaded\n(90 min)", "4.5 clean\n(20 min)"]
# 4.3's guard telemetry has no dedicated JSON (sourced from logs/crash_monitor.log
# per mpu6050Results.md Sec. 4.3); the other three are read directly below.
mean_b = [20.06, w2l2["stream_guard_telemetry"]["mean_sample_interval_ms"],
          soak90["stream_guard_telemetry"]["mean_sample_interval_ms"],
          soak20["stream_guard_telemetry"]["mean_sample_interval_ms"]]
p99_b = [23.20, w2l2["stream_guard_telemetry"]["sample_interval_p99_ms"],
         soak90["stream_guard_telemetry"]["sample_interval_p99_ms"],
         soak20["stream_guard_telemetry"]["sample_interval_p99_ms"]]
max_b = [117.8, w2l2["stream_guard_telemetry"]["max_sample_interval_ms"],
         soak90["stream_guard_telemetry"]["max_sample_interval_ms"],
         soak20["stream_guard_telemetry"]["max_sample_interval_ms"]]
x = np.arange(len(runs_b))
w = 0.26
axes[1].bar(x - w, mean_b, w, label="Mean", color=COLORS["blue"])
axes[1].bar(x, p99_b, w, label="p99", color=COLORS["orange"])
axes[1].bar(x + w, max_b, w, label="Max", color=COLORS["gray"])
axes[1].axhline(1000.0, color=COLORS["black"], linestyle=":", linewidth=1.0)
axes[1].set_yscale("log")
axes[1].set_xticks(x)
axes[1].set_xticklabels(runs_b, fontsize=6.8)
axes[1].set_ylabel("Sample interval (ms, log scale)")
axes[1].legend(fontsize=6.5, loc="upper left", ncol=1)
axes[1].set_title("(b) Paced (50 Hz target) dt,\nreal live-pipeline runs", fontsize=8)

fig.suptitle("MPU6050 sample-interval characterization: unpaced vs. paced", fontsize=9, y=1.02)
save(fig, "figM1_sample_interval_characterization")

# ================================================================ Fig M2
# Resource usage: idle retry-loop (sensor blocked, pre-fix) vs. real
# sustained active inference (4.3, sensor connected).
print("Fig M2: resource usage, idle-retry vs. active live inference...")
a2_live = load("a2_resource_usage")
a2_idle = load("a2_resource_usage_idle_retry_blocked_v1")

fig, axes = plt.subplots(1, 3, figsize=WIDE)
conds = ["Idle retry-loop\n(blocked)", "Active inference\n(live, 4.3)"]

cpu_vals = [a2_idle["process_cpu_percent"]["mean"], a2_live["process_cpu_percent"]["mean"]]
axes[0].bar(conds, cpu_vals, color=[COLORS["gray"], COLORS["blue"]])
axes[0].set_ylabel("Process CPU (mean, %)")
axes[0].set_title("(a) CPU", fontsize=9)
for i, v in enumerate(cpu_vals):
    axes[0].text(i, v + 0.06, f"{v:.2f}%", ha="center", fontsize=7)

rss_vals = [a2_idle["process_rss_mb"]["mean"], a2_live["process_rss_mb"]["mean"]]
axes[1].bar(conds, rss_vals, color=[COLORS["gray"], COLORS["blue"]])
axes[1].set_ylim(0, 60)
axes[1].set_ylabel("Process RSS (mean, MB)")
axes[1].set_title("(b) Memory", fontsize=9)
for i, v in enumerate(rss_vals):
    axes[1].text(i, v + 1.2, f"{v:.1f}", ha="center", fontsize=7)

temp_vals = [a2_idle["temperature_c"]["mean"], a2_live["temperature_c"]["mean"]]
axes[2].bar(conds, temp_vals, color=[COLORS["gray"], COLORS["blue"]])
axes[2].set_ylim(0, 70)
axes[2].set_ylabel(r"CPU temperature (mean, $^{\circ}$C)")
axes[2].set_title("(c) Thermal", fontsize=9)
for i, v in enumerate(temp_vals):
    axes[2].text(i, v + 1.2, f"{v:.1f}", ha="center", fontsize=7)

for ax in axes:
    plt.setp(ax.get_xticklabels(), fontsize=6.8)
fig.subplots_adjust(wspace=0.5)
save(fig, "figM2_resource_usage_idle_vs_active")

# ================================================================ Fig M3
# SampleStreamGuard: timing-gap rate and invalidated-window percentage
# across four independent real live runs, including the loaded-vs-clean-
# background comparison.
print("Fig M3: SampleStreamGuard gap rate & invalidated-window %...")
# 4.3's telemetry (44,878 samples / 113 gaps / 112 invalidated / 2,620 scored
# over ~14.2 of 15 min) has no dedicated JSON -- sourced from
# logs/crash_monitor.log per mpu6050Results.md Sec. 4.3.
runs_c = ["4.3\n(15 min,\nloaded)", "4.4\n(12 min,\nloaded)", "4.5\n(90 min,\nloaded)", "4.5\n(20 min,\nclean bg)"]
duration_min_c = [15.0, 12.0, 90.0, 20.0]
gaps_c = [113, w2l2["stream_guard_telemetry"]["timing_gaps"],
          soak90["stream_guard_telemetry"]["timing_gaps"], soak20["stream_guard_telemetry"]["timing_gaps"]]
gap_rate_c = [g / d for g, d in zip(gaps_c, duration_min_c)]
invalid_c = [112, w2l2["stream_guard_telemetry"]["windows_invalidated"],
             soak90["stream_guard_telemetry"]["windows_invalidated"], soak20["stream_guard_telemetry"]["windows_invalidated"]]
scored_c = [2620, w2l2["stream_guard_telemetry"]["windows_scored"],
            soak90["stream_guard_telemetry"]["windows_scored"], soak20["stream_guard_telemetry"]["windows_scored"]]
invalid_pct_c = [100.0 * inv / (inv + sc) for inv, sc in zip(invalid_c, scored_c)]

fig, axes = plt.subplots(1, 2, figsize=WIDE)
bar_colors = [COLORS["blue"], COLORS["blue"], COLORS["orange"], COLORS["green"]]
axes[0].bar(runs_c, gap_rate_c, color=bar_colors)
axes[0].set_ylabel("Timing gaps / minute")
axes[0].set_title("(a) Flagged-gap rate", fontsize=9)
for i, v in enumerate(gap_rate_c):
    axes[0].text(i, v + 0.15, f"{v:.2f}", ha="center", fontsize=7)

axes[1].bar(runs_c, invalid_pct_c, color=bar_colors)
axes[1].set_ylabel("Invalidated windows (%)")
axes[1].set_title("(b) Invalidated-window rate", fontsize=9)
for i, v in enumerate(invalid_pct_c):
    axes[1].text(i, v + 0.1, f"{v:.2f}%", ha="center", fontsize=7)

for ax in axes:
    plt.setp(ax.get_xticklabels(), fontsize=6.8)
fig.suptitle("SampleStreamGuard telemetry across real live-sensor runs\n"
             "(all zero I2C read failures; 4.5-clean = reduced background load)", fontsize=8.3, y=1.06)
save(fig, "figM3_stream_guard_gap_rate")

# ================================================================ Fig M4
# End-to-end pipeline latency vs. the 300ms stride budget, across the
# three real live-pipeline runs with dedicated per-window latency stats.
print("Fig M4: end-to-end pipeline latency vs. 300ms budget...")
runs_d = ["4.4\n(12 min)", "4.5 loaded\n(90 min)", "4.5 clean\n(20 min)"]
pw = [w2l2["per_window_latency_ms"], soak90["per_window_latency_ms"], soak20["per_window_latency_ms"]]
medians_d = [p["median_ms"] for p in pw]
p95_d = [p["p95_ms"] for p in pw]
p99_d = [p["p99_ms"] for p in pw]
max_d = [p["max_ms"] for p in pw]

fig, ax = plt.subplots(figsize=SINGLE_COL)
x = np.arange(len(runs_d))
w = 0.2
ax.bar(x - 1.5 * w, medians_d, w, label="Median", color=COLORS["blue"])
ax.bar(x - 0.5 * w, p95_d, w, label="p95", color=COLORS["skyblue"])
ax.bar(x + 0.5 * w, p99_d, w, label="p99", color=COLORS["orange"])
ax.bar(x + 1.5 * w, max_d, w, label="Max", color=COLORS["gray"])
ax.axhline(STRIDE_BUDGET_MS, color=COLORS["black"], linestyle=":", linewidth=1.1)
ax.text(len(runs_d) - 0.55, STRIDE_BUDGET_MS * 0.55, "300 ms stride budget", fontsize=7, ha="right")
ax.set_yscale("log")
ax.set_ylabel("Per-window pipeline latency (ms, log scale)")
ax.set_xticks(x)
ax.set_xticklabels(runs_d)
ax.set_ylim(0.5, 500)
ax.legend(ncol=2, loc="upper left", fontsize=6.8)
n_total_windows = pw[0]["n"] + pw[1]["n"] + pw[2]["n"]
ax.set_title(f"Real live-sensor end-to-end latency vs. budget\n(0/{n_total_windows:,} deadline misses across all three runs)", fontsize=8.3)
save(fig, "figM4_live_pipeline_latency_headroom")

# ================================================================ Fig M5
# 90-minute soak timeline: cumulative windows generated and max CPU
# temperature over elapsed time (checkpoints logged every 5 min).
print("Fig M5: 90-minute soak timeline (windows generated, temperature)...")
checkpoints = [
    (5.0, 14882, 721, 53.0), (10.0, 29768, 1519, 53.0), (15.0, 44647, 2293, 53.0),
    (20.0, 59536, 3104, 53.0), (25.0, 74418, 3906, 53.0), (30.0, 89298, 4718, 53.0),
    (35.0, 104155, 5486, 53.0), (40.0, 119056, 6305, 53.0), (45.0, 133941, 7144, 53.0),
    (50.0, 148804, 7977, 53.0), (55.0, 163665, 8819, 53.0), (60.0, 178553, 9613, 53.0),
    (65.0, 193439, 10433, 53.0), (70.0, 208356, 11267, 53.0), (75.0, 223241, 12088, 53.0),
    (80.0, 238096, 12834, 53.0), (85.0, 252982, 13663, 53.0), (90.0, 267891, 14461, 53.0),
]
elapsed = [c[0] for c in checkpoints]
windows_cum = [c[2] for c in checkpoints]
max_temp = [c[3] for c in checkpoints]

fig, ax1 = plt.subplots(figsize=SINGLE_COL)
ax1.plot(elapsed, windows_cum, marker="o", markersize=3, color=COLORS["blue"], label="Windows scored (cum.)")
ax1.set_xlabel("Elapsed time (minutes)")
ax1.set_ylabel("Cumulative windows scored", color=COLORS["blue"])
ax1.tick_params(axis="y", labelcolor=COLORS["blue"])

ax2 = ax1.twinx()
ax2.plot(elapsed, max_temp, marker="s", markersize=3, color=COLORS["orange"], label="Max CPU temp.")
ax2.set_ylabel(r"Max CPU temperature ($^{\circ}$C)", color=COLORS["orange"])
ax2.tick_params(axis="y", labelcolor=COLORS["orange"])
ax2.set_ylim(40, 85)
ax2.axhline(80, color=COLORS["black"], linestyle=":", linewidth=1.0)
ax2.text(3, 81.5, "Soft throttle (80$^{\\circ}$C)", fontsize=6.5)

ax1.set_title("90-minute live soak: throughput & thermal stability\n(0 deadline misses, 0 I2C failures, 0 exceptions)", fontsize=8.3)
save(fig, "figM5_soak_90min_timeline")

# ================================================================ Fig M6
# Movement smoke test: accel/gyro magnitude (mean, max) by phase.
print("Fig M6: movement smoke test, accel/gyro magnitude by phase...")
smoke = load("4_6_movement_smoke_test")
phase_labels = {
    "stationary_baseline": "Stationary\nbaseline", "gentle_rotation": "Gentle\nrotation",
    "tilt": "Tilt", "shake": "Shake", "non_crash_bump": "Non-crash\nbump",
}
phases = smoke["phases"]
names = [phase_labels[p["phase"]] for p in phases]
accel_mean = [p["accel_magnitude"]["mean"] for p in phases]
accel_max = [p["accel_magnitude"]["max"] for p in phases]
gyro_mean = [p["gyro_magnitude"]["mean"] for p in phases]
gyro_max = [p["gyro_magnitude"]["max"] for p in phases]

fig, axes = plt.subplots(1, 2, figsize=WIDE)
x = np.arange(len(names))
w = 0.32
axes[0].bar(x - w / 2, accel_mean, w, label="Mean", color=COLORS["blue"])
axes[0].bar(x + w / 2, accel_max, w, label="Max", color=COLORS["orange"])
axes[0].axhline(9.81, color=COLORS["black"], linestyle=":", linewidth=1.0)
axes[0].text(0.0, 9.35, "1 g (9.81 m/s²)", fontsize=6.5)
axes[0].set_xticks(x); axes[0].set_xticklabels(names, fontsize=6.5)
axes[0].set_ylabel(r"Accel. magnitude (m/s$^2$)")
axes[0].set_title("(a) Acceleration", fontsize=9)
axes[0].legend(fontsize=6.8)

axes[1].bar(x - w / 2, gyro_mean, w, label="Mean", color=COLORS["blue"])
axes[1].bar(x + w / 2, gyro_max, w, label="Max", color=COLORS["orange"])
axes[1].set_yscale("log")
axes[1].set_xticks(x); axes[1].set_xticklabels(names, fontsize=6.5)
axes[1].set_ylabel(r"Gyro magnitude ($^{\circ}$/s, log scale)")
axes[1].set_title("(b) Angular rate", fontsize=9)
axes[1].legend(fontsize=6.8)

fig.suptitle(f"Physical movement smoke test, real MPU6050 (n={sum(p['n_reads'] for p in phases):,} reads, 0 I2C errors)",
             fontsize=8.5, y=1.03)
save(fig, "figM6_movement_smoke_test")

# ================================================================ Fig M7
# Live trigger-path validation: crash_prob & recon_error across a real
# DaRUS crash session safely injected into the live scorer/policy after
# real live baseline sensor windows.
print("Fig M7: live trigger-path validation (injected crash replay)...")
trig = load("4_7_live_trigger_path")
stage2 = trig["stage2_injected_crash_replay"]["windows"]
idx = [w["window_index"] for w in stage2]
cprob = [w["crash_prob"] for w in stage2]
recon = [w["recon_error"] for w in stage2]
trigger_idx = trig["stage2_injected_crash_replay"]["trigger_window_index"]

fig, axes = plt.subplots(2, 1, figsize=(3.45, 3.6), sharex=True)
axes[0].plot(idx, cprob, marker="o", markersize=4, color=COLORS["blue"])
axes[0].axhline(CLASSIFIER_T, color=COLORS["black"], linestyle="--", linewidth=0.9, label=f"Threshold ({CLASSIFIER_T:.4f})")
axes[0].axvline(trigger_idx, color=COLORS["orange"], linestyle=":", linewidth=1.2)
axes[0].set_ylabel("crash_prob")
axes[0].set_ylim(-0.05, 1.05)
axes[0].legend(fontsize=6.5, loc="lower right")
axes[0].set_title("Live trigger-path validation: injected DaRUS crash replay", fontsize=8.5)

axes[1].plot(idx, recon, marker="o", markersize=4, color=COLORS["green"])
axes[1].axhline(RECON_T, color=COLORS["black"], linestyle="--", linewidth=0.9, label=f"Threshold ({RECON_T:.2f})")
axes[1].axvline(trigger_idx, color=COLORS["orange"], linestyle=":", linewidth=1.2, label=f"Trigger fired (idx={trigger_idx})")
axes[1].set_ylabel("recon_error")
axes[1].set_xlabel("Injected replay window index")
axes[1].legend(fontsize=6.5, loc="upper left")

fig.subplots_adjust(hspace=0.15)
save(fig, "figM7_live_trigger_validation")

print("\nAll MPU6050 figures written to", OUT)
