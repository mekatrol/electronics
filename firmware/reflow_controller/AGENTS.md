# Reflow Controller Migration Agent

## Mission

Migrate the legacy Arduino Mega 2560 reflow controller to:

- BIGTREETECH SKR 1.4 Turbo (LPC1769) mainboard.
- BIGTREETECH Mini 12864 V1.0 display module.

Work in phases. Finish and verify one phase before starting the next. Keep the
project usable from this directory on Windows and Linux.

## Source Material

- Legacy behavior: `../reflow_controller_legacy/`
- Reusable board/style reference: `D:/repos/pcb-cnc-mill/`
- Project design: `.codex/design.md`
- Coding rules: `.codex/standards.md`
- Migration map: `docs/MIGRATION.md`

Do not edit either source project during migration. Copy and adapt code here.

## Scope

Keep:

- Existing naming conventions and layered C code style.
- Bare-metal interrupt plus non-blocking scheduler model.
- USB device/CDC, serial UART, and SD-card support.
- Mini 12864 LCD, encoder, button, LEDs/backlight, and sounder where fitted.
- Reflow profiles, temperature measurement, PID control, learning mode,
  configuration, plotting/history, and safety behavior from the legacy unit.

Exclude:

- G-code parsing.
- Motion planning, step generation, homing, limits, probing, and spindle code.
- TMC2209 support.
- CAN bus and toolhead firmware.
- Standalone display firmware or a mainboard/display UART protocol.
- Support for boards other than the SKR 1.4 Turbo and Mini 12864 V1.0.

## Phase 1 - Project And Builds

Goal: one SKR firmware image builds with the attached display module included.

1. Maintain the root `Makefile` with `mainboard`, `all`, `clean`, and
   `print-config` targets.
2. Keep GNU Make recipes valid on Windows and Linux.
3. Keep SKR startup, linker, and pin definitions under `boards/mainboard/`.
4. Keep the passive panel driver under `boards/display/`.
5. Do not add display startup, linker, clock, or separate build files; the
   Mini 12864 has no MCU.
6. Build the SKR image as `firmware.bin` at the BTT bootloader app offset.
7. Document the required ARM GNU toolchain and build commands.
8. Do not energize heaters in bring-up firmware.

Exit check: `make clean all` completes with `arm-none-eabi-gcc`, and
`build/mainboard/btt_skr_1_4_turbo/firmware.bin` exists.

## Phase 2 - Shared Runtime And Mainboard HAL

Goal: reliable clocks, timing, communication, and safe mainboard IO.

1. Port the reference priority scheduler and bounded work queues.
2. Implement LPC1769 clock, SysTick/timers, GPIO, watchdog, and interrupt
   helpers.
3. Add non-blocking diagnostic/control UART.
4. Port USB device and USB CDC for LPC1769; do not copy STM32 register code
   unchanged.
5. Add SPI and SD-card block access, then a small FAT filesystem layer.
6. Add temperature sensor inputs and heater/fan outputs using the single board
   pin map.
7. Default every heater output off at reset and on any unhandled fault.

Exit check: bench diagnostics prove tick timing, UART loopback, USB CDC, SD
mount/read, temperature inputs, display connector reset states, and heater-off
safety.

## Phase 3 - Mini 12864 Display Module

Goal: usable display and local controls within the SKR firmware.

1. Verify the SKR EXP connector mapping and the exact Mini 12864 V1.0 LCD
   controller, encoder, button, LED/backlight, and sounder wiring.
2. Implement bounded LCD transfers and dirty-region updates.
3. Implement debounced encoder and button input events.
4. Implement non-blocking sounder and LED/backlight feedback where supported.
5. Create compact reflow screens and strings for the 128x64 pixel display.
6. Keep all heater control and safety decisions outside the display module.

Exit check: display rendering, encoder/button input, and local feedback pass
bench tests without enabling a heater.

## Phase 4 - Reflow Domain Migration

Goal: move legacy behavior into hardware-independent C modules.

1. Inventory each legacy `.cpp/.h` pair and preserve intended behavior.
2. Port stage/profile logic, temperature averaging, PID, learning, config,
   plots/history, and UI state into focused modules.
3. Replace Arduino `millis`, GPIO, EEPROM, LCD, and serial calls with HAL
   interfaces.
4. Use explicit units in names and comments.
5. Add host tests for averaging, PID limits, stage transitions, profile
   validation, timeouts, and alarm paths.

Exit check: host tests cover the control state machine and simulated profiles
complete with expected temperature targets and safe outputs.

## Phase 5 - Safety And Hardware Commissioning

Goal: safely commission the oven.

1. Implement sensor-open, sensor-short, implausible-rate, over-temperature,
   no-heat-rise, runaway, communication-loss, and watchdog faults.
2. Make every fault latch heater outputs off; require deliberate reset.
3. Verify output polarity with the oven disconnected.
4. Test sensors against a reference thermometer.
5. Test with a low-power dummy load before connecting heaters.
6. Tune control limits and PID with supervised runs.
7. Record results in `docs/BENCH_TESTS.md`.

Exit check: every injected fault turns heaters off, UI reports the cause, and
power-cycle/reset behavior matches the design.

## Phase Rules

- At the start of work, state the active phase.
- Do not silently skip an exit check.
- Update `README.md` and relevant Markdown when behavior or setup changes.
- Keep entry-point `main.c` files small; place logic in feature modules.
- Use bounded, non-blocking work outside short hardware initialization.
- Keep interrupt handlers small.
- Never enable a heater merely to prove that firmware builds.
- If hardware facts are uncertain, mark them `TODO: verify on hardware` and
  keep the affected output in its safe state.
