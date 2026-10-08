package com.yourname.helmx

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.Looper
import android.util.Log
import android.widget.Toast
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import androidx.core.content.ContextCompat
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.firebase.auth.FirebaseAuth
import java.util.Locale

/**
 * Records a ride in a foreground service (type "location") so GPS tracking continues while the
 * screen is off or the app is in the background. Started while the app is visible, it keeps
 * "while in use" location access, so background-location permission is not needed.
 */
class RideTrackingService : Service() {

    companion object {
        private const val TAG = "RideTrackingService"
        private const val CHANNEL_ID = "ride_tracking"
        private const val NOTIFICATION_ID = 1001

        private const val ACTION_START = "com.yourname.helmx.action.START_RIDE"
        private const val ACTION_STOP = "com.yourname.helmx.action.STOP_RIDE"
        private const val EXTRA_DESTINATION = "destination"
        private const val EXTRA_DEST_LAT = "dest_lat"
        private const val EXTRA_DEST_LNG = "dest_lng"
        private const val EXTRA_START_LAT = "start_lat"
        private const val EXTRA_START_LNG = "start_lng"

        fun start(
            context: Context,
            destination: String,
            destLat: Double?,
            destLng: Double?,
            startLat: Double,
            startLng: Double
        ) {
            val intent = Intent(context, RideTrackingService::class.java).apply {
                action = ACTION_START
                putExtra(EXTRA_DESTINATION, destination)
                destLat?.let { putExtra(EXTRA_DEST_LAT, it) }
                destLng?.let { putExtra(EXTRA_DEST_LNG, it) }
                putExtra(EXTRA_START_LAT, startLat)
                putExtra(EXTRA_START_LNG, startLng)
            }
            ContextCompat.startForegroundService(context, intent)
        }

        fun stop(context: Context) {
            if (!RideSession.state.value.isRecording) return
            context.startService(Intent(context, RideTrackingService::class.java).setAction(ACTION_STOP))
        }
    }

    private val tracker = RideTracker()
    private val rideRepository = RideRepository()
    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private var lastNotifiedTenthKm = -1L

    // Captured at start so the ride is saved to the right user even if they log out meanwhile
    private var riderUid: String? = null

    private val locationCallback = object : LocationCallback() {
        override fun onLocationResult(result: LocationResult) {
            for (location in result.locations) {
                tracker.addFix(location.latitude, location.longitude, location.accuracy)
            }
            val distanceKm = tracker.distanceKm
            RideSession.set(RideSession.state.value.copy(distanceKm = distanceKm))
            // Refresh the notification only when the shown value (0.1 km steps) changes
            val tenths = (distanceKm * 10).toLong()
            if (tenths != lastNotifiedTenthKm) {
                lastNotifiedTenthKm = tenths
                getSystemService(NotificationManager::class.java)
                    .notify(NOTIFICATION_ID, buildNotification(RideSession.state.value))
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
        createNotificationChannel()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startRide(intent)
            ACTION_STOP -> stopRide()
            else -> stopSelf() // e.g. unexpected restart with no ride to resume
        }
        return START_NOT_STICKY
    }

    private fun startRide(intent: Intent) {
        if (tracker.isTracking) return // already recording

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
            != PackageManager.PERMISSION_GRANTED
        ) {
            Log.e(TAG, "Location permission missing; cannot record ride")
            stopSelf()
            return
        }

        val state = RideState(
            isRecording = true,
            destination = intent.getStringExtra(EXTRA_DESTINATION).orEmpty(),
            destLat = intent.takeIf { it.hasExtra(EXTRA_DEST_LAT) }?.getDoubleExtra(EXTRA_DEST_LAT, 0.0),
            destLng = intent.takeIf { it.hasExtra(EXTRA_DEST_LNG) }?.getDoubleExtra(EXTRA_DEST_LNG, 0.0)
        )

        try {
            ServiceCompat.startForeground(
                this,
                NOTIFICATION_ID,
                buildNotification(state),
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION else 0
            )
        } catch (e: Exception) {
            // e.g. started while the app was not in the foreground
            Log.e(TAG, "Could not start foreground ride tracking", e)
            stopSelf()
            return
        }

        riderUid = FirebaseAuth.getInstance().currentUser?.uid
        tracker.start(state.destination)
        val startLat = intent.getDoubleExtra(EXTRA_START_LAT, 0.0)
        val startLng = intent.getDoubleExtra(EXTRA_START_LNG, 0.0)
        // Seed the start point so distance is measured from where the ride began
        if (startLat != 0.0 || startLng != 0.0) tracker.addFix(startLat, startLng, 0f)
        lastNotifiedTenthKm = 0
        RideSession.set(state)

        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 5000).build()
        fusedLocationClient.requestLocationUpdates(request, locationCallback, Looper.getMainLooper())
    }

    private fun stopRide() {
        finishRide()
        ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    /** Stops tracking and saves the ride (if long enough). Safe to call more than once. */
    private fun finishRide() {
        if (!tracker.isTracking) return
        fusedLocationClient.removeLocationUpdates(locationCallback)
        val ride = tracker.stop()

        val appContext = applicationContext
        val message = when {
            ride == null -> "Ride too short to save"
            rideRepository.saveRide(ride, riderUid) { e ->
                Toast.makeText(appContext, "Couldn't save ride: ${e.message}", Toast.LENGTH_LONG).show()
            } -> String.format(Locale.getDefault(), "Ride saved: %.1f km", ride.distanceKm)
            else -> "Could not save ride (not logged in)"
        }
        // Cleared only after the save is queued: logout waits for this before signing out
        RideSession.set(RideState())
        Toast.makeText(appContext, message, Toast.LENGTH_SHORT).show()
    }

    override fun onDestroy() {
        // Service killed while recording: keep what was measured
        finishRide()
        super.onDestroy()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(CHANNEL_ID, "Ride recording", NotificationManager.IMPORTANCE_LOW).apply {
            description = "Shown while HelmX is recording a ride"
        }
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    private fun buildNotification(state: RideState): Notification {
        val openIntent = PendingIntent.getActivity(
            this, 0,
            Intent(this, NavigationActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_REORDER_TO_FRONT),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val stopIntent = PendingIntent.getService(
            this, 1,
            Intent(this, RideTrackingService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val title = if (state.destination.isBlank()) "Recording ride" else "Riding to ${state.destination}"
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_motorcycle)
            .setContentTitle(title)
            .setContentText(String.format(Locale.getDefault(), "%.1f km so far", state.distanceKm))
            .setContentIntent(openIntent)
            .addAction(0, "Stop ride", stopIntent)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
            .build()
    }
}
