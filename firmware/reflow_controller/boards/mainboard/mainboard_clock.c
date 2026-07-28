#include <stdint.h>

#include "mainboard_clock.h"

#define LPC_FLASH_CONFIG (*(volatile uint32_t *)0x400FC000u)
#define LPC_PLL0_CONTROL (*(volatile uint32_t *)0x400FC080u)
#define LPC_PLL0_CONFIG (*(volatile uint32_t *)0x400FC084u)
#define LPC_PLL0_STATUS (*(volatile uint32_t *)0x400FC088u)
#define LPC_PLL0_FEED (*(volatile uint32_t *)0x400FC08Cu)
#define LPC_CPU_CLOCK_CONFIG (*(volatile uint32_t *)0x400FC104u)
#define LPC_CLOCK_SOURCE_SELECT (*(volatile uint32_t *)0x400FC10Cu)

#define LPC_PLL_ENABLE (1u << 0u)
#define LPC_PLL_CONNECT (1u << 1u)
#define LPC_PLL_LOCKED (1u << 26u)
#define LPC_FLASH_TIMING_MASK (0xFu << 12u)
#define LPC_FLASH_TIMING_6_CLOCKS (5u << 12u)

static void mainboard_clock_feed_pll(void)
{
  LPC_PLL0_FEED = 0xAAu;
  LPC_PLL0_FEED = 0x55u;
}

void mainboard_clock_initialize(void)
{
  /*
   * Use the LPC1769's internal 4 MHz oscillator to produce a 480 MHz PLL
   * output (M=60, N=1), then divide it by four for the rated 120 MHz CPU
   * clock. This does not depend on clock state left behind by the BTT
   * bootloader.
   */
  LPC_PLL0_CONTROL = 0u;
  mainboard_clock_feed_pll();

  LPC_CLOCK_SOURCE_SELECT = 0u;
  LPC_PLL0_CONFIG = 59u;
  mainboard_clock_feed_pll();

  LPC_FLASH_CONFIG =
      (LPC_FLASH_CONFIG & ~LPC_FLASH_TIMING_MASK) |
      LPC_FLASH_TIMING_6_CLOCKS;
  LPC_CPU_CLOCK_CONFIG = 3u;

  LPC_PLL0_CONTROL = LPC_PLL_ENABLE;
  mainboard_clock_feed_pll();
  while ((LPC_PLL0_STATUS & LPC_PLL_LOCKED) == 0u)
  {
  }

  LPC_PLL0_CONTROL = LPC_PLL_ENABLE | LPC_PLL_CONNECT;
  mainboard_clock_feed_pll();
}
