#include <stdio.h>
#include <stdlib.h>

#include "hardware/rtc.h"
#include "pico/util/datetime.h"

#include "../utils/ascii.h"
#include "../utils/crc16.h"
#include "../utils/core_sync.h"
#include "../storage/flash_pico.h"

#include "buffer.h"
#include "message.h"
#include "protocol.h"
#include "serial.h"

// uint8_t msg_data[1024];
// uint8_t ascii_data[sizeof(msg_data) << 1];

void msg_process_set_addr(uint16_t dest_addr, uint8_t *data, uint16_t msg_length);
void msg_process_set_datetime(uint16_t dest_addr, uint8_t *binary_data, uint16_t msg_length);
void msg_process_init_storage(uint16_t dest_addr, uint8_t *data, uint16_t msg_length);
void msg_process_get_status(uint16_t dest_addr, uint8_t *data, uint16_t msg_length);
uint8_t msg_send_data(serial_conf_t *serial_conf, uint16_t dest_addr, uint16_t message_type, uint8_t *data, uint16_t data_len);

void msg_process_received_data(
    serial_conf_t *serial_conf,
    uint8_t *data, uint16_t data_length,
    void (*process_data_callback)(
        serial_conf_t *serial_conf, uint16_t msg_type,
        uint16_t sndr_addr, uint16_t rcvr_addr,
        uint8_t *data, int msg_len))
{
    if (data_length < 10)
    {
        // At least 10 characters required for a valid message
        // RCVR_ADDR, SNDR_ADDR MT LEN CRC
        // 2          2         2  2   2
        return;
    }

    uint16_t calculatedCrc = crc16_buffer(~0, data, data_length - 2);

    // Get message crc (is in little endian format)
    uint16_t messageCrc = buffer_get_uint16(data, data_length - 2);

    if (calculatedCrc != messageCrc)
    {
        return;
    }

    // Get the receiver address
    uint16_t rcvr_addr = buffer_get_uint16(data, 0);

    if (rcvr_addr != 0xFFFF && rcvr_addr != serial_conf->addr)
    {
        // The message has successfully processed (it was not for this device)
        return;
    }

    // Get the sender address
    uint16_t sndr_addr = buffer_get_uint16(data, 2);

    // Get message type
    uint16_t msg_type = buffer_get_uint16(data, 4);

    // Get message length
    uint16_t msg_length = buffer_get_uint16(data, 6);

    // The message length must be the data length less the length of the CRC (2 bytes)
    if (msg_length != data_length - 2)
    {
        return;
    }

    // Process the callback for the received data
    process_data_callback(serial_conf, msg_type, sndr_addr, rcvr_addr, &data[8], msg_length);
}

void msg_send_byte(serial_conf_t *serial_conf, uint8_t b)
{
    // Wait for space in TX buffer
    while (!uart_is_writable(serial_conf->uart))
        ;

    // Write byte
    uart_putc(serial_conf->uart, b);
}

uint8_t msg_send_data(serial_conf_t *serial_conf, uint16_t dest_addr, uint16_t message_type, uint8_t *data, uint16_t data_len)
{
    // If data is NULL then make sure data_len is 0
    if (!data)
    {
        data_len = 0;
    }

    // RCV ADDR (2) + SND ADDR (2) + MT (2) + LEN (2) + DATA (data_len) + CRC (2)
    uint16_t binary_msg_len = 10 + data_len;

    // Allocate binary buffer
    uint8_t *msg_data = (uint8_t *)malloc(binary_msg_len);

    // Build binary message
    int i = 0;
    msg_data[i++] = dest_addr & 0xFF;         // Destination address (low byte - little endian)
    msg_data[i++] = dest_addr >> 8;           // Destination address (low byte - little endian)
    msg_data[i++] = serial_conf->addr & 0xFF; // Device address (low byte - little endian)
    msg_data[i++] = serial_conf->addr >> 8;   // Device address (low byte - little endian)
    msg_data[i++] = message_type & 0xFF;      // Message type (low byte - little endian)
    msg_data[i++] = message_type >> 8;        // Message type (high byte - little endian)
    msg_data[i++] = data_len & 0xFF;          // LEN length is length of message type being Ok'd (low byte - little endian)
    msg_data[i++] = data_len >> 8;            // LEN (high byte - little endian)

    // Add data
    for (int j = 0; j < data_len; j++)
    {
        msg_data[i++] = data[j];
    }

    // Get message crc (is in little endian format)
    uint16_t calculatedCrc = crc16_buffer(~0, msg_data, binary_msg_len - 2);

    msg_data[binary_msg_len - 2] = calculatedCrc & 0xFF; // CRC value (low byte - little endian)
    msg_data[binary_msg_len - 1] = calculatedCrc >> 8;   // CRC value (high byte - little endian)

    // Allocate ascii buffer
    uint8_t *ascii_data = (uint8_t *)malloc(binary_msg_len << 1); // binary_msg_len * 2

    int16_t ascii_len = binary_to_ascii(msg_data, binary_msg_len, ascii_data, binary_msg_len << 1);

    // Was there an error converting to ascii?
    if (ascii_len < 0)
    {
        return 0;
    }

    // // Queue SOM
    // uint8_t b = MSG_SOM;
    // serial_tx_queue_data(serial_conf, &b, 1);

    // // Queue message
    // serial_tx_queue_data(serial_conf, ascii_data, ascii_len);

    // // Queue EOM
    // b = MSG_EOM;
    // serial_tx_queue_data(serial_conf, &b, 1);

    uint16_t tx_index = 0;

    if (serial_conf->send_enable_pin >= 0)
    {
        gpio_put(serial_conf->send_enable_pin, 1);
    }

    msg_send_byte(serial_conf, MSG_SOM);
    while (tx_index < ascii_len)
    {
        msg_send_byte(serial_conf, ascii_data[tx_index]);
        tx_index++;
    }
    msg_send_byte(serial_conf, MSG_EOM);

    sleep_ms(200);

    if (serial_conf->send_enable_pin >= 0)
    {
        gpio_put(serial_conf->send_enable_pin, 0);
    }

    free(msg_data);
    free(ascii_data);

    return 1;
}

// Send an Not OK response for the specified message type
uint8_t msg_send_nok(serial_conf_t *serial_conf, uint16_t dest_addr, uint16_t msg_type_for_nok)
{
    return msg_send_data(serial_conf, dest_addr, msg_type_for_nok | MT_NOK, NULL, 0);
}

// Send an OK response for the specified message type
uint8_t msg_send_ok(serial_conf_t *serial_conf, uint16_t dest_addr, uint16_t msg_type_for_ok)
{
    return msg_send_data(serial_conf, dest_addr, msg_type_for_ok | MT_OK, NULL, 0);
}