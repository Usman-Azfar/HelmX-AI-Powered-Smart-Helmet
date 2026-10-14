
 — 07_high_range_benign_motion/05_repeated_tilt
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-04T09:17:06.472011+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/05_repeated_tilt
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 90.0,
  "elapsed_s": 90.00096061800002,
  "n_samples": 4434,
  "sample_rate_hz": 49.266140822870376,
  "n_windows": 282,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 4433,
    "mean_ms": 20.29604099571397,
    "median_ms": 20.048077999945235,
    "std_ms": 8.885663998794636,
    "rms_error_from_20ms": 8.89059418546468,
    "p90_ms": 23.166674599974613,
    "p95_ms": 24.651886600031503,
    "p99_ms": 31.313721440024114,
    "p99.9_ms": 52.98460024803344,
    "max_ms": 449.4268800000327,
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
      17,
      161,
      4065,
      138,
      42,
      7,
      1,
      2
    ],
    "deviation_counts": {
      "2": 1453,
      "5": 368,
      "8": 130
    }
  },
  "nominal_positions_received_samples": 292,
  "C_D": 0.9657534246575342,
  "V_T_scored_over_scored_plus_resets": 0.9894736842105263,
  "p_valid_90_sample_position": 0.9385500575373993,
  "gap_count": 3,
  "processing_ms": {
    "0": 1.8325990001812897,
    "50": 2.4808500000119693,
    "95": 9.436523149986431,
    "99": 17.215092089966213,
    "99.9": 33.03739325893876,
    "100": 34.20653899991066
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 6.982829999969908,
    "95": 12.84610209999925,
    "99": 17.526769740018725,
    "100": 47.73571800001264
  },
  "confirmed_alert_events": 1,
  "or_positive_windows": 5,
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
  "conditions": "Guided operator phase: Repeated tilt: operator confirmed ready; hold still during recorder startup, then after separate START cue slowly tilt helmet forward and back in both hands. Ninety seconds total including pre-cue baseline.. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/agent active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "score_distributions": {
    "classifier": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.9166015624999997,
      "99": 0.99609375,
      "99.9": 0.99609375,
      "100": 0.99609375
    },
    "reconstruction": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.39276614785194397,
      "99": 1.019228147268295,
      "99.9": 1.1782984733581543,
      "100": 1.1782984733581543
    }
  },
  "overlapping_three_positive_positions": 3,
  "classifier_crossings": 5,
  "reconstruction_crossings": 0,
  "physical_axes": {
    "ax": {
      "mean": 6.906326852043954,
      "std": 3.5645832396237087,
      "min": -8.877699755859375,
      "max": 15.423447094726562,
      "rms": 7.7719755699223345
    },
    "ay": {
      "mean": 1.729531537925159,
      "std": 2.6096203861254565,
      "min": -13.804966772460936,
      "max": 12.090718383789062,
      "rms": 3.1307184319831993
    },
    "az": {
      "mean": -1.2759258970048117,
      "std": 4.9718905334675325,
      "min": -23.022643164062497,
      "max": 5.702988354492187,
      "rms": 5.132999354318253
    },
    "gx": {
      "mean": 1.1841424909512963,
      "std": 22.532145101283575,
      "min": -214.69512195121953,
      "max": 278.109756097561,
      "rms": 22.563239047268322
    },
    "gy": {
      "mean": 3.4839571162964678,
      "std": 22.749141096438482,
      "min": -242.8658536585366,
      "max": 321.0975609756098,
      "rms": 23.014373287444936
    },
    "gz": {
      "mean": 1.5301385084216201,
      "std": 28.197858574456536,
      "min": -262.6829268292683,
      "max": 565.4268292682927,
      "rms": 28.239344044081598
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.805761439269482,
      "max": 30.75538222844458
    },
    "gyro": {
      "mean": 18.988783788121033,
      "max": 631.9735848806599
    }
  }
}
