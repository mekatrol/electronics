# PCB Design & Schematic Review Guide

**Version:** 2026.11.01  
**Scope:** schematic design, PCB layout, project-specific engineering, manufacturing release  
**Coverage:** 186 steps across 26 review sections.

## How to use

Review the check in order or by risk. Choose Pass, Fail, Needs Review or N/A (with justification). Record evidence: schematic, calculation, screenshot, datasheet, supplier requirement or test report. Resolve critical findings before freezing a production revision.

The guide combines authored source prompts with an expanded engineering interpretation. It is not a regulatory standard or replacement for the exact device datasheet. Conditions and source priority are described below.

## Source precedence

- Applicable regulations and safety requirements
- Exact device datasheet / validated manufacturer reference design
- Current selected fabricator and assembler capabilities
- Later authoritative engineering guidance
- Supplied 2025 PDF checklists
- User original preferences, preserved where consistent

## Exceptions that need explicit engineering judgement

- No single default trace width, via drill or component derating satisfies every PCB; use worst-case device and fabricator-specific design calculations.
- The PDF checklist specifies >70% ground coverage, 9+ thermal vias, untented thermal vias, 2× capacitor voltage, 22 Ω USB resistors and a 1.5 kΩ D+ pull-up as checklist suggestions. They are conditional, not universally mandatory.
- Review the selected JLCPCB PCB/PCBA service offering before applying its specific fiducial/edge-rail values.
- A critical failure blocks release until resolved or formally waived by an authorized reviewer; a not-applicable result needs an explanation for high-risk checks.

## Full review steps


## SCH-01 — Component selection and ratings
Review the logic, component choices, interface electrical requirements and failure conditions before PCB layout is frozen.

### SCH-001 — All components are currently in production (not obsolete/NRND)
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: All components are currently in production (not obsolete/NRND).

**Why:** Late-life components can stop production or force a redesign.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check every purchase/manufacturer part number against manufacturer lifecycle notices and distributor supply data; record last-order concerns.

**Pass when:**
- All build-critical components have acceptable lifecycle status or an approved replacement plan.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Add a sourced margin calculation or reasoned exception; do not impose one blanket derating factor for every part.
- Stock at a distributor is not proof that a device remains in production.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation; BOM with lifecycle fields

**Sources:**
- PD-SCH p.2: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-002 — Second sources available for critical single-source components
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Second sources available for critical single-source components.

**Why:** A sole supplier creates supply-chain risk.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Identify compatible alternates with the same footprint, ratings, pinout and qualification or record a stocked contingency.

**Pass when:**
- Critical single-source parts have a credible sourcing mitigation.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Add a sourced margin calculation or reasoned exception; do not impose one blanket derating factor for every part.
- Avoid assuming a similarly labelled clone is electrically interchangeable.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.2: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-003 — Package types are appropriate (SMT sizes reasonable, THT where needed)
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Package types are appropriate (SMT sizes reasonable, THT where needed).

**Why:** An ill-chosen package can be hard to place, inspect or rework.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check hand/automated assembly plan, land patterns, component mass, heat flow and rework tools.

**Pass when:**
- Packages can be procured and reliably assembled using the intended process.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Add a sourced margin calculation or reasoned exception; do not impose one blanket derating factor for every part.
- A smaller component is not always better for power or mechanical stress.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.2: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-004 — Voltage ratings have adequate margin (check against net voltages)
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Voltage ratings have adequate margin (check against net voltages).

**Why:** Overvoltage and ceramic capacitance loss can destroy parts or defeat bypassing.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Compare worst-case rail and transient peaks to device limits, derating policy and MLCC DC-bias graphs.

**Pass when:**
- Worst-case stress and effective capacitance meet the application/design requirements.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Add a sourced margin calculation or reasoned exception; do not impose one blanket derating factor for every part.
- PDF suggests 2× capacitor voltage as a typical rule; do not enforce universally. Automotive, safety, electrolytic and MLCC requirements vary.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.2: Predictable Designs — Design Review Checklist: Schematic Circuit
- JOHN-VID t=875s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-005 — Power ratings have adequate margin for resistors/regulators
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Power ratings have adequate margin for resistors/regulators.

**Why:** Resistor and regulator ratings fall with ambient temperature and cooling.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Calculate worst-case dissipated power and apply the component temperature derating curve.

**Pass when:**
- Junction/film temperature and dissipation remain within the specified envelope.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Add a sourced margin calculation or reasoned exception; do not impose one blanket derating factor for every part.
- Do not treat nominal package power as unconditional.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.2: Predictable Designs — Design Review Checklist: Schematic Circuit
- JOHN-VID t=875s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-006 — Capacitor voltage ratings include derating
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Capacitor voltage ratings include derating (typically 2x minimum).

**Why:** Overvoltage and ceramic capacitance loss can destroy parts or defeat bypassing.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Compare worst-case rail and transient peaks to device limits, derating policy and MLCC DC-bias graphs.

**Pass when:**
- Worst-case stress and effective capacitance meet the application/design requirements.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Add a sourced margin calculation or reasoned exception; do not impose one blanket derating factor for every part.
- PDF suggests 2× capacitor voltage as a typical rule; do not enforce universally. Automotive, safety, electrolytic and MLCC requirements vary.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.3: Predictable Designs — Design Review Checklist: Schematic Circuit
- JOHN-VID t=875s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## SCH-02 — Power supply and protection
Review the logic, component choices, interface electrical requirements and failure conditions before PCB layout is frozen.

### SCH-007 — Input protection present (reverse polarity, overvoltage)
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Input protection present (reverse polarity, overvoltage).

**Why:** Incorrect supply connection can cause damage or unsafe failure.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Assess all possible external supply voltages, polarity reversals and surge/connection events.

**Pass when:**
- Appropriate protection is demonstrated or the input is demonstrably protected upstream.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Protection selection is application and standard dependent; component presence alone is not proof of protection.
- Fuse/TVS choices must coordinate with fault energy and power source.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.3: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-008 — Inrush current limiting components present if needed
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Inrush current limiting components present if needed.

**Why:** Startup surges can stress contacts, sources, regulators and protection devices.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Estimate input capacitance and source impedance, model hot-plug and test worst-case startup.

**Pass when:**
- Inrush is compatible with the source, connectors, fuses and IC absolute limits.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Protection selection is application and standard dependent; component presence alone is not proof of protection.
- A current limiter is not always required; assess before adding one.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.3: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-009 — Power supply voltages are reasonable for the circuitry
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Power supply voltages are reasonable for the circuitry.

**Why:** Power domains must satisfy required operating range and startup sequencing.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Build a power tree showing tolerance, ripple, sequencing, transient droop and every load.

**Pass when:**
- Every device is supplied within its rated operating range in each permitted state.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Protection selection is application and standard dependent; component presence alone is not proof of protection.
- Check shutdown/back-powering through I/O as well as normal operation.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.3: Predictable Designs — Design Review Checklist: Schematic Circuit
- JOHN-VID t=368s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-010 — Switching regulator has input and output capacitors per datasheet
**Priority:** high · **Applicable:** Switch-mode power supply designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Switching regulator has input and output capacitors per datasheet.

**Why:** Regulators may oscillate or exceed ripple limits without appropriate capacitor ESR and values.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check exact regulator datasheet, min/max effective capacitance, ESR and loop compensation.

**Pass when:**
- Selected input/output network meets specified stability and transient requirements.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Protection selection is application and standard dependent; component presence alone is not proof of protection.
- Do not copy capacitance values without considering DC bias and placement.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.3: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-011 — Linear regulator input/output voltage differential appropriate
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Linear regulator input/output voltage differential appropriate.

**Why:** LDO dropout and dissipation vary with current, tolerance and temperature.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check minimum VIN−VOUT at maximum load and calculate (VIN−VOUT)×Iout power.

**Pass when:**
- Required output regulation and thermal safety are maintained in worst-case operation.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Protection selection is application and standard dependent; component presence alone is not proof of protection.
- Consider reverse current or input sequencing where relevant.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.3: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-012 — ESD protection diodes/TVS on all external-facing connections
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: ESD protection diodes/TVS on all external-facing connections.

**Why:** External ports allow system-level discharges that may exceed chip-level ESD ratings.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Review exposed pins and cable paths; specify appropriately placed TVS/protection with correct voltage, capacitance and discharge path.

**Pass when:**
- All exposed ports have documented ESD strategy appropriate to product conditions.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Protection selection is application and standard dependent; component presence alone is not proof of protection.
- An all-ports TVS rule is not universal; use a risk-based design and compliance target.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.3: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-013 — Fuses or PTC devices sized appropriately if present
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Fuses or PTC devices sized appropriately if present.

**Why:** Protection can fail to disconnect faults if thermal time/current characteristics are wrong.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Compare maximum normal current, inrush, fault current, interrupt rating and fuse/PTC time-current curves.

**Pass when:**
- Protection opens/limits under credible faults and does not nuisance-trip normally.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Protection selection is application and standard dependent; component presence alone is not proof of protection.
- A PTC is not the same as a safety-certified fuse.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.4: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## SCH-03 — Bypass and decoupling
Review the logic, component choices, interface electrical requirements and failure conditions before PCB layout is frozen.

### SCH-014 — Every IC has at least one decoupling capacitor per power pin
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Every IC has at least one decoupling capacitor per power pin.

**Why:** Each supply pin needs a low-inductance transient current path appropriate to its function.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Map pins to the device decoupling table and identify shared pins, internal supplies and mandatory cap location.

**Pass when:**
- Decoupling topology matches the device datasheet rather than a blind one-cap-per-pin count.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A capacitor per supply pin is a useful screening question, not a universal requirement; some devices group pins or prescribe special networks.
- Some pins share capacitors or require special values/layout.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.4: Predictable Designs — Design Review Checklist: Schematic Circuit
- TI-DEC : Texas Instruments — Mixed Signals, Grounding and Bypass Capacitors — https://www.ti.com/video/6245227303001

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-015 — Decoupling capacitor values match IC datasheet recommendations
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Decoupling capacitor values match IC datasheet recommendations.

**Why:** The wrong impedance profile may allow high-frequency supply noise.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check recommended values, package/ESL, effective capacitance at DC bias and supply loop inductance.

**Pass when:**
- Capacitor network satisfies device-specific design guidance.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A capacitor per supply pin is a useful screening question, not a universal requirement; some devices group pins or prescribe special networks.
- Avoid assuming that many arbitrary capacitor values improve performance.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.4: Predictable Designs — Design Review Checklist: Schematic Circuit
- TI-DEC : Texas Instruments — Mixed Signals, Grounding and Bypass Capacitors — https://www.ti.com/video/6245227303001

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-016 — Mix of capacitor values present (bulk + ceramic) where appropriate
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Mix of capacitor values present (bulk + ceramic) where appropriate.

**Why:** Bulk and local bypass address different transient frequencies and energy demands.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check transient load spectrum, input-source impedance, regulator stability and bulk placement.

**Pass when:**
- Bulk and local parts are present where required and are stable with the regulator.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A capacitor per supply pin is a useful screening question, not a universal requirement; some devices group pins or prescribe special networks.
- Parallel MLCCs may create anti-resonances; different values are not automatically better.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.4: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-017 — Analog ICs have separate decoupling from digital where recommended
**Priority:** standard · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Analog ICs have separate decoupling from digital where recommended.

**Why:** Noise on mixed supply pins can couple into precision analog functions.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Follow IC pin-by-pin recommendations and isolate or filter sensitive supply branches as specified.

**Pass when:**
- Sensitive rails meet noise and impedance requirements.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A capacitor per supply pin is a useful screening question, not a universal requirement; some devices group pins or prescribe special networks.
- Separate capacitor networks do not automatically require physically separate ground planes.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.4: Predictable Designs — Design Review Checklist: Schematic Circuit
- TI-DEC : Texas Instruments — Mixed Signals, Grounding and Bypass Capacitors — https://www.ti.com/video/6245227303001

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## SCH-04 — Clock and timing
Review the logic, component choices, interface electrical requirements and failure conditions before PCB layout is frozen.

### SCH-018 — Crystal has correct load capacitors (verify with datasheet)
**Priority:** high · **Applicable:** Crystal/oscillator circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Crystal has correct load capacitors (verify with datasheet).

**Why:** Incorrect crystal loading causes frequency error or startup failure.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Use the crystal CL target, pin and PCB stray capacitance, and the datasheet load-cap model; check ESR and drive limits.

**Pass when:**
- Computed and selected C1/C2 produce the required effective CL within tolerance.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not install external load capacitors for oscillators or devices that already include them unless the vendor requires them.
- CL≈C1×C2/(C1+C2)+Cstray for common two-cap networks; layout stray capacitance matters.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.4: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-019 — Crystal load capacitor calculation is correct (CL = (C1*C2)/(C1+C2) + Cstray)
**Priority:** high · **Applicable:** Crystal/oscillator circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Crystal load capacitor calculation is correct (CL = (C1*C2)/(C1+C2) + Cstray).

**Why:** Incorrect crystal loading causes frequency error or startup failure.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Use the crystal CL target, pin and PCB stray capacitance, and the datasheet load-cap model; check ESR and drive limits.

**Pass when:**
- Computed and selected C1/C2 produce the required effective CL within tolerance.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not install external load capacitors for oscillators or devices that already include them unless the vendor requires them.
- CL≈C1×C2/(C1+C2)+Cstray for common two-cap networks; layout stray capacitance matters.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.5: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-020 — Oscillator circuits match datasheet reference design
**Priority:** standard · **Applicable:** Crystal/oscillator circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Oscillator circuits match datasheet reference design.

**Why:** Oscillator reference circuits reflect device drive and pin topology.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Compare oscillator type, external resistor/capacitor population and power connections with official reference schematic.

