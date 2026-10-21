# Core controller — power, TRIAC drive and analogue-input design notes

**Revision:** 2026-10-21  
**Status:** Preliminary engineering design / calculation record, **not** a validated production schematic.  
**Target:** Raspberry Pi Pico (RP2040 or RP2350) controller with up to eight 24 VAC irrigation style solenoids.

## 1. Latest agreed architecture

```text
Isolated 24–26 VAC, 50 Hz transformer secondary
  ├── 24 VAC solenoid power path → BT136-800E TRIACs → solenoids → AC return
  └── one half-wave rectifier diode (US1M) → TP1 (pulsating DC)
       ├── 1000 µF / 63 V bulk capacitor to AC/DC common return
       ├── 4.7 µF ceramic bypass (voltage/derating to verify)
       └── LMR38020FDDAR buck regulator, configured for 5.0 V
            ├── DS1307ZN RTC and other genuine 5 V loads
            └── AMS1117-3.3 LDO → 3.3 V loads
                 ├── Pico / RP2040 or RP2350 system (see power-path caveat)
                 ├── W25Q128JV flash and STWD100 watchdog
                 ├── two 74HC595 shift registers
                 ├── ten blue indicators, each with 330 Ω resistor
                 └── ULN2803A eight-channel driver → eight MOC3063 input LEDs
```

**Isolation/grounding:** The MOC3063 isolates its *input and output pins*, but if the DC return is wired to one side of the AC transformer secondary, the controller and TRIAC power circuit share that electrical reference. Do not describe the whole controller as galvanically isolated from the secondary. Transformer primary-to-secondary safety isolation must be assured. 

## 2. Selected design components

| Function | Selected component / value | Engineering note |
|---|---|---|
| 5 V buck | TI LMR38020FDDAR | Verify SO-PowerPAD-8 layout, switching frequency, BOOT and input/output ceramics against TI datasheet |
| Buck inductor | Sumida CDRH129RNP-330MC, 33 µH ±20%, 4.25 A quoted, 39.3 mΩ | Verify saturation-current definition and current-limit margin |
| Rectifier | US1M, half-wave | Verify exact manufacturer datasheet, repetitive pulse and inrush capability |
| Reservoir | 1000 µF / 63 V electrolytic | Check ripple rating, ESR, lifetime and transformer no-load voltage |
| Input ceramic | 4.7 µF ceramic plus local 100 nF / 100 V bypass | Verify ceramic voltage rating, DC bias and TI minimum effective capacitance |
| 5 V feedback | RFBT = 100 kΩ; RFBB = 24.9 kΩ | Nominal 5.016 V with 1 V feedback reference |
| 3.3 V regulator | AMS1117-3.3 | Check output capacitor ESR, dropout and heat |
| Logic expansion | Two 74HC595 at 3.3 V | Confirm output HIGH drive into ULN2803A inputs |
| Eight optotriac LED drivers | One ULN2803A, eight channels | Open-collector Darlington sinks; common COM pin connection discussed below |
| Optotriac input resistors | 150 Ω per channel, **provisional** | Recalculate against worst-case optocoupler trigger and ULN voltage drop; validate 74HC595 source capability |
| Optotriacs | MOC3063 zero-cross family | Verify exact package, LED trigger current and 24 VAC firing behavior |
| Power TRIACs | BT136-800E | Verify gate triggering at 24 VAC |
| TRIAC suppression | SMAJ48CA and 47 Ω + 100 nF series snubber | Verify pulse ratings, leakage and thermal performance |
| RTC | DS1307ZN | 5 V rail |
| Flash and watchdog | W25Q128JV and STWD100 | 3.3 V rail; avoid counting onboard Pico flash twice |
| Analogue input | 24.9 kΩ / 10 kΩ divider; 1 kΩ series; 100 nF filter | Add validated low-leakage clamps and connector-level surge protection |

**Design status:** The 150 Ω optocoupler resistor is a **design starting value, not a verified production selection**. Its value and the 74HC595-to-ULN2803A interface require worst-case datasheet checks and bench validation.

## 3. AC-to-DC rectifier and TP1 calculations

### Assumptions

