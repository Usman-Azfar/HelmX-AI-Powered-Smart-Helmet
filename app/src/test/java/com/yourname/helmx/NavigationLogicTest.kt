package com.yourname.helmx

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NavigationLogicTest {

    // ---- OSRM / Photon parsing ----

    private val osrmJson = """
        {"code":"Ok","routes":[{"distance":1000.0,"duration":120.0,
          "geometry":{"type":"LineString","coordinates":[[74.0,31.0],[74.0,31.0045],[74.0,31.009]]},
          "legs":[{"steps":[
            {"name":"Main Boulevard","distance":500.0,"duration":60.0,"maneuver":{"type":"depart","location":[74.0,31.0]}},
            {"name":"Noor Jahan Road","distance":500.0,"duration":60.0,"maneuver":{"type":"turn","modifier":"left","location":[74.0,31.0045]}},
            {"name":"","distance":0.0,"duration":0.0,"maneuver":{"type":"arrive","modifier":"right","location":[74.0,31.009]}}
          ]}]}]}
    """.trimIndent()

    @Test
    fun osrm_parsesGeometryStepsAndTotals() {
        val route = OsrmParser.parse(osrmJson)

        assertEquals(3, route.points.size)
        assertEquals(31.0045, route.points[1].lat, 1e-9) // GeoJSON [lng, lat] swapped correctly
        assertEquals(74.0, route.points[1].lng, 1e-9)
        assertEquals(1000.0, route.distanceM, 0.0)
        assertEquals(120.0, route.durationS, 0.0)
        assertEquals(3, route.steps.size)
        assertEquals("left", route.steps[1].modifier)
        assertEquals(null, route.steps[0].modifier)
    }

    @Test(expected = IllegalArgumentException::class)
    fun osrm_noRoute_throws() {
        OsrmParser.parse("""{"code":"NoRoute","message":"Impossible route"}""")
    }

    @Test
    fun photon_buildsNameAndAddress_andDeduplicates() {
        val json = """
            {"type":"FeatureCollection","features":[
              {"type":"Feature","geometry":{"type":"Point","coordinates":[74.3447,31.5103]},
               "properties":{"name":"Liberty Market","street":"Noor Jahan Road","district":"Gulberg","city":"Lahore","country":"Pakistan"}},
              {"type":"Feature","geometry":{"type":"Point","coordinates":[74.3447,31.5103]},
               "properties":{"name":"Liberty Market","street":"Noor Jahan Road","district":"Gulberg","city":"Lahore","country":"Pakistan"}},
              {"type":"Feature","geometry":{"type":"Point","coordinates":[74.35,31.52]},
               "properties":{"street":"Main Boulevard","housenumber":"12","city":"Lahore"}},
              {"type":"Feature","geometry":{"type":"Point","coordinates":[1,2]},"properties":{}}
            ]}
        """.trimIndent()

        val places = PhotonParser.parse(json)

        assertEquals(2, places.size)
        assertEquals("Liberty Market", places[0].name)
        assertEquals("Noor Jahan Road, Gulberg, Lahore, Pakistan", places[0].address)
        assertEquals(31.5103, places[0].lat, 1e-9)
        assertEquals("Main Boulevard 12", places[1].name)
        assertEquals("Lahore", places[1].address)
    }

    // ---- Instructions and formatting ----

    private fun step(type: String, modifier: String? = null, name: String = "", exit: Int? = null) =
        RouteStep(type, modifier, name, 0.0, 0.0, 0.0, 0.0, exit)

    @Test
    fun instructions() {
        assertEquals("Turn left onto Noor Jahan Road", NavText.instruction(step("turn", "left", "Noor Jahan Road")))
        assertEquals("Keep slightly right", NavText.instruction(step("turn", "slight right")))
        assertEquals("Make a U-turn", NavText.instruction(step("turn", "uturn")))
        assertEquals("Head along Main Boulevard", NavText.instruction(step("depart", "left", "Main Boulevard")))
        assertEquals("Your destination is on the right", NavText.instruction(step("arrive", "right")))
        assertEquals("At the roundabout, take the 2nd exit onto Canal Road",
            NavText.instruction(step("roundabout", "right", "Canal Road", exit = 2)))
        assertEquals("Keep left at the fork", NavText.instruction(step("fork", "slight left")))
        assertEquals("Continue onto Ferozepur Road", NavText.instruction(step("new name", "straight", "Ferozepur Road")))
    }

    @Test
    fun icons() {
        assertEquals(ManeuverIcon(R.drawable.ic_maneuver_turn_right, mirrored = true), NavText.icon(step("turn", "left")))
        assertEquals(ManeuverIcon(R.drawable.ic_maneuver_straight, rotation = 45f), NavText.icon(step("turn", "slight right")))
        assertEquals(ManeuverIcon(R.drawable.ic_place_pin), NavText.icon(step("arrive", "left")))
    }

    @Test
    fun formatting() {
        assertEquals("80 m", NavText.distance(83.0))
        assertEquals("350 m", NavText.distance(361.0))
        assertEquals("1.5 km", NavText.distance(1520.0))
        assertEquals("15 km", NavText.distance(15_200.0))
        assertEquals("300 meters", NavText.spokenDistance(310.0))
        assertEquals("2.0 kilometers", NavText.spokenDistance(2000.0))
        assertEquals("1 min", NavText.duration(20.0))
        assertEquals("5 min", NavText.duration(275.0))
        assertEquals("1 hr 5 min", NavText.duration(3900.0))
    }

    // ---- Guidance ----

    @Test
    fun guide_tracksNextManeuverAndRemaining() {
        val guide = NavigationGuide(OsrmParser.parse(osrmJson)) // ~1 km due north, turn halfway

        val atStart = guide.update(31.0, 74.0)
        assertEquals(1, atStart.nextStepIndex)
        assertEquals(500.0, atStart.distanceToNextM, 5.0)
        assertEquals(1000.0, atStart.remainingDistanceM, 5.0)
        assertEquals(120.0, atStart.remainingDurationS, 1.0)
        assertFalse(atStart.isOffRoute)
        assertFalse(atStart.hasArrived)

        val pastTurn = guide.update(31.006, 74.0) // ~667 m along
        assertEquals(2, pastTurn.nextStepIndex)
        assertEquals(333.0, pastTurn.remainingDistanceM, 5.0)
        assertEquals(pastTurn.remainingDistanceM, pastTurn.distanceToNextM, 1.0)
        assertEquals(0.667, pastTurn.fractionTravelled, 0.01)
        assertEquals(0.0, atStart.fractionTravelled, 0.001)
    }

    @Test
    fun guide_offRoute_needsConsecutiveFixes() {
        val guide = NavigationGuide(OsrmParser.parse(osrmJson))
        val farEast = 74.0 + 100.0 / (111_320.0 * Math.cos(Math.toRadians(31.003))) // ~100 m east

        assertFalse(guide.update(31.003, farEast).isOffRoute) // one bad fix is tolerated
        assertTrue(guide.update(31.003, farEast).isOffRoute)
        assertFalse(guide.update(31.003, 74.0).isOffRoute)    // back on the line
    }

    @Test
    fun guide_detectsArrival() {
        val guide = NavigationGuide(OsrmParser.parse(osrmJson))
        assertFalse(guide.update(31.008, 74.0).hasArrived)   // ~111 m to go
        assertTrue(guide.update(31.0089, 74.0).hasArrived)   // ~11 m to go
    }

    @Test
    fun guide_routePassingNearDestinationEarly_isNotArrival() {
        // Goes north past the destination (10 m to its west), loops round, and ends at it
        val json = """
            {"code":"Ok","routes":[{"distance":800.0,"duration":100.0,
              "geometry":{"type":"LineString","coordinates":[[74.0,31.0],[74.0,31.002],[74.003,31.002],[74.003,31.0],[74.0001,31.001]]},
              "legs":[{"steps":[
                {"name":"","distance":800.0,"duration":100.0,"maneuver":{"type":"depart","location":[74.0,31.0]}},
                {"name":"","distance":0.0,"duration":0.0,"maneuver":{"type":"arrive","location":[74.0001,31.001]}}
              ]}]}]}
        """.trimIndent()
        val guide = NavigationGuide(OsrmParser.parse(json))

        val passing = guide.update(31.001, 74.0) // ~10 m from the destination, but early in the route
        assertFalse(passing.hasArrived)
        assertTrue(passing.remainingDistanceM > 500)
    }

    @Test
    fun bearing() {
        assertEquals(0.0, NavigationGuide.bearingDegrees(31.0, 74.0, 31.01, 74.0), 0.5)
        assertEquals(90.0, NavigationGuide.bearingDegrees(31.0, 74.0, 31.0, 74.01), 0.5)
        assertEquals(180.0, NavigationGuide.bearingDegrees(31.01, 74.0, 31.0, 74.0), 0.5)
    }
}
