#include "buffer.h"

// A helper to get uint 16 buffer from buffer at specified offset
uint16_t buffer_get_uint16(uint8_t *buffer, uint16_t offset)
{
    // Get uint 16 value (is in little endian format)
    uint16_t value = buffer[offset] | buffer[offset + 1] << 8;
    return value;
}

// A helper to set uint 16 value in buffer at specified offset
void buffer_set_uint16(uint8_t *buffer, uint16_t offset, uint16_t value)
{
    buffer[offset] = value & 0xFF;
    buffer[offset + 1] = value >> 8;
}
