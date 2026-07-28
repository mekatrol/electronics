# Project Standards

## Change Rules

- Keep changes tied to the active phase in `AGENTS.md`.
- Update `README.md` and relevant instructions when behavior changes.
- Preserve useful naming and structure from `D:/repos/pcb-cnc-mill`.
- Do not copy CNC motion, G-code, TMC2209, CAN, or toolhead code.
- Keep board-specific register and pin code under `boards/`.
- Keep shared domain and runtime code under `src/`.
- Reserve `main.c` for startup wiring and the main loop.

## Firmware Rules

- Safety beats speed and convenience.
- Heater outputs default off and faults latch them off.
- Keep interrupts small and scheduler tasks bounded.
- Do not block on USB, UART, SD, display, or input.
- Define hardware/protocol constants once in the narrowest shared header.
- Use fixed-width integer types and explicit units.
- Add detailed comments around registers, timing, interrupt ownership, and
  safety boundaries.

## Verification Rules

- Build with warnings treated as errors.
- Add host tests for hardware-independent control behavior.
- Document hardware-only checks in `docs/BENCH_TESTS.md`.
- State what was built/tested and what still needs hardware verification.

