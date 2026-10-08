package com.yourname.helmx

object Validators {

    const val MIN_PASSWORD_LENGTH = 6 // Firebase Auth minimum

    // Optional leading "+", then 10-15 digits (covers 03XXXXXXXXX and +923XXXXXXXXX)
    private val PHONE_REGEX = Regex("^\\+?\\d{10,15}$")

    // Emergency contacts may also be short service numbers such as 1122 or 15
    private val CONTACT_PHONE_REGEX = Regex("^\\+?\\d{2,15}$")

    const val PHONE_ERROR = "Enter a valid phone number (10-15 digits)"

    /** Strips spaces, dashes and brackets so "0321-1234567" or "(042) 111 222 333" is accepted. */
    fun normalizePhone(phone: String): String = phone.replace(Regex("[\\s()-]"), "")

    fun isValidPhone(phone: String): Boolean = PHONE_REGEX.matches(normalizePhone(phone))

    fun isValidContactPhone(phone: String): Boolean = CONTACT_PHONE_REGEX.matches(normalizePhone(phone))
}
