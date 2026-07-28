#include <stdbool.h>
#include <stdint.h>

#include "mainboard_gpio.h"

#define LPC_PIN_CONNECT_BASE_ADDRESS (0x4002C000u)
#define LPC_FAST_GPIO_BASE_ADDRESS (0x2009C000u)
#define LPC_FAST_GPIO_PORT_STRIDE_BYTES (0x20u)
#define LPC_FAST_GPIO_DIRECTION_OFFSET (0x00u)
#define LPC_FAST_GPIO_PIN_OFFSET (0x14u)
#define LPC_FAST_GPIO_SET_OFFSET (0x18u)
#define LPC_FAST_GPIO_CLEAR_OFFSET (0x1Cu)

static uint32_t pin_port(uint32_t pin);
static uint32_t pin_bit(uint32_t pin);

static volatile uint32_t *register_at(uint32_t address)
{
  return (volatile uint32_t *)address;
}

void mainboard_gpio_configure_input(uint32_t pin, bool pull_up)
{
  uint32_t const port = pin_port(pin);
  uint32_t const bit = pin_bit(pin);
  uint32_t const select_index = pin / 16u;
  uint32_t const select_shift = (pin % 16u) * 2u;
  uint32_t const mode_index = pin / 16u;
  uint32_t const mode_shift = (pin % 16u) * 2u;
  uint32_t const port_address =
      LPC_FAST_GPIO_BASE_ADDRESS + (port * LPC_FAST_GPIO_PORT_STRIDE_BYTES);
  volatile uint32_t *const select =
      register_at(LPC_PIN_CONNECT_BASE_ADDRESS + (select_index * 4u));
  volatile uint32_t *const mode =
      register_at(LPC_PIN_CONNECT_BASE_ADDRESS + 0x40u + (mode_index * 4u));
  volatile uint32_t *const direction =
      register_at(port_address + LPC_FAST_GPIO_DIRECTION_OFFSET);

  *select &= ~(3u << select_shift);
  *direction &= ~(1u << bit);
  *mode = (*mode & ~(3u << mode_shift)) |
          ((pull_up ? 0u : 2u) << mode_shift);
}

bool mainboard_gpio_read(uint32_t pin)
{
  uint32_t const port_address =
      LPC_FAST_GPIO_BASE_ADDRESS +
      (pin_port(pin) * LPC_FAST_GPIO_PORT_STRIDE_BYTES);
  return ((*register_at(port_address + LPC_FAST_GPIO_PIN_OFFSET)) &
          (1u << pin_bit(pin))) != 0u;
}

static uint32_t pin_port(uint32_t pin)
{
  return pin / 32u;
}

static uint32_t pin_bit(uint32_t pin)
{
  return pin % 32u;
}

void mainboard_gpio_configure_output(uint32_t pin, bool initial_high)
{
  uint32_t const port = pin_port(pin);
  uint32_t const bit = pin_bit(pin);
  uint32_t const pin_select_index = pin / 16u;
  uint32_t const pin_select_shift = (pin % 16u) * 2u;
  uint32_t const port_address =
      LPC_FAST_GPIO_BASE_ADDRESS + (port * LPC_FAST_GPIO_PORT_STRIDE_BYTES);
  volatile uint32_t *const pin_select =
      register_at(LPC_PIN_CONNECT_BASE_ADDRESS + (pin_select_index * 4u));
  volatile uint32_t *const direction =
      register_at(port_address + LPC_FAST_GPIO_DIRECTION_OFFSET);

  /*
   * Select GPIO function 00 before enabling the output. Establish the desired
   * latch level first so chip-select and reset do not glitch active.
   */
  *pin_select &= ~(3u << pin_select_shift);
  mainboard_gpio_write(pin, initial_high);
  *direction |= 1u << bit;
}

void mainboard_gpio_write(uint32_t pin, bool high)
{
  uint32_t const port_address =
      LPC_FAST_GPIO_BASE_ADDRESS +
      (pin_port(pin) * LPC_FAST_GPIO_PORT_STRIDE_BYTES);
  uint32_t const output_offset =
      high ? LPC_FAST_GPIO_SET_OFFSET : LPC_FAST_GPIO_CLEAR_OFFSET;

  *register_at(port_address + output_offset) = 1u << pin_bit(pin);
}
