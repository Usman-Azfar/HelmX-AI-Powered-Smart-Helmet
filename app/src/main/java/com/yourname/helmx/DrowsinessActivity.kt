package com.yourname.helmx

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.yourname.helmx.databinding.ActivityDrowsinessBinding

class DrowsinessActivity : AppCompatActivity() {

    private lateinit var binding: ActivityDrowsinessBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDrowsinessBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.header.tvHeaderTitle.text = "Drowsiness alerts"
        binding.header.btnBack.setOnClickListener { finish() }

        // Every control saves as soon as it changes
        binding.switchDrowsiness.isChecked = SafetySettings.isDrowsinessEnabled(this)
        binding.switchDrowsiness.setOnCheckedChangeListener { _, checked ->
            SafetySettings.setDrowsinessEnabled(this, checked)
            updateEnabledState()
        }

        binding.switchSoundAlarms.isChecked = SafetySettings.isSoundAlarmsEnabled(this)
        binding.switchSoundAlarms.setOnCheckedChangeListener { _, checked ->
            SafetySettings.setSoundAlarmsEnabled(this, checked)
        }

        val sensitivity = SafetySettings.drowsinessSensitivity(this)
        binding.sliderSensitivity.value = sensitivity.ordinal.toFloat()
        showSensitivity(sensitivity)
        binding.sliderSensitivity.addOnChangeListener { _, value, fromUser ->
            if (!fromUser) return@addOnChangeListener
            val chosen = DrowsinessSensitivity.fromIndex(value.toInt())
            SafetySettings.setDrowsinessSensitivity(this, chosen)
            showSensitivity(chosen)
        }

        binding.btnTestAlarm.setOnClickListener { SafetyMonitor.testDrowsyAlarm(this) }
        updateEnabledState()
    }

    private fun showSensitivity(s: DrowsinessSensitivity) {
        binding.tvSensitivityValue.text = s.label
        binding.tvSensitivityHelp.text = if (s.delayMs == 0L) "Alarm as soon as the helmet reports drowsiness"
        else "Alarm after ${s.delayMs / 1000.0} seconds of drowsiness".replace(".0 ", " ")
    }

    private fun updateEnabledState() {
        val enabled = binding.switchDrowsiness.isChecked
        binding.switchSoundAlarms.isEnabled = enabled
        binding.sliderSensitivity.isEnabled = enabled
        binding.groupSensitivity.alpha = if (enabled) 1f else 0.5f
    }
}
