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
Title: EEPROM Basic Test Script
Description: Basic EEPROM testing for packing, writing, reading, and
erasing configuration data over I2C.

Author: Arshia Keshvari
Role: Independent Developer, Engineer, and Project Author
Last Updated: 2025-11-23
"""

from EEPROM_driver import EEPROM
from machine import UART, I2C, Pin
import ujson
import struct
from config_serializer import pack_config, unpack_config
import time

cfg = {
    "module_type": "IoTbase PICO",
    "mezzanine_type": "IoTextra Combo",
    "channels": [
        {
            "name": "w",
            "channel_type": "1",
            "interface_type": "11",
            "channel_number": 0,
            "actions": 1
        },
        {
            "name": "e",
            "channel_type": "2",
            "interface_type": "21",
            "channel_number": 1,
            "actions": 0,
            "measurement_range": "0b10000011",
            "adc_hardware_gain": 0.237619,
            "shunt_resistance": 0.249,
            "adc_offset": 0.0
        },
        {
            "name": "r",
            "channel_type": "1",
            "interface_type": "11",
            "channel_number": 2,
            "actions": 1
        },
        {
            "name": "t",
            "channel_type": "2",
            "interface_type": "21",
            "channel_number": 3,
            "actions": 0,
            "measurement_range": "0b01000010",
            "adc_hardware_gain": 0.5,
            "shunt_resistance": 0.1,
            "adc_offset": 0.0
        },
        {
            "name": "y",
            "channel_type": "1",
            "interface_type": "11",
            "channel_number": 4,
            "actions": 1
        },
        {
            "name": "u",
            "channel_type": "2",
            "interface_type": "21",
            "channel_number": 5,
            "actions": 0,
            "measurement_range": "0b11000011",
            "adc_hardware_gain": 0.25,
            "shunt_resistance": 0.2,
            "adc_offset": 0.0
        },
        {
            "name": "i",
            "channel_type": "1",
            "interface_type": "11",
            "channel_number": 6,
            "actions": 1
        },
        {
            "name": "o",
            "channel_type": "2",
            "interface_type": "21",
            "channel_number": 7,
            "actions": 0,
            "measurement_range": "0b00111100",
            "adc_hardware_gain": 0.75,
            "shunt_resistance": 0.15,
            "adc_offset": 0.01
        }
    ],
    "network": {
        "wifi_ssid": "example_ssid",
        "wifi_password": "example_password"
    },
    "mqtt": {
        "broker": "mqtt.example",
        "port": 1883,
        "client_id": "pico-iotextra-controller-1",
        "base_topic": "iotextra/device_1"
    },
    "hardware": {
        "mode": "i2c",
        "i2c_bus_id": 0,
        "i2c_sda_pin": 20,
        "i2c_scl_pin": 21,
        "i2c_device_addr": "0x3f",
        "eeprom_i2c_addr": "0x57",
        "eeprom_size": 1024,
        "num_of_adcs": 2,
        "adc_sampling_rate": 128,
        "gpio_host_pins": {
            "1": 10,
            "2": 11,
            "3": 12,
            "4": 13,
            "5": 14,
            "6": 15,
            "7": 18,
            "8": 19
        },
        "adc_i2c_addrs": [
            "0x48",
            "0x49"
        ]
    },
    "pin_config": "0b11110000",
    "status_update_interval_s": 30
}

cfg = {
  "module_type": "IoTbase PICO",
  "mezzanine_type": "IoTextra Analog V2",
  "channels": [
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
  ],
  "network": {
    "wifi_ssid": "vodafone0D3826",
    "wifi_password": "hRZPPZZmygccaP76"
  },
  "mqtt": {
    "broker": "Schrodinger.local",
    "port": 1883,
    "client_id": "pico-iotextra-controller-1",
    "base_topic": "iotextra/device_1"
  },
  "hardware": {
    "mode": "i2c",
    "i2c_bus_id": 0,
    "i2c_sda_pin": 20,
    "i2c_scl_pin": 21,
    "i2c_device_addr": "0x3f",
    "eeprom_i2c_addr": "0x57",
    "eeprom_size": 1024,
    "num_of_adcs": 2,
    "adc_sampling_rate": 128,
    "gpio_host_pins": {
      "1": 10,
      "2": 11,
      "3": 12,
      "4": 13,
      "5": 14,
      "6": 15,
      "7": 18,
      "8": 19
    },
    "adc_i2c_addrs": [
      "0x49",
      "0x4B"
    ]
  },
  "pin_config": "0b00001111",
  "status_update_interval_s": 30
}

# assume cfg is your big JSON dict
# Pack config
packed = pack_config(cfg)
print("Packed size:", len(packed), "bytes")

# Setup I2C and EEPROM
i2c = I2C(0, scl=12, sda=11, freq=400000)
eeprom = EEPROM(i2c, 0x57)

    
# # Write packed config
# eeprom.write_bytes(0x002, packed)
# 
# # Read it back
# raw = eeprom.read_bytes(0x002, len(packed))
# 
# length_bytes = struct.pack(">H", len(packed))   # 2 bytes, big-endian length
# 
# eeprom.write_bytes(0x000, length_bytes)   # <-- writes to address 0x000
# 
# 
# data = eeprom.read_bytes(0, 2)
# print([hex(b) for b in data])
# 
# restored = unpack_config(raw)
# 
# print("Restored config:")
# print(ujson.dumps(restored))

# ERASE FIRST
print("Erasing EEPROM...")
eeprom.erase_all()
