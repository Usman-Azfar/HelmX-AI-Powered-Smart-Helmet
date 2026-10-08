package com.yourname.helmx

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class OfflineTest {

    // ---- Offline map server paths ----

    @Test
    fun assetPaths() {
        assertEquals("map.html", OfflineMapServer.assetPathFor("/map.html"))
        assertEquals("offline/tiles/14/11768/6703.pbf", OfflineMapServer.assetPathFor("/tiles/14/11768/6703.pbf"))
        assertEquals("offline/fonts/Noto Sans Regular/0-255.pbf", OfflineMapServer.assetPathFor("/fonts/Noto Sans Regular/0-255.pbf"))
        assertEquals("offline/styles/liberty.json", OfflineMapServer.assetPathFor("/styles/liberty.json"))
    }

    @Test
    fun assetPaths_rejectTraversalAndEmpty() {
        assertNull(OfflineMapServer.assetPathFor("/../../shared_prefs/x.xml"))
        assertNull(OfflineMapServer.assetPathFor("/tiles/..\\x"))
        assertNull(OfflineMapServer.assetPathFor("/"))
        assertNull(OfflineMapServer.assetPathFor(null))
    }

    @Test
    fun mimeTypes() {
        assertEquals("application/x-protobuf", OfflineMapServer.mimeTypeFor("offline/tiles/1/2/3.pbf"))
        assertEquals("application/javascript", OfflineMapServer.mimeTypeFor("offline/maplibre-gl.js"))
        assertEquals("application/json", OfflineMapServer.mimeTypeFor("offline/sprites/ofm@2x.json"))
        assertEquals("image/png", OfflineMapServer.mimeTypeFor("offline/sprites/ofm.png"))
        assertEquals("text/html", OfflineMapServer.mimeTypeFor("map.html"))
    }

    // ---- Recent places ----

    private val liberty = PlaceSuggestion("Liberty Market", "Gulberg, Lahore", 31.5103, 74.3447)
    private val fortress = PlaceSuggestion("Fortress Stadium", "Lahore Cantt", 31.5279, 74.3612)

    @Test
    fun recents_roundTrip_markedAsRecent() {
        val decoded = RecentPlaces.Codec.decode(RecentPlaces.Codec.encode(listOf(liberty, fortress)))
        assertEquals(listOf("Liberty Market", "Fortress Stadium"), decoded.map { it.name })
        assertEquals(31.5103, decoded[0].lat, 1e-9)
        assertEquals("Gulberg, Lahore", decoded[0].address)
        assertTrue(decoded.all { it.isRecent })
    }

    @Test
    fun recents_newestFirst_noDuplicates_capped() {
        var list = RecentPlaces.Codec.withAdded(emptyList(), liberty)
        list = RecentPlaces.Codec.withAdded(list, fortress)
        list = RecentPlaces.Codec.withAdded(list, liberty.copy(lat = 31.51032)) // same place again
        assertEquals(listOf("Liberty Market", "Fortress Stadium"), list.map { it.name })

        repeat(15) { i -> list = RecentPlaces.Codec.withAdded(list, PlaceSuggestion("Place $i", "", 31.0 + i, 74.0)) }
        assertEquals(RecentPlaces.Codec.MAX, list.size)
        assertEquals("Place 14", list.first().name)
    }

    @Test
    fun recents_filterByNameOrAddress() {
        val list = listOf(liberty, fortress)
        assertEquals(listOf(liberty), RecentPlaces.Codec.filter(list, "liber"))
        assertEquals(listOf(fortress), RecentPlaces.Codec.filter(list, "cantt"))
        assertEquals(list, RecentPlaces.Codec.filter(list, "  "))
    }

    @Test
    fun recents_corruptData_isIgnored() {
        assertEquals(emptyList<PlaceSuggestion>(), RecentPlaces.Codec.decode("{not json"))
        assertEquals(emptyList<PlaceSuggestion>(), RecentPlaces.Codec.decode(null))
    }
}
