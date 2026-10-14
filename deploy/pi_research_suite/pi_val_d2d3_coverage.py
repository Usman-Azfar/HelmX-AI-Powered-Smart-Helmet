"""HelmX_FInal_Pi_REqwuirements.md Sections D2 (Temporal Validity V_T + Decision
Coverage C_D) and D3 (contiguous valid-run distribution + confirmation-
survival probability), computed from a raw per-sample dt CSV (as written by
pi_val_c1_stationary_noise.py or pi_val_d1_timing_loads.py: a `dt_ms` column,
one row per sample-to-sample interval).

Rather than hand-deriving V_T/C_D from formulas, this REPLAYS the actual
captured dt sequence through the real deploy/crash_monitor.py
SampleStreamGuard + WindowScorer classes (with synthetic constant sensor
values -- WindowScorer's scoring/invalidation logic is purely sample-count/
timing-driven, never data-dependent, so this reproduces exactly what the
live deployed pipeline would have scored/invalidated for this exact timing
sequence) instead of a separately-maintained formula that could silently
drift from the real gating logic.

Run once per raw dt CSV:
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_d2d3_coverage.py \\
        --dt-csv piResults/results/final-validation/timing_loads/reduced_background_dt.csv \\
        --label reduced_background
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common
import crash_monitor as cm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dt-csv", required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    cfg = common.load_config()
    period_s = 1.0 / cfg["sensor"]["sample_rate_hz"]
    window_samples = cfg["sensor"]["window_samples"]
    stride_samples = cfg["sensor"]["stride_samples"]

    dt_ms = []
    with open(args.dt_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt_ms.append(float(row["dt_ms"]))
    dt_s = np.asarray(dt_ms, dtype=np.float64) / 1000.0
    n_samples = len(dt_s) + 1  # dt series has one fewer entry than sample count

    # --- Replay through the REAL guard/scorer state machine ---
    import logging
    logger = logging.getLogger("d2d3_replay")
    logger.setLevel(logging.ERROR)
    guard = cm.SampleStreamGuard(cfg["sensor"].get("timing_guard"), period_s, logger)
    scorer = cm.WindowScorer(cfg, model=None, gravity_filter=None)  # never calls try_score's model path here
    dummy_sample = [0.0] * 6

    t = 0.0
    guard.observe(t)  # first sample, dt=None
    scorer.new_samples += 1
    scorer.buffer.append(dummy_sample)
    if len(scorer.buffer) >= window_samples and scorer.new_samples >= stride_samples:
        scorer.new_samples = 0
        guard.record_window_scored()

    for dt in dt_s:
        t += dt
        gap_detected, _ = guard.observe(t)
        if gap_detected:
            scorer.buffer.clear()
            scorer.new_samples = 0
            guard.record_window_invalidated()
        else:
            scorer.buffer.append(dummy_sample)
            scorer.new_samples += 1
            if len(scorer.buffer) >= window_samples and scorer.new_samples >= stride_samples:
                scorer.new_samples = 0
                guard.record_window_scored()

    snap = guard.snapshot()
    n_scored = snap["windows_scored"]
    n_invalid = snap["windows_invalidated"]
    v_t = n_scored / (n_scored + n_invalid) if (n_scored + n_invalid) else None

    nominal_decision_positions = max(0, (n_samples - window_samples) // stride_samples + 1)
    c_d = n_scored / nominal_decision_positions if nominal_decision_positions else None

    # --- D3: contiguous valid-run distribution ---
    max_dt_s = cfg["sensor"]["timing_guard"]["max_dt_s"]
    gap_mask = dt_s > max_dt_s  # True = a gap occurred AFTER this sample (breaks the run)
    run_lengths = []
    current = 1  # first sample starts a run
    for is_gap in gap_mask:
        if is_gap:
            run_lengths.append(current)
            current = 1
        else:
            current += 1
    run_lengths.append(current)
    run_lengths = np.asarray(run_lengths, dtype=np.int64)
    run_seconds = run_lengths * period_s

    def frac_time_in_runs_ge(min_len):
        eligible = run_lengths[run_lengths >= min_len]
        return float(eligible.sum() / n_samples) if n_samples else None

    def p_confirmation_opportunity(win_len):
        # Number of valid win_len-sample start positions across all runs, over
        # the number of such positions if the whole stream were one run.
        n_positions_valid = int(sum(max(0, L - win_len + 1) for L in run_lengths))
        n_positions_total = max(0, n_samples - win_len + 1)
        return (n_positions_valid / n_positions_total) if n_positions_total else None

    report = {
        "label": args.label, "source_csv": args.dt_csv,
        "n_samples": n_samples,
        "temporal_validity": {
            "windows_scored": n_scored, "windows_invalidated": n_invalid, "V_T": v_t,
        },
        "decision_coverage": {
            "nominal_decision_positions": nominal_decision_positions,
            "scored_windows": n_scored,
            "invalidated_candidates": n_invalid,
            "never_formed_or_suppressed_positions": max(0, nominal_decision_positions - n_scored),
            "C_D": c_d,
        },
        "contiguous_valid_runs": {
            "n_runs": int(len(run_lengths)),
            "run_length_samples_p50": float(np.percentile(run_lengths, 50)),
            "run_length_samples_p95": float(np.percentile(run_lengths, 95)),
            "run_length_samples_p99": float(np.percentile(run_lengths, 99)),
            "run_length_samples_max": int(run_lengths.max()),
            "run_length_seconds_p50": float(np.percentile(run_seconds, 50)),
            "run_length_seconds_p95": float(np.percentile(run_seconds, 95)),
            "run_length_seconds_p99": float(np.percentile(run_seconds, 99)),
            "run_length_seconds_max": float(run_seconds.max()),
        },
        "fraction_of_time_in_runs_long_enough_for": {
            "one_60_sample_window": frac_time_in_runs_ge(window_samples),
            "one_75_sample_interval": frac_time_in_runs_ge(window_samples + stride_samples),
            "one_90_sample_3window_confirmation": frac_time_in_runs_ge(window_samples + 2 * stride_samples),
        },
        "p_valid_90_sample_confirmation_opportunity": p_confirmation_opportunity(window_samples + 2 * stride_samples),
        "method": (
            "V_T/C_D computed by replaying the captured dt sequence through the REAL "
            "deploy/crash_monitor.py SampleStreamGuard+WindowScorer state machine (synthetic sensor "
            "values -- scoring/invalidation is purely timing-driven). Contiguous-run analysis uses the "
            "same max_dt_s gap threshold as the deployed guard. '90-sample 3-window confirmation' "
            "approximates the real 3-consecutive-anomalous-window TriggerPolicy requirement as needing "
            "window_samples + 2*stride_samples=90 contiguous valid samples -- a necessary but not fully "
            "sufficient condition (it also requires all 3 windows to be classified anomalous, which is "
            "data-dependent and out of scope for this purely-timing analysis)."
        ),
    }

    print(json.dumps(report, indent=2))
    out_dir = common.ROOT / "piResults" / "results" / "final-validation" / "coverage"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.label}_coverage.json").write_text(json.dumps(report, indent=2))
    print(f"\nWrote {out_dir / (args.label + '_coverage.json')}")


if __name__ == "__main__":
    main()
