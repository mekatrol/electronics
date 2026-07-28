# BTT SKR 1.4 Turbo

Phase 1 target for the LPC1769-based SKR 1.4 Turbo.

- Core: ARM Cortex-M3.
- Internal flash: 512 KiB.
- Application origin: `0x00004000` after the factory BTT bootloader.
- Phase 1 RAM: 32 KiB local SRAM; AHB SRAM banks are reserved for later work.
- Bootloader update filename: `firmware.bin`.

The reference PCB-mill repository has bootloader recovery notes for this board
but no firmware board port. Startup and linking here are therefore new
bring-up code and require hardware verification.

The current image establishes the LPC1769's 120 MHz core clock, configures the
five GPIO signals required to initialize the attached Mini 12864 LCD, and sets
the panel's three NeoPixels to dim white for a visible static bring-up message.
It does not configure heater, fan, sensor, USB, UART, SD-card, encoder, or
sounder peripherals.
