#ifndef BTT_SKR_1_4_TURBO_MAINBOARD_HAL_H
#define BTT_SKR_1_4_TURBO_MAINBOARD_HAL_H

#include <stdbool.h>
#include <stdint.h>

void mainboard_hal_initialize_safe_outputs(void);
void mainboard_hal_fault(void);
bool mainboard_hal_fault_latched(void);
uint32_t mainboard_hal_milliseconds(void);
void mainboard_hal_initialize_tick(void);
void mainboard_hal_initialize_watchdog(void);
void mainboard_hal_feed_watchdog(void);
void mainboard_hal_enable_interrupts(void);

#endif
