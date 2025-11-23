# MIT License
#
# Copyright (c) 2025 makethingshappy,
#               2025 Arshia Keshvari (@TeslaNeuro)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
------------------------------------------------------------
MqttManager – Wi-Fi and MQTT Management for IoTextra Modules
------------------------------------------------------------
This script provides a lightweight MQTT manager for MicroPython, handling
Wi-Fi connections, MQTT broker communication, subscribing to topics, and
publishing messages. It also supports a callback mechanism for received
commands/messages.

Author: Arshia Keshvari
Role: Independent Developer, Engineer, and Project Author
Last Updated: 2025-11-23
"""

import time
from umqtt_simple import MQTTClient
import network
import gc

class MqttManager:
    def __init__(self, client_id, broker, port, command_callback=None):
        self.client_id = client_id
        self.broker = broker
        self.port = port
        self.command_callback = command_callback
        self.client = MQTTClient(client_id, broker, port)
        self.client.set_callback(self._mqtt_callback)

    def connect(self):
        if not self.is_wifi_connected():
            print("Error: Wi-Fi not connected. Cannot connect to MQTT.")
            return False
            
        try:
            print(f"Connecting to MQTT broker at {self.broker}...")
            self.client.connect()
            print("MQTT connected successfully.")
            return True
        except OSError as e:
            print(f"Error: Could not connect to MQTT broker. {e}")
            return False

    def subscribe(self, topic):
        print(f"Subscribing to topic: {topic}")
        self.client.subscribe(topic)
        
    def publish(self, topic, message, retain=False):
        print(f"Publishing to {topic}: {message}")
        self.client.publish(topic, str(message), retain)

    def check_for_messages(self):
        self.client.check_msg()
        
    def _mqtt_callback(self, topic, msg):
        topic = topic.decode()
        msg = msg.decode()
        print(f"Message received on topic '{topic}': {msg}")
        if self.command_callback:
            self.command_callback(topic, msg)
        
    @staticmethod
    def connect_wifi(ssid, password):
        wlan = network.WLAN(network.STA_IF)

        # Force a clean start
        wlan.active(False)
        time.sleep(0.5)
        wlan.active(True)
        wlan.disconnect()
        gc.collect()
        
        timeout = 10
        if not ssid:
            print("No SSID configured; skipping Wi-Fi connection.")
            return False

        print(f"Connecting to Wi-Fi network: '{ssid}'...")
        try:
            wlan.connect(ssid, password)
        except OSError as e:
            # Covers the "Wifi Internal Error" case
            print(f"Wi-Fi connect() failed immediately: {e}")
            return False

        start = time.time()
        while not wlan.isconnected():
            if time.time() - start > timeout:
                print("Wi-Fi connection timed out after", timeout, "seconds.")
                return False
            time.sleep(1)
            print(".", end="")
        
        print("\nWi-Fi connected! Network config:", wlan.ifconfig())
        return True
            
    @staticmethod
    def is_wifi_connected():
        wlan = network.WLAN(network.STA_IF)
        return wlan.isconnected()
    
    @staticmethod
    def disconnect_wifi():
        wlan = network.WLAN(network.STA_IF)
        wlan.disconnect()
        print("Wi-Fi disconnected.")




