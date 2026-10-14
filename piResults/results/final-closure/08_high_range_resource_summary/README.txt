
C4 — High-range live resource and restoration supplement
Status: COMPLETE (UNATTENDED)
UTC: 2026-10-02T15:01:35.363774+00:00
Evidence: piResults/final_pi_review_closure/08_high_range_resource_summary
{
  "primary_evidence": "piResults/final_pi_review_closure/08_high_range_20min",
  "resources_sha256": "368a27738167d5108ff12ef30f9570ce156f6a11a69e1684660a50ff7fc50f91",
  "resource_samples": 1188,
  "resources": {
    "cpu_pct": {
      "min": 0.0,
      "median": 3.9,
      "p95": 10.0,
      "max": 13.1,
      "first": 0.0,
      "last": 2.0
    },
    "rss_bytes": {
      "min": 50008064.0,
      "median": 51773440.0,
      "p95": 52760576.0,
      "max": 52867072.0,
      "first": 50008064.0,
      "last": 52867072.0
    },
    "cpu_temp_c": {
      "min": 54.53,
      "median": 56.965,
      "p95": 59.4,
      "max": 61.835,
      "first": 58.913,
      "last": 55.991
    },
    "sensor_temp_raw": {
      "min": 3461.0,
      "median": 4715.0,
      "p95": 4784.0,
      "max": 4795.0,
      "first": 3461.0,
      "last": 4783.0
    }
  },
  "restored_configuration_fields": {
    "06_high_range_register_check": {
      "SMPLRT_DIV": true,
      "CONFIG": true,
      "GYRO_CONFIG": true,
      "ACCEL_CONFIG": true,
      "ACCEL_CONFIG2": true,
      "FIFO_EN": true,
      "USER_CTRL": true,
      "INT_ENABLE": true,
      "PWR_MGMT_1": true,
      "PWR_MGMT_2": true
    },
    "06_high_range_stationary": {
      "SMPLRT_DIV": true,
      "CONFIG": true,
      "GYRO_CONFIG": true,
      "ACCEL_CONFIG": true,
      "ACCEL_CONFIG2": true,
      "FIFO_EN": true,
      "USER_CTRL": true,
      "INT_ENABLE": true,
      "PWR_MGMT_1": true,
      "PWR_MGMT_2": true
    },
    "08_high_range_20min": {
      "SMPLRT_DIV": true,
      "CONFIG": true,
      "GYRO_CONFIG": true,
      "ACCEL_CONFIG": true,
      "ACCEL_CONFIG2": true,
      "FIFO_EN": true,
      "USER_CTRL": true,
      "INT_ENABLE": true,
      "PWR_MGMT_1": true,
      "PWR_MGMT_2": true
    }
  },
  "summary": {
    "mode": "polling",
    "fifo_overflows": 0,
    "seconds_requested": 1200.0,
    "elapsed_s": 1200.0198600850001,
    "n_samples": 59913,
    "sample_rate_hz": 49.926673710013624,
    "n_windows": 3988,
    "i2c_failures": 0,
    "exception": null,
    "timing": {
      "n": 59912,
      "mean_ms": 20.029271011032844,
      "median_ms": 19.99338600012379,
      "std_ms": 2.0759725796795268,
      "rms_error_from_20ms": 2.07617892862541,
      "p90_ms": 21.94020809988615,
      "p95_ms": 23.17431765005722,
      "p99_ms": 26.602031579950562,
      "p99.9_ms": 35.140314756922365,
      "max_ms": 64.73739800003386,
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
        82,
        801,
        57843,
        992,
        177,
        16,
        1,
        0
      ],
      "deviation_counts": {
        "2": 10992,
        "5": 2069,
        "8": 605
      }
    },
    "nominal_positions_received_samples": 3991,
    "C_D": 0.9992483086945627,
    "V_T_scored_over_scored_plus_resets": 0.9997493106041614,
    "p_valid_90_sample_position": 0.9985123027547472,
    "gap_count": 1,
    "processing_ms": {
      "0": 1.6230589999395306,
      "50": 1.874735499882263,
      "95": 5.826936350024417,
      "99": 9.768649890102106,
      "99.9": 19.0267803998668,
      "100": 22.54888600009508
    },
    "processing_over_300ms": 0,
    "sensor_read_ms": {
      "50": 5.990252000174223,
      "95": 10.360325199872017,
      "99": 14.054026039930195,
      "100": 41.750645000092845
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
        "mean": 1.8844082604248815,
        "std": 0.009120766527344367,
        "min": 1.838746875,
        "max": 1.924938134765625,
        "rms": 1.8844303331085432
      },
      "ay": {
        "mean": -1.6580704665604644,
        "std": 0.008604309775308202,
        "min": -1.6903063720703124,
        "max": -1.6232687255859375,
        "rms": 1.6580927918023
      },
      "az": {
        "mean": -9.438148665133536,
        "std": 0.014503086348764588,
        "min": -9.548076220703125,
        "max": -9.370905297851563,
        "rms": 9.438159808176357
      },
      "gx": {
        "mean": -0.2549112880343165,
        "std": 0.03735196978815407,
        "min": -0.6707317073170732,
        "max": 0.12195121951219513,
        "rms": 0.25763333327496546
      },
      "gy": {
        "mean": 2.1102895947090765,
        "std": 0.05213878413258218,
        "min": 1.2195121951219514,
        "max": 2.9268292682926833,
        "rms": 2.1109335911743456
      },
      "gz": {
        "mean": 1.040656309372167,
        "std": 0.09632475721825597,
        "min": 0.06097560975609757,
        "max": 2.3170731707317076,
        "rms": 1.0451047856981879
      }
    },
    "magnitudes": {
      "accel": {
        "mean": 9.76621765727687,
        "max": 9.879602873473125
      },
      "gyro": {
        "mean": 2.3689278916628185,
        "max": 2.9376071879136356
      }
    }
  },
  "limits": "No independently confirmed mounting/stationarity. Scores and timing characterize technical compatibility, not crash sensitivity. RSS includes research recording buffers."
}
