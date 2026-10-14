
 — 05_corrected_aba/A1_polling
Status: COMPLETE (UNATTENDED)
UTC: 2026-09-29T20:27:56.472690+00:00
Evidence: piResults/final_pi_review_closure/05_corrected_aba/A1_polling
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 1200.0,
  "elapsed_s": 1200.0134424690004,
  "n_samples": 59837,
  "sample_rate_hz": 49.863608091661646,
  "n_windows": 3986,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 59836,
    "mean_ms": 20.05469568184706,
    "median_ms": 19.826534500680282,
    "std_ms": 3.1105903414593543,
    "rms_error_from_20ms": 3.111071180476741,
    "p90_ms": 23.59726450049493,
    "p95_ms": 25.033662750502117,
    "p99_ms": 29.019639049329275,
    "p99.9_ms": 38.14885622998337,
    "max_ms": 57.648023997899145,
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
      250,
      2140,
      54416,
      2595,
      399,
      36,
      0,
      0
    ],
    "deviation_counts": {
      "2": 24648,
      "5": 5420,
      "8": 1510
    }
  },
  "nominal_positions_received_samples": 3986,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.8183750034950208,
    "50": 2.766225998129812,
    "95": 8.207354251680954,
    "99": 13.268392601457894,
    "99.9": 18.25069826189108,
    "100": 22.783658998378087
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 7.657756999833509,
    "95": 12.237275597726693,
    "99": 16.186133361188695,
    "100": 48.950368000078015
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
      "mean": 1.4072898652476107,
      "std": 0.01210529980840495,
      "min": 1.2497732666015624,
      "max": 1.5316905120849609,
      "rms": 1.4073419282861184
    },
    "ay": {
      "mean": -0.9151836246067869,
      "std": 0.018833176767998127,
      "min": -1.0726023437499999,
      "max": -0.766743081665039,
      "rms": 0.9153773840857065
    },
    "az": {
      "mean": -9.611623755198101,
      "std": 0.014390816904125478,
      "min": -9.76116016845703,
      "max": -9.387066159057616,
      "rms": 9.611634528377555
    },
    "gx": {
      "mean": -0.1556792900611547,
      "std": 0.11792816043791368,
      "min": -1.9541984732824427,
      "max": 1.9465648854961832,
      "rms": 0.19530256623561157
    },
    "gy": {
      "mean": 2.159229902813585,
      "std": 0.18201668399195936,
      "min": 0.0,
      "max": 3.900763358778626,
      "rms": 2.1668880558200954
    },
    "gz": {
      "mean": 1.1142096333716776,
      "std": 0.34716477757210606,
      "min": -1.5648854961832062,
      "max": 4.374045801526718,
      "rms": 1.1670417686976493
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.757142927209014,
      "max": 9.905209159661595
    },
    "gyro": {
      "mean": 2.461562225051317,
      "max": 4.754254609482913
    }
  }
}
