
 — 15_iio/stationary_20min_20261007
Status: CAPTURED; OFFLINE REVIEW PENDING
UTC: 2026-10-07T04:50:48.948025+00:00
Evidence: piResults/final_pi_review_closure/15_iio/stationary_20min_20261007
{
  "mode": "iio",
  "seconds_requested": 1200.0,
  "elapsed_s": 1200.0044833249995,
  "n_samples": 60043,
  "n_windows": 3999,
  "exception": null,
  "cleanup_errors": [],
  "sample_rate_hz": 50.035646394946376,
  "gap_count": 0,
  "i2c_failures": null,
  "i2c_failure_scope": "Kernel I2C failures are not counted by userspace; do not interpret null as zero.",
  "confirmed_alert_events": 0,
  "or_positive_windows": 0,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "processing_ms": {
    "50": 2.4061570074991323,
    "95": 8.263435695698718,
    "99": 15.278337101044599,
    "100": 36.291153002821375
  },
  "timestamp_scope": "Kernel FIFO timestamp reconstruction, not physical clock measurement. Host availability time is separately preserved.",
  "conditions": "Operator confirmed untouched on GPIO23 before test; desktop/IDE active. No alarm/SMS.",
  "throttled_end": {
    "command": [
      "vcgencmd",
      "get_throttled"
    ],
    "returncode": 0,
    "stdout": "throttled=0x0\n",
    "stderr": ""
  },
  "timing": {
    "n": 60042,
    "mean_ms": 19.985975860564274,
    "median_ms": 19.98594000178855,
    "std_ms": 0.020706682714117228,
    "rms_error_from_20ms": 0.02500886234789154,
    "p90_ms": 19.986639999842737,
    "p95_ms": 19.997739997052122,
    "p99_ms": 20.00026000016078,
    "p99.9_ms": 20.01967294119823,
    "max_ms": 20.400000001245644,
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
      0,
      0,
      60042,
      0,
      0,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 0,
      "5": 0,
      "8": 0
    }
  },
  "host_availability_timing": {
    "n": 60042,
    "mean_ms": 19.985976385030526,
    "median_ms": 19.979755001259036,
    "std_ms": 1.2357474045499752,
    "rms_error_from_20ms": 1.2358269739849557,
    "p90_ms": 20.94596050083055,
    "p95_ms": 21.595637048085337,
    "p99_ms": 23.82436868232616,
    "p99.9_ms": 28.29975912041139,
    "max_ms": 45.92880100244656,
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
      42,
      227,
      59483,
      258,
      28,
      4,
      0,
      0
    ],
    "deviation_counts": {
      "2": 4156,
      "5": 559,
      "8": 148
    }
  },
  "physical_axes": {
    "ax": {
      "mean": -5.829150722848625,
      "std": 0.008204900823988335,
      "min": -5.862792,
      "max": -5.7916300000000005
    },
    "ay": {
      "mean": -0.8133848638808853,
      "std": 0.008251144043613262,
      "min": -0.883246,
      "max": -0.749294
    },
    "az": {
      "mean": -7.771637261096215,
      "std": 0.013222072701205357,
      "min": -7.826026,
      "max": -7.709416
    },
    "gx": {
      "mean": -2.506909232735851,
      "std": 0.03175428658944441,
      "min": -2.7146763251610206,
      "max": -2.379154532163591
    },
    "gy": {
      "mean": 0.12601060172823664,
      "std": 0.1312469701896051,
      "min": -0.907433940152139,
      "max": 1.1743262754910033
    },
    "gz": {
      "mean": 2.22632737882886,
      "std": 0.032756312177184464,
      "min": 2.081760215643142,
      "max": 2.371529036868195
    }
  },
  "score_distributions": {
    "classifier": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.0,
      "99": 0.0,
      "100": 0.0
    },
    "reconstruction": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.0,
      "99": 0.0,
      "100": 0.0
    }
  }
}
