#ifndef __BCD_H__
#define __BCD_H__

#include "pico/stdlib.h"

uint8_t bcd2bin(uint8_t val);
uint8_t bin2bcd(uint8_t val);

#endif