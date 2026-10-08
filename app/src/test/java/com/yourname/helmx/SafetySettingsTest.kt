package com.yourname.helmx

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SafetySettingsTest {

    @Test
    fun contacts_roundTrip() {
        val contacts = listOf(EmergencyContact("Ammi", "03001234567"), EmergencyContact("Rescue", "1122"))
        val decoded = SafetySettings.ContactsCodec.decode(SafetySettings.ContactsCodec.encode(contacts))
        assertEquals(contacts, decoded)
    }

    @Test
    fun contacts_corruptOrEmpty_isEmptyList() {
        assertEquals(emptyList<EmergencyContact>(), SafetySettings.ContactsCodec.decode(null))
        assertEquals(emptyList<EmergencyContact>(), SafetySettings.ContactsCodec.decode("not json"))
    }

    @Test
    fun alertMessage_includesMapsLinkWhenLocationKnown() {
        val msg = EmergencyActions.alertMessage(31.5103226, 74.3447061)
        assertTrue(msg.startsWith("HelmX alert: my helmet detected a possible crash."))
        assertTrue(msg.endsWith("https://www.google.com/maps/search/?api=1&query=31.510323,74.344706"))
    }

    @Test
    fun alertMessage_withoutLocation_hasNoLink() {
        assertFalse(EmergencyActions.alertMessage(null, null).contains("http"))
    }

    @Test
    fun contactPhoneValidation_allowsShortServiceNumbers() {
        assertTrue(Validators.isValidContactPhone("1122"))
        assertTrue(Validators.isValidContactPhone("15"))
        assertTrue(Validators.isValidContactPhone("+92 300 1234567"))
        assertTrue(Validators.isValidContactPhone("(042) 111-222-333"))
        assertFalse(Validators.isValidContactPhone("1"))
        assertFalse(Validators.isValidContactPhone("call me"))
        assertFalse(Validators.isValidContactPhone(""))
    }

    @Test
    fun sensitivity_fromIndex() {
        assertEquals(DrowsinessSensitivity.LOW, DrowsinessSensitivity.fromIndex(0))
        assertEquals(DrowsinessSensitivity.HIGH, DrowsinessSensitivity.fromIndex(2))
        assertEquals(DrowsinessSensitivity.MEDIUM, DrowsinessSensitivity.fromIndex(99)) // unknown -> default
        assertEquals(0L, DrowsinessSensitivity.HIGH.delayMs)
    }
}
