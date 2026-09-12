# IoTextra Octal4 Board — Basic Control & Monitoring

This flow demonstrates basic control and monitoring of the IoTextra Octal4 module — a mezzanine board combining 4 ISO1211 isolated digital inputs (DI) and 4 SPST relay outputs. Each relay is controlled by a dashboard toggle switch with a status LED confirming the actual output state. Each DI channel is displayed as a live status LED on the Node-RED dashboard. Note: IoTextra Octal and Octal2 use `octal_board_flow.json`; IoTextra Octal3 (latching relays) uses `octal3_board_flow.json`.

Requires an IoTbase or IoTsmart carrier board with an IoTextra Octal4 mezzanine module connected via the HOST connector. Install `node-red-contrib-iotextra` before importing. Update the MQTT broker address to match your setup, then deploy and open the dashboard to start controlling relays and monitoring inputs.
