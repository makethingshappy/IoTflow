import time
import machine
import sys
import os
import uselect
import ujson
import struct
import config
from iot_driver import IotDriver
from mqtt_manager import MqttManager
from EEPROM_driver import EEPROM
from config_serializer import pack_config, unpack_config
from analog_driver import AnalogDriver

# Constants for EEPROM
EEPROM_ADDR = config.EEPROM_I2C_ADDR  # 0x57
EEPROM_SIZE = config.EEPROM_SIZE      # 1024
DEBUG = False  # Disable debug prints to reduce serial noise

os.dupterm(None, 0)

# Serial communication markers
START_MARKER = "<START>"
END_MARKER = "<END>"

driver = None
analog_driver = None
mqtt = None
eeprom = None
last_input_state = -1
last_analog_values = {}  # Track last published analog values for deadband filtering
buffer = ''
config_dict = {
    'WIFI_SSID': config.WIFI_SSID,
    'WIFI_PASSWORD': config.WIFI_PASSWORD,
    'MQTT_BROKER': config.MQTT_BROKER,
    'MQTT_PORT': config.MQTT_PORT,
    'MQTT_CLIENT_ID': config.MQTT_CLIENT_ID,
    'MQTT_BASE_TOPIC': config.MQTT_BASE_TOPIC,
    'HARDWARE_MODE': config.HARDWARE_MODE,
    'I2C_BUS_ID': config.I2C_BUS_ID,
    'I2C_SDA_PIN': config.I2C_SDA_PIN,
    'I2C_SCL_PIN': config.I2C_SCL_PIN,
    'I2C_DEVICE_ADDR': config.I2C_DEVICE_ADDR,
    'GPIO_HOST_PINS': config.GPIO_HOST_PINS,
    'PIN_CONFIG': config.PIN_CONFIG,
    'STATUS_UPDATE_INTERVAL_S': config.STATUS_UPDATE_INTERVAL_S,
    'ADC_I2C_ADDRS': [hex(addr) for addr in config.ADC_I2C_ADDRS],
    'ADC_SAMPLING_RATE': config.ADC_SAMPLING_RATE,
    'CHANNELS': config.CHANNELS,
}

def send_data_back(data):
    """Send JSON data back over serial with markers."""
    try:
        json_str = ujson.dumps(data)
        sys.stdout.write(f"{START_MARKER}{json_str}{END_MARKER}\n")
#         sys.stdout.flush()
    except Exception as e:
        if DEBUG:
            print("Error serializing/sending data:", e)

