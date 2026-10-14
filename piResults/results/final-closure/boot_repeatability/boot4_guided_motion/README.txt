
 — boot_repeatability/boot4_guided_motion
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-05T18:32:21.331942+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot4_guided_motion
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 120.0,
  "elapsed_s": 120.004649556,
  "n_samples": 5998,
  "sample_rate_hz": 49.981396739140855,
  "n_windows": 396,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 5997,
    "mean_ms": 20.007326479906638,
    "median_ms": 20.026858000164793,
    "std_ms": 2.1240219254432344,
    "rms_error_from_20ms": 2.1240345611763023,
    "p90_ms": 22.456294800031177,
    "p95_ms": 23.49477739971917,
    "p99_ms": 25.718329759911285,
    "p99.9_ms": 31.28434226048598,
    "max_ms": 36.35384100016381,
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
      4,
      96,
      5791,
      98,
      8,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1551,
      "5": 206,
      "8": 27
    }
  },
  "nominal_positions_received_samples": 396,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.7583689996172325,
    "50": 2.0448344998840184,
    "95": 3.8104204995761393,
    "99": 7.836801249823124,
    "99.9": 11.605993329844758,
    "100": 11.754254999686964
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 6.507788500130118,
    "95": 9.677678800335343,
    "99": 12.108810080198955,
    "100": 19.851639999615145
  },
  "confirmed_alert_events": 1,
  "or_positive_windows": 38,
  "rail_counts": {
    "ax": 0,
    "ay": 0,
    "az": 0,
    "gx": 0,
    "gy": 2,
    "gz": 1
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
  "conditions": "Guided operator phase: boot4_gentle_rotations_and_tilts. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/agent active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "score_distributions": {
    "classifier": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.99609375,
      "99": 0.99609375,
      "99.9": 0.99609375,
      "100": 0.99609375
    },
    "reconstruction": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.5891492366790771,
      "99": 0.9819153547286987,
      "99.9": 0.9819153547286987,
      "100": 0.9819153547286987
    }
  },
  "overlapping_three_positive_positions": 25,
  "classifier_crossings": 38,
  "reconstruction_crossings": 0,
  "physical_axes": {
    "ax": {
      "mean": -0.7752371487252748,
      "std": 2.8072916339737195,
      "min": -13.632584252929687,
      "max": 15.978901879882812,
      "rms": 2.9123665557313574
    },
    "ay": {
      "mean": 3.4382276623172894,
      "std": 3.476517882991408,
      "min": -6.995857250976562,
      "max": 12.473790649414061,
      "rms": 4.889538429001543
    },
    "az": {
      "mean": -4.9906926039290935,
      "std": 6.307374601114513,
      "min": -17.62850682373047,
      "max": 11.604695446777344,
      "rms": 8.043008580481374
    },
    "gx": {
      "mean": -0.2831898164528126,
      "std": 21.823316241127966,
      "min": -186.23664122137404,
      "max": 213.85496183206106,
      "rms": 21.825153567212812
    },
    "gy": {
      "mean": 3.3107422575973158,
      "std": 33.49979704174896,
      "min": -250.13740458015266,
      "max": 221.64885496183206,
      "rms": 33.66299772947462
    },
    "gz": {
      "mean": 1.124196615156706,
      "std": 21.25769157397986,
      "min": -250.13740458015266,
      "max": 196.46564885496184,
      "rms": 21.287396954160084
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.83786874920672,
      "max": 19.41550124686834
    },
    "gyro": {
      "mean": 26.98130212458825,
      "max": 356.4369965338982
    }
  }
}
