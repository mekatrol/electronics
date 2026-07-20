#include <stdio.h>

#include "ascii.h"

uint8_t ascii_to_byte(uint8_t ch)
{
    // Convert ASCII character to binary equiv
    // [0-9] = [48 -  57] = [0x30 - 0x39]
    // [A-Z] = [65 -  90] = [0x41 - 0x5A]
    // [a-z] = [97 - 122] = [0x61 - 0x7A]

    // a - z are largest values
    if (ch > 'Z')
    {
        return (uint8_t)(ch - 'a' + 10);
    }

    // A - Z are next largest
    if (ch > '9')
    {
        return (uint8_t)(ch - 'A' + 10);
    }

    // Leaves 0 - 9
    return (uint8_t)(ch - '0');
}

uint8_t nibble_to_ascii(uint8_t b)
{
    // Convert binary nibble to ASCII equiv
    // [0-9] = [48 -  57] = [0x30 - 0x39]
    // [A-Z] = [65 -  90] = [0x41 - 0x5A]
    // [a-z] = [97 - 122] = [0x61 - 0x7A]

    // Convert a-f to 'a'-'f'
    if (b > 9)
    {
        return b + 'a' - 10;
    }

    // Convert 0-9 to '0'-'9'
    return b + '0';
}

int16_t ascii_to_binary(uint8_t *ascii_data, uint16_t ascii_data_length, uint8_t *binary_data, uint16_t max_binary_data_length)
{
    uint16_t bindaryIndex = 0;
    for (int i = 0; i < ascii_data_length; i += 2)
    {
        int8_t ch1 = ascii_data[i];
        int8_t ch2 = ascii_data[i + 1];

        bindaryIndex = i >> 1;

        if (bindaryIndex >= max_binary_data_length)
        {
            // Binary data buffer overflow
            return -1;
        }

        binary_data[bindaryIndex] = (int8_t)(ascii_to_byte(ch1) << 4 | ascii_to_byte(ch2));
    }

    return ascii_data_length >> 1;
}

int16_t binary_to_ascii(uint8_t *binary_data, uint16_t binary_data_length, uint8_t *ascii_data, uint16_t max_ascii_data_length)
{
    for (int16_t i = 0; i < binary_data_length; i++)
    {
        int16_t ascii_i = i << 1; // i * 2

        // Return error, ascii buffer not big enough
        if (ascii_i >= max_ascii_data_length)
        {
            return -1;
        }

        ascii_data[ascii_i] = nibble_to_ascii((binary_data[i] >> 4) & 0x0F); // High nibble
        ascii_data[ascii_i + 1] = nibble_to_ascii(binary_data[i] & 0x0F);    // Low nibble
    }

    return binary_data_length << 1;
}
