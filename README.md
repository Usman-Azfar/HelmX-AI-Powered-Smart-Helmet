<div align="center">

<img src="docs/images/logo.png" alt="HelmX logo" width="220" />

# HelmX: AI-Powered Smart Helmet

**Android companion app for the HelmX smart motorcycle helmet**

Live helmet data · Crash & drowsiness alerts · Turn-by-turn navigation with an offline map · Ride analytics

![Platform](https://img.shields.io/badge/platform-Android-3DDC84?logo=android&logoColor=white)
![Kotlin](https://img.shields.io/badge/Kotlin-2.1-7F52FF?logo=kotlin&logoColor=white)
![Min SDK](https://img.shields.io/badge/minSdk-24-blue)
![Target SDK](https://img.shields.io/badge/targetSdk-36-blue)
![Firebase](https://img.shields.io/badge/Firebase-Auth%20%7C%20Firestore-FFCA28?logo=firebase&logoColor=black)
![Maps](https://img.shields.io/badge/maps-MapLibre%20%2B%20OpenStreetMap-0B7285)

<sub>Final Year Project · BS Computer Science · Department of Computer Science, FCIT, University of the Punjab, Lahore · Session 2025–2026</sub>

</div>

---

## Table of contents

- [About the project](#about-the-project)
- [Screenshots](#screenshots)
- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Helmet Bluetooth protocol](#helmet-bluetooth-protocol)
- [Offline map](#offline-map)
- [Data & privacy](#data--privacy)
- [Testing](#testing)
- [Project structure](#project-structure)
- [Known limitations](#known-limitations)
- [Team](#team)
- [Acknowledgements](#acknowledgements)

---

## About the project

Motorcycle riders are among the most vulnerable road users. **HelmX** is a smart helmet that uses AI and IoT to make riding safer: it detects crashes and drowsiness, guides the rider with navigation and voice, and monitors the environment around them.

This repository contains the **Android app**, the rider's companion to the helmet. It connects to the helmet's Raspberry Pi over Bluetooth Low Energy, shows live readings, raises safety alerts, provides Google-Maps-style navigation (including an offline map of Lahore), and records every ride.

> This branch (`android-app`) contains the Android app. The web platform is on the [`web-app`](https://github.com/Usman-Azfar/HelmX-AI-Powered-Smart-Helmet/tree/web-app) branch; the helmet firmware and AI models are developed separately.

---

## Screenshots

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/00_launch_screen.png" width="200"/><br/><sub>Launch screen</sub></td>
    <td align="center"><img src="docs/screenshots/01_login.png" width="200"/><br/><sub>Login</sub></td>
    <td align="center"><img src="docs/screenshots/02_signup.png" width="200"/><br/><sub>Sign up</sub></td>
    <td align="center"><img src="docs/screenshots/03_home.png" width="200"/><br/><sub>Home</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/04_home_pairing.png" width="200"/><br/><sub>Pairing with the helmet</sub></td>
    <td align="center"><img src="docs/screenshots/05_analytics.png" width="200"/><br/><sub>Analytics</sub></td>
    <td align="center"><img src="docs/screenshots/06_analytics_rides.png" width="200"/><br/><sub>Ride history</sub></td>
    <td align="center"><img src="docs/screenshots/25_home_light.png" width="200"/><br/><sub>Light theme</sub></td>
  </tr>
</table>

### Navigation

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/07_navigation_map.png" width="200"/><br/><sub>Map</sub></td>
    <td align="center"><img src="docs/screenshots/08_navigation_search.png" width="200"/><br/><sub>Place search</sub></td>
    <td align="center"><img src="docs/screenshots/09_navigation_recents.png" width="200"/><br/><sub>Recent places</sub></td>
    <td align="center"><img src="docs/screenshots/10_navigation_route_preview.png" width="200"/><br/><sub>Route preview</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/11_navigation_guidance.png" width="200"/><br/><sub>Turn-by-turn guidance</sub></td>
    <td align="center"><img src="docs/screenshots/12_navigation_offline.png" width="200"/><br/><sub>Guidance without internet</sub></td>
    <td align="center"><img src="docs/screenshots/13_navigation_offline_preview.png" width="200"/><br/><sub>Offline map</sub></td>
    <td></td>
  </tr>
</table>

### Safety & settings

<table>
  <tr>
    <td align="center"><img src="docs/screenshots/14_settings.png" width="200"/><br/><sub>Settings</sub></td>
    <td align="center"><img src="docs/screenshots/15_crash_alerts.png" width="200"/><br/><sub>Crash alerts & contacts</sub></td>
    <td align="center"><img src="docs/screenshots/16_crash_countdown_notification.png" width="200"/><br/><sub>Crash alert countdown</sub></td>
    <td align="center"><img src="docs/screenshots/17_crash_test_finished.png" width="200"/><br/><sub>Test crash alert</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/18_drowsiness.png" width="200"/><br/><sub>Drowsiness alerts</sub></td>
    <td align="center"><img src="docs/screenshots/19_voice.png" width="200"/><br/><sub>Voice guidance</sub></td>
    <td align="center"><img src="docs/screenshots/20_account.png" width="200"/><br/><sub>Account</sub></td>
    <td align="center"><img src="docs/screenshots/21_privacy.png" width="200"/><br/><sub>Privacy & permissions</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="docs/screenshots/22_about.png" width="200"/><br/><sub>About</sub></td>
    <td align="center"><img src="docs/screenshots/23_about_features.png" width="200"/><br/><sub>Features</sub></td>
    <td align="center"><img src="docs/screenshots/24_about_team.png" width="200"/><br/><sub>Helmet connection & team</sub></td>
    <td align="center"><img src="docs/screenshots/26_settings_light.png" width="200"/><br/><sub>Settings (light)</sub></td>
  </tr>
</table>

<sub>Screenshots were taken on a Pixel 8 emulator (Android 14) with a simulated GPS position in Lahore and no helmet connected, so the helmet readings show as offline. Screens from before the Settings redesign are kept in <a href="docs/screenshots/before-redesign">docs/screenshots/before-redesign</a>.</sub>

---

## Features

### 🪖 Helmet connection
- Finds the helmet over **Bluetooth Low Energy** (device name `HelmX`) and subscribes to its data stream.
- Shows connection status live and **reconnects automatically** if the link drops mid-ride.
- Clear states and errors: searching, connecting, not found, "Not a HelmX helmet", connection failed.

### 🛡️ Safety
- **Crash alerts**: when the helmet reports a crash, an urgent notification and an in-app dialog appear with **Call** and **Send location** (a Google Maps link to the rider's position).
- **Always allow (automatic response)**: if the rider doesn't respond within **30 seconds**, HelmX texts the location to the emergency contacts and calls the primary contact. Tapping **I'm OK** cancels it.
- **Emergency contacts**: up to two, stored in the rider's account, can be picked from the phone's contacts. Without one, Call opens Rescue 1122.
- **Drowsiness alerts**: alarm sound, vibration and a heads-up notification, with adjustable sensitivity (how quickly the alarm fires).
- **Test buttons** let riders try both alerts without contacting anyone.
- Alerts work on every screen and while riding with the screen off.

### 🧭 Navigation
- Vector map in **light and dark styles** with English labels.
- **Place search** with suggestions biased to the rider's location, **voice search**, and **recent places**.
- **Route preview** with time, distance and arrival time.
- **Turn-by-turn guidance**: maneuver banner, spoken prompts ("In 300 meters, turn left onto…"), map that rotates and tilts with the rider, current speed, and the ridden part of the route greyed out.
- **Automatic rerouting** when the rider leaves the route, and arrival detection.
- A destination sent from the helmet starts navigation automatically.

### 📴 Offline map
- A full-detail map of **Lahore District** is built into the app; it switches over automatically when there is no internet.
- Recent places and guidance on an already-started route keep working offline.

### 📊 Ride analytics
- Pressing **Start** in Navigation records a ride in a foreground service, so it keeps recording with the screen off or the app in the background.
- Rides today, total distance, and a history of recent rides (destination, distance, duration, average speed).
- Live temperature, humidity and air quality from the helmet's sensors.

### ⚙️ Settings & account
- Dark / light theme, voice guidance on/off and volume, permission overview.
- Edit profile, change email (verified by link) or password, log out, and **delete account** (removes profile, rides and contacts).
- An **About** screen with the project, features, helmet connection details and team.

---

## Architecture

```mermaid
flowchart LR
    subgraph Helmet["HelmX helmet (Raspberry Pi)"]
        S[Sensors · cameras · AI models]
    end

    subgraph App["Android app"]
        BLE[HelmetBleManager<br/>BLE connection]
        SM[SafetyMonitor<br/>crash & drowsiness alerts]
        UI[Screens<br/>Home · Analytics · Navigation · Settings]
        RT[RideTrackingService<br/>foreground GPS recording]
        MAP[Map page in WebView<br/>MapLibre GL + offline tiles]
    end

    subgraph Cloud["Online services"]
        FB[(Firebase<br/>Auth + Firestore)]
        OSM[OpenFreeMap tiles<br/>Photon search · OSRM routing]
    end

    S -- "BLE notifications<br/>(JSON / CSV)" --> BLE
    BLE --> SM
    BLE --> UI
    UI --> RT
    UI <--> MAP
    MAP --> OSM
    UI --> OSM
    UI <--> FB
    RT --> FB
    SM -- "SMS / call" --> C[Emergency contacts]
```

**Main pieces**

| Component | Role |
|---|---|
| `HelmetBleManager` | Scans, connects and listens to the helmet; exposes live `HelmetData` as a `StateFlow`. |
| `HelmetDataParser` | Turns the helmet's JSON / CSV messages into `HelmetData`. |
| `SafetyMonitor` | App-wide watcher that raises drowsiness alarms, crash alerts and the 30-second automatic response. |
| `RideTrackingService` + `RideTracker` | Foreground service that measures a ride from GPS and saves it to Firestore. |
| `NavigationActivity` + `NavigationGuide` | Search, routing, turn-by-turn guidance, rerouting and arrival detection. |
| `map.html` + `OfflineMapServer` | MapLibre map in a WebView; bundled assets are served from `https://helmx.local/` so the map works offline. |
| `AuthManager`, `RideRepository`, `SafetySettings` | Firebase account, ride and emergency-contact storage. |

---

## Tech stack

| Area | Technology |
|---|---|
| Language & UI | Kotlin 2.1, Android Views with ViewBinding, Material Components 3 |
| Async & state | Kotlin Coroutines, `StateFlow`, AndroidX Lifecycle |
| Backend | Firebase Authentication, Cloud Firestore |
| Location | Google Play Services Fused Location |
| Map | MapLibre GL JS 4.7.1 in a WebView, OpenFreeMap vector tiles (OpenStreetMap data) |
| Search & routing | Photon (Komoot) geocoder, OSRM routing |
| Helmet link | Android Bluetooth Low Energy (GATT client) |
| Build | Gradle (Kotlin DSL), Android Gradle Plugin 8.13, compile/target SDK 36, min SDK 24 |
| Testing | JUnit 4 (local unit tests) |

---

## Getting started

### Prerequisites
- Android Studio (recent stable version) with JDK 17
- An Android phone with Bluetooth LE (Android 7.0 or newer) for use with the helmet; the emulator works for everything except Bluetooth
- A Firebase project and its `google-services.json` (see [Firebase setup](#firebase-setup))

### Build and run

```bash
git clone -b android-app https://github.com/Usman-Azfar/HelmX-AI-Powered-Smart-Helmet.git
cd HelmX-AI-Powered-Smart-Helmet
# add app/google-services.json first (see Firebase setup below)
./gradlew assembleDebug        # build the debug APK
./gradlew installDebug         # install on a connected device
```

Or open the project in Android Studio and press **Run**.

### Firebase setup
1. Create a Firebase project, add an Android app with package name `com.yourname.helmx`, download its `google-services.json` and place it at `app/google-services.json`. The file is not committed to this repository (it is listed in `.gitignore`); team members can get the project's copy from the project lead.
2. Enable **Email/Password** sign-in under *Authentication → Sign-in method*.
3. Create a **Cloud Firestore** database and publish the security rules from [`firestore.rules`](firestore.rules), which let each user read and write only their own profile, rides and contacts.

### Permissions the app asks for
| Permission | Used for |
|---|---|
| Location | Map, directions, ride distance, location in crash messages |
| Nearby devices (Bluetooth) | Finding and connecting to the helmet |
| Microphone | Voice search |
| Notifications | Crash and drowsiness alerts, ride-recording notification |
| SMS and Phone *(optional)* | Only for **Always allow**: automatic texting and calling after a crash |

---

## Helmet Bluetooth protocol

| Item | Value |
|---|---|
| Helmet computer | Raspberry Pi acting as a BLE peripheral |
| Advertised device name | `HelmX` |
| Service UUID | `0000FFE0-0000-1000-8000-00805F9B34FB` |
| Data characteristic (notify) | `0000FFE1-0000-1000-8000-00805F9B34FB` |
| MTU requested | 512 bytes |

Each notification is one text message in one of these formats (see `HelmetDataParser`):

```text
JSON  {"temperature": 31.5, "humidity": 62, "air_quality": "Good", "destination": "Liberty Market"}
CSV   battery,speed,drowsy,crash,distance        e.g. 95,42.5,0,0,3.2   (flags: 1/0 or true/false)
CSV   temperature,humidity                       (legacy)
```

A non-empty `destination` makes the app search for that place and start navigation automatically.

---

## Offline map

The app includes an offline map of **Lahore District** in `app/src/main/assets/offline` (about 25 MB of files, about 13 MB added to the APK): vector tiles for zoom 0–14, fonts, icons, offline copies of the map styles, and the MapLibre library itself.

| Works offline | Needs internet |
|---|---|
| Map display, your location | Searching for new places |
| Recent places | New directions and rerouting |
| Guidance on a route that was already started | Map outside Lahore District |
| Ride recording (saved and uploaded later) | |

To rebuild the package with newer map data or a different area, edit `BBOX` in the script and run:

```bash
python tools/build_offline_map.py app/src/main/assets/offline
```

---

## Data & privacy

| Data | Where it is stored |
|---|---|
| Name, email, phone number | Firestore `users/{uid}` |
| Emergency contacts | Firestore `users/{uid}.emergencyContacts` (cached on the phone for offline alerts) |
| Rides (date, destination, distance, duration, average speed) | Firestore `users/{uid}/rides` (the GPS track itself is not uploaded) |
| Recent places, app settings | On the phone only |
| Live helmet readings | Not stored |

Searches and route requests are sent to Photon and OSRM to get results. Users can delete their account and all of their data from **Settings → Account → Delete account**.

---

## Testing

```bash
./gradlew testDebugUnitTest
```

41 local unit tests cover the logic that doesn't need a device:

| Test class | Covers |
|---|---|
| `HelmetDataParserTest` | Helmet JSON and CSV message parsing |
| `RideTrackerTest` | Ride distance, GPS jitter filtering, short-ride rules |
| `NavigationLogicTest` | Route and search parsing, instructions, guidance, rerouting, arrival |
| `OfflineTest` | Offline map file serving and recent places |
| `SafetySettingsTest` | Emergency contacts, crash message, sensitivity |
| `ValidatorsTest` | Phone number validation |

The UI flows were tested manually on a Pixel 8 emulator (Android 14) with simulated GPS.

---

## Project structure

```text
HelmX-App/
├── app/src/main/
│   ├── java/com/yourname/helmx/
│   │   ├── *Activity.kt              Screens (Login, Dashboard, Analytics, Navigation, Settings, …)
│   │   ├── HelmetBleManager.kt       Bluetooth LE connection to the helmet
│   │   ├── HelmetDataParser.kt       Helmet message parsing
│   │   ├── SafetyMonitor.kt          Crash & drowsiness alerts, automatic response
│   │   ├── CrashActionActivity.kt    Actions behind the crash-alert buttons
│   │   ├── RideTrackingService.kt    Foreground ride recording
│   │   ├── RideTracker.kt            Ride distance calculation
│   │   ├── NavigationGuide.kt        Turn-by-turn progress, rerouting, arrival
│   │   ├── MapsApi.kt                Photon search and OSRM routing
│   │   ├── OfflineMapServer.kt       Serves the bundled map to the WebView
│   │   ├── AuthManager.kt            Firebase accounts
│   │   ├── RideRepository.kt         Ride storage
│   │   └── SafetySettings.kt         Safety, voice and contact settings
│   ├── assets/
│   │   ├── map.html                  MapLibre map page
│   │   └── offline/                  Offline Lahore map + MapLibre library
│   └── res/                          Layouts, icons, themes, launcher icon
├── app/src/test/                     Unit tests
├── docs/                             Logo and screenshots
├── tools/build_offline_map.py        Rebuilds the offline map package
└── firestore.rules                   Firestore security rules
```

---

## Known limitations

- **Helmet features run on the helmet.** Crash and drowsiness detection, the cameras and the AI voice assistant run on the helmet; the app shows their results and raises alerts.
- **One-way Bluetooth link.** The app only receives data from the helmet and cannot change its settings, so drowsiness sensitivity is applied on the phone.
- **Free map services.** OpenFreeMap, Photon and the public OSRM server have fair-use limits and are meant for development and demos; a production release should use self-hosted or commercial routing and search.
- **Offline coverage.** The offline map covers Lahore District only, and offline routing isn't supported.
- **Automatic calls.** Android may block an automatic call when the app is in the background; the SMS is still sent and a one-tap Call button is shown.
- **Google Play policy.** The SMS and phone permissions used by *Always allow* are restricted on Google Play and would need a policy declaration for a store release.

---

## Team

| Name | Role |
|---|---|
| **Ms. Tayyaba Tariq** | Supervisor |
| **Usman Azfar** | Group leader · hardware & integration, cloud, safety, voice and environment systems, app |
| **Hamza Ahmad** | Web & app development, backend APIs, database, edge computing, ML testing |
| **Abdul Hanan** | ML models for crash & drowsiness detection, alerts, smart navigation, documentation |
| **Awais Imtiaz** | Hardware integration, prototype testing, web & app development, documentation |

Department of Computer Science, Faculty of Computing and Information Technology (FCIT), University of the Punjab, Lahore.

---

## Acknowledgements

- Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors (ODbL)
- Map tiles: [OpenFreeMap](https://openfreemap.org) · [OpenMapTiles](https://openmaptiles.org)
- Map engine: [MapLibre GL JS](https://maplibre.org)
- Place search: [Photon](https://photon.komoot.io) by Komoot
- Routing: [OSRM](https://project-osrm.org)
- Accounts and data: [Firebase](https://firebase.google.com)

Other parts of the project: the **web platform** lives on the [`web-app`](https://github.com/Usman-Azfar/HelmX-AI-Powered-Smart-Helmet/tree/web-app) branch of this repository.

<div align="center"><sub>© 2026 HelmX team, University of the Punjab</sub></div>
