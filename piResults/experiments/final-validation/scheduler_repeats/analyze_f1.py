"""F1 aggregation: pulls detector JSON + perf outputs + D2/D3 coverage for all
3 matched loaded/reduced pairs into run-to-run mean/std/median/range tables,
per the doc's explicit ask ("Report run-to-run: mean, standard deviation,
median, range... Do not lead with single-run maxima."). Adapted from
piResults/newPiResults_raw/analyze_experiment1.py (Round 9's single-pair
version) to handle N pairs.
"""
import json
import re
import statistics
from pathlib import Path

RAW = Path(__file__).resolve().parent
PAIRS = [1, 2, 3]


def parse_perf_stat(path):
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
            rate_val, rate_unit = m.group(3), m.group(4)
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
    text = Path(path).read_text(errors="replace")
    max_delay = 0.0
    for line in text.splitlines():
        m = re.search(r"max:\s*([\d.]+)\s*ms", line)
        if m:
            max_delay = max(max_delay, float(m.group(1)))
    return {"max_delay_ms_any_task": max_delay}


def summarize_run(pair, cond):
    d = json.loads((RAW / f"run{pair}_{cond}_detector.json").read_text())
    cov = json.loads((RAW.parent / "coverage" / f"run{pair}_{cond}_coverage.json").read_text())
    lat = d["per_window_latency_ms"]
    guard = d["stream_guard_telemetry"]
    duration_min = d["config"]["actual_duration_min"]

    proc_perf = parse_perf_stat(RAW / f"run{pair}_{cond}_perf_process.txt")
    sys_perf = parse_perf_stat(RAW / f"run{pair}_{cond}_perf_system.txt")
    sched = parse_sched_latency(RAW / f"run{pair}_{cond}_sched_latency.txt")

    return {
        "pair": pair, "condition": cond, "duration_min": round(duration_min, 2),
        "windows_scored": d["n_windows_generated"],
        "gaps_per_min": round(guard["timing_gaps"] / duration_min, 2),
        "V_T": cov["temporal_validity"]["V_T"],
        "C_D": cov["decision_coverage"]["C_D"],
        "p_valid_90sample_confirmation": cov["p_valid_90_sample_confirmation_opportunity"],
        "dropped_equivalent_per_min": round(guard["suspected_dropped_samples"] / duration_min, 2),
        "decision_latency_p50_ms": lat["median_ms"], "decision_latency_p95_ms": lat["p95_ms"],
        "decision_latency_p99_ms": lat["p99_ms"], "decision_latency_max_ms": lat["max_ms"],
        "deadline_misses_gt_300ms": d["deadline_miss_count_gt_stride_budget"],
        "i2c_failures": d["n_sensor_read_failures"], "reconnects": d["n_reconnects"], "exceptions": d["n_exceptions"],
        "process_cpu_percent_mean": d["resources"]["process_cpu_percent"]["mean"],
        "max_temperature_c": d["max_temperature_c"],
        "context_switches_per_sec_system": sys_perf.get("context_switches_per_sec"),
        "cpu_migrations_per_sec_system": sys_perf.get("cpu_migrations_per_sec"),
        "page_faults_per_sec_system": sys_perf.get("page_faults_per_sec"),
        "process_context_switches": proc_perf.get("context_switches"),
        "process_cpu_migrations": proc_perf.get("cpu_migrations"),
        "process_page_faults": proc_perf.get("page_faults"),
        "sched_max_runqueue_delay_ms_any_task": sched.get("max_delay_ms_any_task"),
    }


def agg_stats(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"mean": None, "std": None, "median": None, "min": None, "max": None, "n": 0}
    return {
        "mean": statistics.mean(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0.0,
        "median": statistics.median(values),
        "min": min(values), "max": max(values), "n": len(values),
    }


def main():
    runs = {}
    for cond in ("loaded", "reduced"):
        runs[cond] = [summarize_run(p, cond) for p in PAIRS]

    metrics = ["gaps_per_min", "V_T", "C_D", "p_valid_90sample_confirmation", "dropped_equivalent_per_min",
               "decision_latency_p50_ms", "decision_latency_p95_ms", "decision_latency_p99_ms",
               "decision_latency_max_ms", "context_switches_per_sec_system", "cpu_migrations_per_sec_system",
               "page_faults_per_sec_system", "sched_max_runqueue_delay_ms_any_task", "process_cpu_percent_mean"]

    aggregate = {}
    for cond in ("loaded", "reduced"):
        aggregate[cond] = {m: agg_stats([r[m] for r in runs[cond]]) for m in metrics}
        aggregate[cond]["total_deadline_misses"] = sum(r["deadline_misses_gt_300ms"] for r in runs[cond])
        aggregate[cond]["total_i2c_failures"] = sum(r["i2c_failures"] for r in runs[cond])
        aggregate[cond]["total_reconnects"] = sum(r["reconnects"] for r in runs[cond])
        aggregate[cond]["total_exceptions"] = sum(r["exceptions"] for r in runs[cond])

    out = {
        "method": (
            "3 matched loaded/reduced pairs, 20 min each, run back-to-back (not interleaved -- "
            "single MPU6050, cannot parallelize). 'loaded'=all default HelmX services active "
            "(bluetooth, helmx-ble, mosquitto, rhasspy, helmx_assistant, wayvnc, wayvnc-control); "
            "'reduced'=those (except bluetooth) stopped. Desktop + VS Code + AI coding agent were "
            "active throughout ALL 6 runs (disclosed confound, consistent with Round 9's own finding "
            "that this stack -- not the targeted BLE/MQTT/voice-assistant services -- was the actual "
            "top scheduler-contention source in that round's single pair too)."
        ),
        "per_run": runs,
        "aggregate_by_condition": aggregate,
    }
    print(json.dumps(out, indent=2))
    (RAW / "scheduler_repeat_summary.json").write_text(json.dumps(out, indent=2))

    import csv
    with open(RAW / "scheduler_repeat_summary.csv", "w", newline="") as f:
        fieldnames = list(runs["loaded"][0].keys())
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for cond in ("loaded", "reduced"):
            for r in runs[cond]:
                w.writerow(r)
    print(f"\nWrote {RAW / 'scheduler_repeat_summary.json'} and .csv")


if __name__ == "__main__":
    main()
