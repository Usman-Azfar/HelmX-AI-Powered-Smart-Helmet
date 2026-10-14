"""Shared utilities for the pi_research_suite experiments (A1-A6, C, D).
Deliberately standalone-friendly (no `import src...`) matching
deploy/crash_monitor.py's own convention -- only tflite-runtime, numpy, yaml,
and psutil are needed on the device itself for the hardware-facing
experiments; a couple of scripts (C, D) additionally import from `src/` and
must therefore be run from a checkout that has the full training-side
package too (see README.md for exactly which)."""
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import yaml

try:
    import psutil
except ImportError:
    psutil = None

ROOT = Path(__file__).resolve().parent.parent.parent
DEPLOY_DIR = ROOT / "deploy"
RESULTS_DIR = ROOT / "results" / "pi_research"


def load_config(path=None):
    path = path or (DEPLOY_DIR / "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def ensure_results_dir():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR


def save_json(obj, name):
    ensure_results_dir()
    path = RESULTS_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=_json_default)
    print(f"Wrote {path}")
    return path


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def percentile_stats(values_ms):
    """Standard latency-statistics bundle -- mean alone hides occasional slow
    inferences, so every experiment that measures timing reports the full set
    (median/p95/p99 are the ones that matter most for a real-time deadline
    argument, per this round's explicit ask)."""
    arr = np.asarray(values_ms, dtype=np.float64)
    if len(arr) == 0:
        return {"n": 0, "mean_ms": None, "median_ms": None, "p95_ms": None,
                "p99_ms": None, "max_ms": None, "std_ms": None}
    return {
        "n": int(len(arr)),
        "mean_ms": float(arr.mean()),
        "median_ms": float(np.median(arr)),
        "p95_ms": float(np.percentile(arr, 95)),
        "p99_ms": float(np.percentile(arr, 99)),
        "max_ms": float(arr.max()),
        "std_ms": float(arr.std()),
    }


def device_info():
    """Best-effort device fingerprint for the report header -- every field
    degrades to None/"" rather than raising if unavailable, since this suite
    must also run (for the non-hardware experiments) on a dev machine."""
    info = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "ram_gb": None,
        "model": None,
        "tflite_runtime_version": None,
    }
    if psutil is not None:
        try:
            info["ram_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        except Exception:
            pass
    model_path = Path("/proc/device-tree/model")
    if model_path.exists():
        try:
            info["model"] = model_path.read_text(errors="ignore").strip("\x00\n ")
        except OSError:
            pass
    try:
        import tflite_runtime
        info["tflite_runtime_version"] = getattr(tflite_runtime, "__version__", "unknown")
    except ImportError:
        info["tflite_runtime_version"] = "not installed (using tensorflow.lite fallback)"
    return info


def read_temp_c():
    """Raspberry Pi CPU temperature via vcgencmd, present on Raspberry Pi OS.
    Returns None (not a fabricated number) off a Pi or if vcgencmd is
    missing -- same "unavailable, not estimated" convention as
    deploy/benchmark_device.py's power probe."""
    try:
        out = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True, timeout=2)
        # e.g. "temp=42.8'C\n"
        text = out.stdout.strip()
        if "=" in text:
            value = text.split("=", 1)[1].split("'")[0]
            return float(value)
    except (FileNotFoundError, subprocess.SubprocessError, ValueError):
        pass
    # Fallback for non-Pi Linux boards that expose the generic thermal zone.
    thermal_path = Path("/sys/class/thermal/thermal_zone0/temp")
    if thermal_path.exists():
        try:
            return int(thermal_path.read_text().strip()) / 1000.0
        except (OSError, ValueError):
            pass
    return None


_THROTTLED_BITS = {
    0: "under_voltage_now", 1: "arm_freq_capped_now", 2: "currently_throttled", 3: "soft_temp_limit_now",
    16: "under_voltage_occurred", 17: "arm_freq_capped_occurred", 18: "throttling_occurred",
    19: "soft_temp_limit_occurred",
}


def read_throttled():
    """Decodes `vcgencmd get_throttled`'s hex bitmask (documented at
    https://www.raspberrypi.com/documentation/computers/os.html#get_throttled)
    into named booleans. The "_occurred" flags matter more than "_now" for a
    sustained-run report -- a transient dip that self-recovered still means
    throttling happened at some point during the test."""
    try:
        out = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2)
        text = out.stdout.strip()
        if "=" not in text:
            return None
        raw = int(text.split("=", 1)[1], 16)
        return {"raw_hex": hex(raw), **{name: bool(raw & (1 << bit)) for bit, name in _THROTTLED_BITS.items()}}
    except (FileNotFoundError, subprocess.SubprocessError, ValueError):
        return None


def sample_process_resources(proc):
    """One CPU%/RSS sample for a psutil.Process, plus system-wide CPU%/RAM%
    and swap, plus temperature if available -- the common per-second sample
    shape used by A2/A6."""
    sample = {"t": time.time()}
    if psutil is not None:
        try:
            sample["process_cpu_percent"] = proc.cpu_percent(interval=None)
            sample["process_rss_mb"] = proc.memory_info().rss / (1024 * 1024)
        except psutil.Error:
            sample["process_cpu_percent"] = None
            sample["process_rss_mb"] = None
        sample["system_cpu_percent"] = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        sample["system_ram_percent"] = vm.percent
        sample["system_ram_used_mb"] = (vm.total - vm.available) / (1024 * 1024)
        swap = psutil.swap_memory()
        sample["swap_used_mb"] = swap.used / (1024 * 1024)
    sample["temperature_c"] = read_temp_c()
    return sample


def summarize_series(samples, key):
    values = [s[key] for s in samples if s.get(key) is not None]
    if not values:
        return {"mean": None, "p95": None, "max": None, "min": None}
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(arr.mean()), "p95": float(np.percentile(arr, 95)),
        "max": float(arr.max()), "min": float(arr.min()),
    }
