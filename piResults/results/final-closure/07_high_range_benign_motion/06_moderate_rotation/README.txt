
 — 07_high_range_benign_motion/06_moderate_rotation
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-04T09:21:38.236684+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/06_moderate_rotation
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 90.0,
  "elapsed_s": 90.01917903599997,
  "n_samples": 4496,
  "sample_rate_hz": 49.94491227477185,
  "n_windows": 296,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 4495,
    "mean_ms": 20.020927161512784,
    "median_ms": 20.055266000099436,
    "std_ms": 2.324047948159166,
    "rms_error_from_20ms": 2.324142166785804,
    "p90_ms": 22.49142360001315,
    "p95_ms": 23.530253499973245,
    "p99_ms": 26.962166800030907,
    "p99.9_ms": 35.27787777194487,
    "max_ms": 41.307875000029526,
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
      7,
      98,
      4289,
      88,
      12,
      1,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1164,
      "5": 206,
      "8": 47
    }
  },
  "nominal_positions_received_samples": 296,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.7697890000363259,
    "50": 2.3354815000402596,
    "95": 5.24642299993161,
    "99": 8.883956800133321,
    "99.9": 14.09782430003769,
    "100": 14.841537000052085
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 6.414690000042356,
    "95": 9.936566999982688,
    "99": 13.320764800022292,
    "100": 26.680085000066356
  },
  "confirmed_alert_events": 1,
  "or_positive_windows": 4,
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
  "conditions": "Guided operator phase: Moderate rotation: operator ready; still baseline until separate START cue, then smooth left-right turns in both hands, about one back-and-forth every 2-3 seconds, comfortable range without jerks. Ninety seconds total including baseline.. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/agent active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "score_distributions": {
    "classifier": {
      "0": 0.0,
      "50": 0.66796875,
      "95": 0.984375,
      "99": 0.9921875,
      "99.9": 0.9921875,
      "100": 0.9921875
    },
    "reconstruction": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.049095768481492996,
      "99": 0.19638307392597198,
      "99.9": 0.19638307392597198,
      "100": 0.19638307392597198
    }
  },
  "overlapping_three_positive_positions": 1,
  "classifier_crossings": 4,
  "reconstruction_crossings": 0,
  "physical_axes": {
    "ax": {
      "mean": 4.37701706396897,
      "std": 2.51442507781686,
      "min": -5.966350537109375,
      "max": 13.536816186523437,
      "rms": 5.047832391257645
    },
    "ay": {
      "mean": 7.549425856800012,
      "std": 1.9318621461292327,
      "min": 0.3064578125,
      "max": 12.301408129882812,
      "rms": 7.792683884193406
    },
    "az": {
      "mean": 1.4017081537158462,
      "std": 2.8818894120086314,
      "min": -7.311891870117187,
      "max": 8.470685473632813,
      "rms": 3.2046953570099204
    },
    "gx": {
      "mean": 0.044551796719034795,
      "std": 17.686739657681947,
      "min": -133.96341463414635,
      "max": 175.91463414634148,
      "rms": 17.686795769194887
    },
    "gy": {
      "mean": 2.820989931429564,
      "std": 41.34255435735846,
      "min": -230.7317073170732,
      "max": 187.50000000000003,
      "rms": 41.43868705671508
    },
    "gz": {
      "mean": 1.1684505468275326,
      "std": 21.34011920705529,
      "min": -244.02439024390247,
      "max": 164.81707317073173,
      "rms": 21.372083764848757
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.808188445679429,
      "max": 16.836425103100105
    },
    "gyro": {
      "mean": 40.235229744033646,
      "max": 282.6457353109552
    }
  }
}
