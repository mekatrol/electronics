#include <stdio.h>

#include "pico/critical_section.h"

#include "hardware/adc.h"
#include "hardware/clocks.h"
#include "hardware/rtc.h"

#include "../common/communication/protocol.h"
#include "../common/rtc/ds1307.h"
#include "../common/storage/flash_w25q128.h"
#include "../common/utils/bcd.h"

#include "74hc595.pio.h"
#include "controller_init.h"
#include "pins.h"
#include "state.h"

PIO shift_register_pio;
uint shift_register_sm;

struct repeating_timer one_sec_timer;

uint8_t datetime_kind = DT_KIND_UNKNOWN;

FlashStorage storage(spi0, SPI0_CS_PIN, SPI0_CLK_PIN, SPI0_RX_PIN, SPI0_TX_PIN);
DS1307 ds1307(i2c1, -1 /* No CS */, I2C1_CLK, I2C1_DAT);
critical_section_t tick_critsec;

bool controller_init_flash_if_needed();
void controller_init_set_default_state();
void controller_init_shift_register();
void controller_init_rtc();
void controller_init_gpio();
void controller_init_timers();

bool controller_flash_is_initialised(uint8_t *page_buf);

bool controller_one_sec_timer_callback(struct repeating_timer *t);

// void inp_irq_callback(uint gpio, uint32_t events);

bool controller_init_startup()
{
#if LIB_PICO_STDIO_USB
  // Initialize USB for stdio
  stdio_usb_init();
#endif

#if LIB_PICO_STDIO_UART
  // Initialize UART1 for stdio (ie for when debugging and cannot use USB)
  stdio_uart_init_full(uart1, 115200, UART1_TX_PIN, UART1_RX_PIN);
#endif

  // Initialise controller state to defaults, will be overridden from
  // any state stored in flash (if flash has been initialised in the past)
  controller_init_set_default_state();

  // Check if flash needs to be initialised
  controller_init_flash_if_needed();

  // Initialise RTC
  controller_init_rtc();

  // Initialise shift register pins and PIO
  controller_init_shift_register();

  // Initialise GPIO
  controller_init_gpio();

  // Initialise timers
  controller_init_timers();

  return true;
}

void controller_init_shift_register()
{
  // Init SPIO program
  shift_register_pio = pio0;
  uint offset = pio_add_program(shift_register_pio, (const pio_program_t *)&shift_register_pio_program);

  // Get available state machine
  shift_register_sm = pio_claim_unused_sm(shift_register_pio, true);

  gpio_init(SHIFT_REG_OE_PIN);
  gpio_set_dir(SHIFT_REG_OE_PIN, GPIO_OUT);
  gpio_put(SHIFT_REG_OE_PIN, 0);

  // Init serial to parallel output PIO
  // data = 0, clock = 1, latch = 2
  sn74hc595_program_init(shift_register_pio, shift_register_sm, offset, SHIFT_REG_CLOCK_PIN, SHIFT_REG_CLOCK_PIN);
  pio_sm_set_enabled(shift_register_pio, shift_register_sm, true);
}

bool controller_init_reset_flash(uint16_t page_addr, uint8_t *page_buf)
{
  // Erase the chip
  storage.ChipErase();

  // Initialise flash marker
  for (uint8_t i = 0; i < FLASH_INIT_MARKER_LEN; i++)
  {
    controller_config.flash.marker[i] = FLASH_INIT_MARKER[i];
  }

  // Initialise flash version
  controller_config.flash.version[0] = FLASH_VERSION[0];
  controller_config.flash.version[1] = FLASH_VERSION[1];
  controller_config.flash.version[2] = FLASH_VERSION[2];
  controller_config.flash.version[3] = FLASH_VERSION[3];

  // Initialise uart0 config
  controller_config.uart_0.addr = 0;
  controller_config.uart_0.baud_rate = 115200;

  // Initialise uart1 config
  controller_config.uart_1.addr = 0;
  controller_config.uart_1.baud_rate = 115200;

  // Fill page buffer with erased value (0xFF)
  for (int i = 0; i < EXT_FLASH_PAGE_SIZE; i++)
  {
    page_buf[i] = 0xFF;
  }

  // Copy to page buf
  memcpy(page_buf, &controller_config, sizeof(controller_config_t));

  // Program the controller config page
  storage.PageProgram(page_addr, page_buf);

  // Re-read the state from first page  from first page
  storage.Read(page_addr, page_buf, EXT_FLASH_PAGE_SIZE);

  if (controller_flash_is_initialised(page_buf))
  {
    // Set flash available flag
    run_state.flags |= RUN_STATE_FLASH_AVAILABLE;
  }
  else
  {
    // Clear flash available flag
    run_state.flags &= ~RUN_STATE_FLASH_AVAILABLE;
  }

  // We needed to initialise the state (though it may have failed)
  return true;
}

