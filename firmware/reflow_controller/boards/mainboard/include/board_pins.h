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
  BOARD_DISPLAY_SPI_CLOCK_PIN = LPC_PIN(0u, 15u),
  BOARD_DISPLAY_SPI_MOSI_PIN = LPC_PIN(0u, 18u),
  BOARD_DISPLAY_ENCODER_BUTTON_PIN = LPC_PIN(0u, 28u),
  BOARD_DISPLAY_BEEPER_PIN = LPC_PIN(1u, 30u),
  BOARD_DISPLAY_CHIP_SELECT_PIN = LPC_PIN(1u, 18u),
  BOARD_DISPLAY_DATA_COMMAND_PIN = LPC_PIN(1u, 19u),
  BOARD_DISPLAY_RESET_PIN = LPC_PIN(1u, 20u),
  BOARD_DISPLAY_NEOPIXEL_DATA_PIN = LPC_PIN(1u, 21u),
  BOARD_DISPLAY_SD_DETECT_PIN = LPC_PIN(1u, 31u),
  BOARD_DISPLAY_ENCODER_A_PIN = LPC_PIN(3u, 26u),
  BOARD_DISPLAY_ENCODER_B_PIN = LPC_PIN(3u, 25u),
  BOARD_HEATER_0_PIN = LPC_PIN(2u, 7u),
  BOARD_HEATER_1_PIN = LPC_PIN(2u, 4u),
  BOARD_HEATED_BED_PIN = LPC_PIN(2u, 5u),
  BOARD_FAN_0_PIN = LPC_PIN(2u, 3u),
};

#endif // BTT_SKR_1_4_TURBO_BOARD_PINS_H
