# ESP32_board — KiCad 10 library

Reusable KiCad symbol and footprint library for plug-in ESP32 development boards.

Included:

- `symbols/ESP32_board.kicad_sym`
- `footprints/ESP32_board.pretty/`

## Global installation

### Symbol library

1. Open **Preferences → Manage Symbol Libraries**.
2. Select **Global Libraries**.
3. Click the folder button.
4. Select `symbols/ESP32_board.kicad_sym`.
5. Use the nickname `ESP32_board`.

### Footprint library

1. Open **Preferences → Manage Footprint Libraries**.
2. Select **Global Libraries**.
3. Click the folder button.
4. Select the folder `footprints/ESP32_board.pretty`.
5. Use the nickname `ESP32_board`.

The footprint references embedded in the symbols are:

- `ESP32_board:Waveshare_ESP32_S3_C6_Zero_THT`
- `ESP32_board:LOLIN_ESP32_S2_Mini_Socket`

## Reuse across projects

Keep the repository in a permanent location so registered global paths remain
valid. For project-local registration, prefer `${KIPRJMOD}`-relative paths.

Verify the footprint against the exact physical board revision before PCB fabrication.
