#ifndef __ASCII_H__
#define __ASCII_H__

#include "pico/stdlib.h"

uint8_t ascii_to_byte(uint8_t ch);
uint8_t nibble_to_ascii(uint8_t b);
int16_t ascii_to_binary(uint8_t *ascii_data, uint16_t ascii_data_length, uint8_t *binary_data, uint16_t max_binary_data_length);
int16_t binary_to_ascii(uint8_t *binary_data, uint16_t binary_data_length, uint8_t *ascii_data, uint16_t max_ascii_data_length);

#endif // __ASCII_H__