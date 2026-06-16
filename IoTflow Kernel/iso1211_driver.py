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
================================================================================
IoTextra ISO1211 Sampled-Mode Digital Input Driver
================================================================================

Author: Arshia Keshvari
Last Updated: 2026-06-15

Description
-----------
Non-blocking driver for ISO1211 sampled-mode digital input channels on the
IoTextra Quadro module (IoTflow Kernel / MicroPython).

This driver ONLY handles *sampled-mode* channels (90V DC, 110V AC, 220V AC),
where the JM jumper is OPEN and FGND is switched by the MCU through a TLP188
optocoupler driven by a dedicated HOST connector pin (`fgnd_gpio`).

Direct-mode channels (12-60V DC, JM closed) are electrically identical to any
other isolated DI input and remain handled by the existing `iot_driver.IotDriver`
without any changes. This module never touches them.

Channel configuration (read from the same EEPROM source as all other channels)
------------------------------------------------------------------------------
A sampled-mode ISO1211 channel is identified by ``channel_type == "3"`` and
carries the following fields:

    name             : human-readable label (<= 8 chars, like other channels)
    channel_type     : "3"  -> ISO1211 sampled-mode DI
    interface_type   : "01" -> OUT read via a direct MCU GPIO pin   (out_source = "gpio")
                       "11" -> OUT read via the TCA9534 I2C expander (out_source = "i2c")
                       (identical meaning/codes to standard DI channels)
    channel_number   : 0-7  -> position used for the OUT read (TCA9534 bit, or
                              HOST pin lookup), and for the MQTT topic
    actions          : 0    -> sampled DI is read-only
    fgnd_gpio        : int  -> HOST connector pin that drives the TLP188 / FGND.
                              *** The only parameter unique to sampled mode. ***
                              REQUIRED. A channel with a missing/invalid
                              fgnd_gpio is rejected (logged) and skipped.
    out_gpio         : int  -> OPTIONAL. Only meaningful when interface_type == "01".
                              Explicit MCU pin for the ISO1211 OUT signal. If
                              omitted, the OUT pin is looked up from
                              gpio_host_pins[channel_number + 1] (same HOST-pin
                              convention the standard DI driver uses).

Safety (CRITICAL)
-----------------
HOST connector pins are undefined at power-on. A floating `fgnd_gpio` can switch
the TLP188 on and energise the ISO1211 at up to 220V AC, overheating the chip.
Therefore the ABSOLUTE FIRST action of this driver is to drive EVERY configured
`fgnd_gpio` to its inactive (TLP188 OFF) level, before any other initialisation.

Scan sequence (per measurement, fully non-blocking)
---------------------------------------------------
    assert fgnd_gpio (TLP188 ON) -> wait t_settle -> read OUT -> de-assert fgnd_gpio
Channels are scanned round-robin, one at a time, so only ONE FGND is ever
asserted simultaneously. The 25 ms settle is implemented with a ticks-based
state machine advanced by ``update()`` from the main cooperative run-loop -
there are no blocking sleeps.