**Pass when:**
- Matches supported oscillator arrangement or has documented validated deviation.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not install external load capacitors for oscillators or devices that already include them unless the vendor requires them.
- Do not add load capacitors to clock modules with driven CMOS outputs without instructions.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.5: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-021 — Clock distribution buffers present if needed for fanout
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Clock distribution buffers present if needed for fanout.

**Why:** Long or heavily loaded clocks can violate amplitude, edge rate and timing limits.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Compute fanout/capacitance and skew; assess clock buffering, termination and timing budget.

**Pass when:**
- Timing and loading meet every receiver specification.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not install external load capacitors for oscillators or devices that already include them unless the vendor requires them.
- Avoid adding buffers unless propagation and skew impacts are understood.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.5: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## SCH-05 — Digital interfaces
Review the logic, component choices, interface electrical requirements and failure conditions before PCB layout is frozen.

### SCH-022 — I2C buses have pullup resistors
**Priority:** standard · **Applicable:** I²C buses · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: I2C buses have pullup resistors (typically 2.2kΩ - 10kΩ).

**Why:** Open-drain I²C needs appropriate pull-up strength to meet rise time and sink current.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Calculate bus capacitance and Rpullup from maximum rise time and VOL/IOL limits; include all installed pullups.

**Pass when:**
- Measured/calculated rise time and low-level sink current meet selected I²C mode.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- 2.2–10 kΩ in the PDF is illustrative, not a universal resistor range.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.5: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-023 — I2C pullup values appropriate for bus speed and capacitance
**Priority:** standard · **Applicable:** I²C buses · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: I2C pullup values appropriate for bus speed and capacitance.

**Why:** Open-drain I²C needs appropriate pull-up strength to meet rise time and sink current.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Calculate bus capacitance and Rpullup from maximum rise time and VOL/IOL limits; include all installed pullups.

**Pass when:**
- Measured/calculated rise time and low-level sink current meet selected I²C mode.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- 2.2–10 kΩ in the PDF is illustrative, not a universal resistor range.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.5: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-024 — SPI signals have correct connections (MISO/MOSI not swapped)
**Priority:** standard · **Applicable:** SPI interfaces · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: SPI signals have correct connections (MISO/MOSI not swapped).

**Why:** Pin naming can depend on controller vs peripheral viewpoint.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Trace each clock, data direction, chip-select and polarity from controller to selected slave.

**Pass when:**
- Pin-to-pin wiring matches device-specific SPI roles and mode.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- Use SDO/SDI labels to avoid MISO/MOSI naming ambiguity.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.5: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-025 — SPI chip selects are active-low with pullups where needed
**Priority:** standard · **Applicable:** SPI interfaces · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: SPI chip selects are active-low with pullups where needed.

**Why:** Floating CS can cause unintended bus contention during reset.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Verify selected polarity, pull resistor and startup state for every SPI peripheral.

**Pass when:**
- No unintended chip is selected during power-up, reset or high-impedance states.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- Many devices support active-high or internal pulls; consult datasheet.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.5: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-026 — UART connections correct (TX to RX, RX to TX)
**Priority:** standard · **Applicable:** UART/serial interfaces · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: UART connections correct (TX to RX, RX to TX).

**Why:** UART link fails if both outputs or both inputs are connected.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Trace MCU TX→peer RX and MCU RX←peer TX, including level shifters and transceivers.

**Pass when:**
- End-to-end TX/RX polarity, voltage and pinout match interface design.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- RS-485 transceiver labels DI/RO/DE/RE are different from UART names; examine direction-control pins.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.6: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-027 — USB data lines have correct termination (22 Ω series resistors)
**Priority:** critical · **Applicable:** USB interfaces · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: USB data lines have correct termination (22Ω series resistors).

**Why:** USB signal integrity relies on PHY-specific source impedance and termination.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Read the USB PHY reference schematic; check whether series resistors are required, integrated or disallowed.

**Pass when:**
- D+/D− network exactly matches PHY and USB speed requirements.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- 22 Ω is an example, not a universal USB termination rule.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.6: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-028 — USB has correct pullup on D+ (1.5k Ω for full-speed)
**Priority:** standard · **Applicable:** USB interfaces · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: USB has correct pullup on D+ (1.5kΩ for full-speed).

**Why:** USB attach/speed signalling may use PHY-controlled termination.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check full-/low-/high-speed negotiation, internal pull-up support and role/connector design.

**Pass when:**
- Pull-up implementation matches the USB controller/PHY reference design.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- Do not add an external 1.5 kΩ D+ pull-up if the controller already implements it.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.6: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-029 — Ethernet has magnetics and correct termination resistors
**Priority:** standard · **Applicable:** Ethernet interfaces · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Ethernet has magnetics and correct termination resistors.

**Why:** PHY magnetics, termination and biasing are PHY- and interface-dependent.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check PHY datasheet, transformer spec, MDI pair design and common-mode/shield strategy.

**Pass when:**
- Magnetics and termination meet the selected Ethernet PHY design.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- Not all Ethernet variants use external magnetics; PoE adds special constraints.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.6: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-030 — CAN bus has 120 Ω termination at both ends only
**Priority:** standard · **Applicable:** CAN bus interfaces · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: CAN bus has 120Ω termination at both ends only.

**Why:** Incorrect CAN termination causes reflections, excess loading and unreliable communication.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Identify bus topology and endpoint locations; verify transceiver common-mode, split termination/bias if applicable.

**Pass when:**
- Only physical trunk endpoints receive appropriate termination (typically 120 Ω each).
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- Nodes on a stub should not independently add an endpoint resistor.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.6: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-031 — Level shifters present where signals cross voltage domains
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Level shifters present where signals cross voltage domains.

**Why:** Voltage-domain mismatch can damage input structures or violate thresholds.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Calculate VIH/VIL, VOH/VOL, power-off injection and absolute-maximum limits for each cross-domain connection.

**Pass when:**
- Every signal interface has valid electrical logic margins and powered-off behavior.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- Open-drain level translators, push-pull devices and timing constraints differ.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.6: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-032 — Logic levels compatible between connected ICs
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Logic levels compatible between connected ICs.

**Why:** Voltage-domain mismatch can damage input structures or violate thresholds.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Calculate VIH/VIL, VOH/VOL, power-off injection and absolute-maximum limits for each cross-domain connection.

**Pass when:**
- Every signal interface has valid electrical logic margins and powered-off behavior.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Typical resistor values in the PDF are examples only; many transceivers and USB controllers integrate some functions.
- Open-drain level translators, push-pull devices and timing constraints differ.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.6: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## SCH-06 — Analog circuits
Review the logic, component choices, interface electrical requirements and failure conditions before PCB layout is frozen.

### SCH-033 — Op-amp feedback networks appear reasonable (gain, stability)
**Priority:** standard · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Op-amp feedback networks appear reasonable (gain, stability).

**Why:** Feedback stability and phase margin depend on load and gain network.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Calculate intended gain/bandwidth, verify common-mode and output swing; examine capacitive loads.

**Pass when:**
- Gain, offset, phase margin and startup meet requirements.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not automatically split analog and digital ground; protect return paths and follow mixed-signal device guidance.
- Voltage-feedback, current-feedback and decompensated amplifiers use different rules.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.7: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-034 — ADC reference voltage is stable (buffered, filtered)
**Priority:** high · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: ADC reference voltage is stable (buffered, filtered).

**Why:** Reference noise directly appears as conversion noise or error.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Audit reference source, capacitor placement, current requirements, buffering and digital coupling.

**Pass when:**
- Reference is within voltage, noise, tolerance and dynamic load limits.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not automatically split analog and digital ground; protect return paths and follow mixed-signal device guidance.
- Some ADCs require particular reference drivers and series isolation.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.7: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-035 — ADC input range matches expected signal levels
**Priority:** critical · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: ADC input range matches expected signal levels.

**Why:** Out-of-range ADC inputs saturate or conduct into protection structures.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Calculate min/max input and common-mode voltages with sensor tolerance and faults.

**Pass when:**
- Signals stay within the specified linear and absolute input envelope.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not automatically split analog and digital ground; protect return paths and follow mixed-signal device guidance.
- Switched-cap ADCs impose acquisition settling limits.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.7: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-036 — Input protection present on ADC inputs (clamp diodes, series R)
**Priority:** critical · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Input protection present on ADC inputs (clamp diodes, series R).

**Why:** Unprotected high-energy inputs can inject current or damage analog inputs.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check clamp current, series resistance, ADC sampling charge, leakage and ESD waveforms.

**Pass when:**
- Protection limits injected current without violating measurement accuracy/bandwidth.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not automatically split analog and digital ground; protect return paths and follow mixed-signal device guidance.
- External clamp diode capacitance and leakage can affect precision measurements.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.7: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-037 — Anti-aliasing filters present before ADC inputs where needed
**Priority:** standard · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Anti-aliasing filters present before ADC inputs where needed.

**Why:** Out-of-band noise can alias into sampled measurement bandwidth.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Compare analog filter corner and roll-off with ADC sample rate and target signal bandwidth.

**Pass when:**
- Aliasing budget is met at expected sample frequency.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not automatically split analog and digital ground; protect return paths and follow mixed-signal device guidance.
- Digital filtering cannot undo aliasing after conversion.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.7: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-038 — DAC output has appropriate load/buffer
**Priority:** standard · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: DAC output has appropriate load/buffer.

**Why:** A DAC may lack current drive or stability into the real load.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check load impedance, buffer drive, output settling and compliance voltage.

**Pass when:**
- DAC output reaches the load accurately and remains stable.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not automatically split analog and digital ground; protect return paths and follow mixed-signal device guidance.
- Additional buffers may add offset, noise or error.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.7: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-039 — Sensor signal conditioning appears appropriate
**Priority:** standard · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Sensor signal conditioning appears appropriate.

**Why:** Sensors often require gain, bias, filtering and protection before conversion.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Verify excitation, sensor dynamic range, calibration path, temperature changes and noise.

**Pass when:**
- Conditioned signal covers intended measurement range without clipping.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not automatically split analog and digital ground; protect return paths and follow mixed-signal device guidance.
- Allow tolerance and field wiring interference.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.7: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-040 — Analog ground separate from digital if used
**Priority:** high · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Analog ground separate from digital if used.

**Why:** Ground partitioning can obstruct high-frequency current return and increase noise.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check device guidance and routing zones before proposing a split; map return paths across domains.

**Pass when:**
- A continuous quiet return path is demonstrated; split used only where justified.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Do not automatically split analog and digital ground; protect return paths and follow mixed-signal device guidance.
- Default to continuous reference plane and functional zoning. TI notes warn against unnecessary splits.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.8: Predictable Designs — Design Review Checklist: Schematic Circuit
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## SCH-07 — IC pin configuration
Review the logic, component choices, interface electrical requirements and failure conditions before PCB layout is frozen.

### SCH-041 — Configuration/strapping pins set with resistors (not left floating)
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Configuration/strapping pins set with resistors (not left floating).

**Why:** Boot strap levels must be valid before firmware configures the pins.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check resistor dividers/pulls, sampling at reset, internal bias and alternate pin function.

**Pass when:**
- Every mode pin has defined startup logic levels with margin.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some unused pins must remain floating or be tied in a specified manner; device-specific datasheet prevails.
- Check drive contention if strap pins later become outputs.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.8: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-042 — Unused inputs have pullups/pulldowns (not left floating)
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Unused inputs have pullups/pulldowns (not left floating).

**Why:** Floating CMOS inputs can chatter and increase current.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Apply the datasheet-specific rule to each unused input, bus pin and analog input.

**Pass when:**
- Every unused pin is either intentionally NC or placed in a supported state.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some unused pins must remain floating or be tied in a specified manner; device-specific datasheet prevails.
- Never automatically tie every unused pin to ground; some require NC.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.8: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-043 — Multi-function pins configured appropriately
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Multi-function pins configured appropriately.

**Why:** Pin multiplexing errors can silently disable peripherals.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Cross-check schematic pin selection with firmware peripheral matrix, boot functions and debug access.

**Pass when:**
- All muxed pins support intended functions without conflict.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some unused pins must remain floating or be tied in a specified manner; device-specific datasheet prevails.
- Include bootloader and production test configurations.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.8: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-044 — Reset pins have pullups if active-low
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Reset pins have pullups if active-low.

**Why:** Marginal reset timing can prevent reliable startup.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Review reset source, required pulse width, supervisor, internal pullup and brownout handling.

**Pass when:**
- Reset satisfies threshold, deassertion timing and startup noise limits.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some unused pins must remain floating or be tied in a specified manner; device-specific datasheet prevails.
- An external pullup is not always needed or allowed.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.8: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-045 — Enable pins configured correctly
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Enable pins configured correctly.

**Why:** Floating/incorrect enable inputs can unintentionally power a subsystem.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Verify pull direction, power sequencing, active polarity and firmware defaults.

**Pass when:**
- Enable has a deterministic safe state before and after firmware boot.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some unused pins must remain floating or be tied in a specified manner; device-specific datasheet prevails.
- Consider current injection into an unpowered domain.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.8: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-046 — Mode/configuration pins set per intended operation
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Mode/configuration pins set per intended operation.

**Why:** Boot strap levels must be valid before firmware configures the pins.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check resistor dividers/pulls, sampling at reset, internal bias and alternate pin function.

**Pass when:**
- Every mode pin has defined startup logic levels with margin.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some unused pins must remain floating or be tied in a specified manner; device-specific datasheet prevails.
- Check drive contention if strap pins later become outputs.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.8: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## SCH-08 — RF and wireless schematic
Review the logic, component choices, interface electrical requirements and failure conditions before PCB layout is frozen.

