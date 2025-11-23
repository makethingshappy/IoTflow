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
IoTextra Analog Driver Module
================================================================================

Author: Arshia Keshvari
Last Updated: 2025/11/23

Description:
This module provides a driver for managing multiple ADS1115 ADCs for analog
input measurements. It handles configuration based on measurement ranges,
hardware gains, and shunt resistances from JSON configuration.

Features:
- Multiple ADC support (up to 4 ADCs per I2C bus)
- Per-channel configuration (measurement range, hardware gain, offset)
- Voltage measurements (0-0.5V, 0-5V, 0-10V, ±0.5V, ±5V, ±10V)
- Current measurements (0-20mA, 4-20mA, ±20mA, 0-40mA)
- Automatic ADS1115 gain selection based on measurement range
- Configurable sampling rates

Dependencies:
- ads1x15.py library for ADS1115 communication
- MicroPython machine module (I2C)
================================================================================
"""

from machine import I2C
import ads1x15
import time

class AnalogDriver:
    def __init__(self, i2c, config):
        """
        Initialize the Analog Driver with configuration from JSON.
        
        Args:
            i2c: Initialized I2C bus object
            config: Configuration dictionary containing:
                - adc_i2c_addrs: List of ADC I2C addresses (hex strings)
                - adc_sampling_rate: Sampling rate in SPS
                - channels: List of channel configurations with analog settings
        """
        self.i2c = i2c
        self.config = config
        self.adcs = []
        self.channel_configs = {}
        
        # Rate mapping (SPS to rate index for ADS1x15 driver)
        self.rate_map = {
            8: 0,    # 128/8 SPS for ADS1115/ADS1015
            16: 1,   # 250/16 SPS
            32: 2,   # 490/32 SPS
            64: 3,   # 920/64 SPS
            128: 4,  # 1600/128 SPS (default)
            250: 5,  # 2400/250 SPS
            475: 6,  # 3300/475 SPS
            860: 7   # -/860 SPS
        }
        
        # ADS1115 gain settings and their corresponding full-scale ranges
        self.ads_gains = {
            0: (6.144, 0),   # ±6.144V, 2/3x gain
            1: (4.096, 1),   # ±4.096V, 1x gain
            2: (2.048, 2),   # ±2.048V, 2x gain
            3: (1.024, 3),   # ±1.024V, 4x gain
            4: (0.512, 4),   # ±0.512V, 8x gain
            5: (0.256, 5)    # ±0.256V, 16x gain
        }
        
        # Measurement range lookup table
        # Binary format: 0bPCRR (P=Polarity, C=Current, RR=Range)
        self.range_configs = {
            # Voltage ranges (bit 5 = 0)
            0b00000001: {'type': 'voltage', 'min': 0, 'max': 0.5, 'bipolar': False, 'ads_gain': 4},
            0b00000010: {'type': 'voltage', 'min': 0, 'max': 5.0, 'bipolar': False, 'ads_gain': 1},
            0b00000011: {'type': 'voltage', 'min': 0, 'max': 10.0, 'bipolar': False, 'ads_gain': 0},
            0b10000001: {'type': 'voltage', 'min': -0.5, 'max': 0.5, 'bipolar': True, 'ads_gain': 4},
            0b10000010: {'type': 'voltage', 'min': -5.0, 'max': 5.0, 'bipolar': True, 'ads_gain': 1},
            0b10000011: {'type': 'voltage', 'min': -10.0, 'max': 10.0, 'bipolar': True, 'ads_gain': 0},
            # Current ranges (bit 5 = 1)
            0b00100001: {'type': 'current', 'min': 0, 'max': 20, 'bipolar': False, 'ads_gain': 1},
            0b10100001: {'type': 'current', 'min': -20, 'max': 20, 'bipolar': True, 'ads_gain': 1},
            0b00100010: {'type': 'current', 'min': 4, 'max': 20, 'bipolar': False, 'ads_gain': 1},
            0b00100011: {'type': 'current', 'min': 0, 'max': 40, 'bipolar': False, 'ads_gain': 0}
        }
        
        self._initialize_adcs()
        self._parse_channel_configs()
    
    def _initialize_adcs(self):
        """Initialize all ADCs from the configuration."""
        adc_addrs = self.config.get('hardware', {}).get('adc_i2c_addrs', [])
        
        for addr_str in adc_addrs:
            try:
                addr = int(addr_str, 16)
                # Initialize with default gain=1, will be set per channel later
                adc = ads1x15.ADS1115(self.i2c, addr, gain=1)
                self.adcs.append({'address': addr, 'instance': adc})
                print(f"Initialized ADS1115 at address {addr_str}")
            except Exception as e:
                print(f"Error initializing ADC at {addr_str}: {e}")
    
    def _parse_channel_configs(self):
        """Parse channel configurations for analog channels."""
        channels = self.config.get('channels', [])
        
        for channel in channels:
            # Check if this is an analog input channel (channel_type == 2)
            if int(channel.get('channel_type')) == 2:
                ch_num = channel.get('channel_number')
                
                # Parse measurement range (binary string or integer)
                range_code = channel.get('measurement_range', '0b00000010')
                if isinstance(range_code, str):
                    range_code = int(range_code, 2)
                
                # Get range configuration
                range_config = self.range_configs.get(range_code, None)
                if range_config is None:
                    print(f"Warning: Unknown measurement range {bin(range_code)} for channel {ch_num}")
                    continue
                
                # Build channel configuration
                self.channel_configs[ch_num] = {
                    'name': channel.get('name', f'Channel {ch_num}'),
                    'measurement_range': bin(range_code),  # Store as binary string for compatibility
                    'type': range_config['type'],
                    'min': range_config['min'],
                    'max': range_config['max'],
                    'bipolar': range_config['bipolar'],
                    'ads_gain': range_config['ads_gain'],
                    'hardware_gain': channel.get('adc_hardware_gain', 0.23761904761904762),
                    'shunt_resistance': channel.get('shunt_resistance', 0.249),
                    'offset': channel.get('adc_offset', 0.0),
                    'range_code': range_code
                }
                
                print(f"Configured channel {ch_num}: {self.channel_configs[ch_num]['name']}, "
                      f"type={range_config['type']}, range={range_config['min']} to {range_config['max']}")
    
    def _get_adc_for_channel(self, channel_number):
        """
        Determine which ADC handles a given channel.
        
        Channel mapping:
        - Channel 0-1: ADC 0 (differential pairs A0-A1, A2-A3)
        - Channel 2-3: ADC 1 (differential pairs A0-A1, A2-A3)
        - Channel 4-5: ADC 2 (differential pairs A0-A1, A2-A3)
        - Channel 6-7: ADC 3 (differential pairs A0-A1, A2-A3)
        
        Returns:
            tuple: (adc_instance, adc_channel_pair) where adc_channel_pair is (ch1, ch2)
        """
        adc_index = channel_number // 2
        pair_index = channel_number % 2
        
        if adc_index >= len(self.adcs):
            return None, None
        
        adc = self.adcs[adc_index]['instance']
        
        # Map to differential pairs: 0 -> (0,1), 1 -> (2,3)
        if pair_index == 0:
            return adc, (0, 1)
        else:
            return adc, (2, 3)
    
    def read_channel_raw(self, channel_number):
        """
        Read raw ADC value from specified channel.
        
        Args:
            channel_number: Channel number (0-7 based on ADC configuration)
            
        Returns:
            int: Raw ADC value, or None on error
        """
        adc, channels = self._get_adc_for_channel(channel_number)
        if adc is None:
            print(f"Error: No ADC configured for channel {channel_number}")
            return None
        
        # Get sampling rate
        sampling_rate = self.config.get('hardware', {}).get('adc_sampling_rate', 128)
        rate_idx = self.rate_map.get(sampling_rate, 4)  # Default to 128 SPS
        
        try:
            raw_value = adc.read(rate=rate_idx, channel1=channels[0], channel2=channels[1])
            return raw_value
        except Exception as e:
            print(f"Error reading channel {channel_number}: {e}")
            return None
    
    def read_channel_voltage(self, channel_number):
        """
        Read voltage from specified channel (ADC voltage, before hardware scaling).
        
        Args:
            channel_number: Channel number
            
        Returns:
            float: Voltage in volts, or None on error
        """
        raw_value = self.read_channel_raw(channel_number)
        if raw_value is None:
            return None
        
        adc, _ = self._get_adc_for_channel(channel_number)
        if adc is None:
            return None
        
        voltage = adc.raw_to_v(raw_value)
        return voltage
    
    def read_channel_physical(self, channel_number):
        """
        Read physical value (voltage or current) from specified channel.
        Applies hardware gain, shunt resistance, and offset corrections.
        
        Args:
            channel_number: Channel number
            
        Returns:
            float: Physical value (V or mA), or None on error
        """
        if channel_number not in self.channel_configs:
            print(f"Error: Channel {channel_number} not configured")
            return None
        
        config = self.channel_configs[channel_number]
        
        # Read ADC voltage
        adc_voltage = self.read_channel_voltage(channel_number)
        if adc_voltage is None:
            return None
        
        # Apply hardware gain (divide by K to get actual voltage)
        scaled_voltage = adc_voltage / config['hardware_gain']
        
        # Convert based on measurement type
        if config['type'] == 'voltage':
            physical_value = scaled_voltage
        else:  # current
            # I = V / R (voltage across shunt resistor)
            physical_value = (scaled_voltage / config['shunt_resistance'])
        
        # Apply offset
        physical_value += config['offset']
        
        # Clamp to range
        physical_value = max(config['min'], min(config['max'], physical_value))
        
        return physical_value
    
    def read_all_analog_channels(self):
        """
        Read all configured analog channels.
        
        Returns:
            dict: Dictionary mapping channel_number -> physical_value
        """
        results = {}
        for ch_num in self.channel_configs.keys():
            value = self.read_channel_physical(ch_num)
            results[ch_num] = value
        return results
    
    def set_channel_gain(self, channel_number, gain_index):
        """
        Set the ADS1115 gain for a specific channel's ADC.
        Note: This reinitializes the ADC instance with the new gain.
        
        Args:
            channel_number: Channel number
            gain_index: Gain index (0-5)
        """
        adc_index = channel_number // 2
        if adc_index >= len(self.adcs):
            print(f"Error: No ADC for channel {channel_number}")
            return
        
        addr = self.adcs[adc_index]['address']
        try:
            # Reinitialize ADC with new gain
            new_adc = ads1x15.ADS1115(self.i2c, addr, gain=gain_index)
            self.adcs[adc_index]['instance'] = new_adc
            print(f"Set gain {gain_index} for ADC at 0x{addr:02X}")
        except Exception as e:
            print(f"Error setting gain: {e}")
    
    def get_channel_info(self, channel_number):
        """
        Get configuration information for a channel.
        
        Args:
            channel_number: Channel number
            
        Returns:
            dict: Channel configuration, or None if not found
        """
        return self.channel_configs.get(channel_number, None)
    
    def print_channel_configs(self):
        """Print all configured analog channels."""
        print("\n=== Analog Channel Configuration ===")
        for ch_num, config in self.channel_configs.items():
            print(f"Channel {ch_num}: {config['name']}")
            print(f"  Type: {config['type']}")
            print(f"  Range: {config['min']} to {config['max']}")
            print(f"  Bipolar: {config['bipolar']}")
            print(f"  ADS Gain: {config['ads_gain']} (±{self.ads_gains[config['ads_gain']][0]}V)")
            print(f"  Hardware Gain (K): {config['hardware_gain']}")
            if config['type'] == 'current':
                print(f"  Shunt Resistance: {config['shunt_resistance']} Ω")
            print(f"  Offset: {config['offset']}")
            print()
