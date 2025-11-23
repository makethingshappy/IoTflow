# IoTflow Forge Configuration Tool

A comprehensive command-line interface tool for configuring digital and analog I/O nodes for IoTextra mezzanines, managing configurations as JSON files, and communicating with devices via serial.

## Overview

IoTflow Forge enables you to:
- Create configurations for both **digital I/O** and **analog input** nodes interactively
- Configure up to 8 channels per node with specific interface types and measurement ranges
- Set network (Wi-Fi) and MQTT communication parameters
- Configure hardware settings (GPIO/I2C modes, EEPROM, ADC settings, pin mappings)
- Define per-channel calibration for analog inputs (hardware gain, shunt resistance, offset)
- Save configurations as JSON files for later use
- Load and edit existing configurations
- Send configurations to devices (Raspberry Pi Pico, ESP32, etc.) over serial
- Read configurations back from devices over serial
- View detailed configuration summaries

The tool creates configurations that can be stored in EEPROM on the device. The firmware on the device uses these configurations to interact with channels via MQTT, enabling remote control and monitoring of I/O operations.

## Features

### Supported Microcontrollers and System On Module (SOM) Microcontrollers
- **IoTbase PICO** - Compatible with Raspberry Pi Pico, Pico 2, Pico W, Pico 2W, Waveshare ESP32-S3 PICO
- **IoTbase NANO** - Arduino Nano ESP32 or ESP32-S3
- **IoTsmart ESP32-S3** - Tiny Adaptor Board with Cable is required for flashing
- **IoTsmart RP2040 or RP2350** - Tiny Adaptor Board with Cable is required for flashing
- **IoTsmart XIAO** - Tiny Adaptor Board with Cable is required for flashing
- **IoTsmart XIAO** - Tiny Adaptor Board with Cable is required for flashing

*Note:*

*Only MQTT over Wi-Fi is currently supported, so modules without Wi-Fi capabilities have limited use.*

*IoTsmart modules are System-on-Module (SOM) microcontroller boards that provide the primary compute and control functionality for the system.
Each module integrates a complete MCU environment, and different form factors (soldered SoM, slot-based modules such as the IoTsmart XIAO, etc.) are treated as implementation variations rather than separate device classes.*

### Supported Mezzanine Categories

#### Digital I/O Mezzanines
- IoTextra Input
- IoTextra Octal
- IoTextra Relay
- IoTextra SSR Small
- Custom digital mezzanines

**Supported Digital Interface Types:**
- **01** - GPIO only
- **11** - I2C via TCA9534 I/O expander
- **12** - GPIO and I2C via TCA9534 (future expansion)

#### Analog Input Mezzanines
- IoTextra Analog (2x TI ADC1115 ADCs)
- IoTextra Combo (1 TI ADC1115 ADC + digital I/O)
- IoTextra Analog2 (Coming Soon)
- IoTextra Analog3 (Future)
- Custom analog mezzanines

**Supported Analog Interface Types:**
- **01** - IoTextra Analog
- **21** - IoTextra Combo
- **02** - IoT Analog 2
- **03** - IoT Analog 3

### Channel Configuration

Each channel supports:

#### Digital Channels (Type "1" - Bit)
- **Name**: Up to 8 alphanumeric characters (unique per configuration)
- **Type**: "1" (Bit type for digital input/output)
- **Interface**: GPIO ("01") or I2C ("11")
- **Channel Number**: 0-7 (maps to AP0-AP7 on HOST connector or P0-P7 on TCA9534)
- **Actions**: 
  - 0 = Read-only
  - 1 = Read+Write (allows control via MQTT)

#### Analog Channels (Type "2" - Int)
- **Name**: Up to 8 alphanumeric characters (unique per configuration)
- **Type**: "2" (Integer type for analog input)
- **Interface**: Analog interface code (01, 21, 02, 03)
- **Channel Number**: 0-7 (maps to ADC input channels)
- **Actions**: 0 (Read-only; analog inputs cannot be written to)
- **Measurement Range**: Selectable from supported ranges:
  - Voltage: 0-0.5V, 0-5V, 0-10V, ±0.5V, ±5V, ±10V
  - Current: 0-20mA, ±20mA, 4-20mA, 0-40mA

#### Per-Channel ADC Calibration (Analog Only)
Each analog channel can have individual calibration parameters:
- **ADC Hardware Gain (K)**: Division factor set by hardware resistors
  - Default: 0.2376 (two 49.9kΩ resistors in parallel)
  - Modified: 0.4752 (one 49.9kΩ resistor - requires jumper changes)
  - Custom values supported for specialized configurations