### SCH-047 — RF section has appropriate antenna connection (connector or chip antenna)
**Priority:** high · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: RF section has appropriate antenna connection (connector or chip antenna).

**Why:** Antenna interface mistakes can reduce range or damage the PA.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Identify antenna connector/element, 0 Ω tuning links and grounding scheme from RF reference design.

**Pass when:**
- Feed network and antenna termination are defined and manufacturable.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- 50-ohm systems are common but not universal, and a 50-ohm net is not a substitute for correct matching and measurement.
- Do not assume that a connector antenna and chip antenna share the same keepout.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.9: Predictable Designs — Design Review Checklist: Schematic Circuit
- JOHN-VID t=286s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-048 — Antenna feed has 50 Ω impedance matching network
**Priority:** high · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Antenna feed has 50Ω impedance matching network.

**Why:** RF impedance mismatch causes reflection and transfer loss.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Compute trace geometry from final stackup; verify pads, transitions and matching network.

**Pass when:**
- Achieves target system impedance or manufacturer-specified alternative.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- 50-ohm systems are common but not universal, and a 50-ohm net is not a substitute for correct matching and measurement.
- 50 Ω is common, not universal; differential and antenna-feed impedances vary.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.9: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-049 — RF section has appropriate filtering
**Priority:** high · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: RF section has appropriate filtering.

**Why:** Spurs and unwanted RF energy can interfere with other circuits and violate emissions requirements.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Evaluate harmonic/antenna filter topology against supported reference design and target band.

**Pass when:**
- RF filter insertion loss and attenuation meet design targets.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- 50-ohm systems are common but not universal, and a 50-ohm net is not a substitute for correct matching and measurement.
- Do not populate arbitrary filters without accounting for matching.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.9: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-050 — Balun/matching network matches reference design
**Priority:** standard · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Balun/matching network matches reference design.

**Why:** Unbalanced or incorrect network geometry changes RF behavior.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Verify balun part, pinout, component values and trace placement from evaluation layout.

**Pass when:**
- RF network matches vendor reference or validated RF analysis.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- 50-ohm systems are common but not universal, and a 50-ohm net is not a substitute for correct matching and measurement.
- Layout parasitics can dominate at high frequencies.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.9: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## SCH-09 — Schematic clarity and documentation
Review the logic, component choices, interface electrical requirements and failure conditions before PCB layout is frozen.

### SCH-051 — All components have unique reference designators
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: All components have unique reference designators.

**Why:** Duplicate designators make BOMs, placement data and assembly labels ambiguous.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Run schematic annotation and check all units and hierarchical sheets.

**Pass when:**
- Each physical component has one unambiguous reference and correctly assigned units.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An ERC pass does not guarantee that the intended signal is connected to the right physical pin.
- Multi-unit symbols must be intentionally grouped.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.9: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-052 — Component values clearly labeled and readable
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Component values clearly labeled and readable.

**Why:** Ambiguous values are a common build and sourcing error.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check value, tolerance, units, footprint and manufacturer part fields are distinct and readable.

**Pass when:**
- Value and procurement fields produce an unambiguous BOM.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An ERC pass does not guarantee that the intended signal is connected to the right physical pin.
- Do not use unspecified resistor/capacitor values for release.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.9: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-053 — Net names are meaningful (not default names)
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Net names are meaningful (not default names).

**Why:** Mislabelled nets can connect unintentionally across sheets.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Review power aliases, hierarchical/global labels and all repeated net labels.

**Pass when:**
- Names express function and voltage, with no accidental cross-sheet ties.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An ERC pass does not guarantee that the intended signal is connected to the right physical pin.
- Avoid relying on automatically assigned net names for critical power signals.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.10: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-054 — Power nets clearly labeled with voltages (3V3, 5V0, etc.)
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Power nets clearly labeled with voltages (3V3, 5V0, etc.).

**Why:** Mislabelled nets can connect unintentionally across sheets.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Review power aliases, hierarchical/global labels and all repeated net labels.

**Pass when:**
- Names express function and voltage, with no accidental cross-sheet ties.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An ERC pass does not guarantee that the intended signal is connected to the right physical pin.
- Avoid relying on automatically assigned net names for critical power signals.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.10: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-055 — All IC pins are connected or explicitly marked NC (no connect)
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: All IC pins are connected or explicitly marked NC (no connect).

**Why:** Disconnected or wrong pin connections can escape cursory schematic review.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Run ERC, inspect NC flags, power pins, connector pins and intentional unused nodes.

**Pass when:**
- No unreviewed dangling pins; every NC marker is deliberate.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An ERC pass does not guarantee that the intended signal is connected to the right physical pin.
- Do not use generic NC flags to suppress genuine ERC violations.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.10: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-056 — Avoid: obvious missing connections or floating nets
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: No obvious missing connections or floating nets.

**Why:** Disconnected or wrong pin connections can escape cursory schematic review.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Run ERC, inspect NC flags, power pins, connector pins and intentional unused nodes.

**Pass when:**
- No unreviewed dangling pins; every NC marker is deliberate.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An ERC pass does not guarantee that the intended signal is connected to the right physical pin.
- Do not use generic NC flags to suppress genuine ERC violations.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.10: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-057 — Connector pin numbering is clear
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Connector pin numbering is clear.

**Why:** Harness wiring relies on physical mating-face pin numbering.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Compare symbol and footprint numbering to connector manufacturer drawings (both views).

**Pass when:**
- Pin numbering and signal assignments agree with the actual mating orientation.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An ERC pass does not guarantee that the intended signal is connected to the right physical pin.
- Front vs rear view reversal is a frequent error.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.10: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-058 — Schematic is organized logically by function
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Schematic is organized logically by function.

**Why:** Poorly structured diagrams slow reviews and conceal power/signal dependencies.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Group functional blocks and add net direction, notes and cross-sheet references.

**Pass when:**
- Another engineer can trace main supply, interface and reset paths without guessing.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An ERC pass does not guarantee that the intended signal is connected to the right physical pin.
- Clarity is a process control, not just cosmetic formatting.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.10: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## SCH-10 — Test and debug architecture
Review the logic, component choices, interface electrical requirements and failure conditions before PCB layout is frozen.

### SCH-059 — Programming header present (JTAG, SWD, ISP, etc.)
**Priority:** standard · **Applicable:** Boards requiring programming/debug/test access · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Programming header present (JTAG, SWD, ISP, etc.).

**Why:** Boards may be impossible to program/recover without the right signals and voltage reference.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check supported programming/debug connector pinout, target voltage, reset, ground and boot selection.

**Pass when:**
- Programming and recovery possible on an unprogrammed board.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- When test pads are too small or inaccessible for automated fixtures, provide an alternative access plan.
- A custom footprint may be used, but cable orientation and access must be documented.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.10: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-060 — Programming header pins correctly connected per standard
**Priority:** standard · **Applicable:** Boards requiring programming/debug/test access · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Programming header pins correctly connected per standard.

**Why:** Boards may be impossible to program/recover without the right signals and voltage reference.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Check supported programming/debug connector pinout, target voltage, reset, ground and boot selection.

**Pass when:**
- Programming and recovery possible on an unprogrammed board.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- When test pads are too small or inaccessible for automated fixtures, provide an alternative access plan.
- A custom footprint may be used, but cable orientation and access must be documented.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.11: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-061 — Serial debug port accessible (UART/USB)
**Priority:** standard · **Applicable:** USB interfaces · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Serial debug port accessible (UART/USB).

**Why:** A boot log is often the fastest diagnosis route for bring-up failures.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Confirm UART/USB debug pins, voltage and boot-state availability and access after assembly.

**Pass when:**
- A practical debug method exists for prototypes or factory use.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- When test pads are too small or inaccessible for automated fixtures, provide an alternative access plan.
- Consider power-off/voltage isolation for external debug adapters.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.11: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-062 — Test points or headers on critical signals
**Priority:** high · **Applicable:** Boards requiring programming/debug/test access · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Test points or headers on critical signals.

**Why:** Board-level measurements need repeatable and safe probe access.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. List rails, ground, reset, programming, clocks and failure-critical signals; reserve pads for probes/fixtures.

**Pass when:**
- Required signals are accessible with the intended probe/tool and enclosure state.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- When test pads are too small or inaccessible for automated fixtures, provide an alternative access plan.
- High-speed test pads can create stubs; use suitable probing or reserved footprints.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.11: Predictable Designs — Design Review Checklist: Schematic Circuit
- JOHN-VID t=602s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### SCH-063 — LED indicators present for power and status
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: LED indicators present for power and status.

**Why:** Indicators can provide quick power/boot diagnostics but consume power.

**How to verify:**
1. Inspect the schematic, BOM and device-specific datasheets; trace the net and test the relevant operating and fault cases.
2. Select LEDs by debug value, current budget, visibility and firmware control.

**Pass when:**
- Appropriate status visibility exists or documented alternative diagnostics.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- When test pads are too small or inaccessible for automated fixtures, provide an alternative access plan.
- Optional for low-power/small-product designs; not a blanket requirement.

**Evidence to record:** Schematic and netlist review; Applicable part datasheet or design calculation

**Sources:**
- PD-SCH p.11: Predictable Designs — Design Review Checklist: Schematic Circuit

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-01 — Board outline and structure
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-001 — Board outline is closed and valid
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Board outline is closed and valid.

**Why:** Open or overlapping contour edges can fail CAM routing.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check Edge.Cuts continuity, segment overlap, cutout geometry and units in a CAM viewer.

**Pass when:**
- Single valid outline plus intentional internal cuts are correctly exported.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Use actual assembly tolerances and supplier capabilities, not visual judgement alone.
- JLCPCB KiCad 9 guide specifically requires a closed Edge.Cuts profile.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.2: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-002 — Board dimensions appear reasonable for application
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Board dimensions appear reasonable for application.

**Why:** PCB dimensions control enclosure fit, cost and mechanical interfaces.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Verify mating enclosure 3D model, mounting bosses, edge connector datum and tolerance stack.

**Pass when:**
- Outline dimensions match approved mechanical drawing and fit envelope.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Use actual assembly tolerances and supplier capabilities, not visual judgement alone.
- Include assembly handling and panel rail allowances.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.2: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-003 — Mounting holes present and properly sized
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Mounting holes present and properly sized.

**Why:** Fasteners can short copper, crush parts or interfere with placement.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check hole diameter, plating type, screw head, washer, standoff, torque and nearby component height.

**Pass when:**
- Mechanical hardware fits without violating electrical or assembly keepouts.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Use actual assembly tolerances and supplier capabilities, not visual judgement alone.
- Tie metal mounting hardware to chassis/ground only by deliberate EMC/safety design.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.2: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-004 — Mounting holes have keepout for screws/standoffs
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Mounting holes have keepout for screws/standoffs.

**Why:** Fasteners can short copper, crush parts or interfere with placement.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check hole diameter, plating type, screw head, washer, standoff, torque and nearby component height.

**Pass when:**
- Mechanical hardware fits without violating electrical or assembly keepouts.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Use actual assembly tolerances and supplier capabilities, not visual judgement alone.
- Tie metal mounting hardware to chassis/ground only by deliberate EMC/safety design.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.2: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-005 — Corner radius appropriate for manufacturability
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Corner radius appropriate for manufacturability.

**Why:** Sharp corners can be fragile and may be more expensive to route.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check outer-corner machining, slots and mechanical envelope against fab constraints.

**Pass when:**
- Outline is machinable and compatible with fit requirements.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Use actual assembly tolerances and supplier capabilities, not visual judgement alone.
- Not every board needs rounded external corners.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.2: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-006 — PCB thickness specified in stackup
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: PCB thickness specified in stackup.

**Why:** Thickness determines connector mating, screw engagement and impedance geometry.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Specify total finished thickness, tolerance, copper weight and controlled-impedance stack.

**Pass when:**
- Manufacturing order agrees with the design and mechanically mating parts.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Use actual assembly tolerances and supplier capabilities, not visual judgement alone.
- Edge connectors often impose tight thickness/finish constraints.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.3: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-02 — Component placement
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-007 — Components grouped logically by function
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Components grouped logically by function.

**Why:** Functional zoning reduces cross-coupling and shortens critical loops.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare placement of noisy power/RF/digital and sensitive analog blocks against functional diagram.

**Pass when:**
- Critical paths remain local and do not force poor return paths.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manufacturer spacing constraints can differ for hand assembly, machine assembly and rework.
- Avoid separation that unnecessarily increases high-speed loop area.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.3: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-008 — High-power components not clustered together
**Priority:** high · **Applicable:** Heat-dissipating circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: High-power components not clustered together.

**Why:** Closely packed heat sources increase local ambient temperature.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Review worst-case loss density and nearby temperature-sensitive components.

**Pass when:**
- Predicted hot spots meet component and enclosure temperature budgets.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manufacturer spacing constraints can differ for hand assembly, machine assembly and rework.
- Grouping can sometimes help heatsinking; validate rather than blindly separate.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.3: Predictable Designs — Design Review Checklist: PCB Layout
- JOHN-VID t=555s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-009 — Tall components positioned to avoid mechanical interference
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Tall components positioned to avoid mechanical interference.

**Why:** An apparently fitting board can fail after mating connectors or closing enclosure.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Inspect 3D component heights, keepouts, plug insertion/removal, and service-tool access.

**Pass when:**
- All parts clear the enclosure, screws, labels and connectors at tolerance extremes.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manufacturer spacing constraints can differ for hand assembly, machine assembly and rework.
- Watch protruding connector cables and flex bend radius.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.3: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-010 — Connectors accessible (not blocked by other components)
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Connectors accessible (not blocked by other components).

