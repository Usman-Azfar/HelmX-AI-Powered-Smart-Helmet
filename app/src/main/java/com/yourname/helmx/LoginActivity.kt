package com.yourname.helmx

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.yourname.helmx.databinding.ActivityLoginBinding
import kotlinx.coroutines.launch

class LoginActivity : AppCompatActivity() {

    // ViewBinding - type-safe access to views
    private lateinit var binding: ActivityLoginBinding

    // AuthManager instance
    private val authManager = AuthManager()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Launcher icon tapped while the app is already running: just bring the existing
        // task (Dashboard, Navigation, ...) back instead of restarting it.
        if (!isTaskRoot && intent.hasCategory(Intent.CATEGORY_LAUNCHER) && intent.action == Intent.ACTION_MAIN) {
            finish()
            return
        }

        // Check if user is already logged in (before inflating, to avoid a flash of the login form)
        if (authManager.isUserLoggedIn()) {
            navigateToDashboard()
            return
        }

        // Initialize ViewBinding
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupClickListeners()
    }

    private fun setupClickListeners() {
        // Login button click
        binding.btnLogin.setOnClickListener {
            val email = binding.etEmail.text.toString().trim()
            val password = binding.etPassword.text.toString().trim()

            // Validate inputs
            if (validateLoginInputs(email, password)) {
                performLogin(email, password)
            }
        }

        // Sign up text click
        binding.tvSignUp.setOnClickListener {
            val intent = Intent(this, SignUpActivity::class.java)
            startActivity(intent)
        }


        // Forgot password click
        binding.tvForgotPassword.setOnClickListener {
            val email = binding.etEmail.text.toString().trim()
            if (email.isEmpty()) {
                binding.tilEmail.error = "Enter your email to reset password"
                binding.etEmail.requestFocus()
                return@setOnClickListener
            }
            binding.tilEmail.error = null
            
            lifecycleScope.launch {
                val result = authManager.sendPasswordResetEmail(email)
                result.fold(
                    onSuccess = {
                        Toast.makeText(this@LoginActivity, "Reset link sent to $email", Toast.LENGTH_LONG).show()
                    },
                    onFailure = { exception ->
                        Toast.makeText(this@LoginActivity, "Error: ${exception.message}", Toast.LENGTH_LONG).show()
                    }
                )
            }
        }
    }

    private fun validateLoginInputs(email: String, password: String): Boolean {
        // Check if email is empty
        if (email.isEmpty()) {
            binding.tilEmail.error = "Email is required"
            return false
        }

        // Check if email is valid format
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            binding.tilEmail.error = "Invalid email format"
            return false
        }

        // Clear email error
        binding.tilEmail.error = null

        // Check if password is empty
        if (password.isEmpty()) {
            binding.tilPassword.error = "Password is required"
            return false
        }

        // Check password length
        if (password.length < Validators.MIN_PASSWORD_LENGTH) {
            binding.tilPassword.error = "Password must be at least ${Validators.MIN_PASSWORD_LENGTH} characters"
            return false
        }

        // Clear password error
        binding.tilPassword.error = null

        return true
    }

    private fun performLogin(email: String, password: String) {
        // Disable button to prevent multiple clicks
        binding.btnLogin.isEnabled = false
        binding.btnLogin.text = "Logging in..."

        // Launch coroutine for async operation
        lifecycleScope.launch {
            // Call AuthManager sign in method
            val result = authManager.signInWithEmail(email, password)

            // Handle result
            result.fold(
                onSuccess = { uid ->
                    // Login successful
                    Toast.makeText(
                        this@LoginActivity,
                        "Welcome back!",
                        Toast.LENGTH_SHORT
                    ).show()

                    navigateToDashboard()
                },
                onFailure = { exception ->
                    // Login failed
                    val errorMessage = authErrorMessage(exception, "Login")

                    Toast.makeText(
                        this@LoginActivity,
                        errorMessage,
                        Toast.LENGTH_LONG
                    ).show()

                    // Re-enable button
                    binding.btnLogin.isEnabled = true
                    binding.btnLogin.text = "Log In"
                }
            )
        }
    }

    private fun navigateToDashboard() {
        val intent = Intent(this, DashboardActivity::class.java)
        // Clear back stack so user can't go back to login
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }
}