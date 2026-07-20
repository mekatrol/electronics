#include <string.h>
#include <stdlib.h>

#include "pico/critical_section.h"

#include "hardware/uart.h"

#include "../utils/io.h"

#include "serial.h"

#define UART_BUFFER_SIZE 1024

#define UART_STATE_INITIALISED_MASK 1U << 31U

#define UART_IRQ_NUM_MASK 0xFF
#define SERIAL_STATE_TO_IRQ_NUMBER(v) (v & UART_IRQ_NUM_MASK)
#define SERIAL_STATE_FROM_IRQ_NUMBER(s, v) ((s & ~UART_IRQ_NUM_MASK) | (v & UART_IRQ_NUM_MASK))

typedef struct
{
  uint settings;
  /// @brief Flags that can be used from interrupts so that critical
  ///        sections are not always needed, only the interrupt handlers
  ///        set the flags, and only critical sections clear flags
  uint flags;
  uint16_t rx_head;
  uint16_t rx_tail;
  uint16_t tx_head;
  uint16_t tx_tail;
  uint8_t *rx_buffer;
  uint8_t *tx_buffer;
  critical_section_t critsec;
  irq_handler_t irq_handler;
  serial_conf_t conf;
} uart_state_t;

static volatile uart_state_t uart0_state;
static volatile uart_state_t uart1_state;

#define SERIAL_FLAG_UART_RX_DATA_AVAIL 0x00000001
#define SERIAL_FLAG_UART_TX_DATA_EMPTY 0x00000002

static inline void serial_set_send_enable(serial_conf_t *conf, bool state)
{
  uint8_t send_enable_state = SERIAL_TO_SEND_ENABLE(conf->settings);
  bool invert = !send_enable_state;

  set_io(conf->send_enable_pin, state, invert);
}

static void inline serial_init_state(uart_state_t *state)
{
  // Setup UART with configured baud rate
  uart_init(state->conf.uart, state->conf.baud_rate);

  // Set the TX and RX pins
  gpio_set_function(state->conf.tx_pin, GPIO_FUNC_UART);
  gpio_set_function(state->conf.rx_pin, GPIO_FUNC_UART);

  if (state->conf.send_enable_pin >= 0)
  {
    gpio_init(state->conf.send_enable_pin);
    gpio_set_dir(state->conf.send_enable_pin, GPIO_OUT);
    serial_set_send_enable(&state->conf, false);
  }

  // Disable UART flow control CTS/RTS
  uart_set_hw_flow(state->conf.uart, false, false);

  // Turn off FIFOs (will tx/rx byte by byte from IRQ handler)
  uart_set_fifo_enabled(state->conf.uart, false);

  // Set data format
  uart_set_format(state->conf.uart,
                  SERIAL_TO_DATA_BITS(state->conf.settings),
                  SERIAL_TO_STOP_BITS(state->conf.settings),
                  SERIAL_TO_PARITY(state->conf.settings));

  // UART instance based
  irq_set_exclusive_handler(SERIAL_STATE_TO_IRQ_NUMBER(state->settings), state->irq_handler);
  state->rx_buffer = (uint8_t *)malloc(UART_BUFFER_SIZE);
  state->tx_buffer = (uint8_t *)malloc(UART_BUFFER_SIZE);
  state->rx_head = 0;
  state->rx_tail = 0;
  state->tx_head = 0;
  state->tx_tail = 0;
  memset((void *)state->rx_buffer, 0, UART_BUFFER_SIZE);
  memset((void *)state->tx_buffer, 0, UART_BUFFER_SIZE);
  critical_section_init(&state->critsec);

  // Enable the UART interrupt
  irq_set_enabled(SERIAL_STATE_TO_IRQ_NUMBER(state->settings), true);

  // Set which UART events to raise interrupts for
  uart_set_irq_enables(state->conf.uart, true, true);
}

