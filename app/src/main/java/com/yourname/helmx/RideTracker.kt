package com.yourname.helmx

import kotlin.math.asin
import kotlin.math.cos
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Measures a ride from a stream of GPS fixes. Pure Kotlin so it can be unit tested.
 *
 * Fixes with poor accuracy are ignored, and very small moves are not counted so GPS jitter
 * while standing still does not add distance.
 */
class RideTracker(private val clock: () -> Long = System::currentTimeMillis) {

    companion object {
        const val MAX_ACCURACY_M = 50f      // ignore fixes less accurate than this
        const val MIN_STEP_M = 5.0          // ignore moves shorter than this (jitter)
        const val MIN_RIDE_DISTANCE_KM = 0.1
        const val MIN_RIDE_DURATION_SEC = 60L

        /** Great-circle distance in metres. */
        fun haversineMeters(lat1: Double, lng1: Double, lat2: Double, lng2: Double): Double {
            val r = 6_371_000.0
            val dLat = Math.toRadians(lat2 - lat1)
            val dLng = Math.toRadians(lng2 - lng1)
            val a = sin(dLat / 2).pow(2) +
                cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) * sin(dLng / 2).pow(2)
            return 2 * r * asin(sqrt(a))
        }
    }

    var isTracking = false
        private set

    val distanceKm: Double
        get() = distanceMeters / 1000.0

    private var startedAt = 0L
    private var destination = ""
    private var distanceMeters = 0.0
    private var lastLat: Double? = null
    private var lastLng: Double? = null

    fun start(destination: String) {
        isTracking = true
        startedAt = clock()
        this.destination = destination
        distanceMeters = 0.0
        lastLat = null
        lastLng = null
    }

    fun addFix(lat: Double, lng: Double, accuracyMeters: Float) {
        if (!isTracking || accuracyMeters > MAX_ACCURACY_M) return
        val prevLat = lastLat
        val prevLng = lastLng
        if (prevLat == null || prevLng == null) {
            lastLat = lat
            lastLng = lng
            return
        }
        val step = haversineMeters(prevLat, prevLng, lat, lng)
        if (step >= MIN_STEP_M) {
            distanceMeters += step
            lastLat = lat
            lastLng = lng
        }
    }

    /**
     * Ends the ride. Returns it, or null when it is too short to be worth saving
     * (e.g. START pressed by accident).
     */
    fun stop(): Ride? {
        if (!isTracking) return null
        isTracking = false
        val endedAt = clock()
        val durationSec = (endedAt - startedAt) / 1000
        val distanceKm = distanceMeters / 1000.0
        if (distanceKm < MIN_RIDE_DISTANCE_KM || durationSec < MIN_RIDE_DURATION_SEC) return null
        return Ride(
            startedAt = startedAt,
            endedAt = endedAt,
            distanceKm = distanceKm,
            durationSec = durationSec,
            avgSpeedKmh = distanceKm / (durationSec / 3600.0),
            destination = destination
        )
    }
}
