# HelmX Raspberry Pi bring-up guide

[← Back to the project overview](../../README.md) · [Full Pi setup reference](PI_SETUP.md)

This guide takes a fresh Raspberry Pi 4 to a working HelmX helmet computer. Every value here matches the reference configuration in [PI_SETUP.md](PI_SETUP.md).

## Contents

1. [Flash and first boot](#1-flash-and-first-boot)
2. [Enable the buses and serial ports](#2-enable-the-buses-and-serial-ports)
3. [Wire the peripherals](#3-wire-the-peripherals)
4. [Check each peripheral](#4-check-each-peripheral)
5. [Install the HelmX services](#5-install-the-helmx-services)
6. [Final checklist](#6-final-checklist)

---

## 1. Flash and first boot

1. Flash **Raspberry Pi OS (64-bit, Bookworm)** to the SSD with Raspberry Pi Imager.
2. In the Imager settings, set the host name to `helx-pi` and create the user `helmx`.
3. Boot the Pi, connect Ethernet and update it:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo usermod -aG dialout,i2c,gpio,audio,video helmx
```

## 2. Enable the buses and serial ports

Add these lines to `/boot/firmware/config.txt`, then reboot:

```ini
dtparam=i2c_arm=on
enable_uart=1
dtoverlay=uart3              # NEO-6M GPS on GPIO4/5
dtoverlay=uart5              # Voice recognition module on GPIO12/13
core_freq=250                # Keeps the GSM baud rate on /dev/serial0 stable
```

In `sudo raspi-config` → **Interface Options** → **Serial Port**, turn the login shell **off** and the serial hardware **on**, so `/dev/serial0` is free for the GSM module. Bluetooth stays enabled for the BLE server.

After rebooting, confirm the ports exist:

```bash
ls -l /dev/serial0 /dev/ttyAMA3 /dev/ttyAMA5 /dev/i2c-1
```

## 3. Wire the peripherals

| Module | Pi pins (physical) | BCM | Bus / device |
|---|---|---|---|
| MPU6050 IMU | 3 (SDA) · 5 (SCL) | GPIO2 · GPIO3 | I2C1 `0x68` |
| SIM800L GSM | 8 (TX → module RX) · 10 (RX ← module TX) | GPIO14 · GPIO15 | UART0 `/dev/serial0` |
| NEO-6M GPS | 7 (TX → module RX) · 29 (RX ← module TX) | GPIO4 · GPIO5 | UART3 `/dev/ttyAMA3` |
| Voice recognition module | 32 (TX → module RX) · 33 (RX ← module TX) | GPIO12 · GPIO13 | UART5 `/dev/ttyAMA5` |
| MQ135 digital out | 11 | GPIO17 | input |
| Crash alarm | 12 | GPIO18 | output |
| DHT22 data | 15 | GPIO22 | data |
| IR night-vision camera | CSI connector | | libcamera |
| USB camera + microphone | any USB port | | `/dev/video0` |

All modules share a common ground with the Pi. The SIM800L needs its own supply that can deliver about 2 A during transmit bursts, so power it from the battery pack rather than the Pi's 3.3 V pin.

## 4. Check each peripheral

| Peripheral | Command | Expected result |
|---|---|---|
| IMU | `i2cdetect -y 1` | `68` in the address grid |
| GPS | `cat /dev/ttyAMA3` (9600 baud) | NMEA sentences such as `$GPGGA` and `$GPRMC` |
| GSM | send `AT` on `/dev/serial0` at 9600 baud | `OK` |
| Voice module | `stty -F /dev/ttyAMA5 9600 && cat /dev/ttyAMA5` | A command code each time a trained phrase is spoken |
| IR camera | `rpicam-hello --list-cameras` | One CSI camera listed |
| USB camera | `v4l2-ctl --list-devices` | `Web Camera` on `/dev/video0` |
| Microphone | `arecord -l` | `card 3: Camera [Web Camera]` |
| Speakers | `speaker-test -t wav -c 2 -l 1` | Voice test on both channels |

For the GSM check, `minicom -D /dev/serial0 -b 9600` gives an interactive terminal; `AT+CSQ` reports signal strength and `AT+CREG?` confirms network registration.

## 5. Install the HelmX services

```bash
# MQTT broker and audio tools
sudo apt install -y mosquitto mpg123 fswebcam ffmpeg i2c-tools minicom

# Python libraries for the BLE server and assistant
sudo pip3 install --break-system-packages bless paho-mqtt adafruit-circuitpython-dht RPi.GPIO
```

1. Install Rhasspy and create the `en` profile under `/home/helmx/.config/rhasspy/profiles/en/`.
2. Copy `bluetooth.py` and `helmx_assistant.py` to `/home/helmx`.
3. Clone the [`crash-detection`](https://github.com/Usman-Azfar/HelmX-AI-Powered-Smart-Helmet/tree/crash-detection) branch and set up its `deploy/` folder as described in its README.
4. Copy the unit files from [PI_SETUP.md, section 7](PI_SETUP.md#7-service-units) to `/etc/systemd/system/`, then enable them:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mosquitto rhasspy helmx-ble helmx_assistant helmx-crash-monitor
```

## 6. Final checklist

```bash
systemctl is-active mosquitto rhasspy helmx-ble helmx_assistant helmx-crash-monitor
vcgencmd get_throttled        # throttled=0x0
```

- [ ] All five services report `active`
- [ ] The Android app finds **HelmX** over Bluetooth and shows temperature, humidity and air quality
- [ ] Saying the wake word gets a spoken reply through the speakers
- [ ] A test crash alert sounds the alarm and can be cancelled within 30 seconds
- [ ] `throttled=0x0` with every service running
