
 — 15_iio/smoke_20261007
Status: CAPTURED; OFFLINE REVIEW PENDING
UTC: 2026-10-07T04:26:40.354477+00:00
Evidence: piResults/final_pi_review_closure/15_iio/smoke_20261007
{
  "mode": "iio",
  "seconds_requested": 30.0,
  "elapsed_s": 30.007593693000672,
  "n_samples": 1502,
  "n_windows": 97,
  "exception": null,
  "cleanup_errors": [],
  "sample_rate_hz": 50.053996843817046,
  "gap_count": 0,
  "i2c_failures": null,
  "i2c_failure_scope": "Kernel I2C failures are not counted by userspace; do not interpret null as zero.",
  "confirmed_alert_events": 0,
  "or_positive_windows": 0,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "processing_ms": {
    "50": 2.401639001618605,
    "95": 6.683096400229251,
    "99": 9.341576561564539,
    "100": 14.350053999805823
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
    "n": 1501,
    "mean_ms": 19.985926315789836,
    "median_ms": 19.985900005849544,
    "std_ms": 0.010203702075631564,
    "rms_error_from_20ms": 0.017383443942317226,
    "p90_ms": 19.986280000011902,
    "p95_ms": 19.986719998996705,
    "p99_ms": 19.998420000774786,
    "p99.9_ms": 19.998619998659706,
    "max_ms": 20.003620003990363,
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
      1501,
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
    "n": 1501,
    "mean_ms": 19.98587176748479,
    "median_ms": 19.990865999716334,
    "std_ms": 0.8216404443476971,
    "rms_error_from_20ms": 0.8217619039246616,
    "p90_ms": 20.664566996856593,
    "p95_ms": 21.17399099370232,
    "p99_ms": 22.516338001878466,
    "p99.9_ms": 25.49558549799282,
    "max_ms": 29.286996003065724,
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
      3,
      1496,
      2,
      0,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 46,
      "5": 5,
      "8": 1
    }
  },
  "physical_axes": {
    "ax": {
      "mean": -5.8280315579227695,
      "std": 0.008003483408829332,
      "min": -5.853822,
      "max": -5.8023940000000005
    },
    "ay": {
      "mean": -0.8147240386151797,
      "std": 0.008166056438952324,
      "min": -0.839592,
      "max": -0.789958
    },
    "az": {
      "mean": -7.77175411584554,
      "std": 0.013226762265844919,
      "min": -7.82184,
      "max": -7.723768
    },
    "gx": {
      "mean": -2.488368683158639,
      "std": 0.031202194442265335,
      "min": -2.5926684004346825,
      "max": -2.356278046277403
    },
    "gy": {
      "mean": 0.13592876900062306,
      "std": 0.12062974403536154,
      "min": -0.45752971772376755,
      "max": 0.5871631377455017
    },
    "gz": {
      "mean": 2.2138508525243785,
      "std": 0.03175927693628526,
      "min": 2.104636701529331,
      "max": 2.30289957920963
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
