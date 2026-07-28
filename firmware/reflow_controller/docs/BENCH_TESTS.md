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

## Phase 2

Use heater power disconnected for every test in this section. Record the
board revision, measuring instrument, firmware commit, and actual readings.

- [ ] SKR monotonic timer accuracy.
- [ ] SKR watchdog reset and reported reset cause.
- [ ] UART0 loopback at 115200 8N1 (one byte is serviced per scheduler pass).
- [ ] USB enumeration and CDC transfer.
- [ ] SKR SD FAT32 mount/root read, removal, and corrupt-card handling.
- [ ] Temperature inputs AD0.0, AD0.1, and AD0.2 track known voltages.
- [ ] EXP connector pins retain safe reset states.
- [ ] Heater outputs remain low during reset, boot, unhandled interrupt, and
      watchdog reset.

USB CDC is not yet implemented and the remaining unchecked items are required
Phase 2 exit evidence. Do not mark Phase 2 complete or begin Phase 3 until all
of them pass.

## Future Peripheral Bring-Up

- [ ] Mini 12864 encoder, button, sounder, and dynamic RGB feedback.
- [ ] Temperature sensor open/short/plausibility faults.
- [ ] Low-power dummy-load control.
