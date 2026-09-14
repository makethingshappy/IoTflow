# IoTextra Quadro Board — Basic Control & Monitoring

This flow demonstrates basic control and monitoring of the IoTextra Quadro module — a mezzanine board combining ISO1211 isolated digital inputs (DI) and relay outputs. Each relay is controlled by a dashboard toggle switch with a status LED confirming the actual output state. Each DI channel is displayed as a live status LED on the Node-RED dashboard.

Requires an IoTbase or IoTsmart carrier board with an IoTextra Quadro mezzanine module connected via the HOST connector. Install `node-red-contrib-iotextra` before importing. Update the MQTT broker address to match your setup, then deploy and open the dashboard to start controlling relays and monitoring inputs.
