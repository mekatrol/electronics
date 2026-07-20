from machine import UART, Pin

FRAME_HEADER_1 = 0x53
FRAME_HEADER_2 = 0x59
SENSOR_INFORMATION_REPORT = 0x0801

# The message structure to reset the device
# Checksum already calculated in following message
RESET_MESSAGE = [
    0x53, 0x59, 0x01, 0x02, 0x00, 0x01, 0x0F, 0xBF, 0x54, 0x43
]

# The message structure to close sending of underlying parameters raw data
# The board will periodically transmit Control Word = 0x08, Command Word = 0x01 after this
# Checksum already calculated in following message
OPEN_MESSAGE = [
    0x53, 0x59, 0x08, 0x00, 0x00, 0x01, 0x01, 0xB6, 0x54, 0x43
]

# The message structure to close sending of underlying parameters raw data
# The board will no longer periodically transmit Control Word = 0x08, Command Word = 0x01 after this
# Checksum already calculated in following message
CLOSE_MESSAGE = [
    0x53, 0x59, 0x08, 0x00, 0x00, 0x01, 0x00, 0xB5, 0x54, 0x43
]


class MmwaveSensor:
    def __init__(self, uart, baudrate, tx, rx):
        self.uart = UART(uart, baudrate=baudrate, tx=Pin(tx), rx=Pin(rx))
        self.buffer = []
        self.data_len = 0
        self.motion_energy = None

    def initialise_device(self) -> bool:
        try:
            # Reset the device
            self.uart.write(bytearray(RESET_MESSAGE))

            # Enable raw parameters
            self.uart.write(bytearray(OPEN_MESSAGE))

            return True
        except Exception as ex:
            print(ex)
            return False

    def process_sensor_information(self, data):
        existence_energy = data[0]
        stationary_distance = data[1]
        motion_energy = data[2]
        motion_distance = data[3]
        motion_speed = data[4]

        return motion_energy

    def process_message(self, buffer):
        control_word = buffer[2]
        command_word = buffer[3]
        command = control_word << 8 | command_word

        if command == SENSOR_INFORMATION_REPORT:
            return self.process_sensor_information(buffer[6:11])

        # Return last known value
        return self.motion_energy

    def calculate_checksum(self):
        # We need everything in buffer up to checksum byte
        buffer_without_cks = self.buffer[0:-1]

        cks = 0

        for c in buffer_without_cks:
            cks += c

        return (cks & 0xFF)

    def poll(self):
        # Read a byte from the port
        byte_list = self.uart.read(10)

        if byte_list == None:
            return self.motion_energy

        for byte in byte_list:
            # Get current length of buffer (before adding new byte)
            buffer_len = len(self.buffer)

            # Append new byte
            self.buffer.append(byte)

            # Are we waiting for first byte of frame header?
            if buffer_len == 0:
                if byte == FRAME_HEADER_1:
                    # Nothing to do here
                    pass

            elif buffer_len == 1:
                if byte != FRAME_HEADER_2:
                    # If not second byte of frame header then reset buffer
                    self.buffer = []

            # Waiting for control word?
            elif buffer_len == 2:
                # Nothing to do other than control word was added to buffer
                pass

            # Waiting for command word?
            elif buffer_len == 3:
                # Reset data length waiting for next two bytes
                self.data_len = 0

            # Waiting for command data length?
            elif buffer_len == 4 or buffer_len == 5:
                # Update data length
                self.data_len += byte

            # Waiting for data?
            elif buffer_len <= (5 + self.data_len):
                # Nothing to do other than data was added to buffer
                pass

            else:
                calculated_checksum = self.calculate_checksum()
                if calculated_checksum != byte:
                    print(
                        f'Bad checksum: {hex(calculated_checksum)} != {hex(byte)}')
                else:
                    self.motion_energy = self.process_message(self.buffer)

                # Reset state
                self.buffer = []
                self.checksum = 0
                self.data_len = 0

        # Return last value received
        return self.motion_energy
