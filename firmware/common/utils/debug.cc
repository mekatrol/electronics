#include "debug.h"

void flash_on(uint32_t delay)
{
    // gpio_put(PICO_DEFAULT_LED_PIN, 1);
    busy_wait_us_32(delay);
    // gpio_put(PICO_DEFAULT_LED_PIN, 0);
    busy_wait_us_32(delay);
}

void flash_code(uint16_t code)
{
    busy_wait_us_32(2000000);

    for (int i = 0; i < code; i++)
    {
        flash_on(800000);
    }
}
