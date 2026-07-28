#include <stdint.h>

#include "board_pins.h"
#include "mainboard_clock.h"
#include "mainboard_display_module.h"
#include "mainboard_hal.h"
#include "mainboard_temperature.h"
#include "mainboard_uart.h"
#include "runtime_scheduler.h"
#include "sd_card.h"

static void service_control(void)
{
  mainboard_temperature_service();
}

static void service_communication(void)
{
  uint8_t value;
  mainboard_uart_service();
  /* Diagnostic loopback is bounded to one byte per scheduler pass. */
  if (mainboard_uart_read_byte(&value))
  {
    (void)mainboard_uart_write_byte(value);
  }
}

static void service_storage(void)
{
  sd_card_service();
}

static void service_display(void)
{
  mainboard_display_module_run_background_tasks();
  mainboard_display_module_run_feedback_tasks();
}

static void service_health(void)
{
  if (!mainboard_hal_fault_latched())
  {
    mainboard_hal_feed_watchdog();
  }
}

int main(void)
{
  static runtime_task_t tasks[] = {
      {service_control, 10u, 0u, 1u, true},
      {service_communication, 1u, 0u, 2u, true},
      {service_storage, 10u, 0u, 5u, true},
      {service_display, 250u, 0u, 6u, true},
      {service_health, 100u, 0u, 0u, true},
  };
  runtime_scheduler_t scheduler = {
      tasks, (uint8_t)(sizeof(tasks) / sizeof(tasks[0]))};

  __asm volatile("cpsid i" ::: "memory");
  mainboard_clock_initialize();
  mainboard_hal_initialize_safe_outputs();
  mainboard_hal_initialize_tick();
  mainboard_uart_initialize();
  mainboard_temperature_initialize();
  sd_card_initialize();
  mainboard_display_module_initialize_hardware();
  runtime_scheduler_initialize(&scheduler, mainboard_hal_milliseconds());
  mainboard_hal_initialize_watchdog();
  mainboard_hal_enable_interrupts();

  while (1)
  {
    runtime_scheduler_run_once(&scheduler, mainboard_hal_milliseconds());
  }
}
