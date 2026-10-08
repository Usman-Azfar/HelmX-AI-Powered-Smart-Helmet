package com.yourname.helmx

import android.content.Context
import androidx.appcompat.app.AppCompatDelegate

/** Single source of truth for user preferences stored in SharedPreferences. */
object AppSettings {

    private const val PREFS_NAME = "HelmXSettings"
    private const val KEY_DARK_MODE = "dark_mode"
    private const val DEFAULT_DARK_MODE = true

    fun isDarkMode(context: Context): Boolean =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getBoolean(KEY_DARK_MODE, DEFAULT_DARK_MODE)

    fun setDarkMode(context: Context, enabled: Boolean) {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit().putBoolean(KEY_DARK_MODE, enabled).apply()
        applyTheme(enabled)
    }

    fun applySavedTheme(context: Context) = applyTheme(isDarkMode(context))

    private fun applyTheme(darkMode: Boolean) {
        AppCompatDelegate.setDefaultNightMode(
            if (darkMode) AppCompatDelegate.MODE_NIGHT_YES else AppCompatDelegate.MODE_NIGHT_NO
        )
    }
}
