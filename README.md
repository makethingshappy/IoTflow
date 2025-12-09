# 🔄 IoTflow  
Workflow Engine for MQTT & Node-RED Automation

# 🌱 Make Things Happy Platform Philosophy
Modern prototyping tools make it easy to build a demo but extremely hard to transition that prototype into a stable, maintainable industrial product. Teams often redesign hardware from the ground up after using Raspberry Pi, Arduino, or similar prototyping boards, a costly and time-consuming process that burdens long-term support.

The **Make Things Happy** platform eliminates this gap by standardizing I/O hardware through the IoTextra module family and providing two clear integration paths:

**IoTbase** for full-featured, serial-ready solutions using SoMs, and **IoTsmart** for compact wireless MCU nodes. All modules are Open Hardware, well-documented, and usable independently.

To unify these hardware options on the software side, we created **IoTflow**, a lightweight orchestration layer that defines message topology, automation behavior, and Node-RED communication patterns. IoTflow enables predictable, scalable automation across diverse modules without requiring custom firmware for each device.

## 🧩 What Is IoTflow?

**IoTflow** is a lightweight workflow orchestration system designed to unify automation across **IoTextra-Digital I/O modules** and **IoTsmart MCU nodes**.

It enables **no-code programming for distributed MCU nodes**, providing a consistent structure for MQTT-based communication and Node-RED automation.

IoTflow is not firmware itself, it is an orchestration layer that defines:

- Message topology  
- Workflow behavior  
- Automation patterns  
- Topic conventions  
- Node-RED flow organization  

This ensures reliable, scalable, and easily maintainable automation across multiple IoTextra and IoTsmart devices.

---

## 🚀 Supported IIoT Workflows

IoTflow is optimized for:

- MQTT-driven event automation  
- Multi-module digital/analog I/O routing  
- Structured topic hierarchies for distributed MCU nodes  
- Node-RED automation flows (import-ready)  
- State-change event pipelines  
- Raspberry Pi, Linux gateways, and ESP32-S3 edge automation  
- Consistent MCU-to-gateway communication patterns  

These workflows allow developers to build stable systems without custom firmware logic for each device.

---

## 🧱 Node-RED Flow Structure

Import-ready Node-RED flows are provided inside:

```
/Node-RED Examples/
```

These example flows demonstrate:

- MQTT topic parsing  
- Input → event mapping  
- Output control logic  
- Multi-device routing patterns  
- Trigger → action automations  
- Integration of IoTextra-Digital modules with IoTsmart MCUs  

All flows are compatible with any Node-RED environment.

---

## 🔗 MQTT Workflow Automation

MQTT is the core transport layer used by IoTflow.

### Features include:
- Well-defined, hierarchical MQTT topics  
- Event-driven reporting from IoTsmart nodes  
- Structured commands for digital outputs  
- Consistent multi-module routing  
- Compatibility with Mosquitto, EMQX, Aedes, and similar brokers  

This repository does **not** provide standalone MQTT client code — only the **automation structure** used to implement workflows.

---

## ⚡ Event-Driven Automation Examples

Examples are stored inside the repository:

```
/Node-RED Examples/
```

They include:

- State-change detection  
- Conditional logic  
- Multi-module orchestration  
- Timed actions and triggers  
- Notification + actuator chains  

These examples are ideal for learning and rapid prototyping.

---

## 📥 Installation & Quick Start

See full setup instructions in:

📄 **[`SETUP.md`](./Documentation/SETUP.md)**

### Quick Start

1. Clone or download this repository.  
2. Upload IoTflow Kernel MicroPython files to your MCU (via Thonny or any IDE).  
3. Use **IoTflow Forge** to configure workflow parameters and module definitions.  
4. Ensure an MQTT broker is active on your network.  
5. Install Node-RED on your gateway (Raspberry Pi or Linux host).  
6. Import flows from `/Node-RED Examples/`.  
7. Configure MQTT topics, device IDs, and automation logic.  
8. Deploy to activate automation.

IoTflow is intentionally lightweight and compatible with any MQTT + Node-RED stack.

---

## 📁 Folder Structure

```
IoTflow/
 ├─ Documentation/
 ├─ IoTflow Forge/
 ├─ IoTflow Kernel/
 ├─ Node-RED Examples/
 ├─ node-red-contrib-iotextra/
 └─ Media/
```

### Directory Overview

- **[`Documentation`](./Documentation/)** — Architecture notes, guides, and workflow documentation  
- **[`IoTflow Forge`](./IoTflow%20Forge/)** — Configuration generator for MCU nodes  
- **[`IoTflow Kernel`](./IoTflow%20Kernel/)** — Core MicroPython workflow engine  
- **[`Node-RED Examples`](./Node-RED%20Examples/)** — Node-RED automation flows  
- **[`node-red-contrib-iotextra`](./node-red-contrib-iotextra/)** — Node-RED IoTextra integration nodes  
- **[`Media`](./Media/)** — Images and example materials  

---

## 🔗 Reference Materials

### GPIO Examples for Device Integration

GPIO reference examples for IoTextra and IoTsmart will be added in future updates by the development team.  
These examples are not yet part of the hardware repositories.

### Pinout Diagrams (MCU Hosts)

Available inside each IoTsmart module folder:

- `RP2040/docs/`  
- `RP2350A/docs/`  
- `ESP32-S3/docs/`  

### SKU & Ordering Files

- **IoTextra-Digital:** `SKU Digital IoTextra.pdf`  
- **IoTsmart:** `SKU IoTsmart.pdf`  

(Located in each repository root.)

---

## 🔄 Planned Updates

Future additions may include:

- Extended automation templates  
- Expanded MQTT topic models  
- Enhanced IoTextra module integration  
- Secure MQTT authentication options  
- Additional distributed workflow examples  

All updates will follow the unified documentation and versioning model.

---

## 📜 Licensing

All IoTflow code, documentation, and media are licensed under:

📄 **[`LICENSE`](./LICENSE)**

Hardware licenses do not apply — this is a software-only repository.