static inline void on_uart_irq(volatile uart_state_t *state)
{
  // Get UART interrupt status register
  io_rw_32 ris = uart_get_hw(state->conf.uart)->ris;
  // io_rw_32 imsc = uart_get_hw(state->conf.uart)->imsc;

  // On UART I/O initialisation these errors might occur as external hardware stabilises
  if (ris & (UART_UARTIMSC_FEIM_BITS | UART_UARTIMSC_PEIM_BITS | UART_UARTIMSC_BEIM_BITS | UART_UARTIMSC_OEIM_BITS))
  {
    // Clear errors (frame, parity, break and overflow)
    uart_get_hw(state->conf.uart)->icr = UART_UARTIMSC_FEIM_BITS | UART_UARTIMSC_PEIM_BITS | UART_UARTIMSC_BEIM_BITS | UART_UARTIMSC_OEIM_BITS;

    while (uart_is_readable(state->conf.uart))
    {
      uart_get_hw(state->conf.uart)->dr;
    }

    return;
  }

  // TX empty status bit set?
  if (ris & UART_UARTRIS_TXRIS_BITS)
  {
    // 4.2.6.3. UARTTXINTR
    // The transmit interrupt changes state when one of the following events occurs:
    // • If the FIFOs are enabled and the transmit FIFO is equal to or lower than the programmed trigger level then the
    //   transmit interrupt is asserted HIGH. The transmit interrupt is cleared by writing data to the transmit FIFO until it
    //   becomes greater than the trigger level, or by clearing the interrupt.
    // • If the FIFOs are disabled (have a depth of one location) and there is no data present in the transmitters single
    //   location, the transmit interrupt is asserted HIGH. It is cleared by performing a single write to the transmit FIFO, or
    //   by clearing the interrupt.
    // To update the transmit FIFO you must:
    // • Write data to the transmit FIFO, either prior to enabling the UART and the interrupts, or after enabling the UART and
    //   interrupts.

    // Can stop further TX empty interrupts
    // uart_get_hw(state->conf.uart)->imsc &= ~UART_UARTIMSC_TXIM_BITS;

    // Clear TX empty status bit
    uart_get_hw(state->conf.uart)->icr = UART_UARTIMSC_TXIM_BITS;

    if (state->tx_tail != state->tx_head)
    {
      // Flag TX not empty
      state->flags &= ~SERIAL_FLAG_UART_TX_DATA_EMPTY;

      if (state->conf.send_enable_pin >= 0)
      {
        serial_set_send_enable(&((uart_state_t *)state)->conf, true);
      }

      // Does TX FIFO have capacity and we have bytes to transmit?
      while (uart_is_writable(state->conf.uart) && state->tx_tail != state->tx_head)
      {
        // Write byte
        uart_putc(state->conf.uart, state->tx_buffer[state->tx_tail]);

        if (++state->tx_tail == UART_BUFFER_SIZE)
        {
          state->tx_tail = 0;
        }
      }
    }
    else
    {
      // Flag TX empty
      state->flags |= SERIAL_FLAG_UART_TX_DATA_EMPTY;

      // Stop further interrupts until we transmit something again
      uart_get_hw(state->conf.uart)->imsc &= ~UART_UARTIMSC_TXIM_BITS;
    }
  }

  // RX empty bit set?
  if (ris & UART_UARTRIS_RXRIS_BITS)
  {
    // 4.2.6.2. UARTRXINTR
    // The receive interrupt changes state when one of the following events occurs:
    // • If the FIFOs are enabled and the receive FIFO reaches the programmed trigger level. When this happens, the
    //   receive interrupt is asserted HIGH. The receive interrupt is cleared by reading data from the receive FIFO until it
    //   becomes less than the trigger level, or by clearing the interrupt.
    // • If the FIFOs are disabled (have a depth of one location) and data is received thereby filling the location, the receive
    //   interrupt is asserted HIGH. The receive interrupt is cleared by performing a single read of the receive FIFO, or by
    //   clearing the interrupt.

    // Can stop further RX timeout interrupts
    // uart_get_hw(state->conf.uart)->imsc &= ~UART_UARTIMSC_RXIM_BITS;

    while (uart_is_readable(state->conf.uart))
    {
      uint8_t ch = uart_getc(state->conf.uart);

      // Update status bits for the character just read
      io_rw_32 rsr = uart_get_hw(state->conf.uart)->rsr;

      // Do not queue bytes that had errors
      if (rsr & UART_UARTRSR_BITS)
      {
        continue;
      }

      state->rx_buffer[state->rx_head++] = ch;

      if (state->rx_head >= UART_BUFFER_SIZE)
      {
        state->rx_head = 0;
      }

      if (state->rx_head == state->rx_tail)
      {
        // Buffer overflow!
        state->rx_tail++;

        if (state->rx_tail >= UART_BUFFER_SIZE)
        {
          state->rx_tail = 0;
        }
      }

      if (state->rx_head != state->rx_tail)
      {
        state->flags |= SERIAL_FLAG_UART_RX_DATA_AVAIL;
      }
    }
  }

  // RX timeout bit set?
  if (ris & UART_UARTRIS_RTRIS_BITS)
  {
    // 4.2.6.4. UARTRTINTR
    // The receive timeout interrupt is asserted when the receive FIFO is not empty, and no more data is received during a 32-
    // bit period. The receive timeout interrupt is cleared either when the FIFO becomes empty through reading all the data (or
    // by reading the holding register), or when a 1 is written to the corresponding bit of the Interrupt Clear Register, UARTICR.

    // Can stop further RX timeout interrupts
    // uart_get_hw(state->conf.uart)->imsc &= ~UART_UARTIMSC_RTIM_BITS;
  }
}

