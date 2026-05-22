# 🌐 IoTflow  
**A Simple, Scalable Automation Engine**

[Official Website ](https://makethingshappy.io/pages/iotflow)

## 🌱 Make Things Happy Platform Philosophy
Modern prototyping tools make it easy to build a demo but extremely hard to transition that prototype into a stable, maintainable industrial product. Teams often redesign hardware from the ground up after using Raspberry Pi, Arduino, or similar prototyping boards, a costly and time-consuming process that burdens long-term support.

The **Make Things Happy** platform eliminates this gap by standardizing I/O hardware through the IoTextra module family and providing two clear integration paths:

**IoTbase** for full-featured, serial-ready solutions using SoMs, and **IoTsmart** for compact wireless MCU nodes. All modules are Open Hardware, well-documented, and usable independently.

To unify these hardware options on the software side, we created **IoTflow**, a lightweight orchestration layer that defines message topology, automation behavior, and Node-RED communication patterns. IoTflow enables predictable, scalable automation across diverse modules without requiring custom firmware for each device.

## 🧩 What Is IoTflow?

**IoTflow** is a lightweight workflow orchestration system designed to unify automation across **IoTextra Digital, Analog and Combo I/O modules** and **IoTsmart or IoTbase MCU nodes**.

It enables **no-code programming for distributed MCU nodes**, providing a consistent structure for MQTT-based communication and Node-RED automation.

IoTflow is not firmware itself, it is an orchestration layer that defines:

- Message topology  
- Workflow behavior  
- Automation patterns  
- Topic conventions  
- Node-RED flow organization  

This ensures reliable, scalable, and easily maintainable automation across multiple IoTextra, IoTsmart and IoTbase devices.

---

## 🛠️ Supported Hardware

### Microcontrollers and System On Modules (SoM)

* [**IoTbase PICO**](https://makethingshappy.io/products/iotbase-pico) - Compatible with Raspberry Pi Pico, Pico 2, Pico W, Pico 2W, Waveshare ESP32-S3 PICO
* [**IoTbase NANO**](https://makethingshappy.io/products/iotbase-nano) - Arduino Nano ESP32 or ESP32-S3 or Waveshare ESP32-S3 Nano
* **IoTbase Feather** - Coming Soon
* [**IoTsmart ESP32-S3**](https://makethingshappy.io/products/iotsmart-esp32-s3) - Tiny Adaptor Board with Cable is required for flashing
* [**IoTsmart RP2040**](https://makethingshappy.io/products/iotsmart-rp2040) or [**IoTsmart RP2350A**](https://makethingshappy.io/products/iotsmart-rp2350) - Tiny Adaptor Board with Cable is required for flashing
* [**IoTsmart XIAO**](https://makethingshappy.io/products/iotsmart-xiao) - Supports multiple Seeed XIAO-compatible SoMs — Coming Soon

*IoTsmart modules are System-on-Module (SOM) microcontroller boards that provide the primary compute and control functionality for the system.
Each module integrates a complete MCU environment, and different form factors (soldered SoM, slot-based modules such as the IoTsmart XIAO, etc.) are treated as implementation variations rather than separate device classes.*

<!-- CARRIER_COMPATIBILITY_START -->
<!-- CARRIER_COMPATIBILITY_END -->

### Supported IoTextra Board Categories

**Digital I/O Boards**
* [**IoTextra Input**](https://makethingshappy.io/products/iotextra-input)
* [**IoTextra Relay2**](https://makethingshappy.io/products/iotextra-relay2)
* [**IoTextra SSR Small**](https://makethingshappy.io/products/iotextra-ssr-small)
* [**IoTextra MOSFET2**](https://makethingshappy.io/products/iotextra-mosfet2)
* **IoTextra Quadro** — Planned
* [**IoTextra Octal**](https://makethingshappy.io/products/iotextra-octal)
* [**IoTextra Octal2**](https://makethingshappy.io/products/iotextra-octal2)
* **IoTextra Octal3** — Planned
* Custom digital mezzanines

**Analog I/O Boards**
* [**IoTextra Analog**](https://makethingshappy.io/products/iotextra-analog)
* **IoTextra Analog2** — Coming Soon
* **IoTextra Analog3** — Coming Soon
* Custom analog mezzanines

**Combo I/O Boards**

* [**IoTextra Combo**](https://makethingshappy.io/products/iotextra-combo)
* **IoTextra Combo2** — Coming Soon
* Custom combo mezzanines

<!-- IOTEXTRA_NODERED_COMPATIBILITY_START -->
<!-- IOTEXTRA_NODERED_COMPATIBILITY_END -->

<!-- IOTEXTRA_TASMOTA_COMPATIBILITY_START -->
<!-- IOTEXTRA_TASMOTA_COMPATIBILITY_END -->

---

## 🚀 Supported IIoT Workflows

IoTflow is optimized for:

- MQTT-driven event automation  
- Multi-module digital, analog and combo I/O routing  
- Structured topic hierarchies for distributed MCU nodes  
- Node-RED automation flows (import-ready)  
- State-change event pipelines  
- Raspberry Pi, Linux gateways, and ESP32-S3 edge automation  
- Consistent MCU-to-gateway communication patterns  

These workflows allow developers to build stable systems without custom firmware logic for each device.

---

## 🧱 Node-RED Flow & Event-Driven Automation Structure

IoTflow provides import-ready Node-RED flows demonstrating how to implement reliable, event-driven automation across IoTextra and IoTsmart modules:

### The flows demonstrate:

- State-change detection and conditional logic
- Input → event → output control logic and mapping  
- MQTT communication handling and topic parsing
- Multi-device orchestration and routing patterns  
- Timed action automations, triggers, notifications and actuator chains
- Integration of IoTextra Digital, Analog and Combo modules with IoTsmart and IoTbase MCU nodes

### Event-Driven Automation Examples

Examples are stored inside the repository:
