#include <stdint.h>

#include "mainboard_display_module.h"

static volatile uint32_t display_module_service_counter;
static volatile uint32_t feedback_service_counter;

void mainboard_display_module_initialize_hardware(void)
{
  /*
   * Phase 1 placeholder. The SKR connector pinout, LCD controller variant,
   * encoder, button, RGB LEDs, and any sounder must be verified before GPIO is
   * configured. This deliberately leaves every panel pin untouched.
   */
}

void mainboard_display_module_run_background_tasks(void)
{
  /*
   * Future bounded work: advance small ST7567 display transfers and scan the
   * encoder/button inputs without blocking the reflow safety tasks.
   */
  display_module_service_counter++;
}

void mainboard_display_module_run_feedback_tasks(void)
{
  /* Future bounded work: service RGB LEDs, backlight, and sounder feedback. */
  feedback_service_counter++;
}
