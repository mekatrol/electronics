#include <stdbool.h>
#include <stdint.h>

#include "mainboard_uart.h"

#define PINSEL0 (*(volatile uint32_t *)0x4002C000u)
#define PCLKSEL0 (*(volatile uint32_t *)0x400FC1A8u)
#define PCONP (*(volatile uint32_t *)0x400FC0C4u)
#define U0RBR (*(volatile uint32_t *)0x4000C000u)
#define U0THR (*(volatile uint32_t *)0x4000C000u)
#define U0DLL (*(volatile uint32_t *)0x4000C000u)
#define U0DLM (*(volatile uint32_t *)0x4000C004u)
#define U0FCR (*(volatile uint32_t *)0x4000C008u)
#define U0LCR (*(volatile uint32_t *)0x4000C00Cu)
#define U0LSR (*(volatile uint32_t *)0x4000C014u)

#define UART_BUFFER_SIZE (64u)
static uint8_t rx_buffer[UART_BUFFER_SIZE];
static uint8_t tx_buffer[UART_BUFFER_SIZE];
static uint8_t rx_read;
static uint8_t rx_count;
static uint8_t tx_read;
static uint8_t tx_count;

void mainboard_uart_initialize(void)
{
  PCONP |= 1u << 3u;
  PCLKSEL0 = (PCLKSEL0 & ~(3u << 6u)) | (1u << 6u);
  PINSEL0 = (PINSEL0 & ~((3u << 4u) | (3u << 6u))) |
            (1u << 4u) | (1u << 6u);
  U0LCR = 0x83u;
  U0DLL = 65u; /* 120 MHz / (16 * 115200), rounded. */
  U0DLM = 0u;
  U0LCR = 0x03u;
  U0FCR = 0x07u;
}

bool mainboard_uart_write_byte(uint8_t value)
{
  uint8_t index;
  if (tx_count == UART_BUFFER_SIZE)
  {
    return false;
  }
  index = (uint8_t)((tx_read + tx_count) % UART_BUFFER_SIZE);
  tx_buffer[index] = value;
  tx_count++;
  return true;
}

bool mainboard_uart_read_byte(uint8_t *value)
{
  if (rx_count == 0u)
  {
    return false;
  }
  *value = rx_buffer[rx_read];
  rx_read = (uint8_t)((rx_read + 1u) % UART_BUFFER_SIZE);
  rx_count--;
  return true;
}

void mainboard_uart_service(void)
{
  if (((U0LSR & 1u) != 0u) && (rx_count < UART_BUFFER_SIZE))
  {
    uint8_t const index = (uint8_t)((rx_read + rx_count) % UART_BUFFER_SIZE);
    rx_buffer[index] = (uint8_t)U0RBR;
    rx_count++;
  }
  if (((U0LSR & (1u << 5u)) != 0u) && (tx_count != 0u))
  {
    U0THR = tx_buffer[tx_read];
    tx_read = (uint8_t)((tx_read + 1u) % UART_BUFFER_SIZE);
    tx_count--;
  }
}