def update_config(new_config):
    """Update config_dict and reinitialize driver/mqtt."""
    global driver, mqtt, config_dict, analog_driver
    try:
        # Build hardware dict for AnalogDriver
        hardware_config = {
            'adc_i2c_addrs': new_config['hardware'].get('adc_i2c_addrs', []),
            'adc_sampling_rate': new_config['hardware'].get('adc_sampling_rate', 128),
        }
        
        # Update config_dict       
        config_dict.update({
            'WIFI_SSID': new_config['network']['wifi_ssid'],
            'WIFI_PASSWORD': new_config['network']['wifi_password'],
            'MQTT_BROKER': new_config['mqtt']['broker'],
            'MQTT_PORT': new_config['mqtt']['port'],
            'MQTT_CLIENT_ID': new_config['mqtt']['client_id'],
            'MQTT_BASE_TOPIC': new_config['mqtt']['base_topic'],
            'HARDWARE_MODE': new_config['hardware']['mode'],
            'I2C_BUS_ID': new_config['hardware']['i2c_bus_id'],
            'I2C_SDA_PIN': new_config['hardware']['i2c_sda_pin'],
            'I2C_SCL_PIN': new_config['hardware']['i2c_scl_pin'],
            'I2C_DEVICE_ADDR': int(new_config['hardware']['i2c_device_addr'], 16),
            'GPIO_HOST_PINS': new_config['hardware']['gpio_host_pins'],
            'PIN_CONFIG': int(new_config['pin_config'], 2),
            'STATUS_UPDATE_INTERVAL_S': new_config['status_update_interval_s'],
            'ADC_I2C_ADDRS': new_config['hardware'].get('adc_i2c_addrs', []),
            'ADC_SAMPLING_RATE': new_config['hardware'].get('adc_sampling_rate', 128),
            'CHANNELS': new_config.get('channels', []),
            'HARDWARE': hardware_config,
        })


        # Reinitialize I2C
        i2c = machine.I2C(
            config_dict['I2C_BUS_ID'],
            scl=machine.Pin(config_dict['I2C_SCL_PIN']),
            sda=machine.Pin(config_dict['I2C_SDA_PIN']),
            freq=400000
        )
        
        # Reinitialize IotDriver
        driver = IotDriver(
            config_dict['I2C_BUS_ID'],
            config_dict['I2C_SDA_PIN'],
            config_dict['I2C_SCL_PIN'],
            config_dict['I2C_DEVICE_ADDR'],
            config_dict['GPIO_HOST_PINS'],
            config_dict['PIN_CONFIG'],
            config_dict['HARDWARE_MODE']
        )
        
        # Build config for AnalogDriver with required fields
        analog_config = {
            'channels': config_dict.get('CHANNELS', []),
            'hardware': {
                'adc_i2c_addrs': config_dict.get('ADC_I2C_ADDRS', []),
                'adc_sampling_rate': config_dict.get('ADC_SAMPLING_RATE', 128),
            }
        }
        
        # Reinitialize AnalogDriver
        analog_driver = AnalogDriver(i2c, analog_config)
        

        # Reinitialize MqttManager
        if mqtt:
            mqtt.client.disconnect()
        mqtt = MqttManager(
            config_dict['MQTT_CLIENT_ID'],
            config_dict['MQTT_BROKER'],
            config_dict['MQTT_PORT'],
            command_callback=handle_mqtt_command
        )
        if MqttManager.is_wifi_connected() and mqtt.connect():
            command_topic = f"{config_dict['MQTT_BASE_TOPIC']}/output/+/set"
            mqtt.subscribe(command_topic)
            mqtt.publish(f"{config_dict['MQTT_BASE_TOPIC']}/status", "online", retain=True)
        if DEBUG:
            print("Configuration updated and driver/mqtt reinitialized")
    except Exception as e:
        if DEBUG:
            print("Error updating configuration:", e)

def handle_mqtt_command(topic, msg):
    """Callback function to process incoming MQTT commands."""
    try:
        topic_str = topic.decode('utf-8') if isinstance(topic, bytes) else topic
        msg_str = msg.decode('utf-8') if isinstance(msg, bytes) else msg
        parts = topic_str.split('/')
        if len(parts) >= 3 and parts[-1] == "set" and parts[-3] == "output":
            channel_str = parts[-2]
            channel = int(channel_str)
            state = bool(int(msg_str))
            if DEBUG:
                print(f"Received MQTT command for channel {channel}: {state}")
            if driver:
                driver.set_output(channel, state)
            if mqtt:
                state_topic = f"{config_dict['MQTT_BASE_TOPIC']}/output/{channel}/state"
                mqtt.publish(state_topic, str(int(state)), retain=True)
    except (ValueError, IndexError, UnicodeError) as e:
        if DEBUG:
            print(f"Error parsing MQTT command: {e}")

def check_and_publish_inputs():
    """Reads input states and publishes them if they have changed."""
    global last_input_state
    if not driver:
        return
    current_inputs = driver.read_all_inputs()
    if current_inputs is None:
        return
    if current_inputs != last_input_state:
        if DEBUG:
            print("Input state changed, publishing updates")
        for i in range(len(current_inputs)):
            if current_inputs[i] is None:
                continue
            channel = i + 1
            state = current_inputs[i]
            topic = f"{config_dict['MQTT_BASE_TOPIC']}/input/{channel}"
            if mqtt:
                mqtt.publish(topic, str(int(state)), retain=True)
        last_input_state = current_inputs
        
