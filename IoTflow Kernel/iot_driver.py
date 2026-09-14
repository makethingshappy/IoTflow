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
iot_driver – Hardware Abstraction Layer for Digital I/O
------------------------------------------------------------
This script provides a unified driver to control IoTextra Digital I/O hardware using
either I2C (via a TCA9534 I/O expander) or GPIO mode through a HOST connector.
It supports setting output states and reading inputs for multiple hardware
variants of the IoTextra Digital I/O boards, including Octal3 / Relay latching
relays and Octal4 (standard TCA9534 4DI + 4DO, not latching).

Octal4 note:
    Octal4 maps 1:1 onto the TCA9534: P0-P3 are ISO1211 direct-mode digital
    inputs, P4-P7 are SPST relay outputs. Use the standard I2C path with
    pin_config 0b00001111. Do not enable Octal3 latching mode.

Latching hybrid note (Octal3 and IoTextra Relay):
    Both boards drive 4 latching relays via the TCA9534 over I2C (2 physical
    TCA pins per relay, all 8 TCA pins are outputs, plus nSLEEP on a host
    GPIO). `pin_config` describes the LOGICAL channel map - it does not
    describe the TCA9534's physical pin directions, which are always
    all-output.

    Octal3: remaining host GPIO channels are digital INPUTS.
    IoTextra Relay: remaining host GPIO channels are ordinary GPIO OUTPUTS
    (SPST relays). Those outputs use the same active-low GPIO path as other
    digital boards; they are not pulsed.

    Which logical channels are latching outputs is given by octal3_channels;
    the relay pin-pair (IN1/IN2) each one drives is assigned dynamically in
    ascending channel order.

