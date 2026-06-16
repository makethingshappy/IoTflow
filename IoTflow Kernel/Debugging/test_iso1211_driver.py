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
Title: ISO1211 Sampled-Mode DI Driver Test
Description:
  Hardware-in-the-loop sanity test for `iso1211_driver.py` (IoTflow Kernel).

  This test runs the driver standalone (no MQTT / no main.py) so you can verify:
    1. STARTUP SAFETY  - every fgnd_gpio is de-asserted (TLP188 OFF) on init,
                         before anything else, including invalid channels.
    2. VALIDATION      - a channel with a missing/invalid fgnd_gpio is rejected
                         (logged) and skipped.
    3. NON-BLOCKING    - update() drives a round-robin scan
                         (assert FGND -> wait t_settle -> read OUT -> de-assert),
                         one FGND asserted at a time, with no blocking sleeps.
    4. OUT READ        - reads OUT via TCA9534 (i2c) or a direct GPIO pin (gpio),
                         and reports per-channel value + error flag.

HOW TO RUN
  Copy iso1211_driver.py + this file to the device and run this file
  (e.g. in Thonny / mpremote). Adjust the "User knobs" below to match your
  wiring. Press Ctrl+C to stop; FGND is de-asserted on exit.

SAFETY
  Use a low/safe field voltage (or no field voltage) for first power-on bring-up.
  Confirm with a meter/scope that each fgnd_gpio sits at the inactive level
  immediately after the driver prints its startup-safety line.

Author: Arshia Keshvari
Role: Independent Developer, Engineer, and Project Author
Last Updated: 2026-06-15
"""

import sys
import time

# Allow running from the Debugging/ subfolder OR from a flat on-device layout.
sys.path.append("..")
sys.path.append("/")

from machine import Pin, I2C
from iso1211_driver import Iso1211Driver

# -----------------------------------------------------------------------------
# User knobs - edit to match your board / wiring
# -----------------------------------------------------------------------------
I2C_BUS_ID = 0
I2C_SDA_PIN = 11
I2C_SCL_PIN = 12
I2C_FREQ = 400000

# TCA9534 I/O-expander address used for i2c OUT reads (same as config I2C_DEVICE_ADDR).
TCA9534_ADDR = 0x27

# HOST connector pin map (channel 1-8 -> GPIO). Used to resolve the OUT pin for
# gpio out_source channels when "out_gpio" is not given. Mirrors config.py.
GPIO_HOST_PINS = {
    1: 9, 2: 10, 3: 17, 4: 18,
    5: 3, 6: 2, 7: 18, 8: 19,
}

# Optional override of the universal settle time for this test run (ms).
# Leave as None to use the driver default (T_SETTLE_MS = 25 ms).
T_SETTLE_MS_OVERRIDE = None

# How often to print a full status snapshot (ms).
SNAPSHOT_MS = 250

# Sampled-mode ISO1211 channels under test.
#   channel_type "3"  -> ISO1211 sampled-mode DI
#   interface_type    -> "01" = OUT via GPIO,  "11" = OUT via TCA9534
#   fgnd_gpio         -> HOST pin driving TLP188/FGND (REQUIRED, unique to sampled mode)
#   out_gpio          -> OPTIONAL explicit OUT pin for interface_type "01"
TEST_CHANNELS = [
    {  # OUT read over the TCA9534 expander (bit = channel_number)
        "name": "IN1",
        "channel_type": "3",
        "interface_type": "11",
        "channel_number": 0,
        "actions": 0,
        "fgnd_gpio": 18,
    },
    {  # OUT read over a direct MCU GPIO pin
        "name": "IN2",
        "channel_type": "3",
        "interface_type": "01",
        "channel_number": 1,
        "actions": 0,
        "fgnd_gpio": 17,
        "out_gpio": 10,
    },
    {  # INVALID on purpose: missing fgnd_gpio -> should be rejected & skipped
        "name": "BAD",
        "channel_type": "3",
        "interface_type": "11",
        "channel_number": 2,
        "actions": 0,
    },
    {  # Direct-mode DI (channel_type "1") -> driver must IGNORE this entirely
        "name": "DIRECT",
        "channel_type": "1",
        "interface_type": "01",
        "channel_number": 3,
        "actions": 0,
    },
]


def _hex_list(int_addrs):
    return [hex(a) for a in int_addrs]


def main():
    i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

    print("Scanning I2C bus...")
    scanned = i2c.scan()
    print("I2C devices found:", len(scanned), _hex_list(scanned))
    if TCA9534_ADDR not in scanned:
        print("WARNING: TCA9534 0x{:02X} not on the bus - i2c OUT reads will "
              "report per-channel errors (this is expected if unwired).".format(TCA9534_ADDR))

    print("\n--- Constructing driver (watch for the startup-safety line) ---")
    if T_SETTLE_MS_OVERRIDE is None:
        drv = Iso1211Driver(i2c, TCA9534_ADDR, GPIO_HOST_PINS, TEST_CHANNELS)
    else:
        drv = Iso1211Driver(i2c, TCA9534_ADDR, GPIO_HOST_PINS, TEST_CHANNELS,
                            t_settle_ms=T_SETTLE_MS_OVERRIDE)

    drv.print_channel_configs()

    if not drv.has_channels():
        print("No valid sampled-mode channels were configured. Check fgnd_gpio "
              "values in TEST_CHANNELS. Nothing to scan - exiting.")
        return

    print("Starting non-blocking scan loop. Press Ctrl+C to stop.\n")
    last_snapshot = time.ticks_ms()
    try:
        while True:
            # Drive the round-robin state machine. Never blocks.
            result = drv.update()
            if result is not None:
                channel, value, changed = result
                tag = "CHANGED" if changed else "same"
                print("  [scan] channel {} -> {} ({})".format(channel, value, tag))

            # Periodic full snapshot of last values + error flags.
            now = time.ticks_ms()
            if time.ticks_diff(now, last_snapshot) >= SNAPSHOT_MS:
                print("--- snapshot --- values={} errors={}".format(
                    drv.get_values(), drv.get_errors()))
                last_snapshot = now

            # Cooperative pacing, mirrors the main run-loop granularity (~10 ms).
            time.sleep_ms(5)
    except KeyboardInterrupt:
        print("\nStopping - de-asserting all FGND (TLP188 OFF).")
        drv.deassert_all()


main()
