#include <stdbool.h>
#include <stdint.h>

#include "mainboard_temperature.h"

#define PCONP (*(volatile uint32_t *)0x400FC0C4u)
#define PINSEL1 (*(volatile uint32_t *)0x4002C004u)
#define AD0CR (*(volatile uint32_t *)0x40034000u)
#define AD0GDR (*(volatile uint32_t *)0x40034004u)

static uint16_t samples[3];
static bool valid[3];
static uint8_t active_channel;

void mainboard_temperature_initialize(void)
{
  PCONP |= 1u << 12u;
  /* P0.23..25 functions 01 select AD0.0..2; no pull resistors. */
  PINSEL1 = (PINSEL1 & ~((3u << 14u) | (3u << 16u) | (3u << 18u))) |
            (1u << 14u) | (1u << 16u) | (1u << 18u);
  AD0CR = (1u << 21u) | (14u << 8u) | 1u;
}

void mainboard_temperature_service(void)
{
  if ((AD0GDR & (1u << 31u)) != 0u)
  {
    samples[active_channel] = (uint16_t)((AD0GDR >> 4u) & 0x0FFFu);
    valid[active_channel] = true;
    active_channel = (uint8_t)((active_channel + 1u) % 3u);
    AD0CR = (AD0CR & ~0xFFu) | (1u << active_channel);
  }
  AD0CR = (AD0CR & ~(7u << 24u)) | (1u << 24u);
}

bool mainboard_temperature_read_raw(uint8_t channel, uint16_t *sample)
{
  if ((channel >= 3u) || !valid[channel])
  {
    return false;
  }
  *sample = samples[channel];
  return true;
}
