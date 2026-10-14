"""HelmX_FInal_Pi_REqwuirements.md Section E2 -- FIFO-based acquisition
condition, compared against the deployed polling baseline (E1). Does NOT
change the trained model, thresholds, or decision policy -- only the
sensor-acquisition layer is different: instead of the deployed
mpu6050-library polling read (crash_monitor.read_sensor -> get_accel_data()/
get_gyro_data(), one on-demand I2C transaction per sample, host-loop-paced),
this configures the MPU6050's hardware FIFO so the sensor itself buffers
samples; the host drains whatever's accumulated every ~20-30ms via burst
reads instead of one polled transaction per 20ms tick.

DISCLOSED FINDING (calibration, before the real run): B1 already found
WHO_AM_I=0x70 -- this is a genuine MPU6500, not the classic MPU6050 the
textbook "Sample Rate = 8kHz / (1+SMPLRT_DIV)" formula assumes. With
SMPLRT_DIV=159 (which should give exactly 50Hz on a real MPU6050),
repeated isolated measurements gave inconsistent, much-higher native FIFO
push rates (390-700+ Hz across several calibration trials; FIFO_COUNT was
confirmed to plateau around ~512 bytes, well under the 1024-byte overflow
limit, so nothing is silently dropped -- this is a genuine higher native
push rate on this chip, not an overflow artifact, and not something this
script's B1-level register decode can fully explain). Rather than keep
guessing at undocumented registers for unfamiliar/mislabeled silicon, this
script calibrates the TRUE native push rate empirically at startup (a short
untimed drain-only pass) and decimates in software to the model's expected
50Hz before feeding samples to the scorer -- an honest, disclosed
workaround, not a hidden assumption. The achieved post-decimation rate is
measured and reported, not just assumed to have landed on exactly 50.0.

Baseline register state (B1, all zero: FIFO_EN=0x00, USER_CTRL=0x00,
SMPLRT_DIV=0x00) is restored at exit so this doesn't leave the device in a
different state for subsequent baseline/polling runs.

This also folds in Section R (optional system-process/runtime
characterization) as extra fields in the same resource-sample stream, since
R explicitly says "during selected runs" rather than asking for a dedicated
run of its own.

Run on the Pi:
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_e2_fifo_acquisition.py --duration-min 20
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_e2_fifo_acquisition.py --duration-min 0.3  # smoke test
"""
import argparse
import gc
import json
import struct
import sys
import threading
import time
from pathlib import Path

import numpy as np
import psutil
import smbus2

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common
import crash_monitor as cm

ACCEL_SENS_LSB_PER_G = 16384.0
GYRO_SENS_LSB_PER_DEG_S = 131.0
G_TO_MS2 = 9.80665

REG_SMPLRT_DIV = 0x19
REG_FIFO_EN = 0x23
REG_USER_CTRL = 0x6A
REG_FIFO_COUNT_H = 0x72
REG_FIFO_R_W = 0x74

TARGET_HZ = 50
SMPLRT_DIV_VALUE = 159  # textbook MPU6050 value for 50Hz; kept for disclosure even though it doesn't gate FIFO push on this chip
FIFO_EN_GYRO_ACCEL = 0x78  # XG_FIFO_EN|YG_FIFO_EN|ZG_FIFO_EN|ACCEL_FIFO_EN
BYTES_PER_SAMPLE = 12  # gyro xyz (6) + accel xyz (6), FIFO's fixed channel order
MAX_BLOCK_READ = 24  # 2 samples per I2C block read, safely under SMBus's 32-byte block limit
CALIBRATION_S = 2.0
POLL_INTERVAL_S = 0.03  # confirmed safe: FIFO_COUNT plateaus ~512/1024 bytes at this cadence, no overflow observed


def configure_fifo(bus, address):
    bus.write_byte_data(address, REG_SMPLRT_DIV, SMPLRT_DIV_VALUE)
    bus.write_byte_data(address, REG_USER_CTRL, 0x04)  # FIFO_RESET (self-clearing)
    time.sleep(0.01)
    bus.write_byte_data(address, REG_USER_CTRL, 0x40)  # FIFO_EN (master)
    bus.write_byte_data(address, REG_FIFO_EN, FIFO_EN_GYRO_ACCEL)


def restore_baseline_registers(bus, address):
    bus.write_byte_data(address, REG_FIFO_EN, 0x00)
    bus.write_byte_data(address, REG_USER_CTRL, 0x00)
    bus.write_byte_data(address, REG_SMPLRT_DIV, 0x00)


