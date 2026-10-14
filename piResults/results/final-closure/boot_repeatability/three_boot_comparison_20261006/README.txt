
H1 — Three-boot saved baseline/motion comparison: boots 1, 3, 4
Status: PARTIAL (BOOT4 MOTION ATTESTATION PENDING)
UTC: 2026-10-06T14:16:27.628498+00:00
Evidence: piResults/final_pi_review_closure/boot_repeatability/three_boot_comparison_20261006
{
  "captures": [
    {
      "boot": 1,
      "phase": "stationary",
      "boot_id": "<redacted-boot-id>",
      "first_sample_uptime_s": 98.728620449,
      "identity_counts": {
        "0x70": 100
      },
      "registers": {
        "SMPLRT_DIV": 0,
        "CONFIG": 0,
        "GYRO_CONFIG": 0,
        "ACCEL_CONFIG": 0,
        "ACCEL_CONFIG2": 0,
        "FIFO_EN": 0,
        "INT_PIN_CFG": 0,
        "INT_ENABLE": 0,
        "INT_STATUS": 1,
        "USER_CTRL": 0,
        "PWR_MGMT_1": 0,
        "PWR_MGMT_2": 0,
        "FIFO_COUNT_H": 0,
        "FIFO_COUNT_L": 0,
        "WHO_AM_I": 112
      },
      "source_hashes": {
        "raw_sensor.csv": "51a8870b45bc7bbd694832e8ecd7edf70a2b8bde3a192ab4455848b2ea217761",
        "README.txt": "6757da1f2b348d24e851b173df39bdbee1ec71b71d3af9a38bf80ebfa8480c23",
        "window_scores.csv": "b7ef9179983c81f7868fa6c66709df262fe9c19be0ad5e7426cbeef717a218ba",
        "metadata.json": "33fff3eaae73c03a91fbdef39300d434f7b6ce2203795cbdd1b81d8e9c211fd1",
        "fifo_batches.json": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
        "registers_during.json": "31d645e3f093b9bb5d7da2a3532bf16639c8d12735ae911358b35a42bfd9f82e",
        "registers_restored.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "registers_before.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "errors.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "configuration.json": "6c7fce2e496de288e22029a3f364b2f07cbd96fe7709dda5623e358f803cc88b",
        "summary.json": "d27f243bf9b60df8a7e145d3241a006792892bc1d969ebcd4eec85c17346b1eb",
        "resources.json": "2baaa8ee86052c50c59fff64db9b8507675e3723f929d8b0b5ef2e1fae9a8943",
        "throttled_start.json": "518a5b7e760f3e653fef809b35392a9839d13a23cf4bdbf3b298cf85fc8117f2",
        "gc_events.json": "bdefaaa00b7367acf506dde18d9e5a920e3ac1c3991a95c8736c66b2d45d09cd"
      },
      "elapsed_s": 600.0190184579999,
      "n_samples": 29997,
      "n_windows": 1996,
      "sample_rate_hz": 49.993415337216895,
      "timing": {
        "n": 29996,
        "mean_ms": 20.002192801040138,
        "median_ms": 19.996806999984074,
        "std_ms": 1.7164298218974587,
        "rms_error_from_20ms": 1.7164312225881186,
        "p90_ms": 21.75382149999905,
        "p95_ms": 22.49819150001997,
        "p99_ms": 25.339696450004823,
        "p99.9_ms": 30.0608402600538,
        "max_ms": 39.721091000018305,
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
          33,
          298,
          29323,
          311,
          31,
          0,
          0,
          0
        ],
        "deviation_counts": {
          "2": 4192,
          "5": 673,
          "8": 164
        }
      },
      "physical_axes": {
        "ax": {
          "mean": -2.54391768186218,
          "std": 0.051595781468997626,
          "min": -4.211400720214844,
          "max": 0.20829554443359374,
          "rms": 2.544440861320311
        },
        "ay": {
          "mean": -1.7925436596373667,
          "std": 0.04800353193204786,
          "min": -4.673481640625,
          "max": -0.6823474731445313,
          "rms": 1.7931863011923983
        },
        "az": {
          "mean": -9.27326094739601,
          "std": 0.05922687642664562,
          "min": -13.333309045410155,
          "max": -8.097190014648437,
          "rms": 9.273450081894612
        },
        "gx": {
          "mean": -0.22283271584155873,
          "std": 0.8979706633519972,
          "min": -19.290076335877863,
          "max": 29.083969465648856,
          "rms": 0.9252057779165404
        },
        "gy": {
          "mean": 2.1357107720950212,
          "std": 1.0284812688607705,
          "min": -32.412213740458014,
          "max": 33.38167938931298,
          "rms": 2.370450215136393
        },
        "gz": {
          "mean": 1.0481226239672312,
          "std": 1.7345243033018887,
          "min": -51.70229007633588,
          "max": 48.786259541984734,
          "rms": 2.0266069164040807
        }
      },
      "score_distributions": {
        "classifier": {
          "0": 0.0,
          "50": 0.0,
          "95": 0.0,
          "99": 0.0,
          "99.9": 0.003925781250000426,
          "100": 0.05078125
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
      "rail_counts": {
        "ax": 0,
        "ay": 0,
        "az": 0,
        "gx": 0,
        "gy": 0,
        "gz": 0
      },
      "confirmed_alert_events": 0,
      "i2c_failures": 0,
      "gap_count": 0,
      "C_D": 1.0
    },
    {
      "boot": 1,
      "phase": "guided_motion",
      "boot_id": "<redacted-boot-id>",
      "first_sample_uptime_s": 1036.215948798,
      "identity_counts": {
        "0x70": 100
      },
      "registers": {
        "SMPLRT_DIV": 0,
        "CONFIG": 0,
        "GYRO_CONFIG": 0,
        "ACCEL_CONFIG": 0,
        "ACCEL_CONFIG2": 0,
        "FIFO_EN": 0,
        "INT_PIN_CFG": 0,
        "INT_ENABLE": 0,
        "INT_STATUS": 1,
        "USER_CTRL": 0,
        "PWR_MGMT_1": 0,
        "PWR_MGMT_2": 0,
        "FIFO_COUNT_H": 0,
        "FIFO_COUNT_L": 0,
        "WHO_AM_I": 112
      },
      "source_hashes": {
        "raw_sensor.csv": "55863df8d4928bd1448fb02ff6442e81fa9195f109c230bf4d192e3253432e4b",
        "README.txt": "07e2218bf57aa24c431345d393e440dd3dbf0ebb9e260872d4aa4407aa63f38e",
        "window_scores.csv": "96611f4d6bdeddf6418dc19c9bee48146daa2acd57bc56d8d27f1ef7d52dcaa1",
        "metadata.json": "eab037a7434b3d9e590659db888eb5b9f9f2a4a35eac4cd9ee07fe258cea8ee5",
        "fifo_batches.json": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
        "registers_during.json": "31d645e3f093b9bb5d7da2a3532bf16639c8d12735ae911358b35a42bfd9f82e",
        "registers_restored.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "registers_before.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "errors.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "configuration.json": "6c7fce2e496de288e22029a3f364b2f07cbd96fe7709dda5623e358f803cc88b",
        "summary.json": "fa1c58f0af44324aa009e6974a47c2d3a7bcdf41f9fb998f2d53c9e867d6ab50",
        "resources.json": "de49a813b98c915bc1dff8562f65dfa416aca0de99b1491e97523e33287038be",
        "cue_record.json": "f7da2a8b19b8d1d1652b9a8deb0da4402e9c702ea157958ba5978c79b42a2bc0",
        "throttled_start.json": "518a5b7e760f3e653fef809b35392a9839d13a23cf4bdbf3b298cf85fc8117f2",
        "gc_events.json": "30e628ad24dc5311f03299bcda448474626822251c87b9bb3bc9d005ad609df5"
      },
      "elapsed_s": 120.01308030900009,
      "n_samples": 5989,
      "n_windows": 396,
      "sample_rate_hz": 49.9028937894103,
      "timing": {
        "n": 5988,
        "mean_ms": 20.039124321309295,
        "median_ms": 20.010933999856206,
        "std_ms": 2.794921892666119,
        "rms_error_from_20ms": 2.7951957174091175,
        "p90_ms": 22.92230339994603,
        "p95_ms": 24.364469349961837,
        "p99_ms": 28.62261392999926,
        "p99.9_ms": 35.87461290004189,
        "max_ms": 43.8281439999173,
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
          24,
          174,
          5549,
          208,
          30,
          3,
          0,
          0
        ],
        "deviation_counts": {
          "2": 1935,
          "5": 439,
          "8": 137
        }
      },
      "physical_axes": {
        "ax": {
          "mean": -1.2505620059362574,
          "std": 2.7939485157349813,
          "min": -16.060304736328124,
          "max": 10.46984385986328,
          "rms": 3.061054334582942
        },
        "ay": {
          "mean": 1.6165746352871702,
          "std": 3.4989026669187524,
          "min": -9.670180505371093,
          "max": 13.644555261230469,
          "rms": 3.8543006400675344
        },
        "az": {
          "mean": -6.914145075190032,
          "std": 4.999582734971557,
          "min": -13.36203946533203,
          "max": 12.021286535644531,
          "rms": 8.532363661061352
        },
        "gx": {
          "mean": -1.3258174337430326,
          "std": 22.5377971577742,
          "min": -194.3587786259542,
          "max": 162.8320610687023,
          "rms": 22.576760010962417
        },
        "gy": {
          "mean": 3.9247156682926336,
          "std": 35.28217501864482,
          "min": -250.13740458015266,
          "max": 250.12977099236642,
          "rms": 35.49979249408687
        },
        "gz": {
          "mean": 0.7065625402296069,
          "std": 29.036697172821604,
          "min": -250.13740458015266,
          "max": 250.12977099236642,
          "rms": 29.04529244695949
        }
      },
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
          "95": 0.7855322957038879,
          "99": 1.1782984733581543,
          "99.9": 1.3746814727783203,
          "100": 1.3746814727783203
        }
      },
      "rail_counts": {
        "ax": 0,
        "ay": 0,
        "az": 0,
        "gx": 0,
        "gy": 4,
        "gz": 2
      },
      "confirmed_alert_events": 1,
      "i2c_failures": 0,
      "gap_count": 0,
      "C_D": 1.0
    },
    {
      "boot": 3,
      "phase": "stationary",
      "boot_id": "<redacted-boot-id>",
      "first_sample_uptime_s": 3901.861378966,
      "identity_counts": {
        "0x70": 100
      },
      "registers": {
        "SMPLRT_DIV": 0,
        "CONFIG": 0,
        "GYRO_CONFIG": 0,
        "ACCEL_CONFIG": 0,
        "ACCEL_CONFIG2": 0,
        "FIFO_EN": 0,
        "INT_PIN_CFG": 0,
        "INT_ENABLE": 0,
        "INT_STATUS": 1,
        "USER_CTRL": 0,
        "PWR_MGMT_1": 0,
        "PWR_MGMT_2": 0,
        "FIFO_COUNT_H": 0,
        "FIFO_COUNT_L": 0,
        "WHO_AM_I": 112
      },
      "source_hashes": {
        "raw_sensor.csv": "dbce5fdf4e833b9068215d11c3b3daadce263fcae71960053553c989f40b1b6a",
        "README.txt": "aa3d44bc26d181d6741b6239d30a10a11c5a772ca4d8327fa1415e91f614efd7",
        "window_scores.csv": "019d24f9fc65772c4637cdfecb12fb4ba8454b1628599173c68ad8cfb3f983e0",
        "metadata.json": "b8f220aefbad104736faf764925fd2e15104a0b84c03785ed853f90cb95fbe9f",
        "fifo_batches.json": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
        "registers_during.json": "31d645e3f093b9bb5d7da2a3532bf16639c8d12735ae911358b35a42bfd9f82e",
        "registers_restored.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "registers_before.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "errors.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "configuration.json": "6c7fce2e496de288e22029a3f364b2f07cbd96fe7709dda5623e358f803cc88b",
        "summary.json": "588fbe297690d290a4d785cab6e86e03d78eaf03c275d063810c02bfafcea792",
        "resources.json": "e803b911d6890692cafdff979a11ac6e449767809e8575779d8bb28aae329b19",
        "throttled_start.json": "518a5b7e760f3e653fef809b35392a9839d13a23cf4bdbf3b298cf85fc8117f2",
        "gc_events.json": "a8c872313deace1a01f323b24a3680c25f0b41c9e69fe5b6810797b61d9a3934"
      },
      "elapsed_s": 300.0110729039998,
      "n_samples": 14988,
      "n_windows": 996,
      "sample_rate_hz": 49.958156060446456,
      "timing": {
        "n": 14987,
        "mean_ms": 20.016605062053763,
        "median_ms": 20.051457999670674,
        "std_ms": 2.287511443800453,
        "rms_error_from_20ms": 2.2875717111390936,
        "p90_ms": 22.39809040020191,
        "p95_ms": 23.51323480015708,
        "p99_ms": 26.531063920237997,
        "p99.9_ms": 33.48818687599688,
        "max_ms": 51.77192099927197,
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
          26,
          272,
          14353,
          297,
          35,
          4,
          0,
          0
        ],
        "deviation_counts": {
          "2": 3898,
          "5": 634,
          "8": 151
        }
      },
      "physical_axes": {
        "ax": {
          "mean": -2.059508146345364,
          "std": 0.049089868611180296,
          "min": -2.7437551025390623,
          "max": -1.4628572143554686,
          "rms": 2.060093109561599
        },
        "ay": {
          "mean": -0.4774874834950968,
          "std": 0.11950898449955549,
          "min": -1.8148048583984373,
          "max": 2.530671154785156,
          "rms": 0.4922161052531656
        },
        "az": {
          "mean": -9.537070528697534,
          "std": 0.09369061154556342,
          "min": -11.741164941406248,
          "max": -8.643067993164061,
          "rms": 9.537530718170341
        },
        "gx": {
          "mean": -0.22709567144809997,
          "std": 0.9725997729331726,
          "min": -11.17557251908397,
          "max": 10.083969465648854,
          "rms": 0.9987606131101298
        },
        "gy": {
          "mean": 2.1001523865402754,
          "std": 0.7670418048127858,
          "min": -4.396946564885496,
          "max": 8.732824427480915,
          "rms": 2.235842833703047
        },
        "gz": {
          "mean": 1.101894747350043,
          "std": 2.6406017833294766,
          "min": -12.603053435114504,
          "max": 16.671755725190838,
          "rms": 2.861284643715201
        }
      },
      "score_distributions": {
        "classifier": {
          "0": 0.0,
          "50": 0.0,
          "95": 0.0,
          "99": 0.0,
          "99.9": 0.003925781250000426,
          "100": 0.0078125
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
      "rail_counts": {
        "ax": 0,
        "ay": 0,
        "az": 0,
        "gx": 0,
        "gy": 0,
        "gz": 0
      },
      "confirmed_alert_events": 0,
      "i2c_failures": 0,
      "gap_count": 0,
      "C_D": 1.0
    },
    {
      "boot": 3,
      "phase": "guided_motion",
      "boot_id": "<redacted-boot-id>",
      "first_sample_uptime_s": 4248.022393239,
      "identity_counts": {
        "0x70": 100
      },
      "registers": {
        "SMPLRT_DIV": 0,
        "CONFIG": 0,
        "GYRO_CONFIG": 0,
        "ACCEL_CONFIG": 0,
        "ACCEL_CONFIG2": 0,
        "FIFO_EN": 0,
        "INT_PIN_CFG": 0,
        "INT_ENABLE": 0,
        "INT_STATUS": 1,
        "USER_CTRL": 0,
        "PWR_MGMT_1": 0,
        "PWR_MGMT_2": 0,
        "FIFO_COUNT_H": 0,
        "FIFO_COUNT_L": 0,
        "WHO_AM_I": 112
      },
      "source_hashes": {
        "raw_sensor.csv": "4221ff28be3565e995974a7262d4ca00ea42de11030eb6b1e69e266ae2f405c0",
        "README.txt": "212b60bcf530699bb1284512b5a45028361aab13145755a5ffe82a7317f84325",
        "window_scores.csv": "a3e8b3fb816299fc5e8ae0e704123bff283c353202fdcf52e7841df5bad5a468",
        "metadata.json": "2a3052cb869531520c01ce841506d1cc3daf7e04a9175f8c06cb86bc539b1dec",
        "fifo_batches.json": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
        "movement_cue.json": "c096aa0e4b3d828652168879339227d9d5f244b4cbccff6715039a06467ac42f",
        "registers_during.json": "31d645e3f093b9bb5d7da2a3532bf16639c8d12735ae911358b35a42bfd9f82e",
        "registers_restored.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "registers_before.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "errors.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "configuration.json": "6c7fce2e496de288e22029a3f364b2f07cbd96fe7709dda5623e358f803cc88b",
        "summary.json": "7d808589fe03fc83f22f41a8f96c0e7ec25fb10a17e5c457b1de3c090184ffee",
        "resources.json": "c125ca77db772ebce19d19c85c1af6354c3ae29fcf1b26e9e1e215b8b9178fba",
        "throttled_start.json": "518a5b7e760f3e653fef809b35392a9839d13a23cf4bdbf3b298cf85fc8117f2",
        "gc_events.json": "8c168a43e565f2e74f7d847eca18b55a95a5d5efb8512d5c3b03a2bd9ba13057"
      },
      "elapsed_s": 120.0051983580006,
      "n_samples": 5985,
      "n_windows": 396,
      "sample_rate_hz": 49.872839526046974,
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
      "rail_counts": {
        "ax": 2,
        "ay": 0,
        "az": 0,
        "gx": 0,
        "gy": 4,
        "gz": 11
      },
      "confirmed_alert_events": 1,
      "i2c_failures": 0,
      "gap_count": 0,
      "C_D": 1.0
    },
    {
      "boot": 4,
      "phase": "stationary",
      "boot_id": "<redacted-boot-id>",
      "first_sample_uptime_s": 97.266535921,
      "identity_counts": {
        "0x70": 100
      },
      "registers": {
        "SMPLRT_DIV": 0,
        "CONFIG": 0,
        "GYRO_CONFIG": 0,
        "ACCEL_CONFIG": 0,
        "ACCEL_CONFIG2": 0,
        "FIFO_EN": 0,
        "INT_PIN_CFG": 0,
        "INT_ENABLE": 0,
        "INT_STATUS": 1,
        "USER_CTRL": 0,
        "PWR_MGMT_1": 0,
        "PWR_MGMT_2": 0,
        "FIFO_COUNT_H": 0,
        "FIFO_COUNT_L": 0,
        "WHO_AM_I": 112
      },
      "source_hashes": {
        "raw_sensor.csv": "0ca85b2eb66ab1013ea6110f6d90b7f941e448afa397e97479155e45dc92e407",
        "README.txt": "683c4aa7db0f9c4b77bd98914ac53b51b6ac7249ccc398603c5230bef540e705",
        "window_scores.csv": "83e171fa4274a30e366d321cf77a077c6776031bd4f123a99cdf8926933a0a1e",
        "metadata.json": "f7305fc3059108f283512b2776fcf03dac5c5cfde624b695033e1a949d28f0c0",
        "fifo_batches.json": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
        "registers_during.json": "31d645e3f093b9bb5d7da2a3532bf16639c8d12735ae911358b35a42bfd9f82e",
        "registers_restored.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "registers_before.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "errors.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "configuration.json": "6c7fce2e496de288e22029a3f364b2f07cbd96fe7709dda5623e358f803cc88b",
        "summary.json": "95360a74adc182693d754810a800251a36569fa127dd4ee2728ec88747e26328",
        "resources.json": "13a71d1f9d415a91b19a44bef5331e5fa64d3e1cbbae4889946481b6c42a0221",
        "throttled_start.json": "518a5b7e760f3e653fef809b35392a9839d13a23cf4bdbf3b298cf85fc8117f2",
        "gc_events.json": "9b60bc8b96500f88a46ee2c5ab26b88686cf2dd82c7d7711fc92b11119e74e66"
      },
      "elapsed_s": 600.00060187,
      "n_samples": 29991,
      "n_windows": 1996,
      "sample_rate_hz": 49.984949859263715,
      "timing": {
        "n": 29990,
        "mean_ms": 20.005811319373127,
        "median_ms": 19.995401000016955,
        "std_ms": 1.8699371573147232,
        "rms_error_from_20ms": 1.869946187391264,
        "p90_ms": 21.813407899963977,
        "p95_ms": 22.780247799968834,
        "p99_ms": 25.96963374000154,
        "p99.9_ms": 31.16463200499196,
        "max_ms": 43.62840200001017,
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
          35,
          421,
          29059,
          427,
          45,
          3,
          0,
          0
        ],
        "deviation_counts": {
          "2": 4713,
          "5": 931,
          "8": 251
        }
      },
      "physical_axes": {
        "ax": {
          "mean": -2.2545541065066104,
          "std": 0.04517171007805832,
          "min": -2.6384102294921874,
          "max": -1.8914193115234375,
          "rms": 2.2550065859232418
        },
        "ay": {
          "mean": 0.7944583947295192,
          "std": 0.047556445400641724,
          "min": 0.040701428222656245,
          "max": 1.3120225097656248,
          "rms": 0.7958804913147127
        },
        "az": {
          "mean": -9.46357226200412,
          "std": 0.05335713275388987,
          "min": -9.72285294189453,
          "max": -9.200916979980468,
          "rms": 9.46372267882938
        },
        "gx": {
          "mean": -0.21221048248316735,
          "std": 0.8371966396926391,
          "min": -4.3816793893129775,
          "max": 3.8931297709923665,
          "rms": 0.8636732613600964
        },
        "gy": {
          "mean": 2.115694250259811,
          "std": 0.6904882224900258,
          "min": -6.633587786259542,
          "max": 11.251908396946565,
          "rms": 2.2255192980470553
        },
        "gz": {
          "mean": 1.0900758777251496,
          "std": 2.779330054394027,
          "min": -14.977099236641221,
          "max": 15.793893129770993,
          "rms": 2.985454901762236
        }
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
      "rail_counts": {
        "ax": 0,
        "ay": 0,
        "az": 0,
        "gx": 0,
        "gy": 0,
        "gz": 0
      },
      "confirmed_alert_events": 0,
      "i2c_failures": 0,
      "gap_count": 0,
      "C_D": 1.0
    },
    {
      "boot": 4,
      "phase": "guided_motion",
      "boot_id": "<redacted-boot-id>",
      "first_sample_uptime_s": 4738.675160321,
      "identity_counts": {
        "0x70": 100
      },
      "registers": {
        "SMPLRT_DIV": 0,
        "CONFIG": 0,
        "GYRO_CONFIG": 0,
        "ACCEL_CONFIG": 0,
        "ACCEL_CONFIG2": 0,
        "FIFO_EN": 0,
        "INT_PIN_CFG": 0,
        "INT_ENABLE": 0,
        "INT_STATUS": 1,
        "USER_CTRL": 0,
        "PWR_MGMT_1": 0,
        "PWR_MGMT_2": 0,
        "FIFO_COUNT_H": 0,
        "FIFO_COUNT_L": 0,
        "WHO_AM_I": 112
      },
      "source_hashes": {
        "raw_sensor.csv": "91ab41bbf0792d0f0e683e7aabc9ad1469d851b28faa21e90c2cdd1cc3212e27",
        "README.txt": "60dbdf4c785c6d205a58c981893d2603abb8ff1c60412e654a978741c8b5a2d8",
        "window_scores.csv": "f94e120d6e00ec26f5042863d23145e937f71ce4b7d9bdbf63c3df4173aff518",
        "metadata.json": "46db3333b6c18d3621e9a2f96dc653a90f64d42008711bb2ce735d7dbc7128ee",
        "fifo_batches.json": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
        "registers_during.json": "31d645e3f093b9bb5d7da2a3532bf16639c8d12735ae911358b35a42bfd9f82e",
        "registers_restored.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "registers_before.json": "8653ee928584842bfd6ee4789da50d2162c1f46baf60b6a000446f41e7344142",
        "errors.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "configuration.json": "6c7fce2e496de288e22029a3f364b2f07cbd96fe7709dda5623e358f803cc88b",
        "summary.json": "324b6217ceef16a5900435beda6ae36f4b8a14a2fe06db8269b29058fd329810",
        "resources.json": "5cdd54bac8ff625497437b7be698c34f8fc6c3adfb6d06ac901cb6cf6e0329cc",
        "throttled_start.json": "518a5b7e760f3e653fef809b35392a9839d13a23cf4bdbf3b298cf85fc8117f2",
        "gc_events.json": "55142eba08fe8598beef36e83641c4d1ee08feb6b41a63053163213bb7945d31"
      },
      "elapsed_s": 120.004649556,
      "n_samples": 5998,
      "n_windows": 396,
      "sample_rate_hz": 49.981396739140855,
      "timing": {
        "n": 5997,
        "mean_ms": 20.007326479906638,
        "median_ms": 20.026858000164793,
        "std_ms": 2.1240219254432344,
        "rms_error_from_20ms": 2.1240345611763023,
        "p90_ms": 22.456294800031177,
        "p95_ms": 23.49477739971917,
        "p99_ms": 25.718329759911285,
        "p99.9_ms": 31.28434226048598,
        "max_ms": 36.35384100016381,
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
          4,
          96,
          5791,
          98,
          8,
          0,
          0,
          0
        ],
        "deviation_counts": {
          "2": 1551,
          "5": 206,
          "8": 27
        }
      },
      "physical_axes": {
        "ax": {
          "mean": -0.7752371487252748,
          "std": 2.8072916339737195,
          "min": -13.632584252929687,
          "max": 15.978901879882812,
          "rms": 2.9123665557313574
        },
        "ay": {
          "mean": 3.4382276623172894,
          "std": 3.476517882991408,
          "min": -6.995857250976562,
          "max": 12.473790649414061,
          "rms": 4.889538429001543
        },
        "az": {
          "mean": -4.9906926039290935,
          "std": 6.307374601114513,
          "min": -17.62850682373047,
          "max": 11.604695446777344,
          "rms": 8.043008580481374
        },
        "gx": {
          "mean": -0.2831898164528126,
          "std": 21.823316241127966,
          "min": -186.23664122137404,
          "max": 213.85496183206106,
          "rms": 21.825153567212812
        },
        "gy": {
          "mean": 3.3107422575973158,
          "std": 33.49979704174896,
          "min": -250.13740458015266,
          "max": 221.64885496183206,
          "rms": 33.66299772947462
        },
        "gz": {
          "mean": 1.124196615156706,
          "std": 21.25769157397986,
          "min": -250.13740458015266,
          "max": 196.46564885496184,
          "rms": 21.287396954160084
        }
      },
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
          "95": 0.5891492366790771,
          "99": 0.9819153547286987,
          "99.9": 0.9819153547286987,
          "100": 0.9819153547286987
        }
      },
      "rail_counts": {
        "ax": 0,
        "ay": 0,
        "az": 0,
        "gx": 0,
        "gy": 2,
        "gz": 1
      },
      "confirmed_alert_events": 1,
      "i2c_failures": 0,
      "gap_count": 0,
      "C_D": 1.0
    }
  ],
  "register_consistency": {
    "SMPLRT_DIV": true,
    "CONFIG": true,
    "GYRO_CONFIG": true,
    "ACCEL_CONFIG": true,
    "ACCEL_CONFIG2": true,
    "FIFO_EN": true,
    "USER_CTRL": true,
    "INT_ENABLE": true,
    "PWR_MGMT_1": true,
    "PWR_MGMT_2": true,
    "WHO_AM_I": true
  },
  "excluded_boot2": "Startup baseline valid, motion files empty; preserved, not substituted or relabeled.",
  "operator_confirmations": {
    "boot1": {
      "operator_confirmation": "Completed as instructed",
      "recorded_utc": "2026-10-04T17:48:38.311864+00:00",
      "raw_rows_verified": 5989,
      "score_rows_verified": 396,
      "configuration_restored": true,
      "i2c_failures": 0,
      "gaps": 0,
      "confirmed_policy_events": 1,
      "positive_windows": 39,
      "rail_counts": {
        "ax": 0,
        "ay": 0,
        "az": 0,
        "gx": 0,
        "gy": 4,
        "gz": 2
      },
      "assessment": "Capture completed. One false policy trigger during operator-attested benign motion; gyro rails reached. No physical alert or SMS sent. Preserve this adverse result; H1 three-boot comparison remains pending.",
      "early_baseline_first_sample_uptime_s": 98.728620449,
      "early_baseline_limitation": "Early recording began about 99 seconds after boot, not at power-on."
    },
    "boot3": {
      "operator_reply": "yes",
      "question_answered": "Completed three left/right and three forward/back cycles after START and returned helmet to rest; preceding five-minute baseline untouched.",
      "baseline_stationarity_user_attested": true,
      "guided_sequence_completion_user_attested": true,
      "baseline_samples": 14988,
      "motion_samples": 5985,
      "baseline_windows": 996,
      "motion_windows": 396,
      "baseline_confirmed_events": 0,
      "motion_confirmed_events": 1,
      "motion_rail_counts": {
        "ax": 2,
        "ay": 0,
        "az": 0,
        "gx": 0,
        "gy": 4,
        "gz": 11
      },
      "baseline_verification": "boot3_baseline_review",
      "motion_verification": "boot3_guided_motion_verification",
      "limitations": [
        "Manual movements are not amplitude-matched.",
        "One false policy event during user-attested benign motion; preserve acceleration and gyro rail hits.",
        "Baseline user-attested untouched; brief recorded signal excursions retained, not removed.",
        "No physical alarm or SMS sent.",
        "This boot baseline begins after 60 minutes uptime, not during cold start.",
        "H1 incomplete because boot2 motion is empty; another complete boot is needed."
      ]
    },
    "boot4_baseline_warm": {
      "boot": 4,
      "recorded_utc": "2026-10-05T17:36:20.881464+00:00",
      "power_off_user_statement": "10-15s",
      "both_pi_and_sensor_unpowered_seconds_range": [
        10,
        15
      ],
      "interval_is_approximate": true,
      "stationarity_user_statement": "yes",
      "stationarity_question": "Was the helmet untouched throughout the recording, approximately 10:13\u201310:23 PM PKT?",
      "baseline_untouched_throughout": true,
      "scope": "Operator confirms completed boot4 stationary baseline only; no attestation of future stationarity or guided motion.",
      "warm_confirmation": {
        "recorded_utc": "2026-10-05T18:29:29.744200+00:00",
        "user_statement": "yes",
        "same_orientation_since_initial_baseline": true,
        "untouched_throughout_warm_recording": true
      }
    }
  },
  "limitations": [
    "Boot4 motion files pass replay verification, but final operator confirmation of the instructed sequence is absent.",
    "Manual motion amplitudes and resting orientation across boots are not matched; axis offsets are not calibrated bias estimates.",
    "Each guided capture produced one policy event. Preserve benign-motion events and clipping; no physical alarm or SMS.",
    "Boot3 baseline was late after boot. No new physical measurement."
  ]
}