def check_and_publish_analog():
    """Reads analog channels and publishes their values."""
    if not analog_driver or not mqtt:
        return
    try:
        results = analog_driver.read_all_analog_channels()
        if results:
            for channel, value in results.items():
                if value is not None:
                    # Get channel config to determine if it's voltage or current
                    channel_configs = analog_driver.channel_configs
                    if channel in channel_configs:
                        ch_config = channel_configs[channel]
                        # Try to get measurement_range, fallback to type if missing
                        if 'measurement_range' in ch_config:
                            range_code = int(ch_config['measurement_range'], 2)
                            config = analog_driver.range_configs.get(range_code)
                        else:
                            config = None
                        
                        # Determine unit based on type or config
                        if config and config['type'] == 'voltage':
                            unit = "V"
                        elif ch_config.get('type') == 'voltage':
                            unit = "V"
                        else:
                            unit = "mA"
                        
                        value_str = f"{value:.3f}"
                        if DEBUG:
                            print(f"Analog channel {channel}: {value_str}{unit}")
                        topic = f"{config_dict['MQTT_BASE_TOPIC']}/analog/{channel}"
                        mqtt.publish(topic, value_str, retain=True)
    except Exception as e:
        if DEBUG:
            print(f"Error reading/publishing analog values: {e}")

# def check_and_publish_analog():
#     """Reads analog channels and publishes their values only when they change."""
#     global last_analog_values
#     if not analog_driver or not mqtt:
#         return
#     try:
#         results = analog_driver.read_all_analog_channels()
#         if results:
#             for channel, value in results.items():
#                 if value is not None:
#                     # Get channel config to determine if it's voltage or current
#                     channel_configs = analog_driver.channel_configs
#                     if channel in channel_configs:
#                         ch_config = channel_configs[channel]
#                         # Try to get measurement_range, fallback to type if missing
#                         if 'measurement_range' in ch_config:
#                             range_code = int(ch_config['measurement_range'], 2)
#                             range_config = analog_driver.range_configs.get(range_code)
#                         else:
#                             range_config = None
#                         
#                         # Determine unit based on type or config
#                         if range_config and range_config['type'] == 'voltage':
#                             unit = "V"
#                         elif ch_config.get('type') == 'voltage':
#                             unit = "V"
#                         else:
#                             unit = "mA"
#                         
#                         # Check if value has changed from last published value
#                         last_value = last_analog_values.get(channel)
#                         if last_value != value:  # Only publish if value changed
#                             value_str = f"{value:.3f}"
#                             if DEBUG:
#                                 print(f"Analog channel {channel}: {value_str}{unit}")
#                             topic = f"{config_dict['MQTT_BASE_TOPIC']}/analog/{channel}"
#                             mqtt.publish(topic, value_str, retain=True)
#                             last_analog_values[channel] = value
#     except Exception as e:
#         if DEBUG:
#             print(f"Error reading/publishing analog values: {e}")

def read_eeprom_config():
    """Read configuration from EEPROM and return as dict."""
    global eeprom
    try:
        length_bytes = eeprom.read_bytes(0x000, 2)
        length = struct.unpack(">H", length_bytes)[0]
        if DEBUG:
            print("EEPROM data length:", length)
        if length > EEPROM_SIZE - 2:
            if DEBUG:
                print("Error: Invalid data length in EEPROM")
            return None
        raw = eeprom.read_bytes(0x002, length)
        restored = unpack_config(raw)
        #print("Restored config from EEPROM:", ujson.dumps(restored))
        return restored
    except Exception as e:
        if DEBUG:
            print("Error reading/unpacking EEPROM:", e)
        return None

