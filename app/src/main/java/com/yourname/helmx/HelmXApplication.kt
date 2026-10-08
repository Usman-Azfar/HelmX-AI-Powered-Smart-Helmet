package com.yourname.helmx

import android.app.Application

class HelmXApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // Apply the saved theme once, before any activity is created
        AppSettings.applySavedTheme(this)
        // Drowsiness / crash alerts work on every screen and while riding with the screen off
        SafetyMonitor.start(this)
    }
}
