#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "board_pins.h"
#include "mainboard_display_module.h"
#include "mainboard_gpio.h"
#include "mainboard_neopixel.h"

#define DISPLAY_WIDTH_PIXELS (128u)
#define DISPLAY_PAGE_COUNT (8u)
#define DISPLAY_GLYPH_WIDTH_PIXELS (5u)
#define DISPLAY_CHARACTER_ADVANCE_PIXELS (6u)

typedef struct
{
  char character;
  uint8_t columns[DISPLAY_GLYPH_WIDTH_PIXELS];
} display_glyph_t;

static display_glyph_t const display_glyphs[] = {
    {' ', {0x00u, 0x00u, 0x00u, 0x00u, 0x00u}},
    {'A', {0x7Eu, 0x11u, 0x11u, 0x11u, 0x7Eu}},
    {'C', {0x3Eu, 0x41u, 0x41u, 0x41u, 0x22u}},
    {'D', {0x7Fu, 0x41u, 0x41u, 0x22u, 0x1Cu}},
    {'E', {0x7Fu, 0x49u, 0x49u, 0x49u, 0x41u}},
    {'F', {0x7Fu, 0x09u, 0x09u, 0x09u, 0x01u}},
    {'I', {0x00u, 0x41u, 0x7Fu, 0x41u, 0x00u}},
    {'L', {0x7Fu, 0x40u, 0x40u, 0x40u, 0x40u}},
    {'N', {0x7Fu, 0x02u, 0x04u, 0x08u, 0x7Fu}},
    {'O', {0x3Eu, 0x41u, 0x41u, 0x41u, 0x3Eu}},
    {'P', {0x7Fu, 0x09u, 0x09u, 0x09u, 0x06u}},
    {'R', {0x7Fu, 0x09u, 0x19u, 0x29u, 0x46u}},
    {'S', {0x46u, 0x49u, 0x49u, 0x49u, 0x31u}},
    {'T', {0x01u, 0x01u, 0x7Fu, 0x01u, 0x01u}},
    {'W', {0x3Fu, 0x40u, 0x38u, 0x40u, 0x3Fu}},
    {'Y', {0x07u, 0x08u, 0x70u, 0x08u, 0x07u}},
};

static void display_delay(void)
{
  /*
   * This deliberately conservative busy wait is used only during Phase 1
   * initialization, before the Phase 2 monotonic timer exists.
   */
  for (volatile uint32_t count = 0u; count < 2000000u; count++)
  {
    __asm volatile("nop");
  }
}

static void display_bus_delay(void)
{
  for (volatile uint32_t count = 0u; count < 12u; count++)
  {
    __asm volatile("nop");
  }
}

static void display_select(void)
{
  /* Marlin establishes the mode-3 idle level before asserting CS. */
  mainboard_gpio_write(BOARD_DISPLAY_SPI_CLOCK_PIN, true);
  mainboard_gpio_write(BOARD_DISPLAY_CHIP_SELECT_PIN, false);
}

static void display_deselect(void)
{
  mainboard_gpio_write(BOARD_DISPLAY_CHIP_SELECT_PIN, true);
  /* Return the shared EXP clock to its mode-0 idle level. */
  mainboard_gpio_write(BOARD_DISPLAY_SPI_CLOCK_PIN, false);
}

static void display_write_selected_byte(bool is_data, uint8_t value)
{
  mainboard_gpio_write(BOARD_DISPLAY_DATA_COMMAND_PIN, is_data);

  /* BTT/FYSETC Mini 12864 requires software SPI mode 3. */
  for (uint32_t bit = 0u; bit < 8u; bit++)
  {
    bool const high = (value & 0x80u) != 0u;

    mainboard_gpio_write(BOARD_DISPLAY_SPI_CLOCK_PIN, false);
    display_bus_delay();
    mainboard_gpio_write(BOARD_DISPLAY_SPI_MOSI_PIN, high);
    display_bus_delay();
    mainboard_gpio_write(BOARD_DISPLAY_SPI_CLOCK_PIN, true);
    display_bus_delay();
    value <<= 1u;
  }
}

static void display_write_data(uint8_t data)
{
  display_write_selected_byte(true, data);
}

static uint8_t display_glyph_column(char character, uint32_t column)
{
  for (size_t index = 0u;
       index < (sizeof(display_glyphs) / sizeof(display_glyphs[0]));
       index++)
  {
    if (display_glyphs[index].character == character)
    {
      return display_glyphs[index].columns[column];
    }
  }

  return 0u;
}

