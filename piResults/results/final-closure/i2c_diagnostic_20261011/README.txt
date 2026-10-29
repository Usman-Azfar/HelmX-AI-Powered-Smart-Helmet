
 — i2c_diagnostic_20261011
Status: COMPLETE (UNATTENDED)
UTC: 2026-10-11T10:32:26.872146+00:00
Evidence: piResults/final_pi_review_closure/i2c_diagnostic_20261011
{
  "mode": "polling",
  "capture_start_monotonic": 15554.995985024,
  "capture_end_monotonic": 15674.999756442,
  "fifo_overflows": 0,
  "seconds_requested": 120.0,
  "elapsed_s": 120.00377141799981,
  "n_samples": 5969,
  "sample_rate_hz": 49.740103410655706,
  "n_windows": 394,
  "i2c_failures": 0,
  "exception": null,
  "timing": {
    "n": 5968,
    "mean_ms": 20.102891671916982,
    "median_ms": 19.884400499904586,
    "std_ms": 3.426951226432708,
    "rms_error_from_20ms": 3.4284955016010326,
    "p90_ms": 23.788622799656878,
    "p95_ms": 25.405270049941464,
    "p99_ms": 30.700802630308313,
    "p99.9_ms": 39.64210517868804,
    "max_ms": 50.942365000082646,
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
      39,
      261,
      5313,
      280,
      69,
      6,
      0,
      0
    ],
    "deviation_counts": {
      "2": 2583,
      "5": 655,
      "8": 215
    }
  },
  "nominal_positions_received_samples": 394,
  "C_D": 1.0,
  "V_T_scored_over_scored_plus_resets": 1.0,
  "p_valid_90_sample_position": 1.0,
  "gap_count": 0,
  "processing_ms": {
    "0": 1.8269450010848232,
    "50": 3.2593470004940173,
    "95": 9.343453150177078,
    "99": 18.52620055005899,
    "99.9": 25.308536001855938,
    "100": 26.861469999857945
  },
  "processing_over_300ms": 0,
  "sensor_read_ms": {
    "50": 7.797411000865395,
    "95": 13.025796000147237,
    "99": 18.02615519969546,
    "100": 40.77413699997123
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
  "conditions": "Unattended, desktop/agent state in metadata. No physical mounting confirmation. No alarm countdown or communication blocks; policy events recorded only.",
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
      "mean": -5.893323174861704,
      "std": 0.035907987079304725,
      "min": -7.275978845214843,
      "max": -5.2624552490234375,
      "rms": 5.893432567434544
    },
    "ay": {
      "mean": -0.9985742220548354,
      "std": 0.02872514758897686,
      "min": -1.5251064575195312,
      "max": -0.24181436767578124,
      "rms": 0.9989872927402171
    },
    "az": {
      "mean": -7.688929897213892,
      "std": 0.060127915838649876,
      "min": -8.027758166503906,
      "max": -7.1203557373046875,
      "rms": 7.689164995663231
    },
    "gx": {
      "mean": -0.10188134880086555,
      "std": 0.7063290222250772,
      "min": -5.259541984732825,
      "max": 8.221374045801527,
      "rms": 0.7136389121053568
    },
    "gy": {
      "mean": 2.1135753556223698,
      "std": 0.6318752090354371,
      "min": -0.22137404580152673,
      "max": 3.900763358778626,
      "rms": 2.2060070407158276
    },
    "gz": {
      "mean": 1.110598141287236,
      "std": 0.16445369037369464,
      "min": -1.465648854961832,
      "max": 4.6106870229007635,
      "rms": 1.1227079975257104
    }
  },
  "magnitudes": {
    "accel": {
      "mean": 9.739153048477652,
      "max": 10.625123584722251
    },
    "gyro": {
      "mean": 2.5178522995300225,
      "max": 8.483708598165036
    }
  }
}
