# IoTflow Setup Guide for IoTextra module series & Node-RED

A universal framework for integrating IoTextra module series with Node-RED or similar software via IoTsmart series devices.

---

## Table of Contents
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Step 1: Hardware Setup](#step-1-hardware-setup)
- [Step 2: Flashing MicroPython Firmware](#step-2-flashing-micropython-firmware)
- [Step 3: Firmware Configuration](#step-3-firmware-configuration)
- [Step 3: Utility Configuration I/O Tool (IoTflow Forge)](#step-4-Utility-Configuration-I/O-Tool)
- [Step 5: Node-RED Installation](#step-5-node-red-installation)
- [Step 6: Importing the Example Dashboard](#step-6-importing-the-example-dashboard)
- [How to use iotextra custom Node-RED nodes](#How-to-use-iotextra-custom-Node-RED-nodes)
- [How It Works: MQTT Protocol](#how-it-works-mqtt-protocol)
- [Troubleshooting](#troubleshooting)

---

## Features
- **Versatile control:** Monitor analog and digital I/O channels.
- **Wireless connectivity:** Wi-Fi and standard MQTT protocol.
- **Easy integration:** Custom Node-RED nodes for quicker set up.
- **Dashboard examples:** Example flows for node-red are supplied for IoTextra Relay2, Input, Analog, Combo and Octal modules.
- **Standardised firmware:** Universal firmware driver can be used with any IoTextra module out of the box.
- **Simple configuration:** All 8 channels can be configured to be either input or output, as well as selecting interface type either I2C or GPIO (HOST connector) using a config file.

---

## Hardware Requirements
- 1 x IoTbase
- 1 x Microcontroller or IoTsmart Module
- 1 x IoTextra Module
- 1 x USB Cable
- 1 x Microcontroller (ESP32-S3, PICO, PICO W, PICO 2W and etc)
- *(Optional)* Computer to run Node-RED or a dedicated Edge device, e.g. Raspberry Pi 5

---

## Software Requirements
- **Thonny IDE** – for flashing firmware to your microcontroller
- **Node-RED** – installed locally or on a Single Board Computer like Raspberry Pi

---

## Step 1: Hardware Setup
- Attach MCU to the IoTbase via header connectors
- Provide power to IoTbase via either connecting to USB slot of MCU or external supply
- Connect USB to the MCU (for flashing the firmware or using the IoTflow Forge Configuration Tool)
- Connect IoTbase and IoTextra module via HOST connector

## IoTsmart System-on-Module (SOM) Microcontrollers

Supported SOMs:

- IoTsmart ESP32-S3
- IoTsmart XIAO
- IoTsmart SAMD21
- IoTsmart RP2040

**Steps:**

1. **Normal Operation:** Insert the SOM into the **HOST connector slot** on the IoTbase.
2. **Firmware Flashing / Configuration:** Use the **IoTsmart adapter cable**.
3. **Power:** Connect USB to the IoTbase to supply power to the SOM and any attached modules.
4. **USB Connection (via adapter cable):** Required for flashing firmware, using the **IoTflow Forge Configuration Tool**, or serial debugging.

## IoTextra Mezzanine Modules

IoTextra modules (Analog, Combo, Digital, etc.) connect **directly to the HOST connector slot** on the IoTbase.

**Step:**

- Insert the IoTextra module into the HOST connector / header slot.  
  This provides power, I²C, and digital signals needed for the module to operate.

---

## Step 2: Flashing MicroPython Firmware (Example: PICO W)
1. Download the `firmware.uf2` file from MicroPython official website
Example: For PICO W - `https://micropython.org/download/RPI_PICO_W/`
2. Hold down BOOTSEL on the Pico W and connect it to your computer via micro-USB.
3. Release BOOTSEL – Pico will appear as a `RPI-RP2` drive.
4. Copy the `firmware.uf2` file to this drive.
5. Pico will reboot with the new firmware.

Above applies for RPI PICO W board but you can find detailed guides for other microcontrollers that support MicroPython via the offical `https://micropython.org` website.

---

## Step 3: Firmware Configuration (IoTflow Kernel)
1. **Connect your microcontroller** to your computer via USB.  
2. **Open an IDE of your choice** (e.g., Thonny, VS Code, or any IDE that supports MicroPython).  
3. **Select the interpreter** for your device:  
   - In your IDE, choose **MicroPython** and select your microcontroller.  
4. **Upload the main script**:  
   - Transfer `main.py` to the root directory of your microcontroller.  
5. **Upload supporting libraries**:  
   - Transfer all other `.py` files into a `lib` folder on the microcontroller.  
6. **Configure settings**:  
   - Open `config.py` on the microcontroller.  
   - Update it with your desired configuration (Wi-Fi credentials, device settings, etc.).  
   - Save the file (**Ctrl+S**).  
7. **Restart your device**:  
   - Reboot the microcontroller.  
   - It will automatically attempt to connect to the network using your configuration (Subject to providing correct credentials or details).

---

## Step 4: Utility Configuration I/O Tool (IoTflow Forge)
For more detailed information about IoTflow Forge please review [`IoTflow Forge/README.md`](../IoTflow%20Forge/README.md)

1. Connect your microcontroller to your computer.
2. Open `IoTflow Forge.py` and run the python program.
3. Make a new configuration or load a configuration.
4. Send your configuration to your microcontroller (via USB).
5. Await a few seconds for system response.
6. If configuration matches your desired setup you may disconnect 
from your computer and close the `IoTflow Forge.py` program.

---

## Step 5: Node-RED Installation
1. Install Node-RED (see the [official guide](https://nodered.org/docs/getting-started/)).
2. Install the dashboard:
   - Open Node-RED in your browser (`http://127.0.0.1:1880`)
   - Menu (top right) → Manage palette → Install
   - Search for `node-red-dashboard` and install
3. Install custom IoTextra nodes:
   - (Local installation example)
   - Go to your Node-RED user directory (e.g. `~/.node-red`)
   - Run:
     ```bash
     npm install /path/to/project/node-red-contrib-iotextra
     ```
   - Restart Node-RED

   - You should see two new custom nodes called "iotextra - input", "iotextra - analog", and "iotextra - output" in the "network" category (check the images -> iotextra-io-node-function-category.png)

---

## Step 6: Importing the Example Dashboard
1. Download the `node-red-examples` folder from the repository.
2. In Node-RED: Menu → Import → select the `[your_board_name]_flow.json` file → Import
3. Configure the MQTT broker address in the iotextra node if it differs from the default.
4. Click Deploy.
5. The dashboard will be available at: `http://<your-node-red-ip>:1880/ui`

---

## How to use iotextra custom Node-RED nodes
- **IoTextra Output for a selected channel:**
  - Accepts an incoming msg.payload in the format of either true/false or 1/0
  - This uses a broker to send the command to the mezzanine device
  - The firmware writes the state of the received message payload to the corresponding channel (pin AP0-AP7)
  - Mezzanine device publishes an outgoing message payload confirming that state has been received and acknowledged
  - IoTextra Output Node-RED node is subcribed to the confirmation message topic and provides an outgoing msg.payload with either '1' or '0'
- **IoTextra Input for a selected channel:**
  - If a change in the state of the input channel (pin AP0-AP7) is detected on the physical mezzanine device by the firmware - it publishes the observed state of the input channel (1 or 0)
  - IoTextra Input Node-RED node listens for changes on the channel and provides an outgoing msg.payload ('1' or '0') corresponding to the state of the input channel
  
---

## How MQTT Protocol is used to send/receive data from the IoTextra Modules 
- **Device status:**
  - `<MQTT_BASE_TOPIC>/status` – online/offline
- **Digital inputs:**
  - `<MQTT_BASE_TOPIC>/input/<channel>` – state of the input channel on the device 1 (ON) or 0 (OFF)
- **Digital outputs:**
  - `<MQTT_BASE_TOPIC>/output/<channel>/set` – used to toggle the state of the output channel on the device -> 1 (ON) or 0 (OFF)
  - `<MQTT_BASE_TOPIC>/output/<channel>/state` – used for confirming that the command has been received by the device and state has indeed changeed -> 1 (ON) or 0 (OFF)
- **Analog channels:**
  - `<MQTT_BASE_TOPIC>/analog/<channel>` – current reading of the analog channel, published as a string (e.g., "3.142")
  - Units are V (voltage) or mA (current), depending on channel configuration
  - Values are updated periodically or change if deadband filtering is enabled within the software (Commented by DEFAULT)

**Notes:**
- Digital input/output channels provide instantaneous state updates.  
- Ensure that `<MQTT_BASE_TOPIC>` matches your device configuration for correct topic mapping.

---

## Troubleshooting
- **No connection to MQTT broker:**
  - Check MQTT_BROKER address and Wi-Fi credentials in `config.py`
  - Make sure the MQTT broker is running and accessible on the network
