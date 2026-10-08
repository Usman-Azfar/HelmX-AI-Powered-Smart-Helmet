package com.yourname.helmx

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ValidatorsTest {

    @Test
    fun validPhoneNumbers() {
        assertTrue(Validators.isValidPhone("03214855000"))
        assertTrue(Validators.isValidPhone("+923214855000"))
        assertTrue(Validators.isValidPhone("0321-4855000"))
        assertTrue(Validators.isValidPhone("0321 485 5000"))
    }

    @Test
    fun invalidPhoneNumbers() {
        assertFalse(Validators.isValidPhone(""))
        assertFalse(Validators.isValidPhone("12345"))
        assertFalse(Validators.isValidPhone("0321abc5000"))
        assertFalse(Validators.isValidPhone("+92+3214855000"))
        assertFalse(Validators.isValidPhone("1234567890123456"))
    }

    @Test
    fun normalizePhone_stripsSpacesAndDashes() {
        assertEquals("03214855000", Validators.normalizePhone("0321-485 5000"))
    }
}
