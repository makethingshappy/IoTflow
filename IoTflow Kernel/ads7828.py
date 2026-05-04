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
================================================================================
ADS7828 I2C Analog-to-Digital Converter Driver
================================================================================

Author: Arshia Keshvari
Last Updated: 2026/05/04

Description:
This module provides a MicroPython driver for the ADS7828 12-bit, 8-channel
analog-to-digital converter (ADC) communicating over I2C.

The ADS7828 is a low-power, single-ended input ADC with an internal 2.5V
reference. It supports up to 8 multiplexed analog input channels and is
commonly used for moderate-precision voltage and current measurements.

Key Features:
- 8 single-ended analog input channels (CH0–CH7)
- 12-bit resolution ADC
- Internal 2.5V reference voltage
- I2C communication interface
- Low-power operation with automatic power-down between conversions
- Fast conversion time suitable for real-time sensor sampling

Usage Context:
This driver is designed to be used as part of the IoTextra Analog Driver
system, where it provides raw ADC readings that are later converted into
engineering units (voltage/current) by higher-level abstraction layers.

Dependencies:
- MicroPython machine.I2C
- time (for conversion delay)

================================================================================
"""

from machine import I2C
import time

class ADS7828:
    # Channel configuration bits (per datasheet)
    _CHANNEL_MAP = [
        0x00,  # CH0
        0x40,  # CH1
        0x10,  # CH2
        0x50,  # CH3
        0x20,  # CH4
        0x60,  # CH5
        0x30,  # CH6
        0x70,  # CH7
    ]

    _SD_BIT  = 0x80  # Single-ended mode
    _PD_BITS = 0x0C  # Power-down mode
    _VREF = 2.5  # Reference voltage

    def __init__(self, i2c: I2C, addr=0x4B):
        self.i2c = i2c
        self.addr = addr

    def _build_command(self, channel):
        return self._SD_BIT | self._CHANNEL_MAP[channel] | self._PD_BITS

    def read_channel(self, channel: int) -> int:
        """Read a single channel (returns raw 12-bit value)."""
        cmd = bytes([self._build_command(channel)])
        self.i2c.writeto(self.addr, cmd)
        time.sleep_us(100)  # wait for conversion: datasheet ~6us give margin
        # Read result — this returns the conversion just triggered
        data = self.i2c.readfrom(self.addr, 2)
        return ((data[0] & 0x0F) << 8) | data[1]

    def read_all_channels(self) -> list:
        """Read all 8 channels."""
        return [self.read_channel(ch) for ch in range(8)]

    def raw_to_v(self, raw):
        return raw * self._VREF / 4095.0