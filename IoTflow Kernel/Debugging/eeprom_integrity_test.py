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
EEPROM Integrity Test Script
Tests byte write/read, page write/read, and cross-block boundary operations.

Author: Arshia Keshvari
Role: Independent Developer, Engineer, and Project Author
Last Updated: 2026-05-03
"""

from machine import I2C, Pin
from EEPROM_driver import EEPROM
import time

# ---- CONFIG ----
I2C_BUS  = 0
SCL_PIN  = 15
SDA_PIN  = 16
I2C_FREQ = 400000
EEPROM_ADDR = 0x57

def init():
    i2c = I2C(I2C_BUS, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
    devices = i2c.scan()
    print("I2C scan:", [hex(d) for d in devices])
    eeprom = EEPROM(i2c, EEPROM_ADDR)
    return eeprom

# ---- TESTS ----

def test_single_byte(eeprom):
    print("\n[TEST 1] Single byte write/read")
    passed = 0
    failed = 0
    addrs = [0x000, 0x0FF, 0x100, 0x1FF, 0x200, 0x2FF, 0x300, 0x3FF]
    for addr in addrs:
        val = addr & 0xFF
        eeprom.write_byte(addr, val)
        result = eeprom.read_byte(addr)
        status = "PASS" if result == val else "FAIL"
        if result == val:
            passed += 1
        else:
            failed += 1
        print(f"  addr={hex(addr)} wrote={hex(val)} read={hex(result)} [{status}]")
    print(f"  Result: {passed} passed, {failed} failed")
    return failed == 0


def test_block_boundary(eeprom):
    print("\n[TEST 2] Cross-block boundary write/read (key test)")
    # Write 300 bytes starting at 0x002
    # This forces crossing 0x100 (block 0 -> block 1) boundary
    test_data = bytes([i % 256 for i in range(300)])
    eeprom.write_bytes(0x002, test_data)
    result = eeprom.read_bytes(0x002, 300)

    if result == test_data:
        print("  PASS: 300 bytes match across 0x0FF->0x100 boundary")
        return True
    else:
        for i, (a, b) in enumerate(zip(test_data, result)):
            if a != b:
                print(f"  FAIL at byte index {i} (addr {hex(0x002 + i)}): wrote {hex(a)}, got {hex(b)}")
                break
        return False


def test_full_memory(eeprom):
    print("\n[TEST 3] Full memory write/read (1024 bytes)")
    test_data = bytes([i % 256 for i in range(1024)])
    eeprom.write_bytes(0x000, test_data)
    result = eeprom.read_bytes(0x000, 1024)

    if result == test_data:
        print("  PASS: All 1024 bytes match")
        return True
    else:
        mismatches = 0
        for i, (a, b) in enumerate(zip(test_data, result)):
            if a != b:
                if mismatches < 5:  # Only print first 5
                    print(f"  FAIL at addr {hex(i)}: wrote {hex(a)}, got {hex(b)}")
                mismatches += 1
        print(f"  Total mismatches: {mismatches}")
        return False


def test_page_boundary(eeprom):
    print("\n[TEST 4] Page boundary write/read")
    # Write 32 bytes starting at 0x00E to cross first page boundary (0x00F -> 0x010)
    test_data = bytes([i % 256 for i in range(32)])
    eeprom.write_bytes(0x00E, test_data)
    result = eeprom.read_bytes(0x00E, 32)

    if result == test_data:
        print("  PASS: 32 bytes match across page boundary")
        return True
    else:
        for i, (a, b) in enumerate(zip(test_data, result)):
            if a != b:
                print(f"  FAIL at byte index {i} (addr {hex(0x00E + i)}): wrote {hex(a)}, got {hex(b)}")
                break
        return False


def test_config_roundtrip(eeprom):
    print("\n[TEST 5] Config pack/unpack roundtrip")
    from config_serializer import pack_config, unpack_config
    import ujson

    cfg = {
        "module_type": "IoTsmart ESP32-S3",
        "mezzanine_type": "IoTextra Analog V3",
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
            },
            {
                "name": "Sensor E",
                "channel_type": "2",
                "interface_type": "01",
                "channel_number": 2,
                "actions": 0,
                "measurement_range": "0b10000011",
                "adc_hardware_gain": 0.23761904761904762,
                "shunt_resistance": 0.249,
                "adc_offset": 0.0
            }
        ],
        "network": {
            "wifi_ssid": "your_wifi_ssid",
            "wifi_password": "your_wifi_password"
        },
        "mqtt": {
            "broker": "Your_mqtt_broker.local",
            "port": 1883,
            "client_id": "pico-iotextra-controller-1",
            "base_topic": "iotextra/device_1"
        },
        "hardware": {
            "mode": "i2c",
            "i2c_bus_id": 0,
            "i2c_sda_pin": 16,
            "i2c_scl_pin": 15,
            "i2c_device_addr": "0x27",
            "eeprom_i2c_addr": "0x57",
            "eeprom_size": 1024,
            "num_of_adcs": 1,
            "adc_sampling_rate": 128,
            "gpio_host_pins": {"1": 10, "2": 11, "3": 12, "4": 13, "5": 14, "6": 15, "7": 18, "8": 19},
            "adc_i2c_addrs": ["0x49", "0x4B"]
        },
        "pin_config": "0b00001111",
        "status_update_interval_s": 30
    }

    packed = pack_config(cfg)
    print(f"  Packed size: {len(packed)} bytes")
    print(f"  Data spans: {hex(0x002)} to {hex(0x002 + len(packed))}")


    # Write length header at 0x000, data at 0x002
    import struct
    
    header = struct.pack(">H", len(packed))

    time.sleep_ms(20)  # ensure previous test's last write is fully settled

    eeprom.write_bytes(0x000, header + packed)

    time.sleep_ms(20)  # ensure this write is fully settled before reading

    # Read from 0x000, not 0x002
    full = eeprom.read_bytes(0x000, 10)
    print(f"  0x000 onwards: {[hex(b) for b in full]}")
    
    # Read back
    raw = eeprom.read_bytes(0x002, len(packed))
    print(f"  First 8 bytes written: {[hex(b) for b in packed[:8]]}")
    print(f"  First 8 bytes read:    {[hex(b) for b in raw[:8]]}")
    print(f"  Bytes around 0x100 written: {[hex(b) for b in packed[0xFE:0x102]]}")
    print(f"  Bytes around 0x100 read:    {[hex(b) for b in raw[0xFE:0x102]]}")
    restored = unpack_config(raw)

    if restored["module_type"] == cfg["module_type"] and \
       restored["network"]["wifi_ssid"] == cfg["network"]["wifi_ssid"] and \
       restored["mqtt"]["broker"] == cfg["mqtt"]["broker"]:
        print("  PASS: Config restored correctly")
        return True
    else:
        print("  FAIL: Config mismatch")
        print("  Expected:", ujson.dumps(cfg))
        print("  Got:     ", ujson.dumps(restored))
        return False


def test_timing(eeprom):
    print("\n[TEST 6] Write/read timing")
    test_data = bytes([0xAB] * 256)

    t0 = time.ticks_ms()
    eeprom.write_bytes(0x000, test_data)
    t1 = time.ticks_ms()
    eeprom.read_bytes(0x000, 256)
    t2 = time.ticks_ms()

    print(f"  Write 256 bytes: {time.ticks_diff(t1, t0)} ms")
    print(f"  Read  256 bytes: {time.ticks_diff(t2, t1)} ms")
    return True


# ---- MAIN ----
print("=" * 40)
print("M24C08-R EEPROM Test Suite")
print("=" * 40)

eeprom = init()

results = {
    "Single byte":      test_single_byte(eeprom),
    "Block boundary":   test_block_boundary(eeprom),
    "Full memory":      test_full_memory(eeprom),
    "Page boundary":    test_page_boundary(eeprom),
    "Config roundtrip": test_config_roundtrip(eeprom),
    "Timing":           test_timing(eeprom),
}

print("\n" + "=" * 40)
print("SUMMARY")
print("=" * 40)
for name, passed in results.items():
    print(f"  {name:<20} {'PASS' if passed else 'FAIL'}")