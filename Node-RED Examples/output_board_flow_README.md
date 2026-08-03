# IoTextra Output Board — Basic Digital Output Control

This flow demonstrates basic control of all 8 digital output channels of the IoTextra SSR Small, IoTextra MOSFET2, or IoTextra Relay module — mezzanine boards with 8 digital outputs (DO). Each channel is controlled by a dashboard toggle switch with a status LED confirming the actual output state.

Requires an IoTbase or IoTsmart carrier board with an IoTextra SSR Small, IoTextra MOSFET2, or IoTextra Relay mezzanine module connected via the HOST connector. Install `node-red-contrib-iotextra` before importing. Update the MQTT broker address to match your setup, then deploy and open the dashboard to start controlling your outputs.
