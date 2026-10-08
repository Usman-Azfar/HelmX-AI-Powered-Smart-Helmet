package com.yourname.helmx

import org.json.JSONObject

/**
 * Parses a BLE notification payload from the helmet into an updated [HelmetData].
 *
 * Supported formats:
 *  - JSON:      {"temperature":..,"humidity":..,"air_quality":..,"destination":..}
 *  - CSV (5+):  battery,speed,drowsy,crash,distance
 *  - CSV (2):   temperature,humidity (legacy)
 *
 * Returns null when the payload is not recognised, so the caller keeps its current state.
 */
object HelmetDataParser {

    fun parse(rawString: String, current: HelmetData): HelmetData? {
        // Clean the string of any non-printable or null characters
        val cleanString = rawString.replace(Regex("[^\\x20-\\x7E]"), "").trim()

        if (cleanString.startsWith("{") && cleanString.endsWith("}")) {
            val json = try {
                JSONObject(cleanString)
            } catch (e: Exception) {
                return null
            }
            return current.copy(
                temperature = json.optDouble("temperature", 0.0).toFloat(),
                humidity = json.optDouble("humidity", 0.0).toFloat(),
                airQuality = json.optString("air_quality", "Unknown"),
                destination = json.optString("destination", ""),
                connectionStatus = ConnectionStatus.CONNECTED
            )
        }

        // Fallback to legacy CSV parsing
        val parts = cleanString.split(",").map { it.trim() }
        if (parts.size >= 5) {
            return current.copy(
                batteryLevel = parts[0].toIntOrNull() ?: 0,
                speed = parts[1].toFloatOrNull() ?: 0f,
                isDrowsy = parts[2] == "1" || parts[2] == "true",
                isCrashDetected = parts[3] == "1" || parts[3] == "true",
                distance = parts[4].toFloatOrNull() ?: 0f,
                connectionStatus = ConnectionStatus.CONNECTED
            )
        }
        if (parts.size == 2) {
            val temp = parts[0].filter { it.isDigit() || it == '.' || it == '-' }.toFloatOrNull()
            val hum = parts[1].filter { it.isDigit() || it == '.' }.toFloatOrNull()
            if (temp != null && hum != null) {
                return current.copy(
                    temperature = temp,
                    humidity = hum,
                    connectionStatus = ConnectionStatus.CONNECTED
                )
            }
        }
        return null
    }
}
