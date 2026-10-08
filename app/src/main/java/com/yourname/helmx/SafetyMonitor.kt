package com.yourname.helmx

import android.Manifest
import android.annotation.SuppressLint
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.telephony.SmsManager
import android.media.AudioAttributes
import android.media.Ringtone
import android.media.RingtoneManager
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.google.android.gms.location.LocationServices
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withTimeoutOrNull

/**
 * Watches helmet data app-wide (also while riding with the screen off) and raises alerts:
 *  - drowsiness: alarm sound, vibration and a heads-up notification, after a delay set by the
 *    rider's sensitivity, until the helmet stops reporting drowsiness;
 *  - crash: an urgent notification with "Call" and "Text my location" actions.
 * Started once from [HelmXApplication].
 */
object SafetyMonitor {

    private const val TAG = "SafetyMonitor"
    private const val CHANNEL_ID = "safety_alerts"
    private const val NOTIFICATION_DROWSY = 2001
    private const val NOTIFICATION_CRASH = 2002
    const val FALLBACK_EMERGENCY_NUMBER = "1122" // Rescue 1122 (Punjab emergency service)

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private var started = false

    private var drowsyJob: Job? = null
    private var drowsyAlarmActive = false
    private var ringtone: Ringtone? = null
    private var crashActive = false

    // Automatic response ("Always allow") countdown after a crash
    private var countdownJob: Job? = null
    private var crashIsTest = false
    private val _countdown = MutableStateFlow<Int?>(null)
    /** Seconds left before HelmX texts and calls automatically; null when no countdown runs. */
    val countdown: StateFlow<Int?> = _countdown.asStateFlow()

    /** True once a countdown ran out (contacts alerted), so the Home dialog can close itself. */
    var countdownFinished = false
        private set

    /** Last known position when a crash was reported (for the Home dialog). */
    var lastCrashLocation: Pair<Double, Double>? = null
        private set

    fun start(context: Context) {
        if (started) return
        started = true
        val app = context.applicationContext
        createChannel(app)
        scope.launch {
            HelmetBleManager.getInstance(app).helmetData.collect { onHelmetData(app, it) }
        }
    }

    private fun onHelmetData(context: Context, data: HelmetData) {
        val connected = data.connectionStatus == ConnectionStatus.CONNECTED

        // --- Drowsiness ---
        val drowsy = connected && data.isDrowsy && SafetySettings.isDrowsinessEnabled(context)
        if (drowsy) {
            if (drowsyJob == null && !drowsyAlarmActive) {
                val delayMs = SafetySettings.drowsinessSensitivity(context).delayMs
                drowsyJob = scope.launch {
                    delay(delayMs)
                    drowsyJob = null
                    startDrowsyAlarm(context)
                }
            }
        } else {
            drowsyJob?.cancel()
            drowsyJob = null
            if (drowsyAlarmActive) stopDrowsyAlarm(context)
        }

        // --- Crash ---
        val crash = connected && data.isCrashDetected && SafetySettings.isCrashDetectionEnabled(context)
        if (crash && !crashActive) {
            crashActive = true
            scope.launch { onCrash(context) }
        } else if (!crash) {
            crashActive = false // the notification stays until the rider dismisses it
        }
    }

    // ---------------------------------------------------------------------------------------
    // Drowsiness
    // ---------------------------------------------------------------------------------------