- Transformer secondary: **24–26 VAC RMS**, **50 Hz**; these are nominal values, not guaranteed min/max including mains tolerance and no-load regulation.
- Half-wave rectifier: one forward diode conducting each positive half-cycle.
- Rectifier drop: **0.7 V assumed** for a rough peak calculation; US1M datasheet gives a higher *maximum* VF at its rated current (the actual drop at low current is different). Check diode curves.
- Reservoir capacitor: `C = 1000 + 4.7 = 1004.7 µF` **nominal**, but the ceramic's DC-bias derating and bulk tolerance change the actual total.
- Diode charging is pulsed; AC source impedance and diode conduction angle matter.

Peak secondary voltage:

`Vpk(ac) = Vrms × sqrt(2)`

Approximate peak at TP1:

`Vpk(TP1) ≈ Vrms × 1.4142 − Vf`

| AC RMS | AC peak | TP1 peak assuming Vf=0.7 V |
|---|---:|---:|
| 24 V | 33.94 V | **33.24 V** |
| 26 V | 36.77 V | **36.07 V** |

**These are nominal peak voltages, not a guaranteed operating range.** Transformer no-load output, mains high-line, and ringing may increase them; sag under load can lower them. Check actual maximum against all VIN component ratings and TI absolute maximum ratings. Use the specified **63 V** bulk capacitor.

### Half-wave ripple

For modest ripple relative to the DC voltage and nearly constant input current:

`ΔVpp ≈ I_TP1 / (f_line × C)` with `f_line = 50 Hz` (NOT 100 Hz for half-wave).

The buck draws approximately constant **power**, not constant current, so the equation is a useful first estimate only. As TP1 falls, buck input current increases. Transformer charging pulses, reservoir ESR, capacitor tolerance and dynamic load must be verified by simulation and measurements.

### Single US1M suitability

From the supplied MDD US1M datasheet excerpt: `VRRM=1000 V`, `IF(AV)=1 A at TL=125°C`, **20% derating for capacitive loads**, `IFSM=30 A for one 8.3 ms half-sine surge`, `RθJA≈55°C/W` (test conditions matter), `Tj max=150°C`. Simple derated average rating: `1.0 × 0.8 = 0.8 A`. This does **not** guarantee repetitive capacitor charging-pulse or startup-inrush capability. Evaluate transformer VA, source impedance, capacitor ESR, peak/repetitive diode currents and diode temperature. One diode is a reasonable *candidate* for the controller electronics; do not parallel two diodes expecting automatic current sharing. A second diode in the AC return does not provide two-rail protection. A full bridge would change the return/ground topology and requires a separate design review.

## 4. Controller load budget — eight optotriacs ON

**These are planning assumptions, not measured or guaranteed maximum component currents.** Confirm actual Pico board supply path, firmware workload, flash activity, GPIO output loading, sensor excitation, communications and peripherals.

| 3.3 V consumer | Assumed current |
|---|---:|
| RP2040 / RP2350 Pico system | 100 mA |
| W25Q128JV flash | 25 mA |
| STWD100 watchdog | 1 mA |
| Two 74HC595, excluding driven outputs | 2 mA |
| Ten blue LEDs with 330 Ω each | 9.1 mA |
| Eight MOC3063 input LEDs, via ULN2803A and 150 Ω | 58.7 mA |
| **Total 3.3 V output load** | **195.8 mA** |

5 V loads: `DS1307 ≈ 2 mA` and `AMS1117-3.3 input ≈ 195.8 mA` (plus small LDO quiescent current). Thus:

`I_5V ≈ 195.8 + 2 = 197.8 mA`

`P_3V3 = 3.3 × 0.1958 = 0.6461 W`

`P_5V,out = 5 × 0.1978 = 0.989 W`

**LED estimate:** `I_LED ≈ (3.3 − 3.0)/330 = 0.91 mA` per blue LED, **assuming** `VF=3.0 V` and 74HC595 output near rail. Ten ≈9.1 mA. Actual VF and output HIGH voltage can materially change brightness/current; 3.3 V gives little headroom for blue LEDs. The 74HC595 output total-current and per-pin limits must be checked.

**MOC/ULN estimate:** Assuming MOC LED `VF = 1.3 V` and ULN2803A output `VCE(sat) = 0.9 V` at this operating point, `IF ≈ (3.3 − 1.3 − 0.9)/150 = 7.33 mA` each; eight ≈58.7 mA. The Darlington output drop is substantial and varies with sink current and temperature. At `VF = 1.5 V` and `VCE(sat) = 1.1 V`, current falls to about **4.67 mA**, potentially below the MOC3063 guaranteed trigger requirement. **Do not release this resistor value without confirming maximum trigger current over temperature, minimum rail voltage, ULN saturation and 74HC595 HIGH drive.** ULN2803A input currents also load the 74HC595 outputs; include those currents in the 3.3 V budget once characterized.

