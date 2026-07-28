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

The current module is an inert Phase 1 placeholder. Connector pinout, voltage
levels, LCD controller, and output polarity require verification before GPIO
initialization is added.
