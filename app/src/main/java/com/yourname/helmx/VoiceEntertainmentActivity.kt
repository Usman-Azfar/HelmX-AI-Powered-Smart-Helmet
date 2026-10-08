package com.yourname.helmx

import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.yourname.helmx.databinding.ActivityVoiceEntertainmentBinding
import java.util.Locale

/** Voice guidance settings: spoken directions on/off and their volume. */
class VoiceEntertainmentActivity : AppCompatActivity(), TextToSpeech.OnInitListener {

    private lateinit var binding: ActivityVoiceEntertainmentBinding
    private var tts: TextToSpeech? = null
    private var ttsReady = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityVoiceEntertainmentBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.header.tvHeaderTitle.text = "Voice guidance"
        binding.header.btnBack.setOnClickListener { finish() }

        // Saved as soon as they change
        binding.switchVoiceGuidance.isChecked = SafetySettings.isVoiceGuidanceEnabled(this)
        binding.switchVoiceGuidance.setOnCheckedChangeListener { _, checked ->
            SafetySettings.setVoiceGuidanceEnabled(this, checked)
            updateEnabledState()
        }

        val volume = SafetySettings.voiceVolume(this).coerceIn(10, 100)
        binding.sliderVolume.value = (volume / 10 * 10).toFloat()
        binding.tvVolumeValue.text = "$volume%"
        binding.sliderVolume.addOnChangeListener { _, value, fromUser ->
            if (!fromUser) return@addOnChangeListener
            SafetySettings.setVoiceVolume(this, value.toInt())
            binding.tvVolumeValue.text = "${value.toInt()}%"
        }

        tts = TextToSpeech(this, this)
        binding.btnTestVoice.setOnClickListener { playSample() }
        updateEnabledState()
    }

    override fun onInit(status: Int) {
        ttsReady = status == TextToSpeech.SUCCESS
        if (ttsReady) tts?.language = Locale.US
    }

    private fun playSample() {
        if (!ttsReady) {
            Toast.makeText(this, "Text-to-speech isn't available on this phone", Toast.LENGTH_SHORT).show()
            return
        }
        val params = Bundle().apply {
            putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, SafetySettings.voiceVolume(this@VoiceEntertainmentActivity) / 100f)
        }
        tts?.speak("In 300 meters, turn left onto Main Boulevard", TextToSpeech.QUEUE_FLUSH, params, "sample")
    }

    private fun updateEnabledState() {
        val enabled = binding.switchVoiceGuidance.isChecked
        binding.sliderVolume.isEnabled = enabled
        binding.btnTestVoice.isEnabled = enabled
        binding.groupVolume.alpha = if (enabled) 1f else 0.5f
    }

    override fun onDestroy() {
        tts?.stop()
        tts?.shutdown()
        super.onDestroy()
    }
}
