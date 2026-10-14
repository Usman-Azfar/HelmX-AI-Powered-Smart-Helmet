
 — 07_high_range_benign_motion/10_controlled_bump
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-04T09:32:40.097384+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/10_controlled_bump
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 90.0,
  "elapsed_s": 90.01881832599997,
  "n_samples": 4499,
  "sample_rate_hz": 49.97843877162473,
  "n_windows": 296,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 4498,
    "mean_ms": 20.00792231525126,
    "median_ms": 20.027110499995615,
    "std_ms": 2.3006397709248967,
    "rms_error_from_20ms": 2.300653411237838,
    "p90_ms": 22.63366289996611,
    "p95_ms": 23.610110350045943,
    "p99_ms": 26.676364609952536,
    "p99.9_ms": 31.116450520939384,
    "max_ms": 37.97129800000221,
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
      9,
      99,
      4286,
      95,
      9,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1222,
      "5": 212,
      "8": 45
    }
  },
  "nominal_positions_received_samples": 296,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.7400699998688651,
    "50": 2.6250135000509545,
    "95": 5.84317000016199,
    "99": 7.4276936001410885,
    "99.9": 10.902647579994355,
    "100": 11.950628000022334
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 6.347671999947124,
    "95": 9.551805599903672,
    "99": 12.242957700182158,
    "100": 22.459718000163775
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
  "conditions": "Guided operator phase: Controlled benign bump: operator ready; helmet stationary on soft surface, after separate START cue give outer shell one light palm tap, then leave untouched. Ninety seconds including baseline/rest. Uncalibrated manual tap, no crash-impact claim.. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/agent active. No alarm countdown or communication blocks; policy events recorded only.",
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
      "mean": 1.9062113162679815,
      "std": 0.09183179010124239,
      "min": -0.32082302246093747,
      "max": 2.882618798828125,
      "rms": 1.9084220340221678
    },
    "ay": {
      "mean": 2.4492102925650143,
      "std": 0.2672445690193596,
      "min": 1.4173673828125,
      "max": 3.1316157714843746,
      "rms": 2.463747291602113
    },
    "az": {
      "mean": -9.203770970534684,
      "std": 0.115447551195509,
      "min": -10.754753857421875,
      "max": -5.717353564453124,
      "rms": 9.204495000549134
    },
    "gx": {
      "mean": -0.2091792756113825,
      "std": 1.6995234190698374,
      "min": -42.43902439024391,
      "max": 71.58536585365854,
      "rms": 1.712348043276288
    },
    "gy": {
      "mean": 2.0621791292373914,
      "std": 5.247515693074411,
      "min": -184.57317073170734,
      "max": 179.45121951219514,
      "rms": 5.6381737921178425
    },
    "gz": {
      "mean": 1.1201676253259534,
      "std": 2.5639419650065753,
      "min": -78.17073170731707,
      "max": 68.29268292682927,
      "rms": 2.797958882605348
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.71751090832016,
      "max": 11.202973827891006
    },
    "gyro": {
      "mean": 2.708020373376503,
      "max": 212.84356521637076
    }
  }
}
