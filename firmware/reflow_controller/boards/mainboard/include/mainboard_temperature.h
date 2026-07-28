#ifndef BTT_SKR_1_4_TURBO_MAINBOARD_TEMPERATURE_H
#define BTT_SKR_1_4_TURBO_MAINBOARD_TEMPERATURE_H

#include <stdbool.h>
#include <stdint.h>

void mainboard_temperature_initialize(void);
void mainboard_temperature_service(void);
bool mainboard_temperature_read_raw(uint8_t channel, uint16_t *sample);

#endif
