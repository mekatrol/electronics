#include <stdio.h>

#include "pico/util/datetime.h"

#include "hardware/adc.h"
#include "hardware/clocks.h"
#include "hardware/pio.h"
#include "hardware/rtc.h"

#include "../common/communication/buffer.h"
#include "../common/communication/message.h"
#include "../common/communication/protocol.h"
#include "../common/communication/serial.h"

#include "../common/rtc/ds1307.h"

#include "../common/storage/flash_pico.h"
#include "../common/storage/flash_w25q128.h"

#include "../common/utils/ascii.h"

#include "controller_init.h"
#include "pins.h"
#include "state.h"
#include "messaging.h"

extern DS1307 ds1307;

void msg_process_init_storage(uint16_t sndr_addr, uint8_t *data, uint16_t msg_length)
{
    // Is force init set?
    if (!*data)
    {
        // Force not set, only init if needed
        uint8_t initialised = flash_storage_init_if_needed(true);
    }
    else
    {
        // Force init set, initialise (override)
        uint8_t initialised = flash_storage_init(true);
    }
}

void msg_process_set_addr(serial_conf_t *serial_conf, uint16_t sndr_addr, uint8_t *data, uint16_t msg_length)
{
    // Get set address
    serial_conf->addr = buffer_get_uint16(data, 0);

    // Send OK response
    msg_send_ok(serial_conf, sndr_addr, MT_SET_ADDR);
}

void msg_process_set_datetime(serial_conf_t *serial_conf, uint16_t sndr_addr, uint16_t rcvr_addr, uint8_t *data, uint16_t msg_length)
{
    // Get date data
    uint16_t year = buffer_get_uint16(data, 0);
    uint16_t month = buffer_get_uint16(data, 2);
    uint16_t day = buffer_get_uint16(data, 4);
    uint16_t hour = buffer_get_uint16(data, 6);
    uint16_t min = buffer_get_uint16(data, 8);
    uint16_t sec = buffer_get_uint16(data, 10);
    uint16_t dotw = data[12] >> 4;
    datetime_kind = data[12] & 0x0F;

    // Construct date
    datetime_t t = {
        .year = (int16_t)year,
        .month = (int8_t)month,
        .day = (int8_t)day,
        .dotw = (int8_t)dotw,
        .hour = (int8_t)hour,
        .min = (int8_t)min,
        .sec = (int8_t)sec};

    // Set date and time
    rtc_set_datetime(&t);
    ds1307.SetDateTime(&t);

    if (rcvr_addr != GLOBAL_ADDR)
    {
        // Send OK response
        msg_send_ok(serial_conf, sndr_addr, MT_SET_DATETIME);
    }
}

void msg_process_get_status(serial_conf_t *serial_conf, uint16_t sndr_addr, uint8_t *data, uint16_t msg_length)
{
    const float conversion_factor = 3.3f / (1 << 12);
    const float conversion_factor_2 = conversion_factor / 3.195f * 10.0f;

    char datetime_buf[256];
    datetime_t t1;
    datetime_t t2;

    rtc_get_datetime(&t1);
    ds1307.GetDateTime(&t2);

    adc_select_input(0);
    uint16_t result = adc_read();
    // printf("A0 Raw value: %04d, voltage: %f V, voltage 2: %f V\n", result, result * conversion_factor, result * conversion_factor_2);

    adc_select_input(1);
    result = adc_read();
    // printf("A1 Raw value: %04d, voltage: %f V, voltage 2: %f V\n", result, result * conversion_factor, result * conversion_factor_2);

    adc_select_input(2);
    result = adc_read();
    // printf("A2 Raw value: %04d, voltage: %f V, voltage 2: %f V\n", result, result * conversion_factor, result * conversion_factor_2);

    bool inp1 = gpio_get(INP1_PIN);
    // printf("INP1 %d\n", inp1);

    uint8_t msg_data[14];

    buffer_set_uint16(msg_data, 0, t2.year);
    buffer_set_uint16(msg_data, 2, t2.month);
    buffer_set_uint16(msg_data, 4, t2.day);
    buffer_set_uint16(msg_data, 6, t2.hour);
    buffer_set_uint16(msg_data, 8, t2.min);
    buffer_set_uint16(msg_data, 10, t2.sec);
    msg_data[12] = (t2.dotw >> 4) | (datetime_kind & 0x0F);
    msg_data[13] = 0;

    // Send status response
    msg_send_data(serial_conf, sndr_addr, MT_GET_STATUS | MT_OK, msg_data, sizeof(msg_data));
}

