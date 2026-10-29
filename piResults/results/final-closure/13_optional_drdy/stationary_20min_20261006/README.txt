
 — 13_optional_drdy/stationary_20min_20261006
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-06T15:07:16.883089+00:00
Evidence: piResults/final_pi_review_closure/13_optional_drdy/stationary_20min_20261006
{
  "mode": "drdy",
  "fifo_overflows": 0,
  "seconds_requested": 1200.0,
  "elapsed_s": 1200.0156610620002,
  "n_samples": 60688,
  "sample_rate_hz": 50.572673315189746,
  "n_windows": 4042,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 60687,
    "mean_ms": 19.77377155023317,
    "median_ms": 19.76177500000631,
    "std_ms": 0.7687511158601625,
    "rms_error_from_20ms": 0.8013473589025862,
    "p90_ms": 20.174311999971906,
    "p95_ms": 20.673157099963646,
    "p99_ms": 22.274308879968885,
    "p99.9_ms": 25.15634402205602,
    "max_ms": 48.763186999849495,
    "histogram_edges_ms": [
      0,
      10,
      15,
      25,
      30,
      40,
      60,
      100,
      "inf"
    ],
    "counts_left_closed_right_open": [
      10,
      75,
      60534,
      57,
      9,
      2,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1934,
      "5": 153,
      "8": 42
    }
  },
  "nominal_positions_received_samples": 4042,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.6032610001275316,
    "50": 1.7748714999470394,
    "95": 4.340702950059947,
    "99": 8.485830749889391,
    "99.9": 14.838939306203503,
    "100": 24.951002000079825
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 1.7069829998490604,
    "95": 2.286971050023112,
    "99": 3.6268472400479324,
    "100": 22.734684999932142
  },
  "confirmed_alert_events": 0,
  "or_positive_windows": 0,
  "rail_counts": {
    "ax": 0,
    "ay": 0,
    "az": 0,
    "gx": 0,
    "gy": 0,
    "gz": 0
  },
  "throttled_end": {
    "command": [
      "vcgencmd",
      "get_throttled"
    ],
    "returncode": 0,
    "stdout": "throttled=0x0\n",
    "stderr": ""
  },
  "fifo_timing_note": "FIFO packets retain common host read-completion timestamps per batch. Zero dt within batches is intentional; these are host availability metrics, not direct physical-sample jitter measurements. No invented timestamps or decimation.",
  "conditions": "Guided operator phase: Stationary helmet confirmed by operator; INT connected to BCM23 physical pin16. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/IDE active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "data_ready": {
    "gpio_bcm": 23,
    "physical_pin": 16,
    "edges_read": 60689,
    "stale_edges_discarded": 1,
    "timeouts": 0,
    "timestamp_scope": "Samples use host read completion. Separate GPIO kernel edge timestamps and wake/read times are in gpio_edges.csv. No synthesized sample timestamps.",
    "missed_sample_scope": "Stale queued edges are discarded above 15 ms age. libgpiod v1 cannot count kernel queue overflow; edge interval gaps are diagnostic, not an exact lost-sample count.",
    "read_path": "Coherent 14-byte burst; differs from deployed polling separate reads.",
    "register_map_source": "https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6500-Register-Map2.pdf"
  },
  "score_distributions": {
    "classifier": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.0,
      "99": 0.0,
      "99.9": 0.0,
      "100": 0.0
    },
    "reconstruction": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.0,
      "99": 0.0,
      "99.9": 0.0,
      "100": 0.0
    }
  },
  "overlapping_three_positive_positions": 0,
  "classifier_crossings": 0,
  "reconstruction_crossings": 0,
  "physical_axes": {
    "ax": {
      "mean": -5.8506308132149,
      "std": 0.014471617795802912,
      "min": -6.043563540649414,
      "max": -5.685630392456054,
      "rms": 5.85064871106284
    },
    "ay": {
      "mean": -0.6066206376985167,
      "std": 0.009145240744776637,
      "min": -0.7619546783447265,
      "max": -0.45669396667480466,
      "rms": 0.606689569310397
    },
    "az": {
      "mean": -7.782199830870674,
      "std": 0.015183174904496794,
      "min": -8.009203103637695,
      "max": -7.6285250396728514,
      "rms": 7.78221464214421
    },
    "gx": {
      "mean": -0.21906829676201436,
      "std": 0.0635056526549161,
      "min": -1.6259541984732824,
      "max": 0.9618320610687022,
      "rms": 0.22808745376573622
    },
    "gy": {
      "mean": 2.0828682255178785,
      "std": 0.34922626350761465,
      "min": -3.83206106870229,
      "max": 5.740458015267175,
      "rms": 2.1119420039374863
    },
    "gz": {
      "mean": 1.0924988880682174,
      "std": 0.049455542456978425,
      "min": 0.47328244274809156,
      "max": 1.5572519083969465,
      "rms": 1.093617698791495
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.755043761559795,
      "max": 9.969597030303248
    },
    "gyro": {
      "mean": 2.3686575948638824,
      "max": 5.928585545140673
    }
  }
}
