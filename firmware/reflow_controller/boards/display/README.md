# BTT Mini 12864 V1.0

The Mini 12864 is attached directly to the SKR 1.4 Turbo expansion connectors.
It has no microcontroller and therefore no separate firmware binary, startup
file, linker script, clock tree, or scheduler.

The driver is compiled into the SKR `firmware.bin`. It will own only:

- 128x64 LCD bus and chip-select/reset pins.
- Rotary encoder and push button.
- RGB status LEDs/backlight.
- Sounder, if present on the exact V1.0 hardware.

The SKR firmware continues to own clocks, scheduling, reflow state, sensors,
heater safety, storage, USB, and serial communication.

The Phase 1 bring-up driver initializes the ST7567/UC1701-compatible LCD over
software SPI mode 3 and displays:

```text
REFLOW CONTROLLER

  DISPLAY READY
```

LCD chip select, data/command, reset, clock, and MOSI are configured. The
three NeoPixels are set once to dim white so the LCD is visible during
bring-up. Encoder/button inputs, SD card, and sounder remain untouched until
their Phase 3 drivers are implemented.

The connector mapping and basic ST7567 initialization were cross-checked
against `D:/repos/pcb-mill/firmware/cnc`. The reusable mapping is:

| Function | SKR EXP pin | LPC1769 pin |
|---|---:|---:|
| LCD clock / shared SD clock | EXP2-2 | P0.15 |
| LCD MOSI / shared SD MOSI | EXP2-6 | P0.18 |
| Encoder button | EXP1-2 | P0.28 |
| LCD chip select | EXP1-3 | P1.18 |
| LCD data/command | EXP1-4 | P1.19 |
| LCD reset | EXP1-5 | P1.20 |
| NeoPixel data | EXP1-6 | P1.21 |
| Beeper | EXP1-1 | P1.30 |
| SD detect | EXP2-7 | P1.31 |
| Encoder A | EXP2-3 | P3.26 |
| Encoder B | EXP2-5 | P3.25 |

The reference's NeoPixel implementation assumes a previously configured
120 MHz clock. This firmware establishes that clock explicitly and uses the
reference GPIO pulse loop for the complete three-pixel chain. The LCD uses
the software-SPI mode 3 and UC1701 initialization sequence proven by Marlin's
`BTT_MINI_12864` implementation. Shared/bounded SPI transactions and dynamic
feedback remain deferred to Phases 2 and 3.

The connector map, orientation, three-pixel backlight, and framebuffer text
were verified on hardware on 2026-07-28. This panel required electronic
volume `0x3F` for text to be readable straight-on; Marlin's initial `0x27`
setting was only faintly visible at an angle.
