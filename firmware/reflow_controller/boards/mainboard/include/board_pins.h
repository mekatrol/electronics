#ifndef BTT_SKR_1_4_TURBO_BOARD_PINS_H
#define BTT_SKR_1_4_TURBO_BOARD_PINS_H

/*
 * LPC1769 pins are encoded as (port * 32 + bit). These assignments follow the
 * published SKR 1.4 Turbo convention but remain disabled in Phase 1.
 * TODO: verify each signal and its inactive level on the actual controller.
 */
#define LPC_PIN(port, bit) (((port) * 32u) + (bit))

enum
{
  BOARD_HEATER_0_PIN = LPC_PIN(2u, 7u),
  BOARD_HEATER_1_PIN = LPC_PIN(2u, 4u),
  BOARD_HEATED_BED_PIN = LPC_PIN(2u, 5u),
  BOARD_FAN_0_PIN = LPC_PIN(2u, 3u),
};

#endif // BTT_SKR_1_4_TURBO_BOARD_PINS_H
