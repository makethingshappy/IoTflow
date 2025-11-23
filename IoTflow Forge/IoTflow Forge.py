"""
MIT License

Copyright (c) 2025 makethingshappy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

"""
IoTflow Forge — I/O Configuration Tool
---------------------------------------

A command-line utility for creating, editing, and managing analog and digital
I/O node configurations. Supports loading and saving configuration profiles
in JSON format for seamless integration with IoTflow systems.

Author: Arshia Keshvari
Role: Independent Developer, Engineer, and Project Author
Last Updated: 2025-11-16
"""

import json
import re
import sys
import serial
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

DIGITAL_INTERFACE_LABELS: Dict[str, str] = {
    "01": "GPIO",
    "11": "I2C via TCA9534",
    "12": "GPIO + I2C via TCA9534",
}

ANALOG_INTERFACE_LABELS: Dict[str, str] = {
    "01": "IoTextra Analog",
    "21": "IoTextra Combo",
    "02": "IoT Analog 2",
    "03": "IoT Analog 3",
}

# Map common mezzanine names to their typical ADC count (used for analog modules)
MEZZANINE_ADC_COUNT: Dict[str, int] = {
    "IoTextra Analog": 2,
    "IoTextra Combo": 1,
    "IoTextra Analog V2": 2,
    "IoTextra Analog V3": 2,
}

CHANNEL_TYPE_LABELS: Dict[str, str] = {
    "1": "Bool (Digital I/O)",
    "2": "Int (Analog Input)",
}

ANALOG_MEASUREMENT_RANGES = [
    ("0b00000001", "Voltage 0-0.5V"),
    ("0b00000010", "Voltage 0-5V"),
    ("0b00000011", "Voltage 0-10V"),
    ("0b10000001", "Voltage ±0.5V"),
    ("0b10000010", "Voltage ±5V"),
    ("0b10000011", "Voltage ±10V"),
    ("0b00100001", "Current 0-20mA"),
    ("0b10100001", "Current ±20mA"),
    ("0b00100010", "Current 4-20mA"),
    ("0b00100011", "Current 0-40mA"),
]

ANALOG_RANGE_LOOKUP: Dict[str, str] = {code: label for code, label in ANALOG_MEASUREMENT_RANGES}

DIGITAL_INTERFACE_CODES = set(DIGITAL_INTERFACE_LABELS.keys())
ANALOG_INTERFACE_CODES = set(ANALOG_INTERFACE_LABELS.keys())

# ADC sampling rate selection mapping (display value -> config code)
ADC_SAMPLING_RATES: Dict[int, int] = {
    8: 0,    # 128/8 SPS for ADS1115/ADS1015
    16: 1,   # 250/16 SPS
    32: 2,   # 490/32 SPS
    64: 3,   # 920/64 SPS
    128: 4,  # 1600/128 SPS (default)
    250: 5,  # 2400/250 SPS
    475: 6,  # 3300/475 SPS
    860: 7   # -/860 SPS
}

# Default per-channel calibration values (used when hardware-level values are not present)
DEFAULT_ADC_HARDWARE_GAIN: float = 0.23761904761904762
DEFAULT_SHUNT_RESISTANCE: float = 0.249
DEFAULT_ADC_OFFSET: float = 0.0


class ModuleType(Enum):
    """Supported module types"""
    IOTBASE_PICO = "IoTbase PICO"
    IOTBASE_NANO = "IoTbase Nano"
    IOTSMART_ESP32S3 = "IoTsmart ESP32-S3"


class InterfaceType(Enum):
    """Supported interface types"""
    GPIO = "01"
    I2C_TCA9534 = "11"
    GPIO_AND_I2C = "12"  # Future expansion


class ChannelType(Enum):
    """Channel types"""
    BIT = "1"  # Digital bit type
    ANALOG_INT = "2"  # Analog input (integer scaled)

class HardwareMode(Enum):
    """Hardware modes"""
    GPIO = "gpio"
    I2C = "i2c"

@dataclass
class Channel:
    """Channel configuration"""
    name: str
    channel_type: str
    interface_type: str
    channel_number: int
    actions: int  # Bit field for possible actions
    measurement_range: Optional[str] = None
    # Per-channel ADC hardware/calibration (only for analog channels)
    adc_hardware_gain: Optional[float] = None
    shunt_resistance: Optional[float] = None
    adc_offset: Optional[float] = None
    
    def __post_init__(self):
        # Validate channel name length
        if len(self.name) > 8:
            raise ValueError("Channel name must be 8 characters or less")
        
        if self.channel_type not in CHANNEL_TYPE_LABELS:
            raise ValueError(f"Unsupported channel type: {self.channel_type}")

        if self.channel_type == ChannelType.BIT.value:
            # Validate interface mapping
            if self.interface_type not in DIGITAL_INTERFACE_CODES:
                raise ValueError(f"Invalid digital interface type: {self.interface_type}")

            # Validate channel number
            if not 0 <= self.channel_number <= 7:
                raise ValueError("Digital channel number must be between 0 and 7")

            # Validate actions (only bit 0 is used for write in current version)
            if self.actions not in (0, 1):
                raise ValueError("Digital channel actions must be 0 or 1 (0=read only, 1=read+write)")

            # Digital channels must not specify measurement ranges
            self.measurement_range = None

        elif self.channel_type == ChannelType.ANALOG_INT.value:
            # Validate interface mapping for analog
            if self.interface_type not in ANALOG_INTERFACE_CODES:
                raise ValueError(f"Invalid analog interface type: {self.interface_type}")

            # Analog mezzanines may expose up to 8 channels (0-7)
            if not 0 <= self.channel_number <= 7:
                raise ValueError("Analog channel number must be between 0 and 7")

            if self.actions != 0:
                raise ValueError("Analog input channels are read-only; actions must be 0")

            if self.measurement_range not in ANALOG_RANGE_LOOKUP:
                raise ValueError("Analog channels require a valid measurement range code")

            # Validate optional per-channel ADC calibration values
            if self.adc_hardware_gain is not None:
                try:
                    g = float(self.adc_hardware_gain)
                    if g <= 0:
                        raise ValueError("adc_hardware_gain must be positive")
                except (TypeError, ValueError):
                    raise ValueError("adc_hardware_gain must be a positive float")

            if self.shunt_resistance is not None:
                try:
                    r = float(self.shunt_resistance)
                    if r <= 0:
                        raise ValueError("shunt_resistance must be positive")
                except (TypeError, ValueError):
                    raise ValueError("shunt_resistance must be a positive float")

            if self.adc_offset is not None:
                try:
                    float(self.adc_offset)
                except (TypeError, ValueError):
                    raise ValueError("adc_offset must be a numeric value")

        else:
            raise ValueError(f"Unknown channel type: {self.channel_type}")

@dataclass
class NetworkConfig:
    """Network configuration"""
    wifi_ssid: str = ""
    wifi_password: str = ""

@dataclass
class MQTTConfig:
    """MQTT configuration"""
    broker: str = ""
    port: int = 1883
    client_id: str = "pico-iotextra-controller-1"
    base_topic: str = "iotextra/device_1"

@dataclass
class HardwareConfig:
    """Hardware configuration"""
    mode: str = "i2c"  # "i2c" or "gpio"
    
    # I2C configuration
    i2c_bus_id: int = 0
    i2c_sda_pin: int = 20
    i2c_scl_pin: int = 21
    i2c_device_addr: str = "0x3f"
    
    # EEPROM configuration
    eeprom_i2c_addr: str = "0x57"
    eeprom_size: int = 1024
    
    # ADC Configuration (for analog modules)
    num_of_adcs: int = 0
    adc_i2c_addresses: Dict[int, str] = None  # Maps ADC number (1, 2, 3, 4) to I2C address
    # ADC runtime options
    adc_sampling_rate: int = 128  # In SPS (one of keys from ADC_SAMPLING_RATES)
    # GPIO configuration
    gpio_host_pins: Dict[int, int] = None
    
    def __post_init__(self):
        if self.adc_i2c_addresses is None:
            self.adc_i2c_addresses = {}
        if self.gpio_host_pins is None:
            # Default GPIO pin mapping for HOST connector
            self.gpio_host_pins = {
                1: 10,  # AP0
                2: 11,  # AP1
                3: 12,  # AP2
                4: 13,  # AP3
                5: 14,  # AP4
                6: 15,  # AP5
                7: 18,  # AP6
                8: 19,  # AP7
            }

@dataclass
class Configuration:
    """Complete configuration for a digital I/O node"""
    module_type: str
    mezzanine_type: str
    channels: List[Channel] = None
    
    # Network and communication settings
    network: NetworkConfig = None
    mqtt: MQTTConfig = None
    hardware: HardwareConfig = None
    
    # Pin configuration (input/output channels)
    pin_config: str = "0b00001111"  # Default: channels 0-3 are outputs, 4-7 are inputs
    status_update_interval_s: int = 30
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = []
        
        if self.network is None:
            self.network = NetworkConfig()
        
        if self.mqtt is None:
            self.mqtt = MQTTConfig()
        
        if self.hardware is None:
            self.hardware = HardwareConfig()
        
        # Validate number of channels
        if len(self.channels) > 8:
            raise ValueError("Maximum 8 channels allowed")
        
        # Note: interface codes are specified per-channel. Top-level interface
        # is not stored. Validate I2C device address if any channel uses I2C.
        uses_i2c = any(ch.interface_type in {InterfaceType.I2C_TCA9534.value, InterfaceType.GPIO_AND_I2C.value} for ch in self.channels)
        if uses_i2c and not self.hardware.i2c_device_addr:
            raise ValueError("I2C address must be specified when channels use I2C interfaces")
        
        # Validate pin configuration
        try:
            pin_config_int = int(self.pin_config, 2) if self.pin_config.startswith('0b') else int(self.pin_config, 16) if self.pin_config.startswith('0x') else int(self.pin_config)
            if not 0 <= pin_config_int <= 0xFF:
                raise ValueError("Pin configuration must be between 0 and 255")
        except ValueError:
            raise ValueError("Invalid pin configuration format")

class Configurator:
    """Main configuration tool"""
    
    def __init__(self):
        self.config = None
        self.config_file = None
        self.is_analog_module = False
    
    def create_new_config(self):
        """Create a new configuration interactively"""
        print("\n=== Creating New Configuration ===\n")
        
        # Module type selection
        print("Available module types:")
        for i, module_type in enumerate(ModuleType, 1):
            print(f"  {i}. {module_type.value}")
        
        while True:
            try:
                choice = int(input("\nSelect module type (1-3): ")) - 1
                if 0 <= choice < len(ModuleType):
                    module_type = list(ModuleType)[choice].value
                    break
                else:
                    print("Invalid choice. Please select 1-3.")
            except ValueError:
                print("Please enter a valid number.")

        # Interface category selection
        print("\nSelect mezzanine category:")
        print("  1. Digital I/O mezzanines")
        print("  2. Analog input mezzanines")

        while True:
            category_choice = input("\nSelect category (1-2): ").strip()
            if category_choice in {"1", "2"}:
                break
            print("Please select 1 or 2.")

        self.is_analog_module = category_choice == "2"

        # Present mezzanine types (user selects the board type rather than a raw interface code)
        if self.is_analog_module:
            mezzanine_menu = [
                "IoTextra Analog",
                "IoTextra Combo",
                "IoTextra Analog V2",
                "IoTextra Analog V3",
            ]
        else:
            mezzanine_menu = [
                "IoTextra Input",
                "IoTextra Octal",
                "IoTextra Relay",
                "IoTextra SSR Small",
            ]

        print("\nAvailable mezzanine types:")
        for idx, name in enumerate(mezzanine_menu, 1):
            print(f"  {idx}. {name}")
        print(f"  {len(mezzanine_menu)+1}. Custom mezzanine (enter name)")

        while True:
            try:
                choice = int(input("\nSelect mezzanine type: ")) - 1
                if 0 <= choice < len(mezzanine_menu):
                    mezzanine_type = mezzanine_menu[choice]
                    break
                elif choice == len(mezzanine_menu):
                    mezzanine_type = input("Enter custom mezzanine type name: ").strip()
                    break
                else:
                    print(f"Invalid choice. Please select 1-{len(mezzanine_menu)+1}.")
            except ValueError:
                print("Please enter a valid number.")

        # Create configuration (interface is specified per-channel)
        self.config = Configuration(
            module_type=module_type,
            mezzanine_type=mezzanine_type,
        )
        
        # Configure network settings
        self.configure_network()
        
        # Configure MQTT settings
        self.configure_mqtt()
        
        # Configure hardware settings
        self.configure_hardware()
        
        # Configure pin configuration
        self.configure_pin_config()
        
        # Configure channels
        self.configure_channels()
        
        print("\n=== Configuration Created Successfully ===")
        return self.config
    
    def configure_network(self):
        """Configure network settings"""
        print(f"\n=== Network Configuration ===")
        
        # Wi-Fi SSID
        wifi_ssid = input("Wi-Fi SSID: ").strip()
        if wifi_ssid:
            self.config.network.wifi_ssid = wifi_ssid
        
        # Wi-Fi Password
        wifi_password = input("Wi-Fi Password: ").strip()
        if wifi_password:
            self.config.network.wifi_password = wifi_password
    
    def configure_mqtt(self):
        """Configure MQTT settings"""
        print(f"\n=== MQTT Configuration ===")
        
        # MQTT Broker
        broker = input("MQTT Broker address (default: empty): ").strip()
        if broker:
            self.config.mqtt.broker = broker
        
        # MQTT Port
        while True:
            port_input = input("MQTT Port (default: 1883): ").strip()
            if not port_input:
                break
            try:
                port = int(port_input)
                if 1 <= port <= 65535:
                    self.config.mqtt.port = port
                    break
                else:
                    print("Port must be between 1 and 65535")
            except ValueError:
                print("Please enter a valid port number")
        
        # MQTT Client ID
        client_id = input("MQTT Client ID (default: pico-iotextra-controller-1): ").strip()
        if client_id:
            self.config.mqtt.client_id = client_id
        
        # MQTT Base Topic
        base_topic = input("MQTT Base Topic (default: iotextra/device_1): ").strip()
        if base_topic:
            self.config.mqtt.base_topic = base_topic
    
    def configure_hardware(self):
        """Configure hardware settings"""
        print(f"\n=== Hardware Configuration ===")
        
        # Hardware Mode
        if self.is_analog_module:
            print("Analog input mezzanines require I2C mode. Setting hardware mode to I2C.")
            self.config.hardware.mode = HardwareMode.I2C.value
        else:
            print("Hardware Mode:")
            print("1. GPIO")
            print("2. I2C")
            
            while True:
                choice = input("Select mode (1-2, default: 2): ").strip()
                if not choice:
                    self.config.hardware.mode = "i2c"
                    break
                if choice == "1":
                    self.config.hardware.mode = "gpio"
                    break
                elif choice == "2":
                    self.config.hardware.mode = "i2c"
                    break
                else:
                    print("Please select 1 or 2")
        
        if self.config.hardware.mode == "i2c":
            # I2C Configuration
            print("\nI2C Configuration:")
            
            # I2C Bus ID
            bus_id_input = input("I2C Bus ID (default: 0): ").strip()
            if bus_id_input:
                try:
                    self.config.hardware.i2c_bus_id = int(bus_id_input)
                except ValueError:
                    print("Invalid bus ID, using default: 0")
            
            # I2C SDA Pin
            sda_input = input("I2C SDA Pin (default: 20): ").strip()
            if sda_input:
                try:
                    self.config.hardware.i2c_sda_pin = int(sda_input)
                except ValueError:
                    print("Invalid SDA pin, using default: 20")
            
            # I2C SCL Pin
            scl_input = input("I2C SCL Pin (default: 21): ").strip()
            if scl_input:
                try:
                    self.config.hardware.i2c_scl_pin = int(scl_input)
                except ValueError:
                    print("Invalid SCL pin, using default: 21")
            
            # I2C Device Address
            while True:
                device_addr = input("I2C I/O Expander Device Address (hex, default: 0x3f or 0x27): ").strip()
                if not device_addr:
                    device_addr = "0x3f"
                try:
                    int(device_addr, 16)
                    self.config.hardware.i2c_device_addr = device_addr
                    break
                except ValueError:
                    print("Please enter a valid hexadecimal address (e.g., 0x3f)")

            # EEPROM Configuration
            print("\nEEPROM Configuration:")
            
            eeprom_addr = input("EEPROM I2C Address (hex, default: 0x57): ").strip()
            if eeprom_addr:
                try:
                    int(eeprom_addr, 16)
                    self.config.hardware.eeprom_i2c_addr = eeprom_addr
                except ValueError:
                    print("Invalid hex address, using default: 0x57")

            eeprom_size_input = input("EEPROM Size in bytes (default: 1024): ").strip()
            if eeprom_size_input:
                try:
                    self.config.hardware.eeprom_size = int(eeprom_size_input)
                except ValueError:
                    print("Invalid size, using default: 1024")
        
        # ADC Configuration (for analog modules)
        if self.is_analog_module:
            # Determine ADC count based on mezzanine type if known, otherwise ask user
            num_adcs = MEZZANINE_ADC_COUNT.get(self.config.mezzanine_type, 0)
            if num_adcs == 0:
                try:
                    num_adcs = int(input("Enter number of ADCs on this mezzanine (default 2): ").strip() or "2")
                except ValueError:
                    num_adcs = 2

            if num_adcs > 0:
                self.config.hardware.num_of_adcs = num_adcs
                interface_name = self.config.mezzanine_type
                print(f"\nADC Configuration for {interface_name}:")
                print(f"This mezzanine requires {num_adcs} ADC(s).")
                
                used_addresses = set()
                for adc_num in range(1, num_adcs + 1):
                    while True:
                        default_addr = "0x49" if adc_num == 1 else "0x48"
                        addr_input = input(f"Enter I2C address for ADC {adc_num} (hex, default: {default_addr}): ").strip()
                        if not addr_input:
                            addr_input = default_addr
                        
                        try:
                            # Validate hex format
                            addr_int = int(addr_input, 16)
                            if not (0x03 <= addr_int <= 0x77):
                                print("I2C address must be in range 0x03-0x77 (7-bit address)")
                                continue
                            
                            # Check for duplicates
                            if addr_input in used_addresses:
                                print(f"Address {addr_input} already used. Please choose a different address.")
                                continue
                            
                            used_addresses.add(addr_input)
                            self.config.hardware.adc_i2c_addresses[adc_num] = addr_input
                            print(f"ADC {adc_num} I2C address set to: {addr_input}")
                            break
                        except ValueError:
                            print("Please enter a valid hexadecimal address (e.g., 0x49)")
                
                # --- ADC runtime options: sampling rate, hardware gain, shunt, offset ---
                try:
                    rates = sorted(ADC_SAMPLING_RATES.keys())
                except NameError:
                    rates = [8, 16, 32, 64, 128, 250, 475, 860]

                print("\nADC Sampling Rate options:")
                for idx, r in enumerate(rates, 1):
                    marker = " (current)" if r == self.config.hardware.adc_sampling_rate else ""
                    print(f"  {idx}. {r} SPS{marker}")

                sr_choice = input(f"Select ADC sampling rate (1-{len(rates)}) or enter value in SPS (default: {self.config.hardware.adc_sampling_rate}): ").strip()
                if sr_choice:
                    try:
                        idx = int(sr_choice) - 1
                        if 0 <= idx < len(rates):
                            self.config.hardware.adc_sampling_rate = rates[idx]
                        else:
                            val = int(sr_choice)
                            if val in rates:
                                self.config.hardware.adc_sampling_rate = val
                    except ValueError:
                        try:
                            val = int(sr_choice)
                            if val in rates:
                                self.config.hardware.adc_sampling_rate = val
                        except ValueError:
                            print("Invalid sampling rate selection, keeping default.")
                # (hardware-level gain/shunt/offset were removed; per-channel calibration is used)
        
        # GPIO Host Pins (always configurable)
        print("\nGPIO Host Pin Configuration:")
        print("Current mapping:")
        for channel, pin in self.config.hardware.gpio_host_pins.items():
            print(f"  Channel {channel}: GPIO {pin}")
        
        change_pins = input("Change GPIO pin mapping? (y/n, default: n): ").strip().lower()
        if change_pins in ['y', 'yes']:
            for channel in range(1, 9):
                pin_input = input(f"GPIO pin for Channel {channel} (current: {self.config.hardware.gpio_host_pins[channel]}): ").strip()
                if pin_input:
                    try:
                        pin = int(pin_input)
                        self.config.hardware.gpio_host_pins[channel] = pin
                    except ValueError:
                        print(f"Invalid pin number, keeping current: {self.config.hardware.gpio_host_pins[channel]}")
    
    def configure_pin_config(self):
        """Configure pin configuration (input/output)"""
        if self.is_analog_module:
            print(f"\n=== Pin Configuration ===")
            print("Analog input mezzanines don't use digital pin configuration.")
            print("Measurement ranges are defined per analog channel instead.")
            return

        print(f"\n=== Pin Configuration ===")
        print("Pin Configuration determines which channels are inputs vs outputs")
        print("Format: 0b[P7][P6][P5][P4][P3][P2][P1][P0]")
        print("1 = Input channel, 0 = Output channel")
        
        # Display current configuration
        current_int = int(self.config.pin_config, 2) if self.config.pin_config.startswith('0b') else int(self.config.pin_config, 16) if self.config.pin_config.startswith('0x') else int(self.config.pin_config)
        print(f"Current: {self.config.pin_config} (0b{current_int:08b})")
        
        # Show examples
        print("\nExamples:")
        print("IoTExtra Relay2: 0b11110000 (P4-P7 i.e. channels 5-8 are unused, 1-4 are outputs)")
        print("IoTExtra Input:  0b11111111 (all channels are inputs)")
        print("IoTExtra Octal:  0b00001111 (channels 0-3 outputs, 4-7 inputs)")
        
        # Get new configuration
        while True:
            config_input = input("\nEnter pin configuration (binary format preferred, e.g., 0b00001111, default: current): ").strip()
            if not config_input:
                break
            
            try:
                if config_input.startswith('0b'):
                    # Binary format (preferred)
                    pin_config_int = int(config_input, 2)
                    pin_config_str = config_input
                elif config_input.startswith('0x'):
                    # Hex format
                    pin_config_int = int(config_input, 16)
                    pin_config_str = f"0b{pin_config_int:08b}"
                else:
                    # Decimal format
                    pin_config_int = int(config_input)
                    pin_config_str = f"0b{pin_config_int:08b}"
                
                if 0 <= pin_config_int <= 0xFF:
                    self.config.pin_config = pin_config_str
                    print(f"Pin configuration updated to: {pin_config_str}")
                    break
                else:
                    print("Pin configuration must be between 0 and 255")
            except ValueError:
                print("Invalid format. Use binary (0b...), hex (0x...), or decimal")
        
        # Status update interval
        interval_input = input("Status update interval in seconds (default: 30): ").strip()
        if interval_input:
            try:
                interval = int(interval_input)
                if interval > 0:
                    self.config.status_update_interval_s = interval
                else:
                    print("Interval must be positive, using default: 30")
            except ValueError:
                print("Invalid interval, using default: 30")
    
    def configure_channels(self):
        """Configure channels for the node"""
        print(f"\n=== Configuring Channels ===")
        print(f"Maximum 8 channels allowed. Current: {len(self.config.channels)}")
        
        while True:
            action = input("\nChannel actions:\n1. Add channel\n2. Edit channel\n3. Remove channel\n4. View channels\n5. Done\nSelect (1-5): ").strip()
            
            if action == "1":
                self.add_channel()
            elif action == "2":
                self.edit_channel()
            elif action == "3":
                self.remove_channel()
            elif action == "4":
                self.view_channels()
            elif action == "5":
                if len(self.config.channels) == 0:
                    print("Warning: No channels configured. Please add at least one channel.")
                    continue
                break
            else:
                print("Invalid choice. Please select 1-5.")
    
    def prompt_measurement_range(self, current: Optional[str] = None) -> str:
        """Prompt the user to select an analog measurement range."""
        print("\nSelect measurement range for this analog channel:")
        for idx, (code, label) in enumerate(ANALOG_MEASUREMENT_RANGES, 1):
            marker = " (current)" if code == current else ""
            print(f"{idx}. {label} [{code}]{marker}")

        while True:
            choice = input("Select range (1-{}): ".format(len(ANALOG_MEASUREMENT_RANGES))).strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(ANALOG_MEASUREMENT_RANGES):
                    selected = ANALOG_MEASUREMENT_RANGES[idx][0]
                    print(f"Measurement range set to {ANALOG_RANGE_LOOKUP[selected]} ({selected})")
                    return selected
            except ValueError:
                pass
            print(f"Please select a value between 1 and {len(ANALOG_MEASUREMENT_RANGES)}.")

    def add_channel(self):
        """Add a new channel"""
        if len(self.config.channels) >= 8:
            print("Maximum 8 channels reached. Cannot add more.")
            return
        
        print(f"\n--- Adding Channel {len(self.config.channels) + 1} ---")
        
        # Channel name
        while True:
            name = input("Channel name (max 8 chars): ").strip()
            if len(name) <= 8 and name:
                # Check for duplicate names
                if any(ch.name == name for ch in self.config.channels):
                    print("Channel name already exists. Please choose a different name.")
                    continue
                break
            else:
                print("Channel name must be 1-8 characters long.")

        # Determine available channel types
        # IoTextra Combo mezzanine supports both digital and analog channels
        if self.config.mezzanine_type == "IoTextra Combo":
            channel_type_options = [
                (ChannelType.BIT.value, CHANNEL_TYPE_LABELS[ChannelType.BIT.value]),
                (ChannelType.ANALOG_INT.value, CHANNEL_TYPE_LABELS[ChannelType.ANALOG_INT.value])
            ]
        elif self.is_analog_module:
            channel_type_options = [(ChannelType.ANALOG_INT.value, CHANNEL_TYPE_LABELS[ChannelType.ANALOG_INT.value])]
        else:
            channel_type_options = [(ChannelType.BIT.value, CHANNEL_TYPE_LABELS[ChannelType.BIT.value])]

        if len(channel_type_options) == 1:
            channel_type = channel_type_options[0][0]
            print(f"Channel type: {channel_type} ({channel_type_options[0][1]})")
        else:
            print("Available channel types:")
            for idx, (_, label) in enumerate(channel_type_options, 1):
                print(f"{idx}. {label}")
            while True:
                choice = input("Select channel type: ").strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(channel_type_options):
                        channel_type = channel_type_options[idx][0]
                        break
                except ValueError:
                    pass
                print(f"Please select 1-{len(channel_type_options)}.")

        # Interface type for this channel
        if channel_type == ChannelType.BIT.value:
            # Digital channels on combo mezzanines need to choose GPIO or I2C
            if self.config.mezzanine_type == "IoTextra Combo":
                print("Digital channels on IoTextra Combo require a digital interface:")
                print(f"1. {DIGITAL_INTERFACE_LABELS[InterfaceType.GPIO.value]} ({InterfaceType.GPIO.value})")
                print(f"2. {DIGITAL_INTERFACE_LABELS[InterfaceType.I2C_TCA9534.value]} ({InterfaceType.I2C_TCA9534.value})")
                while True:
                    choice = input("Select interface type for this digital channel (1-2): ").strip()
                    if choice == "1":
                        interface_type = InterfaceType.GPIO.value
                        break
                    elif choice == "2":
                        interface_type = InterfaceType.I2C_TCA9534.value
                        break
                    else:
                        print("Please select 1 or 2.")
            else:
                # For non-combo (pure digital) mezzanines default to GPIO
                interface_type = InterfaceType.GPIO.value
        else:
            # For analog channels prefer per-mezzanine defaults. If this is an
            # analog mezzanine and known to be the IoTextra Combo use that code,
            # otherwise default to the common analog interface '01'.
            if self.is_analog_module and self.config.mezzanine_type == "IoTextra Combo":
                interface_type = "21"
            elif self.is_analog_module:
                interface_type = "01"
            else:
                # Allow manual selection if configuration was switched after creation
                print("Analog interface types available:")
                for idx, (code, label) in enumerate(((code, ANALOG_INTERFACE_LABELS[code]) for code in ANALOG_INTERFACE_LABELS), 1):
                    print(f"{idx}. {label} ({code})")
                while True:
                    try:
                        choice = int(input("Select analog interface type: ")) - 1
                        codes = list(ANALOG_INTERFACE_LABELS.keys())
                        if 0 <= choice < len(codes):
                            interface_type = codes[choice]
                            break
                    except ValueError:
                        pass
                    print(f"Please select 1-{len(ANALOG_INTERFACE_LABELS)}.")

        # Channel number selection
        used_numbers = [ch.channel_number for ch in self.config.channels]
        if channel_type == ChannelType.BIT.value:
            number_range = range(8)
        else:
            number_range = range(8)

        available_numbers = [i for i in number_range if i not in used_numbers]
        if not available_numbers:
            print("No available channel numbers remain for this channel type.")
            return

        print(f"Available channel numbers: {available_numbers}")
        while True:
            try:
                channel_number = int(input(f"Channel number ({available_numbers[0]}-{available_numbers[-1]}): "))
                if channel_number in available_numbers:
                    break
                else:
                    print(f"Please select from available numbers: {available_numbers}")
            except ValueError:
                print("Please enter a valid number.")

        # Actions / measurement range
        if channel_type == ChannelType.BIT.value:
            print("Channel actions:")
            print("0. Read only")
            print("1. Read + Write")
            while True:
                try:
                    actions = int(input("Select actions (0-1): "))
                    if actions in [0, 1]:
                        break
                    else:
                        print("Please select 0 or 1.")
                except ValueError:
                    print("Please enter a valid number.")
            measurement_range = None
        else:
            actions = 0
            print("Analog input channels are read-only. Actions set to 0 (Read).")
            measurement_range = self.prompt_measurement_range()

            # Prompt per-channel ADC calibration values (defaults come from module defaults)
            # adc_hardware_gain
            default_gain = DEFAULT_ADC_HARDWARE_GAIN
            print("\n--- ADC Hardware Gain Settings ---")
            print("Select the division factor (hardware gain) for this channel (set by jumpers):")
            print(f"  Default: two 49.9kΩ resistors in parallel -> K ≈ {DEFAULT_ADC_HARDWARE_GAIN:.4f} ({DEFAULT_ADC_HARDWARE_GAIN})")
            print(f"  Modified: one 49.9kΩ resistor -> K ≈ {0.47523809523809524:.4f} ({0.47523809523809524}) — requires changing jumpers")
            print(f"  IoTextra Analog V1 Boards Have a gain of K ≈ 0.2")
            print(f"  Custom: You can enter your own value if your making custom modifications different from above.")
            gain_input = input(f"\nEnter ADC hardware gain K (division factor) (default: {default_gain}): ").strip()
            if gain_input:
                try:
                    adc_hardware_gain = float(gain_input)
                except ValueError:
                    print("Invalid gain value, using hardware default.")
                    adc_hardware_gain = default_gain
            else:
                adc_hardware_gain = default_gain

            # shunt_resistance
            default_shunt = DEFAULT_SHUNT_RESISTANCE
            print("\n--- Current Shunt Resistance Settings ---")
            print(f"Select the shunt resistance value used in your hardware (in Ohms).")
            print(f"  Example: 0.12 = 120 Ohms, 0.249 = 249 Ohms")
            print(f"  IoTextra Analog V1 Boards use a 120 Ohm shunt which you can measure using a multimeter.")
            print(f"  You can set a different value according to your hardware setup of your IoTextra module.")
            shunt_input = input(f"\nShunt resistance in Ohms (default: {default_shunt}): ").strip()
            if shunt_input:
                try:
                    shunt_resistance = float(shunt_input)
                except ValueError:
                    print("Invalid shunt value, using hardware default.")
                    shunt_resistance = default_shunt
            else:
                shunt_resistance = default_shunt

            # adc_offset
            default_offset = DEFAULT_ADC_OFFSET
            print("\n--- ADC Offset Settings ---")
            print(f"Set the ADC offset in volts for this channel (can be negative).")
            print(f"  This compensates for any systematic offset in your measurements.")
            offset_input = input(f"\nADC offset in volts (can be negative) (default: {default_offset}): ").strip()
            if offset_input:
                try:
                    adc_offset = float(offset_input)
                except ValueError:
                    print("Invalid offset, using hardware default.")
                    adc_offset = default_offset
            else:
                adc_offset = default_offset

        # Create and add channel
        try:
            # Ensure ADC calibration fields are only set for analog channels
            if channel_type == ChannelType.BIT.value:
                adc_hardware_gain = None
                shunt_resistance = None
                adc_offset = None
            else:
                adc_hardware_gain = locals().get('adc_hardware_gain', None)
                shunt_resistance = locals().get('shunt_resistance', None)
                adc_offset = locals().get('adc_offset', None)

            channel = Channel(
                name=name,
                channel_type=channel_type,
                interface_type=interface_type,
                channel_number=channel_number,
                actions=actions,
                measurement_range=measurement_range,
                adc_hardware_gain=adc_hardware_gain,
                shunt_resistance=shunt_resistance,
                adc_offset=adc_offset,
            )
            self.config.channels.append(channel)
            print(f"\nChannel '{name}' added successfully!")
        except ValueError as e:
            print(f"Error creating channel: {e}")
    
    def edit_channel(self):
        """Edit an existing channel"""
        if not self.config.channels:
            print("No channels to edit.")
            return
        
        self.view_channels()
        while True:
            try:
                choice = int(input("\nEnter channel number to edit (1-{}): ".format(len(self.config.channels)))) - 1
                if 0 <= choice < len(self.config.channels):
                    break
                else:
                    print("Invalid channel number.")
            except ValueError:
                print("Please enter a valid number.")
        
        channel = self.config.channels[choice]
        print(f"\n--- Editing Channel: {channel.name} ---")
        
        # Edit channel properties
        while True:
            print(f"\nCurrent channel: {channel.name}")
            if channel.channel_type == ChannelType.BIT.value:
                print("1. Change name")
                print("2. Change interface type")
                print("3. Change channel number")
                print("4. Change actions")
                print("5. Done")
                action = input("Select action (1-5): ").strip()

                if action == "1":
                    while True:
                        new_name = input("New channel name (max 8 chars): ").strip()
                        if len(new_name) <= 8 and new_name:
                            if any(ch.name == new_name for ch in self.config.channels if ch != channel):
                                print("Channel name already exists. Please choose a different name.")
                                continue
                            channel.name = new_name
                            print(f"Channel name changed to: {new_name}")
                            break
                        else:
                            print("Channel name must be 1-8 characters long.")

                elif action == "2":
                    # Digital channels on combo mezzanines can choose GPIO or I2C
                    if self.config.mezzanine_type == "IoTextra Combo":
                        print("Digital channels on IoTextra Combo can use:")
                        print(f"1. {DIGITAL_INTERFACE_LABELS[InterfaceType.GPIO.value]} ({InterfaceType.GPIO.value})")
                        print(f"2. {DIGITAL_INTERFACE_LABELS[InterfaceType.I2C_TCA9534.value]} ({InterfaceType.I2C_TCA9534.value})")
                        while True:
                            choice = input("Select interface type for this digital channel (1-2): ").strip()
                            if choice == "1":
                                channel.interface_type = InterfaceType.GPIO.value
                                print("Interface type changed to GPIO")
                                break
                            elif choice == "2":
                                channel.interface_type = InterfaceType.I2C_TCA9534.value
                                print("Interface type changed to I2C")
                                break
                            else:
                                print("Please select 1 or 2.")
                    elif not self.is_analog_module:
                        # Pure digital mezzanines default to GPIO
                        print("Only GPIO interface available for this configuration.")
                    else:
                        # For analog-only mezzanines (non-combo), digital channels are not applicable
                        print("Digital channels are not applicable for this mezzanine type.")
                    

                elif action == "3":
                    used_numbers = [ch.channel_number for ch in self.config.channels if ch != channel]
                    available_numbers = [i for i in range(8) if i not in used_numbers]
                    available_numbers.append(channel.channel_number)
                    available_numbers = sorted(set(available_numbers))

                    print(f"Available channel numbers: {available_numbers}")
                    while True:
                        try:
                            new_number = int(input("New channel number (0-7): "))
                            if new_number in available_numbers:
                                channel.channel_number = new_number
                                print(f"Channel number changed to: {new_number}")
                                break
                            else:
                                print(f"Please select from available numbers: {available_numbers}")
                        except ValueError:
                            print("Please enter a valid number.")

                elif action == "4":
                    print("Channel actions:")
                    print("0. Read only")
                    print("1. Read + Write")
                    while True:
                        try:
                            new_actions = int(input("Select actions (0-1): "))
                            if new_actions in [0, 1]:
                                channel.actions = new_actions
                                print(f"Actions changed to: {new_actions}")
                                break
                            else:
                                print("Please select 0 or 1.")
                        except ValueError:
                            print("Please enter a valid number.")

                elif action == "5":
                    break
                else:
                    print("Invalid choice. Please select 1-5.")

            else:
                print("1. Change name")
                print("2. Change interface type")
                print("3. Change channel number")
                print("4. Change measurement range")
                print("5. Change ADC calibration (gain / shunt / offset)")
                print("6. Done")
                action = input("Select action (1-6): ").strip()

                if action == "1":
                    while True:
                        new_name = input("New channel name (max 8 chars): ").strip()
                        if len(new_name) <= 8 and new_name:
                            if any(ch.name == new_name for ch in self.config.channels if ch != channel):
                                print("Channel name already exists. Please choose a different name.")
                                continue
                            channel.name = new_name
                            print(f"Channel name changed to: {new_name}")
                            break
                        else:
                            print("Channel name must be 1-8 characters long.")

                elif action == "2":
                    if self.is_analog_module:
                        print("Analog interface types available:")
                        codes = list(ANALOG_INTERFACE_LABELS.keys())
                        for idx, code in enumerate(codes, 1):
                            label = ANALOG_INTERFACE_LABELS[code]
                            marker = " (current)" if channel.interface_type == code else ""
                            print(f"{idx}. {label} ({code}){marker}")
                        while True:
                            try:
                                selection = int(input("Select analog interface type: ")) - 1
                                if 0 <= selection < len(codes):
                                    channel.interface_type = codes[selection]
                                    print(f"Interface type changed to {ANALOG_INTERFACE_LABELS[channel.interface_type]}")
                                    break
                            except ValueError:
                                pass
                            print(f"Please select 1-{len(codes)}.")
                    else:
                        print("Interface type is fixed for this configuration.")

                elif action == "3":
                    used_numbers = [ch.channel_number for ch in self.config.channels if ch != channel]
                    available_numbers = [i for i in range(8) if i not in used_numbers]
                    available_numbers.append(channel.channel_number)
                    available_numbers = sorted(set(available_numbers))

                    print(f"Available channel numbers: {available_numbers}")
                    while True:
                        try:
                            new_number = int(input("New channel number (0-7): "))
                            if new_number in available_numbers:
                                channel.channel_number = new_number
                                print(f"Channel number changed to: {new_number}")
                                break
                            else:
                                print(f"Please select from available numbers: {available_numbers}")
                        except ValueError:
                            print("Please enter a valid number.")

                elif action == "4":
                    channel.measurement_range = self.prompt_measurement_range(channel.measurement_range)

                elif action == "5":
                    # Edit per-channel ADC calibration
                    print(f"Current ADC gain K: {channel.adc_hardware_gain}")
                    print("Select the division factor (hardware gain) for this channel (set by jumpers):")
                    print(f"  Default: two 49.9kΩ resistors in parallel -> K ≈ {DEFAULT_ADC_HARDWARE_GAIN:.4f} ({DEFAULT_ADC_HARDWARE_GAIN})")
                    print(f"  Modified: one 49.9kΩ resistor -> K ≈ {0.47523809523809524:.4f} ({0.47523809523809524}) — requires changing jumpers")
                    gain_input = input("New ADC hardware gain K (or enter to keep current): ").strip()
                    if gain_input:
                        try:
                            channel.adc_hardware_gain = float(gain_input)
                            print(f"ADC gain updated to {channel.adc_hardware_gain}")
                        except ValueError:
                            print("Invalid value, keeping current.")

                    print(f"Current shunt resistance (Ohm): {channel.shunt_resistance}")
                    sh_input = input("New shunt resistance in Ohms (or enter to keep current): ").strip()
                    if sh_input:
                        try:
                            channel.shunt_resistance = float(sh_input)
                            print(f"Shunt resistance updated to {channel.shunt_resistance}")
                        except ValueError:
                            print("Invalid value, keeping current.")

                    print(f"Current ADC offset (V): {channel.adc_offset}")
                    off_input = input("New ADC offset in volts (or enter to keep current): ").strip()
                    if off_input:
                        try:
                            channel.adc_offset = float(off_input)
                            print(f"ADC offset updated to {channel.adc_offset}")
                        except ValueError:
                            print("Invalid value, keeping current.")

                elif action == "6":
                    break
                else:
                    print("Invalid choice. Please select 1-5.")
    
    def remove_channel(self):
        """Remove a channel"""
        if not self.config.channels:
            print("No channels to remove.")
            return
        
        self.view_channels()
        while True:
            try:
                choice = int(input("\nEnter channel number to remove (1-{}): ".format(len(self.config.channels)))) - 1
                if 0 <= choice < len(self.config.channels):
                    channel = self.config.channels[choice]
                    confirm = input(f"Are you sure you want to remove channel '{channel.name}'? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        removed = self.config.channels.pop(choice)
                        print(f"Channel '{removed.name}' removed successfully!")
                    break
                else:
                    print("Invalid channel number.")
            except ValueError:
                print("Please enter a valid number.")
    
    def view_channels(self):
        """Display all configured channels"""
        if not self.config.channels:
            print("No channels configured.")
            return
        
        print("\n--- Configured Channels ---")
        print(f"{'#':<2} {'Name':<10} {'Type':<6} {'Interface':<20} {'Channel':<7} {'Actions':<12} {'Range':<20}")
        print("-" * 85)
        
        for i, channel in enumerate(self.config.channels, 1):
            if channel.channel_type == ChannelType.BIT.value:
                interface_desc = DIGITAL_INTERFACE_LABELS.get(channel.interface_type, channel.interface_type)
                actions_desc = "Read+Write" if channel.actions == 1 else "Read Only"
                range_desc = "-"
            else:
                interface_desc = ANALOG_INTERFACE_LABELS.get(channel.interface_type, channel.interface_type)
                actions_desc = "Read Only"
                range_desc = ANALOG_RANGE_LOOKUP.get(channel.measurement_range, channel.measurement_range or "-")
                # Append per-channel ADC calibration if present
                details = []
                if getattr(channel, 'adc_hardware_gain', None) is not None:
                    details.append(f"K={channel.adc_hardware_gain}")
                if getattr(channel, 'shunt_resistance', None) is not None:
                    details.append(f"Rs={channel.shunt_resistance}Ω")
                if getattr(channel, 'adc_offset', None) is not None:
                    details.append(f"Offset={channel.adc_offset}V")
                if details:
                    range_desc = f"{range_desc} ({', '.join(details)})"
            print(
                f"{i:<2} {channel.name:<10} {CHANNEL_TYPE_LABELS.get(channel.channel_type, channel.channel_type):<6} "
                f"{interface_desc:<20} {channel.channel_number:<7} {actions_desc:<12} {range_desc:<20}"
            )
    
    def save_config(self, filename: str = None):
        """Save configuration to JSON file"""
        if not self.config:
            print("No configuration to save.")
            return False
        
        if not filename:
            filename = input("Enter filename to save (default: config.json): ").strip()
            if not filename:
                filename = "config.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            # Convert configuration to dictionary
            hardware_dict = asdict(self.config.hardware)
            
            # Convert ADC addresses dictionary to a list for JSON compatibility
            # JSON will include 'adc_i2c_addrs': [addr1, addr2, ...] if any addresses are present
            adc_addrs = hardware_dict.pop('adc_i2c_addresses', {})
            addrs_list = []
            if isinstance(adc_addrs, dict):
                # Build ordered list by ADC number
                for i in sorted(adc_addrs.keys()):
                    if adc_addrs[i]:
                        addrs_list.append(adc_addrs[i])
            elif isinstance(adc_addrs, list):
                addrs_list = [a for a in adc_addrs if a]

            if addrs_list:
                hardware_dict['adc_i2c_addrs'] = addrs_list
            
            config_dict = {
                'module_type': self.config.module_type,
                'mezzanine_type': self.config.mezzanine_type,
                'channels': [],
                'network': asdict(self.config.network),
                'mqtt': asdict(self.config.mqtt),
                'hardware': hardware_dict,
                'pin_config': self.config.pin_config,
                'status_update_interval_s': self.config.status_update_interval_s
            }
            
            for channel in self.config.channels:
                channel_dict = asdict(channel)
                # Remove analog-only keys for digital channels, and drop None values
                if channel.channel_type == ChannelType.BIT.value:
                    channel_dict.pop('measurement_range', None)
                    channel_dict.pop('adc_hardware_gain', None)
                    channel_dict.pop('shunt_resistance', None)
                    channel_dict.pop('adc_offset', None)
                else:
                    # analog channel: remove measurement_range only if None
                    if channel_dict.get('measurement_range') is None:
                        channel_dict.pop('measurement_range', None)
                    # remove adc fields if None to keep JSON clean
                    if channel_dict.get('adc_hardware_gain') is None:
                        channel_dict.pop('adc_hardware_gain', None)
                    if channel_dict.get('shunt_resistance') is None:
                        channel_dict.pop('shunt_resistance', None)
                    if channel_dict.get('adc_offset') is None:
                        channel_dict.pop('adc_offset', None)

                config_dict['channels'].append(channel_dict)
            
            with open(filename, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            print(f"Configuration saved to: {filename}")
            self.config_file = filename
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def load_config(self, filename: str = None):
        """Load configuration from JSON file"""
        if not filename:
            filename = input("Enter filename to load: ").strip()
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        try:
            with open(filename, 'r') as f:
                config_dict = json.load(f)
            
            # Reconstruct configuration object
            channels = []
            for ch_data in config_dict.get('channels', []):
                channel = Channel(
                    name=ch_data['name'],
                    channel_type=ch_data['channel_type'],
                    interface_type=ch_data['interface_type'],
                    channel_number=ch_data['channel_number'],
                    actions=ch_data['actions'],
                    measurement_range=ch_data.get('measurement_range'),
                    adc_hardware_gain=ch_data.get('adc_hardware_gain'),
                    shunt_resistance=ch_data.get('shunt_resistance'),
                    adc_offset=ch_data.get('adc_offset'),
                )
                channels.append(channel)

            # Process hardware config to convert ADC addresses from JSON formats to internal dictionary
            hardware_data = config_dict['hardware'].copy()

            # If a new-style list is present (adc_i2c_addrs), convert to dict {1: addr, 2: addr}
            if 'adc_i2c_addrs' in hardware_data:
                addrs_list = hardware_data.pop('adc_i2c_addrs')
                try:
                    if isinstance(addrs_list, list):
                        adc_addresses = {i+1: addrs_list[i] for i in range(len(addrs_list)) if addrs_list[i]}
                    else:
                        adc_addresses = {}
                except Exception:
                    adc_addresses = {}
                if adc_addresses:
                    hardware_data['adc_i2c_addresses'] = adc_addresses
            else:
                adc_addresses = {}
                # Check for various ADC address field formats (legacy keys)
                # Iterate over a static list of keys to avoid "dictionary changed size during iteration"
                for key in list(hardware_data.keys()):
                    value = hardware_data[key]
                    # Handle formats like "adc_1_i2c_addr", "ADC1_I2C_ADDR", "adc1_i2c_addr"
                    if 'adc' in key.lower() and 'i2c' in key.lower() and 'addr' in key.lower():
                        # Extract ADC number from key
                        match = re.search(r'(\d+)', key)
                        if match:
                            adc_num = int(match.group(1))
                            adc_addresses[adc_num] = value
                            # Remove the original per-ADC key from hardware_data
                            hardware_data.pop(key, None)

                # Set the ADC addresses dictionary if we found legacy fields
                if adc_addresses:
                    hardware_data['adc_i2c_addresses'] = adc_addresses

            # Migrate any deprecated hardware-level calibration values into per-channel defaults.
            hw_gain = hardware_data.pop('adc_hardware_gain', None)
            hw_shunt = hardware_data.pop('shunt_resistance', None)
            hw_offset = hardware_data.pop('adc_offset', None)

            # If channels don't specify per-channel calibration, set them from hardware-level or module defaults
            for ch in channels:
                if ch.channel_type == ChannelType.ANALOG_INT.value:
                    if ch.adc_hardware_gain is None:
                        ch.adc_hardware_gain = hw_gain if hw_gain is not None else DEFAULT_ADC_HARDWARE_GAIN
                    if ch.shunt_resistance is None:
                        ch.shunt_resistance = hw_shunt if hw_shunt is not None else DEFAULT_SHUNT_RESISTANCE
                    if ch.adc_offset is None:
                        ch.adc_offset = hw_offset if hw_offset is not None else DEFAULT_ADC_OFFSET

            # Construct Configuration without a top-level interface_type; channel
            # objects contain per-channel interface codes. Determine whether this
            # is an analog mezzanine from mezzanine_type or channel contents.
            self.config = Configuration(
                module_type=config_dict['module_type'],
                mezzanine_type=config_dict['mezzanine_type'],
                channels=channels,
                network=NetworkConfig(**config_dict['network']),
                mqtt=MQTTConfig(**config_dict['mqtt']),
                hardware=HardwareConfig(**hardware_data),
                pin_config=config_dict['pin_config'],
                status_update_interval_s=config_dict['status_update_interval_s']
            )

            self.is_analog_module = (
                (self.config.mezzanine_type in MEZZANINE_ADC_COUNT and MEZZANINE_ADC_COUNT[self.config.mezzanine_type] > 0)
                or any(ch.channel_type == ChannelType.ANALOG_INT.value for ch in channels)
            )

            # Auto-set num_of_adcs for analog mezzanines if not already set
            if self.is_analog_module and self.config.hardware.num_of_adcs == 0:
                self.config.hardware.num_of_adcs = MEZZANINE_ADC_COUNT.get(self.config.mezzanine_type, 0)
            
            print(f"Configuration loaded from: {filename}")
            self.config_file = filename
            return True
            
        except FileNotFoundError:
            print(f"File not found: {filename}")
            return False
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def display_config(self):
        """Display current configuration"""
        if not self.config:
            print("No configuration loaded.")
            return
        
        print("\n=== Current Configuration ===")
        print(f"Module Type: {self.config.module_type}")
        print(f"Mezzanine Type: {self.config.mezzanine_type}")

        self.view_channels()
        print("\n--- Network Settings ---")
        print(f"Wi-Fi SSID: {self.config.network.wifi_ssid}")
        print(f"Wi-Fi Password: {self.config.network.wifi_password}")
        print(f"MQTT Broker: {self.config.mqtt.broker}")
        print(f"MQTT Port: {self.config.mqtt.port}")
        print(f"MQTT Client ID: {self.config.mqtt.client_id}")
        print(f"MQTT Base Topic: {self.config.mqtt.base_topic}")
        print("\n--- Hardware Settings ---")
        print(f"Hardware Mode: {self.config.hardware.mode.upper()}")
        print(f"I2C Bus ID: {self.config.hardware.i2c_bus_id}")
        print(f"I2C SDA Pin: {self.config.hardware.i2c_sda_pin}")
        print(f"I2C SCL Pin: {self.config.hardware.i2c_scl_pin}")
        print(f"I2C Device Address: {self.config.hardware.i2c_device_addr}")
        print(f"EEPROM I2C Address: {self.config.hardware.eeprom_i2c_addr}")
        print(f"EEPROM Size: {self.config.hardware.eeprom_size} bytes")
        
        # ADC Configuration (for analog modules)
        if self.config.hardware.num_of_adcs > 0:
            print(f"\nADC Configuration:")
            print(f"Number of ADCs: {self.config.hardware.num_of_adcs}")
            for adc_num in sorted(self.config.hardware.adc_i2c_addresses.keys()):
                print(f"  ADC {adc_num} I2C Address: {self.config.hardware.adc_i2c_addresses[adc_num]}")
        
        print("\nGPIO Host Pin Configuration:")
        for channel, pin in self.config.hardware.gpio_host_pins.items():
            print(f"  Channel {channel}: GPIO {pin}")
        print(f"\nPin Configuration: {self.config.pin_config}")
        print(f"Status Update Interval: {self.config.status_update_interval_s} seconds")
    
    # export_eeprom_format removed: EEPROM export functionality deprecated/removed

    def send_to_pi(self):
        """Send the current configuration to the Raspberry Pi Pico over serial."""
        if not self.config:
            print("No configuration loaded. Please create or load one first.")
            return False

        port = input("Enter serial port (default: /dev/cu.usbmodem2101): ").strip() or "/dev/cu.usbmodem2101"
        baudrate = 115200

        try:
            serial_connection = serial.Serial(port, baudrate)
        except serial.SerialException as e:
            print(f"Failed to open serial port {port}: {e}")
            return False

        try:
            # Serialize configuration to JSON
            hardware_dict = asdict(self.config.hardware)
            
            # Convert ADC addresses dictionary to a list for JSON compatibility
            adc_addrs = hardware_dict.pop('adc_i2c_addresses', {})
            addrs_list = []
            if isinstance(adc_addrs, dict):
                for i in sorted(adc_addrs.keys()):
                    if adc_addrs[i]:
                        addrs_list.append(adc_addrs[i])
            elif isinstance(adc_addrs, list):
                addrs_list = [a for a in adc_addrs if a]

            if addrs_list:
                hardware_dict['adc_i2c_addrs'] = addrs_list
            
            # Build channels list similarly to save_config (clean digital/None-only fields)
            channels_list = []
            for ch in self.config.channels:
                ch_dict = asdict(ch)
                if ch.channel_type == ChannelType.BIT.value:
                    # remove analog-only keys
                    ch_dict.pop('measurement_range', None)
                    ch_dict.pop('adc_hardware_gain', None)
                    ch_dict.pop('shunt_resistance', None)
                    ch_dict.pop('adc_offset', None)
                else:
                    if ch_dict.get('measurement_range') is None:
                        ch_dict.pop('measurement_range', None)
                    if ch_dict.get('adc_hardware_gain') is None:
                        ch_dict.pop('adc_hardware_gain', None)
                    if ch_dict.get('shunt_resistance') is None:
                        ch_dict.pop('shunt_resistance', None)
                    if ch_dict.get('adc_offset') is None:
                        ch_dict.pop('adc_offset', None)
                channels_list.append(ch_dict)

            config_dict = {
                'module_type': self.config.module_type,
                'mezzanine_type': self.config.mezzanine_type,
                'channels': channels_list,
                'network': asdict(self.config.network),
                'mqtt': asdict(self.config.mqtt),
                'hardware': hardware_dict,
                'pin_config': self.config.pin_config,
                'status_update_interval_s': self.config.status_update_interval_s
            }
            json_data = json.dumps(config_dict)
            message = f"<START>{json_data}<END>\n"
            #print(message)  # For debugging

            serial_connection.write(message.encode())
            serial_connection.flush()
            print(f"Configuration sent to Pi on {port}")
            print("Please wait 20 seconds...")
            # Wait for and read response
            buffer = ""
            timeout = 20  # Wait up to 20 seconds for a response
            start_time = time.time()

            while time.time() - start_time < timeout:
                if serial_connection.in_waiting > 0:
                    char = serial_connection.read(1).decode()
                    buffer += char
                    if "<START>" in buffer and "<END>" in buffer:
                        start = buffer.find("<START>") + len("<START>")
                        end = buffer.find("<END>")
                        json_str = buffer[start:end]
                        try:
                            received_data = json.loads(json_str)
                            print("Received data:", received_data)
                        except json.JSONDecodeError as e:
                            print("Failed to parse response JSON:", e)
                        buffer = buffer[end + len("<END>"):]  # Clear processed part
                        break
            return True
        except Exception as e:
            print(f"Error sending configuration: {e}")
            return False
        finally:
            serial_connection.close()

    def read_from_pi(self):
        """Read and display configuration data sent back from the Raspberry Pi Pico."""
        port = input("Enter serial port (default: /dev/cu.usbmodem2101): ").strip() or "/dev/cu.usbmodem2101"
        baudrate = 115200

        try:
            serial_connection = serial.Serial(port, baudrate)
        except serial.SerialException as e:
            print(f"Failed to open serial port {port}: {e}")
            return False

        try:
            # Send read command
            read_command = f"<START>{{\"command\":\"read\"}}<END>\n"
            serial_connection.write(read_command.encode())
            serial_connection.flush()

            buffer = ""
            timeout = 5  # Increased to 5 seconds
            start_time = time.time()
            while time.time() - start_time < timeout:
                if serial_connection.in_waiting > 0:
                    char = serial_connection.read(1).decode()
                    buffer += char
                    if "<START>" in buffer and "<END>" in buffer:
                        start = buffer.find("<START>") + len("<START>")
                        end = buffer.find("<END>")
                        json_str = buffer[start:end]
                        try:
                            received_data = json.loads(json_str)
                            print("Received data:", received_data)
                            return True  # Exit loop on successful response
                        except json.JSONDecodeError as e:
                            print("Failed to parse response JSON:", e)
                            print(f"Raw buffer: {buffer!r}")
                            return False
                        finally:
                            buffer = buffer[end + len("<END>"):]  # Clear processed part
            print("No response received within timeout period.")
            print(f"Raw buffer: {buffer!r}")
            return False
        except Exception as e:
            print(f"Error reading from Pi: {e}")
            return False
        finally:
            serial_connection.close()
        
    def run(self):
        """Main application loop"""
        print("=== IoTextra Digital I/O Configuration Tool ===")
        print("This tool helps configure digital I/O nodes for IoTextra mezzanines.")
        
        while True:
            print("\n" + "="*50)
            print("Main Menu:")
            print("1. Create new configuration")
            print("2. Load configuration from file")
            print("3. Save configuration to file")
            print("4. Edit channel configuration")
            print("5. View current configuration")
            print("6. Send configuration to Pi")
            print("7. Read configuration from Pi")
            print("8. Exit")

            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == "1":
                self.create_new_config()
            elif choice == "2":
                self.load_config()
            elif choice == "3":
                self.save_config()
            elif choice == "4":
                if self.config:
                    self.configure_channels()
                else:
                    print("No configuration loaded. Please create or load one first.")
            elif choice == "5":
                self.display_config()
            elif choice == "6":
                self.send_to_pi()
            elif choice == "7":
                self.read_from_pi()
            elif choice == "8":
                if self.config and not self.config_file:
                    save = input("Save configuration before exiting? (y/n): ").strip().lower()
                    if save in ['y', 'yes']:
                        self.save_config()
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please select 1-8.")

def main():
    """Main entry point"""
    try:
        configurator = Configurator()
        configurator.run()
    except KeyboardInterrupt:
        print("\n\nConfiguration interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