**Pico warning:** A complete Pico board includes its own power management; its 3V3 pin is not necessarily an ordinary 3.3 V input in all operating modes. Do **not** connect an external AMS1117 to the Pico 3V3 pin without checking the particular RP2040/RP2350 Pico schematic, VSYS/VBUS rules, USB backfeeding and regulator interaction. If powering Pico via VSYS from 5 V, the current/efficiency budget changes; the Pico's 3.3 V rail and external 3.3 V rail must be architected explicitly.

## 5. LMR38020 buck efficiency and TP1 ripple

For an illustrative **85% efficiency at this operating point** (not a verified TI efficiency curve value):

`P_TP1 ≈ P_5V,out / η = 0.989 / 0.85 = 1.164 W`

At an illustrative 34 V TP1:

`I_TP1,avg ≈ P_TP1 / V_TP1 = 1.164 / 34 = 0.03423 A ≈ 34.2 mA`

`ΔVpp ≈ 0.03423 / (50 × 0.0010047) = 0.681 Vpp ≈ 0.68 Vpp`

For nominal 24 VAC, `V_TP1,min ≈ 33.24 − 0.68 ≈ 32.6 V`; for nominal 26 VAC, `≈ 36.07 − 0.68 ≈ 35.4 V`. These are *approximate troughs under the stated assumptions*, not worst-case guarantees.

### Sensitivity to buck efficiency

Assume the same 0.989 W output, 34 V nominal TP1 and nominal 1004.7 µF:

| Assumed η | Buck input power | TP1 average current | Approx. half-wave ripple |
|---:|---:|---:|---:|
| 75% | 1.319 W | 38.8 mA | 0.77 Vpp |
| 80% | 1.236 W | 36.4 mA | 0.72 Vpp |
| **85%** | **1.164 W** | **34.2 mA** | **0.68 Vpp** |
| 90% | 1.099 W | 32.3 mA | 0.64 Vpp |

At bulk capacitor **−20%** tolerance, nominal 85% efficiency and ignoring the ceramic contribution, ripple increases from ~0.68 Vpp to roughly **0.86 Vpp**. If peak load changes, ripple scales approximately with load current as long as ripple remains small and other assumptions hold.

### Buck dissipation

`P_buck,loss = P_5V,out × (1/η − 1)`

At 85%: `0.989 × (1/0.85 − 1) = 0.175 W` total converter loss **estimate** (IC, inductor, switching, etc.). Do not treat all of this as IC junction dissipation. Actual efficiency at **34 V in, 5 V out, ~0.20 A** must be checked against TI curves or measured.

## 6. AMS1117-3.3 LDO calculations

`I_LDO,out ≈ 195.8 mA`

`P_LDO,in ≈ 5.0 × 0.1958 = 0.979 W`

`P_LDO,out ≈ 3.3 × 0.1958 = 0.6461 W`

`P_LDO,heat ≈ (5.0 − 3.3) × 0.1958 = 0.3329 W` plus quiescent-current contribution.

Idealized linear-stage efficiency `≈ 3.3 / 5.0 = 66%`. This is normal for a linear regulator and distinct from the buck's 85% assumption. Check LDO dropout at maximum load, recommended input/output capacitor values and ESR stability, copper thermal area, ambient temperature and maximum junction temperature. 0.33 W is much better than the old ~1.3 W AMS1117-5.0 loss, but still needs verification in a hot outdoor enclosure.

## 7. LMR38020 adjustable 5 V feedback — TI datasheet §9.2.2.3

**Verified from the user-provided TI excerpt:** `VREF = 1.0 V nominal`, `RFBT` (VOUT to FB) recommended **100 kΩ**, maximum **1 MΩ**. TI's 5 V design example chooses `RFBB = 24.9 kΩ` (FB to GND). These supersede earlier speculative divider combinations.

`VOUT = VREF × (1 + RFBT/RFBB)`

`VOUT = 1.0 × (1 + 100/24.9) = 5.0161 V` **nominal**.

Divider current `Idivider ≈ 5.0161 V / (100 kΩ + 24.9 kΩ) = 40.16 µA`; divider power `≈ 0.202 mW`. This current is additional to the previously estimated load but negligible relative to ~188 mA. Check actual reference accuracy, FB input bias, resistor tolerances and transient limits before declaring a guaranteed output range.