**Why:** Inaccessible connectors prevent correct installation or repair.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Fit the actual mating cable and consider mating direction, latch release and tool clearance.

**Pass when:**
- Connector can be mated/unmated in its installed configuration.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manufacturer spacing constraints can differ for hand assembly, machine assembly and rework.
- Edge overhang and USB connector shell contact deserve special attention.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.3: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-011 — Polarized components oriented consistently where possible
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Polarized components oriented consistently where possible.

**Why:** Consistent orientation reduces assembly and inspection mistakes.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Verify pin1/cathode marking and compare placements with assembly drawings.

**Pass when:**
- Orientation is electrically correct and markings are visible after population.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manufacturer spacing constraints can differ for hand assembly, machine assembly and rework.
- Routing and thermal needs can override cosmetic orientation uniformity.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.3: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-012 — Components with thermal pads positioned for heat management
**Priority:** high · **Applicable:** Heat-dissipating circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Components with thermal pads positioned for heat management.

**Why:** Exposed pads need proper copper, paste and heat path.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare land pattern, thermal via and paste stencil with package manufacturer notes.

**Pass when:**
- Pad can be reliably soldered and junction temperature target met.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manufacturer spacing constraints can differ for hand assembly, machine assembly and rework.
- Thermal pad may be electrically live; follow exact datasheet.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.3: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-013 — Adequate spacing between components for assembly
**Priority:** standard · **Applicable:** Boards with corresponding manufacturing/assembly process · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Adequate spacing between components for assembly.

**Why:** Placement too close to neighbors/edges impairs reflow, rework and panelisation.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check courtyards, nozzle access, soldering tools, depanel force and panel rail clearance.

**Pass when:**
- Selected assembler can place and inspect all components.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manufacturer spacing constraints can differ for hand assembly, machine assembly and rework.
- Component-to-edge restrictions depend on whether panel rails or V-score are used.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.4: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-014 — Avoid: components too close to board edges
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: No components too close to board edges.

**Why:** Placement too close to neighbors/edges impairs reflow, rework and panelisation.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check courtyards, nozzle access, soldering tools, depanel force and panel rail clearance.

**Pass when:**
- Selected assembler can place and inspect all components.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manufacturer spacing constraints can differ for hand assembly, machine assembly and rework.
- Component-to-edge restrictions depend on whether panel rails or V-score are used.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.4: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-03 — Power distribution
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-015 — Power traces appropriately sized for current (wider for high current)
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Power traces appropriately sized for current (wider for high current).

**Why:** Copper and connector bottlenecks lead to voltage drop and excessive heat.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Calculate worst-case Irms, resistive drop, duty cycle and temperature rise for each segment.

**Pass when:**
- Trace/plane/via/connector path meets current, voltage and temperature limits.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Current capacity depends on copper weight, length, layer, temperature environment and allowable rise; avoid fixed-width recipes.
- Manufacturer minimum copper width is a manufacturability limit, not a current rating.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.4: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-016 — Power connector pins/traces sized for expected current
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Power connector pins/traces sized for expected current.

**Why:** Copper and connector bottlenecks lead to voltage drop and excessive heat.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Calculate worst-case Irms, resistive drop, duty cycle and temperature rise for each segment.

**Pass when:**
- Trace/plane/via/connector path meets current, voltage and temperature limits.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Current capacity depends on copper weight, length, layer, temperature environment and allowable rise; avoid fixed-width recipes.
- Manufacturer minimum copper width is a manufacturability limit, not a current rating.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.4: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-017 — Multiple vias used for high-current connections
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Multiple vias used for high-current connections.

**Why:** Via barrels contribute resistance and heating when changing layers.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Calculate via conductance from plated-hole geometry and evaluate current sharing and fabrication yield.

**Pass when:**
- Via quantity and geometry support required current and transient conditions.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Current capacity depends on copper weight, length, layer, temperature environment and allowable rise; avoid fixed-width recipes.
- No fixed 1 A or 2 A per via rule applies to all boards.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.4: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-018 — Decoupling capacitors placed immediately adjacent to IC power pins
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Decoupling capacitors placed immediately adjacent to IC power pins.

**Why:** Long capacitor loops increase supply impedance and emitted noise.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Trace connection from capacitor terminals to supply/ground pins, including vias and plane transitions.

**Pass when:**
- Relevant capacitors are located and routed per IC or regulator reference layout.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Current capacity depends on copper weight, length, layer, temperature environment and allowable rise; avoid fixed-width recipes.
- Cap placement is judged by complete current loop, not distance alone.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.4: Predictable Designs — Design Review Checklist: PCB Layout
- TI-DEC : Texas Instruments — Mixed Signals, Grounding and Bypass Capacitors — https://www.ti.com/video/6245227303001

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-019 — Bulk capacitors positioned near power input
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Bulk capacitors positioned near power input.

**Why:** Long capacitor loops increase supply impedance and emitted noise.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Trace connection from capacitor terminals to supply/ground pins, including vias and plane transitions.

**Pass when:**
- Relevant capacitors are located and routed per IC or regulator reference layout.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Current capacity depends on copper weight, length, layer, temperature environment and allowable rise; avoid fixed-width recipes.
- Cap placement is judged by complete current loop, not distance alone.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.4: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-020 — Ground plane present and continuous
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Ground plane present and continuous.

**Why:** A nearby uninterrupted reference reduces return path impedance and loop area.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. View the plane under representative signals and around vias, connectors and cutouts.

**Pass when:**
- Return paths remain continuous without long detours for critical signals.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Current capacity depends on copper weight, length, layer, temperature environment and allowable rise; avoid fixed-width recipes.
- Power planes can act as valid references with appropriate return-current transitions in some stackups.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.5: Predictable Designs — Design Review Checklist: PCB Layout
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf
- JOHN-VID t=42s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-021 — Power planes used appropriately
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Power planes used appropriately.

**Why:** Disjoint and thin planes can create unintended impedance and EMI problems.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Refill zones and inspect copper islands, voids, neckdowns and rail isolation.

**Pass when:**
- Planes provide intended current/return path without shorts or bottlenecks.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Current capacity depends on copper weight, length, layer, temperature environment and allowable rise; avoid fixed-width recipes.
- Do not add isolated pours merely to increase copper coverage.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.5: Predictable Designs — Design Review Checklist: PCB Layout
- OWN row 15: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-022 — Avoid: long thin power traces creating bottlenecks
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: No long thin power traces creating bottlenecks.

**Why:** Copper and connector bottlenecks lead to voltage drop and excessive heat.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Calculate worst-case Irms, resistive drop, duty cycle and temperature rise for each segment.

**Pass when:**
- Trace/plane/via/connector path meets current, voltage and temperature limits.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Current capacity depends on copper weight, length, layer, temperature environment and allowable rise; avoid fixed-width recipes.
- Manufacturer minimum copper width is a manufacturability limit, not a current rating.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.5: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-023 — Star-point grounding implemented if design uses split ground
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Star-point grounding implemented if design uses split ground.

**Why:** Ground topology determines common impedance and noise coupling.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Identify actual sensitive return paths and assess whether a partition is required by the device/application.

**Pass when:**
- No critical signal crosses an unbridged return-plane gap; chosen topology is justified.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Current capacity depends on copper weight, length, layer, temperature environment and allowable rise; avoid fixed-width recipes.
- A continuous plane with careful functional zoning is generally preferable to automatic splits.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.5: Predictable Designs — Design Review Checklist: PCB Layout
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-04 — Switch-mode regulator placement and routing
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-024 — Switching regulator follows manufacturer layout guidelines
**Priority:** high · **Applicable:** Switch-mode power supply designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Switching regulator follows manufacturer layout guidelines.

**Why:** Regulator stability and EMI performance depend heavily on physical geometry.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare exact PCB placement with regulator evaluation board and datasheet including switch, feedback and bootstrap loops.

**Pass when:**
- Critical loop and feedback placement are consistent with official reference design.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Never enlarge a noisy switching node just for ease of routing; validate compensation and thermal needs.
- Do not clone a reference board for a different stackup without checking return paths.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.5: Predictable Designs — Design Review Checklist: PCB Layout
- JOHN-VID t=506s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-025 — Input capacitor close to regulator input pin
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Input capacitor close to regulator input pin.

**Why:** Long capacitor loops increase supply impedance and emitted noise.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Trace connection from capacitor terminals to supply/ground pins, including vias and plane transitions.

**Pass when:**
- Relevant capacitors are located and routed per IC or regulator reference layout.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Never enlarge a noisy switching node just for ease of routing; validate compensation and thermal needs.
- Cap placement is judged by complete current loop, not distance alone.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.5: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-026 — Output capacitor close to regulator output pin
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Output capacitor close to regulator output pin.

**Why:** Long capacitor loops increase supply impedance and emitted noise.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Trace connection from capacitor terminals to supply/ground pins, including vias and plane transitions.

**Pass when:**
- Relevant capacitors are located and routed per IC or regulator reference layout.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Never enlarge a noisy switching node just for ease of routing; validate compensation and thermal needs.
- Cap placement is judged by complete current loop, not distance alone.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.5: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-027 — Feedback trace routed away from switching node
**Priority:** standard · **Applicable:** Switch-mode power supply designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Feedback trace routed away from switching node.

**Why:** Feedback is high-impedance and easily corrupted by switching-field pickup.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Route from quiet output sensing point away from SW node, inductor and hot loops; check ground reference.

**Pass when:**
- Feedback connects to the intended sense point with low-coupling geometry.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Never enlarge a noisy switching node just for ease of routing; validate compensation and thermal needs.
- Some regulators specify Kelvin routing and particular compensation placement.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.6: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-028 — Switching node trace/copper area minimized
**Priority:** standard · **Applicable:** Switch-mode power supply designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Switching node trace/copper area minimized.

**Why:** High dv/dt and di/dt areas drive emissions and ringing.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Highlight switching node and pulsed forward/return loops and minimise their effective area.

**Pass when:**
- Loop placement matches converter reference layout and EMI target.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Never enlarge a noisy switching node just for ease of routing; validate compensation and thermal needs.
- Thermal copper may conflict with keeping switch-node area compact; follow regulator-specific guidance.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.6: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-029 — Ground connections solid (not thin traces)
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Ground connections solid (not thin traces).

**Why:** Thin high-current returns cause ground bounce and voltage drops.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check return widths, via impedance and connections into planes at each power device.

**Pass when:**
- Ground impedance does not undermine switching stability or fault current handling.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Never enlarge a noisy switching node just for ease of routing; validate compensation and thermal needs.
- High-current thermal pads often require solid plane connections rather than spoke reliefs.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.6: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-030 — Hot loop area minimized
**Priority:** standard · **Applicable:** Switch-mode power supply designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Hot loop area minimized.

**Why:** High dv/dt and di/dt areas drive emissions and ringing.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Highlight switching node and pulsed forward/return loops and minimise their effective area.

**Pass when:**
- Loop placement matches converter reference layout and EMI target.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Never enlarge a noisy switching node just for ease of routing; validate compensation and thermal needs.
- Thermal copper may conflict with keeping switch-node area compact; follow regulator-specific guidance.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.6: Predictable Designs — Design Review Checklist: PCB Layout
- JOHN-VID t=707s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-05 — High-speed and critical signals
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-031 — Differential pairs routed together with consistent spacing
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Differential pairs routed together with consistent spacing.

**Why:** Differential fields depend on consistent geometry and reference.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Review pair gap, trace width, reference and pair-to-pair clearance on each layer.

**Pass when:**
- Geometry meets interface and stackup impedance rules.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Length matching, serpentine routing and 90-degree corner avoidance are conditional on interface timing budgets—not universal targets.
- Near-field coupling benefits vary with pair and reference geometry; do not route around keepouts solely to keep exact spacing.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.6: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-032 — Differential pair lengths matched (equal length)
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Differential pair lengths matched (equal length).

**Why:** Excess intra-pair skew can close the timing eye.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Calculate allowable skew/length mismatch from the protocol and stackup before tuning.

**Pass when:**
- Pair skew is within the interface timing budget.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Length matching, serpentine routing and 90-degree corner avoidance are conditional on interface timing budgets—not universal targets.
- Perfect length equality is rarely necessary and excessive meanders can be worse.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.6: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-033 — High-speed signals have continuous ground plane beneath
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: High-speed signals have continuous ground plane beneath.

**Why:** A nearby uninterrupted reference reduces return path impedance and loop area.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. View the plane under representative signals and around vias, connectors and cutouts.

**Pass when:**
- Return paths remain continuous without long detours for critical signals.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Length matching, serpentine routing and 90-degree corner avoidance are conditional on interface timing budgets—not universal targets.
- Power planes can act as valid references with appropriate return-current transitions in some stackups.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.6: Predictable Designs — Design Review Checklist: PCB Layout
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-034 — High-speed traces avoid crossing splits in ground plane
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: High-speed traces avoid crossing splits in ground plane.

**Why:** A plane gap forces return current onto a longer path and increases EMI.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Cross-probe all critical signals against adjacent reference-plane polygons including at layer changes.

**Pass when:**
- No critical net crosses a void/split without an engineered return bridge.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Length matching, serpentine routing and 90-degree corner avoidance are conditional on interface timing budgets—not universal targets.
- Do not place a stitching capacitor indiscriminately across unrelated supply domains.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.7: Predictable Designs — Design Review Checklist: PCB Layout
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-035 — Clock signals kept short and direct
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Clock signals kept short and direct.

**Why:** Clock edges can couple into other nets and reflections can increase jitter.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Review path length, branch topology, termination and adjacent trace coupling.

