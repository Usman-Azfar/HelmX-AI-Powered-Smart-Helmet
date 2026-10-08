package com.yourname.helmx

import java.util.Locale
import kotlin.math.roundToInt
import kotlin.math.roundToLong

/** How to draw a maneuver arrow: a drawable, rotated and/or mirrored. */
data class ManeuverIcon(val drawableRes: Int, val rotation: Float = 0f, val mirrored: Boolean = false)

/** Turns OSRM maneuvers and numbers into the text and icons shown/spoken to the rider. */
object NavText {

    fun instruction(step: RouteStep): String {
        val onto = if (step.name.isNotBlank()) " onto ${step.name}" else ""
        val modifier = step.modifier ?: "straight"
        return when (step.type) {
            "depart" -> if (step.name.isNotBlank()) "Head along ${step.name}" else "Start your ride"
            "arrive" -> when (modifier) {
                "left", "slight left", "sharp left" -> "Your destination is on the left"
                "right", "slight right", "sharp right" -> "Your destination is on the right"
                else -> "You have arrived at your destination"
            }
            "roundabout", "rotary" -> {
                val exit = step.exit?.let { " take the ${ordinal(it)} exit" } ?: " take the exit"
                "At the roundabout,$exit$onto"
            }
            "exit roundabout", "exit rotary" -> "Exit the roundabout$onto"
            "merge" -> "Merge ${side(modifier)}$onto"
            "on ramp" -> "Take the ramp${sideSuffix(modifier)}$onto"
            "off ramp" -> "Take the exit${sideSuffix(modifier)}$onto"
            "fork" -> "Keep ${side(modifier)} at the fork$onto"
            "end of road" -> "At the end of the road, ${turnPhrase(modifier).replaceFirstChar { it.lowercase() }}$onto"
            "new name", "continue" -> when {
                modifier != "straight" -> "${turnPhrase(modifier)}$onto"
                onto.isEmpty() -> "Continue straight"
                else -> "Continue$onto"
            }
            else -> "${turnPhrase(modifier)}$onto"
        }
    }

    private fun turnPhrase(modifier: String) = when (modifier) {
        "uturn" -> "Make a U-turn"
        "sharp right" -> "Turn sharp right"
        "right" -> "Turn right"
        "slight right" -> "Keep slightly right"
        "straight" -> "Continue straight"
        "slight left" -> "Keep slightly left"
        "left" -> "Turn left"
        "sharp left" -> "Turn sharp left"
        else -> "Continue"
    }

    private fun side(modifier: String) = if (modifier.contains("left")) "left" else if (modifier.contains("right")) "right" else "straight"
    private fun sideSuffix(modifier: String) = when (side(modifier)) { "left" -> " on the left"; "right" -> " on the right"; else -> "" }

    private fun ordinal(n: Int) = n.toString() + when {
        n % 100 in 11..13 -> "th"
        n % 10 == 1 -> "st"
        n % 10 == 2 -> "nd"
        n % 10 == 3 -> "rd"
        else -> "th"
    }

    fun icon(step: RouteStep): ManeuverIcon {
        if (step.type == "arrive") return ManeuverIcon(R.drawable.ic_place_pin)
        return when (step.modifier ?: "straight") {
            "uturn" -> ManeuverIcon(R.drawable.ic_maneuver_uturn)
            "sharp right" -> ManeuverIcon(R.drawable.ic_maneuver_straight, rotation = 135f)
            "right" -> ManeuverIcon(R.drawable.ic_maneuver_turn_right)
            "slight right" -> ManeuverIcon(R.drawable.ic_maneuver_straight, rotation = 45f)
            "slight left" -> ManeuverIcon(R.drawable.ic_maneuver_straight, rotation = -45f)
            "left" -> ManeuverIcon(R.drawable.ic_maneuver_turn_right, mirrored = true)
            "sharp left" -> ManeuverIcon(R.drawable.ic_maneuver_straight, rotation = -135f)
            else -> ManeuverIcon(R.drawable.ic_maneuver_straight)
        }
    }

    /** "80 m", "350 m", "1.2 km", "15 km" */
    fun distance(meters: Double): String = when {
        meters < 100 -> "${(meters / 10).roundToLong() * 10} m"
        meters < 1000 -> "${(meters / 50).roundToLong() * 50} m"
        meters < 10_000 -> String.format(Locale.getDefault(), "%.1f km", meters / 1000)
        else -> "${(meters / 1000).roundToLong()} km"
    }

    /** Distance phrased for text-to-speech, e.g. "300 meters", "1.5 kilometers". */
    fun spokenDistance(meters: Double): String = when {
        meters < 100 -> "${(meters / 10).roundToLong() * 10} meters"
        meters < 1000 -> "${(meters / 50).roundToLong() * 50} meters"
        else -> String.format(Locale.US, "%.1f kilometers", meters / 1000)
    }

    /** "1 min", "12 min", "1 hr 5 min" */
    fun duration(seconds: Double): String {
        val minutes = (seconds / 60).roundToInt().coerceAtLeast(1)
        return if (minutes < 60) "$minutes min" else "${minutes / 60} hr ${minutes % 60} min"
    }
}
