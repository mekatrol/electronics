# Bench Tests

Record board revision, firmware commit, tools, connections, expected result,
actual result, and pass/fail for every test.

## Phase 1

- [ ] SKR image boots without energizing any heater output.
- [ ] Mini 12864 remains electrically safe during reset and early boot.
- [ ] SKR can be recovered using the documented bootloader procedure.

## Future Peripheral Bring-Up

- [ ] SKR monotonic timer accuracy.
- [ ] SKR watchdog reset and reported reset cause.
- [ ] Diagnostic UART loopback.
- [ ] USB enumeration and CDC transfer.
- [ ] SKR SD mount, read, write, remove, and corrupt-card handling.
- [ ] Mini 12864 LCD, encoder, button, sounder, backlight, and RGB LEDs.
- [ ] Temperature sensor open/short/plausibility faults.
- [ ] Heater outputs remain off during reset, boot, link loss, and faults.
- [ ] Low-power dummy-load control.
