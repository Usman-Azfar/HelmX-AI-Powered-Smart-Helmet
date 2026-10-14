"""
HelmX real-time crash monitor for Raspberry Pi.

Reads MPU6050 accel/gyro at a fixed rate, runs the exported crash-detection
TFLite model over a sliding window, and -- after a local buzzer/vibration
countdown the rider can cancel -- sends a GPS-tagged SMS alert via a GSM
module when a crash is confirmed. Runs continuously: an alert does not stop
monitoring, it starts a cooldown so the same event doesn't spam SMS messages
while still catching a second, independent crash later.
"""
import json
import logging
import math
import os
import time
from collections import deque
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

import numpy as np
import serial
import yaml

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow.lite as tflite
    except ImportError:
        tflite = None

try:
    from gpiozero import DigitalOutputDevice
except (ImportError, NotImplementedError):
    DigitalOutputDevice = None

try:
    from mpu6050 import mpu6050
except ImportError:
    mpu6050 = None  # only needed by connect_sensor()/read_sensor() -- lets the
                     # rest of this module (WindowScorer, TriggerPolicy,
                     # CrashModel, CausalGravityFilter, compute_aux_features)
                     # import and run on a dev machine or in
                     # deploy/pi_research_suite/'s replay/inference-only
                     # experiments, which never touch a real MPU6050.

ROOT = Path(__file__).resolve().parent.parent