def main():
    global driver, mqtt, eeprom, buffer, analog_driver
    try:
        # Initialize I2C and EEPROM
        i2c = machine.I2C(config_dict['I2C_BUS_ID'], scl=machine.Pin(config_dict['I2C_SCL_PIN']), sda=machine.Pin(config_dict['I2C_SDA_PIN']), freq=400000)
        eeprom = EEPROM(i2c, EEPROM_ADDR)
        print("Pico script started")

        # Read EEPROM configuration and update config_dict
        eeprom_config = read_eeprom_config()
        if eeprom_config:
            update_config(eeprom_config)
            time.sleep(1)  # 1s delay for balance
            print("Loaded configuration from EEPROM")
        else:
            print("Failed to read EEPROM configuration, using config.py defaults")

        if not config_dict['WIFI_SSID']:
            print("No Wi-Fi SSID configured, skipping Wi-Fi connect")
        else:
            MqttManager.connect_wifi(config_dict['WIFI_SSID'], config_dict['WIFI_PASSWORD'])
        
#         print(config_dict)
        # Initialize Wi-Fi, IotDriver, and MqttManager
        driver = IotDriver(
            config_dict['I2C_BUS_ID'],
            config_dict['I2C_SDA_PIN'],
            config_dict['I2C_SCL_PIN'],
            config_dict['I2C_DEVICE_ADDR'],
            config_dict['GPIO_HOST_PINS'],
            config_dict['PIN_CONFIG'],
            config_dict['HARDWARE_MODE']
        )
        
        # Build config for AnalogDriver with required fields
        analog_config = {
            'channels': config_dict.get('CHANNELS', []),
            'hardware': {
                'adc_i2c_addrs': config_dict.get('ADC_I2C_ADDRS', []),
                'adc_sampling_rate': config_dict.get('ADC_SAMPLING_RATE', 128),
            }
        }
        
        # Initialize AnalogDriver
        analog_driver = AnalogDriver(i2c, analog_config)
                         
        analog_driver.print_channel_configs()

        mqtt = MqttManager(
            config_dict['MQTT_CLIENT_ID'],
            config_dict['MQTT_BROKER'],
            config_dict['MQTT_PORT'],
            command_callback=handle_mqtt_command
        )
                
        if mqtt.connect():
            command_topic = f"{config_dict['MQTT_BASE_TOPIC']}/output/+/set"
            mqtt.subscribe(command_topic)
            mqtt.publish(f"{config_dict['MQTT_BASE_TOPIC']}/status", "online", retain=True)
    
        last_status_update = time.time()
        poller = uselect.poll()
        poller.register(sys.stdin, uselect.POLLIN)
        
        wifi_retry_start = None   # timestamp of first retry attempt
        wifi_retry_stop = False   # flag to stop further retries

        while True:
            # Check for serial input
            events = poller.poll(0)  # 5ms timeout for responsiveness
            
            if events:  # Serial data is available
                # Keep processing serial input until buffer is empty
                while True:
                    events = poller.poll(0)
                    if not events:
                        # No more serial data - exit inner loop and go back to check again
                        break
                    
                    for _, flag in events:
                        if flag & uselect.POLLIN:
                            char = sys.stdin.read(1)
                            buffer += char
                            if START_MARKER in buffer and END_MARKER in buffer:
                                start = buffer.find(START_MARKER) + len(START_MARKER)
                                end = buffer.find(END_MARKER)
                                json_str = buffer[start:end]
                                buffer = buffer[end + len(END_MARKER):]
                                try:
                                    data = ujson.loads(json_str)
                                    if data.get("command") == "read":
                                        if DEBUG:
                                            print("Received read command")
                                        restored = read_eeprom_config()
                                        if restored:
                                            send_data_back(restored)
                                        else:
                                            send_data_back({"error": "Failed to read or unpack EEPROM data"})
                                    else:
                                        packed = pack_config(data)
                                        if DEBUG:
                                            print("Packed size:", len(packed), "bytes")
                                        if len(packed) > EEPROM_SIZE - 2:
                                            print("Error: Packed data too large for EEPROM")
                                            continue
                                        length_bytes = struct.pack(">H", len(packed))
                                        eeprom.write_bytes(0x000, length_bytes)
                                        eeprom.write_bytes(0x002, packed)
                                        if DEBUG:
                                            print("Wrote data to EEPROM")
                                        raw = eeprom.read_bytes(0x002, len(packed))
                                        restored = unpack_config(raw)
                                        if DEBUG:
                                            print("Restored config:", ujson.dumps(restored))
                                        send_data_back(restored)
                                        update_config(restored)
                                        if not config_dict['WIFI_SSID']:
                                            if DEBUG:
                                                print("No Wi-Fi SSID configured, skipping Wi-Fi connect")
                                        else:
                                            MqttManager.connect_wifi(config_dict['WIFI_SSID'],config_dict['WIFI_PASSWORD'])
                                except ValueError as e:
                                    if DEBUG:
                                        print("JSON parsing error:", e)
                                except OSError as e:
                                    if DEBUG:
                                        print("EEPROM operation error:", e)
                                except Exception as e:
                                    if DEBUG:
                                        print("Unexpected error:", e)
                
                # Finished processing all available serial input
                # Go back to top of loop to check for more serial or do background tasks
                time.sleep(0.001)  # 1ms - let buffer refill
                continue

            # MQTT and I/O tasks
            if MqttManager.is_wifi_connected():
                wifi_retry_start = None
                wifi_retry_stop = False
                if mqtt:
                    try:
                        mqtt.check_for_messages()
                    except Exception as e:
                        if DEBUG:
                            print(f"Error checking MQTT messages: {e}")
                check_and_publish_inputs()
                check_and_publish_analog()
                if time.time() - last_status_update > config_dict['STATUS_UPDATE_INTERVAL_S']:
                    if mqtt:
                        mqtt.publish(f"{config_dict['MQTT_BASE_TOPIC']}/status", "online")
                    last_status_update = time.time()
