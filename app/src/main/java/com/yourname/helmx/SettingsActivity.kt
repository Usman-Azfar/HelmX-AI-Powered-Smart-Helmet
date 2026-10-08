package com.yourname.helmx

import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.firebase.auth.FirebaseAuth
import com.yourname.helmx.databinding.ActivitySettingsBinding
import com.yourname.helmx.databinding.ItemSettingsRowBinding
import kotlinx.coroutines.launch
import org.json.JSONObject

class SettingsActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySettingsBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Theme itself is applied at startup by HelmXApplication
        binding.switchDarkMode.isChecked = AppSettings.isDarkMode(this)
        binding.switchDarkMode.setOnCheckedChangeListener { _, isChecked ->
            AppSettings.setDarkMode(this, isChecked)
        }
        binding.cardDarkMode.setOnClickListener { binding.switchDarkMode.toggle() }

        setupRows()
        setupBottomNavigation()

        binding.btnLogoutSettings.setOnClickListener { confirmLogout() }
    }

    override fun onResume() {
        super.onResume()
        binding.bottomNavigation.selectedItemId = R.id.nav_settings
        refreshSummaries() // values may have changed in a sub-screen
    }

    private fun setupRows() {
        row(binding.rowCrash, R.drawable.ic_shield, "Crash alerts & contacts") {
            startActivity(Intent(this, CrashAlertsActivity::class.java))
        }
        row(binding.rowDrowsiness, R.drawable.ic_notification_bell, "Drowsiness alerts") {
            startActivity(Intent(this, DrowsinessActivity::class.java))
        }
        row(binding.rowVoice, R.drawable.ic_mic, "Voice guidance") {
            startActivity(Intent(this, VoiceEntertainmentActivity::class.java))
        }
        row(binding.rowOfflineMap, R.drawable.ic_navigation, "Offline map") { showOfflineMapInfo() }
        row(binding.rowAccount, R.drawable.ic_account_circle, "Account") {
            startActivity(Intent(this, AccountActivity::class.java))
        }
        row(binding.rowPrivacy, R.drawable.ic_lock, "Privacy & permissions") {
            startActivity(Intent(this, PrivacyPermissionsActivity::class.java))
        }
        row(binding.rowAbout, R.drawable.ic_info, "About HelmX") {
            startActivity(Intent(this, AboutActivity::class.java))
        }
    }

    private fun row(row: ItemSettingsRowBinding, icon: Int, title: String, onClick: () -> Unit) {
        row.ivRowIcon.setImageResource(icon)
        row.tvRowTitle.text = title
        row.root.setOnClickListener { onClick() }
    }

    private fun refreshSummaries() {
        val contacts = SafetySettings.cachedContacts(this)
        refreshCrashSummaryOnly()
        // Contacts live in the account; refresh the cache in the background
        lifecycleScope.launch {
            val fresh = SafetySettings.loadContacts(this@SettingsActivity)
            if (fresh != contacts) refreshCrashSummaryOnly()
        }

        binding.rowDrowsiness.tvRowSubtitle.text =
            if (!SafetySettings.isDrowsinessEnabled(this)) "Off"
            else "On · ${SafetySettings.drowsinessSensitivity(this).label} sensitivity" +
                if (SafetySettings.isSoundAlarmsEnabled(this)) " · alarm sound" else " · silent"

        binding.rowVoice.tvRowSubtitle.text =
            if (!SafetySettings.isVoiceGuidanceEnabled(this)) "Spoken directions off"
            else "Spoken directions · ${SafetySettings.voiceVolume(this)}% volume"

        binding.rowOfflineMap.tvRowSubtitle.text = offlineMeta()?.let { "${it.first} · included in the app" } ?: "Not available"
        binding.rowAccount.tvRowSubtitle.text = FirebaseAuth.getInstance().currentUser?.email ?: "Not signed in"

        val permissions = PrivacyPermissionsActivity.relevantPermissions()
        val granted = permissions.count { ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED }
        binding.rowPrivacy.tvRowSubtitle.text = "$granted of ${permissions.size} permissions allowed"

        binding.rowAbout.tvRowSubtitle.text = "Version ${versionName()}"
    }

    private fun refreshCrashSummaryOnly() {
        val contacts = SafetySettings.cachedContacts(this)
        if (!SafetySettings.isCrashDetectionEnabled(this)) {
            binding.rowCrash.tvRowSubtitle.text = "Off"
            return
        }
        val count = when (contacts.size) {
            0 -> "no emergency contact yet"
            1 -> "1 emergency contact"
            else -> "${contacts.size} emergency contacts"
        }
        val auto = if (SafetySettings.canAutoRespond(this)) " · auto-alert on" else ""
        binding.rowCrash.tvRowSubtitle.text = "On · $count$auto"
    }

    /** (region, data date) of the bundled offline map, from assets/offline/meta.json. */
    private fun offlineMeta(): Pair<String, String>? = try {
        val json = JSONObject(assets.open("offline/meta.json").bufferedReader().use { it.readText() })
        json.getString("region") to json.getString("dataDate")
    } catch (e: Exception) {
        null
    }

    private fun versionName(): String = try {
        packageManager.getPackageInfo(packageName, 0).versionName ?: "?"
    } catch (e: PackageManager.NameNotFoundException) {
        "?"
    }

    private fun showOfflineMapInfo() {
        val meta = offlineMeta()
        val message = if (meta == null) "The offline map is not included in this build."
        else "A map of ${meta.first} is built into HelmX, so the map keeps working without internet.\n\n" +
            "• Map data: OpenStreetMap, ${meta.second}\n" +
            "• Works offline: map, your location, recent places, guidance on a route you already started\n" +
            "• Needs internet: search, new directions and rerouting"
        MaterialAlertDialogBuilder(this)
            .setTitle("Offline map")
            .setMessage(message)
            .setPositiveButton("OK", null)
            .show()
    }

    private fun confirmLogout() {
        val ride = if (RideSession.state.value.isRecording) "\n\nYour current ride will be ended and saved." else ""
        MaterialAlertDialogBuilder(this)
            .setTitle("Log out?")
            .setMessage("The helmet will be disconnected.$ride")
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Log out") { _, _ -> logout() }
            .show()
    }

    private fun logout() {
        binding.btnLogoutSettings.isEnabled = false
        lifecycleScope.launch {
            AuthManager().logout(this@SettingsActivity)
            val intent = Intent(this@SettingsActivity, LoginActivity::class.java)
            intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            startActivity(intent)
            finish()
        }
    }

    private fun setupBottomNavigation() {
        binding.bottomNavigation.selectedItemId = R.id.nav_settings
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_home -> {
                    val intent = Intent(this, DashboardActivity::class.java)
                    intent.flags = Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                    startActivity(intent)
                    true
                }
                R.id.nav_analytics -> {
                    val intent = Intent(this, AnalyticsActivity::class.java)
                    intent.flags = Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                    startActivity(intent)
                    true
                }
                R.id.nav_navigation -> {
                    val intent = Intent(this, NavigationActivity::class.java)
                    intent.flags = Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                    startActivity(intent)
                    true
                }
                R.id.nav_settings -> true
                else -> false
            }
        }
    }
}
