#ifndef BTT_SKR_1_4_TURBO_MAINBOARD_UART_H
#define BTT_SKR_1_4_TURBO_MAINBOARD_UART_H

#include <stdbool.h>
#include <stdint.h>

void mainboard_uart_initialize(void);
bool mainboard_uart_write_byte(uint8_t value);
bool mainboard_uart_read_byte(uint8_t *value);
void mainboard_uart_service(void);

#endif
