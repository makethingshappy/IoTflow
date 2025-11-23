# IoTflow: Workflow Engine for MQTT & Node-RED Automation

## Overview

IoTflow is a lightweight orchestration layer designed to unify automation workflows across the IoTextra modules and IoTsmart MCU boards.

It provides structured Node-RED flow patterns, MQTT-friendly workflow organization, and a consistent method for synchronizing digital or analog I/O, and automation logic across multiple devices.

IoTflow is a **workflow framework** used to coordinate existing MQTT and Node-RED environments.

---

## Supported IIoT Workflows

IoTflow is optimized for:

- MQTT-based event automation  
- Digital and Analog I/O routing across IoTextra and IoTsmart devices  
- Input-to-event mappings for Node-RED  
- Multi-device orchestration workflows  
- Edge automation using Raspberry Pi, Linux gateways, and etc.
- Clean, scalable, repeatable automation patterns  

These workflows enable developers to assemble industrial or home-automation logic without complex manual configuration.

---

## Node-RED Flow Structure

This repository includes pre-built Node-RED flow files in the `/Node-RED Examples/` directory.

These flows demonstrate:

- MQTT topic processing  
- Digital / Analog input → event mapping  
- Digital output control logic  
- Routing between multiple devices  
- Trigger → action automations  
- Best-practice patterns for IoTextra + IoTsmart integration  

The flow files are ready to import directly into any Node-RED environment.

---

## MQTT Workflow Automation

IoTflow uses MQTT as its core messaging mechanism.

Features include:

- Clear and consistent topic naming  
- Event-driven digital input reporting  
- Structured command channels for outputs  
- Scalable multi-module workflows  
- Compatibility with Mosquitto, EMQX, Aedes, and other brokers  

This repository does **not** include MQTT client code, only the workflow structure used to organize automation logic.

---

## Event-Driven Automation Examples

Reference examples are located in:

```
/Node-RED Examples/
```

Included examples show:

- State-change automations  
- Timed and conditional logic  
- Multi-module IoTextra/IoTsmart routing  
- Notification and action chains  

These examples are **reference workflows**, not production applications.

---

## Installation & Quick Start

For detailed installation & setup guides please review [`SETUP.md`](./Documentation/SETUP.md)

1. Clone or download this repository.
2. Upload IoTflow Kernel MicroPython files to your MCU using Thonny IDE or other IDE's.
3. Use IoTflow Forge to configure your desired configuration for your setup.
4. Ensure your MQTT Broker is active and running within the same network.
5. Install Node-RED on your Raspberry Pi, Linux host, or IoT gateway.  
6. Open Node-RED → **Import** → Select a file from `/Node-RED Examples/`.  
7. Configure your setup details and MQTT broker settings inside Node-RED.  
8. Deploy the flow to begin automation.

IoTflow is intentionally lightweight and adapts to any existing MQTT + Node-RED stack.

---

## Folder Structure & Versioning

```
IoTflow/
 ├─ Documentation/
 ├─ IoTflow Forge/
 ├─ IoTflow Kernel/
 ├─ Media/
 ├─ Node-RED Examples/
 └─ node-red-contrib-iotextra/
```

- **Documentation/** — Workflow descriptions, system architecture and setup guides
- **IoTflow Kernel/** — Core orchestration structure (Main firmware)
- **IoTflow Forge/** — Configuration Utility Tool for I/O Modules (Experimental with upcoming assets)
- **Media/** — Video Demonstrations and Images
- **Node-RED Examples/** — Importable flow files for demonstration purposes
- **node-red-contrib-iotextra/** — Node-RED extension for IoTextra modules 

---

## Template Updates

Future updates may include:

- New workflow patterns  
- Expanded MQTT routing schemes  
- Additional IoTextra module integrations  
- Developer-friendly automation blocks
- Secure Authentication for MQTT Communication

All updates will maintain the structure required by the unified documentation and licensing rules.

---

## Licensing

This repository's code, documentation, media and all other content is licensed under [`LICENSE`](./LICENSE).

IoTflow is a software-only repository; hardware licenses do not apply here.
