#ifndef BTT_SKR_1_4_TURBO_MAINBOARD_NEOPIXEL_H
#define BTT_SKR_1_4_TURBO_MAINBOARD_NEOPIXEL_H

#include <stdint.h>

void mainboard_neopixel_write_rgb_chain(uint32_t pin,
                                        uint8_t red,
                                        uint8_t green,
                                        uint8_t blue,
                                        uint32_t pixel_count);

#endif // BTT_SKR_1_4_TURBO_MAINBOARD_NEOPIXEL_H
