package com.yourname.helmx

enum class ConnectionStatus(val label: String) {
    DISCONNECTED("Disconnected"),
    SEARCHING("Searching..."),
    CONNECTING("Connecting..."),
    CONNECTED("Connected"),
    RECONNECTING("Reconnecting..."),
    NOT_FOUND("Device Not Found"),
    SCAN_FAILED("Scan Failed"),
    CONNECTION_FAILED("Connection Failed"),
    SERVICE_NOT_FOUND("Not a HelmX helmet");

    val isBusy: Boolean
        get() = this == SEARCHING || this == CONNECTING || this == RECONNECTING
}

data class HelmetData(
    val batteryLevel: Int = 0,
    val speed: Float = 0f,
    val isDrowsy: Boolean = false,
    val isCrashDetected: Boolean = false,
    val distance: Float = 0f,
    val temperature: Float = 0f,
    val humidity: Float = 0f,
    val airQuality: String = "Unknown",
    val destination: String = "",
    val connectionStatus: ConnectionStatus = ConnectionStatus.DISCONNECTED
)
