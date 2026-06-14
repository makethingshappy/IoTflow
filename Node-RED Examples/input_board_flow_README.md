# IoTextra Input Board — Basic Digital Input Monitoring

This flow demonstrates basic monitoring of all 8 digital input channels of the IoTextra Input module — a mezzanine board with 8 optically isolated digital inputs (DI). Each channel state is displayed as a live status LED on the Node-RED dashboard, turning green when the input is active and red when inactive.

Requires an IoTbase or IoTsmart carrier board with an IoTextra Input mezzanine module connected via the HOST connector. Install `node-red-contrib-iotextra` before importing. Update the MQTT broker address to match your setup, then deploy and open the dashboard to start monitoring your digital inputs.