#             else:
#                 if DEBUG:
#                     print("Wi-Fi connection lost. Attempting to reconnect...")
#                 MqttManager.connect_wifi(config_dict['WIFI_SSID'], config_dict['WIFI_PASSWORD'])
#                 if mqtt and mqtt.connect():
#                     command_topic = f"{config_dict['MQTT_BASE_TOPIC']}/output/+/set"
#                     mqtt.subscribe(command_topic)
            else:
                # --- Wi-Fi reconnect watchdog ---
                if not wifi_retry_stop:
                    if wifi_retry_start is None:
                        wifi_retry_start = time.time()
                        if DEBUG:
                            print("Wi-Fi lost, starting retry timer")

                    # Attempt reconnect only while <30 s from first retry
                    if time.time() - wifi_retry_start < 20:
                        if DEBUG:
                            print("Attempting Wi-Fi reconnect...")
                            
                        if not config_dict['WIFI_SSID']:
                            if DEBUG:
                                print("No Wi-Fi SSID configured, skipping Wi-Fi connect")
                        else:
                            MqttManager.connect_wifi(config_dict['WIFI_SSID'],config_dict['WIFI_PASSWORD'])
                        
                        if mqtt and mqtt.connect():
                            command_topic = f"{config_dict['MQTT_BASE_TOPIC']}/output/+/set"
                            mqtt.subscribe(command_topic)
                    else:
                        wifi_retry_stop = True
                        if DEBUG:
                            print("Wi-Fi reconnect timed out (30 s). Stopping retries.")

            time.sleep(0.01)  # 10ms delay for balance

    except Exception as e:
        print(f"A critical error occurred: {e}")
        print("Rebooting in 10 seconds...")
        time.sleep(10)
        machine.reset()

if __name__ == "__main__":
    main()

