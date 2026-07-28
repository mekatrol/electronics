# Migration Map

## Reference Repository Findings

`D:/repos/pcb-cnc-mill` provides useful naming, GNU Make patterns, a bare-metal
scheduler, USB/CDC code, a UART protocol, and a placeholder Mini 12864 attached
display interface. `D:/repos/pcb-mill/firmware/cnc` provides an additional
LPC1769 Mini 12864 experiment with LCD, NeoPixel, clock, SysTick, and UART
code.

Its `firmware/boards/mainboard/btt_skr_1_4/` directory contains bootloader
restore documentation only. It does not contain an LPC1769 startup file,
linker script, HAL, USB driver, UART driver, SD-card driver, or build target.
Those items must be implemented and verified during this migration.

STM32G0 code from the SKR Mini E3 V3 target is not register-compatible with the
LPC1769 and must not be copied as if it were an SKR 1.4 Turbo port.

The `pcb-mill` experiment confirms the SKR 1.4 EXP pin mapping and the basic
ST7567 command sequence. Reuse requires review: its `GPIO0` definition points
to the GPIO1 base address, its P0.18 SPI function-select shift is incorrect,
and its LCD/NeoPixel timing assumes that its 120 MHz clock setup has already
completed. Those defects and assumptions are not carried into this firmware.

## Legacy Module Map

| Legacy module | New responsibility | Planned phase |
|---|---|---|
| `reflow.cpp/.h` | Reflow state machine and run coordination | 4 |
| `stage.cpp/.h` | Profile stage model and transitions | 4 |
| `temperature.cpp/.h` | Temperature service and validation | 4 |
| `temp_sensor.cpp/.h` | Mainboard sensor HAL/adaptor | 2 and 4 |
| `average.cpp/.h` | Hardware-independent sample filtering | 4 |
| `pid.cpp/.h` | Bounded heater controller | 4 |
| `learn.cpp/.h` | Optional tuning/learning workflow | 4 |
| `config.cpp/.h` | Versioned settings and safe defaults | 4 |
| `plot.cpp/.h` | Compact history model and 128x64 graph rendering | 3 and 4 |
| `ui.cpp/.h` | Mini 12864 menus and encoder actions | 3 and 4 |
| `lcd.cpp/.h` | Replaced by Mini 12864 LCD module driver | 3 |
| `pins.h` | Replaced by board pin maps | 2 |
| Arduino `.ino` | Replaced by board-specific C entry points | 1 onward |

## Peripheral Plan

- USB/CDC: adapt the reference API and protocol shape; write an LPC1769 device
  backend.
- UART: LPC1769 diagnostic/control transport. No display UART is needed.
- SD card: implement SPI/block and filesystem access on the SKR.
- Mini 12864: implement the LCD serial bus, encoder, button, LEDs/backlight,
  and sounder within the SKR firmware. There is no second firmware target.
- Excluded: TMC2209, CAN, motion, G-code, limits, probe, spindle, and toolhead.
