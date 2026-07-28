# PCB Reflow Oven Controller

## Operator and maintenance manual

This manual describes the controller represented by the firmware in this
directory. It was reconstructed from the source code; no circuit diagram,
oven specification, or original operating instructions were present with the
firmware.

> **Important:** The current source has not been established as safe for
> unattended or production use. It contains no over-temperature cut-out,
> heating timeout, thermistor open/short detection, or check for disagreement
> between its two sensors. Use an independent, hardware over-temperature
> cut-out and keep the oven attended whenever it is energised.

## 1. Intended use

The controller operates a small PCB reflow oven using:

- two 100 kΩ NTC thermistors;
- one heater output;
- one cooling-fan output;
- a 20 × 4 character LCD;
- a rotary-encoder push button;
- a separate button called `KILL` in the source; and
- a beeper.

The automatic program heats through three stages and then turns on the fan:

| Stage | Default setpoint | Hold time |
| --- | ---: | ---: |
| Preheat | 125 °C | 60 seconds |
| Soak | 160 °C | 60 seconds |
| Reflow | 195 °C | 60 seconds |
| Cooling | No controlled setpoint | Fan runs until below 25 °C |

These are controller defaults, not universal solder-paste recommendations.
Confirm the correct profile from the solder-paste and component data sheets
before processing a board. In particular, 195 °C may be too low for some
lead-free pastes.

## 2. Safety

- The oven may contain exposed mains voltage and surfaces hot enough to cause
  burns or fire. Enclose, earth, fuse, and strain-relieve all mains wiring.
- Drive the heater through a correctly rated and heatsinked, isolated switching
  device. Do not connect an oven heater directly to the controller output.
- Fit an independent thermal fuse or thermostat that removes heater power
  without relying on this firmware, its microcontroller, or its thermistors.
- Keep the oven on a non-combustible surface with clear ventilation.
- Do not leave it unattended. Keep a suitable fire extinguisher nearby.
- Do not use the oven for food after it has processed solder, flux, or PCBs.
- Treat the controller display as an indication, not an independent safety
  instrument.
- If either temperature reading is implausible, differs substantially from the
  other, or stops changing while heating, abort and isolate power.
- Opening the oven early may release hot flux fumes. Use suitable extraction.
- The firmware's stop button is implemented in software. It is not a substitute
  for a latching emergency stop that physically interrupts heater power.

## 3. Controls and indications

### Start/stop button

The input named `KILL` in the source is the only control used by the main
program. With the controller idle, press and release this button to start a
reflow run. The beeper sounds while the button is held.

During a run, press and release the same button to abort. The heater turns off
and the cooling fan turns on.

The rotary encoder and its push button are initialised but are not used by the
active main loop. Turning or pressing the encoder does not select a profile or
change a setpoint in this firmware.

### LCD

The display has four lines:

1. `Stage:` followed by `IDLE`, `PREHEAT`, `SOAK`, or `REFLOW`.
2. `Setpoint:` followed by the active target temperature.
3. Status symbols and, during a hold, seconds remaining.
4. Sensor 1 temperature, sensor 2 temperature, and their average.

Line 3 uses these symbols:

- `^` — heating toward the setpoint;
- `-` — holding at the setpoint;
- `C` — five-second heater cycling has been enabled near the setpoint.

The countdown appears from character position 11 on the third line. The
controller regulates from the average of the two displayed sensor readings.

### Serial output

The serial port runs at 9600 baud. On startup it prints the setpoints stored in
EEPROM. While operating, it continuously emits comma-separated data:

```text
setpoint,sensor_1,sensor_2,average
```

This can be viewed with an Arduino serial monitor or captured for plotting.
There is no header in the live data.

## 4. Before the first run

1. With mains power isolated, inspect the earth connection, heater switching
   device, fuse, fan, wiring, and independent thermal cut-out.
2. Secure both thermistors where they measure useful board/oven temperature.
   Keep them clear of direct electrical contact and prevent them moving during
   a run.
