package com.yourname.helmx

import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Follows the rider's progress along a [Route]: which maneuver comes next, how far away it is,
 * what is left of the trip, and whether the rider has left the route or arrived.
 * Pure Kotlin so it can be unit tested.
 */
class NavigationGuide(private val route: Route) {

    companion object {
        const val OFF_ROUTE_M = 45.0        // farther than this from the line counts as off route
        const val OFF_ROUTE_FIXES = 2       // ...for this many fixes in a row
        const val ARRIVAL_M = 25.0
        // Straight-line closeness only counts near the end, so a route that loops past the
        // destination early on doesn't end the trip prematurely
        const val ARRIVAL_MAX_REMAINING_M = 150.0
        private const val M_PER_DEG = 111_320.0

        /** Initial compass bearing from point 1 to point 2, in degrees 0..360. */
        fun bearingDegrees(lat1: Double, lng1: Double, lat2: Double, lng2: Double): Double {
            val p1 = Math.toRadians(lat1)
            val p2 = Math.toRadians(lat2)
            val dl = Math.toRadians(lng2 - lng1)
            val y = sin(dl) * cos(p2)
            val x = cos(p1) * sin(p2) - sin(p1) * cos(p2) * cos(dl)
            return (Math.toDegrees(atan2(y, x)) + 360.0) % 360.0
        }
    }

    data class Progress(
        val nextStepIndex: Int,         // index into route.steps, -1 if the route has no steps
        val distanceToNextM: Double,
        val remainingDistanceM: Double,
        val remainingDurationS: Double,
        val fractionTravelled: Double,   // 0..1 along the route line
        val isOffRoute: Boolean,
        val hasArrived: Boolean
    )

    private val points = route.points
    private val cumulative = DoubleArray(points.size)
    private val totalM: Double
    private val stepAlong: DoubleArray
    private var lastSegment = 0
    private var offRouteCount = 0

    init {
        for (i in 1 until points.size) {
            cumulative[i] = cumulative[i - 1] + RideTracker.haversineMeters(
                points[i - 1].lat, points[i - 1].lng, points[i].lat, points[i].lng
            )
        }
        totalM = cumulative.lastOrNull() ?: 0.0

        // Where along the line each maneuver happens (searching forward keeps loops in order)
        var searchFrom = 0
        stepAlong = DoubleArray(route.steps.size) { i ->
            val step = route.steps[i]
            var best = searchFrom
            var bestDist = Double.MAX_VALUE
            for (p in searchFrom until points.size) {
                val d = RideTracker.haversineMeters(step.lat, step.lng, points[p].lat, points[p].lng)
                if (d < bestDist) {
                    bestDist = d
                    best = p
                }
            }
            searchFrom = best
            cumulative.getOrElse(best) { 0.0 }
        }
    }

    fun update(lat: Double, lng: Double): Progress {
        if (points.size < 2) {
            return Progress(route.steps.lastIndex, 0.0, 0.0, 0.0, 1.0, isOffRoute = false, hasArrived = true)
        }

        // Search near the last known segment first; fall back to the whole line if that fails
        var best = project(lat, lng, max(0, lastSegment - 3), minOf(points.size - 2, lastSegment + 40))
        if (best.distance > OFF_ROUTE_M) {
            val full = project(lat, lng, 0, points.size - 2)
            if (full.distance < best.distance) best = full
        }
        lastSegment = best.segment

        val segmentLength = cumulative[best.segment + 1] - cumulative[best.segment]
        val along = cumulative[best.segment] + best.t * segmentLength
        val remaining = max(0.0, totalM - along)

        offRouteCount = if (best.distance > OFF_ROUTE_M) offRouteCount + 1 else 0
        val isOffRoute = offRouteCount >= OFF_ROUTE_FIXES

        val next = if (route.steps.isEmpty()) -1
        else (1 until route.steps.size).firstOrNull { stepAlong[it] > along + 3.0 } ?: route.steps.lastIndex
        val toNext = if (next >= 0) max(0.0, stepAlong[next] - along) else remaining

        val end = points.last()
        val toDestination = RideTracker.haversineMeters(lat, lng, end.lat, end.lng)
        val hasArrived = (remaining <= ARRIVAL_M && best.distance <= OFF_ROUTE_M) ||
            (toDestination <= ARRIVAL_M && remaining <= ARRIVAL_MAX_REMAINING_M)

        val remainingDuration = if (totalM > 0) route.durationS * remaining / totalM else 0.0
        val fraction = if (totalM > 0) (along / totalM).coerceIn(0.0, 1.0) else 0.0
        return Progress(next, toNext, remaining, remainingDuration, fraction, isOffRoute, hasArrived)
    }

    private data class Projection(val segment: Int, val t: Double, val distance: Double)

    /** Closest point on segments [from]..[to] to (lat, lng), using a local flat-earth approximation. */
    private fun project(lat: Double, lng: Double, from: Int, to: Int): Projection {
        val mPerDegLng = M_PER_DEG * cos(Math.toRadians(lat))
        var best = Projection(from, 0.0, Double.MAX_VALUE)
        for (i in from..to) {
            val ax = (points[i].lng - lng) * mPerDegLng
            val ay = (points[i].lat - lat) * M_PER_DEG
            val bx = (points[i + 1].lng - lng) * mPerDegLng
            val by = (points[i + 1].lat - lat) * M_PER_DEG
            val dx = bx - ax
            val dy = by - ay
            val lengthSq = dx * dx + dy * dy
            val t = if (lengthSq == 0.0) 0.0 else (-(ax * dx + ay * dy) / lengthSq).coerceIn(0.0, 1.0)
            val cx = ax + t * dx
            val cy = ay + t * dy
            val d = sqrt(cx * cx + cy * cy)
            if (d < best.distance) best = Projection(i, t, d)
        }
        return best
    }
}
