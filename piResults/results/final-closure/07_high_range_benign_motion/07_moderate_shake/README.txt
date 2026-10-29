
 — 07_high_range_benign_motion/07_moderate_shake
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-04T09:24:04.198018+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/07_moderate_shake
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 90.0,
  "elapsed_s": 90.01368330399998,
  "n_samples": 4497,
  "sample_rate_hz": 49.95907105381349,
  "n_windows": 296,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 4496,
    "mean_ms": 20.014782467526693,
    "median_ms": 20.022295499927623,
    "std_ms": 2.2720994027426933,
    "rms_error_from_20ms": 2.272147490214903,
    "p90_ms": 22.423169499973028,
    "p95_ms": 23.507300750054583,
    "p99_ms": 26.690527149975203,
    "p99.9_ms": 34.16786405998795,
    "max_ms": 38.57369499996821,
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
      3,
      95,
      4292,
      96,
      10,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1133,
      "5": 204,
      "8": 49
    }
  },
  "nominal_positions_received_samples": 296,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.7834970001331385,
    "50": 2.0672484999977314,
    "95": 4.768201749897116,
    "99": 12.207933100017977,
    "99.9": 17.666500210066296,
    "100": 17.934054000079414
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 6.47055799993268,
    "95": 9.877844200013893,
    "99": 13.000084320074164,
    "100": 26.000981000038337
  },
  "confirmed_alert_events": 0,
  "or_positive_windows": 1,
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
  "conditions": "Guided operator phase: Moderate shake: operator ready; still baseline before separate START cue, then small controlled back-and-forth shaking while holding helmet securely in both hands. No impacts. Ninety seconds including baseline.. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/IDE active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "score_distributions": {
    "classifier": {
      "0": 0.0,
      "50": 0.33203125,
      "95": 0.95703125,
      "99": 0.98046875,
      "99.9": 0.9910351562500002,
      "100": 0.9921875
    },
    "reconstruction": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.19638307392597198,
      "99": 0.19638307392597198,
      "99.9": 0.19638307392597198,
      "100": 0.19638307392597198
    }
  },
  "overlapping_three_positive_positions": 0,
  "classifier_crossings": 1,
  "reconstruction_crossings": 0,
  "physical_axes": {
    "ax": {
      "mean": 3.499332563619887,
      "std": 2.6879270651323193,
      "min": -3.4859576171874997,
      "max": 10.09395419921875,
      "rms": 4.41251405644009
    },
    "ay": {
      "mean": 6.875162228437665,
      "std": 3.1342805950028194,
      "min": -0.718260498046875,
      "max": 13.953407275390624,
      "rms": 7.555896407147678
    },
    "az": {
      "mean": -2.9902093340058737,
      "std": 3.2010668828630457,
      "min": -10.280701928710936,
      "max": 3.6439749267578123,
      "rms": 4.380431605417255
    },
    "gx": {
      "mean": 0.13830358450348998,
      "std": 20.16486057645249,
      "min": -93.84146341463415,
      "max": 137.9268292682927,
      "rms": 20.165334858346743
    },
    "gy": {
      "mean": 2.168206988941136,
      "std": 47.9693476688099,
      "min": -222.7439024390244,
      "max": 203.78048780487808,
      "rms": 48.01832397447928
    },
    "gz": {
      "mean": 1.5663694495517335,
      "std": 39.16628026906137,
      "min": -141.09756097560978,
      "max": 115.97560975609757,
      "rms": 39.19758950965167
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.761659477800682,
      "max": 14.165648554013005
    },
    "gyro": {
      "mean": 53.51233541438742,
      "max": 223.12443708822425
    }
  }
}
