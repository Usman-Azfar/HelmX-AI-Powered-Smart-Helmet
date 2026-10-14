"""HelmX_FInal_Pi_REqwuirements.md Section Q -- GPS/GSM integration smoke test.

Exercises the real deploy/crash_monitor.py GsmModule (serial connect, GPS NMEA
parsing) and a real local alarm GPIO pulse, across --trials controlled runs.
Per agreed scope: stops BEFORE the final modem write that would actually send
an SMS -- GsmModule.send_sms() is monkeypatched to log the exact AT commands
and message it would have sent, then return a synthetic "not actually sent"
result, rather than writing bytes(26) (Ctrl-Z, the SMS-body terminator) to the
modem. Real GPS fix attempts and real local-alarm GPIO pulses DO happen (they
have no real-world side effect beyond a buzzer/vibration pulse and a serial
read) -- only the SMS transmission step is intercepted.

Requires a real GSM/GPS module connected at deploy/config.yaml: gsm.port
(default /dev/ttyUSB0) -- exits early with a clear message if absent.

Run on the Pi:
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_q_gps_gsm_smoke_test.py --trials 8
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common
import crash_monitor as cm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=8)
    parser.add_argument("--countdown-seconds", type=float, default=None,
                         help="override deploy/config.yaml's alarm.countdown_seconds for faster trials")
    args = parser.parse_args()

    cfg = common.load_config()
    if args.countdown_seconds is not None:
        cfg["alarm"]["countdown_seconds"] = args.countdown_seconds

    port = cfg["gsm"]["port"]
    if not Path(port).exists():
        print(f"ABORT: {port} does not exist -- no GSM/GPS module connected. "
              f"See gps_gsm_optional/gps_gsm_smoke_test_notes.txt.")
        sys.exit(1)

    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger("q_gps_gsm_smoke")

    intercepted_sends = []

    def intercepted_send_sms(self, message):
        if not self._ensure_connected():
            return False
        self.ser.write(b'AT+CMGF=1\r')
        self._read_response(3)
        recipient = self.cfg["recipient_number"].encode()
        would_send_cmd = b'AT+CMGS="' + recipient + b'"\r'
        intercepted_sends.append({
            "t": time.time(), "recipient": self.cfg["recipient_number"],
            "message": message, "at_command_that_would_dispatch": would_send_cmd.decode(errors="ignore"),
            "note": "INTERCEPTED before actual dispatch -- AT+CMGS prompt/body/Ctrl-Z never written",
        })
        self.logger.warning("SMS SEND INTERCEPTED (smoke test, not actually sent): %s", message)
        return False  # matches CrashAlertResult.sms_sent=False semantics -- nothing was confirmed sent

    cm.GsmModule.send_sms = intercepted_send_sms

    results = []
    for i in range(args.trials):
        print(f"\n--- Trial {i + 1}/{args.trials} ---")
        gsm = cm.GsmModule(cfg["gsm"], logger)
        alarm = cm.LocalAlarm(cfg["alarm"]["gpio_pin"], logger)
        canceller = cm.CancellationListener(cfg["alarm"]["cancel_signal_file"], logger)

        t_trigger = time.time()
        result = cm.handle_suspected_crash(alarm, canceller, gsm, cfg, logger)
        t_done = time.time()

        results.append({
            "trial": i + 1, "t_trigger": t_trigger, "t_done": t_done,
            "wall_elapsed_s": t_done - t_trigger,
            "cancelled": result.cancelled, "sms_attempted": result.sms_attempted,
            "sms_sent_per_intercepted_stub": result.sms_sent,
            "gps_available": result.gps_available,
        })
        print(json.dumps(results[-1], indent=2))

    report = {
        "device": common.device_info(),
        "context": "Section Q smoke test -- SMS transmission intercepted before actual dispatch, per agreed scope.",
        "n_trials": args.trials,
        "n_gps_fix_success": sum(1 for r in results if r["gps_available"]),
        "n_gps_no_fix": sum(1 for r in results if not r["gps_available"]),
        "n_sms_attempts": sum(1 for r in results if r["sms_attempted"]),
        "n_modem_accepted": 0,  # never reaches the real modem-accept step by design
        "n_confirmed_received": 0,
        "trials": results,
        "intercepted_sms_payloads": intercepted_sends,
        "important_caveats": [
            "System-context evidence only -- do not claim network reliability from this many trials.",
            "SMS transmission was intercepted before dispatch per agreed scope; n_modem_accepted/"
            "n_confirmed_received are structurally 0 here, not a reliability finding.",
        ],
    }
    out_dir = common.ROOT / "piResults" / "results" / "final-validation" / "gps_gsm_optional"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "gps_gsm_smoke_test.json").write_text(json.dumps(report, indent=2))
    print(f"\nWrote {out_dir / 'gps_gsm_smoke_test.json'}")


if __name__ == "__main__":
    main()
