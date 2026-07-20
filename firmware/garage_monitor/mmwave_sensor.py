from machine import UART, Pin

FRAME_HEADER_1 = 0x53
FRAME_HEADER_2 = 0x59
SENSOR_INFORMATION_REPORT = 0x0801

class MmwaveSensor:
    def __init__(self):
        self.uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
        self.buffer = []
        self.data_len = 0
        self.motion_energy = None

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

    async def poll(self):
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
                    print(f'Bad checksum: {hex(calculated_checksum)} != {hex(byte)}')
                else:
                    self.motion_energy = self.process_message(self.buffer)

                # Reset state
                self.buffer = []
                self.checksum = 0
                self.data_len = 0

        # Return last value received
        return self.motion_energy
