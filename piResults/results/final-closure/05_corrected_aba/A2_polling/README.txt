
 — 05_corrected_aba/A2_polling
Status: COMPLETE (UNATTENDED)
UTC: 2026-09-29T21:08:05.783514+00:00
Evidence: piResults/final_pi_review_closure/05_corrected_aba/A2_polling
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 1200.0,
  "elapsed_s": 1200.0018160379987,
  "n_samples": 59956,
  "sample_rate_hz": 49.96325772068787,
  "n_windows": 3994,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 59955,
    "mean_ms": 20.014648010774728,
    "median_ms": 19.99355999942054,
    "std_ms": 1.937559030604141,
    "rms_error_from_20ms": 1.937614399537564,
    "p90_ms": 21.89036420022603,
    "p95_ms": 22.9763533006917,
    "p99_ms": 26.09647359931841,
    "p99.9_ms": 32.33873440213352,
    "max_ms": 57.912195999961114,
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
      84,
      659,
      58171,
      920,
      109,
      12,
      0,
      0
    ],
    "deviation_counts": {
      "2": 10407,
      "5": 1784,
      "8": 464
    }
  },
  "nominal_positions_received_samples": 3994,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.5813400059414562,
    "50": 1.8121534994861577,
    "95": 5.144034899240068,
    "99": 8.963803950573496,
    "99.9": 14.735894573856095,
    "100": 31.029666995891603
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 5.948688500211574,
    "95": 10.017335248448944,
    "99": 12.99715029708749,
    "100": 50.2162140001019
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
      "mean": 1.411497563534507,
      "std": 0.011665413149160643,
      "min": 1.2605471740722656,
      "max": 1.5316905120849609,
      "rms": 1.4115457674931375
    },
    "ay": {
      "mean": -0.9157133011130463,
      "std": 0.018499394739005064,
      "min": -1.0726023437499999,
      "max": -0.766743081665039,
      "rms": 0.9159001459990398
    },
    "az": {
      "mean": -9.610602596423087,
      "std": 0.014278981785720984,
      "min": -9.78689783630371,
      "max": -9.498995086669922,
      "rms": 9.610613203937353
    },
    "gx": {
      "mean": -0.15338436481918802,
      "std": 0.10787881064595993,
      "min": -1.9541984732824427,
      "max": 1.9312977099236641,
      "rms": 0.18752226843063904
    },
    "gy": {
      "mean": 2.1640233372157387,
      "std": 0.17359079199708802,
      "min": 0.0,
      "max": 3.900763358778626,
      "rms": 2.170974612260706
    },
    "gz": {
      "mean": 1.114289028239029,
      "std": 0.33831124697384013,
      "min": -1.4809160305343512,
      "max": 3.3435114503816794,
      "rms": 1.1645147222267629
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.75679337734407,
      "max": 9.933804054449652
    },
    "gyro": {
      "mean": 2.464000106456826,
      "max": 4.322862413272985
    }
  }
}
