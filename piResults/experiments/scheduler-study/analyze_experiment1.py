"""Experiment 1 analysis: pulls together the detector JSON reports and perf
outputs for both conditions (loaded / reduced) into the metrics table the
protocol's "PRIMARY ANALYSIS TO REPORT" section asks for. Run after both
conditions have finished:

    python3 analyze_experiment1.py
"""
import json
import re
from pathlib import Path

RAW = Path(__file__).resolve().parent


def parse_perf_stat(path):
    """Parses `perf stat -o <path>` plain-text output into a dict of
    {event_name: (value, unit, rate_per_sec_or_None)}."""
    text = Path(path).read_text()
    out = {"elapsed_s": None}
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^([\d,]+\.?\d*)\s+msec\s+task-clock", line)
        if m:
            out["task_clock_msec"] = float(m.group(1).replace(",", ""))
            continue
        m = re.match(r"^([\d,]+)\s+(context-switches|cpu-migrations|page-faults|cycles|instructions)\b.*?#\s*([\d,.]+)\s*(K/sec|/sec|GHz)?", line)
        if m:
            name = m.group(2).replace("-", "_")
            out[name] = int(m.group(1).replace(",", ""))
            rate_val = m.group(3)
            rate_unit = m.group(4)
            if rate_val and rate_unit in ("K/sec", "/sec"):
                rate = float(rate_val.replace(",", ""))
                if rate_unit == "K/sec":
                    rate *= 1000.0
                out[f"{name}_per_sec"] = rate
            continue
        m = re.match(r"^([\d.]+)\s+seconds time elapsed", line)
        if m:
            out["elapsed_s"] = float(m.group(1))
    return out


def parse_sched_latency(path):
    """Extracts the 'Total' summary row from `perf sched latency` output,
    if present, plus a coarse max-delay figure across all tasks."""
    text = Path(path).read_text(errors="replace")
    max_delay = 0.0
    total_line = None
    for line in text.splitlines():
        if line.strip().startswith("TOTAL:") or "Total" in line and "delay" not in line.lower():
            total_line = line.strip()
        m = re.search(r"max:\s*([\d.]+)\s*ms", line)
        if m:
            max_delay = max(max_delay, float(m.group(1)))
    return {"max_delay_ms_any_task": max_delay, "total_line": total_line}


def summarize_condition(name):
    d = json.loads((RAW / f"detector_{name}.json").read_text())
    lat = d["per_window_latency_ms"]
    guard = d["stream_guard_telemetry"]
    duration_s = d["config"]["actual_duration_min"] * 60.0
    duration_min = duration_s / 60.0

    proc_perf = parse_perf_stat(RAW / f"perf_{name}_process.txt")
    sys_perf = parse_perf_stat(RAW / f"perf_{name}_system.txt")
    sched = parse_sched_latency(RAW / f"sched_{name}_latency.txt")

    return {
        "condition": name,
        "duration_min": round(duration_min, 2),
        "windows_scored": d["n_windows_generated"],
        "samples_received": guard["samples_received"],
        "triggers": d["n_triggers"],
        "sensor_read_failures": d["n_sensor_read_failures"],
        "reconnects": d["n_reconnects"],
        "exceptions": d["n_exceptions"],
        "gaps_per_min": round(guard["timing_gaps"] / duration_min, 2),
        "invalidated_windows": guard["windows_invalidated"],
        # Matches the exact formula used by generate_mpu6050_figures.py for every
        # prior run's invalidated-window % (Fig M3 precedent): inv / (inv + scored).
        "invalid_fraction_pct": round(100.0 * guard["windows_invalidated"] / max(1, guard["windows_invalidated"] + guard["windows_scored"]), 2),
        "dropped_equivalent_samples": guard["suspected_dropped_samples"],
        "dropped_equivalent_per_min": round(guard["suspected_dropped_samples"] / duration_min, 2),
        "too_fast_samples": guard["duplicate_or_too_fast_samples"],
        "sample_interval_ms": {
            "p50": guard["sample_interval_p50_ms"], "p95": guard["sample_interval_p95_ms"],
            "p99": guard["sample_interval_p99_ms"], "max": guard["max_sample_interval_ms"],
        },
        "decision_latency_ms": {k: lat[k] for k in ("median_ms", "p95_ms", "p99_ms", "max_ms")},
        "deadline_misses_gt_300ms": d["deadline_miss_count_gt_stride_budget"],
        # NOTE: exp_w2_live3_soak.py's JSON report keeps only percentile summaries of
        # per-window latency, not the raw per-window array -- exact counts of windows
        # exceeding 10/25/50/100ms thresholds are therefore not directly recoverable
        # from this data. What IS exact: deadline_misses_gt_300ms above (the harness
        # computes that count directly from the raw array before discarding it) and
        # the percentile values themselves (e.g. p99 tells you at most ~1% of windows
        # exceeded that value, which upper-bounds -- does not exactly count -- windows
        # past nearby thresholds). No count is fabricated here.
        "process_cpu_percent_mean": d["resources"]["process_cpu_percent"]["mean"],
        "max_temperature_c": d["max_temperature_c"],
        "throttling_status": d["throttling_status"],
        "perf_process": {
            "task_clock_msec": proc_perf.get("task_clock_msec"),
            "context_switches": proc_perf.get("context_switches"),
            "context_switches_per_sec": proc_perf.get("context_switches_per_sec"),
            "cpu_migrations": proc_perf.get("cpu_migrations"),
            "cpu_migrations_per_sec": proc_perf.get("cpu_migrations_per_sec"),
            "page_faults": proc_perf.get("page_faults"),
            "cycles": proc_perf.get("cycles"),
            "instructions": proc_perf.get("instructions"),
            "process_cpu_utilization_pct": round(100.0 * proc_perf.get("task_clock_msec", 0) / (proc_perf.get("elapsed_s", 1) * 1000.0), 3) if proc_perf.get("elapsed_s") else None,
        },
        "perf_system": {
            "context_switches_per_sec": sys_perf.get("context_switches_per_sec"),
            "cpu_migrations_per_sec": sys_perf.get("cpu_migrations_per_sec"),
            "page_faults_per_sec": sys_perf.get("page_faults_per_sec"),
        },
        "sched_latency_summary": sched,
    }


def main():
    results = {}
    for cond in ("loaded", "reduced"):
        p = RAW / f"detector_{cond}.json"
        if not p.exists():
            print(f"SKIP {cond}: {p} not found yet")
            continue
        results[cond] = summarize_condition(cond)

    out_path = RAW / "experiment1_analysis.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Wrote {out_path}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
