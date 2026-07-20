#ifndef __CRC_16_H__
#define __CRC_16_H__

#include "pico/stdlib.h"

// Table for the CRC-16
// The polynomial is 0x8005 (x^16 + x^15 + x^2 + 1) "forward" direction
// This is consistent with the MODBUS CRC
extern const uint16_t crc16_table[256];

static inline uint16_t crc16_byte(uint16_t crc, const uint8_t b)
{
    return (crc >> 8) ^ crc16_table[(crc ^ b) & 0xff];
}

static inline uint16_t crc16_buffer(uint16_t crc, uint8_t const *buffer, size_t buffer_len)
{
    while (buffer_len--)
    {
        crc = crc16_byte(crc, *buffer++);
    }

    return crc;
}

#endif // __CRC_16_H__