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

from machine import I2C, Pin
from EEPROM_driver import EEPROM

i2c = I2C(0, sda=Pin(16), scl=Pin(15), freq=400000)  # your pins
ee = EEPROM(i2c, 0x57)  # or whatever EEPROM_I2C_ADDR is

raw = ee.read_bytes(0x3F0, 4)
print("raw:", [hex(b) for b in raw])

if raw[0:2] != b'O3' or raw[2] != 0x01:
    print("No valid Octal3 state stored yet")
else:
    mask = raw[3]
    print("bitmask:", hex(mask), bin(mask))
    for ch in range(1, 9):
        print(f"  CH{ch}: {'ON' if mask & (1 << (ch - 1)) else 'OFF'}")