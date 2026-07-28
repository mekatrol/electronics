#ifndef __AVG_H__
#define __AVG_H__

#include <Arduino.h>

typedef struct average_set
{
    uint16_t v1 = 0;
    uint16_t v2 = 0;
    uint16_t v3 = 0;
    uint16_t v4 = 0;
    uint16_t v5 = 0;

    uint8_t initialised = 0;
} average_set_t;

uint16_t average_calc(average_set_t *set, uint16_t value);

#endif // __AVG_H__