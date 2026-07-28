#include <stdbool.h>
#include <stdint.h>

#include "mainboard_gpio.h"
#include "mainboard_neopixel.h"

#define LPC_FAST_GPIO_BASE_ADDRESS (0x2009C000u)
#define LPC_FAST_GPIO_PORT_STRIDE_BYTES (0x20u)
#define LPC_FAST_GPIO_SET_OFFSET (0x18u)
#define LPC_FAST_GPIO_CLEAR_OFFSET (0x1Cu)

#define NEOPIXEL_ZERO_HIGH_CYCLES (42u)
#define NEOPIXEL_ONE_HIGH_CYCLES (84u)
#define NEOPIXEL_ZERO_LOW_CYCLES (84u)
#define NEOPIXEL_ONE_LOW_CYCLES (42u)
#define NEOPIXEL_LATCH_DELAY_LOOPS (12000u)

static void delay_cycles(volatile uint32_t cycles)
{
  while (cycles-- != 0u)
  {
    __asm volatile("nop");
    __asm volatile("" ::: "memory");
  }
}

static void write_bit(volatile uint32_t *set_register,
                      volatile uint32_t *clear_register,
                      uint32_t mask,
                      bool one)
{
  *set_register = mask;
  delay_cycles(one ? NEOPIXEL_ONE_HIGH_CYCLES
                   : NEOPIXEL_ZERO_HIGH_CYCLES);
  *clear_register = mask;
  delay_cycles(one ? NEOPIXEL_ONE_LOW_CYCLES
                   : NEOPIXEL_ZERO_LOW_CYCLES);
}

static void write_byte(volatile uint32_t *set_register,
                       volatile uint32_t *clear_register,
                       uint32_t mask,
                       uint8_t value)
{
  for (uint32_t bit = 0u; bit < 8u; bit++)
  {
    write_bit(set_register,
              clear_register,
              mask,
              (value & 0x80u) != 0u);
    value <<= 1u;
  }
}

void mainboard_neopixel_write_rgb_chain(uint32_t pin,
                                        uint8_t red,
                                        uint8_t green,
                                        uint8_t blue,
                                        uint32_t pixel_count)
{
  uint32_t const port = pin / 32u;
  uint32_t const mask = 1u << (pin % 32u);
  uint32_t const port_address =
      LPC_FAST_GPIO_BASE_ADDRESS + (port * LPC_FAST_GPIO_PORT_STRIDE_BYTES);
  volatile uint32_t *const set_register =
      (volatile uint32_t *)(port_address + LPC_FAST_GPIO_SET_OFFSET);
  volatile uint32_t *const clear_register =
      (volatile uint32_t *)(port_address + LPC_FAST_GPIO_CLEAR_OFFSET);

  mainboard_gpio_configure_output(pin, false);
  delay_cycles(NEOPIXEL_LATCH_DELAY_LOOPS);

  for (uint32_t pixel = 0u; pixel < pixel_count; pixel++)
  {
    /* BTT Mini 12864 V1.0 NeoPixels receive bytes in GRB order. */
    write_byte(set_register, clear_register, mask, green);
    write_byte(set_register, clear_register, mask, red);
    write_byte(set_register, clear_register, mask, blue);
  }

  delay_cycles(NEOPIXEL_LATCH_DELAY_LOOPS);
}
