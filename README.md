<div align="center">

<img src="docs/images/logo.png" alt="HelmX logo" width="200" />

# HelmX: AI-Powered Smart Helmet

**A smart motorcycle helmet built on a Raspberry Pi 4 that detects crashes and drowsiness, guides the rider with voice and navigation, and senses the air around them. It comes with an Android companion app and a web store.**

![Raspberry Pi 4](https://img.shields.io/badge/Raspberry%20Pi%204-8%20GB-C51A4A?logo=raspberrypi&logoColor=white)
![Debian 12](https://img.shields.io/badge/Debian%2012-Bookworm%20arm64-A81D33?logo=debian&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![TensorFlow Lite](https://img.shields.io/badge/TensorFlow%20Lite-INT8-FF6F00?logo=tensorflow&logoColor=white)
![ONNX](https://img.shields.io/badge/ONNX-Runtime-005CED?logo=onnx&logoColor=white)
![Bluetooth LE](https://img.shields.io/badge/Bluetooth-LE-0082FC?logo=bluetooth&logoColor=white)
![Android](https://img.shields.io/badge/Android-Kotlin-3DDC84?logo=android&logoColor=white)
![Next.js](https://img.shields.io/badge/Web-Next.js%2016-000000?logo=nextdotjs&logoColor=white)

[**🌐 Live web demo**](https://helmx-silk.vercel.app/) · [**⬇ Android APK v1.0.0**](https://github.com/Usman-Azfar/HelmX-AI-Powered-Smart-Helmet/releases/tag/android-v1.0.0)

<sub>Final Year Project · BS Computer Science · Department of Computer Science, FCIT, University of the Punjab, Lahore · Session 2025–2026</sub>

<br/>

<img src="docs/images/helmet/helmx-prototype-studio.jpg" alt="HelmX prototype helmet, side view" width="100%" />

<sub><i>The HelmX working prototype: a modular full-face helmet with a Raspberry Pi 4, cameras, sensors, a cellular module and a battery pack.</i></sub>

</div>

---

## Contents

- [Why HelmX](#why-helmx)
- [What the helmet does](#what-the-helmet-does)
- [The prototype](#the-prototype)
- [Team](#team)
- [Responsible use](#responsible-use)

---

## Why HelmX

Motorcycle riders are among the most vulnerable road users, and help often arrives late after a crash, especially on empty roads or at night. Most smart-helmet products focus on one feature, such as Bluetooth audio, a camera or crash detection, and many are too expensive for everyday riders.

**HelmX puts seven safety and lifestyle features into one low-cost helmet.** All of the AI runs on the helmet itself, on a Raspberry Pi, so the safety features keep working without an internet connection.

## What the helmet does

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>🚨 Crash detection & emergency alert</h3>
      A six-axis IMU streams motion data at 50 Hz to a hybrid Conv1D classifier and autoencoder running on the Pi as an INT8 TensorFlow Lite model. A crash is confirmed only after three anomalous windows in a row. The rider then has <b>30 seconds to cancel</b> before the helmet takes a GPS fix and tries to send an SMS over GSM.
    </td>
    <td width="50%" valign="top">
      <h3>😴 Drowsiness detection</h3>
      A camera watches the rider's eyes, mouth and head pose. A model that uses only current and past frames (MobileNetV3 image features combined with 12 per-rider measurements) estimates whether the rider is <i>alert</i>, has <i>low vigilance</i> or is <i>drowsy</i>. A time-based controller then decides when to sound the alarm.
    </td>
  </tr>
  <tr>
    <td valign="top">
      <h3>🧭 Navigation</h3>
      The rider can ask for a destination by voice, and the helmet passes it to the phone. The Android app then gives turn-by-turn spoken guidance and re-routes when needed. A map of Lahore District is built into the app so navigation still works offline.
    </td>
    <td valign="top">
      <h3>🎙️ Offline voice assistant</h3>
      Rhasspy runs on the helmet with a Porcupine wake word, Kaldi speech recognition and NanoTTS speech output. Speech is handled on the helmet itself. The rider can ask for sensor readings, a destination, music, a photo or a video clip.
    </td>
  </tr>
  <tr>
    <td valign="top">
      <h3>🌡️ Environmental sensing</h3>
      A DHT22 measures temperature and humidity, and an MQ135 gives an air-quality threshold signal. Readings are sent to the phone over Bluetooth Low Energy every 2.5 seconds.
    </td>
    <td valign="top">
      <h3>📷 Cameras & entertainment</h3>
      The helmet can take photos and 10-second videos and play music through its two speakers. Media is stored in a vault on the helmet.
    </td>
  </tr>
  <tr>
    <td colspan="2" valign="top" align="center">
      <h3>📱 Companion app & web platform</h3>
      An Android app shows live helmet data, crash and drowsiness alerts, navigation and ride analytics. A web platform has a 3D helmet configurator, Stripe checkout and order receipts.
    </td>
  </tr>
</table>

---

## The prototype

<table>
  <tr>
    <td width="33%" align="center"><img src="docs/images/helmet/helmx-prototype-front-ir.jpg" alt="Front view with infrared camera illuminators on" /><br/><sub><b>Front</b>: the top camera's infrared illuminators are on, and the chin-mounted module is below the visor</sub></td>
    <td width="33%" align="center"><img src="docs/images/helmet/helmx-prototype-side.jpg" alt="Side view of the prototype" /><br/><sub><b>Side</b>: chin-arm USB camera, side-mounted DHT22 sensor and rear enclosure</sub></td>
    <td width="33%" align="center"><img src="docs/images/helmet/helmx-prototype-rear.jpg" alt="Rear three-quarter view showing the Raspberry Pi" /><br/><sub><b>Rear</b>: Raspberry Pi 4 mounted on the shell, with the GPIO harness running to the sensors</sub></td>
  </tr>
</table>

| Where on the helmet | What is there |
|---|---|
| Top of the shell, on a raised mount | Raspberry Pi IR night-vision camera on a CSI ribbon cable, with two infrared illuminators for low light and night riding |
| Rear of the shell | Raspberry Pi 4 Model B (8 GB), with the GPIO harness running to the sensors |
| Chin bar | USB camera with a built-in microphone (`/dev/video0`), used by the voice assistant and for media capture |
| Left side | DHT22 temperature and humidity sensor |
| Rear-side enclosure | Power pack (2 × 10,000 mAh lithium batteries) and wiring |
| Inside the shell | MPU6050 IMU, MQ135 air-quality sensor, SIM800L GSM, NEO-6M GPS, voice module and 2 speakers |

---

## Team

HelmX was built by BS Computer Science students as their Final Year Project at the Department of Computer Science, Faculty of Computing and Information Technology (FCIT), University of the Punjab, Lahore.

| Member | Role | GitHub |
|---|---|---|
| **Usman Azfar** | Group leader · hardware and integration, cloud, safety, voice and environment systems, app | [@Usman-Azfar](https://github.com/Usman-Azfar) |
| **Hamza Ahmad** | Web and app development, backend APIs, database, edge computing, ML testing | [@HamzaAhmad536](https://github.com/HamzaAhmad536) |
| **Abdul Hannan** | ML models for crash and drowsiness detection, alerts, smart navigation, documentation | [@Rao-Abdul-Hannan](https://github.com/Rao-Abdul-Hannan) |
| **Awais Imtiaz** | Hardware integration, prototype testing, web and app development, documentation | [@Awais-Imtiaz](https://github.com/Awais-Imtiaz) |

**Supervisor:** Dr. Tayyaba Tariq, Assistant Professor, Department of Computer Science, University of the Punjab

---

## Responsible use

> HelmX is a **student research prototype**. It is not a certified automotive, medical or emergency system, and it must not be relied on as the only way to detect a crash, detect drowsiness or contact emergency services. Always wear a certified helmet and ride safely.

The `crash-detection` and `drowsiness-detection-model` branches are released under the MIT licence. Third-party datasets and trained model weights are **not** covered by that licence; see each branch for its data and licence details.

<div align="center">
<br/>
<img src="docs/images/logo.png" alt="HelmX" width="72" />
<br/>
<sub>© 2026 HelmX team · University of the Punjab · Built for safer roads.</sub>
</div>
