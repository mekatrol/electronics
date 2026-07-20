#ifndef __BUFFER_H__
#define __BUFFER_H__

#include "pico/stdlib.h"

// A helper to get uint 16 buffer from buffer at specified offset
uint16_t buffer_get_uint16(uint8_t *buffer, uint16_t offset);

// A helper to set uint 16 value in buffer at specified offset
void buffer_set_uint16(uint8_t *buffer, uint16_t offset, uint16_t value);

#endif // __BUFFER_H__