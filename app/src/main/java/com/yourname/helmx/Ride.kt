package com.yourname.helmx

import com.google.firebase.firestore.Exclude
import com.google.firebase.firestore.IgnoreExtraProperties

/** A recorded ride, stored at users/{uid}/rides/{id}. */
@IgnoreExtraProperties
data class Ride(
    @get:Exclude val id: String = "",
    val startedAt: Long = 0L,        // epoch millis
    val endedAt: Long = 0L,          // epoch millis
    val distanceKm: Double = 0.0,
    val durationSec: Long = 0L,
    val avgSpeedKmh: Double = 0.0,
    val destination: String = ""
)