- **Shunt Resistance**: Current measurement shunt value in Ohms
  - Default: 0.249Ω
  - IoTextra Analog V1 boards typically use 0.12Ω (120 Ohms)
  - Custom values supported if you want to change the hardware
- **ADC Offset**: Voltage offset compensation in volts
  - Default: 0.0V
  - Can be positive or negative to compensate for systematic errors

*Maximum 8 channels per node (digital, analog, or mixed for combo boards).*

### Network Configuration
- **Wi-Fi SSID and Password**: Device network connectivity settings

### MQTT Configuration
- **Broker Address**: IP address or hostname of MQTT broker
- **Port**: MQTT port (default: 1883)
- **Client ID**: Unique device identifier (default: "pico-iotextra-controller-1")
- **Base Topic**: Base MQTT topic for pub/sub (default: "iotextra/device_1")

### Hardware Configuration

#### Common Settings
- **Hardware Mode**: "gpio" or "i2c" (i2c required for analog modules)
- **I2C Settings**: 
  - Bus ID (default: 0)
  - SDA pin (default: 20)
  - SCL pin (default: 21)
  - Device address for I/O expander (default: 0x3f or 0x27)
- **EEPROM Settings**: 
  - I2C address (default: 0x57)
  - Size in bytes (default: 1024)
- **GPIO Pin Mapping**: Customizable mapping for HOST connector channels 1-8
  - Defaults: 10, 11, 12, 13, 14, 15, 18, 19 for channels 1-8

#### Analog-Specific Settings
- **Number of ADCs**: 1-4 ADCs per mezzanine
- **ADC I2C Addresses**: Individual addresses for each ADC (e.g., 0x49, 0x48)
- **ADC Sampling Rate**: Configurable in SPS (samples per second)
  - Options: 8, 16, 32, 64, 128 (default), 250, 475, 860 SPS
  - Maps to ADS1115/ADS1015 ADC configuration codes

### Pin Configuration (Digital Only)
- **Input/Output Mapping**: 8-bit binary string defining channel directions
  - Format: "0b[P7][P6][P5][P4][P3][P2][P1][P0]"
  - 1 = Input channel, 0 = Output channel
  - Examples:
    - IoTExtra Relay2: "0b11110000" (channels 1-4 outputs, 5-8 unused)
    - IoTExtra Input: "0b11111111" (all inputs)
    - IoTExtra Octal: "0b00001111" (channels 0-3 outputs, 4-7 inputs)
- **Status Update Interval**: Frequency for publishing status updates in seconds (default: 30)

### Serial Communication
- Send JSON configurations to devices over serial for EEPROM storage
- Read configurations back from devices
- Default serial port: /dev/cu.usbmodem2101 (configurable)
- Baudrate: 115200
- Protocol: JSON wrapped in `<START>...<END>` delimiters

### MQTT Node Interaction
Configured nodes enable firmware to handle digital and analog operations via MQTT:
- **Digital Channels**:
  - Read channel status by name
  - Turn on/off channel by name
  - Switch (toggle) channel by name
- **Analog Channels**:
  - Read current measurement value
  - Subscribe to periodic status updates

## Installation

### Requirements
- Python 3.10 or higher
- `pyserial` for serial communication
  ```bash
  pip install pyserial
  ```
- Standard library modules: json, sys, serial, time, typing, dataclasses, enum, re

### Running the Tool
```bash
python3 IoTflow_Forge.py
```

## Usage

### Main Menu Options

1. **Create new configuration** - Start fresh with interactive configuration wizard
2. **Load configuration from file** - Import existing JSON configuration
3. **Save configuration to file** - Export current configuration to JSON
4. **Edit channel configuration** - Modify channels in loaded configuration
5. **View current configuration** - Display detailed configuration summary
6. **Send configuration to Pi** - Transmit configuration via serial to device
7. **Read configuration from Pi** - Retrieve configuration from device via serial
8. **Exit** - Close tool (prompts to save unsaved changes)

### Creating a New Configuration

The tool guides you through:

1. **Module Selection**: Choose your microcontroller board type
2. **Mezzanine Category**: Select Digital I/O or Analog Input
3. **Mezzanine Type**: Pick specific board or enter custom name
4. **Network Settings**: Configure Wi-Fi credentials
5. **MQTT Settings**: Set broker details and topics
6. **Hardware Settings**: 
   - I2C bus configuration
   - EEPROM parameters
   - For analog: ADC count, I2C addresses, sampling rate
   - GPIO pin mappings
7. **Pin Configuration**: Set input/output directions (digital only)
8. **Channel Configuration**: Add, configure, and organize channels

### Channel Management

