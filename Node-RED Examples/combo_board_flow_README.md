# IoTextra Combo Board — Basic Control & Monitoring

This flow demonstrates basic control and monitoring of the IoTextra Combo module — a mezzanine board combining 2 SPDT relays and 2 analog input channels based on the ADS1115 ADC. Each relay is controlled by a dashboard toggle switch with a status LED confirming the actual relay state. Each analog input channel delivers processed voltage or current measurement values via MQTT, displayed in the Node-RED debug sidebar.

Requires an IoTbase or IoTsmart carrier board with an IoTextra Combo mezzanine module connected via the HOST connector. Install `node-red-contrib-iotextra` before importing. Update the MQTT broker address to match your setup, then deploy and open the dashboard to start controlling relays and monitoring analog inputs.