3. Power only the low-voltage controller first, if the hardware permits it.
4. At room temperature, confirm that both displayed readings are plausible and
   close to a trusted thermometer. A large difference between the two sensors
   must be investigated before heating.
5. Confirm that the heater output is off at startup.
6. Test the physical emergency isolation and the software stop function
   without a populated PCB.
7. Perform an instrumented empty-oven trial, followed by a trial with a scrap
   or test PCB. Compare the recorded profile with the paste specification.

## 5. Running a reflow cycle

1. Apply solder paste and place components in accordance with the paste and
   assembly instructions.
2. Place the PCB and both temperature sensors in their validated positions.
3. Close the oven and start fume extraction.
4. Check that the display readings are plausible.
5. Press and release the start/stop button.
6. Remain with the oven and watch both sensor readings throughout the run.

The controller then performs the following sequence:

1. **Preheat:** heats to 125 °C, then holds for 60 seconds.
2. **Soak:** heats to 160 °C, then holds for 60 seconds.
3. **Reflow:** heats to 195 °C, then holds for 60 seconds.
4. **Finish:** turns the heater off, changes the displayed stage to `IDLE`, and
   turns the fan on.
5. **Cool:** leaves the fan on until the averaged temperature falls below
   25 °C, at which point the idle loop turns it off.

Below each setpoint the heater initially remains continuously available. Once
the temperature is within 25 °C of the setpoint, the controller alternates a
five-second enable window and a five-second disable window. During an enabled
window, the heater is energised only while the measured average is below the
setpoint.

Stage duration is not fixed: each stage takes as long as needed to reach its
setpoint, followed by its 60-second hold. There is no timeout if a setpoint
cannot be reached.

## 6. Aborting a run

Press and release the start/stop button. The firmware:

1. turns off the heater;
2. exits the active stage;
3. sets the displayed stage to `IDLE`; and
4. turns on the cooling fan.

If temperature continues to rise unexpectedly, or the button does not respond,
use the independent mains isolation immediately. Do not wait for software
control.

## 7. After a run

- Leave the PCB undisturbed while solder is liquid.
- Keep extraction running and allow the fan-controlled cooling period to
  finish.
- Confirm that the heater is off.
- Open the oven only when doing so is safe for the process and operator.
- Inspect the assembly for bridges, tombstoning, insufficient wetting, damaged
  parts, and other defects.
- Save the serial temperature trace when validating or troubleshooting a
  profile.

## 8. Profile settings

On first startup, the firmware writes these values to EEPROM:

| EEPROM field | Default | Used by active cycle |
| --- | ---: | --- |
| `preheat_setpoint` | 125 °C | Yes |
| `soak_setpoint` | 160 °C | Yes |
| `reflow_setpoint` | 195 °C | Yes |
| `cool_setpoint` | 0 °C | No |
| `overshoot_delta` | 25 °C | Yes |

There is no operator menu for editing them. Changing the constants in
`stage.h` affects only EEPROM that has not previously been initialised.
Existing units reload their saved EEPROM values at boot. Updating a deployed
unit therefore requires a deliberate EEPROM migration/erase or configuration
tool; simply reflashing changed defaults may not change its profile.

Do not alter a profile without measuring the resulting board temperature and
checking:

- the paste's specified preheat/soak range;
- time above liquidus;
- peak package temperature;
- maximum heating and cooling ramp rates; and
- the most temperature-sensitive component limits.

## 9. Temperature sensors

The conversion table is for a 100 kΩ thermistor specified in the source as
`R25 = 100 kΩ`, `β25 = 4092 K`, with a 4.7 kΩ pull-up. Its table spans
approximately −15 °C to 300 °C.

Each sensor reading is smoothed with a five-sample moving average. Control uses
the arithmetic mean of the two independently converted temperatures.

There is no user calibration offset or gain adjustment. Validate both channels
against a traceable or otherwise trusted thermometer across the operating
range. A room-temperature agreement alone does not establish accuracy near
reflow temperature.

