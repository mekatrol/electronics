#ifndef __TEMP_H__
#define __TEMP_H__

#include <Arduino.h>

typedef struct
{
    int16_t value;
    uint16_t celsius;
} temp_entry_t;

float temp_analog_to_celsius(const uint16_t raw);

#endif // __TEMP_H__