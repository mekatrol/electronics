# Bench Tests

Record board revision, firmware commit, tools, connections, expected result,
actual result, and pass/fail for every test.

## Phase 1

- [ ] SKR image boots without energizing any heater output.
- [ ] Mini 12864 remains electrically safe during reset and early boot.
- [x] Mini 12864 shows `REFLOW CONTROLLER` and `DISPLAY READY` with correct
      orientation, column alignment, and readable contrast.
- [x] UC1701 initialization briefly turns every LCD pixel on before restoring
      normal display-RAM mode.
- [x] Mini 12864's three NeoPixels illuminate dim white without flicker.
- [x] SKR can be recovered using the documented bootloader procedure.

### 2026-07-28 Mini 12864 Bring-up

- Connections: 12 V board power, ST-Link SWD, and both LCD ribbon cables.
  ST-Link 5 V was not connected.
- Firmware was written as a raw binary at `0x00004000`; the restored BTT
  bootloader remained at address zero.
- The LPC vector checksum was verified as zero-sum before flashing.
- The UC1701 all-pixels diagnostic produced a solid dark rectangle, proving
  reset and command transfer.
- Inverted framebuffer bands displayed both bring-up strings clearly.
- Electronic volume `0x27` was only readable at an angle on this module.
  `0x3F` was readable straight-on and is the verified bring-up setting.
- The three-LED NeoPixel chain and LCD backlight worked with the timing ported
  from the CNC reference.

## Future Peripheral Bring-Up

- [ ] SKR monotonic timer accuracy.
- [ ] SKR watchdog reset and reported reset cause.
- [ ] Diagnostic UART loopback.
- [ ] USB enumeration and CDC transfer.
- [ ] SKR SD mount, read, write, remove, and corrupt-card handling.
- [ ] Mini 12864 encoder, button, sounder, and dynamic RGB feedback.
- [ ] Temperature sensor open/short/plausibility faults.
- [ ] Heater outputs remain off during reset, boot, link loss, and faults.
- [ ] Low-power dummy-load control.
