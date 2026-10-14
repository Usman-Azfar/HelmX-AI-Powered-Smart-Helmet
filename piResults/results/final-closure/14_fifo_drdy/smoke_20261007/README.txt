
 — 14_fifo_drdy/smoke_20261007
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-06T20:47:58.756429+00:00
Evidence: piResults/final_pi_review_closure/14_fifo_drdy/smoke_20261007
{
  "mode": "fifo-drdy",
  "fifo_overflows": 0,
  "seconds_requested": 30.0,
  "elapsed_s": 30.009964914000193,
  "n_samples": 1519,
  "sample_rate_hz": 50.61652035758826,
  "n_windows": 98,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 1518,
    "mean_ms": 19.767169488800818,
    "median_ms": 19.774679500642378,
    "std_ms": 2.086701238048698,
    "rms_error_from_20ms": 2.0996504718212603,
    "p90_ms": 21.68534800021007,
    "p95_ms": 22.947704100033658,
    "p99_ms": 25.931334960150703,
    "p99.9_ms": 30.584121497366553,
    "max_ms": 32.0065309997517,
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
      5,
      24,
      1464,
      23,
      2,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 290,
      "5": 54,
      "8": 16
    }
  },
  "nominal_positions_received_samples": 98,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.6367679991162731,
    "50": 2.6307010007258214,
    "95": 9.2047430994171,
    "99": 11.929510989884877,
    "99.9": 13.440004398677058,
    "100": 13.607836999653955
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 2.9187520003688405,
    "95": 6.272459699812314,
    "99": 9.621832300090308,
    "100": 16.553699999349192
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
  "conditions": "Guided operator phase: stationary_untouched_confirmed. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/agent active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "data_ready": {
    "gpio_bcm": 23,
    "physical_pin": 16,
    "edges_read": 1519,
    "stale_edges_discarded": 0,
    "timeouts": 0,
    "timestamp_scope": "Shared host drain-completion time per batch. Zero inter-packet host intervals are intentional; no physical sample jitter claim.",
    "missed_sample_scope": "Queued edges may drain zero or multiple packets. No edge-age discard. Kernel queue loss is not directly measurable.",
    "read_path": "Audited 12-byte six-axis FIFO packets drained on DATA_RDY; exact bytes in gpio_edges.csv.",
    "register_map_source": "https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6500-Register-Map2.pdf",
    "packets_drained": 1519,
    "packets_pending_at_deadline": 0
  },
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
      "mean": -5.842153099179597,
      "std": 0.008525828096664297,
      "min": -5.869385369873046,
      "max": -5.816712933349609,
      "rms": 5.842159320319714
    },
    "ay": {
      "mean": -0.7776750001406338,
      "std": 0.01014457681832138,
      "min": -0.8224082702636718,
      "max": -0.7254431030273437,
      "rms": 0.7777411640658849
    },
    "az": {
      "mean": -7.789021664063062,
      "std": 0.01388503393972455,
      "min": -7.831433630371094,
      "max": -7.740453967285156,
      "rms": 7.789034040072698
    },
    "gx": {
      "mean": -0.2097955163350738,
      "std": 0.03295099421906862,
      "min": -0.3129770992366412,
      "max": -0.09923664122137404,
      "rms": 0.21236743322441248
    },
    "gy": {
      "mean": 2.0959047987577204,
      "std": 0.12435385230773838,
      "min": 1.4809160305343512,
      "max": 2.6564885496183206,
      "rms": 2.099590628203368
    },
    "gz": {
      "mean": 1.0609782450286196,
      "std": 0.0341798748504972,
      "min": 0.8091603053435115,
      "max": 1.1908396946564885,
      "rms": 1.0615286620100304
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.767528696328931,
      "max": 9.801524449392113
    },
    "gyro": {
      "mean": 2.3593568332538712,
      "max": 2.9179482922879916
    }
  }
}
