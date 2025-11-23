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
==============================================================
 IoTExtra Firmware Configuration
--------------------------------------------------------------
 This script defines all configuration parameters for Wi-Fi,
 MQTT, hardware selection, ADC ranges, and channel definitions
 used by the IoTextra Hardware Modules

 Author: Arshia Keshvari
 Role: Independent Developer, Engineer, and Project Author
 Last Updated: 2025/11/23
==============================================================
"""

# Wi-Fi Network Credentials
WIFI_SSID = ""
WIFI_PASSWORD = ""

# MQTT Broker Configuration
MQTT_BROKER = "x"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "pico-iotextra-controller-1" # Should be unique for each device

# MQTT Topic Structure
# The firmware will publish sensor states to "base_topic/input/N/state"
# and listen for commands on "base_topic/output/N/set".
MQTT_BASE_TOPIC = "iotextra/device_1"

# Hardware Mode
HARDWARE_MODE = "i2c" # either "i2c" or "gpio"

# Hardware Configuration
# I2C mode Configuration
I2C_BUS_ID = 0     
I2C_SDA_PIN = 11 
I2C_SCL_PIN = 12
I2C_DEVICE_ADDR = 0x3f # The I2C address of the IoTExtra module

# EEPROM Configuration
EEPROM_I2C_ADDR = 0x57  # EEPROM I2C address (different from IoTExtra module) can be 0x27
EEPROM_SIZE = 1024       # EEPROM size in bytes
EEPROM_CONFIG_ADDR = 0   # Starting address for configuration storage

# ADS1115 ADC Configuration
# | ADDR pin connected to | I²C address (7-bit) |
# | --------------------- | ------------------- |
# | GND                   | `0x48`              |
# | VDD                   | `0x49`              |
# | SDA                   | `0x4A`              |
# | SCL                   | `0x4B`              |

ADC_I2C_ADDRS = [0x49, 0x4B]  # use a list for multiple ADCs
ADC_SAMPLING_RATE = 128        # Hz or whatever your firmware expects


# Voltage Ranges
# | Binary Code  | Range   | Polarity |
# | ------------ | ------- | -------- |
# | `0b00000001` | 0–0.5 V | Unipolar |
# | `0b00000010` | 0–5 V   | Unipolar |
# | `0b00000011` | 0–10 V  | Unipolar |
# | `0b10000001` | ±0.5 V  | Bipolar  |
# | `0b10000010` | ±5 V    | Bipolar  |
# | `0b10000011` | ±10 V   | Bipolar  |
# 
# Current Ranges
# | Binary Code  | Range   | Polarity |
# | ------------ | ------- | -------- |
# | `0b00100001` | 0–20 mA | Unipolar |
# | `0b10100001` | ±20 mA  | Bipolar  |
# | `0b00100010` | 4–20 mA | Unipolar |
# | `0b00100011` | 0–40 mA | Unipolar |

# Quick Reference
# Bit 5: 0 = Voltage, 1 = Current
# Bit 7: 0 = Unipolar, 1 = Bipolar
# Bits 0–1: Range selection

# ADS1115 ADC Voltage / Current Measurement Range
# EXAMPLE: ADC_MEASUREMENT_RANGE = 0b10000011

# GPIO mode Configuration
# Layout for GPIO pins on a HOST connector
# channel_number: gpio_pin
GPIO_HOST_PINS = {
    1: 10, # AP0
    2: 11, # AP1
    3: 12, # AP2
    4: 13, # AP3
    5: 14, # AP4
    6: 15, # AP5
    7: 18, # AP6
    8: 19, # AP7
}

# Pin Configuration of the board: 1 -> input channel, 0 -> output channel
# The channels are in this order 0b[P7][P6][P5][P4][P3][P2][P1][P0]
# You can find the pin configuration of the module on the schematic of the IoTExtra board
# IoTExtra Relay2 -> 0b11110000 ATTENTION: check the schematic (P4-P7 i.e. channels 5-8 are unused)
# IoTExtra Input -> 0b11111111
# IoTExtra Octal -> 0b00001111
# IoTExtra Combo -> 0b11000000
# IoTExtra Analog -> 0b00000000
PIN_CONFIG = 0b00001111


STATUS_UPDATE_INTERVAL_S = 30 # How often to publish status updates (in seconds)


CHANNELS = [
    {
      "name": "Sensor A",
      "channel_type": "2",
      "interface_type": "01",
      "channel_number": 0,
      "actions": 0,
      "measurement_range": "0b10000011",
      "adc_hardware_gain": 0.23761904761904762,
      "shunt_resistance": 0.249,
      "adc_offset": 0.0
    },
    {
      "name": "Sensor B",
      "channel_type": "2",
      "interface_type": "01",
      "channel_number": 1,
      "actions": 0,
      "measurement_range": "0b10100001",
      "adc_hardware_gain": 0.23761904761904762,
      "shunt_resistance": 0.249,
      "adc_offset": 0.0
    },
    {
      "name": "Sensor C",
      "channel_type": "2",
      "interface_type": "01",
      "channel_number": 2,
      "actions": 0,
      "measurement_range": "0b10000011",
      "adc_hardware_gain": 0.23761904761904762,
      "shunt_resistance": 0.249,
      "adc_offset": 0.0
    },
    {
      "name": "Sensor D",
      "channel_type": "2",
      "interface_type": "01",
      "channel_number": 3,
      "actions": 0,
      "measurement_range": "0b10100001",
      "adc_hardware_gain": 0.23761904761904762,
      "shunt_resistance": 0.249,
      "adc_offset": 0.0
    }

]