**Pass when:**
- Clock quality meets receiver timing/jitter budget without excess stubs.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Length matching, serpentine routing and 90-degree corner avoidance are conditional on interface timing budgets—not universal targets.
- A topology may require a specific fanout and damping network.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.7: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-036 — Clock traces not running parallel to other signals
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Clock traces not running parallel to other signals.

**Why:** Clock edges can couple into other nets and reflections can increase jitter.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Review path length, branch topology, termination and adjacent trace coupling.

**Pass when:**
- Clock quality meets receiver timing/jitter budget without excess stubs.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Length matching, serpentine routing and 90-degree corner avoidance are conditional on interface timing budgets—not universal targets.
- A topology may require a specific fanout and damping network.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.7: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-037 — Avoid: stubs on high-speed or clock traces
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: No stubs on high-speed or clock traces.

**Why:** Clock edges can couple into other nets and reflections can increase jitter.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Review path length, branch topology, termination and adjacent trace coupling.

**Pass when:**
- Clock quality meets receiver timing/jitter budget without excess stubs.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Length matching, serpentine routing and 90-degree corner avoidance are conditional on interface timing budgets—not universal targets.
- A topology may require a specific fanout and damping network.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.7: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-038 — Via count minimized on critical signals
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Via count minimized on critical signals.

**Why:** Transitions create impedance discontinuity and can interrupt the reference return.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Inspect all signal vias and provide nearby return stitching vias when references change.

**Pass when:**
- Transition discontinuities satisfy interface budget.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Length matching, serpentine routing and 90-degree corner avoidance are conditional on interface timing budgets—not universal targets.
- A necessary via is preferable to an unnecessarily long or badly routed trace.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.7: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-039 — Controlled impedance traces have appropriate width
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Controlled impedance traces have appropriate width.

**Why:** Wrong geometry causes reflections and mismatch.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Use manufacturer-provided dielectric/copper geometry and field-solver targets for each named net class.

**Pass when:**
- Trace, via and connector launch impedance meet interface requirements.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Length matching, serpentine routing and 90-degree corner avoidance are conditional on interface timing budgets—not universal targets.
- A single generic width is not valid across different layers/stackups.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.7: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them
- JOHN-VID t=1287s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-06 — RF layout
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-040 — RF traces are 50 Ω controlled impedance
**Priority:** high · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: RF traces are 50Ω controlled impedance.

**Why:** RF impedance mismatch causes reflection and transfer loss.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compute trace geometry from final stackup; verify pads, transitions and matching network.

**Pass when:**
- Achieves target system impedance or manufacturer-specified alternative.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An antenna keepout must follow the selected device; no-copper underneath is not a universal rule for every antenna.
- 50 Ω is common, not universal; differential and antenna-feed impedances vary.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.7: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-041 — RF trace has ground plane underneath
**Priority:** critical · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: RF trace has ground plane underneath.

**Why:** RF feed return needs a defined reference for predictable impedance.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Examine feedline over its whole length, including matching pads and antenna launcher.

**Pass when:**
- Reference geometry matches the antenna/module design.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An antenna keepout must follow the selected device; no-copper underneath is not a universal rule for every antenna.
- Some coplanar waveguides have additional same-layer guard geometry.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.8: Predictable Designs — Design Review Checklist: PCB Layout
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-042 — Antenna keepout area maintained (no copper beneath)
**Priority:** high · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Antenna keepout area maintained (no copper beneath).

**Why:** Nearby copper and components can detune or shield antennas.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Overlay the antenna manufacturer keepout drawing onto all affected layers and enclosure model.

**Pass when:**
- No restricted copper/components/metal intrude into required areas.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An antenna keepout must follow the selected device; no-copper underneath is not a universal rule for every antenna.
- Keepout layer and ground exceptions are antenna-specific.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.8: Predictable Designs — Design Review Checklist: PCB Layout
- JOHN-VID t=286s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08
- JOHN-VID t=813s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-043 — RF section has ground stitching vias
**Priority:** high · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: RF section has ground stitching vias.

**Why:** Stitching can constrain RF/return fields and connect fragmented ground regions.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Place vias around critical transitions/perimeter where vendor reference or analysis indicates benefit.

**Pass when:**
- Stitch pattern meets RF/reference and manufacturing needs.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An antenna keepout must follow the selected device; no-copper underneath is not a universal rule for every antenna.
- No universal via spacing or perimeter-via requirement exists.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.8: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-044 — RF traces kept away from digital signals
**Priority:** high · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: RF traces kept away from digital signals.

**Why:** Coupling from digital clocks can degrade receiver sensitivity.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Inspect route proximity, reference plane, shielding and ground strategy.

**Pass when:**
- Sufficient isolation for receiver and transmit power requirements.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An antenna keepout must follow the selected device; no-copper underneath is not a universal rule for every antenna.
- Distance alone may not solve coupling through shared supplies.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.8: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-045 — Matching network layout matches reference design
**Priority:** standard · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Matching network layout matches reference design.

**Why:** Unbalanced or incorrect network geometry changes RF behavior.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Verify balun part, pinout, component values and trace placement from evaluation layout.

**Pass when:**
- RF network matches vendor reference or validated RF analysis.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- An antenna keepout must follow the selected device; no-copper underneath is not a universal rule for every antenna.
- Layout parasitics can dominate at high frequencies.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.8: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-07 — Analog routing
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-046 — Analog traces routed away from digital/switching signals
**Priority:** standard · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Analog traces routed away from digital/switching signals.

**Why:** Switching fields can corrupt low-level analog measurement.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare high-impedance and low-level routes with digital clocks, switching nodes and return paths.

**Pass when:**
- Sensitive nets have adequate isolation/noise margin.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A guard ring is effective only with appropriate low-impedance drive and geometry; splits may make returns worse.
- Separation must not destroy the common return path.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.8: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-047 — Analog ground separate or star-connected if used
**Priority:** high · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Analog ground separate or star-connected if used.

**Why:** Ground partitioning can obstruct high-frequency current return and increase noise.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check device guidance and routing zones before proposing a split; map return paths across domains.

**Pass when:**
- A continuous quiet return path is demonstrated; split used only where justified.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A guard ring is effective only with appropriate low-impedance drive and geometry; splits may make returns worse.
- Default to continuous reference plane and functional zoning. TI notes warn against unnecessary splits.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.8: Predictable Designs — Design Review Checklist: PCB Layout
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-048 — ADC input traces kept short and direct
**Priority:** standard · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: ADC input traces kept short and direct.

**Why:** High input capacitance and leakage can degrade acquisition settling.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Keep ADC inputs short where practical and follow required RC anti-alias network layout.

**Pass when:**
- Meets sampling settling, channel-to-channel leakage and accuracy budget.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A guard ring is effective only with appropriate low-impedance drive and geometry; splits may make returns worse.
- High input impedance sensors may need guard/shield rather than shortest routing alone.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.9: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-049 — Guard rings around sensitive analog inputs if needed
**Priority:** standard · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Guard rings around sensitive analog inputs if needed.

**Why:** Driven guard structures reduce leakage and capacitive pickup on very high impedance nodes.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Evaluate need, guard drive impedance, bias potential and contamination/creepage constraints.

**Pass when:**
- Guard improves or at least does not degrade input error budget.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A guard ring is effective only with appropriate low-impedance drive and geometry; splits may make returns worse.
- A grounded ring is not equivalent to a driven guard around all analog inputs.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.9: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-050 — Differential analog signals routed as pairs
**Priority:** standard · **Applicable:** Precision analog / mixed-signal designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Differential analog signals routed as pairs.

**Why:** Pair routing can reduce loop area and improve common-mode noise rejection.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Route forward/return sensing inputs with suitable proximity and reference; keep source impedance balanced.

**Pass when:**
- Balanced input signal routing preserves required measurement CMRR.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A guard ring is effective only with appropriate low-impedance drive and geometry; splits may make returns worse.
- Pair length matching is not always required at low bandwidth.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.9: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-08 — Thermal management
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-051 — Thermal vias present under power components (ICs, regulators)
**Priority:** high · **Applicable:** Heat-dissipating circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Thermal vias present under power components (ICs, regulators).

**Why:** Thermal conduction and solder joint quality both depend on via construction.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check exposed-pad vendor drawing, via drill/pad size, count, filling/capping/tenting and solder paste mask.

**Pass when:**
- Thermal/via design is manufacturable and meets junction temperature and solder void limits.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Thermal-via count, tenting and solder-mask treatment depend on the exact exposed-pad specification and assembly process.
- PDF claims 9+ vias and untented vias. These are examples, not universal requirements. Component-side tenting or filled/capped vias may reduce solder wicking.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation; Footprint/paste design and thermal calculation

**Sources:**
- PD-LAY p.9: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/
- TI-POWER : Texas Instruments — PowerPAD Thermally Enhanced Package — https://www.ti.com/lit/an/slma002h/slma002h.pdf
- OWN row 16: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-052 — Thermal vias adequate count
**Priority:** high · **Applicable:** Heat-dissipating circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Thermal vias adequate count (typically 9+ for high power).

**Why:** Thermal conduction and solder joint quality both depend on via construction.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check exposed-pad vendor drawing, via drill/pad size, count, filling/capping/tenting and solder paste mask.

**Pass when:**
- Thermal/via design is manufacturable and meets junction temperature and solder void limits.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Thermal-via count, tenting and solder-mask treatment depend on the exact exposed-pad specification and assembly process.
- PDF claims 9+ vias and untented vias. These are examples, not universal requirements. Component-side tenting or filled/capped vias may reduce solder wicking.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation; Footprint/paste design and thermal calculation

**Sources:**
- PD-LAY p.9: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/
- TI-POWER : Texas Instruments — PowerPAD Thermally Enhanced Package — https://www.ti.com/lit/an/slma002h/slma002h.pdf

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-053 — Thermal vias not tented (open for heat transfer)
**Priority:** high · **Applicable:** Heat-dissipating circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Thermal vias not tented (open for heat transfer).

**Why:** Thermal conduction and solder joint quality both depend on via construction.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check exposed-pad vendor drawing, via drill/pad size, count, filling/capping/tenting and solder paste mask.

**Pass when:**
- Thermal/via design is manufacturable and meets junction temperature and solder void limits.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Thermal-via count, tenting and solder-mask treatment depend on the exact exposed-pad specification and assembly process.
- PDF claims 9+ vias and untented vias. These are examples, not universal requirements. Component-side tenting or filled/capped vias may reduce solder wicking.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation; Footprint/paste design and thermal calculation

**Sources:**
- PD-LAY p.9: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/
- TI-POWER : Texas Instruments — PowerPAD Thermally Enhanced Package — https://www.ti.com/lit/an/slma002h/slma002h.pdf

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-054 — Copper area around hot components for heat spreading
**Priority:** high · **Applicable:** Heat-dissipating circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Copper area around hot components for heat spreading.

**Why:** Copper spreads local heat before transfer to air or case.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Estimate available copper plane area and junction-to-ambient/case resistance under enclosure conditions.

**Pass when:**
- Heat-spreader geometry keeps hot devices within ratings.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Thermal-via count, tenting and solder-mask treatment depend on the exact exposed-pad specification and assembly process.
- Hot copper near temperature-sensitive references can create drift.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.9: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-055 — Heatsink mounting provisions if pads present
**Priority:** high · **Applicable:** Heat-dissipating circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Heatsink mounting provisions if pads present.

**Why:** Mechanical sink mounting can stress packages and solder joints.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check sink footprint, pressure, pad/insulator, fasteners and heat path.

**Pass when:**
- Sink mounting is feasible without electrical shorts or excess mechanical force.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Thermal-via count, tenting and solder-mask treatment depend on the exact exposed-pad specification and assembly process.
- Verify isolation if exposed pad or package tab is live.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.10: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-056 — Thermal reliefs on ground plane connections (for soldering)
**Priority:** critical · **Applicable:** Heat-dissipating circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Thermal reliefs on ground plane connections (for soldering).

**Why:** Spokes balance plane connection with soldering heat flow.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Inspect high-current and heat-dissipating pads separately from ordinary passives; assess assembly process.

**Pass when:**
- Pads solder reliably and carry required current/heat.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Thermal-via count, tenting and solder-mask treatment depend on the exact exposed-pad specification and assembly process.
- Original preference 0.3 mm gap / 0.4 mm spokes is a project starting point, not global rule. Solid pad-to-plane ties may be needed for thermal/electrical performance.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.10: Predictable Designs — Design Review Checklist: PCB Layout
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf
- TI-POWER : Texas Instruments — PowerPAD Thermally Enhanced Package — https://www.ti.com/lit/an/slma002h/slma002h.pdf
- OWN row 5: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-09 — Crystal and oscillator layout
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-057 — Crystal placed very close to IC
**Priority:** standard · **Applicable:** Crystal/oscillator circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Crystal placed very close to IC.

**Why:** Crystal nodes are high impedance and sensitive to stray capacitance and EMI.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare precise crystal route and surrounding ground/keepouts to MCU datasheet layout example.

**Pass when:**
- Oscillator circuit has short, quiet, predictable parasitics and sufficient startup margin.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some oscillators explicitly require a particular ground keepout; do not blindly require solid ground beneath every crystal.
- Some crystal guidelines specify ground exclusion; device layout recommendation takes precedence.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.10: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-058 — Crystal load capacitors placed immediately adjacent
**Priority:** high · **Applicable:** Crystal/oscillator circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Crystal load capacitors placed immediately adjacent.

**Why:** Crystal nodes are high impedance and sensitive to stray capacitance and EMI.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare precise crystal route and surrounding ground/keepouts to MCU datasheet layout example.