## 10. Troubleshooting

| Symptom | Checks and action |
| --- | --- |
| Run will not start | Confirm the separate start/stop (`KILL`) input changes state and the encoder push button is not stuck pressed. |
| Heater does not warm | Abort. Check the displayed temperatures, fuse, independent cut-out, heater supply, isolation device, and heater output path. Do not bypass safety devices. |
| Temperature rises with `IDLE` displayed | Isolate mains immediately. Suspect a shorted or incorrectly wired heater switching device. |
| Temperature never reaches a setpoint | Abort manually; there is no automatic timeout. Check heater power, sensor placement, oven losses, and fan state. |
| One reading is very high or low | Abort and isolate power. Check that thermistor, connector, divider wiring, and analogue input. The firmware does not detect a failed sensor. |
| Sensors disagree | Abort. Check placement, attachment, wiring, and calibration. The controller does not reject mismatched readings. |
| Large temperature overshoot | Stop using the profile. Check sensor thermal contact and heater inertia; validate a safer setpoint/cycling strategy with instrumentation. |
| Fan remains on | This is expected until the average falls below 25 °C. Check sensor readings and fan output wiring if it never stops. |
| Changed source defaults have no effect | Old values remain in EEPROM. Use a controlled EEPROM reset or migration before relying on new defaults. |
| Encoder does nothing | Expected in the active firmware; the main loop never services the encoder routine. |

## 11. Maintainer reference

The source targets Arduino-style hardware and uses the following pin
assignments:

| Function | Pin |
| --- | ---: |
| Heater output | D8 |
| Fan output | D10 |
| Thermistor 1 | A13 |
| Thermistor 2 | A15 |
| LCD RS / Enable | D16 / D17 |
| LCD D4–D7 | D23 / D25 / D27 / D29 |
| Encoder A / B / push | D31 / D33 / D35 |
| Beeper | D37 |
| Start/stop (`KILL`) | D41 |
| SD detect / select | D49 / D53 |

The pin selection implies a board with Arduino Mega-class pin availability.
Verify the actual controller board before relying on this table.

### Source-derived limitations

The following are important characteristics of the current source, not merely
future enhancements:

- no thermal runaway, maximum-temperature, or maximum-stage-time protection;
- no thermistor open-circuit, short-circuit, plausibility, or disagreement
  checks;
- no feedback proving that the heater or fan actually switched;
- no watchdog handling in the application;
- no configurable profile UI;
- the cooling setpoint and `COOL` stage are defined but not used;
- `learn_run()` exists but is not called by the main program;
- `lcd_loop()` exists but is not called by the main program;
- the PID implementation exists but the active reflow cycle does not use it;
- the SD-card and encoder code is inactive because `lcd_loop()` is not called;
- the LCD is initialised with `lcd.begin(SCREEN_WIDTH, SCREEN_WIDTH)` rather
  than the declared 20 × 4 dimensions;
- `config` is declared external in `config.h` but static in `config.cpp`; and
- LCD functions declared for other files are defined static in `lcd.cpp`; and
- the first dwell-screen update in `reflow.cpp` passes the numeric value `60`
  where `ui_update()` requires a pointer to the countdown value.

The last four items should be reviewed before attempting a fresh build. This
manual describes the apparent intended runtime behavior of the source, not a
successful build verification.

## 12. Recommended validation before further use

Before returning this controller to service:

1. Correct the build/linkage and LCD initialisation issues.
2. Add fail-safe sensor plausibility checks, sensor-disagreement limits,
   absolute over-temperature shutdown, and timeouts for every heating stage.
3. Define a fault state that latches the heater off and requires operator
   acknowledgement.
4. Confirm output polarity and safe power-up behavior on the actual hardware.
5. Validate the independent hardware cut-out by test.
6. Record a thermocouple-instrumented profile on a representative PCB.
7. Update this manual with enclosure-specific mains isolation, fuse ratings,
   heater rating, fan behavior, sensor locations, and emergency-stop details.
