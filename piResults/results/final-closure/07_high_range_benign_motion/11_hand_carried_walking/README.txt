
 — 07_high_range_benign_motion/11_hand_carried_walking
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-04T09:35:00.419562+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/11_hand_carried_walking
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 90.0,
  "elapsed_s": 90.00945415000001,
  "n_samples": 4497,
  "sample_rate_hz": 49.96141841395668,
  "n_windows": 296,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 4496,
    "mean_ms": 20.014552162366574,
    "median_ms": 20.027905500000998,
    "std_ms": 2.2421341550256466,
    "rms_error_from_20ms": 2.242181378604798,
    "p90_ms": 22.511956500011365,
    "p95_ms": 23.54721224998002,
    "p99_ms": 26.570616400113078,
    "p99.9_ms": 31.511326945050087,
    "max_ms": 37.03894300019783,
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
      8,
      79,
      4317,
      80,
      12,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1163,
      "5": 179,
      "8": 53
    }
  },
  "nominal_positions_received_samples": 296,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.796260999981314,
    "50": 2.109604499764828,
    "95": 4.984863499998937,
    "99": 10.308458299994077,
    "99.9": 16.00034616001296,
    "100": 18.113712000058513
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 6.4102629999069904,
    "95": 9.697007400109213,
    "99": 13.188431119870073,
    "100": 25.99055399991812
  },
  "confirmed_alert_events": 1,
  "or_positive_windows": 3,
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
  "conditions": "Guided operator phase: Hand-carried walking-like motion: operator ready; hold helmet still before separate START cue, then gentle steps in place while carrying helmet securely and keeping wires slack. Ninety seconds including baseline. Not an actual road or free-walking trial.. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/agent active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "score_distributions": {
    "classifier": {
      "0": 0.0,
      "50": 0.16015625,
      "95": 0.9296875,
      "99": 0.9884765625,
      "99.9": 0.9921875,
      "100": 0.9921875
    },
    "reconstruction": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.0,
      "99": 0.19638307392597198,
      "99.9": 0.19638307392597198,
      "100": 0.19638307392597198
    }
  },
  "overlapping_three_positive_positions": 1,
  "classifier_crossings": 3,
  "reconstruction_crossings": 0,
  "physical_axes": {
    "ax": {
      "mean": 5.101843023088525,
      "std": 3.0205437372622104,
      "min": -2.4899697265625,
      "max": 13.570335009765625,
      "rms": 5.928953255082303
    },
    "ay": {
      "mean": 6.9477698410702615,
      "std": 2.4096778431833195,
      "min": -3.1842882080078123,
      "max": 14.168885424804687,
      "rms": 7.353778149523829
    },
    "az": {
      "mean": -2.018408363865841,
      "std": 1.543790058154345,
      "min": -7.1203557373046875,
      "max": 1.8148048583984373,
      "rms": 2.5411139421481628
    },
    "gx": {
      "mean": -0.4173649641766598,
      "std": 22.89829053280338,
      "min": -159.51219512195124,
      "max": 227.68292682926833,
      "rms": 22.902093852702528
    },
    "gy": {
      "mean": 3.9919431382439248,
      "std": 27.487262137640528,
      "min": -175.00000000000003,
      "max": 157.37804878048783,
      "rms": 27.775622222415457
    },
    "gz": {
      "mean": 1.135824967322388,
      "std": 23.290890368855692,
      "min": -126.70731707317074,
      "max": 139.14634146341464,
      "rms": 23.31856926422476
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.742479490447167,
      "max": 16.509776506370294
    },
    "gyro": {
      "mean": 35.3454314995811,
      "max": 268.2178110605946
    }
  }
}
