# IoTextra Octal3 Board — Basic Control & Monitoring

This flow demonstrates basic control and monitoring of the IoTextra Octal3 module — a hybrid mezzanine board combining 4 latching relay outputs and 4 digital inputs (DI). Each relay is controlled by a dashboard toggle switch with a status LED reflecting the stored relay state. Each DI channel is displayed as a live status LED on the Node-RED dashboard. Note: IoTextra Octal and Octal2 (standard digital outputs) use `octal_board_flow.json` instead; they are not supported by this flow.

Requires an IoTbase or IoTsmart carrier board with an IoTextra Octal3 mezzanine module connected via the HOST connector. Install `node-red-contrib-iotextra` before importing. Update the MQTT broker address to match your setup, then deploy and open the dashboard to start controlling relays and monitoring inputs.
