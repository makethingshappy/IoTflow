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
- Edge automation using Raspberry Pi, Linux gateways, and ESP32-S3 boards  
- Clean, scalable, repeatable automation patterns  

These workflows enable developers to assemble industrial or home-automation logic without complex manual configuration.

---

## Node-RED Flow Structure

This repository includes pre-built Node-RED flow files in the `/Node-RED Examples/` directory.

These flows demonstrate:

- MQTT topic processing  
- Digital input → event mapping  
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

1. Install Node-RED on your Raspberry Pi, Linux host, or IoT gateway.  
2. Clone or download this repository.  
3. Open Node-RED → **Import** → Select a file from `/Node-RED Examples/`.  
4. Configure your MQTT broker details inside Node-RED.  
5. Deploy the flow to begin automation.

IoTflow is intentionally lightweight and adapts to any existing MQTT + Node-RED stack.

---

## Folder Structure & Versioning

```
IoTflow/
 ├─ Documentation/
 ├─ IoTflow Forge/
 ├─ IoTflow Kernel/
 ├─ Node-RED Examples/
 └─ node-red-contrib-iotextra/
```

- **Documentation/** — Workflow descriptions, system architecture and setup guides
- **IoTflow Kernel/** — Core orchestration structure (Main firmware)
- **Node-RED Examples/** — Importable flow files for demonstration purposes
- **node-red-contrib-iotextra/** — Node-RED extension for IoTextra modules 
- **IoTflow Forge/** — Configuration Utility Tool for I/O Modules (Experimental with upcoming assets)

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

This repository uses separate licenses for code, documentation, and media.

- **Code:** [`LICENSE_CODE.md`](./LICENSE_CODE.md)  
- **Documentation:** [`LICENSE_DOCS.md`](./LICENSE_DOCS.md)  
- **Media:** [`LICENSE_MEDIA.md`](./LICENSE_MEDIA.md)  

IoTflow is a software-only repository; hardware licenses do not apply here.

---