#### Adding Channels
- **Digital Channels**:
  - Assign unique name (max 8 characters)
  - Select interface type (GPIO or I2C)
  - Choose channel number (0-7)
  - Set actions (read-only or read+write)
  
- **Analog Channels**:
  - Assign unique name (max 8 characters)
  - Select measurement range (voltage/current)
  - Choose channel number (0-7, maps to ADC inputs)
  - Configure per-channel calibration:
    - Hardware gain (K factor)
    - Shunt resistance for current measurements
    - Offset compensation
  - Actions automatically set to read-only

#### Editing Channels
- Modify name, interface, channel number, or actions
- For analog: Update measurement range or calibration parameters
- All changes validated in real-time

#### Removing Channels
- Delete channels with confirmation prompt
- Channel numbers become available for reuse

#### Viewing Channels
- Tabular display with all channel details
- Shows calibration parameters for analog channels

### Sending/Reading Configurations

**Send Configuration (Option 6)**:
- Wraps JSON in `<START>...<END>` delimiters
- Transmits via serial to device
- Waits up to 20 seconds for device acknowledgment
- Device stores configuration in EEPROM

**Read Configuration (Option 7)**:
- Sends read command to device
- Receives and displays stored configuration
- Useful for verification and backup

## Configuration File Format

Configurations are saved as JSON files with the following structure:

```json
{
  "module_type": "IoTbase PICO",
  "mezzanine_type": "IoTextra Analog",
  "channels": [
    {
      "name": "VoltIn1",
      "channel_type": "2",
      "interface_type": "01",
      "channel_number": 0,
      "actions": 0,
      "measurement_range": "0b00000010",
      "adc_hardware_gain": 0.23761904761904762,
      "shunt_resistance": 0.249,
      "adc_offset": 0.0
    }
  ],
  "network": {
    "wifi_ssid": "MyNetwork",
    "wifi_password": "MyPassword"
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
    "num_of_adcs": 2,
    "adc_i2c_addrs": ["0x49", "0x48"],
    "adc_sampling_rate": 128,
    "gpio_host_pins": {
      "1": 10, "2": 11, "3": 12, "4": 13,
      "5": 14, "6": 15, "7": 18, "8": 19
    }
  },
  "pin_config": "0b00001111",
  "status_update_interval_s": 30
}
```

### Key Configuration Parameters

#### Network Settings
- `wifi_ssid`: Network name
- `wifi_password`: Network password

#### MQTT Settings
- `broker`: Broker IP/hostname
- `port`: Broker port (default: 1883)
- `client_id`: Unique identifier
- `base_topic`: Topic prefix for device

#### Hardware Settings
- `mode`: "gpio" or "i2c"
- `i2c_bus_id`: I2C bus number
- `i2c_sda_pin`: SDA GPIO pin
- `i2c_scl_pin`: SCL GPIO pin
- `i2c_device_addr`: I/O expander address (hex)
- `eeprom_i2c_addr`: EEPROM address (hex)
- `eeprom_size`: EEPROM capacity in bytes
- `num_of_adcs`: Number of ADCs (analog only)
- `adc_i2c_addrs`: Array of ADC addresses (analog only)
- `adc_sampling_rate`: Sampling rate in SPS (analog only)
- `gpio_host_pins`: Channel-to-GPIO mapping

#### Channel Settings
- `name`: Channel identifier (max 8 chars)
- `channel_type`: "1" (digital) or "2" (analog)
- `interface_type`: Interface code
- `channel_number`: Physical channel (0-7)
- `actions`: 0 (read-only) or 1 (read+write)
- `measurement_range`: Analog range code (analog only)
- `adc_hardware_gain`: K factor (analog only)
- `shunt_resistance`: Shunt value in Ω (analog only)
- `adc_offset`: Offset in V (analog only)

#### Pin Configuration (Digital Only)
- `pin_config`: Binary string (e.g., "0b00001111")
- `status_update_interval_s`: Update frequency in seconds

## EEPROM Requirements

- **Minimum Size**: 8 Kbit (1024 bytes)
- **Estimated Usage**: ~228-300 bytes depending on channel count and types
- **Storage**: Device firmware handles EEPROM writing after receiving configuration
- **Access**: EEPROM is device-internal; configuration tool doesn't directly program it

## Validation Rules

The tool enforces:
- **Channel names**: 1-8 characters, alphanumeric, unique within configuration
- **Channel numbers**: 0-7, unique per channel type
- **Maximum channels**: 8 total per node
- **I2C addresses**: Valid hex format (0x03-0x77 for 7-bit addresses)
- **Actions**: 0 or 1 for digital; must be 0 for analog
- **Pin configuration**: 0-255 (8-bit), accepts binary/hex/decimal input
- **ADC calibration**: Positive values for gain/shunt; any numeric for offset
- **Measurement ranges**: Must be from predefined list
- **Status interval**: Positive integer

