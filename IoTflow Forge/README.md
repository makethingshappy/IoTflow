# IoTflow Forge

A configuration tool for configuring digital I/O nodes for IoTextra mezzanines, saving/loading configurations as JSON files, and sending configurations to devices via serial.

## Overview

This tool allows you to:
- Create new digital I/O node configurations interactively
- Configure up to 8 channels with specific interface types
- Set network (Wi-Fi) and MQTT communication parameters
- Configure hardware settings (GPIO/I2C modes, EEPROM, pin mappings)
- Set pin configurations for input/output channels
- Save configurations as JSON files for later use
- Load existing configurations for editing or viewing
- Send configurations to Raspberry Pi Pico (or similar) devices over serial
- Read configurations back from devices over serial
- View current configurations in detail
- Export estimated EEPROM format information (binary representation details)

The tool is designed to create configurations that can be stored in EEPROM on the device, as described in the accompanying documentation. Configurations define digital input/output nodes based on IoTextra mezzanines and supported microcontroller modules. The firmware on the device (not included in this tool) would use this configuration to interact with channels via MQTT.

## Features

### Supported Module Types
- IoTbase PICO (with installed modules like Raspberry Pi Pico W, Pico 2W, Waveshare ESP32-S3 PICO, etc.)
- IoTbase Nano (future full support; listed but development ongoing)
- IoTsmart ESP32-S3

Note: At this stage, only MQTT over Wi-Fi is supported, so modules without Wi-Fi are not fully usable.

### Supported Interface Types
- **01** - GPIO only
- **11** - I2C via TCA9534
- **12** - GPIO and I2C via TCA9534 (future expansion; allows per-channel selection)

### Channel Configuration
Each channel supports:
- **Name**: Up to 8 alphanumeric characters (unique per configuration)
- **Type**: Currently only "1" (Bit type; digital input/output)
- **Interface**: GPIO ("01") or I2C ("11"), depending on overall interface type
- **Channel Number**: 0-7 (corresponds to AP0-AP7 on HOST connector or P0-P7 on TCA9534)
- **Actions**: Read-only (0) or Read+Write (1); stored as a bit field (bit 0 for write capability)

Up to 8 channels per node. Channels are stored in EEPROM on the device.

### Network Configuration
- **Wi-Fi SSID and Password**: For connecting the device to Wi-Fi networks

### MQTT Configuration
- **Broker Address**: IP or hostname of the MQTT broker
- **Port**: MQTT port (default: 1883)
- **Client ID**: Unique identifier (default: "pico-iotextra-controller-1")
- **Base Topic**: Base MQTT topic for publishing/subscribing (default: "iotextra/device_1")

### Hardware Configuration
- **Hardware Mode**: "gpio" or "i2c" (default: "i2c")
- **I2C Settings**: Bus ID (default: 0), SDA pin (default: 20), SCL pin (default: 21), device address (default: "0x3f")
- **EEPROM Settings**: I2C address (default: "0x57"), size in bytes (default: 1024); EEPROM is used to store the node configuration and is accessible only from the node
- **GPIO Pin Mapping**: Customizable mapping for HOST connector channels 1-8 (defaults: 10,11,12,13,14,15,18,19)

### Pin Configuration
- **Input/Output Mapping**: 8-bit binary string defining channel directions (stored as e.g., "0b00001111")
  - Format: "0b[P7][P6][P5][P4][P3][P2][P1][P0]"
  - 1 = Input channel, 0 = Output channel
- **Status Update Interval**: Frequency for publishing status updates in seconds (default: 30)

### Serial Communication
- Send JSON configurations to devices (e.g., Raspberry Pi Pico) over serial for storage in EEPROM
- Read configurations back from devices over serial
- Default serial port: /dev/cu.usbmodem2101 (configurable), baudrate: 115200

### Node Interaction (as per Documentation)
The configuration enables firmware to handle digital nodes via MQTT commands:
- Read channel status by name
- Turn on channel by name
- Turn off channel by name
- Switch channel by name

Future enhancements may include channel IDs for faster interaction.

## Installation

### Requirements
- Python 3.10 or higher
- `pyserial` for serial communication features (install via `pip install pyserial`)
- Standard library modules: json, sys, serial, time, typing, dataclasses, enum

### Running the Tool
```bash
python3 configurator.py
```

## Usage

### Main Menu Options

1. **Create new configuration** - Interactively create a new configuration
2. **Load configuration from file** - Load an existing JSON file
3. **Save configuration to file** - Save the current configuration to a JSON file
4. **Edit channel configuration** - Modify channels in the current configuration
5. **View current configuration** - Display details of the current configuration
6. **Export EEPROM format info** - Show estimated binary EEPROM usage and format details
7. **Send configuration to Pi** - Transmit the configuration over serial to the device
8. **Read configuration from Pi** - Retrieve the configuration over serial from the device
9. **Exit** - Exit the tool (prompts to save if unsaved changes)

### Creating a New Configuration

