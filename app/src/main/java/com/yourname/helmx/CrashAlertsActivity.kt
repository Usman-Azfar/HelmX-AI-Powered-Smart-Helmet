package com.yourname.helmx

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.ContactsContract
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.widget.doAfterTextChanged
import androidx.lifecycle.lifecycleScope
import com.google.android.material.textfield.TextInputEditText
import com.yourname.helmx.databinding.ActivityCrashAlertsBinding
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

class CrashAlertsActivity : AppCompatActivity() {

    private lateinit var binding: ActivityCrashAlertsBinding

    // Which contact slot the contact picker fills (1 or 2)
    private var pickingSlot = 1
    private var userEdited = false
    private var settingText = false

    // Picking from Phone.CONTENT_URI grants read access to the chosen entry only,
    // so READ_CONTACTS permission is not needed
    private val pickContact = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        val uri = result.data?.data ?: return@registerForActivityResult
        contentResolver.query(
            uri,
            arrayOf(ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME, ContactsContract.CommonDataKinds.Phone.NUMBER),
            null, null, null
        )?.use { cursor ->
            if (cursor.moveToFirst()) {
                val name = cursor.getString(0).orEmpty()
                val number = cursor.getString(1).orEmpty()
                val (nameField, phoneField) = slotFields(pickingSlot)
                nameField.setText(name)
                phoneField.setText(number)
                userEdited = true
            }
        }
    }

    private val notificationPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    private val autoResponsePermissions = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
        val granted = result.values.all { it }
        SafetySettings.setAutoResponseEnabled(this, granted)
        binding.switchAutoResponse.isChecked = granted
        if (!granted) {
            Toast.makeText(this, "SMS and phone permission are needed for automatic alerts", Toast.LENGTH_LONG).show()
        }
        updateAutoResponseHelp()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCrashAlertsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.header.tvHeaderTitle.text = "Crash alerts & contacts"
        binding.header.btnBack.setOnClickListener { finish() }

        binding.switchCrashDetection.isChecked = SafetySettings.isCrashDetectionEnabled(this)
        binding.switchCrashDetection.setOnCheckedChangeListener { _, checked ->
            SafetySettings.setCrashDetectionEnabled(this, checked) // saved immediately
        }

        binding.switchAutoResponse.isChecked = SafetySettings.isAutoResponseEnabled(this) &&
            SafetySettings.hasAutoResponsePermissions(this)
        binding.switchAutoResponse.setOnCheckedChangeListener { _, checked ->
            if (!checked) {
                SafetySettings.setAutoResponseEnabled(this, false)
            } else if (SafetySettings.hasAutoResponsePermissions(this)) {
                SafetySettings.setAutoResponseEnabled(this, true)
            } else {
                autoResponsePermissions.launch(SafetySettings.AUTO_RESPONSE_PERMISSIONS)
            }
            updateAutoResponseHelp()
        }
        updateAutoResponseHelp()

        binding.tilContact1Phone.setEndIconOnClickListener { pick(1) }
        binding.tilContact2Phone.setEndIconOnClickListener { pick(2) }

        showContacts(SafetySettings.cachedContacts(this))
        lifecycleScope.launch {
            val fresh = SafetySettings.loadContacts(this@CrashAlertsActivity)
            if (!userEdited) showContacts(fresh) // don't overwrite what the rider is typing
        }
        listOf(binding.etContact1Name, binding.etContact1Phone, binding.etContact2Name, binding.etContact2Phone).forEach {
            it.doAfterTextChanged { if (!settingText) userEdited = true }
        }

        binding.btnSave.setOnClickListener { save() }
        binding.btnTestAlert.setOnClickListener {
            ensureNotificationPermission()
            SafetyMonitor.showTestCrashAlert(this)
            Toast.makeText(this, "Test alert sent. Check your notifications.", Toast.LENGTH_SHORT).show()
        }
    }

    private fun updateAutoResponseHelp() {
        val base = "If you don't respond within ${SafetySettings.AUTO_RESPONSE_SECONDS} seconds of a crash, HelmX texts your location to your contacts and calls your primary contact."
        binding.tvAutoResponseHelp.text =
            if (binding.switchAutoResponse.isChecked && SafetySettings.cachedContacts(this).isEmpty()) "$base\n\nAdd an emergency contact below for this to work."
            else base
    }

    private fun slotFields(slot: Int): Pair<TextInputEditText, TextInputEditText> =
        if (slot == 1) binding.etContact1Name to binding.etContact1Phone else binding.etContact2Name to binding.etContact2Phone

    private fun pick(slot: Int) {
        pickingSlot = slot
        try {
            pickContact.launch(Intent(Intent.ACTION_PICK, ContactsContract.CommonDataKinds.Phone.CONTENT_URI))
        } catch (e: android.content.ActivityNotFoundException) {
            Toast.makeText(this, "No contacts app found", Toast.LENGTH_SHORT).show()
        }
    }

    private fun showContacts(contacts: List<EmergencyContact>) {
        settingText = true
        contacts.getOrNull(0).let {
            binding.etContact1Name.setText(it?.name.orEmpty())
            binding.etContact1Phone.setText(it?.phone.orEmpty())
        }
        contacts.getOrNull(1).let {
            binding.etContact2Name.setText(it?.name.orEmpty())
            binding.etContact2Phone.setText(it?.phone.orEmpty())
        }
        settingText = false
    }

    /** Validates one slot; returns the contact, null for an empty slot, or throws on invalid input. */
    private fun readSlot(slot: Int): EmergencyContact? {
        val (nameField, phoneField) = slotFields(slot)
        val phoneLayout = if (slot == 1) binding.tilContact1Phone else binding.tilContact2Phone
        val name = nameField.text?.toString()?.trim().orEmpty()
        val phone = Validators.normalizePhone(phoneField.text?.toString()?.trim().orEmpty())
        phoneLayout.error = null
        if (name.isEmpty() && phone.isEmpty()) return null
        if (!Validators.isValidContactPhone(phone)) {
            phoneLayout.error = if (phone.isEmpty()) "Enter a phone number" else "Enter a valid phone number"
            throw IllegalArgumentException()
        }
        return EmergencyContact(name.ifEmpty { phone }, phone)
    }

    private fun save() {
        val contacts = try {
            listOfNotNull(readSlot(1), readSlot(2))
        } catch (e: IllegalArgumentException) {
            return
        }
        ensureNotificationPermission()
        binding.btnSave.isEnabled = false
        lifecycleScope.launch {
            // Firestore queues the write when offline, so don't wait forever for the server
            val result = runCatching { withTimeoutOrNull(5000) { SafetySettings.saveContacts(this@CrashAlertsActivity, contacts) } }
            binding.btnSave.isEnabled = true
            if (result.isFailure) {
                Toast.makeText(this@CrashAlertsActivity, "Couldn't save contacts: ${result.exceptionOrNull()?.message}", Toast.LENGTH_LONG).show()
                return@launch
            }
            Toast.makeText(
                this@CrashAlertsActivity,
                if (contacts.isEmpty()) "Emergency contacts cleared" else "Emergency contacts saved",
                Toast.LENGTH_SHORT
            ).show()
            finish()
        }
    }

    /** Crash alerts are notifications; ask for permission where Android requires it (13+). */
    private fun ensureNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            notificationPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }
}
