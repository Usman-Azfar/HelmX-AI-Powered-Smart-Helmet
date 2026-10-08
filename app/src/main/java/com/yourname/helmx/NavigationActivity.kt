package com.yourname.helmx

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.location.Location
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.os.Build
import android.os.Bundle
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.text.Editable
import android.text.TextWatcher
import android.view.View
import android.view.WindowManager
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.result.IntentSenderRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.google.android.gms.common.api.ResolvableApiException
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.LocationSettingsRequest
import com.google.android.gms.location.Priority
import com.yourname.helmx.databinding.ActivityNavigationBinding
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import org.json.JSONArray
import java.text.DateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.roundToInt

class NavigationActivity : AppCompatActivity(), TextToSpeech.OnInitListener {

    companion object {
        private const val KEY_LAST_DESTINATION = "last_handled_destination"
        private const val BROWSE_INTERVAL_MS = 5000L
        private const val NAV_INTERVAL_MS = 1000L
        private const val REROUTE_MIN_INTERVAL_MS = 10_000L
        private const val SEARCH_DEBOUNCE_MS = 350L
        private const val MAP_LOAD_TIMEOUT_MS = 15_000L
        private const val FAR_PROMPT_M = 400.0
        private const val NEAR_PROMPT_M = 40.0
    }

    private lateinit var binding: ActivityNavigationBinding
    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private var speechRecognizer: SpeechRecognizer? = null
    private lateinit var textToSpeech: TextToSpeech
    private var ttsReady = false

    // --- Location ---
    private var currentLat = 0.0
    private var currentLng = 0.0
    private var hasLocation = false
    private var lastBearing = -1.0
    private var locationCallback: LocationCallback? = null
    private var locationIntervalMs = 0L
    private var askedForLocationPermission = false
    private var isResolvingLocationSettings = false
    private var declinedLocationSettings = false

    // --- Map bridge (WebView) ---
    private var mapReady = false
    private val pendingJs = mutableListOf<String>()

    // --- Search ---
    private lateinit var suggestionAdapter: PlaceSuggestionAdapter
    private var searchJob: Job? = null
    private var suppressSuggestions = false
    // Text chosen from a suggestion / set by the app; don't look it up again
    private var settledQuery: String? = null
    private lateinit var recentPlaces: RecentPlaces

    // --- Offline ---
    private lateinit var offlineMapServer: OfflineMapServer
    private lateinit var connectivityManager: ConnectivityManager
    private var isOffline = false
    private var offlineRerouteWarned = false
    private val networkCallback = object : ConnectivityManager.NetworkCallback() {
        override fun onCapabilitiesChanged(network: Network, capabilities: NetworkCapabilities) {
            runOnUiThread { updateOfflineState() }
        }
        override fun onLost(network: Network) {
            runOnUiThread { updateOfflineState() }
        }
    }

    // --- Route & guidance ---
    private var destinationName = ""
    private var lastDestLat: Double? = null
    private var lastDestLng: Double? = null
    private var currentRoute: Route? = null
    private var guide: NavigationGuide? = null
    private var routeJob: Job? = null
    private var isNavigating = false
    private var autoStartWhenRouted = false     // helmet destination / restored ride
    private var restoreRideRoute = false        // screen recreated during a ride
    private var lastRerouteAt = 0L
    private var promptedStep = -1
    private var farPromptDone = false
    private var nearPromptDone = false

    // --- Helmet-sent destination ---
    private var lastHandledDestination = ""
    private var pendingDestinationQuery: String? = null   // waiting for the first GPS fix

