# IoTflow: Workflow Engine for MQTT & Node-RED Automation

## Overview

**IoTflow** is a lightweight workflow orchestration engine designed to unify automation across IoTextra modules and IoTsmart MCU nodes.  

It enables **no-code programming for distributed MCU nodes**, providing a consistent structure for MQTT-driven messaging and Node-RED workflow automation.

IoTflow is not firmware in itself; rather, it acts as a **workflow layer** that coordinates communication, event routing, and automation logic across supported devices.

---

## Supported IIoT Workflows

IoTflow is optimized for:

- MQTT-based event automation  
- Digital and analog I/O routing across IoTextra and IoTsmart devices  
- Input-to-event mappings for Node-RED  
- Multi-device orchestration workflows  
- Edge automation using Raspberry Pi, Linux gateways, ESP32-S3, and distributed MCU nodes  
- Clean, scalable, repeatable automation patterns  

These workflows allow developers to build stable automation systems without complex manual configuration.

---

## Node-RED Flow Structure

This repository includes pre-built Node-RED flow files located in:

```
/Node-RED Examples/
```

These flows demonstrate:

- MQTT topic parsing  
- Digital/analog input → event mapping  
- Output control logic  
- Multi-device routing patterns  
- Trigger → action automations  
- Reference flows for integrating IoTextra-Digital and IoTsmart nodes  

All flow files are import-ready for any Node-RED environment.

---

## MQTT Workflow Automation

IoTflow uses MQTT as its primary transport layer.

Core features include:

- Consistent and well-defined MQTT topic hierarchy  
- Event-driven reporting from distributed MCU nodes  
- Structured command channels for outputs  
- Scalable multi-module messaging patterns  
- Compatibility with Mosquitto, EMQX, Aedes, and similar brokers  

This repository does **not** include standalone MQTT client code, only the orchestration structure used to implement automation logic.

---

## Event-Driven Automation Examples

Reference examples are located in:

```
/Node-RED Examples/
```

Included examples show:

- State-change automation  
- Timed and conditional logic  
- Multi-module routing (IoTextra ↔ IoTsmart ↔ Node-RED)  
- Notification and action chains  

These are reference workflows intended for learning and rapid prototyping.

---

## Installation & Quick Start

For complete setup instructions, see:

📄 **[`SETUP.md`](./Documentation/SETUP.md)**

### Quick Start

1. Clone or download this repository.  
2. Upload IoTflow Kernel MicroPython files to your MCU (via Thonny or any IDE).  
3. Use **IoTflow Forge** to configure your I/O modules and workflow parameters.  
4. Ensure your MQTT Broker is active within the same network.  
5. Install Node-RED on your Raspberry Pi or gateway device.  
6. Import the desired flows from `/Node-RED Examples/`.  
7. Configure MQTT topics, device IDs, and automation logic in Node-RED.  
8. Deploy your flow to activate automation.

IoTflow is intentionally lightweight and adapts to any existing MQTT + Node-RED stack.

---

## Folder Structure

```
IoTflow/
 ├─ Documentation/
 ├─ IoTflow Forge/
 ├─ IoTflow Kernel/
 ├─ Media/
 ├─ Node-RED Examples/
 └─ node-red-contrib-iotextra/
```

### Directory Overview

- **[`Documentation`](./Documentation/)**  
  Architecture overview, setup guides, and workflow explanations.

- **[`IoTflow Forge`](./IoTflow%20Forge/)**  
  Configuration utility for defining MCU node behavior (experimental).

- **[`IoTflow Kernel`](./IoTflow%20Kernel/)**  
  Core MicroPython orchestration engine deployed on MCU nodes.

- **[`Node-RED Examples`](./Node-RED%20Examples/)**  
  Importable Node-RED flows demonstrating common patterns.

- **[`node-red-contrib-iotextra`](./node-red-contrib-iotextra/)**  
  Node-RED extension for IoTextra module interaction.

- **[`Media`](./Media/)**  
  Videos, images, and demo assets.

---

## Reference Materials

The following resources are available for developers:

### GPIO Examples  
Located inside the hardware repositories under their respective `/examples/` folders.

### Pinout Diagrams  
Available inside each IoTsmart module folder:
- `RP2040/v1.02/docs/`
- `RP2350A/v1.02/docs/`
- `ESP32-S3/v1.02/docs/`

### SKU & Ordering Files  
Available in the root of each hardware repository:
- **IoTsmart repository root:** SKU IoTsmart.pdf  
- **IoTextra-Digital repository root:** SKU Digital IoTextra.pdf

---

## Template Updates

Future updates may include:

- New workflow templates  
- Expanded MQTT routing schemes  
- Enhanced IoTextra module integrations  
- Secure MQTT authentication support  
- Additional examples for distributed automation  

All updates will maintain the unified documentation and versioning model defined across the project.

---

## Licensing

All code, documentation, images, and media in this repository are licensed under:

📄 **[`LICENSE`](./LICENSE)**

IoTflow is a software-only repository, hardware licenses do not apply here.