static inline uart_state_t *serial_get_state(serial_conf_t *serial_conf)
{
  if (serial_conf->uart == uart0)
  {
    return (uart_state_t *)&uart0_state;
  }

  return (uart_state_t *)&uart1_state;
}

static void on_uart0_irq()
{
  on_uart_irq(&uart0_state);
}

static void on_uart1_irq()
{
  on_uart_irq(&uart1_state);
}

void serial_init(serial_conf_t *serial_conf)
{
  // Get state associated with conf
  uart_state_t *state = serial_get_state(serial_conf);

  // Only init if not already initialised
  if ((state->settings & UART_STATE_INITIALISED_MASK) != 0)
  {
    return;
  }

  // Flag as initialised
  state->settings |= UART_STATE_INITIALISED_MASK;

  // Copy configuration
  memcpy((void *)&state->conf, serial_conf, sizeof(serial_conf_t));

  // UART specific state mangement
  if (serial_conf->uart == uart0)
  {
    state->settings = SERIAL_STATE_FROM_IRQ_NUMBER(state->settings, UART0_IRQ);
    state->irq_handler = on_uart0_irq;
  }
  else
  {
    state->settings = SERIAL_STATE_FROM_IRQ_NUMBER(state->settings, UART1_IRQ);
    state->irq_handler = on_uart1_irq;
  }

  // Initialise the state
  serial_init_state(state);
}

void serial_deinit(serial_conf_t *serial_conf)
{
  // Get state associated with conf
  uart_state_t *state = serial_get_state(serial_conf);

  // Only deinit if initialised
  if ((state->settings & UART_STATE_INITIALISED_MASK) == 0)
  {
    return;
  }

  // Disable interrupts
  uart_set_irq_enables(state->conf.uart, false, false);
  irq_set_enabled(SERIAL_STATE_TO_IRQ_NUMBER(state->settings), false);

  // De-initialise the UART
  uart_deinit(state->conf.uart);

  // Release critical section
  critical_section_deinit(&state->critsec);

  // Free memory
  free(state->rx_buffer);
  free(state->tx_buffer);

  // Clear initialisaed flag
  state->settings &= ~UART_STATE_INITIALISED_MASK;
}

