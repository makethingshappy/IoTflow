import machine

# IoTextra board with TCA9534 I/O expander
# driver = IotDriver(
#         config.I2C_BUS_ID,
#         config.I2C_SDA_PIN,
#         config.I2C_SCL_PIN,
#         config.I2C_DEVICE_ADDR,
#         config.GPIO_HOST_PINS,
#         config.PIN_CONFIG,
#         config.HARDWARE_MODE
#     )
class IotDriver:
    def __init__(self, bus_id, sda_pin, scl_pin, device_address, gpio_host_pins, pin_config, hardware_mode):
        self.device_address = device_address
        self.i2c = None
        self.gpio_host_pins = gpio_host_pins
        self.hardware_mode = hardware_mode
        self.pin_config = pin_config # pin_config: 1 means input, 0 means output
        self.output_pin_state = 0b11111111 # All relays off initially -> this is to track state of the outputs on the firmware
        self.gpio_pins = {} # to store machine.Pin objects for GPIO mode through a HOST connector

        # TCA9534 register addresses
        self.OUTPUT_PORT_REGISTER = 0x01
        self.INPUT_PORT_REGISTER = 0x00
        self.CONFIG_REGISTER = 0x03

        if self.hardware_mode == "i2c":
            try:
                self.i2c = machine.I2C(bus_id, sda=machine.Pin(sda_pin), scl=machine.Pin(scl_pin), freq=400000)
                # configure IO expander on the board
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
                    # configure as input with pull-up
                    self.gpio_pins[channel] = machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_UP)
                else:
                    # configure as output and set to default high state (relay off)
                    self.gpio_pins[channel] = machine.Pin(pin_num, machine.Pin.OUT)
                    self.gpio_pins[channel].value(1)
            print("GPIO pins initialized.")
            
    def set_output(self, channel, state):
        # check the channel is set to output (0)
        if not ((self.pin_config >> (channel - 1)) & 0x01) == 0:
            return

        if self.hardware_mode == "i2c":
            if not self.i2c: return
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
        
        elif self.hardware_mode == "gpio":
            if channel in self.gpio_pins:
                print(f"Setting GPIO output for channel {channel} to {state}")
                # Use active-low logic: True -> 0, False -> 1
                self.gpio_pins[channel].value(0 if state else 1)

    def read_all_inputs(self):
        if self.hardware_mode == "i2c":
            if not self.i2c: return None
            try:
                # Read 1 byte from the INPUT_PORT_REGISTER (0x00)
                data = self.i2c.readfrom_mem(self.device_address, self.INPUT_PORT_REGISTER, 1)
                byte_val = int.from_bytes(data, 'big')

                result = []
                # pin_config: 1 means input, 0 means output
                for i in range(8):
                    if (self.pin_config >> i) & 0x01:
                        # input pin: get its state
                        state = (byte_val >> i) & 0x01
                        # reversing state so that 1 means there is signal and 0 means no signal
                        result.append(state ^ 0x01)
                    else:
                        # output pin: set as None
                        result.append(None)
                return result
            except OSError as e:
                print(f"Error reading from I2C device: {e}")
                return None
        
        elif self.hardware_mode == "gpio":
            result = []
            for i in range(8):
                channel = i + 1
                if (self.pin_config >> i) & 0x01:
                    # It's an input, read its value
                    if channel in self.gpio_pins:
                        state = self.gpio_pins[channel].value()
                        # reversing state so that 1 means there is signal (GND) and 0 means no signal (PULL_UP)
                        result.append(state ^ 0x01)
                    else:
                        result.append(None) # Should not happen if configured correctly
                else:
                    # It's an output, append None
                    result.append(None)
            return result
        
        return None