def read_fifo_count(bus, address):
    hi, lo = bus.read_i2c_block_data(address, REG_FIFO_COUNT_H, 2)
    return (hi << 8) | lo


def drain_fifo_bytes(bus, address, n_bytes):
    raw = bytearray()
    offset = 0
    while offset < n_bytes:
        chunk = min(MAX_BLOCK_READ, n_bytes - offset)
        raw += bytes(bus.read_i2c_block_data(address, REG_FIFO_R_W, chunk))
        offset += chunk
    return raw


def calibrate_native_rate(bus, address, duration_s):
    """Untimed (not counted against the requested run duration) drain-only
    pass to measure the true native FIFO push rate on this chip, since
    SMPLRT_DIV doesn't reliably predict it here (see module docstring)."""
    t0 = time.monotonic()
    deadline = t0 + duration_s
    n_samples = 0
    max_fc = 0
    while time.monotonic() < deadline:
        fc = read_fifo_count(bus, address)
        max_fc = max(max_fc, fc)
        if fc >= BYTES_PER_SAMPLE:
            nbytes = (fc // BYTES_PER_SAMPLE) * BYTES_PER_SAMPLE
            drain_fifo_bytes(bus, address, nbytes)
            n_samples += nbytes // BYTES_PER_SAMPLE
        time.sleep(POLL_INTERVAL_S)
    elapsed = time.monotonic() - t0
    native_hz = n_samples / elapsed if elapsed > 0 else 0.0
    return native_hz, max_fc


def proc_faults(pid):
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
        after = text.rsplit(")", 1)[1].split()
        minflt, majflt = int(after[7]), int(after[9])
        return minflt, majflt
    except (OSError, IndexError, ValueError):
        return None, None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--duration-min", type=float, default=20.0)
    p.add_argument("--label", default="e2_fifo_acquisition")
    p.add_argument("--sched-fifo-note", default=None,
                    help="If launched under chrt/taskset (Section E3), record what was applied.")
    args = p.parse_args()

    cfg = common.load_config()
    address = cfg["sensor"]["i2c_address"]
    bus = smbus2.SMBus(1)

    print(f"Configuring MPU6050/6500 FIFO: SMPLRT_DIV={SMPLRT_DIV_VALUE}, FIFO_EN=0x{FIFO_EN_GYRO_ACCEL:02X}")
    configure_fifo(bus, address)
    time.sleep(0.05)

    print(f"Calibrating true native FIFO push rate ({CALIBRATION_S}s, untimed, not counted in run duration)...")
    native_hz, max_fc_calib = calibrate_native_rate(bus, address, CALIBRATION_S)
    decimation_n = max(1, round(native_hz / TARGET_HZ))
    print(f"Calibration: native_hz={native_hz:.1f}, max_fifo_bytes_seen={max_fc_calib} (no overflow if <1024), "
          f"decimation_n={decimation_n}")

    classifier_t, recon_t = cm.load_model_thresholds(cfg)
    model = cm.CrashModel(common.ROOT / cfg["model_path"], common.ROOT / cfg["normalizer_path"])
    gravity_filter = cm.CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], cfg["sensor"]["sample_rate_hz"])
    scorer = cm.WindowScorer(cfg, model, gravity_filter)
    policy = cm.TriggerPolicy(classifier_t, recon_t, cfg["thresholds"]["consecutive_windows"],
                               cfg["thresholds"]["cooldown_seconds"])

    proc = psutil.Process()
    proc.cpu_percent(interval=None)
    gc_stats_start = gc.get_stats()

    duration_s = args.duration_min * 60.0
    start = time.monotonic()
    deadline = start + duration_s
    next_resource_sample = time.monotonic()

    n_raw_samples = 0       # every sample drained from the FIFO, pre-decimation
    n_fed_samples = 0       # samples actually kept (post-decimation) and fed to the scorer
    decim_counter = 0
    n_windows = 0
    n_triggers = 0
    n_i2c_errors = 0
    n_fifo_overflow_suspected = 0
    exceptions = []
    trigger_events = []
    window_latencies_ms = []
    resource_samples = []
    batch_sizes = []
    batch_drain_intervals_s = []
    last_drain_t = None

    print(f"FIFO acquisition running for {args.duration_min} min (decimating every {decimation_n}th sample to ~{TARGET_HZ}Hz)...",
          flush=True)
    while time.monotonic() < deadline:
        try:
            fifo_count = read_fifo_count(bus, address)
        except OSError:
            n_i2c_errors += 1
            time.sleep(POLL_INTERVAL_S)
            continue

        if fifo_count >= BYTES_PER_SAMPLE:
            if fifo_count > 1000:
                n_fifo_overflow_suspected += 1
            n_bytes_to_read = (fifo_count // BYTES_PER_SAMPLE) * BYTES_PER_SAMPLE
            now = time.monotonic()
            if last_drain_t is not None:
                batch_drain_intervals_s.append(now - last_drain_t)
            last_drain_t = now
            batch_sizes.append(n_bytes_to_read // BYTES_PER_SAMPLE)

            try:
                raw_bytes = drain_fifo_bytes(bus, address, n_bytes_to_read)
            except OSError:
                n_i2c_errors += 1
                continue

            for i in range(0, len(raw_bytes), BYTES_PER_SAMPLE):
                # Actual MPU6050/6500 FIFO packet order is accel (6 bytes) followed by gyro (6 bytes),
                # not gyro-first. Decoding as gyro-first caused the stationary FIFO sanity check to
                # appear as large rail-like motion because acceleration raw values were being treated as gyro.
                ax_r, ay_r, az_r, gx_r, gy_r, gz_r = struct.unpack(">hhhhhh", raw_bytes[i:i + BYTES_PER_SAMPLE])
                n_raw_samples += 1
                decim_counter += 1
                if decim_counter < decimation_n:
                    continue
                decim_counter = 0

                ax = (ax_r / ACCEL_SENS_LSB_PER_G) * G_TO_MS2
                ay = (ay_r / ACCEL_SENS_LSB_PER_G) * G_TO_MS2
                az = (az_r / ACCEL_SENS_LSB_PER_G) * G_TO_MS2
                gx = gx_r / GYRO_SENS_LSB_PER_DEG_S
                gy = gy_r / GYRO_SENS_LSB_PER_DEG_S
                gz = gz_r / GYRO_SENS_LSB_PER_DEG_S
                n_fed_samples += 1
                try:
                    scorer.append([ax, ay, az, gx, gy, gz])
                except Exception as e:
                    exceptions.append({"t_elapsed_s": time.monotonic() - start, "error": str(e)})
                    continue
                try:
                    result = scorer.try_score()
                except Exception as e:
                    exceptions.append({"t_elapsed_s": time.monotonic() - start, "error": str(e)})
                    result = None
                if result is not None:
                    n_windows += 1
                    window_latencies_ms.append(result["windowing_ms"] + result["inference_ms"])
                    try:
                        is_anomaly, triggered = policy.update(result["crash_prob"], result["recon_error"])
                        if triggered:
                            n_triggers += 1
                            trigger_events.append({"t_elapsed_s": time.monotonic() - start,
                                                    "crash_prob": result["crash_prob"], "recon_error": result["recon_error"]})
                    except Exception as e:
                        exceptions.append({"t_elapsed_s": time.monotonic() - start, "error": str(e)})

        now2 = time.monotonic()
        if now2 >= next_resource_sample:
            minflt, majflt = proc_faults(proc.pid)
            ctx = proc.num_ctx_switches()
            resource_samples.append({
                "t_elapsed_s": now2 - start,
                "process_cpu_percent": proc.cpu_percent(interval=None),
                "process_rss_mb": proc.memory_info().rss / (1024 * 1024),
                "thread_count": threading.active_count(),
                "cpu_affinity": proc.cpu_affinity() if hasattr(proc, "cpu_affinity") else None,
                "ctx_switches_voluntary": ctx.voluntary,
                "ctx_switches_involuntary": ctx.involuntary,
                "minor_page_faults_cumulative": minflt,
                "major_page_faults_cumulative": majflt,
                "temperature_c": common.read_temp_c(),
            })
            next_resource_sample = now2 + 1.0

        time.sleep(POLL_INTERVAL_S)

    gc_stats_end = gc.get_stats()
    restore_baseline_registers(bus, address)
    print("Restored baseline registers (FIFO_EN=0, USER_CTRL=0, SMPLRT_DIV=0).")

    actual_duration_s = time.monotonic() - start
    lat = np.asarray(window_latencies_ms, dtype=np.float64)
    stride_budget_ms = (cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"]) * 1000.0
    drain_intervals_ms = np.asarray(batch_drain_intervals_s, dtype=np.float64) * 1000.0

    report = {
        "device": common.device_info(),
        "context": "Section E2 -- FIFO-based acquisition condition (hardware-buffered, software-decimated "
                    "to the model's 50Hz), compared against the deployed polling baseline. Model/thresholds unchanged.",
        "sched_fifo_note": args.sched_fifo_note,
        "chip_note": "WHO_AM_I=0x70 (MPU6500, per B1) -- SMPLRT_DIV does not gate FIFO push rate as the "
                      "classic MPU6050 datasheet formula predicts; see module docstring for the disclosed "
                      "calibration finding and software-decimation workaround.",
        "fifo_config": {"smplrt_div_written": SMPLRT_DIV_VALUE, "fifo_en_reg": hex(FIFO_EN_GYRO_ACCEL),
                         "bytes_per_sample": BYTES_PER_SAMPLE, "host_poll_interval_s": POLL_INTERVAL_S},
        "calibration": {"duration_s": CALIBRATION_S, "measured_native_hz": native_hz,
                         "max_fifo_bytes_seen_during_calibration": max_fc_calib,
                         "decimation_n": decimation_n, "target_hz": TARGET_HZ},
        "requested_duration_min": args.duration_min,
        "actual_duration_min": actual_duration_s / 60.0,
        "n_raw_samples_drained": n_raw_samples,
        "n_samples_fed_to_model": n_fed_samples,
        "achieved_fed_hz": n_fed_samples / actual_duration_s if actual_duration_s > 0 else None,
        "achieved_raw_drain_hz": n_raw_samples / actual_duration_s if actual_duration_s > 0 else None,
        "n_windows_scored": n_windows,
        "n_triggers": n_triggers,
        "trigger_events": trigger_events,
        "n_i2c_errors": n_i2c_errors,
        "n_fifo_overflow_suspected": n_fifo_overflow_suspected,
        "n_exceptions": len(exceptions),
        "exceptions_sample": exceptions[:50],
        "per_window_latency_ms": common.percentile_stats(window_latencies_ms),
        "deadline_miss_count_gt_stride_budget": int((lat > stride_budget_ms).sum()) if len(lat) else 0,
        "deadline_miss_rate": float((lat > stride_budget_ms).mean()) if len(lat) else None,
        "batch_drain_stats": {
            "n_batches": len(batch_sizes),
            "raw_samples_per_batch": {"mean": float(np.mean(batch_sizes)) if batch_sizes else None,
                                       "max": int(np.max(batch_sizes)) if batch_sizes else None},
            "drain_interval_ms": common.percentile_stats(drain_intervals_ms),
        },
        "resources": {
            "process_cpu_percent": common.summarize_series(resource_samples, "process_cpu_percent"),
            "process_rss_mb": common.summarize_series(resource_samples, "process_rss_mb"),
            "temperature_c": common.summarize_series(resource_samples, "temperature_c"),
            "n_resource_samples": len(resource_samples),
        },
        "section_R_runtime_characterization": {
            "thread_count_series": [s["thread_count"] for s in resource_samples],
            "cpu_affinity": resource_samples[0]["cpu_affinity"] if resource_samples else None,
            "ctx_switches_voluntary_start_end": [resource_samples[0]["ctx_switches_voluntary"], resource_samples[-1]["ctx_switches_voluntary"]] if resource_samples else None,
            "ctx_switches_involuntary_start_end": [resource_samples[0]["ctx_switches_involuntary"], resource_samples[-1]["ctx_switches_involuntary"]] if resource_samples else None,
            "minor_page_faults_start_end": [resource_samples[0]["minor_page_faults_cumulative"], resource_samples[-1]["minor_page_faults_cumulative"]] if resource_samples else None,
            "major_page_faults_start_end": [resource_samples[0]["major_page_faults_cumulative"], resource_samples[-1]["major_page_faults_cumulative"]] if resource_samples else None,
            "gc_stats_start": gc_stats_start,
            "gc_stats_end": gc_stats_end,
        },
        "raw_resource_samples": resource_samples,
    }
    print("\n=== Summary ===")
    print(json.dumps({k: v for k, v in report.items() if k not in ("raw_resource_samples", "trigger_events")}, indent=2)[:4000])

    out_dir = common.ROOT / "piResults" / "results" / "final-validation" / "acquisition_compare"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.label}.json").write_text(json.dumps(report, indent=2, default=common._json_default))
    print(f"\nWrote {out_dir / (args.label + '.json')}")


if __name__ == "__main__":
    main()
