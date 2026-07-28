#include <stdbool.h>
#include <stdint.h>

#include "board_pins.h"
#include "mainboard_gpio.h"
#include "mainboard_hal.h"

#define SYSTICK_CONTROL (*(volatile uint32_t *)0xE000E010u)
#define SYSTICK_RELOAD (*(volatile uint32_t *)0xE000E014u)
#define SYSTICK_CURRENT (*(volatile uint32_t *)0xE000E018u)
#define WATCHDOG_MODE (*(volatile uint32_t *)0x40000000u)
#define WATCHDOG_TIMER_CONSTANT (*(volatile uint32_t *)0x40000004u)
#define WATCHDOG_FEED (*(volatile uint32_t *)0x40000008u)
#define WATCHDOG_CLOCK_SELECT (*(volatile uint32_t *)0x40000010u)

static volatile uint32_t milliseconds;
static volatile bool fault_latched;

static void force_outputs_off(void)
{
  mainboard_gpio_write(BOARD_HEATER_0_PIN, false);
  mainboard_gpio_write(BOARD_HEATER_1_PIN, false);
  mainboard_gpio_write(BOARD_HEATED_BED_PIN, false);
  mainboard_gpio_write(BOARD_FAN_0_PIN, false);
}

void mainboard_hal_initialize_safe_outputs(void)
{
  /*
   * SKR MOSFET gates are active high. Set each output latch low before changing
   * its direction. No Phase 2 code contains an API that can turn a heater on.
   * TODO: verify polarity on the exact board revision with loads disconnected.
   */
  mainboard_gpio_configure_output(BOARD_HEATER_0_PIN, false);
  mainboard_gpio_configure_output(BOARD_HEATER_1_PIN, false);
  mainboard_gpio_configure_output(BOARD_HEATED_BED_PIN, false);
  mainboard_gpio_configure_output(BOARD_FAN_0_PIN, false);
  fault_latched = false;
}

void mainboard_hal_fault(void)
{
  __asm volatile("cpsid i" ::: "memory");
  force_outputs_off();
  fault_latched = true;
  __asm volatile("cpsie i" ::: "memory");
}

bool mainboard_hal_fault_latched(void)
{
  return fault_latched;
}

uint32_t mainboard_hal_milliseconds(void)
{
  return milliseconds;
}

void mainboard_hal_initialize_tick(void)
{
  SYSTICK_RELOAD = 120000u - 1u;
  SYSTICK_CURRENT = 0u;
  SYSTICK_CONTROL = 7u;
}

void SysTick_Handler(void)
{
  milliseconds++;
}

void mainboard_hal_initialize_watchdog(void)
{
  /* 4 MHz internal RC / 4, giving a conservative two-second timeout. */
  WATCHDOG_CLOCK_SELECT = 1u;
  WATCHDOG_TIMER_CONSTANT = 2000000u;
  WATCHDOG_MODE = 3u;
  mainboard_hal_feed_watchdog();
}

void mainboard_hal_feed_watchdog(void)
{
  WATCHDOG_FEED = 0xAAu;
  WATCHDOG_FEED = 0x55u;
}

void mainboard_hal_enable_interrupts(void)
{
  __asm volatile("cpsie i" ::: "memory");
}
