# save as deploy/pi_research_suite/exp_a3_thermal.py and run:
#   python deploy/pi_research_suite/exp_a3_thermal.py --duration-min 30 --interval-s 8
import argparse, time, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

p = argparse.ArgumentParser()
p.add_argument("--duration-min", type=float, default=30.0)
p.add_argument("--interval-s", type=float, default=8.0)
args = p.parse_args()

samples = []
start = time.monotonic()
deadline = start + args.duration_min * 60.0
checkpoints = {10: None, 20: None, 30: None}  # minutes -> temp_c
while time.monotonic() < deadline:
    elapsed_min = (time.monotonic() - start) / 60.0
    temp = common.read_temp_c()
    samples.append({"elapsed_min": elapsed_min, "temp_c": temp})
    for cp in list(checkpoints):
        if checkpoints[cp] is None and elapsed_min >= cp:
            checkpoints[cp] = temp
    time.sleep(args.interval_s)

temps = [s["temp_c"] for s in samples if s["temp_c"] is not None]
throttled = common.read_throttled()
report = {
    "device": common.device_info(),
    "duration_min_requested": args.duration_min,
    "n_samples": len(samples),
    "initial_temp_c": temps[0] if temps else None,
    "mean_temp_c": sum(temps) / len(temps) if temps else None,
    "max_temp_c": max(temps) if temps else None,
    "temp_at_checkpoints_c": checkpoints,
    "throttling_status": throttled,
    "thermal_throttling_occurred": bool(throttled and (
        throttled["currently_throttled"] or throttled["throttling_occurred"]
        or throttled["arm_freq_capped_now"] or throttled["arm_freq_capped_occurred"]
    )) if throttled else None,
    "raw_samples": samples,
}
common.save_json(report, "a3_thermal")
print(report["initial_temp_c"], report["mean_temp_c"], report["max_temp_c"], report["temp_at_checkpoints_c"])
print("Throttling occurred:", report["thermal_throttling_occurred"])
