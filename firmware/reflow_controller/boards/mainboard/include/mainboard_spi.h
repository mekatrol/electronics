#ifndef BTT_SKR_1_4_TURBO_MAINBOARD_SPI_H
#define BTT_SKR_1_4_TURBO_MAINBOARD_SPI_H

#include <stdint.h>

void mainboard_spi_initialize_sd(void);
uint8_t mainboard_spi_transfer(uint8_t value);
void mainboard_spi_set_slow(bool slow);

#endif
