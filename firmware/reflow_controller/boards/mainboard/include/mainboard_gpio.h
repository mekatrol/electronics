#ifndef BTT_SKR_1_4_TURBO_MAINBOARD_GPIO_H
#define BTT_SKR_1_4_TURBO_MAINBOARD_GPIO_H

#include <stdbool.h>
#include <stdint.h>

void mainboard_gpio_configure_output(uint32_t pin, bool initial_high);
void mainboard_gpio_write(uint32_t pin, bool high);

#endif // BTT_SKR_1_4_TURBO_MAINBOARD_GPIO_H
