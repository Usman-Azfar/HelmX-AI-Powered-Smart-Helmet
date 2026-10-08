package com.yourname.helmx

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

/**
 * Invisible screen behind the crash-alert buttons. Going through an activity (instead of
 * opening the dialer/SMS app directly) lets every button first stop the auto-response
 * countdown, and lets "Always allow" show Android's permission prompt.
 */
class CrashActionActivity : AppCompatActivity() {

    companion object {
        const val ACTION_OK = "ok"
        const val ACTION_CALL = "call"
        const val ACTION_TEXT = "text"
        const val ACTION_ALLOW = "allow"
        private const val EXTRA_ACTION = "action"

        fun intent(context: Context, action: String) =
            Intent(context, CrashActionActivity::class.java)
                .putExtra(EXTRA_ACTION, action)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_NO_ANIMATION)

        fun pendingIntent(context: Context, action: String): PendingIntent = PendingIntent.getActivity(
            context, action.hashCode(), intent(context, action),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    private val permissionRequest = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
        if (result.values.all { it }) {
            SafetySettings.setAutoResponseEnabled(this, true)
            Toast.makeText(
                this,
                "Always allowed. After a crash, HelmX will text and call your contact if you don't respond in ${SafetySettings.AUTO_RESPONSE_SECONDS} s.",
                Toast.LENGTH_LONG
            ).show()
        } else {
            Toast.makeText(this, "Not enabled: SMS and phone permission are needed", Toast.LENGTH_LONG).show()
        }
        finish()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val contacts = SafetySettings.cachedContacts(this)
        when (intent.getStringExtra(EXTRA_ACTION)) {
            ACTION_OK -> {
                SafetyMonitor.onRiderResponded(this, dismiss = true)
                Toast.makeText(this, "Glad you're OK. Alert cancelled.", Toast.LENGTH_SHORT).show()
                finish()
            }
            ACTION_CALL -> {
                SafetyMonitor.onRiderResponded(this, dismiss = false)
                val number = contacts.firstOrNull()?.phone ?: SafetyMonitor.FALLBACK_EMERGENCY_NUMBER
                if (!EmergencyActions.launch(this, EmergencyActions.dialIntent(number))) {
                    Toast.makeText(this, "No phone app available", Toast.LENGTH_SHORT).show()
                }
                finish()
            }
            ACTION_TEXT -> {
                SafetyMonitor.onRiderResponded(this, dismiss = false)
                val location = SafetyMonitor.lastCrashLocation
                if (!EmergencyActions.launch(this, EmergencyActions.smsIntent(contacts, location?.first, location?.second))) {
                    Toast.makeText(this, "No messaging app available", Toast.LENGTH_SHORT).show()
                }
                finish()
            }
            ACTION_ALLOW -> {
                if (SafetySettings.hasAutoResponsePermissions(this)) {
                    SafetySettings.setAutoResponseEnabled(this, true)
                    Toast.makeText(this, "Always allowed", Toast.LENGTH_SHORT).show()
                    finish()
                } else {
                    permissionRequest.launch(SafetySettings.AUTO_RESPONSE_PERMISSIONS)
                }
            }
            else -> finish()
        }
    }
}
