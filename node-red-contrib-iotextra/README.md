# ⚡ node-red-contrib-iotextra

Connect Node-RED to **IoTextra** mezzanine modules—stackable I/O boards for digital relays, GPIO inputs, and analog measurements. This package adds three custom nodes that speak MQTT to your IoTextra hardware, so you can build dashboards, automations, and integrations without writing firmware.

IoTextra modules run on the [IoTflow](https://github.com/makethingshappy/IoTflow) framework (MicroPython firmware on an IoTsmart or IoTbase with compatible SoM). Once your device is on the network and publishing to an MQTT broker, these nodes let you read inputs, drive outputs, and stream analog values directly in your flows.

## Included nodes

All three nodes appear in the **network** category in the Node-RED editor. Each node is configured with an MQTT broker, a base topic (matching your device's `MQTT_BASE_TOPIC`), and a channel number.

### iotextra-input — digital input

Subscribes to digital input changes on a selected channel (pins AP0–AP7 on the module). When the firmware detects a state change on the physical input, it publishes `1` (ON) or `0` (OFF). This node forwards that value as `msg.payload` (`'1'` or `'0'`).

### iotextra-output — digital output

Sends ON/OFF commands to a digital output channel. Accepts `msg.payload` as `true`/`false` or `1`/`0`, publishes the command over MQTT, and emits a confirmation when the device acknowledges the new state (`'1'` or `'0'` on the state topic).

### iotextra-analog — analog input

Subscribes to analog readings from single-ended to differential ADC channels (e.g. A0–A1, A2–A3 on Analog and Combo modules). The firmware publishes converted voltage or current as a numeric string (e.g. `"3.124"`). Each message becomes `msg.payload` for use in gauges, charts, or logic nodes.

> **Tip:** For full wiring, firmware, and broker setup, see the [setup guide](https://github.com/makethingshappy/IoTflow/blob/main/Documentation/SETUP.md) in the IoTflow repository.

## Compatible hardware

These nodes work with IoTextra mezzanine modules connected via the IoTbase or IoTsmart HOST connector and running IoTflow:

| Family | Description |
|--------|-------------|
| [Digital IoTextra](https://makethingshappy.io/collections/digital-iotextra) | Digital inputs and outputs |
| [Analog IoTextra](https://makethingshappy.io/collections/analog-iotextra) | Differential or Single-ended ADC channels (voltage/current) |
| [Combo IoTextra](https://makethingshappy.io/collections/combo-iotextra) | Digital and analog I/O on one module |

You will also need an IoTbase with compatible SoM or IoTsmart module, and MQTT broker access on your network.

## Installation

### Via Node-RED Manage Palette

1. Open Node-RED (`http://127.0.0.1:1880` or your instance URL).
2. Menu → **Manage palette** → **Install** tab.
3. Search for `node-red-contrib-iotextra` and install.
4. Restart Node-RED if prompted.

### Via npm

From your Node-RED user directory (often `~/.node-red`):

```bash
npm install node-red-contrib-iotextra
```

Restart Node-RED after installation.

## MQTT topics reference

Topics use `<MQTT_BASE_TOPIC>` as the root (configured on your device, e.g. `home/iotextra`).

| Category | MQTT topic | Description | Values |
|----------|------------|-------------|--------|
| Device status | `<MQTT_BASE_TOPIC>/status` | Device online/offline | `online` / `offline` |
| Digital input | `<MQTT_BASE_TOPIC>/input/<channel>` | Input channel state | `1` (ON) / `0` (OFF) |
| Digital output (command) | `<MQTT_BASE_TOPIC>/output/<channel>/set` | Set output state | `1` (ON) / `0` (OFF) |
| Digital output (confirm) | `<MQTT_BASE_TOPIC>/output/<channel>/state` | Confirmed output state | `1` (ON) / `0` (OFF) |
| Analog channel | `<MQTT_BASE_TOPIC>/analog/<channel>` | ADC reading | Numeric string (e.g. `"3.142"`) — unit is **V** or **mA** per channel config |

Ensure the **base topic** in each node matches your device configuration.

## Links

- [Full setup guide](https://github.com/makethingshappy/IoTflow/blob/main/Documentation/SETUP.md) — hardware, firmware, Forge config, and Node-RED
- [Node-RED flow examples](https://github.com/makethingshappy/IoTflow/tree/main/Node-RED%20Examples) — importable flows for Relay, Input, Analog, Combo, Octal, MOSFET and Quadro boards
- [Make Things Happy](https://makethingshappy.io) — IoTextra products and documentation
- [GitHub — IoTflow](https://github.com/makethingshappy/IoTflow) — source repository

## Full compatibility table

The following table shows all IoTextra modules and their Node-RED flow availability:

<!-- IOTEXTRA_NODERED_COMPATIBILITY_START -->
# IoTextra Node-RED Compatibility

| IoTextra Module | Node-RED | Blynk |
|---|:---:|:---:|
| Input | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/input_board_flow.json) | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/input_board_flow_with_blynk.json) |
| Relay2 | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/relay2_board_flow.json) | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/relay2_board_flow_with_blynk.json) |
| SSR Small | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/output_board_flow.json) | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/output_board_flow_with_blynk.json) |
| MOSFET2 | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/output_board_flow.json) | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/output_board_flow_with_blynk.json) |
| Quadro | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/quadro_board_flow_with_blynk.json) | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/quadro_board_flow.json) |
| Octal | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/octal_board_flow.json) | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/octal_board_flow_with_blynk.json) |
| Octal2 | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/octal_board_flow.json) | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/octal_board_flow_with_blynk.json) |
| Octal3 | 🔲 | 🔲 |
| Analog | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/analog_board_flow.json) | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/analog_board_flow_with_blynk.json) |
| Analog2 | 🔲 | 🔲 |
| Analog3 | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/analog_3_board_flow.json) | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/analog_3_board_flow_with_blynk.json) |
| Combo | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/combo_board_flow.json) | [![Example](https://img.shields.io/badge/Example-yellowgreen)](https://github.com/makethingshappy/IoTflow/blob/main/Node-RED%20Examples/combo_board_flow_with_blynk.json) |
| Combo2 | 🔲 | 🔲 |

**Legend:**
- [![Example](https://img.shields.io/badge/Example-yellowgreen)]() — available, click to open
- 🔶 — Coming Soon
- 🔲 — Planned

<!-- IOTEXTRA_NODERED_COMPATIBILITY_END -->

## License

MIT — see [LICENSE](https://github.com/makethingshappy/IoTflow/blob/main/LICENSE).