**Pass when:**
- Oscillator circuit has short, quiet, predictable parasitics and sufficient startup margin.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some oscillators explicitly require a particular ground keepout; do not blindly require solid ground beneath every crystal.
- Some crystal guidelines specify ground exclusion; device layout recommendation takes precedence.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.10: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-059 — Ground plane solid under crystal
**Priority:** critical · **Applicable:** Crystal/oscillator circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Ground plane solid under crystal.

**Why:** Crystal nodes are high impedance and sensitive to stray capacitance and EMI.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare precise crystal route and surrounding ground/keepouts to MCU datasheet layout example.

**Pass when:**
- Oscillator circuit has short, quiet, predictable parasitics and sufficient startup margin.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some oscillators explicitly require a particular ground keepout; do not blindly require solid ground beneath every crystal.
- Some crystal guidelines specify ground exclusion; device layout recommendation takes precedence.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.10: Predictable Designs — Design Review Checklist: PCB Layout
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-060 — Crystal traces kept short with no vias if possible
**Priority:** high · **Applicable:** Crystal/oscillator circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Crystal traces kept short with no vias if possible.

**Why:** Crystal nodes are high impedance and sensitive to stray capacitance and EMI.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare precise crystal route and surrounding ground/keepouts to MCU datasheet layout example.

**Pass when:**
- Oscillator circuit has short, quiet, predictable parasitics and sufficient startup margin.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some oscillators explicitly require a particular ground keepout; do not blindly require solid ground beneath every crystal.
- Some crystal guidelines specify ground exclusion; device layout recommendation takes precedence.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.10: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-061 — Avoid: high-speed signals routed near crystal
**Priority:** high · **Applicable:** Crystal/oscillator circuits · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: No high-speed signals routed near crystal.

**Why:** Crystal nodes are high impedance and sensitive to stray capacitance and EMI.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare precise crystal route and surrounding ground/keepouts to MCU datasheet layout example.

**Pass when:**
- Oscillator circuit has short, quiet, predictable parasitics and sufficient startup margin.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Some oscillators explicitly require a particular ground keepout; do not blindly require solid ground beneath every crystal.
- Some crystal guidelines specify ground exclusion; device layout recommendation takes precedence.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.10: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-10 — EMI, ground and return paths
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-062 — Ground plane coverage good (>70% on ground layers)
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Ground plane coverage good (>70% on ground layers).

**Why:** Area percentage does not measure return-current integrity.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Inspect continuity, necks, isolated zones and every critical return path; record coverage as a secondary diagnostic only.

**Pass when:**
- Critical reference regions are continuous and low impedance.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- The PDF ground-coverage >70% is an informal heuristic, not a universal pass/fail requirement.
- The PDF’s >70% heuristic must not be an automatic pass/fail threshold.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.11: Predictable Designs — Design Review Checklist: PCB Layout
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-063 — Ground stitching vias around board perimeter
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Ground stitching vias around board perimeter.

**Why:** Stitching can constrain RF/return fields and connect fragmented ground regions.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Place vias around critical transitions/perimeter where vendor reference or analysis indicates benefit.

**Pass when:**
- Stitch pattern meets RF/reference and manufacturing needs.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- The PDF ground-coverage >70% is an informal heuristic, not a universal pass/fail requirement.
- No universal via spacing or perimeter-via requirement exists.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.11: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-064 — Ground stitching vias near RF circuits and high-speed
**Priority:** high · **Applicable:** RF or wireless designs · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Ground stitching vias near RF circuits and high-speed.

**Why:** Stitching can constrain RF/return fields and connect fragmented ground regions.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Place vias around critical transitions/perimeter where vendor reference or analysis indicates benefit.

**Pass when:**
- Stitch pattern meets RF/reference and manufacturing needs.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- The PDF ground-coverage >70% is an informal heuristic, not a universal pass/fail requirement.
- No universal via spacing or perimeter-via requirement exists.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.11: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-065 — Avoid: long parallel trace runs (creates coupling)
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: No long parallel trace runs (creates coupling).

**Why:** Long close parallel runs allow capacitive and inductive crosstalk.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Inspect aggressor/victim route length and gap; prioritise clocks, high-impedance nodes and fast edges.

**Pass when:**
- Measured/modelled coupling or layout margin fits signal requirements.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- The PDF ground-coverage >70% is an informal heuristic, not a universal pass/fail requirement.
- Phil suggests a 3× dielectric-height spacing as a starting heuristic; not a universal DRC value.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.11: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-066 — Traces not running along board edges
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Traces not running along board edges.

**Why:** Exposed edges may increase coupling to cables/chassis and reduce mechanical margin.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Inspect edge clearance and critical-signal location relative to exposed/mating interfaces.

**Pass when:**
- Tracks meet fabrication edge rules and do not create unnecessary emissions risk.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- The PDF ground-coverage >70% is an informal heuristic, not a universal pass/fail requirement.
- Edge routing is allowed when engineered, e.g. certain connectors/antenna feeds.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.11: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-067 — Isolated copper islands removed or grounded
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Isolated copper islands removed or grounded.

**Why:** Floating copper may act as an uncontrolled parasitic conductor.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Refill pours and identify islands on every copper layer; tie or remove intentionally.

**Pass when:**
- No unexplained floating islands remain.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- The PDF ground-coverage >70% is an informal heuristic, not a universal pass/fail requirement.
- Copper islands used for shields or capacitive structures require design justification.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.11: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-068 — Return current paths not interrupted
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Return current paths not interrupted.

**Why:** Long detours increase loop area, crosstalk and radiated emissions.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Follow reference under fast nets through connector, via and split transitions.

**Pass when:**
- A local return route exists for all critical signals.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- The PDF ground-coverage >70% is an informal heuristic, not a universal pass/fail requirement.
- Review reference plane under every change of layer, not just trace proximity.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.11: Predictable Designs — Design Review Checklist: PCB Layout
- TI-GND : Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules — https://www.ti.com/lit/an/scaa082a/scaa082a.pdf
- JOHN-VID t=42s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-11 — Manufacturability and assembly
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-069 — Fiducials present (minimum 3, asymmetrically placed)
**Priority:** standard · **Applicable:** Boards with corresponding manufacturing/assembly process · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Fiducials present (minimum 3, asymmetrically placed).

**Why:** Optical placement alignment requires unobstructed, correct reference marks.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Determine assembler service/panel requirements; place un-drilled copper marks, appropriate mask clear and asymmetric geometry.

**Pass when:**
- Fiducial pattern meets the selected assembler requirements and is visible to cameras.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- JLCPCB-specific geometry can change by service tier and should be checked with the actual selected assembly option.
- JLCPCB Sept 2026: recommended 1 mm copper, 2 mm mask opening, 3–4 marks, 3.35 mm edge clearance including keepout; validate specific service.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.12: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-FID : JLCPCB — How to Add Edge Rails and Fiducials for PCB Assembly Orders — https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order
- OWN row 6: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-070 — Fiducials in clear area (not obscured)
**Priority:** standard · **Applicable:** Boards with corresponding manufacturing/assembly process · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Fiducials in clear area (not obscured).

**Why:** Optical placement alignment requires unobstructed, correct reference marks.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Determine assembler service/panel requirements; place un-drilled copper marks, appropriate mask clear and asymmetric geometry.

**Pass when:**
- Fiducial pattern meets the selected assembler requirements and is visible to cameras.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- JLCPCB-specific geometry can change by service tier and should be checked with the actual selected assembly option.
- JLCPCB Sept 2026: recommended 1 mm copper, 2 mm mask opening, 3–4 marks, 3.35 mm edge clearance including keepout; validate specific service.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.12: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-FID : JLCPCB — How to Add Edge Rails and Fiducials for PCB Assembly Orders — https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-071 — Tooling holes present if needed
**Priority:** standard · **Applicable:** Boards with corresponding manufacturing/assembly process · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Tooling holes present if needed.

**Why:** Fixture alignment may need separate mechanical registration holes.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check whether selected assembly/panel equipment needs NPTH holes and their geometry.

**Pass when:**
- Tooling-hole dimensions/location meet assembler setup.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- JLCPCB-specific geometry can change by service tier and should be checked with the actual selected assembly option.
- Fiducials are not tooling holes and should be specified separately.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.12: Predictable Designs — Design Review Checklist: PCB Layout
- OWN row 6: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-072 — Component orientation consistent (same direction where possible)
**Priority:** standard · **Applicable:** Boards with corresponding manufacturing/assembly process · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Component orientation consistent (same direction where possible).

**Why:** Consistent orientation reduces assembly and inspection mistakes.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Verify pin1/cathode marking and compare placements with assembly drawings.

**Pass when:**
- Orientation is electrically correct and markings are visible after population.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- JLCPCB-specific geometry can change by service tier and should be checked with the actual selected assembly option.
- Routing and thermal needs can override cosmetic orientation uniformity.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.12: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-073 — Fine-pitch components oriented for easier inspection
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Fine-pitch components oriented for easier inspection.

**Why:** High-density pads require reliable soldering and inspection access.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check reflow orientation, solder-mask constraints, paste design and optical/x-ray inspection.

**Pass when:**
- Assembler can place, inspect and rework as needed.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- JLCPCB-specific geometry can change by service tier and should be checked with the actual selected assembly option.
- Uniform orientation is less important than solderability and access.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.12: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-074 — Panelization appropriate if multiple boards per panel
**Priority:** standard · **Applicable:** Boards with corresponding manufacturing/assembly process · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Panelization appropriate if multiple boards per panel.

**Why:** Panel handling and board separation can damage edge components.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Validate breakaways, tabs, mousebites, V-score, rails and depanel tool against BOM and outline.

**Pass when:**
- Panel fits process and can be depanelised without part damage.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- JLCPCB-specific geometry can change by service tier and should be checked with the actual selected assembly option.
- Choose panel technology consistent with edge components, layer stack and flex restrictions.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.12: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-075 — Breakaway tabs or V-scoring visible if panelized
**Priority:** standard · **Applicable:** Boards with corresponding manufacturing/assembly process · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Breakaway tabs or V-scoring visible if panelized.

**Why:** Panel handling and board separation can damage edge components.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Validate breakaways, tabs, mousebites, V-score, rails and depanel tool against BOM and outline.

**Pass when:**
- Panel fits process and can be depanelised without part damage.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- JLCPCB-specific geometry can change by service tier and should be checked with the actual selected assembly option.
- Choose panel technology consistent with edge components, layer stack and flex restrictions.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.12: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-12 — Silkscreen and markings
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-076 — All ICs have pin 1 marked clearly
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: All ICs have pin 1 marked clearly.

**Why:** Ambiguous orientation marking causes placement errors.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. View printed/soldered board and confirm marker aligns with real pin-1 pad.

**Pass when:**
- Pin1 is unambiguous after placement where inspection is necessary.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Marks must survive component placement and silkscreen clipping; minimum text/stroke limits vary by fab.
- Move marking outside component body or place in assembly drawing when board space prohibits.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.13: Predictable Designs — Design Review Checklist: PCB Layout
- OWN row 3: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-077 — Polarized components have polarity marked (+/-, cathode stripe)
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Polarized components have polarity marked (+/-, cathode stripe).

**Why:** Reversed polarity may destroy components or produce hazardous failures.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check diode cathode, electrolytic polarity, LED orientation and footprint conventions from datasheet.

**Pass when:**
- Marks match component and net polarity and remain visible after assembly.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Marks must survive component placement and silkscreen clipping; minimum text/stroke limits vary by fab.
- Diode and LED package marks may differ between manufacturers.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.13: Predictable Designs — Design Review Checklist: PCB Layout
- OWN row 4: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-078 — Component reference designators present and readable
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Component reference designators present and readable.

**Why:** Refdes aid rework, test and assembly identification.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check readability in Gerber with components mounted.

**Pass when:**
- Useful references visible or provided on controlled assembly drawing.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Marks must survive component placement and silkscreen clipping; minimum text/stroke limits vary by fab.
- Not all dense designs can print every refdes; prioritize correctness and drawing.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.13: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-079 — Silkscreen not covering pads or vias
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Silkscreen not covering pads or vias.

**Why:** Ink on pads can impair solder wetting or be clipped unexpectedly.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Inspect Gerber legend against mask openings and paste layers.

**Pass when:**
- No problematic silkscreen reaches exposed pads/metal.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Marks must survive component placement and silkscreen clipping; minimum text/stroke limits vary by fab.
- JLCPCB currently lists 0.15 mm pad-to-silkscreen clearance as a capability.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.13: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-080 — Board revision number visible on silkscreen
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Board revision number visible on silkscreen.

**Why:** Unmarked board revisions cause field and assembly confusion.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare board silkscreen, schematic title block, BOM/assembly files and version-control tag.

**Pass when:**
- All release deliverables share a unique approved revision.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Marks must survive component placement and silkscreen clipping; minimum text/stroke limits vary by fab.
- Revision is not the same as board serial number.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.13: Predictable Designs — Design Review Checklist: PCB Layout
- OWN row 9: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-081 — Company name or logo present if appropriate
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Company name or logo present if appropriate.

**Why:** Branding and ownership markings can help traceability.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Place optional logo where it does not obscure functional identifiers or pads.

**Pass when:**
- Logo and functional labels are readable without violating DFM.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Marks must survive component placement and silkscreen clipping; minimum text/stroke limits vary by fab.
- Optional; remove branding before removing any safety/connector marking.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.13: Predictable Designs — Design Review Checklist: PCB Layout
- OWN row 17: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-082 — Test point labels present where applicable
**Priority:** high · **Applicable:** Boards requiring programming/debug/test access · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Test point labels present where applicable.

**Why:** Identified test pads speed bring-up and prevent probing wrong rail.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Mark ground, rail voltage, critical interfaces and reset with meaningful identifiers.

