# HelmX Raspberry Pi setup

[← Back to the project overview](../../README.md)

This is the complete reference for the computer on the HelmX helmet: the hardware fitted to it, how the Pi is configured, and the services it runs.

| | |
|---|---|
| **Hardware inventory** | 13 Oct 2026 (Asia/Karachi) |
| **System configuration snapshot** | 11 Oct 2026, 19:34 PKT |

## Contents

1. [Hardware inventory](#1-hardware-inventory)
2. [Host platform](#2-host-platform)
3. [GPIO, buses and peripherals](#3-gpio-buses-and-peripherals)
4. [Detected devices](#4-detected-devices)
5. [Firmware configuration](#5-firmware-configuration)
6. [HelmX services](#6-helmx-services)
7. [Service units](#7-service-units)
8. [Crash detection deployment](#8-crash-detection-deployment)
9. [Software versions](#9-software-versions)
10. [Service overview](#10-service-overview)
11. [File hashes](#11-file-hashes)

---

## 1. Hardware inventory

All ten component types are fitted, including two 10,000 mAh batteries and two speakers.

| Component | Qty | Connection / configuration |
|---|---:|---|
| **Raspberry Pi IR night-vision camera** | 1 | CSI ribbon camera with two infrared illuminators for low light and night riding |
| **MQ135** air-quality sensor | 1 | Digital threshold input on BCM17 (physical pin 11), read by the BLE server |
| **DHT22** temperature / humidity | 1 | BCM22 (physical pin 15), read by the BLE server through `board.D22` |
| **SIM800L** GSM module | 1 | UART0 on BCM14/15 (pins 8/10), `/dev/serial0`, 9600 baud. Cellular SMS for emergency alerts |
| **NEO-6M** GPS receiver | 1 | UART3 on BCM4/5 (pins 7/29), `/dev/ttyAMA3`, 9600 baud NMEA. Position fix for the emergency SMS |
| **USB camera** | 1 | `/dev/video0`. icSpring Web Camera `32e6:9221` with a built-in USB microphone |
| **Lithium battery**, 10,000 mAh | 2 | Portable power supply |
| **Voice recognition module** | 1 | UART5 on BCM12/13 (pins 32/33), `/dev/ttyAMA5`, 9600 baud. Hardware voice commands alongside Rhasspy |
| **Speakers** | 2 | Voice responses, alerts and music |
| **MPU6050** IMU | 1 | I2C1, address `0x68`. Accelerometer and gyroscope for crash detection |

---

## 2. Host platform

| Item | Value |
|---|---|
| Host name / operator account | `helx-pi` / `helmx` (uid 1000) |
| Board | Raspberry Pi 4 Model B Rev 1.5 |
| CPU | 4 × ARM Cortex-A72 r0p3 · fixed 1.8 GHz (`force_turbo=1`, `ondemand` CPU governor) · L2 cache 1 MiB |
| Memory | 7.6 GiB usable (8 GB fitted) · 511 MiB swap (`dphys-swapfile`) |
| Storage | SanDisk X400 128 GB SSD through an ASMedia ASM1051E/1053E/1153 USB 3 SATA bridge |
| Partitions | `sda1` 512 MB vfat → `/boot/firmware` (14 % used) · `sda2` 118.7 GB ext4 → `/` (28 GB used, 25 %) |
| OS | Debian GNU/Linux 12 (Bookworm), arm64 |
| Kernel | `Linux 6.12.96+rpt-rpi-v8 #1 SMP PREEMPT Debian 1:6.12.96-1+rpt1 (2026-07-24) aarch64` |
| Firmware | `May 21 2026 11:20:25`, version `288930ab4712b99596f32732664aaaeb881ef1e0` (clean, release) |
| Boot target | `graphical.target`: LightDM with the labwc / Wayland desktop |
| Remote access | WayVNC and Raspberry Pi Connect |
| Network | Ethernet (`eth0`) |
| Health | 44.8–45.7 °C · `throttled=0x0` (no under-voltage or thermal throttling) |
| Memory use | 3.1 GiB used · 4.6 GiB available, with every HelmX service running and the desktop open |

**Operator groups:** `adm dialout cdrom sudo audio video plugdev games users input render netdev spi i2c gpio lpadmin`

---

## 3. GPIO, buses and peripherals

```text
 Physical pin   BCM      Function     Connected to
 ────────────   ──────   ──────────   ─────────────────────────────────
      3         GPIO2    I2C1 SDA     MPU6050 IMU (0x68)
      5         GPIO3    I2C1 SCL     MPU6050 IMU (0x68)
      7         GPIO4    UART3 TXD    NEO-6M GPS RX
      8         GPIO14   UART0 TXD    SIM800L GSM RX   (/dev/serial0)
     10         GPIO15   UART0 RXD    SIM800L GSM TX   (/dev/serial0)
     11         GPIO17   input        MQ135 digital output
     12         GPIO18   output       Crash alarm (buzzer / indicator)
     15         GPIO22   data         DHT22 data
     29         GPIO5    UART3 RXD    NEO-6M GPS TX
     32         GPIO12   UART5 TXD    Voice recognition module RX
     33         GPIO13   UART5 RXD    Voice recognition module TX
```

| Component | Connection | Device | Status |
|---|---|---|:---:|
| IMU | I2C1 `0x68`, SDA on pin 3 and SCL on pin 5, 100 kHz | `/dev/i2c-1` | ✅ Connected, sampled at 50 Hz |
| GSM SIM800L | UART0, BCM14/15 (pins 8/10), 9600 baud | `/dev/serial0 → ttyS0` | ✅ Connected |
| GPS NEO-6M | UART3, BCM4/5 (pins 7/29), 9600 baud NMEA | `/dev/ttyAMA3` | ✅ Connected |
| Voice recognition module | UART5, BCM12/13 (pins 32/33), 9600 baud | `/dev/ttyAMA5` | ✅ Connected |
| DHT22 | BCM22, pin 15 | GPIO | ✅ Read every 2.5 s |
| MQ135 | BCM17, pin 11 | GPIO | ✅ Air-quality threshold |
| Alarm | BCM18, pin 12 | GPIO | ✅ Driven during the 30 s cancel window |
| IR night-vision camera | CSI, two IR illuminators | libcamera | ✅ Connected |
| USB camera / microphone | USB icSpring Web Camera `32e6:9221` | `/dev/video0`, ALSA card 3 | ✅ Connected |

Each serial module's TX goes to the Pi's RX and its RX to the Pi's TX. All modules share a common ground with the Pi.

**Device nodes**

| Class | Nodes |
|---|---|
| I2C | `/dev/i2c-1`, `/dev/i2c-20`, `/dev/i2c-21` |
| GPIO | `/dev/gpiochip0`, `/dev/gpiochip1`, `/dev/gpiochip4 → gpiochip0` |
| Serial | `/dev/serial0 → /dev/ttyS0` (GSM) · `/dev/ttyAMA3` (GPS) · `/dev/ttyAMA5` (voice module) |
| Video | USB camera: `/dev/video0`, `/dev/video1`, `/dev/media1`. The others belong to the bcm2835 codec, ISP and HEVC decoder |

---

## 4. Detected devices

**USB**

```text
Bus 002 Device 002: ID 174c:55aa ASMedia ASM1051E/1053E/1153 SATA bridge   (SSD)
Bus 001 Device 005: ID 32e6:9221 icSpring Web Camera                      (camera + mic)
Bus 001 Device 004: ID 09da:8736 A4Tech USB Mouse                         (dev peripheral)
Bus 001 Device 003: ID 046d:c31c Logitech Keyboard K120                   (dev peripheral)
Bus 001 Device 002: ID 2109:3431 VIA Labs Hub
```

**Audio**

| Direction | Device |
|---|---|
| Capture | card 3: `Camera [Web Camera]`, USB Audio |
| Playback | card 0: `bcm2835 Headphones` (3.5 mm) · cards 1–2: `vc4-hdmi-0/1` |

---

## 5. Firmware configuration

`/boot/firmware/config.txt` (active settings):

```ini
dtparam=i2c_arm=on
dtparam=audio=on
camera_auto_detect=1
display_auto_detect=1
auto_initramfs=1
dtoverlay=vc4-kms-v3d
max_framebuffers=2
disable_fw_kms_setup=1
arm_64bit=1
disable_overscan=1
arm_boost=1

[cm4]
otg_mode=1

[cm5]
dtoverlay=dwc2,dr_mode=host

[all]
enable_uart=1
dtoverlay=uart3              # NEO-6M GPS on GPIO4/5
dtoverlay=uart5              # Voice recognition module on GPIO12/13
#dtoverlay=disable-bt        # Bluetooth stays enabled for the BLE server
force_turbo=1
core_freq=250
```

SPI and I2S are off. `core_freq=250` keeps the GPU core clock fixed, so the mini-UART baud rate used by the GSM module on `/dev/serial0` stays stable.

---

## 6. HelmX services

### BLE server: `helmx-ble.service`

| | |
|---|---|
| Command | `/usr/bin/python3 /home/helmx/bluetooth.py` · runs as root in `/home/helmx` |
| Libraries | Bless 0.3.0 on BlueZ / dbus-next, Adafruit Blinka + DHT, RPi.GPIO |
| Advertised name | `HelmX` |
| Service UUID | `0000FFE0-0000-1000-8000-00805F9B34FB` |
| Characteristic | `0000FFE1-0000-1000-8000-00805F9B34FB` (read / notify) |
| Payload | JSON with `temperature`, `humidity`, `air_quality` and `destination` |
| Timing | Sensor update every 2.5 s · `sensor_data.json` written every 10 s |
| Navigation | Reads `navigation_target.json`, sends its destination, then clears the file |
| Restart | `Restart=always`, 3 s delay, waits 5 s before starting |

### Voice assistant: `helmx_assistant.service`

| | |
|---|---|
| Command | `/usr/bin/python3 /home/helmx/helmx_assistant.py` · runs as user `helmx` |
| Depends on | Mosquitto and Rhasspy (`Wants=`), starts after `network-online.target` |
| Messaging | paho-mqtt 2.1.0 through the local Mosquitto broker |
| Audio | PulseAudio-compatible socket `/run/user/1000/pulse/native` with `XDG_RUNTIME_DIR=/run/user/1000` |
| Skills | Sensor answers, navigation, music (`mpg123`), photos (`fswebcam` / `ffmpeg`), 10-second video (`ffmpeg`) from `/dev/video0` |
| Storage | Media in `/home/helmx/helmx_vault` · log at `/home/helmx/helmx_debug.log` |
| Restart | `Restart=always`, 5 s delay |

### Rhasspy: `rhasspy.service`

| | |
|---|---|
| Command | `/usr/bin/rhasspy --profile en` · user and group `helmx` |
| Profile | `/home/helmx/.config/rhasspy/profiles/en/profile.json` |
| Pipeline | Microphone **PyAudio** → wake word **Porcupine** → speech-to-text **Kaldi** → intent **fsticuffs** → dialogue **Rhasspy** → text-to-speech **NanoTTS** → playback **aplay** |
| Restart | Waits 10 s before starting · `Restart=always`, 5 s delay |

### Crash monitor: `helmx-crash-monitor.service`

| | |
|---|---|
| Command | `deploy/crash_monitor.py` from the [`crash-detection`](https://github.com/Usman-Azfar/HelmX-AI-Powered-Smart-Helmet/tree/crash-detection) branch |
| Model | INT8 TensorFlow Lite hybrid classifier + autoencoder |
| Pipeline | IMU at 50 Hz → timing guard → 1.2 s window → model → 3-window confirmation → alarm and 30 s cancel → GPS fix → GSM SMS |

### Supporting services

| Service | Purpose |
|---|---|
| `mosquitto.service` | Local MQTT broker on `localhost:1883` |
| `bluetooth.service` | BlueZ daemon |
| `pipewire`, `pipewire-pulse`, `wireplumber` (user) | Audio server with the PulseAudio compatibility layer |
| `supervisor.service` | Process supervisor |
| `helmx-research-boot-capture.service` | Boot-time identity and stationary capture for research (one-shot, armed on demand) |
| `helmx-cold-warm-research.service` | Cold-start and warm-start raw capture for research (one-shot, armed on demand) |

The application scripts (`bluetooth.py`, `helmx_assistant.py`) and the Rhasspy profile live on the Pi under `/home/helmx`. Their SHA-256 hashes are recorded in [section 11](#11-file-hashes).

---

## 7. Service units

<details>
<summary><code>/etc/systemd/system/helmx-ble.service</code></summary>

```ini
[Unit]
Description=HelmX BLE Server
After=bluetooth.service
Requires=bluetooth.service

[Service]
ExecStart=/usr/bin/python3 /home/helmx/bluetooth.py
WorkingDirectory=/home/helmx
Restart=always
RestartSec=3
User=root

# Optional but improves stability
ExecStartPre=/bin/sleep 5

[Install]
WantedBy=multi-user.target
```
</details>

<details>
<summary><code>/etc/systemd/system/helmx_assistant.service</code></summary>

```ini
[Unit]
Description=HelmX Python Assistant
After=network-online.target mosquitto.service rhasspy.service
Wants=mosquitto.service rhasspy.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/helmx/helmx_assistant.py
WorkingDirectory=/home/helmx
Restart=always
RestartSec=5
User=helmx

[Install]
WantedBy=multi-user.target
```
</details>

<details>
<summary><code>/etc/systemd/system/rhasspy.service</code></summary>

```ini
[Unit]
Description=Rhasspy Voice Assistant
After=network-online.target mosquitto.service sound.target
Wants=network-online.target mosquitto.service

[Service]
Type=simple
User=helmx
Group=helmx
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/rhasspy --profile en
WorkingDirectory=/home/helmx
Environment=HOME=/home/helmx
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
</details>

<details>
<summary><code>/etc/systemd/system/helmx-research-boot-capture.service</code></summary>

```ini
[Unit]
Description=HelmX armed research identity and stationary boot capture
After=local-fs.target dev-i2c\x2d1.device
Wants=dev-i2c\x2d1.device
ConditionPathExists=/home/helmx/Crash Detection/Crash-Detection/piResults/final_pi_review_closure/metadata/boot_capture_arm.json

[Service]
Type=simple
User=helmx
Group=helmx
SupplementaryGroups=i2c gpio
WorkingDirectory=/home/helmx/Crash Detection/Crash-Detection
ExecStart="/home/helmx/Crash Detection/Crash-Detection/.pi_research_venv/bin/python" "/home/helmx/Crash Detection/Crash-Detection/piResults/final_pi_review_closure/scripts/boot_capture.py" run
TimeoutStopSec=30
Restart=no

[Install]
WantedBy=multi-user.target
```
</details>

<details>
<summary><code>/etc/systemd/system/helmx-cold-warm-research.service</code></summary>

```ini
[Unit]
Description=HelmX one-shot cold/warm research raw capture
After=local-fs.target dev-i2c\x2d1.device
Wants=dev-i2c\x2d1.device
Before=display-manager.service
ConditionPathExists=/home/helmx/Crash Detection/Crash-Detection/piResults/final_pi_review_closure/metadata/cold_warm_arm.json

[Service]
Type=simple
User=helmx
Group=helmx
SupplementaryGroups=i2c gpio
WorkingDirectory=/home/helmx/Crash Detection/Crash-Detection
ExecStart="/home/helmx/Crash Detection/Crash-Detection/.pi_research_venv/bin/python" "/home/helmx/Crash Detection/Crash-Detection/piResults/final_pi_review_closure/scripts/cold_warm_capture.py" run
TimeoutStopSec=30
Restart=no

[Install]
WantedBy=multi-user.target
```
</details>

---

## 8. Crash detection deployment

| | |
|---|---|
| Repository on the Pi | `/home/helmx/Crash Detection/Crash-Detection`. Published as the [`crash-detection`](https://github.com/Usman-Azfar/HelmX-AI-Powered-Smart-Helmet/tree/crash-detection) branch |
| Research environment | `.pi_research_venv` on Python 3.11.2 with system site packages |

**`deploy/config.yaml`**

| Setting | Value |
|---|---|
| Model | `models/helmx_crash_model_int8.tflite` |
| Normaliser / thresholds | `models/normalizer.npz` / `models/thresholds.json` |
| Sampling | 50 Hz · window 60 samples · stride 15 samples |
| Gravity filter | 0.3 Hz cutoff |
| Timing guard | Gap between samples 0.010–0.060 s · reset after a gap of more than 1.0 s |
| Confirmation | 3 consecutive anomalous windows · 60 s cooldown |
| Alarm | 30 s countdown on BCM18 · cancel signal `/tmp/helmx_cancel_alert` |
| GPS | NEO-6M on `/dev/ttyAMA3` · 15 s fix timeout |
| GSM | SIM800L on `/dev/serial0` at 9600 baud |
| Logging | `logs/crash_monitor.log`, INFO level, 5,000,000 bytes with 3 backups |

**`models/thresholds.json`**

```json
{
  "recon_error": 10.878735866546593,
  "recon_error_peak": 134.2400975036617,
  "classifier_prob_balanced": 0.9892255067825317,
  "classifier_prob_moderate_recall": 0.9772439002990723,
  "classifier_prob_high_recall": 0.76202392578125,
  "classifier_prob": 0.9892255067825317
}
```

**Research runs completed on the Pi**

| Study | Run ID |
|---|---|
| D4 (randomised) | `randomized_D4_20261011T065644991406Z` ✅ |
| K1 (randomised) | `randomized_K1_20261011T103536168830Z` ✅ |
| I2 (cold / warm start) | `cold_warm_20261007T141614Z`, reviewed in `I2_review_20261011` ✅ |

Research root: `piResults/final_pi_review_closure` · runner: `scripts/randomized_studies.py` · plan: `randomized_studies_v2_20261011/plan.json`.

---

## 9. Software versions

| Component | Version |
|---|---|
| System Python | 3.11.2 |
| NumPy (system / research venv) | 1.24.2 / 1.26.4 |
| TensorFlow (research venv) | 2.16.1 |
| tflite-runtime (research venv) | 2.14.0 |
| Keras / scikit-learn / SciPy / pandas (venv) | 3.15.1 / 1.9.0 / 1.17.1 / 3.0.5 |
| Bless / dbus-next / bleak | 0.3.0 / 0.2.3 / 3.0.1 |
| paho-mqtt | 2.1.0 |
| Adafruit Blinka / CircuitPython DHT | 9.1.0 / 4.0.12 |
| RPi.GPIO / gpiozero / smbus2 / pyserial | 0.7.1 / 2.0.1 / 0.4.2 / 3.5 |
| mpu6050-raspberrypi | 1.2 |
| picamera2 / OpenCV (Debian) | 0.3.31 / 4.6.0 |
| BlueZ | 5.66-1+rpt2+deb12u2 |
| Mosquitto | 2.0.11-1.2+deb12u2 |
| Rhasspy | 2.5.11 |
| PipeWire / PulseAudio | 1.2.7 / 16.1 |
| ffmpeg / fswebcam / mpg123 | 5.1.9 / 20140113 / 1.31.2 |
| libcamera / rpicam-apps | 0.5.2 / 1.9.0 |

---

## 10. Service overview

| Service | Role | State | Starts at boot |
|---|---|:---:|:---:|
| `helmx-ble.service` | Bluetooth link to the Android app | ✅ Running | ✅ |
| `helmx_assistant.service` | Voice assistant skills | ✅ Running | ✅ |
| `rhasspy.service` | Offline speech pipeline | ✅ Running | ✅ |
| `mosquitto.service` | MQTT message bus | ✅ Running | ✅ |
| `helmx-crash-monitor.service` | Crash detection and emergency alert | ✅ Running | ✅ |
| `bluetooth.service` | BlueZ Bluetooth stack | ✅ Running | ✅ |
| `helmx-research-boot-capture.service` | Research capture (one-shot) | Armed on demand | ✅ |
| `helmx-cold-warm-research.service` | Research capture (one-shot) | Armed on demand | ✅ |

| Peripheral | Bus | State |
|---|---|:---:|
| MPU6050 IMU | I2C1 | ✅ Working |
| SIM800L GSM | UART0 | ✅ Working |
| NEO-6M GPS | UART3 | ✅ Working |
| Voice recognition module | UART5 | ✅ Working |
| DHT22 / MQ135 | GPIO | ✅ Working |
| IR night-vision camera / USB camera | CSI / USB | ✅ Working |
| Speakers | Audio | ✅ Working |

---

## 11. File hashes

SHA-256 hashes of the deployed application, configuration and model files:

```text
8bea44a2a023098037448b44e920b8f79a7b3b967d4e600decad1704550dedf1  /home/helmx/bluetooth.py
38113863a73825d94c5cf5ad60827e6f44fc8f0f7ba4fa83abb809694c4ce06d  /home/helmx/helmx_assistant.py
1f8fb2480a6bd9c213ad332cad75107b7e8fb89a04380641e7914d36c1e95ae5  Crash-Detection/deploy/config.yaml
2e59379601b02706e97832a93e72bb954a5b62e4ba77ccd82acbcbaa0a515bd6  Crash-Detection/models/helmx_crash_model_int8.tflite
747b123d2741c0adf7e42b9cd1dea945128d341168a4b55adb85f781b45336b5  Crash-Detection/models/normalizer.npz
f61e2fa4122d9b1944c36d67eddaf4c20dde53961c2822804a032875ac2b50de  Crash-Detection/models/thresholds.json
```

---

[← Back to the project overview](../../README.md)
