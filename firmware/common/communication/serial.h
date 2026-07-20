#ifndef __SERIAL_H__
#define __SERIAL_H__

#include "pico/stdlib.h"

// Set send_enable_pin to this value to enable sending
#define SERIAL_SEND_ENABLE_SET 1 << 24
#define SERIAL_SEND_ENABLE_CLR 0 << 24

// 1 = enabled, 0 = disabled
#define SERIAL_ENABLE_MASK 1 << 31

#define SERIAL_TO_SEND_ENABLE(v) ((v >> 24) & 0x01)

#define SERIAL_TO_DATA_BITS(v) ((v >> 8) & 0x0F)
#define SERIAL_TO_STOP_BITS(v) ((v >> 4) & 0x03)
#define SERIAL_TO_PARITY(v) ((uart_parity_t)(v & 0x03))

#define SERIAL_FROM_DATA_BITS(v) ((v & 0x0F) << 8)
#define SERIAL_FROM_STOP_BITS(v) ((v & 0x03) << 4)
#define SERIAL_FROM_PARITY(v) (v & 0x03)

typedef struct serial_conf
{
  // Settings is made up of the following four byte configs:
  // b24 - b31 flags such as enable flag
  // b08 - b23 reserved
  // b04 - b07 serial format data bits, 5..8
  // b02 - b03 serial format stop bits, 1..2
  // b00 - b01 serial format parity none, even, odd as defined in uart_parity_t
  uint settings;
  uint baud_rate;
  uint addr;
  int send_enable_pin;
  uint tx_pin;
  uint rx_pin;
  uart_inst_t *uart;
} serial_conf_t;

void serial_deinit(serial_conf_t *serial_conf);
void serial_init(serial_conf_t *serial_conf);
uint serial_get_rx_waiting_count(serial_conf_t *serial_conf);
int serial_get_rx_data(serial_conf_t *serial_conf, uint8_t *buffer, uint16_t max_len);
bool serial_has_rx_data(serial_conf_t *serial_conf);
bool serial_tx_empty(serial_conf_t *serial_conf);
uint serial_tx_queue_data(serial_conf_t *serial_conf, uint8_t *buffer, uint16_t len);

#endif // __SERIAL_H__