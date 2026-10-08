package com.yourname.helmx

import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import com.yourname.helmx.databinding.ActivityAnalyticsBinding
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import java.util.Calendar
import java.util.Locale

class AnalyticsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityAnalyticsBinding
    private val rideRepository = RideRepository()
    private val rideAdapter = RideHistoryAdapter()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityAnalyticsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupBottomNavigation()
        setupRideHistory()
        observeHelmetData()
    }

    override fun onStart() {
        super.onStart()
        // Tabs are reordered rather than recreated, so reload rides each time this screen shows
        loadRides()
    }

    override fun onResume() {
        super.onResume()
        binding.bottomNavigation.selectedItemId = R.id.nav_analytics
    }

    private fun observeHelmetData() {
        val helmetBleManager = HelmetBleManager.getInstance(this)
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                helmetBleManager.helmetData.collectLatest { data -> updateEnvironment(data) }
            }
        }
    }

    private fun updateEnvironment(data: HelmetData) {
        val secondary = ContextCompat.getColor(this, R.color.text_secondary)
        if (data.connectionStatus != ConnectionStatus.CONNECTED) {
            // No helmet link: no live readings (0.0 would look like a real measurement)
            binding.tvTempValue.text = "--"
            binding.tvHumidityValue.text = "--"
            binding.progressHumidity.progress = 0
            binding.tvAirQualityValue.text = "Helmet offline"
            binding.tvAirQualityValue.setTextColor(secondary)
            return
        }

        binding.tvTempValue.text = String.format(Locale.getDefault(), "%.1f", data.temperature)
        binding.tvHumidityValue.text = String.format(Locale.getDefault(), "%.1f", data.humidity)
        binding.progressHumidity.progress = data.humidity.toInt().coerceIn(0, 100)

        val air = data.airQuality
        binding.tvAirQualityValue.text = air
        val airLower = air.lowercase(Locale.ROOT)
        binding.tvAirQualityValue.setTextColor(
            when {
                listOf("contaminated", "poor", "bad", "unhealthy", "hazard").any { it in airLower } -> Color.parseColor("#E53935")
                listOf("good", "clean", "fresh").any { it in airLower } -> Color.parseColor("#4ADE80")
                else -> secondary // "Unknown" or an unrecognised label: no judgement implied
            }
        )
    }

    private fun setupRideHistory() {
        binding.rvRideHistory.layoutManager = LinearLayoutManager(this)
        binding.rvRideHistory.adapter = rideAdapter
    }

    private fun loadRides() {
        lifecycleScope.launch {
            val todayResult = rideRepository.getRidesSince(startOfToday())
            todayResult.onSuccess { today ->
                binding.tvActiveRidesValue.text = today.size.toString()
                binding.tvActiveRidesSubtext.text = String.format(
                    Locale.getDefault(), "%.1f km today", today.sumOf { it.distanceKm }
                )
            }.onFailure {
                binding.tvActiveRidesValue.text = "--"
                binding.tvActiveRidesSubtext.text = "Couldn't load rides"
            }

            rideRepository.getRecentRides().onSuccess { rides ->
                rideAdapter.submitList(rides)
                binding.tvRideHistoryEmpty.text =
                    "No rides yet. Start navigation and press START to record a ride."
                binding.tvRideHistoryEmpty.visibility = if (rides.isEmpty()) android.view.View.VISIBLE else android.view.View.GONE
            }.onFailure { e ->
                android.util.Log.e("AnalyticsActivity", "Failed to load rides", e)
                binding.tvRideHistoryEmpty.text = "Couldn't load rides. Check your connection."
                binding.tvRideHistoryEmpty.visibility = android.view.View.VISIBLE
            }
        }
    }

    private fun startOfToday(): Long = Calendar.getInstance().apply {
        set(Calendar.HOUR_OF_DAY, 0)
        set(Calendar.MINUTE, 0)
        set(Calendar.SECOND, 0)
        set(Calendar.MILLISECOND, 0)
    }.timeInMillis

    private fun setupBottomNavigation() {
        binding.bottomNavigation.selectedItemId = R.id.nav_analytics
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_home -> {
                    val intent = Intent(this, DashboardActivity::class.java)
                    intent.flags = Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                    startActivity(intent)
                    true
                }
                R.id.nav_analytics -> true
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
}