    private fun startDrowsyAlarm(context: Context) {
        drowsyAlarmActive = true
        Log.i(TAG, "Drowsiness alarm on")
        if (SafetySettings.isSoundAlarmsEnabled(context)) {
            playAlarmSound(context)
            vibrate(context)
        }
        notify(
            context, NOTIFICATION_DROWSY,
            NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification_bell)
                .setContentTitle("Drowsiness detected")
                .setContentText("Pull over safely and take a break.")
                .setPriority(NotificationCompat.PRIORITY_MAX)
                .setCategory(NotificationCompat.CATEGORY_ALARM)
                .setOngoing(true)
                .setContentIntent(openAppIntent(context))
        )
    }

    private fun stopDrowsyAlarm(context: Context) {
        drowsyAlarmActive = false
        Log.i(TAG, "Drowsiness alarm off")
        ringtone?.stop()
        ringtone = null
        vibrator(context)?.cancel()
        NotificationManagerCompat.from(context).cancel(NOTIFICATION_DROWSY)
    }

    // ---------------------------------------------------------------------------------------
    // Crash
    // ---------------------------------------------------------------------------------------

    /** Shows the crash alert without a real crash (Settings → Crash alerts → Test). */
    fun showTestCrashAlert(context: Context) {
        scope.launch { onCrash(context.applicationContext, test = true) }
    }

    /** Plays the drowsiness alarm for a few seconds (Settings → Drowsiness → Test). */
    fun testDrowsyAlarm(context: Context, durationMs: Long = 3000) {
        if (drowsyAlarmActive) return
        val app = context.applicationContext
        playAlarmSound(app)
        vibrate(app)
        scope.launch {
            delay(durationMs)
            if (!drowsyAlarmActive) {
                ringtone?.stop()
                ringtone = null
                vibrator(app)?.cancel()
            }
        }
    }

    private suspend fun onCrash(context: Context, test: Boolean = false) {
        Log.i(TAG, if (test) "Test crash alert" else "Crash reported by helmet")
        crashIsTest = test
        lastCrashLocation = lastLocation(context)
        cancelCountdown()
        val auto = SafetySettings.canAutoRespond(context)
        postCrashNotification(context, if (auto) SafetySettings.AUTO_RESPONSE_SECONDS else null)
        vibrate(context, repeat = false)
        if (auto) startCountdown(context)
    }

    private fun startCountdown(context: Context) {
        countdownFinished = false
        countdownJob = scope.launch {
            for (remaining in SafetySettings.AUTO_RESPONSE_SECONDS downTo 1) {
                _countdown.value = remaining
                // Refresh the notification text every 5 s (and each of the last 5 s)
                if (remaining % 5 == 0 || remaining <= 5) postCrashNotification(context, remaining)
                delay(1000)
            }
            countdownFinished = true
            _countdown.value = null
            countdownJob = null
            autoRespond(context)
        }
    }

    private fun cancelCountdown() {
        countdownJob?.cancel()
        countdownJob = null
        _countdown.value = null
    }

    /**
     * The rider responded (I'm OK, or called/texted themselves): stop the countdown.
     * [dismiss] also removes the alert.
     */
    fun onRiderResponded(context: Context, dismiss: Boolean) {
        val wasCounting = countdownJob != null
        cancelCountdown()
        if (dismiss) {
            dismissCrash(context)
        } else if (wasCounting) {
            postCrashNotification(context, null) // same alert, without the countdown text
        }
    }

    /** No response in time: text the location to every contact, then call the primary contact. */
    @SuppressLint("MissingPermission") // checked by canAutoRespond()
    private fun autoRespond(context: Context) {
        val contacts = SafetySettings.cachedContacts(context)
        val primary = contacts.firstOrNull()
        if (crashIsTest) {
            Log.i(TAG, "Test: auto response would run now (nothing sent)")
            postInfo(
                context, if (primary == null) "Test finished" else "Test finished: nothing was sent",
                "In a real crash HelmX would now text your location to ${contacts.joinToString { it.name }} and call ${primary?.name ?: "your contact"}."
            )
            return
        }
        if (!SafetySettings.canAutoRespond(context) || primary == null) return

        val (lat, lng) = lastCrashLocation ?: (null to null)
        val message = EmergencyActions.alertMessage(lat, lng)
        var sent = 0
        contacts.forEach { contact ->
            try {
                val sms = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    context.getSystemService(SmsManager::class.java)
                } else {
                    @Suppress("DEPRECATION") SmsManager.getDefault()
                }
                sms.sendMultipartTextMessage(contact.phone, null, sms.divideMessage(message), null, null)
                sent++
            } catch (e: Exception) {
                Log.e(TAG, "Auto SMS to ${contact.phone} failed", e)
            }
        }

        // Android may block starting a call while HelmX is in the background; the SMS above
        // does not depend on that. The notification below always offers a one-tap call.
        val called = try {
            context.startActivity(
                Intent(Intent.ACTION_CALL, Uri.parse("tel:${Uri.encode(primary.phone)}"))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            )
            true
        } catch (e: Exception) {
            Log.e(TAG, "Auto call failed", e)
            false
        }

        val text = buildString {
            append(if (sent > 0) "Your location was texted to ${contacts.take(sent).joinToString { it.name }}. " else "Texting your location failed. ")
            append(if (called) "Calling ${primary.name}." else "Tap to call ${primary.name}.")
        }
        Log.i(TAG, "Auto response: sms=$sent called=$called")
        postInfo(context, "Emergency contacts alerted", text, callNumber = primary.phone)
    }

    private fun postCrashNotification(context: Context, secondsLeft: Int?) {
        val contacts = SafetySettings.cachedContacts(context)
        val first = contacts.firstOrNull()
        val autoAllowed = SafetySettings.canAutoRespond(context)

        val body = when {
            secondsLeft != null && first != null ->
                "Are you OK? If you don't respond, HelmX will text your location and call ${first.name} in $secondsLeft s."
            contacts.isEmpty() -> "Are you OK? No emergency contact is set, so Call opens Rescue $FALLBACK_EMERGENCY_NUMBER."
            else -> "Are you OK? Call ${first!!.name} or text your location to your emergency contacts."
        }
        val builder = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle(if (crashIsTest) "Test: crash detected" else "Crash detected")
            .setContentText(if (secondsLeft != null) "Auto-alert in $secondsLeft s. Tap I'm OK to cancel." else "Are you OK? Tap to call or text for help.")
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setOnlyAlertOnce(true) // countdown updates shouldn't buzz again
            .setAutoCancel(false)
            .setContentIntent(openAppIntent(context))

        // Android shows at most 3 action buttons
        if (secondsLeft != null) {
            builder.addAction(0, "I'm OK", CrashActionActivity.pendingIntent(context, CrashActionActivity.ACTION_OK))
        }
        // Short labels: three buttons share one row (the body text names the contact)
        val callLabel = if (first != null) "Call" else "Call $FALLBACK_EMERGENCY_NUMBER"
        builder.addAction(0, callLabel, CrashActionActivity.pendingIntent(context, CrashActionActivity.ACTION_CALL))
        if (contacts.isNotEmpty()) {
            builder.addAction(0, "Send location", CrashActionActivity.pendingIntent(context, CrashActionActivity.ACTION_TEXT))
        }
        if (secondsLeft == null && !autoAllowed && contacts.isNotEmpty()) {
            builder.addAction(0, "Always allow", CrashActionActivity.pendingIntent(context, CrashActionActivity.ACTION_ALLOW))
        }
        notify(context, NOTIFICATION_CRASH, builder)
    }

    private fun postInfo(context: Context, title: String, text: String, callNumber: String? = null) {
        val builder = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(openAppIntent(context))
        if (callNumber != null) {
            builder.addAction(0, "Call now", activityIntent(context, 3, EmergencyActions.dialIntent(callNumber)))
        }
        notify(context, NOTIFICATION_CRASH, builder)
    }

    fun dismissCrash(context: Context) {
        NotificationManagerCompat.from(context).cancel(NOTIFICATION_CRASH)
    }

    @SuppressLint("MissingPermission")
    private suspend fun lastLocation(context: Context): Pair<Double, Double>? {
        val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
        if (!granted) return null
        return try {
            withTimeoutOrNull(3000) {
                LocationServices.getFusedLocationProviderClient(context).lastLocation.await()
            }?.let { it.latitude to it.longitude }
        } catch (e: Exception) {
            null
        }
    }

    // ---------------------------------------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------------------------------------

    private fun createChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(CHANNEL_ID, "Safety alerts", NotificationManager.IMPORTANCE_HIGH).apply {
            description = "Drowsiness and crash alerts from your helmet"
            enableVibration(true)
        }
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    @SuppressLint("MissingPermission") // checked: without POST_NOTIFICATIONS the alert is sound/vibration only
    private fun notify(context: Context, id: Int, builder: NotificationCompat.Builder) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            Log.w(TAG, "Notification permission not granted; alert not shown as notification")
            return
        }
        NotificationManagerCompat.from(context).notify(id, builder.build())
    }

    private fun openAppIntent(context: Context): PendingIntent = PendingIntent.getActivity(
        context, 0,
        Intent(context, DashboardActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_REORDER_TO_FRONT),
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
    )

    private fun activityIntent(context: Context, requestCode: Int, intent: Intent): PendingIntent =
        PendingIntent.getActivity(
            context, requestCode, intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

    private fun playAlarmSound(context: Context) {
        val uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
        ringtone = RingtoneManager.getRingtone(context, uri)?.apply {
            audioAttributes = AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).build()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) isLooping = true
            play()
        }
    }

    private fun vibrator(context: Context): Vibrator? =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            context.getSystemService(VibratorManager::class.java)?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        }

    private fun vibrate(context: Context, repeat: Boolean = true) {
        val pattern = longArrayOf(0, 700, 400, 700, 400)
        val v = vibrator(context) ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            v.vibrate(VibrationEffect.createWaveform(pattern, if (repeat) 0 else -1))
        } else {
            @Suppress("DEPRECATION")
            v.vibrate(pattern, if (repeat) 0 else -1)
        }
    }
}
