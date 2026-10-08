package com.yourname.helmx

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.abs

/** Recently used destinations, stored on the device so they also work offline. */
class RecentPlaces(context: Context) {

    private val prefs = context.getSharedPreferences("HelmXRecentPlaces", Context.MODE_PRIVATE)

    fun all(): List<PlaceSuggestion> = Codec.decode(prefs.getString(KEY, null))

    fun add(place: PlaceSuggestion) {
        prefs.edit().putString(KEY, Codec.encode(Codec.withAdded(all(), place))).apply()
    }

    fun clear() {
        prefs.edit().remove(KEY).apply()
    }

    /** Recents whose name or address contains [query] (all of them for a blank query). */
    fun matching(query: String): List<PlaceSuggestion> = Codec.filter(all(), query)

    companion object {
        private const val KEY = "recents"
    }

    /** Pure helpers, unit tested. */
    object Codec {
        const val MAX = 10

        fun encode(places: List<PlaceSuggestion>): String = JSONArray().apply {
            places.forEach { p ->
                put(JSONObject().put("name", p.name).put("address", p.address).put("lat", p.lat).put("lng", p.lng))
            }
        }.toString()

        fun decode(json: String?): List<PlaceSuggestion> {
            if (json.isNullOrBlank()) return emptyList()
            return try {
                val array = JSONArray(json)
                (0 until array.length()).map { i ->
                    val o = array.getJSONObject(i)
                    PlaceSuggestion(o.getString("name"), o.optString("address"), o.getDouble("lat"), o.getDouble("lng"), isRecent = true)
                }
            } catch (e: Exception) {
                emptyList() // corrupt data: start fresh rather than crash
            }
        }

        /** Newest first; the same place (same name, within ~50 m) is moved to the top, not duplicated. */
        fun withAdded(current: List<PlaceSuggestion>, place: PlaceSuggestion): List<PlaceSuggestion> {
            val others = current.filterNot {
                it.name.equals(place.name, ignoreCase = true) &&
                    abs(it.lat - place.lat) < 0.0005 && abs(it.lng - place.lng) < 0.0005
            }
            return (listOf(place) + others).take(MAX)
        }

        fun filter(places: List<PlaceSuggestion>, query: String): List<PlaceSuggestion> {
            val q = query.trim()
            if (q.isEmpty()) return places
            return places.filter { it.name.contains(q, ignoreCase = true) || it.address.contains(q, ignoreCase = true) }
        }
    }
}
