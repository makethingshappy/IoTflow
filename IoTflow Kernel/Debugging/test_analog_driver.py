# MIT License
#
# Copyright (c) 2025 makethingshappy,
#               2025 Arshia Keshvari (@TeslaNeuro)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Title: AnalogDriver ADC Test
Description:
  Quick sanity test for `analog_driver.py` with BOTH ADC backends:
  - ADS7828 when cfg["mezzanine_type"] == "IoTextra Analog V3"
  - ADS1115 otherwise

Author: Arshia Keshvari
Role: Independent Developer, Engineer, and Project Author
Last Updated: 2026-05-04
"""

from machine import Pin, I2C
import time
from analog_driver import AnalogDriver


# ---- User knobs ----
MEZZANINE_TYPE = "IoTextra Analog V3"  # set to anything else to test ADS1115 path
I2C_BUS_ID = 0
I2C_SDA_PIN = 16
I2C_SCL_PIN = 15
I2C_FREQ = 400000

# If None, we'll try to auto-pick a sane default from scan results.
ADC_ADDRS = None  # e.g. ["0x4b"] for ADS7828, ["0x49"] for ADS1115

# ADS1115 uses this; ADS7828 ignores it (kept for config compatibility)
ADC_SAMPLING_RATE = 128

POLL_MS = 500


def _hex_list(int_addrs):
    return [hex(a) for a in int_addrs]


def _pick_adc_addrs(mezzanine_type, scanned):
    if ADC_ADDRS is not None:
        return ADC_ADDRS

    mt = (mezzanine_type or "").strip()
    scanned_set = set(scanned or [])

    if mt == "IoTextra Analog V3":
        # Common ADS7828 addresses: 0x48..0x4B (A0/A1 strap). Default in driver is 0x4B.
        for cand in (0x4B, 0x4A, 0x49, 0x48):
            if cand in scanned_set:
                return [hex(cand)]
        return ["0x4b"]

    # ADS1115 common addresses: 0x48..0x4B. Pick the first one we actually see.
    for cand in (0x48, 0x49, 0x4A, 0x4B):
        if cand in scanned_set:
            return [hex(cand)]
    return ["0x48"]


def main():
    i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

    print("Scanning I2C bus...")
    scanned = i2c.scan()
    print("I2C devices found:", len(scanned), _hex_list(scanned))

    adc_i2c_addrs = _pick_adc_addrs(MEZZANINE_TYPE, scanned)
    print("Using mezzanine_type:", MEZZANINE_TYPE)
    print("Using adc_i2c_addrs:", adc_i2c_addrs)

    cfg = {
        "mezzanine_type": MEZZANINE_TYPE,
        "hardware": {
            "adc_i2c_addrs": adc_i2c_addrs,
            "adc_sampling_rate": ADC_SAMPLING_RATE,
        },
        "channels": [
            # Voltage example: 0-5V (after hardware scaling)
            {
                "name": "AIN0 Voltage 0-5V",
                "channel_type": "2",
                "interface_type": "01",
                "channel_number": 0,
                "actions": 0,
                "measurement_range": "0b00000010",
                "adc_hardware_gain": 0.23761904761904762,
                "shunt_resistance": 0.249,
                "adc_offset": 0.0,
            },
            # Current example: 0-20mA (after scaling + shunt)
            {
                "name": "AIN1 Current 0-20mA",
                "channel_type": "2",
                "interface_type": "01",
                "channel_number": 1,
                "actions": 0,
                "measurement_range": "0b00100001",
                "adc_hardware_gain": 0.23761904761904762,
                "shunt_resistance": 0.249,
                "adc_offset": 0.0,
            },
        ],
    }

    drv = AnalogDriver(i2c, cfg)
    drv.print_channel_configs()

    print("Starting read loop. Press Ctrl+C to stop.")
    while True:
        for ch in sorted(drv.channel_configs.keys()):
            raw = drv.read_channel_raw(ch)
            adc_v = drv.read_channel_voltage(ch)
            phys = drv.read_channel_physical(ch)

            ch_cfg = drv.get_channel_info(ch) or {}
            unit = "V" if ch_cfg.get("type") == "voltage" else "mA"

            print(
                "CH{} raw={} adc_v={:.6f}V physical={:.6f}{}".format(
                    ch,
                    raw,
                    adc_v if adc_v is not None else float("nan"),
                    phys if phys is not None else float("nan"),
                    unit,
                )
            )

        print("---")
        time.sleep_ms(POLL_MS)


main()

