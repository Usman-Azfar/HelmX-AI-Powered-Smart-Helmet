package com.yourname.helmx

import android.content.Context
import android.content.Intent
import android.net.Uri
import java.util.Locale

/**
 * Builds the "call" and "text my location" intents used after a crash.
 * They open the dialer / SMS app pre-filled, so no CALL_PHONE or SEND_SMS permission is needed;
 * the rider (or a passer-by) confirms with one tap.
 */
object EmergencyActions {

    fun dialIntent(phone: String): Intent =
        Intent(Intent.ACTION_DIAL, Uri.parse("tel:${Uri.encode(phone)}"))

    fun smsIntent(contacts: List<EmergencyContact>, lat: Double?, lng: Double?): Intent {
        val recipients = contacts.joinToString(";") { it.phone }
        return Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:$recipients"))
            .putExtra("sms_body", alertMessage(lat, lng))
    }

    /** Message text with a Google Maps link to the rider's position (when known). */
    fun alertMessage(lat: Double?, lng: Double?): String {
        val base = "HelmX alert: my helmet detected a possible crash. Please check on me."
        if (lat == null || lng == null) return base
        val link = String.format(Locale.US, "https://www.google.com/maps/search/?api=1&query=%.6f,%.6f", lat, lng)
        return "$base My location: $link"
    }

    /** Starts [intent]; returns false if no app can handle it (e.g. a tablet without telephony). */
    fun launch(context: Context, intent: Intent): Boolean = try {
        context.startActivity(intent)
        true
    } catch (e: android.content.ActivityNotFoundException) {
        false
    }
}
