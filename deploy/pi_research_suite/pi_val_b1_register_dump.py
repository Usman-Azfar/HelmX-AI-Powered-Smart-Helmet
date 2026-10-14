"""HelmX_FInal_Pi_REqwuirements.md Section B1 -- full MPU6050 register readback
on the actual deployed helmet/Pi configuration. Reads raw register values via
smbus2 (same I2C bus/address the mpu6050-raspberrypi library and
deploy/crash_monitor.py use) and decodes them.

Run on the Pi:
    .pi_research_venv/bin/python deploy/pi_research_suite/pi_val_b1_register_dump.py
"""
import json
import sys
from pathlib import Path

import smbus2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

REGISTERS = {
    "SMPLRT_DIV": 0x19, "CONFIG": 0x1A, "GYRO_CONFIG": 0x1B, "ACCEL_CONFIG": 0x1C,
    "FIFO_EN": 0x23, "INT_ENABLE": 0x38, "INT_STATUS": 0x3A,
    "PWR_MGMT_1": 0x6B, "PWR_MGMT_2": 0x6C, "WHO_AM_I": 0x75,
    "USER_CTRL": 0x6A,
}

ACCEL_FS_MAP = {0: "+/-2g", 1: "+/-4g", 2: "+/-8g", 3: "+/-16g"}
GYRO_FS_MAP = {0: "+/-250 deg/s", 1: "+/-500 deg/s", 2: "+/-1000 deg/s", 3: "+/-2000 deg/s"}
DLPF_BANDWIDTH_MAP = {
    0: "260Hz accel / 256Hz gyro (DLPF off)", 1: "184Hz / 188Hz", 2: "94Hz / 98Hz",
    3: "44Hz / 42Hz", 4: "21Hz / 20Hz", 5: "10Hz / 10Hz", 6: "5Hz / 5Hz", 7: "reserved",
}
CLKSEL_MAP = {
    0: "internal 8MHz oscillator", 1: "PLL with X gyro reference", 2: "PLL with Y gyro reference",
    3: "PLL with Z gyro reference", 4: "PLL with external 32.768kHz", 5: "PLL with external 19.2MHz",
    6: "reserved", 7: "internal oscillator, timing generator in reset",
}


def decode(regs):
    pwr1 = regs["PWR_MGMT_1"]
    cfg = regs["CONFIG"]
    gyro_cfg = regs["GYRO_CONFIG"]
    accel_cfg = regs["ACCEL_CONFIG"]
    smplrt_div = regs["SMPLRT_DIV"]
    dlpf_cfg = cfg & 0x07
    gyro_fs_sel = (gyro_cfg >> 3) & 0x03
    accel_afs_sel = (accel_cfg >> 3) & 0x03
    clksel = pwr1 & 0x07
    sleep_bit = bool(pwr1 & (1 << 6))
    gyro_output_rate_hz = 8000 if dlpf_cfg == 0 else 1000
    sample_rate_hz = gyro_output_rate_hz / (1 + smplrt_div)

    return {
        "accel_full_scale": ACCEL_FS_MAP.get(accel_afs_sel), "accel_afs_sel_raw": accel_afs_sel,
        "gyro_full_scale": GYRO_FS_MAP.get(gyro_fs_sel), "gyro_fs_sel_raw": gyro_fs_sel,
        "dlpf_mode_bandwidth": DLPF_BANDWIDTH_MAP.get(dlpf_cfg), "dlpf_cfg_raw": dlpf_cfg,
        "smplrt_div_raw": smplrt_div,
        "gyro_output_rate_hz_before_divider": gyro_output_rate_hz,
        "configured_sample_rate_hz": sample_rate_hz,
        "device_clock_source": CLKSEL_MAP.get(clksel), "clksel_raw": clksel,
        "sleep_mode": sleep_bit,
        "fifo_enabled_register_nonzero": bool(regs["FIFO_EN"] != 0),
        "fifo_en_raw": regs["FIFO_EN"],
        "data_ready_interrupt_enabled": bool(regs["INT_ENABLE"] & 0x01),
        "int_enable_raw": regs["INT_ENABLE"],
        "int_status_data_ready": bool(regs["INT_STATUS"] & 0x01),
        "who_am_i": hex(regs["WHO_AM_I"]),
        "who_am_i_expected_0x68": regs["WHO_AM_I"] == 0x68,
    }


def main():
    cfg = common.load_config()
    address = cfg["sensor"]["i2c_address"]
    bus_num = 1  # standard Pi I2C bus for the header pins (i2cdetect -y 1 confirmed 0x68 here)

    bus = smbus2.SMBus(bus_num)
    raw = {}
    for name, reg in REGISTERS.items():
        raw[name] = bus.read_byte_data(address, reg)

    # I2C bus clock/baudrate from the kernel's device-tree-configured setting.
    i2c_baudrate = None
    for candidate in Path("/sys/class/i2c-adapter").glob(f"i2c-{bus_num}*"):
        pass
    try:
        import subprocess
        out = subprocess.run(["bash", "-c", "vcgencmd get_config i2c_baudrate 2>/dev/null || true"],
                              capture_output=True, text=True, timeout=2)
        if "=" in out.stdout:
            i2c_baudrate = out.stdout.strip()
    except Exception:
        pass
    if i2c_baudrate is None:
        try:
            dt_paths = list(Path("/proc/device-tree").rglob("i2c@*/clock-frequency"))
            if dt_paths:
                data = dt_paths[0].read_bytes()
                i2c_baudrate = f"{int.from_bytes(data, 'big')} Hz (device-tree clock-frequency)"
        except Exception:
            pass

    report = {
        "device": common.device_info(),
        "i2c_bus": bus_num, "i2c_address": hex(address),
        "i2c_baudrate": i2c_baudrate,
        "raw_hex": {name: hex(v) for name, v in raw.items()},
        "raw_binary": {name: format(v, "#010b") for name, v in raw.items()},
        "decoded": decode(raw),
    }

    print(json.dumps(report, indent=2))

    out_dir = common.ROOT / "piResults" / "results" / "final-validation" / "mpu_config"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "mpu6050_register_dump.json").write_text(json.dumps(report, indent=2))

    lines = [f"MPU6050 register dump -- {report['device'].get('model')}, I2C {hex(address)}, bus {bus_num}", ""]
    for name in REGISTERS:
        lines.append(f"{name:15s} (0x{REGISTERS[name]:02X}) = {report['raw_hex'][name]}  ({report['raw_binary'][name]})")
    lines.append("")
    lines.append("Decoded:")
    for k, v in report["decoded"].items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append(f"I2C baudrate: {i2c_baudrate}")
    (out_dir / "mpu6050_register_dump.txt").write_text("\n".join(lines))
    print(f"\nWrote {out_dir / 'mpu6050_register_dump.json'} and .txt")


if __name__ == "__main__":
    main()
