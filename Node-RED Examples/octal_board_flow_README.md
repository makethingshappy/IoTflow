# IoTextra Octal Board — Basic Control & Monitoring

This flow demonstrates basic control and monitoring of the IoTextra Octal series modules (IoTextra Octal, Octal2, and upcoming Octal4) — mezzanine boards combining 4 digital inputs (DI) and 4 digital outputs (DO). Note: IoTextra Octal3 (latching relay outputs) is not supported by this flow. Each DI channel is displayed as a live status LED on the Node-RED dashboard. Each DO channel is controlled by a dashboard toggle switch with visual feedback confirming the actual output state.

Requires an IoTbase or IoTsmart carrier board with an IoTextra Octal series module connected via the HOST connector. Install `node-red-contrib-iotextra` before importing. Update the MQTT broker address to match your setup, then deploy and open the dashboard to start controlling and monitoring your device.