def load_config(path=None):
    path = path or (Path(__file__).parent / "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def load_model_thresholds(cfg):
    """Loads classifier_prob/recon_error directly from
    models/thresholds.json (cfg['thresholds_path']) rather than a manually
    duplicated copy in config.yaml -- a previous version of this file
    hardcoded those two numbers in YAML, which silently drifted out of sync
    with the actual trained model after a retrain (changesToMake2.txt item
    1). Re-running scripts/train.py regenerates thresholds.json; this always
    reflects whatever model is currently deployed, with nothing to edit."""
    path = ROOT / cfg.get("thresholds_path", "models/thresholds.json")
    with open(path) as f:
        thresholds = json.load(f)
    return thresholds["classifier_prob"], thresholds["recon_error"]


def setup_logging(cfg):
    log_path = ROOT / cfg["logging"]["log_file"]
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("crash_monitor")
    logger.setLevel(cfg["logging"]["level"])
    handler = RotatingFileHandler(
        log_path, maxBytes=cfg["logging"]["max_bytes"], backupCount=cfg["logging"]["backup_count"]
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    return logger


class CausalGravityFilter:
    """Causal (online) approximation of the offline zero-phase Butterworth
    high-pass used at training time: an exponential-moving-average gravity
    estimate subtracted from the raw reading. Same cutoff frequency as
    training, but introduces a small phase lag the offline filter doesn't
    have -- documented tradeoff for being usable in a streaming loop."""

    def __init__(self, cutoff_hz, sample_rate_hz):
        tau = 1.0 / (2 * math.pi * cutoff_hz)
        self.alpha = math.exp(-1.0 / (tau * sample_rate_hz))
        self.gravity = None

    def apply(self, accel_xyz):
        accel_xyz = np.asarray(accel_xyz, dtype=np.float64)
        if self.gravity is None:
            self.gravity = accel_xyz.copy()
        else:
            self.gravity = self.alpha * self.gravity + (1 - self.alpha) * accel_xyz
        return accel_xyz - self.gravity

    def reset(self):
        """Discards the running gravity estimate so the next apply() call
        cold-starts (see logic_robustness_tests_2.py 3.27: the first-ever
        apply() call after this always returns exactly [0,0,0]). Only meant
        to be called for a genuinely stale estimate -- e.g. after a timing
        gap long enough that the pre-gap EMA state no longer reflects the
        rider's current orientation -- not after every buffer clear; see
        SampleStreamGuard / handle_suspected_crash()'s cancellation path."""
        self.gravity = None


class LocalAlarm:
    """Drives a buzzer or vibration motor via a GPIO pin during the
    cancellation countdown. Both a buzzer module and a vibration motor (via a
    transistor/MOSFET driver) are simple on/off digital loads, so one class
    covers either -- `gpio_pin` in deploy/config.yaml picks which one you
    wired. Degrades to a log-only no-op off the Pi (no gpiozero / no GPIO
    access) so this still runs for local testing."""

    def __init__(self, gpio_pin, logger):
        self.logger = logger
        self.device = None
        if DigitalOutputDevice is not None:
            try:
                self.device = DigitalOutputDevice(gpio_pin)
            except Exception as e:
                self.logger.warning("Local alarm GPIO unavailable (%s) -- logging only", e)
        else:
            self.logger.warning("gpiozero not available -- local alarm will log only")

    def start(self):
        self.logger.warning("LOCAL ALARM ON")
        if self.device is not None:
            self.device.on()

    def stop(self):
        self.logger.info("Local alarm off")
        if self.device is not None:
            self.device.off()


class CancellationListener:
    """One-shot file-based signal the voice-assistant module writes to when
    the rider cancels a pending alert by voice. Deliberately simple (no
    sockets, no extra services) so an independent process just has to
    create/touch one file -- crash_monitor.py consumes (deletes) it so a
    stale cancellation from a previous event can't silently suppress a new
    one."""

    def __init__(self, signal_path, logger):
        self.path = signal_path
        self.logger = logger

    def check_and_clear(self):
        if not os.path.exists(self.path):
            return False
        try:
            os.remove(self.path)
        except OSError as e:
            self.logger.warning("Failed to clear cancellation signal file: %s", e)
        return True


class CrashModel:
    """Uses the TFLite signature-runner API (keyed by the Keras layer names
    given in src/model.py: 'seq'/'aux' in, 'crash_prob'/'recon_error' out)
    instead of raw tensor indices, which shift around between TF versions and
    quantization modes."""

    def __init__(self, model_path, normalizer_path):
        if tflite is None:
            raise RuntimeError(
                "No TensorFlow Lite interpreter is installed. Install "
                "tflite-runtime on the Raspberry Pi or TensorFlow on a development machine."
            )
        self.interpreter = tflite.Interpreter(model_path=str(model_path))
        self.runner = self.interpreter.get_signature_runner()

        norm = np.load(normalizer_path)
        self.seq_mean, self.seq_std = norm["seq_mean"], norm["seq_std"]
        self.aux_mean, self.aux_std = norm["aux_mean"], norm["aux_std"]

    def predict(self, seq_window, aux_features):
        seq = ((seq_window - self.seq_mean) / self.seq_std)[np.newaxis].astype(np.float32)
        aux = ((aux_features - self.aux_mean) / self.aux_std)[np.newaxis].astype(np.float32)
        outputs = self.runner(seq=seq, aux=aux)
        return float(outputs["crash_prob"][0, 0]), float(outputs["recon_error"][0, 0])


class WindowScorer:
    """The exact per-sample -> per-window scoring path main() uses, extracted
    so deploy/pi_research_suite/'s experiments can drive this identical code
    with recorded or synthetic samples instead of a live MPU6050, without
    duplicating (and risking silently diverging from) the real detection
    logic -- see pi_research_suite/README.md, Experiment C in particular.

    Split into append()/try_score() rather than one combined call
    specifically to preserve main()'s existing sequencing: the real-time
    pacing sleep happens BETWEEN buffering a sample and checking/running
    inference (so inference latency isn't silently absorbed into the next
    sample's timing budget) -- collapsing these into one call would change
    that behavior."""

    def __init__(self, cfg, model, gravity_filter):
        self.window_samples = cfg["sensor"]["window_samples"]
        self.stride_samples = cfg["sensor"]["stride_samples"]
        self.model = model
        self.gravity_filter = gravity_filter
        self.buffer = deque(maxlen=self.window_samples)
        self.new_samples = 0

    def append(self, sample):
        """Gravity-corrects and buffers one raw [ax,ay,az,gx,gy,gz] sample.
        Returns the preprocessing stage's wall-clock cost in milliseconds."""
        t0 = time.perf_counter()
        sample = list(sample)
        sample[0:3] = self.gravity_filter.apply(sample[0:3])
        self.buffer.append(sample)
        self.new_samples += 1
        return (time.perf_counter() - t0) * 1000.0

    def try_score(self):
        """Returns None if a full window + a new stride's worth of samples
        aren't buffered yet; otherwise runs the model and returns a dict:
        window, aux, crash_prob, recon_error, and perf_counter-based stage
        timings in milliseconds (windowing_ms, inference_ms, total_ms)."""
        if len(self.buffer) < self.window_samples or self.new_samples < self.stride_samples:
            return None
        self.new_samples = 0

        t0 = time.perf_counter()
        window = np.array(self.buffer, dtype=np.float32)
        aux = compute_aux_features(window)
        t1 = time.perf_counter()
        crash_prob, recon_error = self.model.predict(window, aux)
        t2 = time.perf_counter()

        return {
            "window": window, "aux": aux,
            "crash_prob": crash_prob, "recon_error": recon_error,
            "windowing_ms": (t1 - t0) * 1000.0,
            "inference_ms": (t2 - t1) * 1000.0,
            "total_ms": (t2 - t0) * 1000.0,
        }

    def clear(self):
        self.buffer.clear()
        self.new_samples = 0


class SampleStreamGuard:
    """Timestamp-based acquisition-layer gap detector, sitting BETWEEN
    read_sensor() and WindowScorer.append() in main()'s live loop -- not
    inside WindowScorer itself. WindowScorer stays purely sample-count
    driven (confirmed by logic_robustness_tests_2.py 3.19/3.20: it has no
    timing input at all and cannot tell a dropped sample from a normal
    one), so every deploy/pi_research_suite/ experiment that drives
    WindowScorer directly with recorded/synthetic samples keeps working
    completely unchanged; only main()'s real-time loop uses this class.

    Uses time.monotonic() deltas between successive real sensor reads (not
    sample count) to notice when a sample was probably delayed or dropped,
    so a nominal window_samples-sized window is never silently treated as
    if it still spanned window_samples/sample_rate_hz seconds of real time
    when it didn't.

    max_dt_s/min_dt_s/long_gap_reset_s are PROVISIONAL -- chosen as a
    conservative multiple of the expected sample period during the correction
    work. Later live characterization measured actual I2C sample-interval
    jitter; deploy/config.yaml: sensor.timing_guard documents the resulting
    deployed values and piResults/ preserves the validation evidence."""

    def __init__(self, cfg, expected_period_s, logger):
        cfg = cfg or {}
        self.expected_period_s = expected_period_s
        self.max_dt_s = cfg.get("max_dt_s", expected_period_s * 1.5)
        self.min_dt_s = cfg.get("min_dt_s", expected_period_s * 0.5)
        self.long_gap_reset_s = cfg.get("long_gap_reset_s", 1.0)
        self.logger = logger

        self.last_ts = None
        self.samples_received = 0
        self.timing_gaps = 0
        self.suspected_dropped_samples = 0
        self.duplicate_or_too_fast_samples = 0
        self.windows_invalidated = 0
        self.windows_scored = 0
        self.max_interval_s = 0.0
        self._interval_sum_s = 0.0
        self._interval_count = 0
        self._interval_history = deque(maxlen=2000)

    def reset_baseline(self):
        """Call right after a KNOWN, already-handled gap -- e.g. main()'s
        existing scorer.clear() following the alarm cancellation countdown
        -- so the next real sample isn't mistaken for an undetected drop.
        Deliberately does not touch gravity_filter; whether to reset that
        after the alarm countdown is a separate, already-made decision (see
        logic_robustness_tests_2.py 3.27) that this correction does not
        change."""
        self.last_ts = None

    def observe(self, now):
        """now: time.monotonic() timestamp of a just-read real sample.
        Returns (gap_detected, dt_s). dt_s is None on the first observation
        after construction/reset_baseline() -- nothing to compare against
        yet."""
        self.samples_received += 1
        if self.last_ts is None:
            self.last_ts = now
            return False, None

        dt = now - self.last_ts
        self.last_ts = now
        self.max_interval_s = max(self.max_interval_s, dt)
        self._interval_sum_s += dt
        self._interval_count += 1
        self._interval_history.append(dt)

        gap_detected = False
        if dt > self.max_dt_s:
            self.timing_gaps += 1
            self.suspected_dropped_samples += max(0, round(dt / self.expected_period_s) - 1)
            gap_detected = True
        elif dt < self.min_dt_s:
            self.duplicate_or_too_fast_samples += 1
        return gap_detected, dt

    def record_window_invalidated(self):
        self.windows_invalidated += 1

    def record_window_scored(self):
        self.windows_scored += 1

    def snapshot(self):
        """Return the acquisition-integrity telemetry used by the Pi validation suite."""
        n = self._interval_count
        percentiles = {}
        if n:
            arr_ms = np.asarray(self._interval_history, dtype=np.float64) * 1000.0
            percentiles = {
                "sample_interval_p50_ms": float(np.percentile(arr_ms, 50)),
                "sample_interval_p95_ms": float(np.percentile(arr_ms, 95)),
                "sample_interval_p99_ms": float(np.percentile(arr_ms, 99)),
            }
        return {
            "samples_received": self.samples_received,
            "timing_gaps": self.timing_gaps,
            "suspected_dropped_samples": self.suspected_dropped_samples,
            "duplicate_or_too_fast_samples": self.duplicate_or_too_fast_samples,
            "windows_invalidated": self.windows_invalidated,
            "windows_scored": self.windows_scored,
            "max_sample_interval_ms": self.max_interval_s * 1000.0,
            "mean_sample_interval_ms": (self._interval_sum_s / n * 1000.0) if n else None,
            **percentiles,
        }


class TriggerPolicy:
    """The exact consecutive-window + cooldown confirmation rule main() uses
    (deploy/config.yaml: thresholds.consecutive_windows/cooldown_seconds),
    extracted so it can be driven independently of live sensor timing -- e.g.
    pi_research_suite/exp_a5_trigger_latency.py replays known crash windows
    with synthetic timestamps and measures how long this rule takes to
    confirm, without waiting through real wall-clock cooldowns."""

    def __init__(self, classifier_threshold, recon_threshold, consecutive_windows, cooldown_seconds):
        self.classifier_threshold = classifier_threshold
        self.recon_threshold = recon_threshold
        self.consecutive_windows = consecutive_windows
        self.cooldown_seconds = cooldown_seconds
        self.anomaly_streak = 0
        self.cooldown_until = 0.0

    def update(self, crash_prob, recon_error, now=None):
        """Returns (is_anomaly, triggered) for this window. `now`: monotonic
        seconds; defaults to time.monotonic() for live use -- pass an
        explicit replayed timestamp for deterministic offline/replay
        testing."""
        now = time.monotonic() if now is None else now
        is_anomaly = crash_prob > self.classifier_threshold or recon_error > self.recon_threshold
        self.anomaly_streak = self.anomaly_streak + 1 if is_anomaly else 0
        triggered = False
        if self.anomaly_streak >= self.consecutive_windows and now >= self.cooldown_until:
            triggered = True
            self.anomaly_streak = 0
            self.cooldown_until = now + self.cooldown_seconds
        return is_anomaly, triggered


def compute_aux_features(seq_window):
    accel_mag = np.linalg.norm(seq_window[:, 0:3], axis=1)
    gyro_mag = np.linalg.norm(seq_window[:, 3:6], axis=1)
    jerk = np.abs(np.diff(accel_mag)).max() if len(accel_mag) > 1 else 0.0
    return np.array([
        accel_mag.mean(), accel_mag.std(), accel_mag.max(),
        gyro_mag.mean(), gyro_mag.std(), gyro_mag.max(),
        jerk,
    ], dtype=np.float32)


class GsmModule:
    def __init__(self, cfg, logger):
        self.cfg = cfg
        self.logger = logger
        self.ser = None
        self._connect()

    def _connect(self):
        try:
            self.ser = serial.Serial(self.cfg["port"], baudrate=self.cfg["baudrate"], timeout=1)
            self.logger.info("GSM serial connected on %s", self.cfg["port"])
        except serial.SerialException as e:
            self.logger.error("GSM serial connection failed: %s", e)
            self.ser = None

    def _ensure_connected(self):
        if self.ser is None or not self.ser.is_open:
            self._connect()
        return self.ser is not None

    def get_gps_coordinates(self, timeout_seconds):
        if not self._ensure_connected():
            return None
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                line = self.ser.readline().decode(errors="ignore")
            except serial.SerialException as e:
                self.logger.error("GPS read failed: %s", e)
                self.ser = None
                return None
            if "$GPGGA" in line:
                parts = line.split(",")
                if len(parts) > 4 and parts[2] and parts[4]:
                    try:
                        lat = float(parts[2][:2]) + float(parts[2][2:]) / 60
                        lon = float(parts[4][:3]) + float(parts[4][3:]) / 60
                        return lat, lon
                    except ValueError:
                        continue
        self.logger.warning("GPS fix not acquired within %ss", timeout_seconds)
        return None

    def _read_response(self, timeout_seconds):
        """Reads from the modem until it reports OK/ERROR or the timeout
        expires, instead of a fixed sleep-and-hope -- lets send_sms tell a
        message that actually sent from one that silently failed."""
        deadline = time.monotonic() + timeout_seconds
        buffer = ""
        while time.monotonic() < deadline and "OK" not in buffer and "ERROR" not in buffer:
            try:
                waiting = self.ser.in_waiting
                chunk = self.ser.read(waiting if waiting else 1)
            except serial.SerialException as e:
                self.logger.error("GSM read failed: %s", e)
                self.ser = None
                break
            buffer += chunk.decode(errors="ignore")
        return buffer

    def send_sms(self, message):
        if not self._ensure_connected():
            self.logger.error("Cannot send SMS: no GSM connection")
            return False
        try:
            self.ser.write(b'AT+CMGF=1\r')
            resp = self._read_response(3)
            if "OK" not in resp:
                self.logger.warning("Unexpected response to AT+CMGF=1: %r", resp)

            recipient = self.cfg["recipient_number"].encode()
            self.ser.write(b'AT+CMGS="' + recipient + b'"\r')
            time.sleep(0.5)
            self.ser.read(self.ser.in_waiting or 0)  # discard the '>' prompt

            self.ser.write(message.encode())
            self.ser.write(bytes([26]))
            resp = self._read_response(10)
            if "OK" not in resp:
                self.logger.error("SMS send failed, modem response: %r", resp)
                return False

            self.logger.info("SMS sent: %s", message)
            return True
        except serial.SerialException as e:
            self.logger.error("SMS send failed: %s", e)
            self.ser = None
            return False


def read_sensor(sensor, logger):
    try:
        accel = sensor.get_accel_data()
        gyro = sensor.get_gyro_data()
        return [accel["x"], accel["y"], accel["z"], gyro["x"], gyro["y"], gyro["z"]]
    except OSError as e:
        logger.error("Sensor read failed: %s", e)
        return None


def connect_sensor(cfg, logger):
    if mpu6050 is None:
        raise RuntimeError(
            "mpu6050 package not installed -- required for a real sensor connection "
            "(pip install mpu6050-raspberrypi, deploy/requirements.txt). Replay/inference-only "
            "experiments in deploy/pi_research_suite/ don't need this at all."
        )
    while True:
        try:
            return mpu6050(cfg["sensor"]["i2c_address"])
        except OSError as e:
            logger.error("MPU6050 connection failed (%s), retrying in 5s", e)
            time.sleep(5)


@dataclass
class CrashAlertResult:
    """Structured outcome of one handle_suspected_crash() call. Replaces a
    bare bool -- the previous version returned True unconditionally once
    the cancellation window expired, even when gsm.send_sms() itself
    returned False, so True did not actually mean "SMS confirmed sent"
    (found by logic_robustness_tests.py 3.30c/3.32, harmless today only
    because main() discarded the return value). cancelled/gps_available/
    sms_attempted/sms_sent are
    independent events and are reported as such rather than collapsed into
    one flag."""
    cancelled: bool
    sms_attempted: bool
    sms_sent: bool
    gps_available: bool


def handle_suspected_crash(alarm, canceller, gsm, cfg, logger):
    """Runs the cancellation countdown for one suspected crash and returns a
    CrashAlertResult describing exactly what happened. An SMS is only ever
    attempted after this window expires uncancelled -- the model's
    consecutive-window trigger starts a local check-in, not an emergency
    message, by itself."""
    countdown_seconds = cfg["alarm"]["countdown_seconds"]
    logger.warning("CRASH SUSPECTED -- %ds cancellation window started", countdown_seconds)
    canceller.check_and_clear()  # discard any stale signal from before this event
    alarm.start()

    deadline = time.monotonic() + countdown_seconds
    while time.monotonic() < deadline:
        if canceller.check_and_clear():
            alarm.stop()
            logger.warning("CRASH_ALERT_CANCELLED -- rider cancelled, no SMS attempted")
            return CrashAlertResult(cancelled=True, sms_attempted=False, sms_sent=False, gps_available=False)
        time.sleep(0.2)

    alarm.stop()
    logger.warning("Cancellation window expired -- attempting SMS alert")

    coords = gsm.get_gps_coordinates(cfg["gps"]["timeout_seconds"])
    gps_available = coords is not None
    if coords:
        lat, lon = coords
        location_text = f"https://maps.google.com/?q={lat},{lon}"
    else:
        logger.warning("GPS_UNAVAILABLE -- sending alert without coordinates")
        location_text = "location unavailable"
    message = f"CRASH DETECTED!\nLocation:\n{location_text}"

    logger.warning("SMS_ATTEMPTED")
    sms_sent = bool(gsm.send_sms(message))
    if sms_sent:
        logger.warning("SMS_SENT")
    else:
        logger.error("SMS_FAILED -- alert was NOT confirmed delivered")

    return CrashAlertResult(cancelled=False, sms_attempted=True, sms_sent=sms_sent, gps_available=gps_available)


def main():
    cfg = load_config()
    logger = setup_logging(cfg)

    sample_rate = cfg["sensor"]["sample_rate_hz"]
    period = 1.0 / sample_rate

    classifier_threshold, recon_threshold = load_model_thresholds(cfg)
    logger.info("Loaded thresholds from %s: classifier_prob=%.6f recon_error=%.6f",
                cfg.get("thresholds_path", "models/thresholds.json"), classifier_threshold, recon_threshold)

    model = CrashModel(ROOT / cfg["model_path"], ROOT / cfg["normalizer_path"])
    gravity_filter = CausalGravityFilter(cfg["gravity_filter"]["cutoff_hz"], sample_rate)
    scorer = WindowScorer(cfg, model, gravity_filter)
    policy = TriggerPolicy(
        classifier_threshold, recon_threshold,
        cfg["thresholds"]["consecutive_windows"], cfg["thresholds"]["cooldown_seconds"],
    )
    gsm = GsmModule(cfg["gsm"], logger)
    alarm = LocalAlarm(cfg["alarm"]["gpio_pin"], logger)
    canceller = CancellationListener(cfg["alarm"]["cancel_signal_file"], logger)
    guard = SampleStreamGuard(cfg["sensor"].get("timing_guard"), period, logger)
    sensor = connect_sensor(cfg, logger)

    logger.info("Crash monitor started")
    next_tick = time.monotonic()
    next_telemetry_log = time.monotonic() + 60.0

    while True:
        next_tick += period
        sample = read_sensor(sensor, logger)
        if sample is None:
            sensor = connect_sensor(cfg, logger)
            continue

        now = time.monotonic()
        gap_detected, dt = guard.observe(now)
        if gap_detected:
            logger.warning(
                "TIMING_GAP dt=%.1fms (max_dt=%.1fms) -- discarding in-flight window, "
                "resuming once a fresh full window has accumulated",
                dt * 1000.0, guard.max_dt_s * 1000.0,
            )
            scorer.clear()
            guard.record_window_invalidated()
            if dt >= guard.long_gap_reset_s:
                gravity_filter.reset()
                logger.warning("Gap >= %.1fs -- resetting gravity filter state", guard.long_gap_reset_s)

        scorer.append(sample)

        sleep_for = next_tick - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)
        else:
            next_tick = time.monotonic()

        if now >= next_telemetry_log:
            logger.info("stream_telemetry=%s", guard.snapshot())
            next_telemetry_log = now + 60.0

        result = scorer.try_score()
        if result is None:
            continue
        guard.record_window_scored()

        is_anomaly, triggered = policy.update(result["crash_prob"], result["recon_error"])
        logger.info(
            "crash_prob=%.4f recon_error=%.4f streak=%d",
            result["crash_prob"], result["recon_error"], policy.anomaly_streak,
        )

        if triggered:
            alert_result = handle_suspected_crash(alarm, canceller, gsm, cfg, logger)
            logger.info(
                "Crash alert outcome: cancelled=%s sms_attempted=%s sms_sent=%s gps_available=%s",
                alert_result.cancelled, alert_result.sms_attempted,
                alert_result.sms_sent, alert_result.gps_available,
            )

            # The countdown blocks sensor reads for up to countdown_seconds,
            # so the buffer is now stale (a real time gap, not continuous
            # motion) -- drop it rather than let the model score a window
            # that spans the gap. This is a KNOWN, already-handled gap (not
            # a Weakness-2-style silent drop), so tell the guard to rebase
            # rather than flag it as an unexpected one on the next sample.
            scorer.clear()
            guard.reset_baseline()
            next_tick = time.monotonic()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.getLogger("crash_monitor").info("Crash monitor stopped by user")
