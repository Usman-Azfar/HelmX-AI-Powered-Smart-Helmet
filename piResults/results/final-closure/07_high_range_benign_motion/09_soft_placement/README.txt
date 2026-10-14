
 — 07_high_range_benign_motion/09_soft_placement
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-04T09:29:42.441247+00:00
Evidence: piResults/final_pi_review_closure/07_high_range_benign_motion/09_soft_placement
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 90.0,
  "elapsed_s": 90.00501330899988,
  "n_samples": 4497,
  "sample_rate_hz": 49.963883506812735,
  "n_windows": 296,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 4496,
    "mean_ms": 20.014589352757987,
    "median_ms": 20.068078000008427,
    "std_ms": 2.172870522765509,
    "rms_error_from_20ms": 2.1729195010209543,
    "p90_ms": 22.2762785000441,
    "p95_ms": 23.3167387501112,
    "p99_ms": 25.799648749966774,
    "p99.9_ms": 33.99983042010837,
    "max_ms": 40.66003399998408,
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
      66,
      4345,
      63,
      13,
      1,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1104,
      "5": 151,
      "8": 40
    }
  },
  "nominal_positions_received_samples": 296,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.7434070000490465,
    "50": 2.2002504999818484,
    "95": 4.731740250065286,
    "99": 9.429663649916622,
    "99.9": 11.581698329899924,
    "100": 12.213713999926767
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 6.368471000087084,
    "95": 9.734493600126369,
    "99": 12.756186679862367,
    "100": 26.13327900007789
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
  "conditions": "Guided operator phase: Soft placement: operator ready; initially held still, after separate START cue gently place helmet once on a stable soft surface and leave untouched. Ninety seconds including baseline and subsequent rest. No drop or impact.. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/agent active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "score_distributions": {
    "classifier": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.91796875,
      "99": 0.9886718750000001,
      "99.9": 0.99609375,
      "100": 0.99609375
    },
    "reconstruction": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.0,
      "99": 0.19638307392597198,
      "99.9": 0.39276614785194397,
      "100": 0.39276614785194397
    }
  },
  "overlapping_three_positive_positions": 1,
  "classifier_crossings": 3,
  "reconstruction_crossings": 0,
  "physical_axes": {
    "ax": {
      "mean": 3.030489634029023,
      "std": 2.2521867143182317,
      "min": -3.380612744140625,
      "max": 9.658209497070311,
      "rms": 3.775739982852224
    },
    "ay": {
      "mean": 3.594883410929552,
      "std": 1.1996691611932064,
      "min": -1.0726023437499999,
      "max": 13.474566943359374,
      "rms": 3.7897747735841114
    },
    "az": {
      "mean": -5.211901763491198,
      "std": 6.303662632150523,
      "min": -11.166556542968749,
      "max": 10.82179150390625,
      "rms": 8.179247066341347
    },
    "gx": {
      "mean": 0.9661590111564893,
      "std": 9.811551937839027,
      "min": -49.57317073170732,
      "max": 169.02439024390245,
      "rms": 9.859006778765885
    },
    "gy": {
      "mean": 1.8239395369270575,
      "std": 13.479546852948783,
      "min": -117.56097560975611,
      "max": 173.2926829268293,
      "rms": 13.602387246186131
    },
    "gz": {
      "mean": 1.8337021428920097,
      "std": 20.16841042872165,
      "min": -389.87804878048786,
      "max": 314.0853658536586,
      "rms": 20.251598523825592
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.769502013631499,
      "max": 14.91569418249789
    },
    "gyro": {
      "mean": 9.832389725119299,
      "max": 406.6976129679313
    }
  }
}
