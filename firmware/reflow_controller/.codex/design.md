# Reflow Controller Firmware Design

## Goal

Build safe, maintainable firmware for a reflow oven using a BTT SKR 1.4 Turbo
mainboard and a BTT Mini 12864 V1.0 display module.

The main job is to:

- Measure oven temperature.
- Execute a validated reflow temperature profile.
- Control heater and cooling outputs.
- Present state, temperatures, profiles, plots, and alarms on the TFT.
- Accept local controls and optional USB/serial commands.
- Store configuration, profiles, and logs.
- turn all heaters off promptly when operation becomes unsafe.

## Architecture

Use a layered bare-metal design with interrupts for urgent hardware events and
a priority scheduler for short, non-blocking service work. Do not make an RTOS
part of the base design.

1. Reflow control
   - Owns idle, preheat, soak, reflow, cool, complete, and alarm states.
   - Validates profiles before a run.
   - Converts profile targets and measured temperatures into bounded output
     requests.

2. Temperature acquisition
   - Samples thermocouple or temperature interfaces.
   - Filters readings without hiding rapid unsafe changes.
   - Detects missing, shorted, stale, and implausible sensors.

3. Heater control
   - Applies PID or bounded time-proportioning control.
   - Enforces output, temperature, rate, and time limits.
   - Cannot override the safety interlock.

4. Safety supervisor
   - Independently evaluates sensors, temperature, heating response, timing,
     watchdog health, and control state.
   - Latches heater outputs off on a fault.
   - Requires deliberate acknowledgement/reset after a fault.

5. User interface
   - Runs as part of the SKR firmware and renders to the Mini 12864.
   - Displays current/target temperatures, active stage, time, output level,
     plots, profiles, configuration, link state, and alarms.
   - Sends input events to the reflow application; it never directly controls
     heaters.

6. Communication
   - Uses USB CDC and optional serial UART for diagnostics and control.

7. Storage
   - Uses versioned persistent settings.
   - Supports SD-card profiles, logs, and firmware-update workflows.
   - Performs storage work in bounded steps outside safety-critical paths.

8. Hardware abstraction
   - Wraps GPIO, timers, PWM/time-proportioning outputs, ADC/SPI sensor inputs,
     USB, UART, SD card, flash, interrupts, and watchdog.
   - Keeps LPC1769 and GD32F205 register code out of domain logic.

## Board Responsibilities

### SKR 1.4 Turbo

The mainboard is authoritative for:

- Temperature acquisition.
- Reflow profile and state-machine execution.
- PID and heater/cooling outputs.
- Safety interlocks and watchdog.
- Persistent settings and primary logging.
- USB CDC and diagnostic serial.
- SD-card access.
- Status/command exchange with the TFT.

All heater outputs must be configured inactive before other application
initialization and must return inactive after reset or fault.

### Mini 12864 V1.0

The attached display module driver owns:

- LCD rendering.
- Encoder and button input.
- Sounder, backlight, and RGB LEDs where fitted.
- UI state that does not affect safety authority.

It is compiled into the SKR firmware and has no separate MCU, clock tree,
startup code, linker script, scheduler, communication link, or firmware image.
Display work must remain lower priority than temperature control and safety.

## Scheduler And Work Queues

Periodic tasks perform small service operations. Priority work queues hold
bounded one-shot commands. No task or work item may wait synchronously for USB,
UART, SD card, display transfer, touch, or another queue item.

Priority bands:

- Emergency: force outputs off, latch and report faults.
- Control: acquire temperature, evaluate safety, advance profile, update
  bounded heater requests.
- Communication: receive/transmit serial and USB frames.
- User input: debounce encoder and buttons.
- Display: update dirty regions and feedback.
- Background: SD-card work, config saves, logs, and diagnostics.

Queues are bounded. Safety work reserves capacity. Coalescing is allowed for
screen redraws and status updates where only the newest value matters.

## Timing Model

- Use hardware timers for monotonic time and heater time-proportioning.
- Keep interrupt handlers short and deterministic.
- Schedule sensor acquisition and safety evaluation at documented periods.
- Use elapsed-time comparisons rather than blocking delays.
- Split slow peripheral transactions into bounded operations.
- Feed the watchdog only from a known healthy scheduler point.

## Safety Model

- Heater pins start inactive.
- Invalid profiles cannot start.
- A sensor fault, over-temperature, runaway, failed heat rise, stale control
  loop, watchdog reset, or internal invariant failure forces heaters off.
- Mainboard/display link loss never leaves the operator believing control is
  healthy; mainboard policy determines whether an active run may safely
  continue.
- Manual output tests require an explicit service mode, hard limits, timeout,
  and visible warning.
- Configuration defaults are conservative and values have bounds and units.

## Configuration

- Board pins live in one board-specific header per board.
- Reflow limits and defaults live in a versioned configuration module.
- Public values include units in names or documentation.
- Persistent records have version and integrity checks.
- Unsupported or corrupt configuration falls back to safe defaults.

## Testing

Prefer tests that catch mistakes without powered heater hardware:

- Host tests for filtering, PID saturation/anti-windup, profile validation,
  stage transitions, timeouts, and all alarm paths.
- Protocol tests for USB/serial framing, CRC, versioning, and malformed input.
- Build the SKR image with warnings treated as errors.
- Bench tests for reset pin states, clocks, UART, USB CDC, SD, sensors, LCD,
  encoder, buttons, LEDs, sounder, and watchdog.
- Use a dummy load before commissioning real heaters.