    private val locationPermissionRequest = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        if (permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
            permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        ) {
            checkLocationSettings()
        } else {
            Toast.makeText(this, "Location permission is needed to show where you are", Toast.LENGTH_LONG).show()
        }
    }

    private val locationSettingsLauncher = registerForActivityResult(
        ActivityResultContracts.StartIntentSenderForResult()
    ) { result ->
        isResolvingLocationSettings = false
        if (result.resultCode == RESULT_OK) {
            startLocationUpdates(currentInterval())
        } else {
            declinedLocationSettings = true // don't nag again on every resume
            Toast.makeText(this, "Turn on Location to navigate", Toast.LENGTH_SHORT).show()
        }
    }

    private val micPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) startVoiceSearch()
        else Toast.makeText(this, "Microphone permission is needed for voice search", Toast.LENGTH_SHORT).show()
    }

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* Recording works either way; the permission only makes the ride notification visible */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityNavigationBinding.inflate(layoutInflater)
        setContentView(binding.root)

        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
        textToSpeech = TextToSpeech(this, this)
        lastHandledDestination = savedInstanceState?.getString(KEY_LAST_DESTINATION, "") ?: ""
        recentPlaces = RecentPlaces(this)
        offlineMapServer = OfflineMapServer(assets)
        connectivityManager = getSystemService(ConnectivityManager::class.java)
        isOffline = !isOnlineNow()

        setupWebView()
        setupSearch()
        setupButtons()
        setupBottomNavigation()
        observeHelmetData()
        observeRideSession()
        restoreRideIfRecording()
        updateOfflineBadge()

        // Tell the map which parts of it are covered by the search bar / banner / bottom card
        listOf(binding.cardSearch, binding.cardManeuver, binding.cardRoute).forEach { view ->
            view.addOnLayoutChangeListener { _, _, _, _, _, _, _, _, _ -> updateMapInsets() }
        }
    }

    override fun onStart() {
        super.onStart()
        connectivityManager.registerDefaultNetworkCallback(networkCallback)
        updateOfflineState()
    }

    override fun onResume() {
        super.onResume()
        binding.bottomNavigation.selectedItemId = R.id.nav_navigation
        if (!isResolvingLocationSettings) ensureLocation()
    }

    override fun onStop() {
        super.onStop()
        runCatching { connectivityManager.unregisterNetworkCallback(networkCallback) }
        // Map updates only; ride distance keeps being measured by RideTrackingService
        stopLocationUpdates()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putString(KEY_LAST_DESTINATION, lastHandledDestination)
    }

    override fun onDestroy() {
        stopLocationUpdates()
        searchJob?.cancel()
        routeJob?.cancel()
        if (::textToSpeech.isInitialized) {
            textToSpeech.stop()
            textToSpeech.shutdown()
        }
        speechRecognizer?.destroy()
        speechRecognizer = null
        binding.webViewMap.destroy()
        super.onDestroy()
    }

    // ------------------------------------------------------------------------------------
    // Map (MapLibre GL in a WebView)
    // ------------------------------------------------------------------------------------

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        binding.webViewMap.settings.javaScriptEnabled = true
        binding.webViewMap.settings.domStorageEnabled = true
        binding.webViewMap.webViewClient = object : WebViewClient() {
            // Serves the page, MapLibre and the offline Lahore map from the app's assets
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? =
                offlineMapServer.handle(request.url)
        }
        binding.webViewMap.webChromeClient = WebChromeClient()
        binding.webViewMap.addJavascriptInterface(MapBridge(), "Android")
        val dark = if (isDarkTheme()) 1 else 0
        val offline = if (isOffline) 1 else 0
        binding.webViewMap.loadUrl("${OfflineMapServer.MAP_URL}?dark=$dark&offline=$offline")

        // The map libraries and tiles come from the internet
        binding.webViewMap.postDelayed({
            if (!mapReady && !isFinishing) {
                Toast.makeText(this, "Map couldn't load. Check your internet connection.", Toast.LENGTH_LONG).show()
            }
        }, MAP_LOAD_TIMEOUT_MS)
    }

    /** Runs JavaScript on the map, queueing it until the page has finished loading. */
    private fun runJs(script: String) {
        if (mapReady) binding.webViewMap.evaluateJavascript(script, null) else pendingJs += script
    }

    private fun isDarkTheme() =
        (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES

    private fun updateMapInsets() {
        val density = resources.displayMetrics.density
        val mapTop = binding.webViewMap.top
        val topView = when {
            binding.cardManeuver.visibility == View.VISIBLE -> binding.cardManeuver
            binding.cardSearch.visibility == View.VISIBLE -> binding.cardSearch
            else -> null
        }
        val top = topView?.let { (it.bottom - mapTop) / density } ?: 0f
        val bottom = if (binding.cardRoute.visibility == View.VISIBLE)
            (binding.webViewMap.bottom - binding.cardRoute.top) / density else 0f
        runJs("setInsets(${top.roundToInt()}, ${bottom.coerceAtLeast(0f).roundToInt()})")
    }

    inner class MapBridge {
        @JavascriptInterface
        fun onMapReady() {
            runOnUiThread {
                mapReady = true
                binding.webViewMap.evaluateJavascript("setTheme(${isDarkTheme()}); setOffline($isOffline)", null)
                pendingJs.forEach { binding.webViewMap.evaluateJavascript(it, null) }
                pendingJs.clear()
                updateMapInsets()
            }
        }

        @JavascriptInterface
        fun onFollowChanged(following: Boolean) {
            runOnUiThread {
                binding.btnRecenter.visibility = if (!following && isNavigating) View.VISIBLE else View.GONE
            }
        }
    }

    // ------------------------------------------------------------------------------------
    // Offline
    // ------------------------------------------------------------------------------------

    private fun isOnlineNow(): Boolean {
        val capabilities = connectivityManager.getNetworkCapabilities(connectivityManager.activeNetwork) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }

    private fun updateOfflineState() {
        val offline = !isOnlineNow()
        if (offline == isOffline) return
        isOffline = offline
        runJs("setOffline($offline)") // switch between live tiles and the bundled Lahore map
        updateOfflineBadge()
        if (!offline) {
            // Back online: retry a destination that arrived while offline (e.g. from the helmet)
            pendingDestinationQuery?.let { query ->
                if (hasLocation) {
                    pendingDestinationQuery = null
                    searchAndRoute(query)
                }
            }
        }
    }

    private fun updateOfflineBadge() {
        binding.tvOfflineBadge.visibility =
            if (isOffline && binding.cardSearch.visibility == View.VISIBLE) View.VISIBLE else View.GONE
    }

    // ------------------------------------------------------------------------------------
    // Location
    // ------------------------------------------------------------------------------------

    private fun hasLocationPermission() =
        ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED

    private fun ensureLocation() {
        when {
            hasLocationPermission() -> checkLocationSettings()
            !askedForLocationPermission -> {
                askedForLocationPermission = true
                locationPermissionRequest.launch(
                    arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
                )
            }
        }
    }

    private fun currentInterval() = if (isNavigating) NAV_INTERVAL_MS else BROWSE_INTERVAL_MS

    private fun checkLocationSettings() {
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, currentInterval()).build()
        LocationServices.getSettingsClient(this)
            .checkLocationSettings(LocationSettingsRequest.Builder().addLocationRequest(request).build())
            .addOnSuccessListener { startLocationUpdates(currentInterval()) }
            .addOnFailureListener { e ->
                if (e is ResolvableApiException && !declinedLocationSettings && !isResolvingLocationSettings) {
                    isResolvingLocationSettings = true
                    locationSettingsLauncher.launch(IntentSenderRequest.Builder(e.resolution).build())
                } else {
                    // Settings can't be fixed from here; still try with what is available
                    startLocationUpdates(currentInterval())
                }
            }
    }

    @SuppressLint("MissingPermission")
    private fun startLocationUpdates(intervalMs: Long) {
        if (!hasLocationPermission() || isFinishing || isDestroyed) return
        if (locationCallback != null && locationIntervalMs == intervalMs) return
        stopLocationUpdates()

        val callback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation?.let { onNewLocation(it) }
            }
        }
        locationCallback = callback
        locationIntervalMs = intervalMs
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, intervalMs).build()
        fusedLocationClient.requestLocationUpdates(request, callback, Looper.getMainLooper())

        // Show the last known position straight away instead of waiting for a fresh fix
        if (!hasLocation) fusedLocationClient.lastLocation.addOnSuccessListener { it?.let(::onNewLocation) }
    }

    private fun stopLocationUpdates() {
        locationCallback?.let { fusedLocationClient.removeLocationUpdates(it) }
        locationCallback = null
    }

    private fun onNewLocation(location: Location) {
        val previousLat = currentLat
        val previousLng = currentLng
        val hadLocation = hasLocation
        currentLat = location.latitude
        currentLng = location.longitude
        hasLocation = true

        // Heading: from the GPS when moving, otherwise from the last two fixes
        lastBearing = when {
            location.hasBearing() && location.speed > 1f -> location.bearing.toDouble()
            hadLocation && RideTracker.haversineMeters(previousLat, previousLng, currentLat, currentLng) > 3 ->
                NavigationGuide.bearingDegrees(previousLat, previousLng, currentLat, currentLng)
            else -> lastBearing
        }
        runJs("updateLocation($currentLat, $currentLng, ${location.accuracy}, ${lastBearing.roundToInt()})")

        if (isNavigating && location.hasSpeed()) {
            binding.tvSpeed.text = (location.speed * 3.6f).roundToInt().toString()
        }

        if (restoreRideRoute) {
            restoreRideRoute = false
            val lat = lastDestLat
            val lng = lastDestLng
            if (lat != null && lng != null) {
                autoStartWhenRouted = true
                requestRoute(lat, lng, destinationName)
            }
        }
        pendingDestinationQuery?.let { query ->
            pendingDestinationQuery = null
            searchAndRoute(query)
        }
        if (isNavigating) updateGuidance()
    }

    // ------------------------------------------------------------------------------------
    // Search
    // ------------------------------------------------------------------------------------

    private fun setupSearch() {
        suggestionAdapter = PlaceSuggestionAdapter(this)
        binding.etSearch.setAdapter(suggestionAdapter)

        binding.etSearch.addTextChangedListener(object : TextWatcher {
            override fun afterTextChanged(s: Editable?) {
                val query = s?.toString()?.trim().orEmpty()
                binding.btnClear.visibility = if (query.isEmpty()) View.GONE else View.VISIBLE
                binding.btnVoice.visibility = if (query.isEmpty()) View.VISIBLE else View.GONE
                if (suppressSuggestions || query == settledQuery) return
                settledQuery = null

                searchJob?.cancel()
                val recents = recentPlaces.matching(query)
                if (query.length < 3 || isOffline) {
                    // Short query or no internet: recent places only (they are stored on the phone)
                    showSuggestions(recents)
                    return
                }
                searchJob = lifecycleScope.launch {
                    delay(SEARCH_DEBOUNCE_MS) // wait until the rider pauses typing
                    val near = if (hasLocation) currentLat to currentLng else null
                    MapsApi.searchPlaces(query, near?.first, near?.second)
                        .onSuccess { places ->
                            // Matching recents first, then search results not already listed
                            val top = recents.take(3)
                            showSuggestions(top + places.filterNot { p -> top.any { it.name == p.name && it.address == p.address } })
                        }
                        .onFailure { e ->
                            android.util.Log.w("NavigationActivity", "Place search failed", e)
                            showSuggestions(recents)
                        }
                }
            }
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
        })

        binding.etSearch.setOnItemClickListener { _, _, position, _ ->
            val place = suggestionAdapter.getItem(position) ?: return@setOnItemClickListener
            searchJob?.cancel()
            setSearchText(place.name)
            hideKeyboard()
            requestRoute(place.lat, place.lng, place.name, place.address)
        }

        // Tapping the empty search bar shows recent destinations (works offline too).
        // Click as well as focus: the box often already has focus when the screen opens.
        binding.etSearch.setOnFocusChangeListener { _, hasFocus ->
            if (hasFocus && binding.etSearch.text.isNullOrBlank()) showSuggestions(recentPlaces.all())
        }
        binding.etSearch.setOnClickListener {
            if (binding.etSearch.text.isNullOrBlank()) showSuggestions(recentPlaces.all())
        }

        binding.etSearch.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                val query = binding.etSearch.text.toString().trim()
                if (query.isNotEmpty()) {
                    hideKeyboard()
                    searchAndRoute(query)
                }
                true
            } else false
        }
    }

    private fun showSuggestions(places: List<PlaceSuggestion>) {
        suggestionAdapter.setItems(places)
        if (places.isNotEmpty() && binding.cardSearch.visibility == View.VISIBLE) {
            // Posted: AutoCompleteTextView reacts to the data change by hiding the list when the
            // text is empty (below its threshold); showing it afterwards keeps recents visible
            binding.etSearch.post { binding.etSearch.showDropDown() }
        } else {
            binding.etSearch.dismissDropDown()
        }
    }

    /** Sets the search text without triggering a new suggestions lookup. */
    private fun setSearchText(text: String) {
        settledQuery = text.trim()
        suppressSuggestions = true
        binding.etSearch.setText(text, false) // false: don't run the drop-down filter
        binding.etSearch.setSelection(binding.etSearch.text.length)
        binding.etSearch.dismissDropDown()
        suggestionAdapter.setItems(emptyList())
        suppressSuggestions = false
    }

    /** Looks up [query] and routes to the best match (typed search, voice, helmet). */
    private fun searchAndRoute(query: String) {
        if (!hasLocation) {
            pendingDestinationQuery = query
            Toast.makeText(this, "Waiting for your location...", Toast.LENGTH_SHORT).show()
            ensureLocation()
            return
        }
        if (isOffline) {
            // Retried automatically when the connection comes back (e.g. helmet destinations)
            pendingDestinationQuery = query
            Toast.makeText(this, "No internet. Search and directions need a connection.", Toast.LENGTH_LONG).show()
            return
        }
        searchJob?.cancel()
        searchJob = lifecycleScope.launch {
            MapsApi.searchPlaces(query, currentLat, currentLng)
                .onSuccess { places ->
                    val best = places.firstOrNull()
                    if (best == null) {
                        autoStartWhenRouted = false
                        Toast.makeText(this@NavigationActivity, "No results for \"$query\"", Toast.LENGTH_SHORT).show()
                    } else {
                        setSearchText(best.name)
                        requestRoute(best.lat, best.lng, best.name, best.address)
                    }
                }
                .onFailure {
                    autoStartWhenRouted = false
                    Toast.makeText(this@NavigationActivity, "Search failed. Check your connection.", Toast.LENGTH_SHORT).show()
                }
        }
    }

    private fun hideKeyboard() {
        val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        imm.hideSoftInputFromWindow(binding.etSearch.windowToken, 0)
        binding.etSearch.clearFocus()
    }

    // ------------------------------------------------------------------------------------
    // Routing
    // ------------------------------------------------------------------------------------

    private fun requestRoute(destLat: Double, destLng: Double, name: String, address: String = "") {
        if (!hasLocation) {
            Toast.makeText(this, "Waiting for your location...", Toast.LENGTH_SHORT).show()
            ensureLocation()
            return
        }
        lastDestLat = destLat
        lastDestLng = destLng
        destinationName = name
        if (name.isNotBlank()) recentPlaces.add(PlaceSuggestion(name, address, destLat, destLng))

        routeJob?.cancel()
        if (isOffline) {
            runJs("showPlace($destLat, $destLng)") // the offline map can still show where it is
            onRouteFailed("No internet. Directions need a connection.")
            return
        }
        routeJob = lifecycleScope.launch {
            MapsApi.fetchRoute(currentLat, currentLng, destLat, destLng)
                .onSuccess { route -> onRouteReady(route, destLat, destLng) }
                .onFailure { e ->
                    onRouteFailed(e.message?.takeIf { it.startsWith("No route") } ?: "Couldn't get directions. Check your connection.")
                }
        }
    }

    private fun onRouteFailed(message: String) {
        autoStartWhenRouted = false
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
        // A ride is recording (restored screen) but the route can't be drawn: still offer Exit
        if (RideSession.state.value.isRecording && !isNavigating) {
            showRouteCard()
            binding.tvRouteDuration.text = "Recording ride"
            binding.tvRouteDistance.text = ""
            binding.tvRouteEta.text = destinationName
            setNavigationUi(true)
        }
    }

    private fun onRouteReady(route: Route, destLat: Double, destLng: Double) {
        currentRoute = route
        guide = NavigationGuide(route)
        promptedStep = -1
        offlineRerouteWarned = false

        val points = JSONArray().apply {
            route.points.forEach { put(JSONArray().put(it.lat).put(it.lng)) }
        }
        runJs("showRoute($points, $destLat, $destLng, ${!isNavigating})")

        if (isNavigating) {
            updateGuidance() // rerouted mid-ride
        } else {
            showRoutePreview(route)
            if (autoStartWhenRouted) {
                autoStartWhenRouted = false
                toggleNavigation(true)
            }
        }
    }

    private fun showRouteCard() {
        binding.cardRoute.visibility = View.VISIBLE
    }

    private fun showRoutePreview(route: Route) {
        showRouteCard()
        showTripSummary(route.durationS, route.distanceM)
    }

    private fun showTripSummary(durationS: Double, distanceM: Double) {
        binding.tvRouteDuration.text = NavText.duration(durationS)
        binding.tvRouteDistance.text = "(${NavText.distance(distanceM)})"
        val arrival = DateFormat.getTimeInstance(DateFormat.SHORT).format(Date(System.currentTimeMillis() + (durationS * 1000).toLong()))
        binding.tvRouteEta.text = if (destinationName.isBlank()) "Arrive $arrival" else "Arrive $arrival · $destinationName"
    }

    private fun clearRoute() {
        routeJob?.cancel()
        currentRoute = null
        guide = null
        lastDestLat = null
        lastDestLng = null
        destinationName = ""
        binding.cardRoute.visibility = View.GONE
        runJs("clearRoute(); recenter()")
    }

    // ------------------------------------------------------------------------------------
    // Turn-by-turn guidance
    // ------------------------------------------------------------------------------------

    private fun updateGuidance() {
        val route = currentRoute ?: return
        val progress = guide?.update(currentLat, currentLng) ?: return

        if (progress.hasArrived) {
            onArrived()
            return
        }
        if (progress.isOffRoute) reroute()

        val step = route.steps.getOrNull(progress.nextStepIndex)
        if (step != null) {
            val icon = NavText.icon(step)
            binding.ivManeuver.setImageResource(icon.drawableRes)
            binding.ivManeuver.rotation = icon.rotation
            binding.ivManeuver.scaleX = if (icon.mirrored) -1f else 1f
            binding.tvManeuverDistance.text = NavText.distance(progress.distanceToNextM)
            binding.tvManeuverText.text = NavText.instruction(step)
            announce(progress.nextStepIndex, progress.distanceToNextM, NavText.instruction(step))
        }
        showTripSummary(progress.remainingDurationS, progress.remainingDistanceM)
        runJs("setRouteProgress(${progress.fractionTravelled})") // grey out the part already ridden
    }

    /** Voice prompts: once ahead of the maneuver ("In 300 meters, turn left") and once at it. */
    private fun announce(stepIndex: Int, distanceM: Double, instruction: String) {
        if (stepIndex != promptedStep) {
            promptedStep = stepIndex
            farPromptDone = distanceM < NEAR_PROMPT_M * 3 // too close for an advance prompt
            nearPromptDone = false
        }
        if (!nearPromptDone && distanceM <= NEAR_PROMPT_M) {
            nearPromptDone = true
            farPromptDone = true
            speak(instruction)
        } else if (!farPromptDone && distanceM <= FAR_PROMPT_M) {
            farPromptDone = true
            speak("In ${NavText.spokenDistance(distanceM)}, ${instruction.replaceFirstChar { it.lowercase() }}")
        }
    }

    private fun reroute() {
        val now = System.currentTimeMillis()
        val lat = lastDestLat
        val lng = lastDestLng
        if (isOffline) {
            // Keep guiding along the last route; say once that a new one can't be fetched
            if (!offlineRerouteWarned) {
                offlineRerouteWarned = true
                speak("You are off the route. Rerouting needs an internet connection.")
                Toast.makeText(this, "Offline: can't reroute. Head back to the blue line.", Toast.LENGTH_LONG).show()
            }
            return
        }
        if (now - lastRerouteAt < REROUTE_MIN_INTERVAL_MS || lat == null || lng == null) return
        lastRerouteAt = now
        speak("Rerouting")
        requestRoute(lat, lng, destinationName)
    }

    private fun onArrived() {
        val place = destinationName.ifBlank { "your destination" }
        speak("You have arrived at $place")
        Toast.makeText(this, "You have arrived", Toast.LENGTH_LONG).show()
        toggleNavigation(false) // ends and saves the ride
        clearRoute()
        setSearchText("")
    }

    // ------------------------------------------------------------------------------------
    // Start / stop navigation
    // ------------------------------------------------------------------------------------

    private fun setupButtons() {
        binding.btnBack.setOnClickListener {
            if (currentRoute != null && !isNavigating) clearRoute() else finish()
        }
        binding.btnClear.setOnClickListener {
            setSearchText("")
            if (!isNavigating) clearRoute()
            binding.etSearch.requestFocus()
            showSuggestions(recentPlaces.all())
        }
        binding.btnVoice.setOnClickListener {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                startVoiceSearch()
            } else {
                micPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            }
        }
        binding.fabMyLocation.setOnClickListener {
            if (hasLocation) runJs("recenter()") else ensureLocation()
        }
        binding.btnRecenter.setOnClickListener { runJs("recenter()") }
        binding.btnStartNav.setOnClickListener { toggleNavigation(!isNavigating) }
        binding.btnCloseRoute.setOnClickListener { clearRoute() }
    }

    private fun toggleNavigation(start: Boolean) {
        setNavigationUi(start)
        if (start) {
            startRide()
            currentRoute?.steps?.firstOrNull()?.let { first ->
                val to = destinationName.ifBlank { "your destination" }
                speak("Starting route to $to. ${NavText.instruction(first)}")
            }
            if (hasLocation) updateGuidance()
        } else {
            RideTrackingService.stop(this)
            runJs("setRouteProgress(0)") // preview shows the whole route again
            currentRoute?.let { showRoutePreview(it) }
        }
    }

    /** Switches the screen between route preview and active navigation (does not touch the ride). */
    private fun setNavigationUi(active: Boolean) {
        isNavigating = active
        if (active) {
            binding.btnStartNav.text = "Exit"
            binding.btnStartNav.setIconResource(R.drawable.ic_close)
            binding.btnStartNav.backgroundTintList = ColorStateList.valueOf(ContextCompat.getColor(this, R.color.nav_exit_red))
            binding.btnCloseRoute.visibility = View.GONE
            binding.cardSearch.visibility = View.GONE
            binding.cardManeuver.visibility = if (currentRoute != null) View.VISIBLE else View.GONE
            binding.speedBubble.visibility = View.VISIBLE
            binding.fabMyLocation.visibility = View.GONE
            window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            hideKeyboard()
        } else {
            binding.btnStartNav.text = "Start"
            binding.btnStartNav.setIconResource(R.drawable.ic_navigation)
            binding.btnStartNav.backgroundTintList = ColorStateList.valueOf(ContextCompat.getColor(this, R.color.nav_blue))
            binding.btnCloseRoute.visibility = View.VISIBLE
            binding.cardSearch.visibility = View.VISIBLE
            binding.cardManeuver.visibility = View.GONE
            binding.speedBubble.visibility = View.GONE
            binding.btnRecenter.visibility = View.GONE
            binding.fabMyLocation.visibility = View.VISIBLE
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }
        updateOfflineBadge()
        runJs("setNavMode($active)")
        // Faster GPS updates while navigating
        if (locationCallback != null) startLocationUpdates(currentInterval())
    }

    // ------------------------------------------------------------------------------------
    // Ride recording (RideTrackingService) and helmet destinations
    // ------------------------------------------------------------------------------------

    private fun startRide() {
        if (RideSession.state.value.isRecording) return // already recording (e.g. restored screen)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
        RideTrackingService.start(this, destinationName, lastDestLat, lastDestLng, currentLat, currentLng)
    }

    private fun restoreRideIfRecording() {
        val ride = RideSession.state.value
        if (!ride.isRecording) return
        destinationName = ride.destination
        setSearchText(ride.destination)
        lastDestLat = ride.destLat
        lastDestLng = ride.destLng
        if (ride.destLat != null && ride.destLng != null) {
            // Route is re-fetched on the first GPS fix, then navigation resumes
            restoreRideRoute = true
        } else {
            showRouteCard()
            binding.tvRouteDuration.text = "Recording ride"
            binding.tvRouteDistance.text = ""
            binding.tvRouteEta.text = ride.destination
            setNavigationUi(true)
        }
    }

    private fun observeRideSession() {
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                RideSession.state.collectLatest { ride ->
                    // Ride stopped elsewhere (notification "Stop ride" action): leave navigation
                    if (!ride.isRecording && isNavigating) {
                        setNavigationUi(false)
                        currentRoute?.let { showRoutePreview(it) }
                    }
                }
            }
        }
    }

    private fun observeHelmetData() {
        val helmetBleManager = HelmetBleManager.getInstance(this)
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                helmetBleManager.helmetData.collectLatest { data ->
                    if (data.destination.isEmpty()) {
                        lastHandledDestination = "" // allow the same destination to trigger again later
                    } else if (data.destination != lastHandledDestination && !isNavigating) {
                        lastHandledDestination = data.destination
                        setSearchText(data.destination)
                        autoStartWhenRouted = true
                        searchAndRoute(data.destination)
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------------------------------
    // Voice search and spoken guidance
    // ------------------------------------------------------------------------------------

    private fun startVoiceSearch() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            Toast.makeText(this, "Voice search isn't available on this device", Toast.LENGTH_SHORT).show()
            return
        }
        speechRecognizer?.destroy()
        val recognizer = SpeechRecognizer.createSpeechRecognizer(this)
        speechRecognizer = recognizer

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
            putExtra(RecognizerIntent.EXTRA_PROMPT, "Where to?")
        }

        recognizer.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                binding.etSearch.hint = "Listening..."
            }
            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {
                binding.etSearch.hint = "Search here"
            }
            override fun onError(error: Int) {
                binding.etSearch.hint = "Search here"
                val message = when (error) {
                    SpeechRecognizer.ERROR_NO_MATCH, SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Didn't catch that. Try again."
                    SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Voice search needs an internet connection"
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission is needed for voice search"
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Voice search is busy. Try again."
                    else -> "Voice search failed. Try again."
                }
                Toast.makeText(this@NavigationActivity, message, Toast.LENGTH_SHORT).show()
            }
            override fun onResults(results: Bundle?) {
                val spoken = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()
                if (!spoken.isNullOrBlank()) {
                    setSearchText(spoken)
                    hideKeyboard()
                    searchAndRoute(spoken)
                }
            }
            override fun onPartialResults(partialResults: Bundle?) {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
        })
        recognizer.startListening(intent)
    }

    override fun onInit(status: Int) {
        ttsReady = status == TextToSpeech.SUCCESS
        if (ttsReady) textToSpeech.language = Locale.US
    }

    private fun speak(text: String) {
        if (!ttsReady || !SafetySettings.isVoiceGuidanceEnabled(this)) return
        val params = Bundle().apply {
            putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, SafetySettings.voiceVolume(this@NavigationActivity) / 100f)
        }
        textToSpeech.speak(text, TextToSpeech.QUEUE_FLUSH, params, "nav")
    }

    // ------------------------------------------------------------------------------------

    private fun setupBottomNavigation() {
        binding.bottomNavigation.selectedItemId = R.id.nav_navigation
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_home -> {
                    val intent = Intent(this, DashboardActivity::class.java)
                    intent.flags = Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                    startActivity(intent)
                    true
                }
                R.id.nav_analytics -> {
                    val intent = Intent(this, AnalyticsActivity::class.java)
                    intent.flags = Intent.FLAG_ACTIVITY_REORDER_TO_FRONT
                    startActivity(intent)
                    true
                }
                R.id.nav_navigation -> true
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
