#include <stdbool.h>
#include <stdint.h>

#include "mainboard_spi.h"

#define PCONP (*(volatile uint32_t *)0x400FC0C4u)
#define PCLKSEL0 (*(volatile uint32_t *)0x400FC1A8u)
#define PINSEL0 (*(volatile uint32_t *)0x4002C000u)
#define SSP1CR0 (*(volatile uint32_t *)0x40030000u)
#define SSP1DR (*(volatile uint32_t *)0x40030008u)
#define SSP1SR (*(volatile uint32_t *)0x4003000Cu)
#define SSP1CPSR (*(volatile uint32_t *)0x40030010u)
#define SSP1CR1 (*(volatile uint32_t *)0x40030004u)

void mainboard_spi_initialize_sd(void)
{
  PCONP |= 1u << 10u;
  PCLKSEL0 = (PCLKSEL0 & ~(3u << 20u)) | (1u << 20u);
  PINSEL0 = (PINSEL0 & ~((3u << 14u) | (3u << 16u) | (3u << 18u))) |
            (2u << 14u) | (2u << 16u) | (2u << 18u);
  SSP1CR0 = 7u;
  SSP1CPSR = 150u; /* 400 kHz card initialization clock. */
  SSP1CR1 = 2u;
}

void mainboard_spi_set_slow(bool slow)
{
  SSP1CPSR = slow ? 150u : 4u; /* 400 kHz or 15 MHz. */
}

uint8_t mainboard_spi_transfer(uint8_t value)
{
  while ((SSP1SR & (1u << 1u)) == 0u)
  {
  }
  SSP1DR = value;
  while ((SSP1SR & (1u << 2u)) == 0u)
  {
  }
  return (uint8_t)SSP1DR;
}
