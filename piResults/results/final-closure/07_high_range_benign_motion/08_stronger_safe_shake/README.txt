
 — 07_high_range_benign_motion/08_stronger_safe_shake
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-04T09:27:10.761280+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/08_stronger_safe_shake
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 90.0,
  "elapsed_s": 90.00714668399996,
  "n_samples": 4498,
  "sample_rate_hz": 49.97380947750433,
  "n_windows": 296,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 4497,
    "mean_ms": 20.009927913720233,
    "median_ms": 20.024890999820855,
    "std_ms": 2.1709911672817226,
    "rms_error_from_20ms": 2.171013867271716,
    "p90_ms": 22.329062800008614,
    "p95_ms": 23.383617600120488,
    "p99_ms": 26.286900200029777,
    "p99.9_ms": 31.14294131204773,
    "max_ms": 43.56359399980647,
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
      4,
      77,
      4327,
      79,
      9,
      1,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1139,
      "5": 170,
      "8": 33
    }
  },
  "nominal_positions_received_samples": 296,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.7542949999551638,
    "50": 2.0062049998159637,
    "95": 4.594884999846727,
    "99": 7.792995949967022,
    "99.9": 14.6647590149703,
    "100": 16.411507999919195
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 6.388775999994323,
    "95": 9.493039600033615,
    "99": 12.047493389861739,
    "100": 27.594019999924058
  },
  "confirmed_alert_events": 0,
  "or_positive_windows": 2,
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
  "conditions": "Guided operator phase: Stronger safe shake: operator ready; still baseline before separate START cue, then slightly firmer controlled hand-held movements than moderate shake, secure two-handed grip, no impacts or wire strain. Ninety seconds including baseline. Amplitude not measured or matched.. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/IDE active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "score_distributions": {
    "classifier": {
      "0": 0.0,
      "50": 0.4140625,
      "95": 0.96484375,
      "99": 0.98828125,
      "99.9": 0.9949414062500002,
      "100": 0.99609375
    },
    "reconstruction": {
      "0": 0.0,
      "50": 0.19638307392597198,
      "95": 0.39276614785194397,
      "99": 0.39276614785194397,
      "99.9": 0.5891492366790771,
      "100": 0.5891492366790771
    }
  },
  "overlapping_three_positive_positions": 0,
  "classifier_crossings": 2,
  "reconstruction_crossings": 0,
  "physical_axes": {
    "ax": {
      "mean": 3.0956111941841775,
      "std": 3.5734931402881585,
      "min": -11.042058056640624,
      "max": 15.95495986328125,
      "rms": 4.727860180805362
    },
    "ay": {
      "mean": 5.325795669022386,
      "std": 4.472963310804149,
      "min": -3.907337109375,
      "max": 18.44971799316406,
      "rms": 6.954962277969423
    },
    "az": {
      "mean": -4.399769778799258,
      "std": 2.854022716795828,
      "min": -11.271901416015623,
      "max": 0.6416460449218749,
      "rms": 5.244370293411965
    },
    "gx": {
      "mean": 5.431357025886844,
      "std": 38.831492538589195,
      "min": -267.8048780487805,
      "max": 208.109756097561,
      "rms": 39.209494410374106
    },
    "gy": {
      "mean": 1.2146319773557905,
      "std": 80.45128541226224,
      "min": -349.81707317073176,
      "max": 325.0,
      "rms": 80.46045398408894
    },
    "gz": {
      "mean": 2.499403528939691,
      "std": 68.91889586684863,
      "min": -217.8048780487805,
      "max": 244.32926829268294,
      "rms": 68.96420249307609
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.856641659512107,
      "max": 20.412224806019555
    },
    "gyro": {
      "mean": 92.54861573506068,
      "max": 409.1144529756331
    }
  }
}
