#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pico/stdlib.h"

#include "../common/communication/serial.h"
#include "../common/memory/memory.h"
#include "../iw_8_controller/pins.h"

// Linker definitions for heap
extern char __StackLimit;
extern size_t __end__;

volatile serial_conf_t serial_conf = {0};

int main()
{
  // Initialize all of the present standard stdio types that are linked into the binary.
  stdio_init_all();

  // Initialise memory before anything else
  memory_init((void *)&__end__, (size_t)&__StackLimit - (size_t)&__end__);

  // Initialise LED pin
  gpio_init(PICO_DEFAULT_LED_PIN);
  gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);

  serial_conf.uart = uart0;
  serial_conf.baud_rate = 115200;
  serial_conf.send_enable_pin = UART0_DE_PIN;
  serial_conf.rx_pin = UART0_RX_PIN;
  serial_conf.tx_pin = UART0_TX_PIN;
  serial_conf.settings = SERIAL_ENABLE_MASK | SERIAL_SEND_ENABLE_SET | SERIAL_FROM_DATA_BITS(8) | SERIAL_FROM_STOP_BITS(1) | SERIAL_TO_PARITY(UART_PARITY_NONE);
  serial_init((serial_conf_t *)&serial_conf);

  while (true)
  {
    uint8_t buffer[32];
    int len = serial_get_rx_data((serial_conf_t *)&serial_conf, buffer, 1);

    if (len > 0)
    {
      buffer[1] = '\r';
      buffer[2] = '\n';

      gpio_put(PICO_DEFAULT_LED_PIN, 1);
      serial_tx_queue_data((serial_conf_t *)&serial_conf, buffer, 3);
      uart_tx_wait_blocking(serial_conf.uart);
      gpio_put(UART0_DE_PIN, 0);
      gpio_put(PICO_DEFAULT_LED_PIN, 0);

      serial_deinit((serial_conf_t *)&serial_conf);
      serial_init((serial_conf_t *)&serial_conf);

      for (int i = 0; i < 100; i++)
      {
        uint8_t *b = (uint8_t *)malloc(8 * 1024);
        int j;
        for (j = 0; j < 26; j++)
        {
          b[j] = 'A' + j;
        }

        b[j++] = '\r';
        b[j++] = '\n';
        b[j++] = '\0';

        gpio_put(PICO_DEFAULT_LED_PIN, 1);
        serial_tx_queue_data((serial_conf_t *)&serial_conf, b, j);
        uart_tx_wait_blocking(serial_conf.uart);
        gpio_put(UART0_DE_PIN, 0);
        gpio_put(PICO_DEFAULT_LED_PIN, 0);

        free(b);
      }
    }
  }
}