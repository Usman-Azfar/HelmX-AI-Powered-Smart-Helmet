package com.yourname.helmx

import android.content.pm.PackageManager
import android.os.Bundle
import android.view.View
import android.widget.LinearLayout
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.yourname.helmx.databinding.ActivityAboutBinding
import com.yourname.helmx.databinding.ItemAboutRowBinding
import kotlinx.coroutines.launch

/** Project, features, helmet connection details, team and credits. */
class AboutActivity : AppCompatActivity() {

    private lateinit var binding: ActivityAboutBinding
    private var statusRow: ItemAboutRowBinding? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityAboutBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.header.tvHeaderTitle.text = "About HelmX"
        binding.header.btnBack.setOnClickListener { finish() }
        binding.tvVersion.text = "Version ${versionName()}"

        // Core features from the project proposal
        listOf(
            Triple(R.drawable.ic_shield, "Crash detection", "IMU sensors detect impacts; HelmX alerts your emergency contacts with your location"),
            Triple(R.drawable.ic_notification_bell, "Drowsiness detection", "Camera-based AI watches for eye closure and head pose and sounds an alarm"),
            Triple(R.drawable.ic_navigation, "Smart navigation", "Turn-by-turn directions with voice prompts, rerouting and an offline Lahore map"),
            Triple(R.drawable.ic_mic, "AI voice assistant", "A talking ride companion: ask by voice for directions, calls, music or helmet status, hands-free"),
            Triple(R.drawable.ic_phone, "Voice control & entertainment", "Hands-free voice search and spoken guidance; calls and audio over Bluetooth"),
            Triple(R.drawable.ic_thermometer, "Environment monitoring", "Temperature, humidity and air quality from the helmet's sensors"),
            Triple(R.drawable.ic_motorcycle, "Dual cameras", "Front and rear cameras for evidence capture (helmet feature)"),
            Triple(R.drawable.ic_analytics, "Ride analytics", "Rides recorded with distance, duration and average speed")
        ).forEach { (icon, title, text) -> addRow(binding.listFeatures, title, text, icon) }

        // Helmet connection (values used by HelmetBleManager)
        statusRow = addRow(binding.listConnection, "Status", "Disconnected", R.drawable.ic_bluetooth)
        addRow(binding.listConnection, "Helmet computer", "Raspberry Pi (Bluetooth Low Energy peripheral)")
        addRow(binding.listConnection, "Device name", "HelmX")
        addRow(binding.listConnection, "Service UUID", "0000FFE0-0000-1000-8000-00805F9B34FB")
        addRow(binding.listConnection, "Data characteristic", "0000FFE1-0000-1000-8000-00805F9B34FB (notify)")
        addRow(binding.listConnection, "Data format", "JSON: temperature, humidity, air_quality, destination\nCSV: battery, speed, drowsy, crash, distance")
        addRow(binding.listConnection, "Packet size", "MTU 512 bytes requested")

        // Team (from the project proposal)
        addRow(binding.listTeam, "Ms. Tayyaba Tariq", "Supervisor", R.drawable.ic_user_check)
        addRow(binding.listTeam, "Usman Azfar", "Group leader · hardware & integration, cloud, safety, voice and environment systems, app", R.drawable.ic_person)
        addRow(binding.listTeam, "Hamza Ahmad", "Web & app development, backend APIs, database, edge computing, ML testing", R.drawable.ic_person)
        addRow(binding.listTeam, "Abdul Hanan", "ML models for crash & drowsiness detection, alerts, smart navigation, documentation", R.drawable.ic_person)
        addRow(binding.listTeam, "Awais Imtiaz", "Hardware integration, prototype testing, web & app development, documentation", R.drawable.ic_person)

        // Live helmet status
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                HelmetBleManager.getInstance(this@AboutActivity).helmetData.collect { data ->
                    statusRow?.tvSubtitle?.text = data.connectionStatus.label
                }
            }
        }
    }

    private fun addRow(parent: LinearLayout, title: String, subtitle: String, icon: Int? = null): ItemAboutRowBinding {
        val row = ItemAboutRowBinding.inflate(layoutInflater, parent, true)
        row.tvTitle.text = title
        row.tvSubtitle.text = subtitle
        if (icon != null) row.ivIcon.setImageResource(icon) else row.iconFrame.visibility = View.GONE
        return row
    }

    private fun versionName(): String = try {
        packageManager.getPackageInfo(packageName, 0).versionName ?: "?"
    } catch (e: PackageManager.NameNotFoundException) {
        "?"
    }
}
