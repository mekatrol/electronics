#ifndef __OUTPUT_CONTROLLER_MESSAGING_H__
#define __OUTPUT_CONTROLLER_MESSAGING_H__

#include "pico/stdlib.h"

int8_t process_rx_message(serial_conf_t *serial_conf, uint8_t *asciiData, int asciiDataLength);

#endif // __OUTPUT_CONTROLLER_MESSAGING_H__