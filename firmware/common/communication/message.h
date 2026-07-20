#ifndef __MESSAGE_H__
#define __MESSAGE_H__

#include "pico/stdlib.h"

#include "serial.h"

extern uint8_t datetime_kind;

typedef struct message
{
    uint16_t receiver_address;
    uint16_t sender_address;
    uint16_t message_type;
    uint16_t data_length;
    uint8_t *data;
} message_t;

void msg_process_received_data(
    serial_conf_t *serial_conf,
    uint8_t *binary_data,
    uint16_t binary_data_length,
    void (*process_data_callback)(serial_conf_t *serial_conf, uint16_t msg_type, uint16_t sndr_addr, uint16_t rcvr_addr, uint8_t *data, int msg_len));

uint8_t msg_send_data(serial_conf_t *serial_conf, uint16_t dest_addr, uint16_t message_type, uint8_t *data, uint16_t data_len);
uint8_t msg_send_nok(serial_conf_t *serial_conf, uint16_t dest_addr, uint16_t msg_type_for_nok);
uint8_t msg_send_ok(serial_conf_t *serial_conf, uint16_t dest_addr, uint16_t msg_type_for_ok);

#endif // __MESSAGE_H__