void controller_init_set_default_state()
{
  // No outputs are initally overriden
  run_state.outputs.overridden = 0x00000000;

  // All override values are initially 0
  run_state.outputs.override_value = 0x00000000;

  // All outputs are initially off
  // NOTE: on board outputs are 2nd most significant byte
  run_state.outputs.state = 0x00000000;

  // No inputs are initally overriden
  run_state.outputs.overridden = 0x00000000;

  // All override values are initially 0
  run_state.outputs.override_value = 0x00000000;

  // All inputs are initially off
  run_state.outputs.state = 0x00000000;

  // Reset flash manufacture & device IDs
  run_state.flash_id = 0;

  // Clear flash available flag
  run_state.flags &= ~RUN_STATE_FLASH_AVAILABLE;
}

bool controller_init_flash_if_needed()
{
  // Get the device manufacturer ID
  run_state.flash_id = storage.ReadManufacturerId();

  // Read the first page of flash, which holds the controller configuration
  const uint32_t page_addr = 0;
  uint8_t page_buf[EXT_FLASH_PAGE_SIZE];
  storage.Read(page_addr, page_buf, EXT_FLASH_PAGE_SIZE);

  if (controller_flash_is_initialised(page_buf))
  {
    // Set flash available flag
    run_state.flags |= RUN_STATE_FLASH_AVAILABLE;

    // Save to config state
    memcpy(&controller_config, page_buf, sizeof(controller_config_t));

    // Return false to indicate that we did not initialise the flash
    // it was already initialised
    return false;
  }

  return controller_init_reset_flash(page_addr, page_buf);
}

bool controller_flash_is_initialised(uint8_t *page_buf)
{
  // Check if flash signature already set
  for (uint8_t i = 0; i < FLASH_INIT_MARKER_LEN; i++)
  {
    if (page_buf[i] != FLASH_INIT_MARKER[i])
    {
      return false;
    }
  }

  return true;
}

void controller_init_rtc()
{
  // Initialise RTC
  rtc_init();

  uint8_t data[64];
  // ds1307.GetRam(data, 0, 64);

  // Default to Sat 1 Jan 2000
  datetime_t t = {
      .year = 2000,
      .month = 1,
      .day = 1,
      .dotw = 6,
      .hour = 0,
      .min = 0,
      .sec = 0};

  // Only set time if the signature is right.
  // A bad signature means the RTC battery is flat or missing
  if (data[8] == (RTC_INIT_SIGNATURE & 0xFF) && ((data[9] >> 8) & 0XFF) == 0x56)
  {
    // Convert to date / time
    t.year = bcd2bin(data[6]) + 2000U;
    t.month = bcd2bin(data[5]);
    t.day = bcd2bin(data[4]);
    t.hour = bcd2bin(data[2]);
    t.min = bcd2bin(data[1]);
    t.sec = bcd2bin(data[0] & 0x7F);
    t.dotw = data[3];
  }

  // Set PI RTC
  rtc_set_datetime(&t);
}

void controller_init_gpio()
{
  // Analogue inputs
  adc_init();
  adc_gpio_init(ADC0_PIN);
  adc_gpio_init(ADC1_PIN);
  adc_gpio_init(ADC2_PIN);

  // Default PICO LED
  gpio_init(LED_PIN);
  gpio_set_dir(LED_PIN, GPIO_OUT);
  gpio_put(LED_PIN, 0);

  // Digital inputs
  gpio_init(INP1_PIN);
  gpio_pull_up(INP1_PIN);
  gpio_set_dir(INP1_PIN, GPIO_IN);

  gpio_init(INP2_PIN);
  gpio_pull_up(INP2_PIN);
  gpio_set_dir(INP2_PIN, GPIO_IN);

  // // Digital input interrupts
  // gpio_set_irq_callback(&inp_irq_callback);

  // // ISR will trigger on rising and falling edge of pins
  // gpio_set_irq_enabled(INP1_PIN, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true);
  // gpio_set_irq_enabled(INP2_PIN, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true);

  // // Enable IRQ for GPIO bank
  // irq_set_enabled(IO_IRQ_BANK0, true);
}

void controller_init_timers()
{
  add_repeating_timer_ms(
      -1000,                             // Negative value means from start of tick to start of next tick
      controller_one_sec_timer_callback, // The callback method for the timer
      NULL,                              // User data
      &one_sec_timer);                   // The timer struct to store instance data
}

// void inp_irq_callback(uint gpio, uint32_t events)
// {
// }

bool controller_one_sec_timer_callback(struct repeating_timer *t)
{

  return true;
}