Author: Arshia Keshvari
Role: Independent Developer, Engineer, and Project Author
Last Updated: 2026-07-18
"""

import machine
import time


class IotDriver:

    def __init__(self, bus_id, sda_pin, scl_pin, device_address, gpio_host_pins, pin_config, hardware_mode,
                 iso1211_channels=None, nsleep_pin=None, octal3_channels=None):

        self.device_address = device_address
        self.i2c = None
        self.gpio_host_pins = gpio_host_pins
        self.hardware_mode = hardware_mode
        self.pin_config = pin_config  # pin_config: 1 means input, 0 means output (LOGICAL channel map)
        self.output_pin_state = 0b11111111  # All relays off initially
        self.gpio_pins = {}  # host GPIO pins (GPIO mode, and hybrid host I/O in i2c mode)

        # Channels owned by the ISO1211 driver
        self.iso1211_channels = set(iso1211_channels) if iso1211_channels else set()

        # Octal3 specific
        self.nsleep_pin = None
        self.is_octal3 = bool(octal3_channels)
        self.octal3_channels = set(octal3_channels) if octal3_channels else set()
        # Software mirror of latching-relay ON/OFF (no I2C readback available).
        # Defaults OFF until loaded from EEPROM or set via set_output.
        self.octal3_output_states = {ch: False for ch in self.octal3_channels}

        # TCA9534 register addresses
        self.OUTPUT_PORT_REGISTER = 0x01
        self.INPUT_PORT_REGISTER = 0x00
        self.CONFIG_REGISTER = 0x03

        # Relay to I2C IO Expander port mapping for Octal3 Only. The TCA9534 
        # physically has 4 fixed relay pin-pairs (IN1, IN2) at P0-P7. Which 
        # LOGICAL channel drives which physical relay pair depends on 
        # octal3_channels, so this is built dynamically: the lowest-numbered 
        # output channel gets relay pin-pair 1, the next gets pair 2, and so on.
        physical_relay_pin_pairs = [(1, 0), (3, 2), (5, 4), (7, 6)]
        self.RELAY_PINS = {
            channel: physical_relay_pin_pairs[i]
            for i, channel in enumerate(sorted(self.octal3_channels))
            if i < len(physical_relay_pin_pairs)
        }

        # --- Pin collision validation ------------------------------------
        # Only channels that are actually input channels under pin_config 
        # get a real machine.Pin() created (see the init loop below), so 
        # only those entries are checked here; a dummy/unused entry for an
        # output channel can't collide because it's never turned into a
        # real Pin object.
        if self.hardware_mode == "i2c" and self.is_octal3:
            reserved = {}  # pin_number -> label, for error messages

            def _reserve(pin_number, label):
                if pin_number is None:
                    return
                if pin_number in reserved:
                    raise ValueError(
                        f"GPIO pin conflict: {label} and {reserved[pin_number]} "
                        f"both use pin {pin_number}. Each must use a distinct GPIO."
                    )
                reserved[pin_number] = label

            _reserve(sda_pin, "sda_pin")
            _reserve(scl_pin, "scl_pin")
            _reserve(nsleep_pin, "nsleep_pin")
            for channel, pin_num in self.gpio_host_pins.items():
                is_input = (self.pin_config >> (channel - 1)) & 0x01
                role = "input" if is_input else "output"
                _reserve(pin_num, f"CH{channel} ({role} host pin)")

        if self.hardware_mode == "i2c":
            try:
                self.i2c = machine.I2C(bus_id, sda=machine.Pin(sda_pin), scl=machine.Pin(scl_pin), freq=400000)

                if self.is_octal3:
                    # All 8 TCA9534 pins (P0-P7) are relay H-bridge drive
                    # outputs on Octal3 (2 pins per relay x 4 relays).
                    # pin_config describes logical channels, not TCA9534
                    # pin directions, so force the TCA9534 config register
                    # to all-output (0x00) regardless of pin_config's value.
                    self.i2c.writeto(self.device_address, bytes([self.CONFIG_REGISTER, 0x00]))
                    print(f"Latching TCA9534 configured as all-output (relay drivers) "
                          f"at device_address {hex(device_address)}.")

                    if nsleep_pin is not None:
                        self.nsleep_pin = machine.Pin(nsleep_pin, machine.Pin.OUT)
                        self.nsleep_pin.value(0)  # Start in sleep
                        print(f"nSLEEP initialized on pin {nsleep_pin}")

                    # Host GPIO channels live on the MCU, NOT on the TCA9534.
                    # pin_config selects direction: Octal3 uses inputs here,
                    # IoTextra Relay uses ordinary GPIO outputs (SPST).
                    # Latching outputs are pure I2C (via _octal3_pulse_relay)
                    # and are not present in gpio_host_pins.
                    for channel, pin_num in self.gpio_host_pins.items():
                        is_input = (self.pin_config >> (channel - 1)) & 0x01
                        if is_input:
                            self.gpio_pins[channel] = machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_UP)
                            print(f"Hybrid input CH{channel} initialized on host GPIO pin {pin_num}")
                        else:
                            self.gpio_pins[channel] = machine.Pin(pin_num, machine.Pin.OUT)
                            self.gpio_pins[channel].value(1)  # active-low off
                            print(f"Hybrid GPIO output CH{channel} initialized on host GPIO pin {pin_num}")

                else:
                    # Standard (non-Octal3) I2C expander: pin_config maps
                    # directly onto the TCA9534's own pins.
                    self.i2c.writeto(self.device_address, bytes([self.CONFIG_REGISTER, self.pin_config]))
                    print(f"Pin configuration of the board is set to {hex(self.pin_config)}.")

                print(f"Successfully initialized I/O expander at device_address {hex(device_address)}.")

            except OSError as e:
                print(f"Error: Could not initialize I/O expander. {e}")
                self.i2c = None

        elif self.hardware_mode == "gpio":
            print("Initializing in GPIO mode.")
            for channel, pin_num in self.gpio_host_pins.items():
                is_input = (self.pin_config >> (channel - 1)) & 0x01
                if is_input:
                    self.gpio_pins[channel] = machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_UP)
                else:
                    self.gpio_pins[channel] = machine.Pin(pin_num, machine.Pin.OUT)
                    self.gpio_pins[channel].value(1)
            print("GPIO pins initialized.")

    def _octal3_pulse_relay(self, relay_num, set_state=True, pulse_ms=5):
        """Pulse a latching relay for Octal3 (only for I2C mode)"""
        if not self.is_octal3 or relay_num not in self.RELAY_PINS or not self.i2c:
            return False

        in1_pin, in2_pin = self.RELAY_PINS[relay_num]

        # Wake up drivers
        if self.nsleep_pin:
            self.nsleep_pin.value(1)
            time.sleep_ms(1)

        # Prepare pulse
        if set_state:
            # Set: IN1=1, IN2=0
            pulse_val = (1 << in1_pin)
        else:
            # Reset: IN1=0, IN2=1
            pulse_val = (1 << in2_pin)

        # Apply pulse
        try:
            self.i2c.writeto_mem(self.device_address, self.OUTPUT_PORT_REGISTER, bytes([pulse_val]))
            time.sleep_ms(pulse_ms)

            # Return to idle (both IN1=IN2=0)
            self.i2c.writeto_mem(self.device_address, self.OUTPUT_PORT_REGISTER, bytes([0x00]))

            # Sleep drivers again
            time.sleep_ms(1)
            if self.nsleep_pin:
                self.nsleep_pin.value(0)

            state_str = "SET" if set_state else "RESET"
            print(f"Latching relay {relay_num} {state_str} pulsed ({pulse_ms}ms)")
            return True
        except OSError as e:
            print(f"Error pulsing latching relay: {e}")
            return False

    def set_output(self, channel, state):
        """Set output state. For latching relays, this triggers a pulse.

        Returns:
            True if a latching logical state changed (caller should persist),
            False/None otherwise.
        """
        # check the channel is set to output (0)
        if not ((self.pin_config >> (channel - 1)) & 0x01) == 0:
            return False

        # Handle latching relays (Octal3 / IoTextra Relay) specially
        if self.is_octal3 and channel in self.octal3_channels and self.hardware_mode == "i2c":
            new_state = bool(state)
            print(f"Setting latching output for channel {channel} to {new_state}")
            if not self._octal3_pulse_relay(channel, set_state=new_state):
                return False
            changed = self.octal3_output_states.get(channel) != new_state
            self.octal3_output_states[channel] = new_state
            return changed

        # Host GPIO outputs (IoTextra Relay SPST, or any hybrid GPIO out)
        # even when hardware_mode is i2c for the latching expander.
        if channel in self.gpio_pins and ((self.pin_config >> (channel - 1)) & 0x01) == 0:
            print(f"Setting GPIO output for channel {channel} to {state}")
            self.gpio_pins[channel].value(0 if state else 1)
            return False

        if self.hardware_mode == "i2c":
            if not self.i2c:
                return False
            print(f"Setting I2C output for channel {channel} to {state}")
            pin_index = channel - 1

            if state:
                # set bit to 0 to activate relay (active-low)
                self.output_pin_state &= ~(1 << pin_index)
            else:
                # set bit to 1 to deactivate relay
                self.output_pin_state |= (1 << pin_index)
            try:
                self.i2c.writeto(self.device_address, bytes([self.OUTPUT_PORT_REGISTER, self.output_pin_state]))
            except OSError as e:
                print(f"Error writing to I2C device: {e}")
            return False

        elif self.hardware_mode == "gpio":
            if channel in self.gpio_pins:
                print(f"Setting GPIO output for channel {channel} to {state}")
                # Use active-low logic: True -> 0, False -> 1
                self.gpio_pins[channel].value(0 if state else 1)
            return False

        return False

    def get_output(self, channel):
        """Return stored Octal3 output state, or None if not an Octal3 output."""
        if not self.is_octal3 or channel not in self.octal3_channels:
            return None
        return self.octal3_output_states.get(channel, False)

    def load_octal3_states(self, bitmask):
        """Load Octal3 output states from a CH1-CH8 bitmask (no hardware pulse)."""
        if not self.is_octal3:
            return
        for channel in self.octal3_channels:
            self.octal3_output_states[channel] = bool(bitmask & (1 << (channel - 1)))

    def octal3_states_bitmask(self):
        """Pack stored Octal3 output states into a CH1-CH8 bitmask."""
        bitmask = 0
        for channel, state in self.octal3_output_states.items():
            if state:
                bitmask |= (1 << (channel - 1))
        return bitmask

    def read_all_inputs(self):
        if self.hardware_mode == "i2c":
            if not self.i2c:
                return None

            if self.is_octal3:
                # Latching output channels are on the TCA9534 - there is no
                # readback for them. Host GPIO channels live on the MCU:
                # inputs are read here; GPIO outputs (Relay SPST) have no
                # input readback.
                result = []
                for i in range(8):
                    channel = i + 1
                    if i in self.iso1211_channels:  # owned by ISO1211 - don't touch
                        result.append(None)
                    elif (self.pin_config >> i) & 0x01:
                        # logical input channel -> read from host GPIO pin
                        if channel in self.gpio_pins:
                            state = self.gpio_pins[channel].value()
                            # reversing state so that 1 means there is signal and 0 means no signal
                            result.append(state ^ 0x01)
                        else:
                            result.append(None)
                    else:
                        # output pin: latching relay or GPIO SPST, no input readback
                        result.append(None)
                return result

            try:
                # Read 1 byte from the INPUT_PORT_REGISTER (0x00)
                data = self.i2c.readfrom_mem(self.device_address, self.INPUT_PORT_REGISTER, 1)
                byte_val = int.from_bytes(data, 'big')
                result = []
                # pin_config: 1 means input, 0 means output
                for i in range(8):
                    if i in self.iso1211_channels:   # owned by ISO1211 — don't touch
                        result.append(None)
                    elif (self.pin_config >> i) & 0x01:
                        # input pin: get its state
                        state = (byte_val >> i) & 0x01
                        # reversing state so that 1 means there is signal and 0 means no signal
                        result.append(state ^ 0x01)
                    else:
                        # output pin: set as None (Octal3 outputs are latching, no readback)
                        result.append(None)
                return result
            except OSError as e:
                print(f"Error reading from I2C device: {e}")
                return None

        elif self.hardware_mode == "gpio":
            result = []
            for i in range(8):
                channel = i + 1
                if i in self.iso1211_channels:
                    result.append(None)
                elif (self.pin_config >> i) & 0x01:
                    # It's an input, read its value
                    if channel in self.gpio_pins:
                        state = self.gpio_pins[channel].value()
                        result.append(state ^ 0x01)
                    else:
                        result.append(None)
                else:
                    result.append(None)
            return result

        return None