## Analog Measurement Ranges

The tool supports the following measurement ranges for analog channels:

| Code | Range | Description |
|------|-------|-------------|
| 0b00000001 | 0-0.5V | Unipolar voltage |
| 0b00000010 | 0-5V | Unipolar voltage |
| 0b00000011 | 0-10V | Unipolar voltage |
| 0b10000001 | ±0.5V | Bipolar voltage |
| 0b10000010 | ±5V | Bipolar voltage |
| 0b10000011 | ±10V | Bipolar voltage |
| 0b00100001 | 0-20mA | Unipolar current |
| 0b10100001 | ±20mA | Bipolar current |
| 0b00100010 | 4-20mA | Industrial current loop |
| 0b00100011 | 0-40mA | Extended current range |

## ADC Sampling Rates

Available sampling rates (maps to ADS1115/ADS1015 configuration):

| SPS | Config Code | Notes |
|-----|-------------|-------|
| 8 | 0 | 128 /8 samples per second - Lowest noise, slowest |
| 16 | 1 | 250 /16 samples per second |
| 32 | 2 | 490 /32 samples per second |
| 64 | 3 | 920 /64 samples per second |
| 128 | 4 | 1600/128 samples per second **Default** - balanced |
| 250 | 5 | 2400/250 samples per second |
| 475 | 6 | 3300/475 samples per second |
| 860 | 7 | -/860 samples per second - Fastest, higher noise |

## Calibration Guide

### ADC Hardware Gain (K Factor)

The hardware gain compensates for voltage division in the analog input circuitry:

- **Standard Configuration (K ≈ 0.2376)**: Two 49.9kΩ resistors in parallel
- **Modified Configuration (K ≈ 0.4752)**: Single 49.9kΩ resistor (requires jumper change)
- **V1 Boards (K ≈ 0.2)**: Older IoTextra Analog boards
- **Custom**: Measure and calculate based on your circuit

### Shunt Resistance

For current measurements, the shunt resistance determines the voltage-to-current conversion:

- **Standard (0.249Ω)**: Common in newer designs
- **V1 Boards (0.12Ω / 120Ω)**: Verify with multimeter
- **Custom**: Match your hardware specifications

### ADC Offset

Compensates for systematic measurement errors:

- Set to 0.0V for no compensation
- Positive values shift readings up
- Negative values shift readings down
- Calibrate by measuring known reference voltages

## Troubleshooting

### Serial Communication Issues
- **Error**: "Failed to open serial port"
  - **Solution**: Install pyserial (`pip install pyserial`), verify port name
  - **macOS**: Ports typically `/dev/cu.usbmodem*`
  - **Linux**: Ports typically `/dev/ttyACM*` or `/dev/ttyUSB*`
  - **Windows**: Ports typically `COM*`

### Configuration Errors
- **"Channel name already exists"**: Use unique names for all channels
- **"Maximum 8 channels reached"**: Remove channels before adding more
- **"Invalid I2C address"**: Use hex format (e.g., "0x3f", "0x49")
- **"Invalid pin configuration"**: Use "0b..." (binary), "0x..." (hex), or decimal

### Device Communication
- **"No response from device"**: 
  - Verify serial connection is active
  - Check device is powered and running firmware
  - Ensure baudrate matches (115200)
  - Wait full timeout period (20 seconds for send, 5 for read)
- **"Failed to parse response JSON"**:
  - Device firmware may not be compatible
  - Check for firmware updates

### Configuration Loading
- **"Error loading configuration"**:
  - Verify JSON file syntax
  - Check all required fields are present
  - Legacy configurations may need manual migration of ADC settings

## Future Enhancements

- Support for event counters on digital inputs
- Additional I/O expander types
- Advanced MQTT features (TLS, authentication)
- Configuration version management

## Technical Notes

- Configurations stored as JSON on PC, converted to binary format by device firmware
- Serial protocol uses `<START>` and `<END>` delimiters for reliable framing
- EEPROM accessible only from device (I2C address known to firmware)
- Tool supports interactive editing with sensible defaults for rapid prototyping
- Analog calibration supports per-channel values for maximum flexibility
- Legacy hardware-level calibration values automatically migrated to per-channel settings
- Compatible with Node-RED for MQTT-based automation

## License

This tool is part of the IoTflow project for IoTextra Hardware Modules.

---

**Author**: Arshia Keshvari  
**Role**: Independent Developer, Engineer, and Project Author
