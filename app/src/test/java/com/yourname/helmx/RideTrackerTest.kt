package com.yourname.helmx

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class RideTrackerTest {

    private var now = 1_000_000L
    private val tracker = RideTracker { now }

    // ~0.001 deg latitude ≈ 111 m
    private val startLat = 31.5204
    private val startLng = 74.3587

    @Test
    fun haversine_knownDistance() {
        // 0.01 deg of latitude ≈ 1112 m
        val d = RideTracker.haversineMeters(31.0, 74.0, 31.01, 74.0)
        assertEquals(1112.0, d, 2.0)
    }

    @Test
    fun ride_accumulatesDistance_andComputesSpeed() {
        tracker.start("Liberty Market")
        for (i in 0..10) tracker.addFix(startLat + i * 0.001, startLng, 10f) // ~1.11 km
        now += 5 * 60 * 1000 // 5 minutes

        val ride = tracker.stop()

        assertNotNull(ride)
        ride!!
        assertEquals(1.11, ride.distanceKm, 0.02)
        assertEquals(300L, ride.durationSec)
        assertEquals(13.3, ride.avgSpeedKmh, 0.3)
        assertEquals("Liberty Market", ride.destination)
        assertFalse(tracker.isTracking)
    }

    @Test
    fun inaccurateFixes_andJitter_areIgnored() {
        tracker.start("X")
        tracker.addFix(startLat, startLng, 10f)
        tracker.addFix(startLat + 0.01, startLng, 200f)      // poor accuracy: ignored
        repeat(50) { tracker.addFix(startLat + 0.00001, startLng, 10f) } // ~1 m jitter: ignored
        tracker.addFix(startLat + 0.002, startLng, 10f)      // ~222 m real move
        now += 2 * 60 * 1000

        val ride = tracker.stop()!!

        assertEquals(0.222, ride.distanceKm, 0.01)
    }

    @Test
    fun shortRide_isNotSaved() {
        tracker.start("X")
        tracker.addFix(startLat, startLng, 10f)
        tracker.addFix(startLat + 0.0005, startLng, 10f) // ~55 m
        now += 10 * 60 * 1000
        assertNull(tracker.stop())

        tracker.start("X")
        tracker.addFix(startLat, startLng, 10f)
        tracker.addFix(startLat + 0.005, startLng, 10f) // ~555 m but only 20 s
        now += 20 * 1000
        assertNull(tracker.stop())
    }

    @Test
    fun fixesOutsideRide_areIgnored_andStopWithoutStartIsNull() {
        tracker.addFix(startLat, startLng, 10f)
        assertNull(tracker.stop())
        tracker.start("X")
        assertTrue(tracker.isTracking)
    }

    @Test
    fun formatDuration() {
        assertEquals("5 min", RideHistoryAdapter.formatDuration(300))
        assertEquals("1 h 5 min", RideHistoryAdapter.formatDuration(3900))
    }
}
