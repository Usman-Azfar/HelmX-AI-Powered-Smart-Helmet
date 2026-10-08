package com.yourname.helmx

import android.content.Intent
import android.os.Bundle
import android.text.InputType
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseAuthInvalidCredentialsException
import com.google.firebase.firestore.FirebaseFirestore
import com.yourname.helmx.databinding.ActivityAccountBinding
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await

class AccountActivity : AppCompatActivity() {

    private lateinit var binding: ActivityAccountBinding
    private val authManager = AuthManager()
    private val firestore = FirebaseFirestore.getInstance()
    private var currentUserId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityAccountBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.header.tvHeaderTitle.text = "Account"
        binding.header.btnBack.setOnClickListener { finish() }

        val user = authManager.getCurrentUser()
        currentUserId = user?.uid
        if (currentUserId == null) {
            Toast.makeText(this, "Not logged in", Toast.LENGTH_SHORT).show()
            finish()
            return
        }
        loadUserData(currentUserId!!)

        binding.btnSave.setOnClickListener { saveUserData() }
        binding.btnLogout.setOnClickListener { confirmLogout() }
        binding.btnDeleteAccount.setOnClickListener { confirmDeleteAccount() }
    }

    private fun loadUserData(uid: String) {
        lifecycleScope.launch {
            // Reload so an email changed via the verification link is picked up
            runCatching { FirebaseAuth.getInstance().currentUser?.reload()?.await() }
            val authEmail = FirebaseAuth.getInstance().currentUser?.email.orEmpty()
            binding.tvEmail.text = "Email: $authEmail"

            authManager.getUserData(uid).onSuccess { user ->
                binding.etFullName.setText(user.fullname)
                binding.etPhone.setText(user.phone)
                // Keep the profile's copy of the email in step with the login email
                if (authEmail.isNotEmpty() && user.email != authEmail) {
                    firestore.collection("users").document(uid).update("email", authEmail)
                }
            }.onFailure {
                Toast.makeText(this@AccountActivity, "Couldn't load your profile", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun clearErrors() {
        listOf(binding.tilFullName, binding.tilPhone, binding.tilNewEmail, binding.tilNewPassword, binding.tilCurrentPassword)
            .forEach { it.error = null }
    }

    private fun saveUserData() {
        val uid = currentUserId ?: return
        clearErrors()
        val newName = binding.etFullName.text.toString().trim()
        val newPhone = Validators.normalizePhone(binding.etPhone.text.toString().trim())
        val newEmail = binding.etNewEmail.text.toString().trim()
        val newPass = binding.etNewPassword.text.toString()
        val currentPass = binding.etCurrentPassword.text.toString()
        val currentEmail = FirebaseAuth.getInstance().currentUser?.email.orEmpty()

        if (newName.isEmpty()) { binding.tilFullName.error = "Name cannot be empty"; return }
        if (!Validators.isValidPhone(newPhone)) { binding.tilPhone.error = Validators.PHONE_ERROR; return }

        val changeEmail = newEmail.isNotEmpty() && !newEmail.equals(currentEmail, ignoreCase = true)
        if (changeEmail && !android.util.Patterns.EMAIL_ADDRESS.matcher(newEmail).matches()) {
            binding.tilNewEmail.error = "Invalid email format"; return
        }
        val changePassword = newPass.isNotEmpty()
        if (changePassword && newPass.length < Validators.MIN_PASSWORD_LENGTH) {
            binding.tilNewPassword.error = "At least ${Validators.MIN_PASSWORD_LENGTH} characters"; return
        }
        if ((changeEmail || changePassword) && currentPass.isEmpty()) {
            binding.tilCurrentPassword.error = "Needed to change email or password"; return
        }

        binding.btnSave.isEnabled = false
        lifecycleScope.launch {
            try {
                val messages = mutableListOf<String>()
                if (changeEmail || changePassword) {
                    if (authManager.reauthenticate(currentPass).isFailure) {
                        binding.tilCurrentPassword.error = "Incorrect password"
                        return@launch
                    }
                    if (changePassword) {
                        authManager.updatePassword(newPass).getOrElse { e ->
                            Toast.makeText(this@AccountActivity, "Couldn't change password: ${e.message}", Toast.LENGTH_LONG).show()
                            return@launch
                        }
                        messages += "Password changed."
                    }
                    if (changeEmail) {
                        // Firebase switches the email only after the link in this message is opened
                        authManager.updateEmail(newEmail).getOrElse { e ->
                            Toast.makeText(this@AccountActivity, "Couldn't change email: ${e.message}", Toast.LENGTH_LONG).show()
                            return@launch
                        }
                        messages += "We sent a link to $newEmail. Your email changes after you open it."
                    }
                }

                firestore.collection("users").document(uid)
                    .update(mapOf("fullname" to newName, "phone" to newPhone))
                    .await()
                messages.add(0, "Profile saved.")

                binding.etCurrentPassword.text?.clear()
                binding.etNewPassword.text?.clear()
                binding.etNewEmail.text?.clear()
                MaterialAlertDialogBuilder(this@AccountActivity)
                    .setTitle("Saved")
                    .setMessage(messages.joinToString("\n\n"))
                    .setPositiveButton("OK", null)
                    .show()
            } catch (e: Exception) {
                Toast.makeText(this@AccountActivity, "Couldn't save: ${e.message}", Toast.LENGTH_LONG).show()
            } finally {
                binding.btnSave.isEnabled = true
            }
        }
    }

    private fun confirmLogout() {
        val ride = if (RideSession.state.value.isRecording) "\n\nYour current ride will be ended and saved." else ""
        MaterialAlertDialogBuilder(this)
            .setTitle("Log out?")
            .setMessage("The helmet will be disconnected.$ride")
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Log out") { _, _ ->
                binding.btnLogout.isEnabled = false
                lifecycleScope.launch {
                    authManager.logout(this@AccountActivity)
                    goToLogin()
                }
            }
            .show()
    }

    private fun confirmDeleteAccount() {
        val passwordLayout = TextInputLayout(
            androidx.appcompat.view.ContextThemeWrapper(this, com.google.android.material.R.style.Widget_Material3_TextInputLayout_OutlinedBox),
            null, 0
        ).apply {
            hint = "Current password"
            endIconMode = TextInputLayout.END_ICON_PASSWORD_TOGGLE
        }
        val passwordField = TextInputEditText(passwordLayout.context).apply {
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
            typeface = android.graphics.Typeface.DEFAULT // password inputType defaults to monospace
        }
        passwordLayout.addView(passwordField)
        val padding = (20 * resources.displayMetrics.density).toInt()
        val container = android.widget.FrameLayout(this).apply {
            setPadding(padding, padding / 2, padding, 0)
            addView(passwordLayout)
        }

        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle("Delete account?")
            .setMessage("This permanently deletes your profile, all saved rides and your emergency contacts. It can't be undone.")
            .setView(container)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Delete", null) // handled below so a wrong password keeps the dialog open
            .show()

        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).apply {
            setTextColor(getColor(R.color.danger_red))
            setOnClickListener {
                val password = passwordField.text?.toString().orEmpty()
                if (password.isEmpty()) {
                    passwordLayout.error = "Enter your password"
                    return@setOnClickListener
                }
                passwordLayout.error = null
                isEnabled = false
                lifecycleScope.launch {
                    authManager.deleteAccount(this@AccountActivity, password)
                        .onSuccess {
                            dialog.dismiss()
                            Toast.makeText(this@AccountActivity, "Your account was deleted", Toast.LENGTH_LONG).show()
                            goToLogin()
                        }
                        .onFailure { e ->
                            isEnabled = true
                            passwordLayout.error = if (e is FirebaseAuthInvalidCredentialsException) "Incorrect password"
                            else "Couldn't delete: ${e.message}"
                        }
                }
            }
        }
    }

    private fun goToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }
}
