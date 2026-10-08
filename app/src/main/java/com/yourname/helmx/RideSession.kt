package com.yourname.helmx

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Live state of the ride being recorded by [RideTrackingService]. */
data class RideState(
    val isRecording: Boolean = false,
    val destination: String = "",
    val destLat: Double? = null,
    val destLng: Double? = null,
    val distanceKm: Double = 0.0
)

/**
 * Process-wide holder for the current ride. Lives outside any Activity, so the ride survives
 * screen recreation (theme change, rotation) and keeps running while the app is in the background.
 */
object RideSession {
    private val _state = MutableStateFlow(RideState())
    val state: StateFlow<RideState> = _state.asStateFlow()

    internal fun set(state: RideState) {
        _state.value = state
    }
}
