package com.yourname.helmx

import org.json.JSONObject

data class LatLng(val lat: Double, val lng: Double)

/** One OSRM route step; the maneuver happens at ([lat], [lng]) at the start of the step. */
data class RouteStep(
    val type: String,           // e.g. "depart", "turn", "roundabout", "arrive"
    val modifier: String?,      // e.g. "left", "slight right", "uturn"
    val name: String,           // street name, may be empty
    val lat: Double,
    val lng: Double,
    val distanceM: Double,
    val durationS: Double,
    val exit: Int? = null       // roundabout exit number
)

data class Route(
    val points: List<LatLng>,
    val distanceM: Double,
    val durationS: Double,
    val steps: List<RouteStep>
)

data class PlaceSuggestion(
    val name: String,
    val address: String,
    val lat: Double,
    val lng: Double,
    val isRecent: Boolean = false
)

/** Parses responses from the OSRM route service (geometries=geojson, steps=true). */
object OsrmParser {
    fun parse(json: String): Route {
        val root = JSONObject(json)
        val code = root.optString("code")
        require(code == "Ok") { if (code == "NoRoute") "No route found to this destination" else "Routing failed ($code)" }
        val routeJson = root.getJSONArray("routes").getJSONObject(0)

        val coords = routeJson.getJSONObject("geometry").getJSONArray("coordinates")
        val points = (0 until coords.length()).map { i ->
            val c = coords.getJSONArray(i)
            LatLng(lat = c.getDouble(1), lng = c.getDouble(0)) // GeoJSON is [lng, lat]
        }

        val steps = mutableListOf<RouteStep>()
        val legs = routeJson.getJSONArray("legs")
        for (l in 0 until legs.length()) {
            val stepsJson = legs.getJSONObject(l).getJSONArray("steps")
            for (s in 0 until stepsJson.length()) {
                val step = stepsJson.getJSONObject(s)
                val maneuver = step.getJSONObject("maneuver")
                val location = maneuver.getJSONArray("location")
                steps += RouteStep(
                    type = maneuver.optString("type"),
                    modifier = maneuver.optString("modifier").ifEmpty { null },
                    name = step.optString("name"),
                    lat = location.getDouble(1),
                    lng = location.getDouble(0),
                    distanceM = step.optDouble("distance", 0.0),
                    durationS = step.optDouble("duration", 0.0),
                    exit = if (maneuver.has("exit")) maneuver.optInt("exit") else null
                )
            }
        }

        return Route(
            points = points,
            distanceM = routeJson.optDouble("distance", 0.0),
            durationS = routeJson.optDouble("duration", 0.0),
            steps = steps
        )
    }
}

/** Parses Photon geocoder responses (GeoJSON FeatureCollection) into suggestions. */
object PhotonParser {
    fun parse(json: String): List<PlaceSuggestion> {
        val features = JSONObject(json).optJSONArray("features") ?: return emptyList()
        val results = LinkedHashMap<String, PlaceSuggestion>() // de-duplicate, keep order
        for (i in 0 until features.length()) {
            val feature = features.getJSONObject(i)
            val props = feature.optJSONObject("properties") ?: continue
            val coords = feature.optJSONObject("geometry")?.optJSONArray("coordinates") ?: continue

            fun prop(key: String) = props.optString(key).takeIf { it.isNotBlank() }
            val street = listOfNotNull(prop("street"), prop("housenumber")).joinToString(" ").ifBlank { null }
            val name = prop("name") ?: street ?: prop("city") ?: continue
            val address = listOfNotNull(
                street?.takeIf { it != name },
                prop("district"),
                prop("city"),
                prop("state"),
                prop("country")
            ).filter { it != name }.distinct().joinToString(", ")

            val suggestion = PlaceSuggestion(name, address, lat = coords.getDouble(1), lng = coords.getDouble(0))
            results.putIfAbsent("$name|$address", suggestion)
        }
        return results.values.toList()
    }
}
