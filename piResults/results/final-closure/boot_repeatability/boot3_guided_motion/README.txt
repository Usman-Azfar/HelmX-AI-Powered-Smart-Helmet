
 — boot_repeatability/boot3_guided_motion
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-05T17:03:26.159627+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot3_guided_motion
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 120.0,
  "elapsed_s": 120.0051983580006,
  "n_samples": 5985,
  "sample_rate_hz": 49.872839526046974,
  "n_windows": 396,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 5984,
    "mean_ms": 20.05055327356285,
    "median_ms": 20.06706599968311,
    "std_ms": 2.536480966987979,
    "rms_error_from_20ms": 2.5369846923779797,
    "p90_ms": 22.55757180046203,
    "p95_ms": 23.662166550184338,
    "p99_ms": 27.8540624100242,
    "p99.9_ms": 36.77975662441444,
    "max_ms": 46.95153200009372,
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
      16,
      132,
      5672,
      130,
      31,
      3,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1692,
      "5": 312,
      "8": 95
    }
  },
  "nominal_positions_received_samples": 396,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.7952170010175905,
    "50": 2.2973384998294932,
    "95": 7.58398700008911,
    "99": 12.138761199958042,
    "99.9": 16.056968649536483,
    "100": 17.18703599908622
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 6.457494000642328,
    "95": 10.765821799395782,
    "99": 15.129272839913018,
    "100": 36.972973000047205
  },
  "confirmed_alert_events": 1,
  "or_positive_windows": 38,
  "rail_counts": {
    "ax": 2,
    "ay": 0,
    "az": 0,
    "gx": 0,
    "gy": 4,
    "gz": 11
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
  "conditions": "Guided operator phase: boot3_gentle_rotations_and_tilts. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/agent active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "score_distributions": {
    "classifier": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.99609375,
      "99": 0.99609375,
      "99.9": 0.99609375,
      "100": 0.99609375
    },
    "reconstruction": {
      "0": 0.0,
      "50": 0.0,
      "95": 0.8346280604600906,
      "99": 1.1881176233291648,
      "99.9": 1.3746814727783203,
      "100": 1.3746814727783203
    }
  },
  "overlapping_three_positive_positions": 23,
  "classifier_crossings": 38,
  "reconstruction_crossings": 0,
  "physical_axes": {
    "ax": {
      "mean": -0.10825851845903012,
      "std": 3.733928227949589,
      "min": -9.813832604980469,
      "max": 19.61270144958496,
      "rms": 3.7354972785825593
    },
    "ay": {
      "mean": 2.1407706140243796,
      "std": 3.508221193449607,
      "min": -7.524975817871093,
      "max": 15.011644409179686,
      "rms": 4.10980714438516
    },
    "az": {
      "mean": -5.632144387406912,
      "std": 5.920030372880606,
      "min": -13.5224509765625,
      "max": 11.693280908203125,
      "rms": 8.171157201793884
    },
    "gx": {
      "mean": 0.18817399733430282,
      "std": 30.42777745301511,
      "min": -191.99236641221373,
      "max": 165.61068702290078,
      "rms": 30.428359308110707
    },
    "gy": {
      "mean": 3.3672348810958694,
      "std": 34.14968267966184,
      "min": -250.13740458015266,
      "max": 250.12977099236642,
      "rms": 34.31528956407136
    },
    "gz": {
      "mean": 2.032466662840307,
      "std": 28.58549917315794,
      "min": -250.13740458015266,
      "max": 250.12977099236642,
      "rms": 28.657663612272554
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.849286381276158,
      "max": 24.269906151455217
    },
    "gyro": {
      "mean": 30.400184585173022,
      "max": 353.7773595620366
    }
  }
}
