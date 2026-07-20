# ESP32_board — KiCad 10 library

Reusable KiCad symbol and footprint library for plug-in ESP32 development boards.

Included:

- `ESP32_board.kicad_sym`
- `ESP32_board.pretty/Waveshare_ESP32_S3_C6_Zero_THT.kicad_mod`
- `ESP32_board.pretty/LOLIN_ESP32_S2_Mini_Socket.kicad_mod`
- project-local `sym-lib-table`
- project-local `fp-lib-table`

## Global installation

### Symbol library

1. Open **Preferences → Manage Symbol Libraries**.
2. Select **Global Libraries**.
3. Click the folder button.
4. Select `ESP32_board.kicad_sym`.
5. Use the nickname `ESP32_board`.

### Footprint library

1. Open **Preferences → Manage Footprint Libraries**.
2. Select **Global Libraries**.
3. Click the folder button.
4. Select the folder `ESP32_board.pretty`.
5. Use the nickname `ESP32_board`.

The footprint references embedded in the symbols are:

- `ESP32_board:Waveshare_ESP32_S3_C6_Zero_THT`
- `ESP32_board:LOLIN_ESP32_S2_Mini_Socket`

## Reuse across projects

For a global library, store the files in a permanent location such as:

`~/KiCad/Libraries/ESP32_board/`

Do not leave the registered library inside a Downloads folder that may later be moved or deleted.

Verify the footprint against the exact physical board revision before PCB fabrication.
