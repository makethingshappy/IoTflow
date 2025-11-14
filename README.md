# IoTflow  
Unified Software I/O Platform for the IoT & IIoT Ecosystem

IoTflow is a comprehensive software platform designed to provide a unified framework for managing Input/Output (I/O) modules within the Internet of Things (IoT) and Industrial Internet of Things (IIoT) ecosystem. While optimized for the architecture of our module series, its components can be adapted for use with a wide range of hardware solutions.

## Supported Hardware Series
- **IoTextra** – unified I/O modules  
- **IoTbase** – carrier modules with a SOM slot  
- **IoTsmart** – auxiliary modules with non-volatile memory

## Platform Components

### 1. IoTflow Kernel
The firmware running on the MCU, responsible for:
- Managing all hardware I/O  
- Communicating via the MQTT protocol  
- Acting as a robust, standalone IoT/IIoT node  
- Integrating with Node-RED  
- Providing compatibility with platforms such as Blynk

### 2. IoTflow Forge
A PC-based configuration application offering:
- A user-friendly interface for defining and editing I/O configurations  
- Writing configurations to the EEPROM on IoTsmart or IoTbase modules  
- Streamlined setup and customization workflows

## Overview
IoTflow delivers a fast, flexible, and standardized method for deploying IoT solutions by combining modular hardware with a unified software environment. It simplifies system design, accelerates development, and ensures consistent behavior across devices.
