package com.yourname.helmx

import android.content.Context
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.SetOptions
import kotlinx.coroutines.tasks.await
import org.json.JSONArray
import org.json.JSONObject

data class EmergencyContact(val name: String, val phone: String)

/** How quickly a drowsiness report from the helmet turns into an alarm. */
enum class DrowsinessSensitivity(val label: String, val delayMs: Long) {
    LOW("Low", 3000),
    MEDIUM("Medium", 1500),
    HIGH("High", 0);

    companion object {
        fun fromIndex(index: Int) = entries.getOrElse(index) { MEDIUM }
    }
}

/**
 * Safety and voice preferences.
 * Toggles live on the device; emergency contacts belong to the account (Firestore
 * users/{uid}.emergencyContacts) and are cached here so alerts work offline.
 */
object SafetySettings {

    private const val PREFS = "HelmXSafety"
    private const val KEY_CRASH = "crash_detection"
    private const val KEY_CONTACTS = "emergency_contacts"
    private const val KEY_DROWSY = "drowsiness_detection"
    private const val KEY_SENSITIVITY = "drowsiness_sensitivity"
    private const val KEY_SOUND = "sound_alarms"
    private const val KEY_VOICE = "voice_guidance"
    private const val KEY_VOICE_VOLUME = "voice_volume"
    private const val KEY_AUTO_RESPONSE = "auto_emergency_response"
    const val MAX_CONTACTS = 2
    const val AUTO_RESPONSE_SECONDS = 30

    /** Permissions needed to text and call without the rider tapping anything. */
    val AUTO_RESPONSE_PERMISSIONS = arrayOf(
        android.Manifest.permission.SEND_SMS,
        android.Manifest.permission.CALL_PHONE
    )

    private fun prefs(context: Context) = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun isCrashDetectionEnabled(c: Context) = prefs(c).getBoolean(KEY_CRASH, true)
    fun setCrashDetectionEnabled(c: Context, v: Boolean) = prefs(c).edit().putBoolean(KEY_CRASH, v).apply()

    fun isDrowsinessEnabled(c: Context) = prefs(c).getBoolean(KEY_DROWSY, true)
    fun setDrowsinessEnabled(c: Context, v: Boolean) = prefs(c).edit().putBoolean(KEY_DROWSY, v).apply()

    fun drowsinessSensitivity(c: Context) = DrowsinessSensitivity.fromIndex(prefs(c).getInt(KEY_SENSITIVITY, 1))
    fun setDrowsinessSensitivity(c: Context, v: DrowsinessSensitivity) = prefs(c).edit().putInt(KEY_SENSITIVITY, v.ordinal).apply()

    fun isSoundAlarmsEnabled(c: Context) = prefs(c).getBoolean(KEY_SOUND, true)
    fun setSoundAlarmsEnabled(c: Context, v: Boolean) = prefs(c).edit().putBoolean(KEY_SOUND, v).apply()

    fun isVoiceGuidanceEnabled(c: Context) = prefs(c).getBoolean(KEY_VOICE, true)
    fun setVoiceGuidanceEnabled(c: Context, v: Boolean) = prefs(c).edit().putBoolean(KEY_VOICE, v).apply()

    /** 0..100 */
    fun voiceVolume(c: Context) = prefs(c).getInt(KEY_VOICE_VOLUME, 100)
    fun setVoiceVolume(c: Context, v: Int) = prefs(c).edit().putInt(KEY_VOICE_VOLUME, v.coerceIn(0, 100)).apply()

    /**
     * "Always allow": after a crash, if the rider doesn't respond within [AUTO_RESPONSE_SECONDS],
     * text the location to the contacts and call the primary contact automatically.
     */
    fun isAutoResponseEnabled(c: Context) = prefs(c).getBoolean(KEY_AUTO_RESPONSE, false)
    fun setAutoResponseEnabled(c: Context, v: Boolean) = prefs(c).edit().putBoolean(KEY_AUTO_RESPONSE, v).apply()

    fun hasAutoResponsePermissions(c: Context) = AUTO_RESPONSE_PERMISSIONS.all {
        androidx.core.content.ContextCompat.checkSelfPermission(c, it) == android.content.pm.PackageManager.PERMISSION_GRANTED
    }

    /** True only when the rider opted in, granted both permissions and has a contact to reach. */
    fun canAutoRespond(c: Context) =
        isAutoResponseEnabled(c) && hasAutoResponsePermissions(c) && cachedContacts(c).isNotEmpty()

    // ---- Emergency contacts ----

    fun cachedContacts(c: Context): List<EmergencyContact> = ContactsCodec.decode(prefs(c).getString(KEY_CONTACTS, null))

    private fun cacheContacts(c: Context, contacts: List<EmergencyContact>) =
        prefs(c).edit().putString(KEY_CONTACTS, ContactsCodec.encode(contacts)).apply()

    /** Loads the signed-in user's contacts (Firestore serves its cache when offline). */
    suspend fun loadContacts(c: Context): List<EmergencyContact> {
        val uid = FirebaseAuth.getInstance().currentUser?.uid ?: return cachedContacts(c)
        return try {
            val doc = FirebaseFirestore.getInstance().collection("users").document(uid).get().await()
            @Suppress("UNCHECKED_CAST")
            val raw = doc.get("emergencyContacts") as? List<Map<String, Any?>>
            val contacts = raw?.mapNotNull { m ->
                val name = m["name"] as? String ?: return@mapNotNull null
                val phone = m["phone"] as? String ?: return@mapNotNull null
                EmergencyContact(name, phone)
            } ?: emptyList()
            cacheContacts(c, contacts)
            contacts
        } catch (e: Exception) {
            cachedContacts(c)
        }
    }

    suspend fun saveContacts(c: Context, contacts: List<EmergencyContact>) {
        val clean = contacts.filter { it.phone.isNotBlank() }.take(MAX_CONTACTS)
        cacheContacts(c, clean)
        val uid = FirebaseAuth.getInstance().currentUser?.uid ?: return
        FirebaseFirestore.getInstance().collection("users").document(uid)
            .set(mapOf("emergencyContacts" to clean.map { mapOf("name" to it.name, "phone" to it.phone) }), SetOptions.merge())
            .await()
    }

    /** Called on logout / account deletion so the next user doesn't inherit contacts. */
    fun clearAccountData(c: Context) = prefs(c).edit().remove(KEY_CONTACTS).apply()

    /** Pure helpers, unit tested. */
    object ContactsCodec {
        fun encode(contacts: List<EmergencyContact>): String = JSONArray().apply {
            contacts.forEach { put(JSONObject().put("name", it.name).put("phone", it.phone)) }
        }.toString()

        fun decode(json: String?): List<EmergencyContact> {
            if (json.isNullOrBlank()) return emptyList()
            return try {
                val array = JSONArray(json)
                (0 until array.length()).map { i ->
                    val o = array.getJSONObject(i)
                    EmergencyContact(o.optString("name"), o.getString("phone"))
                }
            } catch (e: Exception) {
                emptyList()
            }
        }
    }
}