uint serial_get_rx_waiting_count(serial_conf_t *conf)
{
  // Get state associated with conf
  uart_state_t *state = serial_get_state(conf);

  uint bytes_rxed = 0;

  critical_section_enter_blocking(&state->critsec);

  if (state->rx_head > state->rx_tail)
  {
    bytes_rxed = state->rx_head - state->rx_tail;
  }
  else if (state->rx_head < state->rx_tail)
  {
    bytes_rxed = (UART_BUFFER_SIZE - state->rx_head) + state->rx_tail;
  }

  critical_section_exit(&state->critsec);

  return bytes_rxed;
}

int serial_get_rx_data(serial_conf_t *serial_conf, uint8_t *buffer, uint16_t max_len)
{
  // Get state associated with conf
  uart_state_t *state = serial_get_state(serial_conf);

  uint count = 0;

  critical_section_enter_blocking(&state->critsec);

  while (state->rx_tail != state->rx_head && count < max_len)
  {
    buffer[count++] = state->rx_buffer[state->rx_tail];

    if (++state->rx_tail == UART_BUFFER_SIZE)
    {
      state->rx_tail = 0;
    }
  }

  // Clear rx data available if not data remaining
  if (state->rx_tail == state->rx_head)
  {
    state->flags &= ~SERIAL_FLAG_UART_RX_DATA_AVAIL;
  }

  critical_section_exit(&state->critsec);

  return count;
}

bool serial_has_rx_data(serial_conf_t *serial_conf)
{
  // Get state associated with conf
  uart_state_t *state = serial_get_state(serial_conf);

  return (state->flags & SERIAL_FLAG_UART_RX_DATA_AVAIL) != 0;
}

bool serial_tx_empty(serial_conf_t *serial_conf)
{
  // Get state associated with conf
  uart_state_t *state = serial_get_state(serial_conf);

  // If there is data in the TX buffer then TX not empty
  if (state->tx_head != state->tx_tail)
  {
    return true;
  }

  // Return true if all UART FIFO bytes have been sent (or the last byte is being sent)
  return (state->flags & SERIAL_FLAG_UART_TX_DATA_EMPTY) != 0;
}

void serial_prime_tx(uart_state_t *state)
{
  // Enable the TX empty interrupt flag (will trigger empty interrupt to send byte)
  uart_get_hw(state->conf.uart)->imsc |= UART_UARTIMSC_TXIM_BITS;

  critical_section_enter_blocking(&state->critsec);

  // If data register empty then put data in it
  if (!(uart_get_hw(state->conf.uart)->fr & UART_UARTFR_BUSY_BITS) &&
      state->tx_tail != state->tx_head)
  {
    serial_set_send_enable(&state->conf, true);

    uart_get_hw(state->conf.uart)->dr = state->tx_buffer[state->tx_tail];

    if (++state->tx_tail == UART_BUFFER_SIZE)
    {
      state->tx_tail = 0;
    }
  }

  critical_section_exit(&state->critsec);
}

uint serial_tx_queue_data(serial_conf_t *serial_conf, uint8_t *buffer, uint16_t len)
{
  // Get state associated with conf
  uart_state_t *state = serial_get_state(serial_conf);

  int i;

  critical_section_enter_blocking(&state->critsec);

  for (i = 0; i < len; i++)
  {
    state->tx_buffer[state->tx_head] = buffer[i];

    if (++state->tx_head == UART_BUFFER_SIZE)
    {
      state->tx_head = 0;
    }

    if (state->tx_head == state->tx_tail)
    {
      // We have reached tail, this is a buffer overrun
      break;
    }
  }

  critical_section_exit(&state->critsec);

  // Make sure TX interrupt enable and prime data register if empty
  serial_prime_tx(state);

  return i;
}