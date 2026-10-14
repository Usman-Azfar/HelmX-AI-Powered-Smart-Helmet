"""Generates IEEE-style publication figures from the results already collected
in piResults/results/generated/. Two figures (long-tail latency histogram, offline-
vs-real-time crash_prob scatter) need raw per-sample arrays that earlier
scripts only summarized -- this script recomputes those two lightweight
passes directly (both cheap: ~50k inferences, ~5.4k-window replay) rather
than modifying the original experiment scripts after the fact.

Output: piResults/figures/*.png (300 DPI) and *.pdf (vector, where practical).

Run on the Pi:
    python deploy/pi_research_suite/generate_figures.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import common

RESULTS = ROOT / "piResults" / "results" / "generated"
OUT = ROOT / "piResults" / "figures"
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


# ================================================================ Fig 1
# Isolated-inference latency headroom: median/p95/p99/max across
# experiments, log scale, against the 300ms stride budget.
print("Fig 1: latency headroom across experiments...")
a1 = load("a1_isolated_inference")
a1r = load("a1_isolated_inference_repeat_final")
longtail = load("a1_long_tail_latency")

groups = ["A1\n(n=5000)", "A1 repeat\n(n=5000)", "Long-tail\n(n=50000)"]
medians = [a1["across_repeats"]["median_ms_mean"], a1r["across_repeats"]["median_ms_mean"], longtail["median_ms"]]
p95s = [a1["across_repeats"]["p95_ms_mean"], a1r["across_repeats"]["p95_ms_mean"], longtail["p95_ms"]]
p99s = [a1["across_repeats"]["p99_ms_mean"], a1r["across_repeats"]["p99_ms_mean"], longtail["p99_ms"]]
maxs = [a1["across_repeats"]["max_ms_worst"], a1r["across_repeats"]["max_ms_worst"], longtail["max_ms"]]
budget = a1["stride_seconds"] * 1000.0

fig, ax = plt.subplots(figsize=SINGLE_COL)
x = np.arange(len(groups))
w = 0.2
ax.bar(x - 1.5 * w, medians, w, label="Median", color=COLORS["blue"])
ax.bar(x - 0.5 * w, p95s, w, label="p95", color=COLORS["skyblue"])
ax.bar(x + 0.5 * w, p99s, w, label="p99", color=COLORS["orange"])
ax.bar(x + 1.5 * w, maxs, w, label="Max", color=COLORS["gray"])
ax.axhline(budget, color=COLORS["black"], linestyle=":", linewidth=1.1)
ax.text(len(groups) - 0.55, budget * 1.15, "300 ms stride budget", fontsize=7, ha="right")
ax.set_yscale("log")
ax.set_ylabel("Per-inference latency (ms, log scale)")
ax.set_xticks(x)
ax.set_xticklabels(groups)
ax.set_ylim(0.1, 500)
ax.legend(ncol=2, loc="upper left")
ax.set_title("INT8 TFLite inference latency vs. 300 ms deployment budget", fontsize=9)
save(fig, "fig1_inference_latency_headroom")

# ================================================================ Fig 2
# Long-tail latency histogram (recomputed raw array -- earlier script
# only saved summary stats).
print("Fig 2: long-tail latency histogram (recomputing 50,000 raw samples)...")
import time
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

cfg = common.load_config()
interp = tflite.Interpreter(model_path=str(ROOT / cfg["model_path"]))
interp.allocate_tensors()
runner = interp.get_signature_runner()
rng = np.random.default_rng(42)
dummy_seq = np.zeros((1, 60, 6), dtype=np.float32)
dummy_aux = np.zeros((1, 7), dtype=np.float32)
runner(seq=dummy_seq, aux=dummy_aux)

N = 50000
lat = np.empty(N)
for i in range(N):
    seq = rng.normal(0, 1, size=(1, 60, 6)).astype(np.float32)
    aux = rng.normal(0, 1, size=(1, 7)).astype(np.float32)
    t0 = time.perf_counter()
    runner(seq=seq, aux=aux)
    lat[i] = (time.perf_counter() - t0) * 1000.0
np.save(OUT / "fig2_raw_latencies_ms.npy", lat)

fig, ax = plt.subplots(figsize=SINGLE_COL)
bins = np.logspace(np.log10(max(lat.min(), 0.05)), np.log10(lat.max() * 1.1), 60)
ax.hist(lat, bins=bins, color=COLORS["blue"], edgecolor="white", linewidth=0.3)
ax.set_xscale("log")
ax.set_yscale("log")
for thr, lbl, c in [(10, "10 ms", COLORS["orange"]), (100, "100 ms", COLORS["pink"]),
                     (300, "300 ms budget", COLORS["black"])]:
    ax.axvline(thr, color=c, linestyle=":", linewidth=1.0)
ax.set_xlabel("Per-inference latency (ms, log scale)")
ax.set_ylabel("Count (log scale)")
ax.set_title(f"Latency-tail distribution, n={N:,} inferences", fontsize=9)
ax.text(0.02, 0.95, f"p99={np.percentile(lat,99):.2f}ms  max={lat.max():.1f}ms",
        transform=ax.transAxes, fontsize=7, va="top")
save(fig, "fig2_long_tail_latency_histogram")

# ================================================================ Fig 3
# Thermal stability: sustained-load vs. idle-recovery curves.
print("Fig 3: thermal stability over time...")
therm_load = load("a3_thermal")
therm_idle = load("a3_thermal_recovery_curve")

fig, ax = plt.subplots(figsize=SINGLE_COL)
tl = therm_load["raw_samples"]
ti = therm_idle["raw_samples"]
ax.plot([s["elapsed_min"] for s in tl], [s["temp_c"] for s in tl],
        color=COLORS["orange"], label="Sustained inference load (30 min)", linewidth=1.0)
ax.plot([s["elapsed_min"] for s in ti], [s["temp_c"] for s in ti],
        color=COLORS["blue"], label="Idle, no load (12 min)", linewidth=1.0)
ax.set_xlabel("Elapsed time (minutes)")
ax.set_ylabel(r"CPU temperature ($^{\circ}$C)")
ax.set_ylim(45, 90)
ax.axhline(80, color=COLORS["black"], linestyle=":", linewidth=1.0)
ax.text(0.3, 82.5, "Pi 4 soft throttle limit (80$^{\\circ}$C)", fontsize=7)
ax.legend(loc="lower right")
ax.set_title("CPU temperature: sustained inference vs. idle", fontsize=9)
save(fig, "fig3_thermal_stability")

# ================================================================ Fig 4
# Experiment C: offline (zero-phase) vs. real-time (causal) crash_prob
# scatter -- recomputed to get raw per-window arrays.
print("Fig 4: offline-vs-real-time filter agreement scatter (recomputing)...")
import crash_monitor as cm
from src import io_loaders, preprocess, manifest, units

classifier_t, recon_t = cm.load_model_thresholds(cfg)
raw_sessions = io_loaders.load_all_sessions()
split_of = manifest.assign_splits(raw_sessions)
canon_by_id = {s.session_id: s for s in preprocess.canonicalize_all(raw_sessions)}
raw_test = [s for s in raw_sessions if split_of.get(s.session_id) == "test"]
model = cm.CrashModel(ROOT / cfg["model_path"], ROOT / cfg["normalizer_path"])

off_all, rt_all, label_all = [], [], []
for s in raw_test:
    canon = canon_by_id[s.session_id]
    ds = manifest.build_dataset([canon], {canon.session_id: "test"}, "test")
    if len(ds.y) == 0:
        continue
    off_p = [model.predict(ds.X_seq[i], ds.X_aux[i])[0] for i in range(len(ds.y))]

    df = units.gyro_to_deg_per_s(s.df, s.gyro_in_deg_per_s)
    gf = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
    scorer = cm.WindowScorer(cfg, model, gf)
    rt_p = []
    for row in df.itertuples():
        scorer.append([row.ax, row.ay, row.az, row.gx, row.gy, row.gz])
        r = scorer.try_score()
        if r is not None:
            rt_p.append(r["crash_prob"])

    n = min(len(off_p), len(rt_p))
    off_all.extend(off_p[:n]); rt_all.extend(rt_p[:n]); label_all.extend([s.label] * n)

off_arr, rt_arr, label_arr = np.array(off_all), np.array(rt_all), np.array(label_all)
np.savez(OUT / "fig4_raw_offline_vs_realtime.npz", offline=off_arr, realtime=rt_arr, label=label_arr)
corr = np.corrcoef(off_arr, rt_arr)[0, 1]

fig, ax = plt.subplots(figsize=SINGLE_COL)
mask0, mask1 = label_arr == 0, label_arr == 1
ax.scatter(off_arr[mask0], rt_arr[mask0], s=6, alpha=0.35, color=COLORS["blue"],
           label="Normal", edgecolors="none")
ax.scatter(off_arr[mask1], rt_arr[mask1], s=10, alpha=0.6, color=COLORS["orange"],
           label="Crash-like", edgecolors="none", marker="^")
ax.plot([0, 1], [0, 1], color=COLORS["black"], linestyle=":", linewidth=1.0, label="y = x")
ax.axvline(classifier_t, color=COLORS["gray"], linestyle="--", linewidth=0.8)
ax.axhline(classifier_t, color=COLORS["gray"], linestyle="--", linewidth=0.8)
ax.set_xlabel("Offline (zero-phase Butterworth) crash_prob")
ax.set_ylabel("Real-time (causal EMA) crash_prob")
ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
ax.legend(loc="upper left")
ax.set_title(f"Filter agreement, held-out test set (r={corr:.3f})", fontsize=9)
save(fig, "fig4_offline_vs_realtime_agreement")

# ================================================================ Fig 5
# Quantization comparison: size / latency / agreement, 3-panel.
print("Fig 5: quantization comparison (Keras/FP16/INT8)...")
dq = load("d_quantization_comparison")
fig, axes = plt.subplots(1, 3, figsize=WIDE)

names = ["Keras\n(float32)", "FP16", "INT8\n(deployed)"]
sizes_kb = [dq["keras"]["size_bytes"] / 1024, dq["fp16"]["size_bytes"] / 1024, dq["int8"]["size_bytes"] / 1024]
axes[0].bar(names, sizes_kb, color=[COLORS["gray"], COLORS["skyblue"], COLORS["blue"]])
axes[0].set_ylabel("Model size (KB)")
axes[0].set_title("(a) Size", fontsize=9)
for i, v in enumerate(sizes_kb):
    axes[0].text(i, v + 15, f"{v:.0f}", ha="center", fontsize=7)

lat_names = ["FP16", "INT8"]
medians = [dq["fp16"]["median_ms"], dq["int8"]["median_ms"]]
p95s = [dq["fp16"]["p95_ms"], dq["int8"]["p95_ms"]]
xw = np.arange(2)
axes[1].bar(xw - 0.18, medians, 0.35, label="Median", color=COLORS["blue"])
axes[1].bar(xw + 0.18, p95s, 0.35, label="p95", color=COLORS["orange"])
axes[1].set_xticks(xw); axes[1].set_xticklabels(lat_names)
axes[1].set_ylabel("Latency (ms)")
axes[1].set_title("(b) Latency", fontsize=9)
axes[1].legend(fontsize=7)

agree_05 = [dq["fp16"]["classification_agreement_vs_keras_at_0.5"] * 100,
            dq["int8"]["classification_agreement_vs_keras_at_0.5"] * 100]
agree_dep = [dq["fp16"]["classification_agreement_vs_keras_at_deployed_threshold"] * 100,
             dq["int8"]["classification_agreement_vs_keras_at_deployed_threshold"] * 100]
axes[2].bar(xw - 0.18, agree_05, 0.35, label="@0.5 threshold", color=COLORS["pink"])
axes[2].bar(xw + 0.18, agree_dep, 0.35, label="@deployed threshold", color=COLORS["green"])
axes[2].set_xticks(xw); axes[2].set_xticklabels(lat_names)
axes[2].set_ylabel("Agreement vs. Keras (%)", labelpad=2)
axes[2].set_ylim(85, 101)
axes[2].set_title("(c) Decision agreement", fontsize=9)
axes[2].legend(fontsize=7, loc="lower left")
axes[2].yaxis.set_tick_params(pad=2)

fig.subplots_adjust(wspace=0.45)
save(fig, "fig5_quantization_comparison")

# ================================================================ Fig 6
# Thread-count sensitivity.
print("Fig 6: thread-count sensitivity...")
tc = load("thread_count_sensitivity")
threads = ["1", "2", "4"]
fig, ax = plt.subplots(figsize=SINGLE_COL)
metrics = ["median_ms", "p95_ms", "max_ms"]
labels = ["Median", "p95", "Max"]
colors = [COLORS["blue"], COLORS["orange"], COLORS["gray"]]
x = np.arange(len(threads))
w = 0.25
for i, (m, lbl, c) in enumerate(zip(metrics, labels, colors)):
    vals = [tc[f"{t}_threads"][m] for t in threads]
    ax.bar(x + (i - 1) * w, vals, w, label=lbl, color=c)
ax.set_yscale("log")
ax.set_xticks(x); ax.set_xticklabels([f"{t} thread(s)" for t in threads])
ax.set_ylabel("Latency (ms, log scale)")
ax.legend(fontsize=7)
ax.set_title("TFLite thread-count sensitivity", fontsize=9)
save(fig, "fig6_thread_count_sensitivity")

# ================================================================ Fig 7
# Concurrent-load degradation.
print("Fig 7: concurrent CPU-load degradation...")
w0 = load("pi_benchmark_workers_0")
w1 = load("pi_benchmark_workers_1")
w2 = load("pi_benchmark_workers_2")
w3 = load("pi_benchmark_workers_3")

worker_counts = [0, 1, 2, 3]
concurrent_means = [
    w0["solo"]["latency"]["mean_ms"],
    w1["concurrent"]["latency"]["mean_ms"],
    w2["concurrent"]["latency"]["mean_ms"],
    w3["concurrent"]["latency"]["mean_ms"],
]
fig, ax = plt.subplots(figsize=SINGLE_COL)
ax.plot(worker_counts, concurrent_means, marker="o", color=COLORS["blue"], markersize=5)
ax.set_xlabel("Concurrent busy-loop workers")
ax.set_ylabel("Mean inference latency (ms)")
ax.set_xticks(worker_counts)
ax.set_title("Latency under simulated CPU contention", fontsize=9)
save(fig, "fig7_concurrent_load_degradation")

# ================================================================ Fig 8
# A5 trigger latency by source.
print("Fig 8: trigger-confirmation latency by source...")
a5 = load("a5_trigger_latency")
by_source = {}
for r in a5["per_session"]:
    if r["detected"]:
        by_source.setdefault(r["source"], []).append(r["synthetic_latency_s"])

fig, ax = plt.subplots(figsize=SINGLE_COL)
sources = sorted(by_source.keys())
data = [by_source[s] for s in sources]
bp = ax.boxplot(data, tick_labels=[s.replace("_", "-") for s in sources], patch_artist=True,
                 widths=0.5, medianprops=dict(color=COLORS["black"]))
for patch, c in zip(bp["boxes"], [COLORS["blue"], COLORS["orange"], COLORS["green"]]):
    patch.set_facecolor(c); patch.set_alpha(0.6)
ax.set_yscale("symlog", linthresh=1)
ax.set_ylim(0, 100)
ax.set_ylabel("Trigger confirmation latency (s, symlog scale)")
ax.set_title("Confirmation latency by crash-session source (n=35 detected)", fontsize=8.5)
for i, (s, d) in enumerate(zip(sources, data)):
    ax.text(i + 1, 0.15, f"n={len(d)}", ha="center", fontsize=7, color=COLORS["black"])
save(fig, "fig8_trigger_latency_by_source")

# ================================================================ Fig 9
# OR-rule branch contribution (window level).
print("Fig 9: OR-rule branch contribution...")
eab = load("extended_ablation_batch")
branch = eab["3.25_or_rule_branch_contribution_window_level"]
fig, ax = plt.subplots(figsize=(3.0, 2.55))
cats = ["Classifier\nonly", "Reconstruction\nonly", "Both", "Neither"]
vals = [branch["classifier_only_positive"], branch["reconstruction_only_positive"],
        branch["both_positive"], branch["neither"]]
colors9 = [COLORS["blue"], COLORS["orange"], COLORS["green"], COLORS["gray"]]
ax.bar(cats, vals, color=colors9)
ax.set_yscale("symlog", linthresh=1)
ax.set_ylabel("Windows (log scale)")
for i, v in enumerate(vals):
    ax.text(i, v * 1.15 if v > 0 else 0.5, str(v), ha="center", fontsize=7)
plt.setp(ax.get_xticklabels(), fontsize=7)
ax.set_title("OR-rule branch contribution\n(n=5,437 test windows)", fontsize=9)
save(fig, "fig9_or_rule_branch_contribution")

# ================================================================ Fig 10
# Loaded (full desktop/IDE/services) vs. headless (services stopped)
# long-tail latency comparison -- Final Things.txt's suggested experiment.
# The ORIGINAL loaded-condition raw JSON was overwritten in-place by the
# headless rerun (same filename) before this figure was written -- its
# summary numbers were already transcribed into piResults/ResultsFromPi.md
# at collection time and are hardcoded here from that record, not invented.
print("Fig 10: loaded vs. headless long-tail latency comparison...")
loaded = {
    "mean_ms": 0.9361458074174516, "median_ms": 0.7710039990342921,
    "p95_ms": 1.777779899566666, "p99_ms": 3.940116518970174,
    "p99_9_ms": 7.232069371839417, "max_ms": 256.7288299997017,
    "event_counts_exceeding_threshold": {">2ms": 1788, ">5ms": 297, ">10ms": 18,
                                          ">25ms": 9, ">50ms": 9, ">100ms": 3, ">300ms": 0},
}
headless = load("a1_long_tail_latency_headless")

fig, ax = plt.subplots(figsize=SINGLE_COL)
metric_keys = ["median_ms", "p95_ms", "p99_ms", "max_ms"]
metric_labels = ["Median", "p95", "p99", "Max"]
x = np.arange(len(metric_keys))
w = 0.32
loaded_vals = [loaded[k] for k in metric_keys]
headless_vals = [headless[k] for k in metric_keys]
ax.bar(x - w / 2, loaded_vals, w, label="Loaded (desktop+IDE+services)", color=COLORS["orange"])
ax.bar(x + w / 2, headless_vals, w, label="Headless (services stopped)", color=COLORS["blue"])
ax.set_yscale("log")
ax.set_xticks(x); ax.set_xticklabels(metric_labels)
ax.set_ylabel("Latency (ms, log scale)")
ax.legend(fontsize=7)
ax.set_title("Latency, loaded vs. reduced-background Pi (n=50,000 each)", fontsize=8.5)
for i, (lv, hv) in enumerate(zip(loaded_vals, headless_vals)):
    ax.text(i - w / 2, lv * 1.15, f"{lv:.2f}", ha="center", fontsize=6.5)
    ax.text(i + w / 2, hv * 1.15, f"{hv:.2f}", ha="center", fontsize=6.5)
save(fig, "fig10_loaded_vs_headless_latency")

print("\nAll figures written to", OUT)
