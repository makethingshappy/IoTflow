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
test_iot_driver_relay.py - Test script for IoTextra Relay on IoTsmart ESP32-S3

IoTextra Relay host-pin roles are FIXED, MCU-to-MCU (only the underlying
GPIO numbers change between boards - the role of each host-pin position
never does):

    Host pin 1 (AP0) -> CH1 SPST GPIO output (RS1)
    Host pin 2 (AP1) -> CH2 SPST GPIO output (RS2)
    Host pin 3 (AP2) -> CH3 SPST GPIO output (RS3)
    Host pin 4 (AP3) -> CH4 SPST GPIO output (RS4)
    Host pin 5 (AP4) -> unused
    Host pin 6 (AP5) -> nSLEEP  (always, every MCU)
    Host pin 7 (AP6) -> unused
    Host pin 8 (AP7) -> unused

    CH1-4 SPST outputs (RS1-RS4) -> ordinary active-low host GPIO (same as
    other digital GPIO outputs).

    CH5-8 latching outputs (RL1-RL4) -> pure I2C via the TCA9534 (+ nSLEEP
    on host pin 6). They have no host GPIO pin of their own at all.

Configuration under test:
    Hardware mode : I2C (TCA9534 for latching relays)
    I2C bus       : id=0, SDA=GPIO16, SCL=GPIO15, address=0x27
    pin_config    : 0b00000000  (all 8 channels = output)

You only need to fill in GPIO_HOST_PINS below with this board's real GPIO
numbers for positions 1-8 (matching your wiring/schematic) - everything
else is derived automatically.
"""

import time
from iot_driver import IotDriver

# --- Fill in the real MCU GPIO number behind each host-pin position -----
# (values for 5, 7, 8 can be left as None - Relay never uses them, but
# leaving them in the table keeps this consistent with your board's full
# host-pin pinout documentation)
GPIO_HOST_PINS = {
    1: 8,     # AP0 -> CH1 SPST (RS1)
    2: 9,     # AP1 -> CH2 SPST (RS2)
    3: 10,    # AP2 -> CH3 SPST (RS3)
    4: 11,    # AP3 -> CH4 SPST (RS4)
    5: None,  # AP4 -> unused
    6: 5,     # AP5 -> nSLEEP (always)
    7: None,  # AP6 -> unused
    8: None,  # AP7 -> unused
}

BUS_ID = 0
SDA_PIN = 16
SCL_PIN = 15
DEVICE_ADDRESS = 0x27

PIN_CONFIG = 0b00000000  # all outputs
LATCHING_CHANNELS = {5, 6, 7, 8}
SPST_CHANNELS = [1, 2, 3, 4]
LATCHING_OUTPUT_CHANNELS = [5, 6, 7, 8]

_RELAY_GPIO_HOST_PIN_TO_CHANNEL = {1: 1, 2: 2, 3: 3, 4: 4}
_RELAY_NSLEEP_HOST_PIN = 6


def relay_config_from_host_pins(host_pins):
    """
    Translate a full physical host-pin table (position 1-8 -> MCU GPIO
    number) into the (gpio_host_pins, nsleep_pin) IotDriver expects for
    an IoTextra Relay board.
    """
    required = set(_RELAY_GPIO_HOST_PIN_TO_CHANNEL) | {_RELAY_NSLEEP_HOST_PIN}
    missing = [p for p in required if host_pins.get(p) is None]
    if missing:
        raise ValueError(f"host_pins is missing a GPIO number for required position(s): {sorted(missing)}")

    gpio_host_pins = {
        channel: host_pins[host_pin]
        for host_pin, channel in _RELAY_GPIO_HOST_PIN_TO_CHANNEL.items()
    }
    nsleep_pin = host_pins[_RELAY_NSLEEP_HOST_PIN]
    return gpio_host_pins, nsleep_pin


def main():
    gpio_host_pins, nsleep_pin = relay_config_from_host_pins(GPIO_HOST_PINS)

    driver = IotDriver(
        bus_id=BUS_ID,
        sda_pin=SDA_PIN,
        scl_pin=SCL_PIN,
        device_address=DEVICE_ADDRESS,
        gpio_host_pins=gpio_host_pins,
        pin_config=PIN_CONFIG,
        hardware_mode="i2c",
        nsleep_pin=nsleep_pin,
        octal3_channels=LATCHING_CHANNELS,
    )

    print("\n=== Cycling each latching relay (CH5-8 / RL1-4) ON then OFF ===")
    for ch in LATCHING_OUTPUT_CHANNELS:
        print(f"\n-- Latching CH{ch} --")
        print(f"Setting CH{ch} ON")
        driver.set_output(ch, True)
        time.sleep_ms(300)

        print(f"Setting CH{ch} OFF")
        driver.set_output(ch, False)
        time.sleep_ms(300)

    print("\n=== Cycling each SPST GPIO relay (CH1-4 / RS1-4) ON then OFF ===")
    for ch in SPST_CHANNELS:
        print(f"\n-- SPST CH{ch} --")
        print(f"Setting CH{ch} ON")
        driver.set_output(ch, True)
        time.sleep_ms(500)

        print(f"Setting CH{ch} OFF")
        driver.set_output(ch, False)
        time.sleep_ms(300)

    print("\nTest complete. All outputs commanded OFF.")


if __name__ == "__main__":
    main()