static void display_write_text_page(uint8_t page,
                                    uint8_t start_column,
                                    char const *text,
                                    bool inverted)
{
  uint32_t current_column = 0u;
  size_t text_length = 0u;

  while (text[text_length] != '\0')
  {
    text_length++;
  }

  /*
   * This is Marlin's Mini 12864 data-start sequence. These modules need the
   * controller setup refreshed before each page, particularly after startup.
   */
  display_select();
  display_write_selected_byte(false, 0x40u);
  display_write_selected_byte(false, 0xA0u);
  display_write_selected_byte(false, 0xC8u);
  display_write_selected_byte(false, 0xA6u);
  display_write_selected_byte(false, 0xA2u);
  display_write_selected_byte(false, 0x2Fu);
  display_write_selected_byte(false, 0xF8u);
  display_write_selected_byte(false, 0x00u);
  display_write_selected_byte(false, 0x23u);
  display_write_selected_byte(false, 0xACu);
  display_write_selected_byte(false, 0x00u);
  display_write_selected_byte(false, 0xAFu);
  display_write_selected_byte(false, 0x10u);
  display_write_selected_byte(false, (uint8_t)(0xB0u | page));
  display_write_selected_byte(false, 0x00u);

  while (current_column < DISPLAY_WIDTH_PIXELS)
  {
    uint8_t output = inverted ? 0xFFu : 0x00u;

    if (current_column >= start_column)
    {
      uint32_t const text_column = current_column - start_column;
      uint32_t const character_index =
          text_column / DISPLAY_CHARACTER_ADVANCE_PIXELS;
      uint32_t const glyph_column =
          text_column % DISPLAY_CHARACTER_ADVANCE_PIXELS;

      if ((character_index < text_length) &&
          (glyph_column < DISPLAY_GLYPH_WIDTH_PIXELS))
      {
        uint8_t const glyph =
            display_glyph_column(text[character_index], glyph_column);
        output = inverted ? (uint8_t)~glyph : glyph;
      }
    }

    display_write_data(output);
    current_column++;
  }

  display_deselect();
}

static void display_render_test_screen(void)
{
  for (uint8_t page = 0u; page < DISPLAY_PAGE_COUNT; page++)
  {
    if (page == 2u)
    {
      display_write_text_page(page, 16u, "REFLOW CONTROLLER", true);
    }
    else if (page == 4u)
    {
      display_write_text_page(page, 28u, "DISPLAY READY", true);
    }
    else
    {
      display_write_text_page(page, 0u, "", false);
    }
  }
}

void mainboard_display_module_initialize_hardware(void)
{
  mainboard_neopixel_write_rgb_chain(BOARD_DISPLAY_NEOPIXEL_DATA_PIN,
                                    32u,
                                    32u,
                                    32u,
                                    3u);

  mainboard_gpio_configure_output(BOARD_DISPLAY_CHIP_SELECT_PIN, true);
  mainboard_gpio_configure_output(BOARD_DISPLAY_DATA_COMMAND_PIN, false);
  mainboard_gpio_configure_output(BOARD_DISPLAY_RESET_PIN, false);
  mainboard_gpio_configure_output(BOARD_DISPLAY_SPI_CLOCK_PIN, false);
  mainboard_gpio_configure_output(BOARD_DISPLAY_SPI_MOSI_PIN, false);

  display_delay();
  mainboard_gpio_write(BOARD_DISPLAY_RESET_PIN, true);
  display_delay();

  /*
   * UC1701 sequence used by Marlin's BTT/FYSETC Mini 12864 driver. Keep CS
   * asserted across the complete command sequence.
   */
  display_select();
  display_write_selected_byte(false, 0xE2u); /* Software reset. */
  display_write_selected_byte(false, 0x40u); /* Start line zero. */
  display_write_selected_byte(false, 0xA0u); /* Normal ADC direction. */
  display_write_selected_byte(false, 0xC8u); /* Reverse common direction. */
  display_write_selected_byte(false, 0xA6u); /* Normal pixels. */
  display_write_selected_byte(false, 0xA2u); /* 1/9 bias. */
  display_write_selected_byte(false, 0x2Fu); /* Enable all power circuits. */
  display_write_selected_byte(false, 0xF8u); /* Booster ratio follows. */
  display_write_selected_byte(false, 0x00u); /* 4x booster ratio. */
  display_write_selected_byte(false, 0x23u); /* Large V0 resistor ratio. */
  display_write_selected_byte(false, 0x81u); /* Contrast follows. */
  display_write_selected_byte(false, 0x3Fu); /* Bring-up contrast maximum. */
  display_write_selected_byte(false, 0xACu); /* Indicator follows. */
  display_write_selected_byte(false, 0x00u); /* Indicator disabled. */
  display_write_selected_byte(false, 0xAFu); /* Display on. */
  display_deselect();

  display_delay();
  display_select();
  display_write_selected_byte(false, 0xA5u); /* All pixels on test. */
  display_deselect();
  display_delay();
  display_delay();
  display_select();
  display_write_selected_byte(false, 0xA4u); /* Return to display RAM. */
  display_deselect();
  display_delay();

  display_render_test_screen();
}

void mainboard_display_module_run_background_tasks(void)
{
  display_render_test_screen();
}

void mainboard_display_module_run_feedback_tasks(void)
{
  /* NeoPixels and sounder remain unconfigured during safe bring-up. */
}
