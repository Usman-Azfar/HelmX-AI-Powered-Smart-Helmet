package com.yourname.helmx

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class HelmetDataParserTest {

    private val initial = HelmetData(batteryLevel = 80, speed = 12f)

    @Test
    fun json_updatesEnvironmentFields_andKeepsRideFields() {
        val raw = """{"temperature":31.5,"humidity":62,"air_quality":"Good","destination":"Liberty Market"}"""

        val result = HelmetDataParser.parse(raw, initial)

        assertNotNull(result)
        result!!
        assertEquals(31.5f, result.temperature, 0.001f)
        assertEquals(62f, result.humidity, 0.001f)
        assertEquals("Good", result.airQuality)
        assertEquals("Liberty Market", result.destination)
        assertEquals(ConnectionStatus.CONNECTED, result.connectionStatus)
        // Fields not present in the JSON packet are preserved
        assertEquals(80, result.batteryLevel)
        assertEquals(12f, result.speed, 0.001f)
    }

    @Test
    fun json_missingFields_useDefaults() {
        val result = HelmetDataParser.parse("{}", initial)!!

        assertEquals(0f, result.temperature, 0.001f)
        assertEquals("Unknown", result.airQuality)
        assertEquals("", result.destination)
    }

    @Test
    fun json_withNullAndControlCharacters_isCleanedBeforeParsing() {
        val raw = "\u0000{\"temperature\":20}\n\u0000"

        val result = HelmetDataParser.parse(raw, initial)

        assertNotNull(result)
        assertEquals(20f, result!!.temperature, 0.001f)
    }

    @Test
    fun malformedJson_returnsNull() {
        assertNull(HelmetDataParser.parse("{temperature:}", initial))
    }

    @Test
    fun csv_fiveFields_updatesRideAndSafetyFields() {
        val result = HelmetDataParser.parse("95, 42.5, 1, 0, 3.2", HelmetData())!!

        assertEquals(95, result.batteryLevel)
        assertEquals(42.5f, result.speed, 0.001f)
        assertTrue(result.isDrowsy)
        assertFalse(result.isCrashDetected)
        assertEquals(3.2f, result.distance, 0.001f)
        assertEquals(ConnectionStatus.CONNECTED, result.connectionStatus)
    }

    @Test
    fun csv_acceptsTrueFlags_andDefaultsInvalidNumbers() {
        val result = HelmetDataParser.parse("abc,xyz,true,true,1", HelmetData())!!

        assertEquals(0, result.batteryLevel)
        assertEquals(0f, result.speed, 0.001f)
        assertTrue(result.isDrowsy)
        assertTrue(result.isCrashDetected)
    }

    @Test
    fun csv_twoFields_legacyTemperatureHumidity() {
        val result = HelmetDataParser.parse("T:-4.5C,H:55%", initial)!!

        assertEquals(-4.5f, result.temperature, 0.001f)
        assertEquals(55f, result.humidity, 0.001f)
    }

    @Test
    fun unrecognisedPayload_returnsNull() {
        assertNull(HelmetDataParser.parse("hello", initial))
        assertNull(HelmetDataParser.parse("1,2,3", initial))
        assertNull(HelmetDataParser.parse("abc,def", initial))
    }
}
