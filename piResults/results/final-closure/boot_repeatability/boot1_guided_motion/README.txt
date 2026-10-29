
 — boot_repeatability/boot1_guided_motion
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-04T17:47:17.236072+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot1_guided_motion
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 120.0,
  "elapsed_s": 120.01308030900009,
  "n_samples": 5989,
  "sample_rate_hz": 49.9028937894103,
  "n_windows": 396,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 5988,
    "mean_ms": 20.039124321309295,
    "median_ms": 20.010933999856206,
    "std_ms": 2.794921892666119,
    "rms_error_from_20ms": 2.7951957174091175,
    "p90_ms": 22.92230339994603,
    "p95_ms": 24.364469349961837,
    "p99_ms": 28.62261392999926,
    "p99.9_ms": 35.87461290004189,
    "max_ms": 43.8281439999173,
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
      24,
      174,
      5549,
      208,
      30,
      3,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1935,
      "5": 439,
      "8": 137
    }
  },
  "nominal_positions_received_samples": 396,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.7568700002357218,
    "50": 2.369754500023191,
    "95": 7.228789499947652,
    "99": 12.80417630005104,
    "99.9": 15.625362319925722,
    "100": 16.74217899994801
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 6.922538000026179,
    "95": 11.497374599912288,
    "99": 15.597724679928431,
    "100": 28.519463000066025
  },
  "confirmed_alert_events": 1,
  "or_positive_windows": 39,
  "rail_counts": {
    "ax": 0,
    "ay": 0,
    "az": 0,
    "gx": 0,
    "gy": 4,
    "gz": 2
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
  "conditions": "Guided operator phase: Boot 1 H1 sequence: 10 seconds resting after START cue, three gentle left/right rotations, three gentle forward/back tilts, return to original resting position; execution confirmation pending. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/IDE active. No alarm countdown or communication blocks; policy events recorded only.",
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
      "95": 0.7855322957038879,
      "99": 1.1782984733581543,
      "99.9": 1.3746814727783203,
      "100": 1.3746814727783203
    }
  },
  "overlapping_three_positive_positions": 21,
  "classifier_crossings": 39,
  "reconstruction_crossings": 0,
  "physical_axes": {
    "ax": {
      "mean": -1.2505620059362574,
      "std": 2.7939485157349813,
      "min": -16.060304736328124,
      "max": 10.46984385986328,
      "rms": 3.061054334582942
    },
    "ay": {
      "mean": 1.6165746352871702,
      "std": 3.4989026669187524,
      "min": -9.670180505371093,
      "max": 13.644555261230469,
      "rms": 3.8543006400675344
    },
    "az": {
      "mean": -6.914145075190032,
      "std": 4.999582734971557,
      "min": -13.36203946533203,
      "max": 12.021286535644531,
      "rms": 8.532363661061352
    },
    "gx": {
      "mean": -1.3258174337430326,
      "std": 22.5377971577742,
      "min": -194.3587786259542,
      "max": 162.8320610687023,
      "rms": 22.576760010962417
    },
    "gy": {
      "mean": 3.9247156682926336,
      "std": 35.28217501864482,
      "min": -250.13740458015266,
      "max": 250.12977099236642,
      "rms": 35.49979249408687
    },
    "gz": {
      "mean": 0.7065625402296069,
      "std": 29.036697172821604,
      "min": -250.13740458015266,
      "max": 250.12977099236642,
      "rms": 29.04529244695949
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.826050254597945,
      "max": 19.56818161332323
    },
    "gyro": {
      "mean": 27.04217540911844,
      "max": 320.83534141142246
    }
  }
}