**Implementation:** RFBT = 100 kΩ from 5 V output to FB; RFBB = 24.9 kΩ from FB to GND. Place the divider close to FB, sense after the output filter and route away from the SW node.

## 8. Buck inductor selection — TI datasheet §9.2.2.3 excerpt

TI states that inductor ripple is commonly targeted at **20–40% of maximum device output current**, with 30% typical. Crucially, for a design whose load is far below the converter's 2 A rating, TI directs the designer to use the **maximum device current** in the calculation, **not** the ~0.198 A estimated baseline actual load.

For a first-order continuous-conduction buck approximation:

`ΔIL ≈ VOUT × (VIN − VOUT) / (VIN × L × fSW)`

`L ≈ VOUT × (VIN − VOUT) / (VIN × fSW × IOUT,max × K)`

where `K` is the chosen ripple fraction, `IOUT,max = 2 A` for this device, and `fSW` is the actual configured switching frequency. TI's **15 µH** example follows its own example conditions and **does not automatically make 33 µH wrong** for this design.

For the selected **33 µH ±20% Sumida CDRH129RNP-330MC**, at `VIN=34 V` and `VOUT=5 V`:

`ΔIL ≈ 0.129 A` at `fSW=1 MHz`; `≈ 0.258 A` at `fSW=500 kHz` (illustrative frequencies, **not verified for this part's actual configured switching frequency**).

Relative to 2 A device rating, these are about 6.5% and 12.9%, respectively — below TI's usual 20–40% target. Higher inductance reduces ripple but can affect size, cost, load-step response and control behavior. At ~0.188 A actual load, operation may enter DCM/pulse-skipping, so the CCM formula does **not** predict the exact light-load waveform or efficiency.

**Before final selection:** verify LMR38020FDDAR switching frequency / RT setting, minimum on-time at 34–40+ V to 5 V, the full TI inductor selection guidance, and the inductor's **saturation-current rating against high-side switch current limit**, not merely the ~0.188 A operating current. The quoted 4.25 A rating must be checked for whether it is saturation or temperature-rise current. Also verify effective input and output ceramics, BOOT, enable/UVLO, EMI, and exposed-pad layout. A 1000 µF reservoir does not replace local VIN ceramics.

## 9. Eight TRIAC outputs and 74HC595 drive

**Control chain:** Pico GPIO (3.3 V) → 74HC595 outputs → ULN2803A inputs (one per channel) → corresponding ULN2803A open-collector outputs → MOC3063 input LED cathodes (pin 2). Each MOC3063 input LED anode (pin 1) connects through its own **150 Ω provisional** resistor to 3.3 V. ULN2803A GND pin connects to controller GND. The ULN2803A COM pin is the common cathode of its internal inductive flyback diodes; for optocoupler LED loads, **leave COM unconnected**, rather than tying it to 3.3 V by habit. Verify exact package pin numbering.

- **No external MOSFET gate resistors or gate pull-downs** are used in this version. The ULN2803A has built-in input resistors and Darlington stages; its input characteristics must be verified for **3.3 V 74HC595 HIGH** levels and the 74HC595's available source current.
- The ULN2803A is not a logic-level MOSFET: its Darlington saturation voltage reduces voltage across the MOC3063 LED resistor. With 150 Ω, the nominal example is ~7.33 mA per channel, but a plausible adverse combination gives ~4.67 mA. Validate against guaranteed optotriac LED trigger current at all temperatures; adjust drive architecture if necessary. The ULN2803A package power at the assumed 0.9 V × 7.33 mA × 8 is ~53 mW in output stages, excluding input-stage losses; verify thermal limits.
- **ULN2803A input currents are additional 3.3 V loads** not included in the numerical estimates. A 74HC595 may not source the necessary input current while maintaining the required HIGH voltage; measure or calculate from worst-case datasheets. If the interface cannot meet guaranteed margins, revise the interface rather than treating typical bench operation as proof.
- Ten separate blue indicator LEDs remain on 74HC595 outputs at 330 Ω each. Verify aggregate 74HC595 current and output HIGH levels.
- Output TRIAC is **BT136-800E**, switched from 24 VAC through MOC3063. The previously pictured schematic included an **R3 ≈330 Ω gate resistor** and a **47 Ω + 100 nF snubber**, plus **SMAJ48CA**. **Do not assume that the gate drive is adequate at only 24 VAC**: check the BT136-800E's quadrant-dependent IGT, MOC3063 on-state voltage, zero-cross inhibit voltage, available AC instantaneous voltage and worst-case line voltage. A zero-cross optocoupler may have difficulty firing certain TRIAC/load combinations at low voltage; bench test with the actual solenoid.
- The **47 Ω + 100 nF** series RC snubber draws reactive off-state leakage: approximately `I ≈ 2π × 50 × 100 nF × 24 V ≈ 0.75 mA RMS` at 24 VAC, neglecting R. Verify solenoid releases fully and snubber resistor pulse/power ratings. Choose capacitor type and voltage rating for the actual secondary environment and transient conditions.
- **SMAJ48CA:** 48 V standoff is above nominal 24 VAC peak (~34 V), but assess high-line/no-load transformer voltage, TVS breakdown/clamp, repetitive energy, inductive turn-off and TRIAC off-state dV/dt. A TVS does not automatically replace a snubber.
- Solenoid current **bypasses** the US1M controller rectifier if it is supplied directly from the AC transformer. Still include all simultaneously energized solenoids in the **transformer VA**, fuse, connector, PCB copper and TRIAC thermal ratings. Solenoid **inrush/holding** current and 50 m cable transients are separate from the electronics power budget.

## 10. 0–10 V analogue inputs — replace LM324 with protected dividers

**Proposed per-input starting point (not yet fault-rated):**

```text
0–10 V SENSOR + --- 24.9 kΩ ---o--- 1 kΩ --- ADC input
                               |
                              10 kΩ
                               |
                          analogue GND

ADC input --- 100 nF --- analogue GND
ADC input --- low-leakage positive/negative clamps (to be engineered)
```

`V_ADC = V_SENSOR × 10/(24.9+10) = 0.28653 × V_SENSOR`

At 10.0 V: `V_ADC = 2.865 V`. At 12 V input: `V_ADC = 3.438 V` **before clamp action**, already beyond the nominal 3.3 V ADC supply; protection is therefore necessary.

Divider input resistance: `34.9 kΩ`. Divider current at 10 V: `10/34.9k = 0.287 mA`. Divider Thevenin resistance: `24.9k || 10k ≈ 7.13 kΩ`. With 1 kΩ ADC series resistance and 100 nF at ADC, approximate small-signal RC time constant is `(7.13k + 1k) × 100 nF = 0.813 ms`, cutoff ≈196 Hz (before ADC sampling effects). This source impedance may be too high for the Pico ADC acquisition time at high sampling rates: validate settling, input sampling capacitance and accuracy; use longer acquisition time, a smaller divider or buffer if needed.

**Input-protection requirements:**

1. Select **low-leakage** clamp diodes or a suitable low-capacitance/low-leakage protection IC; avoid uncharacterized high-leakage Zeners directly on precision ADC nodes. Account for leakage over outdoor temperatures.
2. Design for **overvoltage, reverse polarity, ESD, EFT, cable-induced surges and accidental 24 VAC miswiring**, with a documented maximum fault voltage/energy. The divider and 1 kΩ resistor alone are not guaranteed to survive these faults.
3. Calculate worst-case clamp current and resistor power at the chosen fault voltage. Check both positive and negative ADC absolute maximum input limits, **including when 3.3 V is OFF**.
4. Clamping to 3.3 V can **back-power the rail** during faults or power-off; use a clamp architecture and rail sink/limiting strategy that prevents this.
5. Protect at the **connector entry** with appropriately rated TVS/ESD devices and series impedance; place sensitive ADC filtering and clamps near the MCU. Use return paths, grounding and cable shielding appropriate for long outdoor sensor wires.
6. Confirm whether the sensor outputs are truly ground-referenced **0–10 V** and share a suitable ground. Avoid ground loops and assess common-mode offsets; differential/isolated input may be necessary for some installations.
7. Account for 1% resistor tolerance and Pico ADC gain/offset/reference error. Calibrate in firmware if accuracy matters. Provide test points for sensor input and ADC node.
8. Do not use an uncharacterized 3.3 V Zener as an ADC precision clamp without leakage, knee-current and tolerance analysis.

## 11. Safety, protection and production checks

- Verify transformer is appropriately isolated and rated for **eight solenoids concurrently**, including inrush and controller load; secondary voltage may be much higher at no load.
- Add appropriately rated **secondary fuse / PTC** and consider primary protection in the transformer installation as required by applicable standards. A rectifier diode is not a fuse or two-rail protection device.
- Evaluate **reservoir-capacitor startup inrush** and repetitive charging pulses; verify US1M 30 A non-repetitive surge limit is not misapplied to repetitive peaks.
- Confirm 63 V electrolytic voltage margin under high mains and no-load transformer conditions; verify its 105°C lifetime and ripple-current rating.
- Use proper PCB clearance, isolation boundaries, trace widths, connector current rating and surge suppression for the transformer secondary and field wiring. Do not assume the entire system is SELV unless installation/transformer conditions establish that.
- Assess heat in the LMR38020, 33 µH inductor, AMS1117-3.3, TRIACs, rectifier and snubber resistors at worst-case enclosure temperature.
- Verify the real Pico 3.3 V power path and USB connection behaviour before powering it from the external regulator.
- Confirm regulator output ripple/transient behaviour while all eight optocouplers switch and while solenoids energize/de-energize.
- Measure TP1 **peak, valley and ripple**, 5 V, 3.3 V, buck efficiency and temperatures at low/high line and worst-case load. A DMM average reading does not reveal charging-current peaks.
- Confirm exact manufacturer datasheets and footprints for the US1M, MOC3063, ULN2803A, 74HC595 and TRIACs.

## 12. Quick calculation summary (illustrative nominal case)

| Quantity | Estimate / assumption |
|---|---:|
| AC input | 24–26 VAC RMS, 50 Hz |
| Rectification | Single-diode half-wave |
| TP1 nominal peak at 24 VAC | 33.24 V (0.7 V diode drop assumed) |
| TP1 nominal peak at 26 VAC | 36.07 V (same assumption) |
| Bulk + ceramic nominal capacitance | 1004.7 µF |
| 3.3 V rail current | 195.8 mA **plus ULN input currents** |
| 5 V rail current (including LDO input) | 197.8 mA **plus ULN input currents and regulator IQ** |
| 5 V buck output power | 0.989 W **baseline, excludes ULN input current** |
| Buck efficiency | 85% **assumed** |
| TP1 input power | 1.164 W baseline |
| TP1 current at 34 V | 34.2 mA baseline |
| TP1 ripple at 50 Hz, nominal C | ~0.68 Vpp baseline |
| TP1 ripple with 1000 µF bulk at −20% tolerance | ~0.86 Vpp baseline |
| Buck total estimated loss | ~0.175 W baseline |
| AMS1117-3.3 heat | ~0.333 W baseline |
| AMS1117-3.3 ideal efficiency | 66% |
| 10 blue LEDs at 330 Ω, 3.3 V | ~9.1 mA total, conditional on VF and HC595 VOH |
| 8 MOC3063 LEDs at 150 Ω, 3.3 V via ULN2803A | ~58.7 mA total at assumed VF = 1.3 V, VCE(sat) = 0.9 V |
| 10 V sensor after 24.9 kΩ / 10 kΩ divider | 2.865 V |

**Accounting caveat:** The budget excludes ULN2803A input-stage currents and AMS1117 quiescent current, and assumes the Pico and flash are not double-counted. These must be resolved before specifying maximum current, efficiency, ripple or transformer capacity. All values are nominal planning estimates, not worst-case specifications.

### Open design checks before KiCad production release

1. Verify 100 kΩ / 24.9 kΩ feedback, switching frequency, BOOT, ceramics, 33 µH saturation and minimum on-time from TI datasheet.
2. Decide Pico 3.3 V power path and USB interaction.
3. Verify 74HC595 3.3 V HIGH output against **ULN2803A input-current and switching requirements**.
4. Verify the **150 Ω** optocoupler resistors deliver guaranteed MOC3063 triggering across supply and temperature tolerances; revise driver if they do not.
5. Specify sensor fault limits and validate clamps, resistor pulse ratings and powered-off protection.
6. Verify MOC3063/BT136-800E firing at 24 VAC with actual solenoids.
7. Check rectifier repetitive charging pulses, transformer capacity, EMI, thermal performance and PCB layout.
8. Measure input ripple, both regulated rails, optocoupler LED current, ULN input currents and efficiency under worst-case load.

---

*Calculations are first-pass engineering estimates. They are intended as annotated KiCad design notes and a review checklist, not as proof of component suitability or electrical safety.*
