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

# IoTextra Octal3 MicroPython Test Script
# Simple test for 4x latching relays (EC2-5SNU) via TCA9534A + DRV8837C
# ESP32-S3 with IoTextra Octal3 Mezzanine

from machine import I2C, Pin
import time

# Configuration
I2C_ID = 0
SDA_PIN = 16
SCL_PIN = 15
TCA_ADDR = 0x27  # TCA9534A

# nSLEEP pin (AP5 -> GPIO 5 on host)
NSLEEP_PIN = 5

# Relay to TCA port mapping (P0-P7)
# DRV1 (K1): P1=IN1, P0=IN2
# DRV2 (K2): P3=IN1, P2=IN2
# DRV3 (K3): P5=IN1, P4=IN2
# DRV4 (K4): P7=IN1, P6=IN2
RELAY_PINS = {
    1: (1, 0),  # Relay 1: (IN1 pin, IN2 pin)
    2: (3, 2),
    3: (5, 4),
    4: (7, 6)
}

class Octal3Relays:
    def __init__(self):
        self.i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
        self.nsleep = Pin(NSLEEP_PIN, Pin.OUT)
        self.nsleep.value(0)  # Start in sleep
        
        # TCA9534A registers
        self.REG_INPUT = 0x00
        self.REG_OUTPUT = 0x01
        self.REG_POLARITY = 0x02
        self.REG_CONFIG = 0x03
        
        # Set all pins as outputs (0 = output)
        self.i2c.writeto_mem(TCA_ADDR, self.REG_CONFIG, b'\x00')
        
        # Initial state: all outputs low, sleep
        self.set_all_low()
        print("Octal3 initialized - all relays off, nSLEEP low")

    def write_outputs(self, value):
        """Write 8-bit value to output register"""
        self.i2c.writeto_mem(TCA_ADDR, self.REG_OUTPUT, bytes([value]))

    def set_all_low(self):
        self.write_outputs(0x00)

    def pulse_relay(self, relay_num, set_state=True, pulse_ms=5):
        """
        Pulse a single latching relay
        set_state=True: Set (latch ON)
        set_state=False: Reset (latch OFF)
        """
        if relay_num not in RELAY_PINS:
            print(f"Invalid relay {relay_num}")
            return
        
        in1_pin, in2_pin = RELAY_PINS[relay_num]
        
        # Wake up drivers
        self.nsleep.value(1)
        time.sleep_ms(1)  # Allow charge pump to stabilize
        
        mask = 1 << in1_pin | 1 << in2_pin
        
        # Prepare pulse
        if set_state:
            # Set: IN1=1, IN2=0
            pulse_val = (1 << in1_pin)
        else:
            # Reset: IN1=0, IN2=1
            pulse_val = (1 << in2_pin)
        
        # Apply pulse
        self.write_outputs(pulse_val)
        time.sleep_ms(pulse_ms)
        
        # Return to idle (both IN1=IN2=0)
        self.write_outputs(0x00)
        
        # Sleep drivers again
        time.sleep_ms(1)
        self.nsleep.value(0)
        
        state_str = "SET" if set_state else "RESET"
        print(f"Relay {relay_num} {state_str} pulsed ({pulse_ms}ms)")

    def test_sequence(self):
        """Basic test sequence"""
        print("\n=== Starting Relay Test Sequence ===")
        
        for r in range(1, 5):
            print(f"\n--- Testing Relay {r} ---")
            self.pulse_relay(r, set_state=True, pulse_ms=4)
            time.sleep(1)
            self.pulse_relay(r, set_state=False, pulse_ms=4)
            time.sleep(1)
        
        print("\nTest complete. All relays reset.")

# Main
if __name__ == "__main__":
    relays = Octal3Relays()
#     relays.test_sequence()
    
    relays.pulse_relay(1, False)
    
    print("\nReady for manual control. Example:")
    print("relays.pulse_relay(1, True)   # Set Relay 1")
    print("relays.pulse_relay(2, False)  # Reset Relay 2")