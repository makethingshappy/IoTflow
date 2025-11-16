"""
==============================================================
 Configuration Serializer & Deserializer
--------------------------------------------------------------
 This module provides efficient binary serialization and
 deserialization for IoTextra firmware configuration data.
 The format is compact, deterministic, and EEPROM-safe.

 Author: Arshia Keshvari
 Role: Independent Developer, Engineer, and Project Author
 Last Updated: 2025-11-16
==============================================================
"""

import struct

# ----------------------------
# Helpers
# ----------------------------

def pack_string(s: str) -> bytes:
    b = s.encode("utf-8")
    if len(b) > 255:
        raise ValueError("String too long for 1-byte length prefix")
    return struct.pack("B", len(b)) + b


def unpack_string(buf: bytes, offset: int):
    length = buf[offset]
    s = buf[offset+1:offset+1+length].decode("utf-8")
    return s, offset+1+length

# ----------------------------
# Serializer (optimized)
# ----------------------------

def pack_config(cfg: dict) -> bytes:
    out = bytearray()

    # module & mezzanine
    out += pack_string(cfg["module_type"])
    out += pack_string(cfg["mezzanine_type"])

    # channels
    channels = cfg["channels"]
    out += struct.pack("B", len(channels))
    for ch in channels:
        out += pack_string(ch["name"])
        out += struct.pack(
            "BBBB",
            int(ch["channel_type"]),
            int(ch["interface_type"]),
            ch["channel_number"],
            ch["actions"]
        )
        
        # ADC fields presence flag
        adc_fields_present = 0
        if "measurement_range" in ch: adc_fields_present |= 0x01
        if "adc_hardware_gain" in ch: adc_fields_present |= 0x02
        if "shunt_resistance" in ch: adc_fields_present |= 0x04
        if "adc_offset" in ch: adc_fields_present |= 0x08
        out += struct.pack("B", adc_fields_present)

        # Pack ADC fields
        if adc_fields_present & 0x01:
            out += struct.pack("B", int(ch["measurement_range"], 2))
        if adc_fields_present & 0x02:
            # 4-byte float
            out += struct.pack(">f", float(ch["adc_hardware_gain"]))
        if adc_fields_present & 0x04:
            # 2-byte fixed point
            shunt = int(ch["shunt_resistance"] * 1000)
            out += struct.pack(">H", shunt)
        if adc_fields_present & 0x08:
            # 2-byte fixed point
            offset_val = int(ch["adc_offset"] * 1000)
            out += struct.pack(">H", offset_val)

    # network
    out += pack_string(cfg["network"]["wifi_ssid"])
    out += pack_string(cfg["network"]["wifi_password"])

    # mqtt
    mqtt = cfg["mqtt"]
    out += pack_string(mqtt["broker"])
    out += struct.pack(">H", mqtt["port"])
    out += pack_string(mqtt["client_id"])
    out += pack_string(mqtt["base_topic"])

    # hardware
    hw = cfg["hardware"]
    out += pack_string(hw["mode"])

    # Pack bus id, SDA/SCL, device addr and EEPROM addr
    out += struct.pack(
        "BBBBB",
        hw["i2c_bus_id"],
        hw["i2c_sda_pin"],
        hw["i2c_scl_pin"],
        int(hw["i2c_device_addr"], 16),
        int(hw["eeprom_i2c_addr"], 16)
    )
    # Pack eeprom_size as 2-byte unsigned (big-endian) to support sizes >255
    out += struct.pack(">H", int(hw.get("eeprom_size", 0)))

    # GPIO pins (pack 2 per byte, 4 bits each if pins <= 15)
    for i in range(0, 8, 2):
        packed = ((hw["gpio_host_pins"][str(i+1)] & 0x0F) << 4) | (hw["gpio_host_pins"][str(i+2)] & 0x0F)
        out += struct.pack("B", packed)

    # ADC addresses
    adc_addrs = hw.get("adc_i2c_addrs", [])
    out += struct.pack("B", len(adc_addrs))
    for addr in adc_addrs:
        out += struct.pack("B", int(addr, 16))

    # ADC sampling rate (Hz) as 2-byte unsigned (big-endian). Optional.
    out += struct.pack(">H", int(hw.get("adc_sampling_rate", 0)))

    # pin config + status interval (1 byte interval)
    out += struct.pack("BB", int(cfg["pin_config"], 2), min(cfg["status_update_interval_s"], 255))

    return bytes(out)

