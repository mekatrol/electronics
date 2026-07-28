#include <stdint.h>

#include "board_pins.h"
#include "mainboard_display_module.h"

static void mask_interrupts(void)
{
  __asm volatile("cpsid i" ::: "memory");
}

int main(void)
{
  /*
   * Phase 1 is intentionally inert. Do not configure or drive an oven output
   * until reset-state polarity and the SKR pin map have passed bench review.
   */
  mask_interrupts();

  (void)BOARD_HEATER_0_PIN;
  (void)BOARD_HEATER_1_PIN;
  (void)BOARD_HEATED_BED_PIN;

  mainboard_display_module_initialize_hardware();

  while (1)
  {
    mainboard_display_module_run_background_tasks();
    mainboard_display_module_run_feedback_tasks();
  }
}
