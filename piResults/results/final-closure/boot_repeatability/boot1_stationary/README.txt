
 — boot_repeatability/boot1_stationary
Status: COMPLETE (UNATTENDED)
UTC: 2026-10-04T17:39:40.068401+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot1_stationary
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 600.0,
  "elapsed_s": 600.0190184579999,
  "n_samples": 29997,
  "sample_rate_hz": 49.993415337216895,
  "n_windows": 1996,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 29996,
    "mean_ms": 20.002192801040138,
    "median_ms": 19.996806999984074,
    "std_ms": 1.7164298218974587,
    "rms_error_from_20ms": 1.7164312225881186,
    "p90_ms": 21.75382149999905,
    "p95_ms": 22.49819150001997,
    "p99_ms": 25.339696450004823,
    "p99.9_ms": 30.0608402600538,
    "max_ms": 39.721091000018305,
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
      33,
      298,
      29323,
      311,
      31,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 4192,
      "5": 673,
      "8": 164
    }
  },
  "nominal_positions_received_samples": 1996,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.5852799998583578,
    "50": 1.9033090000277753,
    "95": 4.678654750097877,
    "99": 7.814320649985951,
    "99.9": 14.57323461500842,
    "100": 16.43528500000002
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 5.985542000018995,
    "95": 8.767885999998265,
    "99": 11.243866399963737,
    "100": 22.32332599999154
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
      "99.9": 0.003925781250000426,
      "100": 0.05078125
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
      "mean": -2.54391768186218,
      "std": 0.051595781468997626,
      "min": -4.211400720214844,
      "max": 0.20829554443359374,
      "rms": 2.544440861320311
    },
    "ay": {
      "mean": -1.7925436596373667,
      "std": 0.04800353193204786,
      "min": -4.673481640625,
      "max": -0.6823474731445313,
      "rms": 1.7931863011923983
    },
    "az": {
      "mean": -9.27326094739601,
      "std": 0.05922687642664562,
      "min": -13.333309045410155,
      "max": -8.097190014648437,
      "rms": 9.273450081894612
    },
    "gx": {
      "mean": -0.22283271584155873,
      "std": 0.8979706633519972,
      "min": -19.290076335877863,
      "max": 29.083969465648856,
      "rms": 0.9252057779165404
    },
    "gy": {
      "mean": 2.1357107720950212,
      "std": 1.0284812688607705,
      "min": -32.412213740458014,
      "max": 33.38167938931298,
      "rms": 2.370450215136393
    },
    "gz": {
      "mean": 1.0481226239672312,
      "std": 1.7345243033018887,
      "min": -51.70229007633588,
      "max": 48.786259541984734,
      "rms": 2.0266069164040807
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.781766658424466,
      "max": 14.309032100856426
    },
    "gyro": {
      "mean": 2.8400245962389907,
      "max": 62.29849048843556
    }
  }
}