# ----------------------------
# Deserializer (optimized)
# ----------------------------

def unpack_config(buf: bytes) -> dict:
    offset = 0
    cfg = {}

    # module + mezzanine
    cfg["module_type"], offset = unpack_string(buf, offset)
    cfg["mezzanine_type"], offset = unpack_string(buf, offset)

    # channels
    num_channels = buf[offset]; offset += 1
    cfg["channels"] = []
    for _ in range(num_channels):
        name, offset = unpack_string(buf, offset)
        ch_type, if_type, ch_num, actions = struct.unpack_from("BBBB", buf, offset)
        offset += 4

        ch = {
            "name": name,
            "channel_type": str(ch_type),
            "interface_type": str(if_type),
            "channel_number": ch_num,
            "actions": actions
        }

        adc_fields_present = buf[offset]; offset += 1
        if adc_fields_present & 0x01:
            ch["measurement_range"] = "0b" + "{:08b}".format(buf[offset])
            offset += 1
        if adc_fields_present & 0x02:
            gain = struct.unpack_from(">f", buf, offset)[0]
            ch["adc_hardware_gain"] = gain
            offset += 4
        if adc_fields_present & 0x04:
            shunt = struct.unpack_from(">H", buf, offset)[0] / 1000.0
            ch["shunt_resistance"] = shunt
            offset += 2
        if adc_fields_present & 0x08:
            offset_val = struct.unpack_from(">H", buf, offset)[0] / 1000.0
            ch["adc_offset"] = offset_val
            offset += 2

        cfg["channels"].append(ch)

    # network
    ssid, offset = unpack_string(buf, offset)
    pwd, offset = unpack_string(buf, offset)
    cfg["network"] = {"wifi_ssid": ssid, "wifi_password": pwd}

    # mqtt
    broker, offset = unpack_string(buf, offset)
    port = struct.unpack_from(">H", buf, offset)[0]; offset += 2
    client_id, offset = unpack_string(buf, offset)
    base_topic, offset = unpack_string(buf, offset)
    cfg["mqtt"] = {
        "broker": broker,
        "port": port,
        "client_id": client_id,
        "base_topic": base_topic
    }

    # hardware
    mode, offset = unpack_string(buf, offset)
    bus_id, sda, scl, dev_addr, eeprom_addr = struct.unpack_from("BBBBB", buf, offset)
    offset += 5
    # eeprom_size stored as 2-byte unsigned big-endian
    eeprom_size = struct.unpack_from(">H", buf, offset)[0]; offset += 2

    # GPIO unpack (2 per byte)
    gpio = {}
    for i in range(0, 8, 2):
        packed = buf[offset]; offset += 1
        gpio[str(i+1)] = (packed >> 4) & 0x0F
        gpio[str(i+2)] = packed & 0x0F

    # ADC addresses
    num_adcs = buf[offset]; offset += 1
    adc_addrs = []
    for _ in range(num_adcs):
        addr = buf[offset]; offset += 1
        adc_addrs.append(hex(addr))
        
    # ADC sampling rate (2 bytes)
    adc_sampling_rate = struct.unpack_from(">H", buf, offset)[0]; offset += 2

    cfg["hardware"] = {
        "mode": mode,
        "i2c_bus_id": bus_id,
        "i2c_sda_pin": sda,
        "i2c_scl_pin": scl,
        "i2c_device_addr": hex(dev_addr),
        "eeprom_i2c_addr": hex(eeprom_addr),
        "eeprom_size": eeprom_size,
        "gpio_host_pins": gpio,
        "adc_i2c_addrs": adc_addrs,
        "num_of_adcs": num_adcs,
        "adc_sampling_rate": adc_sampling_rate
    }

    # pin config + status interval
    pin_cfg, status_int = struct.unpack_from("BB", buf, offset); offset += 2
    cfg["pin_config"] = "0b" + "{:08b}".format(pin_cfg)
    cfg["status_update_interval_s"] = status_int

    return cfg
