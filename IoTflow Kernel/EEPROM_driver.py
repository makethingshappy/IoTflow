"""
Title: M24C08-R MicroPython EEPROM Driver
Description: Driver for the M24C08-R 8-Kbit (1KB) I2C serial EEPROM,
             supporting byte-level and page-level read/write operations,
             device polling, erase utilities, and memory dump tools.

Author: Arshia Keshvari
Role: Independent Developer, Engineer, and Project Author
Last Updated: 2025-11-16
"""

"""
M24C08-R EEPROM Driver for MicroPython
8-Kbit (1024 bytes) I2C Serial EEPROM

Features:
- 1024 bytes of EEPROM storage
- 16-byte page writes
- I2C interface (100kHz/400kHz)
- Write protection support
- Polling-based write completion detection
"""

import time
from machine import I2C

class EEPROM:
    """
    Driver for M24C08-R 8-Kbit I2C EEPROM
    
    Memory organization: 1024 bytes (0x000 to 0x3FF)
    Page size: 16 bytes
    """
    
    # Constants
    MEMORY_SIZE = 1024  # 1KB total memory
    PAGE_SIZE = 16      # 16-byte pages
    MAX_WRITE_TIME_MS = 10  # Maximum write cycle time in ms (increase for ESP32-S3 stability)
    
    def __init__(self, i2c, address=0x57, e2_bit=0):
        """
        Initialize the M24C08-R EEPROM driver
        
        Args:
            i2c: I2C object (machine.I2C)
            address: Base I2C address (0x57 default, bits A2:A0 can modify this)
            e2_bit: E2 pin state (0 or 1) - affects device select code bit 3
        """
        self.i2c = i2c
        self.base_address = address
        self.e2_bit = e2_bit & 1  # Ensure it's 0 or 1
        
        # Verify EEPROM is responding
        if not self._is_device_present():
            raise RuntimeError("M24C08-R EEPROM not found at address 0x{:02X}".format(address))
    
    def _get_device_address(self, memory_address):
        """
        Calculate the I2C device address based on memory address
        
        The M24C08-R uses A9 and A8 bits in the device select code
        Device select format: 1010 E2 A9 A8 R/W
        """
        # Extract A9 and A8 from memory address
        a9_a8 = (memory_address >> 8) & 0x03
        
        # Build device select code: 1010 E2 A9 A8 (without R/W bit)
        device_addr = 0x57 | (self.e2_bit << 2) | a9_a8
        return device_addr
    
    def _is_device_present(self):
        """Check if the device is present and responding"""
        try:
            device_addr = self._get_device_address(0)
            self.i2c.writeto(device_addr, b'')
            return True
        except OSError:
            return False
    
    def _wait_write_complete(self, memory_address):
        """
        Wait for write cycle to complete using ACK polling
        
        During internal write cycle, the device won't acknowledge.
        We poll until it responds with ACK.
        """
        device_addr = self._get_device_address(memory_address)
        timeout = time.ticks_ms() + (self.MAX_WRITE_TIME_MS * 3)  # Add more margin for some chips
        
        while time.ticks_diff(timeout, time.ticks_ms()) > 0:
            try:
                # Try to communicate with device
                self.i2c.writeto(device_addr, b'')
                return  # Success - write cycle complete
            except OSError:
                # Device still busy, continue polling
                time.sleep_ms(1)
        
        raise RuntimeError("Write cycle timeout")
    
    def _validate_address(self, address, length=1):
        """Validate memory address and length"""
        if address < 0 or address >= self.MEMORY_SIZE:
            raise ValueError("Address 0x{:03X} out of range (0x000-0x3FF)".format(address))
        if address + length > self.MEMORY_SIZE:
            raise ValueError("Address + length exceeds memory size")
    
    def read_byte(self, address):
        """
        Read a single byte from the specified address
        
        Args:
            address: Memory address (0x000 to 0x3FF)
            
        Returns:
            int: Byte value (0-255)
        """
        self._validate_address(address)
        
        device_addr = self._get_device_address(address)
        addr_byte = address & 0xFF  # Lower 8 bits
        
        # Random address read: write address, then read data
        self.i2c.writeto(device_addr, bytes([addr_byte]))
        data = self.i2c.readfrom(device_addr, 1)
        
        return data[0]
    
    def read_bytes(self, address, length):
        """
        Read multiple bytes starting from the specified address
        
        Args:
            address: Starting memory address
            length: Number of bytes to read
            
        Returns:
            bytes: Data read from EEPROM
        """
        self._validate_address(address, length)
        
        device_addr = self._get_device_address(address)
        addr_byte = address & 0xFF
        
        # For reads crossing page boundaries, we need to handle address rollover
        data = bytearray()
        remaining = length
        current_addr = address
        
        while remaining > 0:
            # Calculate how many bytes we can read before hitting address boundary
            current_device_addr = self._get_device_address(current_addr)
            current_addr_byte = current_addr & 0xFF
            
            # Read up to the end of current 256-byte block or remaining bytes
            bytes_to_read = min(remaining, 256 - current_addr_byte)
            
            # Set address and read
            self.i2c.writeto(current_device_addr, bytes([current_addr_byte]))
            chunk = self.i2c.readfrom(current_device_addr, bytes_to_read)
            data.extend(chunk)
            
            remaining -= bytes_to_read
            current_addr += bytes_to_read
        
        return bytes(data)
    
    def write_byte(self, address, value):
        """
        Write a single byte to the specified address
        
        Args:
            address: Memory address (0x000 to 0x3FF)
            value: Byte value to write (0-255)
        """
        self._validate_address(address)
        
        if not (0 <= value <= 255):
            raise ValueError("Value must be 0-255")
        
        device_addr = self._get_device_address(address)
        addr_byte = address & 0xFF
        
        # Write address and data
        self.i2c.writeto(device_addr, bytes([addr_byte, value]))
        
        # Wait for write cycle to complete
        self._wait_write_complete(address)
    
    def write_bytes(self, address, data):
        """
        Write multiple bytes starting at the specified address
        Uses page write when possible for efficiency
        
        Args:
            address: Starting memory address
            data: bytes or list of integers to write
        """
        if isinstance(data, (list, tuple)):
            data = bytes(data)
        elif isinstance(data, int):
            data = bytes([data])
        
        self._validate_address(address, len(data))
        
        offset = 0
        while offset < len(data):
            current_addr = address + offset
            
            # Calculate page boundary - pages are 16 bytes aligned
            page_start = (current_addr // self.PAGE_SIZE) * self.PAGE_SIZE
            bytes_left_in_page = self.PAGE_SIZE - (current_addr - page_start)
            
            # Write up to end of page or remaining data
            chunk_size = min(bytes_left_in_page, len(data) - offset)
            chunk_data = data[offset:offset + chunk_size]
            
            device_addr = self._get_device_address(current_addr)
            addr_byte = current_addr & 0xFF
            
            # Page write: address byte followed by data bytes
            write_data = bytes([addr_byte]) + chunk_data
            self.i2c.writeto(device_addr, write_data)
            
            # Wait for write cycle to complete
            self._wait_write_complete(current_addr)
            
            offset += chunk_size
    
    def erase_page(self, page_number):
        """
        Erase a page (fill with 0xFF)
        
        Args:
            page_number: Page number (0 to 63)
        """
        if not (0 <= page_number < (self.MEMORY_SIZE // self.PAGE_SIZE)):
            raise ValueError("Page number out of range (0-63)")
        
        address = page_number * self.PAGE_SIZE
        erase_data = bytes([0xFF] * self.PAGE_SIZE)
        self.write_bytes(address, erase_data)
    
    def erase_all(self):
        """Erase entire EEPROM (fill with 0xFF)"""
        print("Erasing entire EEPROM...")
        for page in range(self.MEMORY_SIZE // self.PAGE_SIZE):
            self.erase_page(page)
            if page % 8 == 7:  # Progress indicator
                print(".", end="")
        print(" Done!")
    
    def dump_hex(self, start_addr=0, length=None, bytes_per_line=16):
        """
        Print memory contents in hexadecimal format
        
        Args:
            start_addr: Starting address
            length: Number of bytes to dump (None for entire memory)
            bytes_per_line: Number of bytes per line
        """
        if length is None:
            length = self.MEMORY_SIZE - start_addr
        
        self._validate_address(start_addr, length)
        
        for i in range(0, length, bytes_per_line):
            addr = start_addr + i
            chunk_size = min(bytes_per_line, length - i)
            data = self.read_bytes(addr, chunk_size)
            
            # Format address
            line = "0x{:03X}: ".format(addr)
            
            # Format hex bytes
            hex_part = ""
            ascii_part = ""
            for j in range(chunk_size):
                hex_part += "{:02X} ".format(data[j])
                ascii_part += chr(data[j]) if 32 <= data[j] <= 126 else "."
            
            # Pad hex part if needed
            hex_part = hex_part.ljust(bytes_per_line * 3)
            
            print(line + hex_part + " |" + ascii_part + "|")
    
    def get_info(self):
        """Return information about the EEPROM"""
        return {
            'model': 'M24C08-R',
            'size_bytes': self.MEMORY_SIZE,
            'size_kbit': self.MEMORY_SIZE * 8 // 1024,
            'page_size': self.PAGE_SIZE,
            'num_pages': self.MEMORY_SIZE // self.PAGE_SIZE,
            'i2c_address': "0x{:02X}".format(self.base_address),
            'address_range': "0x000 - 0x3FF"
        }
