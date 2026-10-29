
 — boot_repeatability/boot1_warm_stationary
Status: COMPLETE (UNATTENDED)
UTC: 2026-10-04T18:38:02.215445+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/boot1_warm_stationary
{
  "mode": "polling",
  "fifo_overflows": 0,
  "seconds_requested": 600.0,
  "elapsed_s": 600.0073105739998,
  "n_samples": 30000,
  "sample_rate_hz": 49.999390792922775,
  "n_windows": 1997,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 29999,
    "mean_ms": 20.000040170339002,
    "median_ms": 19.995646000097622,
    "std_ms": 1.006925336321365,
    "rms_error_from_20ms": 1.006925337122644,
    "p90_ms": 21.151989999998477,
    "p95_ms": 21.789342000056422,
    "p99_ms": 22.857433600065633,
    "p99.9_ms": 25.37160172375506,
    "max_ms": 36.17398200003663,
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
      43,
      29911,
      43,
      1,
      0,
      0,
      0
    ],
    "deviation_counts": {
      "2": 1575,
      "5": 88,
      "8": 11
    }
  },
  "nominal_positions_received_samples": 1997,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.5969579999364214,
    "50": 1.7439370003557997,
    "95": 2.279469999757566,
    "99": 3.3788358001584125,
    "99.9": 6.52563904015032,
    "100": 10.806951000176923
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 5.903019500010487,
    "95": 6.675077149952813,
    "99": 8.087378250406791,
    "100": 18.919181000001117
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
  "conditions": "Unattended, desktop/IDE state in metadata. No physical mounting confirmation. No alarm countdown or communication blocks; policy events recorded only.",
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
      "mean": -2.0080759893473306,
      "std": 0.06680366632180489,
      "min": -2.29843359375,
      "max": -1.695094775390625,
      "rms": 2.0091868775271493
    },
    "ay": {
      "mean": -0.19733943821655273,
      "std": 0.04352705207766475,
      "min": -0.45968671875,
      "max": -0.00239420166015625,
      "rms": 0.20208280020376887
    },
    "az": {
      "mean": -9.559375256404621,
      "std": 0.05929892305529346,
      "min": -9.80665,
      "max": -9.34696328125,
      "rms": 9.55955917681545
    },
    "gx": {
      "mean": -0.2208804071246819,
      "std": 1.4645628282232854,
      "min": -6.900763358778626,
      "max": 7.206106870229007,
      "rms": 1.4811253937681823
    },
    "gy": {
      "mean": 2.1376371501272264,
      "std": 2.642141248040385,
      "min": -10.50381679389313,
      "max": 14.549618320610687,
      "rms": 3.3985883775768513
    },
    "gz": {
      "mean": 1.0482966921119592,
      "std": 1.400853079158583,
      "min": -6.152671755725191,
      "max": 8.442748091603054,
      "rms": 1.7496614827105725
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.770348255962826,
      "max": 10.03530104237747
    },
    "gyro": {
      "mean": 3.630126922039714,
      "max": 15.082466624766964
    }
  }
}
