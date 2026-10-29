
 — boot_repeatability/boot4_warm_stationary
Status: COMPLETE (UNATTENDED)
UTC: 2026-10-05T18:24:46.673501+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot4_warm_stationary
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 600.0,
  "elapsed_s": 600.0022906589998,
  "n_samples": 29999,
  "sample_rate_hz": 49.99814245217504,
  "n_windows": 1996,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 29998,
    "mean_ms": 20.00041241616107,
    "median_ms": 19.994384500023443,
    "std_ms": 1.1339532932212208,
    "rms_error_from_20ms": 1.1339533682186151,
    "p90_ms": 21.33163250000507,
    "p95_ms": 21.817853099878448,
    "p99_ms": 23.38443771969196,
    "p99.9_ms": 27.164517920758822,
    "max_ms": 41.15462000027037,
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
      8,
      73,
      29828,
      82,
      6,
      1,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1867,
      "5": 170,
      "8": 35
    }
  },
  "nominal_positions_received_samples": 1996,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.6198789999180008,
    "50": 1.740543999858346,
    "95": 2.362464999578151,
    "99": 3.6997150502884293,
    "99.9": 8.587932654336486,
    "100": 18.550271000094654
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 5.898583000089275,
    "95": 7.0190132002153405,
    "99": 9.093822900522355,
    "100": 20.71880700032125
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
  "conditions": "Unattended, desktop/IDE state in metadata. No physical mounting confirmation. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
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
      "mean": -2.2488247999856017,
      "std": 0.044548338507922086,
      "min": -2.4516625,
      "max": -1.9943699829101562,
      "rms": 2.249265999274896
    },
    "ay": {
      "mean": 0.7887511772666185,
      "std": 0.04882949809022477,
      "min": 0.612915625,
      "max": 1.0869675537109373,
      "rms": 0.7902611843708509
    },
    "az": {
      "mean": -9.463154329163267,
      "std": 0.05270959358176557,
      "min": -9.65342109375,
      "max": -9.200916979980468,
      "rms": 9.46330112375259
    },
    "gx": {
      "mean": -0.21451860100171274,
      "std": 0.8727450564743034,
      "min": -4.0534351145038165,
      "max": 3.900763358778626,
      "rms": 0.8987225176749868
    },
    "gy": {
      "mean": 2.1161242270416647,
      "std": 0.6576501180640094,
      "min": -0.40458015267175573,
      "max": 5.854961832061068,
      "rms": 2.215961511863933
    },
    "gz": {
      "mean": 1.088394803999828,
      "std": 3.0170337238215086,
      "min": -13.557251908396946,
      "max": 16.068702290076335,
      "rms": 3.207350267752199
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.758852056500535,
      "max": 9.989787132787797
    },
    "gyro": {
      "mean": 3.658353169823236,
      "max": 16.523122504459025
    }
  }
}