**Pass when:**
- Technician can correlate probe pad to schematic without ambiguity.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Marks must survive component placement and silkscreen clipping; minimum text/stroke limits vary by fab.
- Tiny boards may use an indexed test-point map rather than complete silk legends.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.13: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-083 — Connector pin numbering marked if helpful
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Connector pin numbering marked if helpful.

**Why:** Harness wiring relies on physical mating-face pin numbering.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare symbol and footprint numbering to connector manufacturer drawings (both views).

**Pass when:**
- Pin numbering and signal assignments agree with the actual mating orientation.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Marks must survive component placement and silkscreen clipping; minimum text/stroke limits vary by fab.
- Front vs rear view reversal is a frequent error.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.14: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-084 — Silkscreen text size readable (>1mm height)
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Silkscreen text size readable (>1mm height).

**Why:** Undersized text may vanish or become unreadable after printing.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Check physical height and stroke against chosen fab and actual board view.

**Pass when:**
- Text meets the fabricator readability limit and remains visible.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Marks must survive component placement and silkscreen clipping; minimum text/stroke limits vary by fab.
- JLCPCB currently lists 1.0 mm minimum height and 0.15 mm line width; choose larger when practical.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.14: Predictable Designs — Design Review Checklist: PCB Layout
- JLC-CAP : JLCPCB — PCB Manufacturing & Assembly Capabilities — https://jlcpcb.com/capabilities/pcb-capabilities/

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-13 — Stackup
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-085 — Layer count appropriate (not excessive)
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Layer count appropriate (not excessive).

**Why:** Insufficient reference planes can compromise return paths; excess layers add cost.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Determine signal classes, power density and ground requirements before final layer count.

**Pass when:**
- Stackup supports electrical, thermal, cost and fabrication goals.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A symmetric stack can help warpage, but controlled impedance and mechanical stack needs must be agreed with the fab.
- A two-layer board is not inherently wrong; consider 4+ layers if ground continuity cannot be maintained.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.14: Predictable Designs — Design Review Checklist: PCB Layout
- JOHN-VID t=993s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-086 — Ground layers positioned for signal return paths
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Ground layers positioned for signal return paths.

**Why:** A nearby uninterrupted reference reduces return path impedance and loop area.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. View the plane under representative signals and around vias, connectors and cutouts.

**Pass when:**
- Return paths remain continuous without long detours for critical signals.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A symmetric stack can help warpage, but controlled impedance and mechanical stack needs must be agreed with the fab.
- Power planes can act as valid references with appropriate return-current transitions in some stackups.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.14: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-087 — Power planes present where appropriate
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Power planes present where appropriate.

**Why:** Disjoint and thin planes can create unintended impedance and EMI problems.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Refill zones and inspect copper islands, voids, neckdowns and rail isolation.

**Pass when:**
- Planes provide intended current/return path without shorts or bottlenecks.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A symmetric stack can help warpage, but controlled impedance and mechanical stack needs must be agreed with the fab.
- Do not add isolated pours merely to increase copper coverage.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.14: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-088 — Stackup appears symmetrical (prevents warping)
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Stackup appears symmetrical (prevents warping).

**Why:** Stackup imbalance can contribute to board warp and unexpected impedance.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Obtain fabricator stack data and verify dielectric/copper symmetry and impedance targets.

**Pass when:**
- Selected stackup can be manufactured at agreed thickness and impedances.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A symmetric stack can help warpage, but controlled impedance and mechanical stack needs must be agreed with the fab.
- Use actual pre-preg/core availability; do not infer dielectric from nominal board thickness.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.14: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-089 — Layer thicknesses reasonable
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Layer thicknesses reasonable.

**Why:** Stackup imbalance can contribute to board warp and unexpected impedance.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Obtain fabricator stack data and verify dielectric/copper symmetry and impedance targets.

**Pass when:**
- Selected stackup can be manufactured at agreed thickness and impedances.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- A symmetric stack can help warpage, but controlled impedance and mechanical stack needs must be agreed with the fab.
- Use actual pre-preg/core availability; do not infer dielectric from nominal board thickness.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.14: Predictable Designs — Design Review Checklist: PCB Layout
- JOHN-VID t=1110s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## PCB-14 — Final layout verification
Review mechanical implementation, electrical routing, assembly access and electromagnetic/thermal effects in the completed layout.

### PCB-090 — Avoid: obvious DRC violations visible
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: No obvious DRC violations visible.

**Why:** DRC finds electrical clearance and unrouted faults but not all functional errors.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Refill copper; run all enabled design checks; review every warning and configured waiver.

**Pass when:**
- Zero unresolved critical errors and documented, approved exceptions.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manually accepted DRC exclusions need a written justification and reviewer signoff.
- A green DRC report alone is not a board release.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.15: Predictable Designs — Design Review Checklist: PCB Layout
- JOHN-VID t=1076s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-091 — All component footprints appear correct
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: All component footprints appear correct.

**Why:** The wrong land pattern or pad numbering can make a board unpopulatable.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Compare every critical footprint against manufacturer land pattern and 3D/body dimensions.

**Pass when:**
- Footprints and pin mappings are verified and version-controlled.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manually accepted DRC exclusions need a written justification and reviewer signoff.
- Verify thermal pad, pin1, NPTH/PTH and unusual side-specific packages.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.15: Predictable Designs — Design Review Checklist: PCB Layout
- OWN row 14: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-092 — Net names visible and make sense
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: Net names visible and make sense.

**Why:** Mislabelled nets can connect unintentionally across sheets.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Review power aliases, hierarchical/global labels and all repeated net labels.

**Pass when:**
- Names express function and voltage, with no accidental cross-sheet ties.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manually accepted DRC exclusions need a written justification and reviewer signoff.
- Avoid relying on automatically assigned net names for critical power signals.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.15: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-093 — BOM count matches components on board
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: BOM count matches components on board.

**Why:** Mismatch between CAD and parts list leads to assembly omissions.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Reconcile reference designators, fitted/DNP variants and quantity per assembly across BOM and CPL.

**Pass when:**
- All placed parts are represented with correct population state and quantities.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manually accepted DRC exclusions need a written justification and reviewer signoff.
- Include mechanical, alternate and DNP components intentionally.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.15: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-094 — Test points accessible
**Priority:** high · **Applicable:** Boards requiring programming/debug/test access · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Test points accessible.

**Why:** Board-level measurements need repeatable and safe probe access.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. List rails, ground, reset, programming, clocks and failure-critical signals; reserve pads for probes/fixtures.

**Pass when:**
- Required signals are accessible with the intended probe/tool and enclosure state.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manually accepted DRC exclusions need a written justification and reviewer signoff.
- High-speed test pads can create stubs; use suitable probing or reserved footprints.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.15: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-095 — Programming header accessible and properly connected
**Priority:** standard · **Applicable:** Boards requiring programming/debug/test access · **Conditional:** Yes

**Check / intent:** Review whether this source checklist requirement is satisfied: Programming header accessible and properly connected.

**Why:** Test fixtures can be blocked after mechanical assembly.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Overlay probe/cable keepout and verify power/debug connection under enclosure constraints.

**Pass when:**
- Manufacturing and service programming remain possible.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manually accepted DRC exclusions need a written justification and reviewer signoff.
- USB bootloader may substitute for a header if recovery path is documented.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.15: Predictable Designs — Design Review Checklist: PCB Layout

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### PCB-096 — Avoid: obvious routing errors (traces going wrong direction)
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review whether this source checklist requirement is satisfied: No obvious routing errors (traces going wrong direction).

**Why:** DRC may allow nets that are connected to the wrong intended function.

**How to verify:**
1. Inspect the routed PCB in both 2D and 3D with zones refilled, plus stackup, DRC settings and selected manufacturer capabilities.
2. Perform independent visual net highlighting for high-impact power/interface/reset paths.

**Pass when:**
- No unexplained route topology or misplaced net connections.
- Record the applicable component datasheet, calculation, or manufacturer rule and resolve any deviation before approval.

**Constraints and guidance:**
- Manually accepted DRC exclusions need a written justification and reviewer signoff.
- Cross-check with schematic, not just connectivity engine.

**Evidence to record:** PCB editor inspection / screenshot; DRC, fabrication rule or relevant mechanical calculation

**Sources:**
- PD-LAY p.15: Predictable Designs — Design Review Checklist: PCB Layout
- PHIL : Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## EXT-01 — Personal and cross-cutting checks
Cross-cutting checks from your own checklist and later video sources that warrant independent review steps.

### EXT-001 — Mark outlines for test pads and mechanically important features
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Mark outlines for test pads and mechanically important features.

**Why:** A technician must find test pads, connector mechanical outlines and special touch points quickly.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Annotate test points, selected connector envelopes and clearance-critical hardware in appropriate legend/assembly layers.

**Pass when:**
- All functional indicators remain visible on finished or installed board.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Do not obscure exposed pads or overlap reference designators.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 2: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-002 — Label connector functions, not only pin numbers
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Label connector functions, not only pin numbers.

**Why:** A connector may be correctly numbered yet impossible to wire safely without the pin-function legend.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. For each external connector, label supply, ground and meaningful signal roles (for example A/B, CAN-H/CAN-L, TX/RX) and match the mating view.

**Pass when:**
- All essential connector functions are unambiguous from installed orientation or controlled wiring drawing.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Do not print misleading labels under connector bodies; use assembly drawing if board space is insufficient.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 7: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-003 — Mark buttons, jumpers, indicators and mounting features
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Mark buttons, jumpers, indicators and mounting features.

**Why:** Functional labels reduce board bring-up and installation errors.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Check labels for LEDs, buttons, reset, jumpers, polarity switches, sensor ports and hardware locations in the 3D populated view.

**Pass when:**
- Technician can identify the function of each important manual/service feature.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Prefer function labels to abbreviations that can be confused across revisions.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 10: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-004 — Check connector labels are visible after assembly
**Priority:** standard · **Applicable:** Boards with corresponding manufacturing/assembly process · **Conditional:** Yes

**Check / intent:** Review and document this distinct project requirement: Check connector labels are visible after assembly.

**Why:** Labels hidden by plugged connectors cannot support field service.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Inspect 3D model with mating cables and nearby enclosure parts; move text or document it elsewhere.

**Pass when:**
- All important labels remain readable in the relevant service state.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Check both board and enclosure viewing orientations.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 11: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-005 — Verify connectors can mate near board edge and enclosure
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Yes

**Check / intent:** Review and document this distinct project requirement: Verify connectors can mate near board edge and enclosure.

**Why:** A connector can clear DRC yet collide with enclosure wall or adjacent cable.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Check shell overhang, mating plug envelope, latch release, bend radius, edge-to-copper and required panel rail.

**Pass when:**
- Connector mating/unmating is physically feasible with tolerance.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Use real connector 3D model and manufacturer drawing.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 12: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-006 — Review UART-to-RS-485 transceiver signal directions and enable pins
**Priority:** critical · **Applicable:** UART/serial interfaces · **Conditional:** Yes

**Check / intent:** Review and document this distinct project requirement: Review UART-to-RS-485 transceiver signal directions and enable pins.

**Why:** UART/RS-485 failures often result from swapped MCU/DI/RO signals or inverted DE/RE control.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Trace CPU TX→transceiver DI; transceiver RO→CPU RX, verify DE/RE and bus-side A/B per transceiver convention.

**Pass when:**
- All logic direction, control polarity, voltage domain and bus termination verified against exact transceiver.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Bus A/B naming conventions differ; never infer polarity from letter alone.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 13: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-007 — Decide whether to print board production date or build date code
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Decide whether to print board production date or build date code.

**Why:** A visible code can help field traceability but should match the actual production process.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Define fixed PCB artwork code vs variable manufacturing label and ensure documentation explains it.

**Pass when:**
- Date / lot marking is correct for the release and traceability process.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- A fixed Gerber date is not a true board-specific manufacture date.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 8: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-008 — Reserve a unique serial-number marking area where required
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Yes

**Check / intent:** Review and document this distinct project requirement: Reserve a unique serial-number marking area where required.

**Why:** Per-unit serialisation supports traceability and service history.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Provide an accessible label/laser/ink box with sufficient margin and confirm supplier printing workflow.

**Pass when:**
- Unique ID can be applied and scanned/read without damaging functional labels.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Optional for non-serialized prototypes.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 18: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-009 — Provide battery charging and protection appropriate to battery chemistry
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Provide battery charging and protection appropriate to battery chemistry.

**Why:** Cell faults, deep discharge and charging errors can create major safety and reliability risks.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Check cell pack protection, charger topology, voltage/current limits, temperature sensing, shipping modes and connector miswire.

**Pass when:**
- Battery system is protected against realistic abuse cases and meets intended certification scope.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Protected cells do not automatically remove the need for product-level protection.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- JOHN-VID t=158s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-010 — Validate low-power modes and total battery energy budget
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Validate low-power modes and total battery energy budget.

**Why:** A nominal low-power MCU may be defeated by external leakage, regulator quiescent current or pullups.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Build sleep/wake state table, measure expected duty cycle and leakage, and compute lifetime under worst-case temperature/aging.

**Pass when:**
- Expected runtime meets required duration with stated margin and wake behavior.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Firmware configuration and peripheral off-state current are part of the electrical review.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- JOHN-VID t=436s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-011 — Assess solder joint robustness of mechanically stressed parts
**Priority:** high · **Applicable:** Boards with corresponding manufacturing/assembly process · **Conditional:** Yes

**Check / intent:** Review and document this distinct project requirement: Assess solder joint robustness of mechanically stressed parts.

**Why:** Large components, cable connectors and repeated handling can crack solder joints.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Review strain relief, through-hole reinforcement, anchors, pad layout and expected drop/vibration cycles.

