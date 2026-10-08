package com.yourname.helmx

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.yourname.helmx.databinding.ActivityPrivacyPermissionsBinding
import com.yourname.helmx.databinding.ItemPermissionRowBinding

/** Shows what each permission is for, whether it's allowed, and a way to change it. */
class PrivacyPermissionsActivity : AppCompatActivity() {

    companion object {
        private val LOCATION = arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
        private val NEARBY = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S)
            arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT) else emptyArray()
        private val MICROPHONE = arrayOf(Manifest.permission.RECORD_AUDIO)
        private val NOTIFICATIONS = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU)
            arrayOf(Manifest.permission.POST_NOTIFICATIONS) else emptyArray()

        /** One representative permission per row that exists on this Android version (for summaries). */
        fun relevantPermissions(): List<String> = listOfNotNull(
            LOCATION.first(), NEARBY.lastOrNull(), MICROPHONE.first(), NOTIFICATIONS.firstOrNull()
        )
    }

    private lateinit var binding: ActivityPrivacyPermissionsBinding

    // Permissions the rider asked for from this screen; if still denied afterwards, Android
    // won't show the prompt again, so we send them to App info instead
    private val permissionRequest = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
        val denied = result.filterValues { !it }.keys
        if (denied.isNotEmpty() && denied.none { shouldShowRequestPermissionRationale(it) }) openAppSettings()
        refresh()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityPrivacyPermissionsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.header.tvHeaderTitle.text = "Privacy & permissions"
        binding.header.btnBack.setOnClickListener { finish() }

        setupRow(binding.permLocation, "Location", "Map, directions and ride distance", LOCATION)
        setupRow(binding.permNearby, "Nearby devices", "Find and connect to your helmet over Bluetooth", NEARBY)
        setupRow(binding.permMicrophone, "Microphone", "Voice search (\"Where to?\")", MICROPHONE)
        setupRow(binding.permNotifications, "Notifications", "Crash and drowsiness alerts, ride recording", NOTIFICATIONS)

        // Rows that don't exist as separate permissions on older Android versions
        if (NEARBY.isEmpty()) {
            binding.permNearby.root.visibility = View.GONE
            binding.dividerNearby.visibility = View.GONE
        }
        if (NOTIFICATIONS.isEmpty()) {
            binding.permNotifications.root.visibility = View.GONE
            binding.dividerNotifications.visibility = View.GONE
        }
    }

    override fun onResume() {
        super.onResume()
        refresh() // the rider may have changed something in system settings
    }

    private val rows = mutableListOf<Pair<ItemPermissionRowBinding, Array<String>>>()

    private fun setupRow(row: ItemPermissionRowBinding, title: String, description: String, permissions: Array<String>) {
        row.tvPermTitle.text = title
        row.tvPermDesc.text = description
        row.btnPermAction.setOnClickListener {
            if (isGranted(permissions)) openAppSettings() else permissionRequest.launch(permissions)
        }
        rows += row to permissions
    }

    private fun isGranted(permissions: Array<String>): Boolean =
        permissions.isNotEmpty() && permissions.any { ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED }

    private fun refresh() {
        rows.forEach { (row, permissions) ->
            if (permissions.isEmpty()) return@forEach
            val granted = isGranted(permissions)
            row.tvPermStatus.text = if (granted) "Allowed" else "Not allowed"
            row.tvPermStatus.setTextColor(
                ContextCompat.getColor(this, if (granted) R.color.nav_route_time else R.color.danger_red)
            )
            row.btnPermAction.text = if (granted) "Manage" else "Allow"
        }
    }

    private fun openAppSettings() {
        startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", packageName, null)))
    }
}
