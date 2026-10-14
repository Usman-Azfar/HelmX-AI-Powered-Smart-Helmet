
G,O2 — Controlled injected-trace onset-to-local-alert timing
Status: COMPLETE (CONTROLLED TRACE SEGMENTS)
UTC: 2026-10-02T15:13:56.764015+00:00
Evidence: piResults/final_pi_review_closure/gpio_G_O2
{
  "trials": 10,
  "unique_sessions": 10,
  "triggered": 5,
  "latencies_s": {
    "onset_to_first_anomaly": {
      "n": 6,
      "50": 1.7826898275001213,
      "95": 2.0099434492501587,
      "100": 2.0841261710002073
    },
    "onset_to_confirmation": {
      "n": 5,
      "50": 2.3818826270000955,
      "95": 2.3866160418001074,
      "100": 2.387148919000083
    },
    "onset_to_gpio_call": {
      "n": 5,
      "50": 2.3821948270001485,
      "95": 2.3871548188000817,
      "100": 2.38766023900007
    },
    "first_anomaly_to_confirmation": {
      "n": 5,
      "50": 0.6000569689999793,
      "95": 0.6047164406000775,
      "100": 0.6055586780000795
    },
    "confirmation_to_gpio_call": {
      "n": 5,
      "50": 0.0005113199999868812,
      "95": 0.0040999362000093235,
      "100": 0.004962769000030676
    }
  },
  "trace_summary": [
    {
      "session": "carla_onder",
      "source_samples": [
        0,
        300
      ],
      "injected_samples": 300,
      "onset": 1420.644652903,
      "confirmation": null,
      "first_anomaly": null,
      "confirmation_triplet_times": [],
      "gpio_on_call_start": null,
      "gpio_on_call_return": null,
      "gpio_off_call_start": null,
      "gpio_off_call_return": null,
      "cancel_outcome": null,
      "cancellation_handler_start": null,
      "cancellation_accepted": null,
      "cancellation_handler_end": null,
      "outcome": "no trigger within injected segment"
    },
    {
      "session": "road_2. Aggressive",
      "source_samples": [
        0,
        300
      ],
      "injected_samples": 300,
      "onset": 1426.66375527,
      "confirmation": null,
      "first_anomaly": null,
      "confirmation_triplet_times": [],
      "gpio_on_call_start": null,
      "gpio_on_call_return": null,
      "gpio_off_call_start": null,
      "gpio_off_call_return": null,
      "cancel_outcome": null,
      "cancellation_handler_start": null,
      "cancellation_accepted": null,
      "cancellation_handler_end": null,
      "outcome": "no trigger within injected segment"
    },
    {
      "session": "road_2.Bump",
      "source_samples": [
        0,
        251
      ],
      "injected_samples": 251,
      "onset": 1432.649321479,
      "confirmation": null,
      "first_anomaly": null,
      "confirmation_triplet_times": [],
      "gpio_on_call_start": null,
      "gpio_on_call_return": null,
      "gpio_off_call_start": null,
      "gpio_off_call_return": null,
      "cancel_outcome": null,
      "cancellation_handler_start": null,
      "cancellation_accepted": null,
      "cancellation_handler_end": null,
      "outcome": "no trigger within injected segment"
    },
    {
      "session": "near_fall_Acceleration On Curve",
      "source_samples": [
        0,
        120
      ],
      "injected_samples": 90,
      "onset": 1437.657498444,
      "confirmation": 1439.446814573,
      "first_anomaly": 1438.841255895,
      "confirmation_triplet_times": [
        1438.841255895,
        1439.14240162,
        1439.446814573
      ],
      "gpio_on_call_start": 1439.451777342,
      "gpio_on_call_return": 1439.456204568,
      "gpio_off_call_start": 1440.459887581,
      "gpio_off_call_return": 1440.460373066,
      "cancel_outcome": {
        "cancelled": true,
        "sms_attempted": false,
        "sms_sent": false,
        "gps_available": false
      },
      "cancellation_handler_start": 1439.446850074,
      "cancellation_accepted": 1440.459874987,
      "cancellation_handler_end": 1440.460632375,
      "outcome": "triggered and controlled-cancelled"
    },
    {
      "session": "fall_fall-in-a-leaning",
      "source_samples": [
        0,
        120
      ],
      "injected_samples": 90,
      "onset": 1440.465124863,
      "confirmation": 1442.247119171,
      "first_anomaly": 1441.647062202,
      "confirmation_triplet_times": [
        1441.647062202,
        1441.947332567,
        1442.247119171
      ],
      "gpio_on_call_start": 1442.24751193,
      "gpio_on_call_return": 1442.24789193,
      "gpio_off_call_start": 1443.248588839,
      "gpio_off_call_return": 1443.249079863,
      "cancel_outcome": {
        "cancelled": true,
        "sms_attempted": false,
        "sms_sent": false,
        "gps_available": false
      },
      "cancellation_handler_start": 1442.247139968,
      "cancellation_accepted": 1443.248578876,
      "cancellation_handler_end": 1443.249349209,
      "outcome": "triggered and controlled-cancelled"
    },
    {
      "session": "darus_crash_Iso_115_Out",
      "source_samples": [
        0,
        150
      ],
      "injected_samples": 120,
      "onset": 1443.254821096,
      "confirmation": 1445.639305629,
      "first_anomaly": 1445.037958138,
      "confirmation_triplet_times": [
        1445.037958138,
        1445.340473961,
        1445.639305629
      ],
      "gpio_on_call_start": 1445.639954234,
      "gpio_on_call_return": 1445.640840553,
      "gpio_off_call_start": 1446.642276085,
      "gpio_off_call_return": 1446.64264551,
      "cancel_outcome": {
        "cancelled": true,
        "sms_attempted": false,
        "sms_sent": false,
        "gps_available": false
      },
      "cancellation_handler_start": 1445.639329834,
      "cancellation_accepted": 1446.642268567,
      "cancellation_handler_end": 1446.642804907,
      "outcome": "triggered and controlled-cancelled"
    },
    {
      "session": "darus_crash_Iso_312_2_Out",
      "source_samples": [
        0,
        150
      ],
      "injected_samples": 120,
      "onset": 1446.644753351,
      "confirmation": 1449.026635978,
      "first_anomaly": 1448.426995964,
      "confirmation_triplet_times": [
        1448.426995964,
        1448.726763452,
        1449.026635978
      ],
      "gpio_on_call_start": 1449.026948178,
      "gpio_on_call_return": 1449.027121705,
      "gpio_off_call_start": 1450.029690688,
      "gpio_off_call_return": 1450.030661197,
      "cancel_outcome": {
        "cancelled": true,
        "sms_attempted": false,
        "sms_sent": false,
        "gps_available": false
      },
      "cancellation_handler_start": 1449.026651997,
      "cancellation_accepted": 1450.029669557,
      "cancellation_handler_end": 1450.031119404,
      "outcome": "triggered and controlled-cancelled"
    },
    {
      "session": "darus_crash_Iso_513_2_Out",
      "source_samples": [
        0,
        150
      ],
      "injected_samples": 120,
      "onset": 1450.038710783,
      "confirmation": 1452.425859702,
      "first_anomaly": 1451.826106067,
      "confirmation_triplet_times": [
        1451.826106067,
        1452.121462595,
        1452.425859702
      ],
      "gpio_on_call_start": 1452.426371022,
      "gpio_on_call_return": 1452.426738225,
      "gpio_off_call_start": 1453.429935834,
      "gpio_off_call_return": 1453.430373448,
      "cancel_outcome": {
        "cancelled": true,
        "sms_attempted": false,
        "sms_sent": false,
        "gps_available": false
      },
      "cancellation_handler_start": 1452.425889055,
      "cancellation_accepted": 1453.429925908,
      "cancellation_handler_end": 1453.430677369,
      "outcome": "triggered and controlled-cancelled"
    },
    {
      "session": "darus_non_crash_Pothole_5_Out",
      "source_samples": [
        0,
        150
      ],
      "injected_samples": 150,
      "onset": 1453.437863564,
      "confirmation": null,
      "first_anomaly": null,
      "confirmation_triplet_times": [],
      "gpio_on_call_start": null,
      "gpio_on_call_return": null,
      "gpio_off_call_start": null,
      "gpio_off_call_return": null,
      "cancel_outcome": null,
      "cancellation_handler_start": null,
      "cancellation_accepted": null,
      "cancellation_handler_end": null,
      "outcome": "no trigger within injected segment"
    },
    {
      "session": "darus_non_crash_Randomstate_60_Out",
      "source_samples": [
        0,
        150
      ],
      "injected_samples": 150,
      "onset": 1456.423796143,
      "confirmation": null,
      "first_anomaly": 1458.507922314,
      "confirmation_triplet_times": [],
      "gpio_on_call_start": null,
      "gpio_on_call_return": null,
      "gpio_off_call_start": null,
      "gpio_off_call_return": null,
      "cancel_outcome": null,
      "cancellation_handler_start": null,
      "cancellation_accepted": null,
      "cancellation_handler_end": null,
      "outcome": "no trigger within injected segment"
    }
  ],
  "selection": "One segment per held-out session; trigger-bearing segments selected around prior composed-replay trigger position. Controls use first six seconds. Filter starts fresh per segment; this is not a blind sensitivity experiment.",
  "limitations": "Software GPIO-call timestamps, not measured electrical edges. Synthetic 50-Hz pacing, no live IMU acquisition. Triggered trials execute actual cancellation handler with a controlled software cancellation after one second; no voice-recognition or GPS/GSM validation. Injection onset is NOT physical crash onset."
}
