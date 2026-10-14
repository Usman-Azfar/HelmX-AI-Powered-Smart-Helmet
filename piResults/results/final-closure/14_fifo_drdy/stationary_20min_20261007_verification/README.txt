
 — Saved capture verification
Status: PASS
UTC: 2026-10-07T04:25:55.661050+00:00
Evidence: piResults/final_pi_review_closure/14_fifo_drdy/stationary_20min_20261007_verification
{
  "label": "14_fifo_drdy/stationary_20min_20261007",
  "checks": {
    "frozen_artifacts_unchanged": true,
    "full_duration": true,
    "no_exception": true,
    "no_i2c_errors": true,
    "raw_rows_match": true,
    "window_rows_match": true,
    "nonempty": true,
    "indices_contiguous": true,
    "times_nondecreasing": true,
    "registers_restored": true,
    "replay_endpoints_exact": true,
    "replay_scores_exact": true,
    "replay_policy_exact": true,
    "gap_count_matches": true,
    "no_overflow": true,
    "no_edge_timeout": true,
    "edge_rows_match": true,
    "fifo_packet_accounting": true,
    "fifo_raw_decode_exact": true,
    "fifo_host_times_exact": true,
    "fifo_configuration_correct": true
  },
  "metrics": {
    "mode": "fifo-drdy",
    "elapsed_s": 1200.0189315459993,
    "sample_rate_hz": 50.59253517091099,
    "n_samples": 60712,
    "n_windows": 4040,
    "gap_count": 1,
    "C_D": 0.9990108803165183,
    "V_T_scored_over_scored_plus_resets": 0.9997525365008662,
    "p_valid_90_sample_position": 0.9985319103310625,
    "timing": {
      "n": 60711,
      "mean_ms": 19.76593503964685,
      "median_ms": 19.78094200057967,
      "std_ms": 1.4648896507149674,
      "rms_error_from_20ms": 1.4834716358720659,
      "p90_ms": 21.027349999712897,
      "p95_ms": 21.80241250016479,
      "p99_ms": 23.997024800155494,
      "p99.9_ms": 29.480820050276115,
      "max_ms": 89.1436629999589,
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
        54,
        374,
        59915,
        318,
        47,
        2,
        1,
        0
      ],
      "deviation_counts": {
        "2": 6312,
        "5": 796,
        "8": 195
      }
    },
    "processing_ms": {
      "0": 1.63339799928508,
      "50": 2.0967125001334352,
      "95": 7.088683950269113,
      "99": 12.03355814998759,
      "99.9": 23.027007696570116,
      "100": 36.67136900003243
    },
    "i2c_failures": 0,
    "confirmed_alert_events": 0,
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
    "physical_axes": {
      "ax": {
        "mean": -5.838907015533184,
        "std": 0.0089292138992266,
        "min": -6.042964990234375,
        "max": -5.651513018798828,
        "rms": 5.838913843079337
      },
      "ay": {
        "mean": -0.7776428471967248,
        "std": 0.010382668494174225,
        "min": -1.7902642913818358,
        "max": -0.14963760375976562,
        "rms": 0.7777121560071494
      },
      "az": {
        "mean": -7.792635472584663,
        "std": 0.013615334957525321,
        "min": -7.9661074737548825,
        "max": -7.4591352722167965,
        "rms": 7.792647366969121
      },
      "gx": {
        "mean": -0.21006888737113477,
        "std": 0.05740371189476498,
        "min": -7.137404580152672,
        "max": 2.7251908396946565,
        "rms": 0.21777080516139827
      },
      "gy": {
        "mean": 2.0982698693066197,
        "std": 0.17941007456787206,
        "min": -0.6717557251908397,
        "max": 7.152671755725191,
        "rms": 2.10592602417475
      },
      "gz": {
        "mean": 1.062140210972289,
        "std": 0.03870841385225415,
        "min": -1.0,
        "max": 2.229007633587786,
        "rms": 1.062845317563763
      }
    },
    "resources": {
      "cpu_pct": {
        "min": 4.9,
        "max": 41.7,
        "mean": 7.651637279596978
      },
      "rss_bytes": {
        "min": 50270208,
        "max": 61419520,
        "mean": 56218318.7774979
      },
      "cpu_temp_c": {
        "min": 45.277,
        "max": 53.556,
        "mean": 48.19940890008396
      }
    }
  },
  "source_hashes": {
    "raw_sensor.csv": "6ecd42d1c17fcc598db77ad76a0d088ec76d092272cc135c2c055decd75dc569",
    "README.txt": "621b5dc410106d23be5d34dc27da607bbe332642aaf531c6573f41ebc78e5266",
    "window_scores.csv": "5a4f2fa1fdbf3dc5d5bf01cbccad773ad0f1738967fb3f445f9537b61e475009",
    "metadata.json": "57bdca34c7bc8cc4ce2e9de77154e4b804d3a7daf13095cbc559be565d0d73b1",
    "fifo_batches.json": "145ecf52a921888fa91c4c229331c97e12ae39ce39e88aac61712143da734876",
    "registers_during.json": "05d16c1396535cfdc0f31800a4c520f4ae9badd041470cd18a560f7647f5cd2f",
    "registers_restored.json": "1c82b166dd54a26a4d5a4115dfd6d614a1e3933621cbea008db05e313ec65d71",
    "registers_before.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
    "errors.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "configuration.json": "6c7fce2e496de288e22029a3f364b2f07cbd96fe7709dda5623e358f803cc88b",
    "summary.json": "d70e1ce4cbfd27170ad1a60b1df6f7655fd94b0d48bd9a90e591728529eef9bc",
    "resources.json": "398d147ccdbee66600b59b37d32a12606f02efc5cead86432b252a6f336700f0",
    "throttled_start.json": "518a5b7e760f3e653fef809b35392a9839d13a23cf4bdbf3b298cf85fc8117f2",
    "gc_events.json": "def4400306333f9f949b3f6820f00d656fb0bf94f4a81830d09689803e85921a",
    "gpio_edges.csv": "e46248170424c64420e8329668715d57f68b9bb3d2db1ddad53083fd1bbedde3"
  },
  "scope": "Offline replay and byte integrity. FIFO shared host times are not physical sample jitter. Physical conditions require operator attestation."
}