extern FlashStorage storage;

void msg_process_reset_flash(serial_conf_t *serial_conf, uint16_t sndr_addr, uint8_t *data, uint16_t msg_length)
{
    const uint32_t page_addr = 0;
    uint8_t page_buf[EXT_FLASH_PAGE_SIZE];

    if (controller_init_reset_flash(page_addr, page_buf))
    {
        // Send fail response
        msg_send_nok(serial_conf, sndr_addr, MT_FLASH_RESET);
    }

    // Send OK response
    msg_send_ok(serial_conf, sndr_addr, MT_FLASH_RESET);
}

void msg_process_dump_flash_page(serial_conf_t *serial_conf, uint16_t sndr_addr, uint8_t *data, uint16_t msg_length)
{
    // Get flash page address (0 to 65,535/0xFFFF is valid)
    uint16_t page_addr = buffer_get_uint16(data, 0);

    // Dump the page
    storage.DumpPage(page_addr);

    // Send OK response
    msg_send_ok(serial_conf, sndr_addr, MT_FLASH_DUMP_PAGE);
}

void process_data_callback(
    serial_conf_t *serial_conf, uint16_t msg_type,
    uint16_t sndr_addr, uint16_t rcvr_addr,
    uint8_t *data, int msg_len)
{
    switch (msg_type)
    {
    case MT_SET_ADDR:
        msg_process_set_addr(serial_conf, sndr_addr, data, msg_len);
        break;

    case MT_SET_DATETIME:
        msg_process_set_datetime(serial_conf, sndr_addr, rcvr_addr, data, msg_len);
        break;

    case MT_INIT_STORAGE:
        msg_process_init_storage(sndr_addr, data, msg_len);
        break;

    case MT_GET_STATUS:
        msg_process_get_status(serial_conf, sndr_addr, data, msg_len);
        break;

    case MT_FLASH_DUMP_PAGE:
        msg_process_dump_flash_page(serial_conf, sndr_addr, data, msg_len);
        break;

    case MT_FLASH_RESET:
        msg_process_reset_flash(serial_conf, sndr_addr, data, msg_len);
        break;
    }
}

int8_t process_rx_message(serial_conf_t *serial_conf, uint8_t *ascii_data, int ascii_data_length)
{
    uint8_t binary_data[1024];

    if (ascii_data[0] != MSG_SOM || ascii_data[ascii_data_length - 1] != MSG_EOM)
    {
        // Failed MSG_SOM and MSG_EOM check, return fail code
        return -1;
    }

    // Shift everything left 1
    for (uint16_t i = 1; i < ascii_data_length; i++)
    {
        ascii_data[i - 1] = ascii_data[i];
    }

    // Adjust length for removal of MSG_SOM and MSG_EOM
    ascii_data_length -= 2;

    ascii_data[ascii_data_length] = '\0';

    // Convert ascii to binary
    uint16_t binaryDataLength = ascii_to_binary(ascii_data, ascii_data_length, binary_data, sizeof(binary_data));

    // Process the message structure, process_data_callback is called if the CRC is correct
    // and the message was sent to GLOBAL_ADDR or device addr
    msg_process_received_data(serial_conf, binary_data, binaryDataLength, process_data_callback);

    return 0;
}
