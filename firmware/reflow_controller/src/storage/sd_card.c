#include <stdbool.h>
#include <stdint.h>

#include "board_pins.h"
#include "mainboard_gpio.h"
#include "mainboard_spi.h"
#include "sd_card.h"

#define SD_BLOCK_SIZE (512u)
#define SD_RESPONSE_ATTEMPTS (16u)

static sd_card_state_t state;
static uint8_t initialization_step;
static bool high_capacity;

static uint8_t command(uint8_t index, uint32_t argument, uint8_t crc)
{
  uint8_t response = 0xFFu;
  mainboard_gpio_write(BOARD_SD_CHIP_SELECT_PIN, false);
  (void)mainboard_spi_transfer((uint8_t)(0x40u | index));
  (void)mainboard_spi_transfer((uint8_t)(argument >> 24u));
  (void)mainboard_spi_transfer((uint8_t)(argument >> 16u));
  (void)mainboard_spi_transfer((uint8_t)(argument >> 8u));
  (void)mainboard_spi_transfer((uint8_t)argument);
  (void)mainboard_spi_transfer(crc);
  for (uint8_t attempt = 0u; attempt < SD_RESPONSE_ATTEMPTS; attempt++)
  {
    response = mainboard_spi_transfer(0xFFu);
    if ((response & 0x80u) == 0u)
    {
      break;
    }
  }
  return response;
}

static void deselect(void)
{
  mainboard_gpio_write(BOARD_SD_CHIP_SELECT_PIN, true);
  (void)mainboard_spi_transfer(0xFFu);
}

void sd_card_initialize(void)
{
  mainboard_gpio_configure_output(BOARD_SD_CHIP_SELECT_PIN, true);
  mainboard_gpio_configure_input(BOARD_SD_DETECT_PIN, true);
  mainboard_spi_initialize_sd();
  state = SD_CARD_INITIALIZING;
  initialization_step = 0u;
  high_capacity = false;
}

void sd_card_service(void)
{
  uint8_t response;
  if (state != SD_CARD_INITIALIZING)
  {
    return;
  }
  if (initialization_step == 0u)
  {
    for (uint8_t index = 0u; index < 10u; index++)
    {
      (void)mainboard_spi_transfer(0xFFu);
    }
    initialization_step++;
    return;
  }
  if (initialization_step == 1u)
  {
    response = command(0u, 0u, 0x95u);
    deselect();
    if (response != 1u)
    {
      state = SD_CARD_ERROR;
      return;
    }
    initialization_step++;
    return;
  }
  if (initialization_step == 2u)
  {
    response = command(8u, 0x1AAu, 0x87u);
    if (response == 1u)
    {
      uint32_t reply = 0u;
      for (uint8_t index = 0u; index < 4u; index++)
      {
        reply = (reply << 8u) | mainboard_spi_transfer(0xFFu);
      }
      if ((reply & 0xFFFu) != 0x1AAu)
      {
        state = SD_CARD_ERROR;
      }
    }
    deselect();
    initialization_step++;
    return;
  }
  response = command(55u, 0u, 0x01u);
  deselect();
  if (response > 1u)
  {
    state = SD_CARD_ERROR;
    return;
  }
  response = command(41u, 0x40000000u, 0x01u);
  deselect();
  if (response == 0u)
  {
    high_capacity = true;
    mainboard_spi_set_slow(false);
    state = SD_CARD_READY;
  }
}

sd_card_state_t sd_card_state(void)
{
  return state;
}

bool sd_card_read_block(uint32_t block, uint8_t *destination)
{
  uint16_t timeout = 0xFFFFu;
  if (state != SD_CARD_READY)
  {
    return false;
  }
  if (command(17u, high_capacity ? block : block * SD_BLOCK_SIZE, 0x01u) != 0u)
  {
    deselect();
    return false;
  }
  while ((mainboard_spi_transfer(0xFFu) != 0xFEu) && (--timeout != 0u))
  {
  }
  if (timeout == 0u)
  {
    deselect();
    return false;
  }
  for (uint16_t index = 0u; index < SD_BLOCK_SIZE; index++)
  {
    destination[index] = mainboard_spi_transfer(0xFFu);
  }
  (void)mainboard_spi_transfer(0xFFu);
  (void)mainboard_spi_transfer(0xFFu);
  deselect();
  return true;
}
