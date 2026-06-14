# IoTextra Analog Board — Basic Analog Input Monitoring

This flow demonstrates basic reading of analog input channels from the IoTextra Analog module — a mezzanine board with 4 analog input channels based on the ADS1115 ADC. Each channel delivers processed voltage or current measurement values via MQTT, displayed in the Node-RED debug sidebar for easy verification and inspection before building further automation logic.

Requires an IoTbase or IoTsmart carrier board with an IoTextra Analog mezzanine module connected via the HOST connector. Install `node-red-contrib-iotextra` before importing. Update the MQTT broker address to match your setup, then deploy and open the debug panel to start receiving measurements.