Dependencies: machine, time (MicroPython)
================================================================================
"""

import machine
import time

# -----------------------------------------------------------------------------
# User-modifiable constants
# -----------------------------------------------------------------------------

# Universal settling time for ALL sampled-mode ranges (90V DC / 110V AC / 220V AC).
# Covers RC settling of the input circuit and acts as a conservative
# inter-measurement interval that limits average power dissipation.
# Users needing faster response / tighter thermal control may lower this.
T_SETTLE_MS = 25

# TLP188 / FGND drive polarity.
#   True  -> assert  = pin high (1), de-assert = pin low (0)   [default]
#   False -> assert  = pin low (0),  de-assert = pin high (1)
# "Inactive / TLP188 OFF" is always the de-asserted level above.
FGND_ACTIVE_HIGH = True

# ISO1211 OUT logic. The standard DI driver treats inputs as active-low and
# inverts so that 1 == "signal present". We mirror that convention here.
OUT_ACTIVE_LOW = True

# Channel type code identifying an ISO1211 sampled-mode DI channel in the
# shared channel configuration (analogous to "1" = digital bit, "2" = analog).
ISO1211_CHANNEL_TYPE = 3

# interface_type codes (shared with standard DI channels) -> out_source
_OUT_SOURCE_BY_INTERFACE = {
    "01": "gpio",
    "11": "i2c",
    "12": "i2c",  # GPIO + I2C: OUT is read over the expander
}

# Internal scan-state-machine states
_STATE_IDLE = 0      # nothing asserted; ready to start the next channel
_STATE_SETTLING = 1  # FGND asserted on current channel; waiting for t_settle

# TCA9534 register (same as iot_driver.py)
_INPUT_PORT_REGISTER = 0x00


class Iso1211Driver:
    """Non-blocking driver for ISO1211 sampled-mode digital input channels."""

    def __init__(self, i2c, device_address, gpio_host_pins, channels,
                 t_settle_ms=T_SETTLE_MS):
        """
        Args:
            i2c:            Initialised machine.I2C bus (shared) used for
                            TCA9534 OUT reads. May be None if no channel uses
                            the i2c out_source.
            device_address: TCA9534 I2C address (int) used for i2c OUT reads.
            gpio_host_pins: dict mapping channel (1-8) -> HOST GPIO pin. Used to
                            resolve the OUT pin for gpio out_source channels when
                            `out_gpio` is not given explicitly. Keys may be int
                            or str.
            channels:       list of channel config dicts (the same list used by
                            the rest of the firmware). Only entries with
                            channel_type == ISO1211_CHANNEL_TYPE are handled.
            t_settle_ms:    settling time in ms (defaults to T_SETTLE_MS = 25).
        """
        self.i2c = i2c
        self.device_address = device_address
        self.gpio_host_pins = self._normalise_host_pins(gpio_host_pins)
        self.t_settle_ms = t_settle_ms

        # Per-channel runtime state, list of dicts:
        #   { 'name', 'channel_number', 'out_source', 'fgnd_pin' (machine.Pin),
        #     'out_pin' (machine.Pin or None), 'out_bit' (int or None),
        #     'last_value' (0/1 or None), 'error' (bool) }
        self.channels = []

        # Scan state machine
        self._state = _STATE_IDLE
        self._index = 0
        self._t_assert = 0
        self._current = None

        # ---------------------------------------------------------------
        # STEP 1 - ABSOLUTE FIRST ACTION (SAFETY):
        # De-assert EVERY configured fgnd_gpio (TLP188 OFF) before anything else.
        # ---------------------------------------------------------------
        valid_specs = self._safe_deassert_all_fgnd(channels)

        # ---------------------------------------------------------------
        # STEP 2 - Build OUT readers for the channels that passed validation.
        # ---------------------------------------------------------------
        self._build_channels(valid_specs)

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalise_host_pins(gpio_host_pins):
        """Return a {int channel: int pin} map, tolerating str keys/values."""
        result = {}
        if not gpio_host_pins:
            return result
        try:
            items = gpio_host_pins.items()
        except AttributeError:
            return result
        for key, pin in items:
            try:
                result[int(key)] = int(pin)
            except (TypeError, ValueError):
                continue
        return result

    @staticmethod
    def _is_valid_pin(value):
        """fgnd_gpio must be a non-negative integer pin number."""
        if value is None or isinstance(value, bool):
            return False
        try:
            return int(value) >= 0
        except (TypeError, ValueError):
            return False

    def _fgnd_inactive_level(self):
        return 0 if FGND_ACTIVE_HIGH else 1

    def _fgnd_active_level(self):
        return 1 if FGND_ACTIVE_HIGH else 0

    def _safe_deassert_all_fgnd(self, channels):
        """
        SAFETY-CRITICAL first action: validate fgnd_gpio for every sampled-mode
        channel and immediately drive each one to the inactive (TLP188 OFF)
        level. Returns the list of (channel_dict, fgnd_pin) specs that are valid;
        invalid channels are logged and skipped.
        """
        valid_specs = []
        if not channels:
            print("ISO1211: no channels provided; nothing to de-assert.")
            return valid_specs

        for ch in channels:
            try:
                if int(ch.get("channel_type")) != ISO1211_CHANNEL_TYPE:
                    continue
            except (TypeError, ValueError):
                continue

            ch_num = ch.get("channel_number")
            fgnd_gpio = ch.get("fgnd_gpio")

            if not self._is_valid_pin(fgnd_gpio):
                print("ISO1211: REJECTED channel '{}' (number {}): missing or "
                      "invalid fgnd_gpio ({!r}). Channel skipped."
                      .format(ch.get("name", "?"), ch_num, fgnd_gpio))
                continue

            fgnd_pin_num = int(fgnd_gpio)
            try:
                # Configure as output and force inactive (TLP188 OFF) NOW.
                fgnd_pin = machine.Pin(fgnd_pin_num, machine.Pin.OUT)
                fgnd_pin.value(self._fgnd_inactive_level())
            except Exception as e:
                print("ISO1211: REJECTED channel '{}' (number {}): could not "
                      "init fgnd_gpio pin {} ({}). Channel skipped."
                      .format(ch.get("name", "?"), ch_num, fgnd_pin_num, e))
                continue

            print("ISO1211: fgnd_gpio pin {} de-asserted (TLP188 OFF) for "
                  "channel '{}'.".format(fgnd_pin_num, ch.get("name", "?")))
            valid_specs.append((ch, fgnd_pin))

        print("ISO1211: startup safety complete - {} FGND pin(s) de-asserted."
              .format(len(valid_specs)))
        return valid_specs

    def _build_channels(self, valid_specs):
        """Build the OUT-reader state for each validated channel."""
        for ch, fgnd_pin in valid_specs:
            ch_num = ch.get("channel_number")
            interface_type = str(ch.get("interface_type", "01"))
            out_source = _OUT_SOURCE_BY_INTERFACE.get(interface_type, "gpio")

            out_pin = None
            out_bit = None

            if out_source == "i2c":
                # OUT read from TCA9534 input register, bit = channel_number.
                try:
                    out_bit = int(ch_num)
                except (TypeError, ValueError):
                    out_bit = None
                if out_bit is None or not (0 <= out_bit <= 7):
                    print("ISO1211: channel '{}' has invalid channel_number {!r} "
                          "for i2c OUT; defaulting to bit 0."
                          .format(ch.get("name", "?"), ch_num))
                    out_bit = 0
            else:
                # gpio OUT: explicit out_gpio, else HOST-pin convention.
                out_pin_num = ch.get("out_gpio")
                if not self._is_valid_pin(out_pin_num):
                    try:
                        out_pin_num = self.gpio_host_pins.get(int(ch_num) + 1)
                    except (TypeError, ValueError):
                        out_pin_num = None
                if self._is_valid_pin(out_pin_num):
                    try:
                        out_pin = machine.Pin(int(out_pin_num),
                                              machine.Pin.IN, machine.Pin.PULL_UP)
                    except Exception as e:
                        print("ISO1211: channel '{}' could not init OUT gpio pin "
                              "{} ({}); reads will report error."
                              .format(ch.get("name", "?"), out_pin_num, e))
                        out_pin = None
                else:
                    print("ISO1211: channel '{}' (number {}) has no resolvable "
                          "OUT gpio pin; reads will report error."
                          .format(ch.get("name", "?"), ch_num))

            self.channels.append({
                "name": ch.get("name", "ISO1211 {}".format(ch_num)),
                "channel_number": ch_num,
                "out_source": out_source,
                "fgnd_pin": fgnd_pin,
                "out_pin": out_pin,
                "out_bit": out_bit,
                "last_value": None,
                "error": False,
            })
            print("ISO1211: configured channel '{}' (number {}), out_source={}."
                  .format(ch.get("name", "?"), ch_num, out_source))

    # ------------------------------------------------------------------
    # FGND control
    # ------------------------------------------------------------------
    def _assert_fgnd(self, ch):
        ch["fgnd_pin"].value(self._fgnd_active_level())

    def _deassert_fgnd(self, ch):
        ch["fgnd_pin"].value(self._fgnd_inactive_level())

    def deassert_all(self):
        """Force every FGND inactive (TLP188 OFF). Safe to call anytime."""
        for ch in self.channels:
            try:
                self._deassert_fgnd(ch)
            except Exception:
                pass
        self._state = _STATE_IDLE
        self._current = None

    # ------------------------------------------------------------------
    # OUT reading
    # ------------------------------------------------------------------
    def _read_out(self, ch):
        """
        Read the ISO1211 OUT pin for the given channel.
        Returns 0/1 on success (1 == signal present), or None on error.
        Sets/clears the per-channel error flag. Error handling mirrors the
        standard DI driver (TCA9534 not found / I2C read failure -> error).
        """
        if ch["out_source"] == "i2c":
            if not self.i2c:
                ch["error"] = True
                return None
            try:
                data = self.i2c.readfrom_mem(self.device_address,
                                             _INPUT_PORT_REGISTER, 1)
                byte_val = int.from_bytes(data, "big")
                state = (byte_val >> ch["out_bit"]) & 0x01
                if OUT_ACTIVE_LOW:
                    state ^= 0x01
                ch["error"] = False
                return state
            except OSError as e:
                print("ISO1211: I2C read error on channel '{}': {}"
                      .format(ch["name"], e))
                ch["error"] = True
                return None

        # gpio out_source
        if ch["out_pin"] is None:
            ch["error"] = True
            return None
        try:
            state = ch["out_pin"].value()
            if OUT_ACTIVE_LOW:
                state ^= 0x01
            ch["error"] = False
            return state
        except Exception as e:
            print("ISO1211: GPIO read error on channel '{}': {}"
                  .format(ch["name"], e))
            ch["error"] = True
            return None

    # ------------------------------------------------------------------
    # Non-blocking scan state machine
    # ------------------------------------------------------------------
    def update(self):
        """
        Advance the round-robin scan by one step. Call this frequently from the
        main cooperative run-loop. Never blocks.

        Returns:
            None, or a tuple (channel_number, value, changed) when a channel
            measurement has just completed this call. `changed` is True if the
            confirmed value differs from the previously confirmed value.
        """
        if not self.channels:
            return None

        now = time.ticks_ms()

        if self._state == _STATE_IDLE:
            # Start the next channel in round-robin order.
            self._current = self.channels[self._index]
            self._assert_fgnd(self._current)          # TLP188 ON
            self._t_assert = now
            self._state = _STATE_SETTLING
            return None

        # _STATE_SETTLING
        if time.ticks_diff(now, self._t_assert) < self.t_settle_ms:
            return None  # still settling - non-blocking wait

        ch = self._current
        value = self._read_out(ch)                    # read OUT
        self._deassert_fgnd(ch)                        # TLP188 OFF
        self._state = _STATE_IDLE
        self._index = (self._index + 1) % len(self.channels)
        self._current = None

        if value is None:
            return None

        changed = (ch["last_value"] != value)
        ch["last_value"] = value
        return (ch["channel_number"], value, changed)

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def has_channels(self):
        return bool(self.channels)

    def get_values(self):
        """Return {channel_number: last_confirmed_value}."""
        return {ch["channel_number"]: ch["last_value"] for ch in self.channels}

    def get_errors(self):
        """Return {channel_number: error_flag}."""
        return {ch["channel_number"]: ch["error"] for ch in self.channels}

    def print_channel_configs(self):
        print("\n=== ISO1211 Sampled-Mode Channel Configuration ===")
        print("t_settle = {} ms".format(self.t_settle_ms))
        for ch in self.channels:
            print("Channel {}: {}".format(ch["channel_number"], ch["name"]))
            print("  OUT source: {}".format(ch["out_source"]))
            if ch["out_source"] == "i2c":
                print("  OUT bit: {} (TCA9534 0x{:02X})"
                      .format(ch["out_bit"], self.device_address))
            print("  Last value: {}  Error: {}"
                  .format(ch["last_value"], ch["error"]))
        print()