**Pass when:**
- Mechanically stressed parts have adequate retention and assembly process.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- SMT-only connectors may need support tabs, adhesive or chassis load path.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- JOHN-VID t=224s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-012 — Verify temperature-dependent ratings and operational thermal testing plan
**Priority:** critical · **Applicable:** Heat-dissipating circuits · **Conditional:** Yes

**Check / intent:** Review and document this distinct project requirement: Verify temperature-dependent ratings and operational thermal testing plan.

**Why:** Capacitor life, MOSFET RDS(on), resistor ratings, crystal drift and battery performance change with temperature.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Review part derating curves at ambient extremes; plan maximum-load tests in representative enclosure and orientation.

**Pass when:**
- Bench/enclosure evidence shows all parts within specified operating and lifetime envelope.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- A thermal camera image alone does not yield junction temperature without calibration/model.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- JOHN-VID t=1177s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-013 — Check component availability and approved alternates before release
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Check component availability and approved alternates before release.

**Why:** An electrically correct layout can be impractical to produce if key parts are unavailable.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Revalidate supplier stock, lifecycle, lead time, substitutions and footprint compatibility using final BOM.

**Pass when:**
- Build quantity can be sourced or approved alternates exist.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Supply conditions change: check again before each batch.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- JOHN-VID t=1235s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-014 — Plan interface protection, filtering and cable shields
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Plan interface protection, filtering and cable shields.

**Why:** Cables can conduct ESD, surges, conducted RF and radiated interference into the board.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Identify external interfaces and choose ESD, common-mode filtering, chassis/return connection and surge strategy based on cable environment.

**Pass when:**
- Protection and filtering meet product EMC/safety targets and maintain signal bandwidth.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Do not automatically connect cable shield to digital ground without system-level EMC review.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- JOHN-VID t=1337s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-015 — Review whether an added ground layer is warranted
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Review whether an added ground layer is warranted.

**Why:** A nominally cheaper two-layer board may prevent reliable high-speed return paths and increase redesign cost.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Compare two-layer routes/ground cutouts against a 4-layer stack with a continuous reference; document trade-offs.

**Pass when:**
- Chosen layer count provides acceptable reference, power and layout performance.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Two layers are valid where return paths and routing requirements can be met.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- JOHN-VID t=993s: John Teel — 21 Worst PCB Design Mistakes — https://www.youtube.com/watch?v=D5gHNvsrX08

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-016 — Review trace spacing beyond fabrication minima
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Review trace spacing beyond fabrication minima.

**Why:** Closely parallel traces can couple even when DRC considers them manufacturable.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Review spacing relative to reference-plane height, edge rates, parallel length and victim sensitivity.

**Pass when:**
- Signal noise/crosstalk risk is acceptable with documented rule/analysis.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Phil article suggests spacing around 3× the adjacent dielectric height as a useful starting heuristic—not a fixed requirement.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- PHIL t=42s: Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-017 — Define signal-class trace widths and controlled impedance
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Define signal-class trace widths and controlled impedance.

**Why:** Uniform trace widths ignore current heating, noise susceptibility and impedance targets.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Create net classes for power, clocks, precision analog, RF and high-speed; use current and impedance calculations.

**Pass when:**
- Each class has justified minimum/target width and clearance matched to fab stackup.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Do not set signal widths from manufacturing minimum alone.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- PHIL t=220s: Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-018 — Review all via pad, drill and annular-ring sizes
**Priority:** high · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Review all via pad, drill and annular-ring sizes.

**Why:** Vias can fail manufacture or overheat if drills/rings are poorly chosen.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Check via pad/drill, annular ring, copper thickness, current and return-path transition; use fab capabilities.

**Pass when:**
- Standard and special vias meet fabricator rules plus required electrical performance.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Phil’s example 0.7 mm pad / 0.3 mm drill is not a universal via dimension.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- PHIL t=361s: Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them — https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-019 — Inspect filled copper planes and check return-path bottlenecks
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Inspect filled copper planes and check return-path bottlenecks.

**Why:** Unrefilled zones may conceal open traces, isolated ground and unsuitable thermal spokes.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Refill all copper zones, then view filled mode on every layer and highlight supply/return net segments.

**Pass when:**
- No unintended plane islands, broken returns, neckdowns or thermal/electrical connection mistakes.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Compare filled Gerbers with CAD layers; do not trust zone outlines alone.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 15: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-020 — Review via-in-pad solder-wicking and thermal-via details
**Priority:** high · **Applicable:** Heat-dissipating circuits · **Conditional:** Yes

**Check / intent:** Review and document this distinct project requirement: Review via-in-pad solder-wicking and thermal-via details.

**Why:** Open barrels within solder land can draw solder away from the joint.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Review via drill vs pad geometry, solder paste reductions, component-side tenting or filled/capped fabrication options and heat path.

**Pass when:**
- Via/paste construction is consistent with selected IC and assembler design rules.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Your original “0.3 mm” likely refers to drill but was not specified; require explicit via dimensions and method.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 16: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### EXT-021 — Optional SVG company logo reviewed for manufacturability
**Priority:** standard · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Yes

**Check / intent:** Review and document this distinct project requirement: Optional SVG company logo reviewed for manufacturability.

**Why:** A large logo can crowd essential labels or fail minimum artwork sizes.

**How to verify:**
1. Inspect the relevant schematic, assembled 3D board, CAD release artifacts or bench test depending on the check.
2. Inspect SVG import, copper/silk layer selection, clearances and Gerber image.

**Pass when:**
- Optional logo is legible and does not obscure functional information.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Branding never takes priority over safety/connector markings.

**Evidence to record:** Review notes and relevant CAD or manufacturing artifact

**Sources:**
- OWN row 17: Original personal PCB checklist

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## REL-01 — Final manufacturing and release
Perform final production readiness and controlled release review after design changes have been incorporated.

### REL-001 — Generate Gerbers and drill files from the approved CAD revision
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Generate Gerbers and drill files from the approved CAD revision.

**Why:** A CAD design is not what the fab builds: output layer/outline/drill errors can invalidate it.

**How to verify:**
1. Regenerate manufacturing outputs from the final saved revision, independently inspect the exports and approve the release package.
2. Freeze revision, refill zones, run DRC, plot all copper/mask/silk/Edge.Cuts and separate plated/non-plated drill files as supported.

**Pass when:**
- Archive includes every required fabrication layer and correctly interpreted holes, slots and contour.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Use current KiCad/JLCPCB instructions corresponding to installed software; original KiCad 7 link is a legacy reference.

**Evidence to record:** Released Gerber / drill / BOM / CPL package; Independent CAM/3D comparison and sign-off

**Sources:**
- OWN row 21: Original personal PCB checklist
- JLC-K9 : JLCPCB — How to Generate Gerber and Drill Files from KiCad 9 — https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-9

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### REL-002 — Independently inspect Gerbers and drill files in a viewer
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Independently inspect Gerbers and drill files in a viewer.

**Why:** A plotting configuration error may not appear in the CAD editor.

**How to verify:**
1. Regenerate manufacturing outputs from the final saved revision, independently inspect the exports and approve the release package.
2. Open generated files in a separate viewer; verify copper, outline, NPTH/PTH holes, vias, mask, silk, paste and registration.

**Pass when:**
- Independent render agrees with approved PCB geometry and layer count.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Check stencil/assembly paste separately if ordering stencil or SMT assembly.

**Evidence to record:** Released Gerber / drill / BOM / CPL package; Independent CAM/3D comparison and sign-off

**Sources:**
- JLC-K9 : JLCPCB — How to Generate Gerber and Drill Files from KiCad 9 — https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-9
- JLC-K9 : JLCPCB — How to Generate Gerber and Drill Files from KiCad 9 — https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-9

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### REL-003 — Generate and validate manufacturing BOM with supplier part numbers
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Generate and validate manufacturing BOM with supplier part numbers.

**Why:** The assembler needs exact MPN / LCSC identities and population state.

**How to verify:**
1. Regenerate manufacturing outputs from the final saved revision, independently inspect the exports and approve the release package.
2. Generate BOM from the final schematic; check refdes, value, footprint, quantity, DNP status and supplier part IDs.

**Pass when:**
- Every placed part has a valid supply/assembly definition; exceptions tracked.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Preserve the original project-specific BOM script as an option but verify against current JLCPCB required headers.

**Evidence to record:** Released Gerber / drill / BOM / CPL package; Independent CAM/3D comparison and sign-off

**Sources:**
- OWN row 24: Original personal PCB checklist
- JLC-K10 : JLCPCB — How to Export BOM and Pick & Place Files From KiCad 10 — https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### REL-004 — Generate and visually validate pick-and-place / CPL file
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Generate and visually validate pick-and-place / CPL file.

**Why:** Wrong rotation, side or origin causes systematic assembly errors.

**How to verify:**
1. Regenerate manufacturing outputs from the final saved revision, independently inspect the exports and approve the release package.
2. Generate centroid using correct PCB origin/units; verify Designator, Mid X, Mid Y, Rotation and Layer, then visually compare preview.

**Pass when:**
- All assembled parts match approved placement, side and rotation.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Original header mapping Ref→Designator; PosX→Mid X; PosY→Mid Y; Rot→Rotation; Side→Layer remains useful if exports require mapping.

**Evidence to record:** Released Gerber / drill / BOM / CPL package; Independent CAM/3D comparison and sign-off

**Sources:**
- OWN row 27: Original personal PCB checklist
- JLC-K10 : JLCPCB — How to Export BOM and Pick & Place Files From KiCad 10 — https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### REL-005 — Reconcile BOM, CPL, footprint population and assembly drawings
**Priority:** critical · **Applicable:** Boards with corresponding manufacturing/assembly process · **Conditional:** Yes

**Check / intent:** Review and document this distinct project requirement: Reconcile BOM, CPL, footprint population and assembly drawings.

**Why:** Even valid individual files may disagree about fitted parts and orientations.

**How to verify:**
1. Regenerate manufacturing outputs from the final saved revision, independently inspect the exports and approve the release package.
2. Compare all fitted/DNP designators and sample polarity-sensitive parts on the manufacturer preview.

**Pass when:**
- Quantities, designators, footprint orientations and assembly variants agree.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- Do not rely on automatic part matching without reviewing substituted parts.

**Evidence to record:** Released Gerber / drill / BOM / CPL package; Independent CAM/3D comparison and sign-off

**Sources:**
- JLC-K10 : JLCPCB — How to Export BOM and Pick & Place Files From KiCad 10 — https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad
- JLC-K10 : JLCPCB — How to Export BOM and Pick & Place Files From KiCad 10 — https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________

### REL-006 — Perform final release gate with reviewer sign-off
**Priority:** critical · **Applicable:** All PCB projects (review for applicability) · **Conditional:** Review all

**Check / intent:** Review and document this distinct project requirement: Perform final release gate with reviewer sign-off.

**Why:** Unresolved critical checks can enter production unnoticed without a formal gate.

**How to verify:**
1. Regenerate manufacturing outputs from the final saved revision, independently inspect the exports and approve the release package.
2. Review critical/high failures, accepted exceptions, device-specific data, revision and manufacturing zip checksum.

**Pass when:**
- No unresolved critical failure; all review exceptions have reviewer and rationale, revision is frozen.
- Document any justified exception with owner, consequence and planned validation.

**Constraints and guidance:**
- N/A is acceptable only with a reason for conditional checks.

**Evidence to record:** Released Gerber / drill / BOM / CPL package; Independent CAM/3D comparison and sign-off

**Sources:**
- GUIDE : Guide author — consolidated engineering review and release gate

**Review record:** ☐ Pass ☐ Fail ☐ Needs review ☐ N/A · Notes: _________ · Evidence: _________


## Source registry

- **GUIDE:** Guide author — consolidated engineering review and release gate; 
- **PD-SCH:** Predictable Designs — Design Review Checklist: Schematic Circuit; PredictableDesigns_DesignReviewChecklist_Schematic.pdf
- **PD-LAY:** Predictable Designs — Design Review Checklist: PCB Layout; PredictableDesigns_DesignReviewChecklist_PCBlayout.pdf
- **OWN:** Original personal PCB checklist; pcb-checklist.xlsx
- **PREV:** Earlier consolidated PCB guide; pcb-design-guide-consolidated.xlsx
- **PHIL:** Phil Salmony (Altium) — Beginner PCB Design Mistakes and How To Avoid Them; https://resources.altium.com/p/top-5-pcb-design-mistakes-and-how-fix-them
- **PHIL-VID:** Altium Academy / Phil Salmony — Top 5 Beginner PCB Design Mistakes; https://www.youtube.com/watch?v=D0X76Kbf8fQ
- **JOHN-VID:** John Teel — 21 Worst PCB Design Mistakes; https://www.youtube.com/watch?v=D5gHNvsrX08
- **JLC-FID:** JLCPCB — How to Add Edge Rails and Fiducials for PCB Assembly Orders; https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order
- **JLC-CAP:** JLCPCB — PCB Manufacturing & Assembly Capabilities; https://jlcpcb.com/capabilities/pcb-capabilities/
- **JLC-K9:** JLCPCB — How to Generate Gerber and Drill Files from KiCad 9; https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-9
- **JLC-K10:** JLCPCB — How to Export BOM and Pick & Place Files From KiCad 10; https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad
- **TI-GND:** Texas Instruments — High-Speed Layout Guidelines / Practical PCB Design Rules; https://www.ti.com/lit/an/scaa082a/scaa082a.pdf
- **TI-DEC:** Texas Instruments — Mixed Signals, Grounding and Bypass Capacitors; https://www.ti.com/video/6245227303001
- **TI-POWER:** Texas Instruments — PowerPAD Thermally Enhanced Package; https://www.ti.com/lit/an/slma002h/slma002h.pdf