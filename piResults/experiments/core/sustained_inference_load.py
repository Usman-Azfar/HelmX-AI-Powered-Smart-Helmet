"""Not part of the official A1-D suite in PI_RESEARCH_GUIDE.md. A3 asks for a thermal
reading taken *while inference is actively running*, but crash_monitor.py can't get past
MPU6050 connection on this Pi (no sensor wired -- see piResults/ResultsFromPi.md, A2). This
script is an honest stand-in: it calls the REAL deployed INT8 TFLite model, on synthetic
correctly-shaped input (same convention as exp_a1), once every stride_seconds (300ms) --
matching the actual deployed cadence -- for the requested duration, so A3's thermal reading
is taken against genuine repeated inference load at the real duty cycle, not an idle Pi.

    python deploy/pi_research_suite/sustained_inference_load.py --duration-min 30
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

import common

p = argparse.ArgumentParser()
p.add_argument("--duration-min", type=float, default=30.0)
args = p.parse_args()

cfg = common.load_config()
model_path = common.ROOT / cfg["model_path"]
stride_seconds = cfg["sensor"]["stride_samples"] / cfg["sensor"]["sample_rate_hz"]

interpreter = tflite.Interpreter(model_path=str(model_path))
interpreter.allocate_tensors()
runner = interpreter.get_signature_runner()
rng = np.random.default_rng(0)

deadline = time.monotonic() + args.duration_min * 60.0
n = 0
next_tick = time.monotonic()
while time.monotonic() < deadline:
    seq = rng.normal(0, 1, size=(1, 60, 6)).astype(np.float32)
    aux = rng.normal(0, 1, size=(1, 7)).astype(np.float32)
    runner(seq=seq, aux=aux)
    n += 1
    next_tick += stride_seconds
    sleep_for = next_tick - time.monotonic()
    if sleep_for > 0:
        time.sleep(sleep_for)
    else:
        next_tick = time.monotonic()

print(f"Ran {n} inferences over {args.duration_min} min at {stride_seconds*1000:.0f}ms cadence")
