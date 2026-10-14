
 — boot_repeatability/boot2_stationary
Status: COMPLETE (UNATTENDED)
UTC: 2026-10-05T14:31:51.488365+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot2_stationary
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 300.0,
  "elapsed_s": 300.00589979299997,
  "n_samples": 14991,
  "sample_rate_hz": 49.96901731047152,
  "n_windows": 996,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 14990,
    "mean_ms": 20.012004165310206,
    "median_ms": 19.97993449998603,
    "std_ms": 2.4560760107518083,
    "rms_error_from_20ms": 2.45610534598484,
    "p90_ms": 22.546186499999976,
    "p95_ms": 23.899651350008355,
    "p99_ms": 27.580413160016803,
    "p99.9_ms": 33.5522978370099,
    "max_ms": 38.98565399998688,
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
      36,
      374,
      14144,
      382,
      54,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 4158,
      "5": 846,
      "8": 234
    }
  },
  "nominal_positions_received_samples": 996,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.82911500002092,
    "50": 2.528572000031204,
    "95": 7.69917999999592,
    "99": 11.369419500009299,
    "99.9": 13.209530984976402,
    "100": 14.55198200005725
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 7.076713000003565,
    "95": 10.620368999994412,
    "99": 13.500275899994564,
    "100": 23.77627699999607
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
  "conditions": "Unattended, desktop/agent state in metadata. No physical mounting confirmation. No alarm countdown or communication blocks; policy events recorded only.",
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
      "mean": -1.9468060070832536,
      "std": 0.02728127158148948,
      "min": -2.1452046874999997,
      "max": -1.8411410766601561,
      "rms": 1.946997148686804
    },
    "ay": {
      "mean": -0.7077929928098461,
      "std": 0.026232006693294417,
      "min": -0.9193734375,
      "max": -0.6009446166992187,
      "rms": 0.7082789272919785
    },
    "az": {
      "mean": -9.534995232978817,
      "std": 0.055042519927195464,
      "min": -9.758765966796874,
      "max": -9.349357482910156,
      "rms": 9.535154103208228
    },
    "gx": {
      "mean": -0.25295584475367155,
      "std": 0.44182273362621244,
      "min": -1.9541984732824427,
      "max": 1.9465648854961832,
      "rms": 0.5091109774341765
    },
    "gy": {
      "mean": 2.1004918472712126,
      "std": 0.6462182296898055,
      "min": 0.0,
      "max": 3.900763358778626,
      "rms": 2.1976496537974968
    },
    "gz": {
      "mean": 1.1207599877992955,
      "std": 0.178229711073791,
      "min": -0.29770992366412213,
      "max": 2.5572519083969465,
      "rms": 1.1348430641112117
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.75749463004538,
      "max": 9.976896005794565
    },
    "gyro": {
      "mean": 2.4723085845739985,
      "max": 4.593098751904515
    }
  }
}
