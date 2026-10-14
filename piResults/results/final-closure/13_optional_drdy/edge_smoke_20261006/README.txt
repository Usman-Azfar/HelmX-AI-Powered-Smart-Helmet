
 — 13_optional_drdy/edge_smoke_20261006
Status: COMPLETE (GUIDED; OPERATOR-ATTESTED)
UTC: 2026-10-06T14:46:52.417884+00:00
Evidence: piResults/final_pi_review_closure/13_optional_drdy/edge_smoke_20261006
{
  "mode": "drdy",
  "fifo_overflows": 0,
  "seconds_requested": 10.0,
  "elapsed_s": 10.007956295000099,
  "n_samples": 506,
  "sample_rate_hz": 50.55977315296569,
  "n_windows": 30,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 505,
    "mean_ms": 19.810950231683115,
    "median_ms": 19.775664000007964,
    "std_ms": 2.409586299358084,
    "rms_error_from_20ms": 2.416991094099201,
    "p90_ms": 21.533761400064577,
    "p95_ms": 22.6850514000489,
    "p99_ms": 25.942514879961884,
    "p99.9_ms": 41.79610760799918,
    "max_ms": 42.24755200004893,
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
      1,
      10,
      487,
      3,
      2,
      2,
      0,
      0
    ],
    "deviation_counts": {
      "2": 88,
      "5": 18,
      "8": 6
    }
  },
  "nominal_positions_received_samples": 30,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.6992420000860875,
    "50": 2.27464049999071,
    "95": 15.106652599939675,
    "99": 28.414915359951475,
    "99.9": 31.427746935950196,
    "100": 31.762505999950008
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 1.842714000019896,
    "95": 4.629179499943348,
    "99": 6.7827380500034415,
    "100": 26.081502000010914
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
  "conditions": "Guided operator phase: Stationary helmet confirmed by operator; INT connected to BCM23 physical pin16. User reported readiness; performed motion is not independently verified or amplitude-matched. Desktop/agent active. No alarm countdown or communication blocks; policy events recorded only.",
  "memory_scope": "Raw samples stream to disk and are loaded only after capture. RSS still includes score/resource/GC research buffers; do not interpret their growth as a production-monitor leak.",
  "timing_scope": "Processing latency excludes scheduled pacing sleep and raw file write; sensor reads reported separately. Stream dt includes harness logging/resource overhead. CPU temperature from sysfs; sensor temperature preserved RAW because device identity differs from MPU6050.",
  "data_ready": {
    "gpio_bcm": 23,
    "physical_pin": 16,
    "edges_read": 507,
    "stale_edges_discarded": 1,
    "timeouts": 0,
    "timestamp_scope": "Samples use host read completion. Separate GPIO kernel edge timestamps and wake/read times are in gpio_edges.csv. No synthesized sample timestamps.",
    "missed_sample_scope": "Stale queued edges are discarded above 15 ms age. libgpiod v1 cannot count kernel queue overflow; edge interval gaps are diagnostic, not an exact lost-sample count.",
    "read_path": "Coherent 14-byte burst; differs from deployed polling separate reads.",
    "register_map_source": "https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6500-Register-Map2.pdf"
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
      "mean": -5.829371210012322,
      "std": 0.011896605432588173,
      "min": -5.9017070922851556,
      "max": -5.786785412597656,
      "rms": 5.829383349321037
    },
    "ay": {
      "mean": -0.6017442611272156,
      "std": 0.015465211709882853,
      "min": -0.6865373260498047,
      "max": -0.4848258361816406,
      "rms": 0.601942961228695
    },
    "az": {
      "mean": -7.79606829092757,
      "std": 0.018301434312689355,
      "min": -7.9283987976074215,
      "max": -7.659649661254883,
      "rms": 7.796089772398996
    },
    "gx": {
      "mean": -0.21657665268684184,
      "std": 0.08261041804083886,
      "min": -0.48854961832061067,
      "max": 0.05343511450381679,
      "rms": 0.23179716921895116
    },
    "gy": {
      "mean": 2.0927797725009807,
      "std": 0.4850170585961794,
      "min": 0.3282442748091603,
      "max": 3.5801526717557253,
      "rms": 2.1482478263269686
    },
    "gz": {
      "mean": 1.101756026913677,
      "std": 0.06503209512847559,
      "min": 0.8015267175572519,
      "max": 1.3129770992366412,
      "rms": 1.1036736457111813
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.753091759711284,
      "max": 9.888520526303262
    },
    "gyro": {
      "mean": 2.3865415071307474,
      "max": 3.8136933971757037
    }
  }
}
