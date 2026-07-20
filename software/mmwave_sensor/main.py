import serial
import serial.tools.list_ports as port_list

FRAME_HEADER_1 = 0x53
FRAME_HEADER_2 = 0x59
SENSOR_INFORMATION_REPORT = 0x0801

ports = list(port_list.comports())

for p in ports:
    print(p)

buffer = []


def process_sensor_information(data):
    existence_energy = data[0]
    stationary_distance = data[1]
    motion_energy = data[2]
    motion_distance = data[3]
    motion_speed = data[4]

    print(f'ee: {existence_energy}, sd: {stationary_distance}, me: {
          motion_energy}, md: {motion_distance}, ms: {motion_speed}')


def process_message(buffer):
    control_word = buffer[2]
    command_word = buffer[3]
    command = control_word << 8 | command_word

    if command == SENSOR_INFORMATION_REPORT:
        process_sensor_information(buffer[6:11])


with serial.Serial('COM25', 115200, 8, 'N', 1, None) as ser:
    checksum = 0
    data_len = 0
    data_count = 0

    while True:
        # Read a byte from the port
        byte = ser.read(1)[0]

        # Get current length of buffer
        buffer_len = len(buffer)

        # Are we waiting for first byte of frame header?
        if buffer_len == 0:
            if byte == FRAME_HEADER_1:
                buffer.append(byte)
                checksum = byte

        elif buffer_len == 1:
            if byte == FRAME_HEADER_2:
                buffer.append(byte)

                checksum += byte
            else:
                # If not second byte of frame header then reset buffer
                buffer = []

                # Reset checksum
                checksum = 0

                # It might be the first byte of frame header though
                if byte == FRAME_HEADER_1:
                    buffer.append(byte)
                    checksum = byte

        # Waiting for control word?
        elif buffer_len == 2:
            buffer.append(byte)
            checksum += byte

        # Waiting for command word?
        elif buffer_len == 3:
            buffer.append(byte)
            checksum += byte
            data_len = 0

        # Waiting for command data length?
        elif buffer_len == 4 or buffer_len == 5:
            buffer.append(byte)
            checksum += byte
            data_len += byte
            data_count = 0

        # Waiting for data?
        elif buffer_len <= (5 + data_len):
            buffer.append(byte)
            checksum += byte

        else:
            if (checksum & 0xFF) != byte:
                print('Bad checksum')
            else:
                process_message(buffer)

            buffer = []
            cks = 0
            data_len = 0
            data_count = 0
