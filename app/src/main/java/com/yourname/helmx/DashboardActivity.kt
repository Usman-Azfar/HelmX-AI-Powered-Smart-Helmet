package com.yourname.helmx

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.location.LocationManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.location.LocationManagerCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.ProcessLifecycleOwner
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.yourname.helmx.databinding.ActivityDashboardBinding
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class DashboardActivity : AppCompatActivity() {

    companion object {
        private const val KEY_LAST_DESTINATION = "last_handled_destination"
        private const val KEY_CRASH_ALERTED = "crash_alerted"

        private val COLOR_OK = Color.parseColor("#43A047")      // Green
        private val COLOR_BUSY = Color.parseColor("#FB8C00")    // Orange
        private val COLOR_ERROR = Color.parseColor("#E53935")   // Red
    }

    private lateinit var binding: ActivityDashboardBinding
    private val authManager = AuthManager()
    private lateinit var helmetBleManager: HelmetBleManager

    // Kept across recreation (e.g. theme change) so the same event is not handled twice
    private var lastHandledDestination = ""
    private var crashAlerted = false
    private var crashDialog: AlertDialog? = null

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val denied = permissions.filterValues { granted -> !granted }.keys
        when {
            denied.isEmpty() -> checkBluetoothAndScan()
            // No rationale after a denial means "Don't ask again": only Settings can grant it now
            denied.none { shouldShowRequestPermissionRationale(it) } -> showOpenSettingsDialog()
            else -> Toast.makeText(this, "Bluetooth and Location permissions are required for pairing", Toast.LENGTH_LONG).show()
        }
    }

    private val bluetoothEnableLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            startHelmetScan()
        } else {
            Toast.makeText(this, "Bluetooth must be enabled to pair with the helmet", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDashboardBinding.inflate(layoutInflater)
        setContentView(binding.root)

        helmetBleManager = HelmetBleManager.getInstance(this)

        // Check if user is logged in
        if (authManager.getCurrentUser() == null) {
            navigateToLogin()
            return
        }

        savedInstanceState?.let {
            lastHandledDestination = it.getString(KEY_LAST_DESTINATION, "")
            crashAlerted = it.getBoolean(KEY_CRASH_ALERTED, false)
        }

        // Setup UI listeners
        setupClickListeners()
        setupBottomNavigation()
        setupBackNavigation()

        // Observe real-time data from BLE
        observeHelmetData()
    }

    override fun onStart() {
        super.onStart()
        // Reload on every return so profile edits made in AccountActivity show up here
        authManager.getCurrentUser()?.let { loadUserData(it.uid) }
    }

    override fun onResume() {
        super.onResume()
        binding.bottomNavigation.selectedItemId = R.id.nav_home
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putString(KEY_LAST_DESTINATION, lastHandledDestination)
        outState.putBoolean(KEY_CRASH_ALERTED, crashAlerted)
    }

    override fun onDestroy() {
        crashDialog?.dismiss()
        crashDialog = null
        super.onDestroy()
    }

    private fun setupBottomNavigation() {
        binding.bottomNavigation.selectedItemId = R.id.nav_home
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_home -> true
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
                R.id.nav_settings -> {
                    val intent = Intent(this, SettingsActivity::class.java)
                    intent.flags = Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                    startActivity(intent)
                    true
                }
                else -> false
            }
        }
    }

    private fun setupBackNavigation() {
        // Home is the root tab: Back leaves the app instead of cycling through other tabs
        // that were reordered underneath. The task (and helmet connection) stays alive.
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                moveTaskToBack(true)
            }
        })
    }

    private fun setupClickListeners() {
        binding.ivProfile.setOnClickListener {
            startActivity(Intent(this, AccountActivity::class.java))
        }

        binding.btnNotifications.setOnClickListener {
            Toast.makeText(this, "No new notifications", Toast.LENGTH_SHORT).show()
        }

        // Debug builds only: long-press Pair to start/stop a simulated helmet (demos, screenshots)
        val debuggable = (applicationInfo.flags and android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0
        if (debuggable) {
            binding.btnPair.setOnLongClickListener {
                if (helmetBleManager.isDemoMode) {
                    helmetBleManager.stopDemo()
                    Toast.makeText(this, "Demo helmet stopped", Toast.LENGTH_SHORT).show()
                } else {
                    helmetBleManager.startDemo()
                    Toast.makeText(this, "Demo helmet started (simulated data, debug build)", Toast.LENGTH_SHORT).show()
                }
                true
            }
        }

        binding.btnPair.setOnClickListener {
            when (helmetBleManager.helmetData.value.connectionStatus) {
                ConnectionStatus.CONNECTED -> {
                    helmetBleManager.disconnect()
                    Toast.makeText(this, "Disconnected from HelmX", Toast.LENGTH_SHORT).show()
                }
                ConnectionStatus.RECONNECTING -> {
                    helmetBleManager.disconnect()
                    Toast.makeText(this, "Stopped reconnecting", Toast.LENGTH_SHORT).show()
                }
                else -> checkPermissionsAndScan()
            }
        }

        binding.cardDrowsinessAlert.setOnClickListener {
            startActivity(Intent(this, DrowsinessActivity::class.java))
        }

        binding.cardCrashAlert.setOnClickListener {
            startActivity(Intent(this, CrashAlertsActivity::class.java))
        }
    }

    private fun checkPermissionsAndScan() {
        if (!helmetBleManager.isBluetoothSupported()) {
            Toast.makeText(this, "This device does not support Bluetooth Low Energy", Toast.LENGTH_LONG).show()
            return
        }

        val permissions = mutableListOf<String>()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissions.add(Manifest.permission.BLUETOOTH_SCAN)
            permissions.add(Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            permissions.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }

        val missingPermissions = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missingPermissions.isEmpty()) {
            checkBluetoothAndScan()
        } else {
            requestPermissionLauncher.launch(missingPermissions.toTypedArray())
        }
    }

    private fun checkBluetoothAndScan() {
        if (helmetBleManager.isBluetoothEnabled()) {
            startHelmetScan()
        } else {
            val enableBtIntent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
            bluetoothEnableLauncher.launch(enableBtIntent)
        }
    }

    private fun startHelmetScan() {
        // Before Android 12, BLE scans return no results while Location services are off
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
            val locationManager = getSystemService(LOCATION_SERVICE) as LocationManager
            if (!LocationManagerCompat.isLocationEnabled(locationManager)) {
                MaterialAlertDialogBuilder(this)
                    .setTitle("Turn on Location")
                    .setMessage("Android needs Location services switched on to find Bluetooth devices nearby.")
                    .setPositiveButton("Open Settings") { _, _ ->
                        startActivity(Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS))
                    }
                    .setNegativeButton("Cancel", null)
                    .show()
                return
            }
        }

        helmetBleManager.startScan()
        Toast.makeText(this, "Scanning for HelmX Pro v1...", Toast.LENGTH_SHORT).show()
    }

    private fun showOpenSettingsDialog() {
        MaterialAlertDialogBuilder(this)
            .setTitle("Permission needed")
            .setMessage(
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S)
                    "Pairing needs the Nearby devices permission. Please allow it in App settings."
                else
                    "Pairing needs the Location permission to find Bluetooth devices. Please allow it in App settings."
            )
            .setPositiveButton("Open Settings") { _, _ ->
                startActivity(
                    Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", packageName, null))
                )
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun observeHelmetData() {
        // UI updates only while this screen is visible
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                helmetBleManager.helmetData.collectLatest { data ->
                    updateUI(data)
                    handleCrashAlert(data)
                }
            }
        }

        // Auto-navigate when the helmet sends a destination, even if another tab is on top.
        // Skipped while the app is in the background; NavigationActivity applies the
        // pending destination itself once it is opened.
        lifecycleScope.launch {
            helmetBleManager.helmetData.collectLatest { data ->
                if (data.destination.isEmpty()) {
                    // Cleared (e.g. after a disconnect): allow the same destination to trigger again
                    lastHandledDestination = ""
                } else if (data.destination != lastHandledDestination) {
                    lastHandledDestination = data.destination
                    val appInForeground = ProcessLifecycleOwner.get().lifecycle.currentState
                        .isAtLeast(Lifecycle.State.STARTED)
                    if (appInForeground) {
                        val intent = Intent(this@DashboardActivity, NavigationActivity::class.java)
                        intent.flags = Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                        startActivity(intent)
                    }
                }
            }
        }
    }

    private fun handleCrashAlert(data: HelmetData) {
        val crash = data.isCrashDetected && data.connectionStatus == ConnectionStatus.CONNECTED &&
            SafetySettings.isCrashDetectionEnabled(this)
        if (crash && !crashAlerted) {
            crashAlerted = true
            showCrashDialog()
        } else if (!crash) {
            crashAlerted = false
        }
    }

    /** Same choices as the crash notification raised by SafetyMonitor. */
    private fun showCrashDialog() {
        val contacts = SafetySettings.cachedContacts(this)
        val first = contacts.firstOrNull()
        val callNumber = first?.phone ?: SafetyMonitor.FALLBACK_EMERGENCY_NUMBER
        val callLabel = first?.let { "Call ${it.name.ifBlank { it.phone }}" } ?: "Call ${SafetyMonitor.FALLBACK_EMERGENCY_NUMBER}"

        val builder = MaterialAlertDialogBuilder(this)
            .setTitle("Crash detected")
            .setMessage(
                if (contacts.isEmpty()) "Your helmet reported a possible crash. Are you OK?\n\nNo emergency contact is set (Settings → Crash alerts)."
                else "Your helmet reported a possible crash. Are you OK?"
            )
            .setCancelable(false)
            .setPositiveButton("I'm OK") { _, _ -> SafetyMonitor.onRiderResponded(this, dismiss = true) }
            .setNegativeButton(callLabel) { _, _ ->
                SafetyMonitor.onRiderResponded(this, dismiss = false)
                if (!EmergencyActions.launch(this, EmergencyActions.dialIntent(callNumber))) {
                    Toast.makeText(this, "No phone app available", Toast.LENGTH_SHORT).show()
                }
            }
        if (contacts.isNotEmpty()) {
            builder.setNeutralButton("Text location") { _, _ ->
                SafetyMonitor.onRiderResponded(this, dismiss = false)
                val location = SafetyMonitor.lastCrashLocation
                val intent = EmergencyActions.smsIntent(contacts, location?.first, location?.second)
                if (!EmergencyActions.launch(this, intent)) {
                    Toast.makeText(this, "No messaging app available", Toast.LENGTH_SHORT).show()
                }
            }
        }
        val dialog = builder.show()
        crashDialog = dialog

        // Show the automatic-response countdown live in the dialog
        val baseMessage = if (contacts.isEmpty()) null else "Your helmet reported a possible crash. Are you OK?"
        if (baseMessage != null) {
            lifecycleScope.launch {
                SafetyMonitor.countdown.collect { seconds ->
                    if (!dialog.isShowing) return@collect
                    dialog.setMessage(
                        if (seconds == null) baseMessage
                        else "$baseMessage\n\nIf you don't respond, HelmX will text your location and call ${first?.name} in $seconds s."
                    )
                    if (seconds == null && SafetyMonitor.countdownFinished) dialog.dismiss()
                }
            }
        }
    }

    private fun updateUI(data: HelmetData) {
        binding.tvHelmetName.text = if (helmetBleManager.isDemoMode) "HelmX Pro v1 · Demo" else "HelmX Pro v1"
        val status = data.connectionStatus
        val connected = status == ConnectionStatus.CONNECTED
        binding.tvConnectionStatus.text = status.label

        when {
            connected -> {
                binding.tvConnectionStatus.setTextColor(COLOR_OK)
                binding.btnPair.text = "Unpair"
                binding.btnPair.isEnabled = true
            }
            status == ConnectionStatus.RECONNECTING -> {
                binding.tvConnectionStatus.setTextColor(COLOR_BUSY)
                binding.btnPair.text = "Cancel"
                binding.btnPair.isEnabled = true
            }
            status.isBusy -> {
                binding.tvConnectionStatus.setTextColor(COLOR_BUSY)
                binding.btnPair.text = "Wait"
                binding.btnPair.isEnabled = false
            }
            else -> {
                binding.tvConnectionStatus.setTextColor(COLOR_ERROR)
                binding.btnPair.text = "Pair"
                binding.btnPair.isEnabled = true
            }
        }
        // The layout's fixed text color hides the disabled state, so dim it explicitly
        binding.btnPair.alpha = if (binding.btnPair.isEnabled) 1f else 0.4f

        if (!connected) {
            // Without a helmet link there is no live data and no active monitoring
            val offlineColor = ContextCompat.getColor(this, R.color.text_secondary)
            binding.tvBatteryStat.text = "--"
            binding.tvSpeedStat.text = "--"
            binding.tvDistanceStat.text = "--"
            binding.tvDrowsinessStatus.text = "Offline"
            binding.tvDrowsinessStatus.setTextColor(offlineColor)
            binding.tvCrashStatus.text = "Offline"
            binding.tvCrashStatus.setTextColor(offlineColor)
            return
        }

        binding.tvBatteryStat.text = "${data.batteryLevel}%"
        binding.tvSpeedStat.text = "${data.speed.toInt()} km/h"
        binding.tvDistanceStat.text = "${String.format("%.1f", data.distance)} km"

        binding.tvDrowsinessStatus.text = if (data.isDrowsy) "ALERT!" else "Normal"
        binding.tvDrowsinessStatus.setTextColor(if (data.isDrowsy) COLOR_ERROR else COLOR_OK)

        binding.tvCrashStatus.text = if (data.isCrashDetected) "CRASH!" else "Active"
        binding.tvCrashStatus.setTextColor(if (data.isCrashDetected) COLOR_ERROR else COLOR_OK)
    }

    private fun loadUserData(uid: String) {
        lifecycleScope.launch {
            val result = authManager.getUserData(uid)
            val firstName = result.getOrNull()?.fullname?.trim()?.split(Regex("\\s+"))?.firstOrNull()
            binding.tvWelcome.text = if (firstName.isNullOrBlank()) "Hello, Rider!" else "Hello, $firstName!"
        }
    }

    private fun navigateToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }
}