1. Select module type from the list
2. Enter mezzanine type (e.g., "IoTextra Octal2")
3. Choose interface type (GPIO, I2C, or both)
4. Configure network settings (Wi-Fi SSID/password)
5. Configure MQTT settings (broker, port, etc.)
6. Configure hardware settings (mode, I2C pins/addresses, EEPROM, GPIO mapping)
7. Set pin configuration (input/output mapping, with examples for common modules)
8. Configure channels interactively (add/edit/remove/view)

### Channel Management

- **Add Channel**: Create new channels with validation for uniqueness and limits
- **Edit Channel**: Modify name, interface, number, or actions
- **Remove Channel**: Delete channels with confirmation
- **View Channels**: Display channels in a tabular format

### Sending/Reading Configurations
- Use option 7 to send the current JSON configuration over serial (wrapped in <START>...<END>)
- Use option 8 to send a read command and receive the configuration back
- Supports timeout and JSON parsing for responses

## Configuration File Format

Configurations are saved in JSON format:

```json
{
  "module_type": "IoTbase PICO",
  "mezzanine_type": "IoTextra Octal2",
  "interface_type": "11",
  "channels": [
    {
      "name": "Relay1",
      "channel_type": "1",
      "interface_type": "11",
      "channel_number": 0,
      "actions": 1
    }
  ],
  "network": {
    "wifi_ssid": "MyWiFiNetwork",
    "wifi_password": "MyWiFiPassword"
  },
  "mqtt": {
    "broker": "192.168.1.100",
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
    "gpio_host_pins": {
      "1": 10, "2": 11, "3": 12, "4": 13,
      "5": 14, "6": 15, "7": 18, "8": 19
    }
  },
  "pin_config": "0b00001111",
  "status_update_interval_s": 30
}
```

### Configuration Parameters

#### Network Settings
- `wifi_ssid`: Wi-Fi network name (default: empty)
- `wifi_password`: Wi-Fi network password (default: empty)

#### MQTT Settings
- `broker`: MQTT broker IP/hostname (default: empty)
- `port`: MQTT broker port (default: 1883)
- `client_id`: Unique client identifier (default: "pico-iotextra-controller-1")
- `base_topic`: Base MQTT topic (default: "iotextra/device_1")

#### Hardware Settings
- `mode`: "gpio" or "i2c" (default: "i2c")
- `i2c_bus_id`: I2C bus identifier (default: 0)
- `i2c_sda_pin`: I2C SDA pin (default: 20)
- `i2c_scl_pin`: I2C SCL pin (default: 21)
- `i2c_device_addr`: Mezzanine I2C address (hex, default: "0x3f")
- `eeprom_i2c_addr`: EEPROM I2C address (hex, default: "0x57")
- `eeprom_size`: EEPROM size in bytes (default: 1024)
- `gpio_host_pins`: Dictionary mapping channels 1-8 to GPIO pins

#### Pin Configuration
- `pin_config`: Binary string for channel directions (default: "0b00001111")
  - Examples:
    - IoTExtra Relay2: "0b11110000" (channels 1-4 outputs, 5-8 unused/inputs)
    - IoTExtra Input: "0b11111111" (all inputs)
    - IoTExtra Octal: "0b00001111" (channels 0-3 outputs, 4-7 inputs)

#### Status Settings
- `status_update_interval_s`: Update frequency in seconds (default: 30)

## EEPROM Requirements

- **Minimum**: 8 Kbit (1024 bytes) EEPROM

## Validation Rules

- Channel names: 1-8 characters, unique
- Channel numbers: 0-7, unique
- Maximum: 8 channels
- I2C address: Required for I2C interfaces, valid hex
- Actions: 0 or 1
- Pin configuration: 0-255 (8-bit value), supports binary/hex/decimal input
- Status interval: Positive integer

## Future Enhancements

- Support for analog I/O nodes
- Event counter functionality for digital nodes
- Interaction with other platforms (e.g., Blynk, Modbus)
- Additional interface types (e.g., MCP23008)
- Direct binary EEPROM export and programming tools
- Advanced MQTT features (e.g., security)
- Node-RED dashboard examples for channel commands (read/on/off/switch)
- Virtual channel IDs for faster MQTT interactions

## Technical Notes

- Configurations are PC-side JSON; devices store in binary EEPROM format
- Serial communication uses <START>JSON<END> framing
- EEPROM is accessible only from the node (default I2C address known to firmware)
- Tool supports interactive editing with defaults for quick setup
- Based on documentation for Node-RED integration with digital I/O mezzanines

## Troubleshooting

- **Serial errors**: Ensure pyserial is installed and the port is correct (e.g., /dev/cu.usbmodem2101 on macOS)
- **"Channel name already exists"**: Use unique names
- **"Maximum 8 channels reached"**: Remove channels before adding more
- **"Invalid I2C address"**: Use hex format (e.g., "0x3f")
- **"No configuration loaded"**: Create or load before editing/sending
- **"Invalid pin configuration"**: Use "0b..." (binary), "0x..." (hex), or decimal
- **No response from device**: Check serial connection, baudrate, and device firmware

## License

This tool is part of the IoTflow project for Smart IoT Modular PCBs.
