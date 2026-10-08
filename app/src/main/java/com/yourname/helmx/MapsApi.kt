package com.yourname.helmx

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

/**
 * Network calls for the Navigation screen.
 *  - Place search: Photon (photon.komoot.io), an OpenStreetMap geocoder built for search-as-you-type.
 *  - Routing: OSRM public demo server (router.project-osrm.org). It is meant for light use;
 *    a production app should host its own OSRM or use a commercial routing API.
 */
object MapsApi {

    private const val USER_AGENT = "HelmX/1.0 (Android)"
    private const val TIMEOUT_MS = 10_000

    suspend fun searchPlaces(query: String, nearLat: Double?, nearLng: Double?): Result<List<PlaceSuggestion>> =
        withContext(Dispatchers.IO) {
            runCatching {
                val bias = if (nearLat != null && nearLng != null) "&lat=$nearLat&lon=$nearLng" else ""
                val url = "https://photon.komoot.io/api/?q=${URLEncoder.encode(query, "UTF-8")}&limit=6&lang=en$bias"
                PhotonParser.parse(httpGet(url))
            }
        }

    suspend fun fetchRoute(fromLat: Double, fromLng: Double, toLat: Double, toLng: Double): Result<Route> =
        withContext(Dispatchers.IO) {
            runCatching {
                val url = "https://router.project-osrm.org/route/v1/driving/" +
                    "$fromLng,$fromLat;$toLng,$toLat?overview=full&geometries=geojson&steps=true"
                OsrmParser.parse(httpGet(url))
            }
        }

    private fun httpGet(url: String): String {
        val connection = URL(url).openConnection() as HttpURLConnection
        try {
            connection.connectTimeout = TIMEOUT_MS
            connection.readTimeout = TIMEOUT_MS
            connection.setRequestProperty("User-Agent", USER_AGENT)
            val code = connection.responseCode
            // OSRM returns 400 with a JSON body for "NoRoute"; let the parser report it
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            val body = stream?.bufferedReader()?.use { it.readText() }
            if (body.isNullOrEmpty()) throw IOException("HTTP $code")
            return body
        } finally {
            connection.disconnect()
        }
    }
}
