# WS2812 ESP32 KiCad 10 library — corrected package

This package contains:

- `WS2812_ESP32.kicad_sym`
- `WS2812_ESP32.pretty/Waveshare_ESP32_S3_C6_Zero_THT.kicad_mod`
- `WS2812_ESP32.pretty/LOLIN_ESP32_S2_Mini_Socket.kicad_mod`
- project-local `sym-lib-table`
- project-local `fp-lib-table`

## Why KiCad reported “footprint does not exist”

The symbol contains a footprint reference such as:

`WS2812_ESP32:Waveshare_ESP32_S3_C6_Zero_THT`

KiCad interprets this as:

- footprint-library nickname: `WS2812_ESP32`
- footprint name: `Waveshare_ESP32_S3_C6_Zero_THT`

Adding only the symbol library is not enough. The `.pretty` footprint library must also be registered with the exact nickname `WS2812_ESP32`.

## Recommended project-local installation

1. Extract this entire folder into the KiCad project directory.
2. Keep `sym-lib-table`, `fp-lib-table`, `WS2812_ESP32.kicad_sym`, and
   `WS2812_ESP32.pretty` beside the `.kicad_pro` file.
3. Close and reopen the KiCad project.
4. In the schematic, open Symbol Properties and confirm the footprint field is:
   `WS2812_ESP32:Waveshare_ESP32_S3_C6_Zero_THT`
   or
   `WS2812_ESP32:LOLIN_ESP32_S2_Mini_Socket`.

## Global installation

### Symbol

Preferences → Manage Symbol Libraries → Global Libraries → folder button

Select:

`WS2812_ESP32.kicad_sym`

Set nickname:

`WS2812_ESP32`

### Footprint

Preferences → Manage Footprint Libraries → Global Libraries → folder button

Select the folder:

`WS2812_ESP32.pretty`

Set nickname exactly:

`WS2812_ESP32`

Do not select an individual `.kicad_mod` file.

## Verification included in this package

- The symbol footprint properties exactly match the contained footprint names.
- Both required footprint files are present.
- The S3/C6 footprint has pads 1–18.
- The S2 Mini footprint has pads 1–32.

Mechanical dimensions and GPIO assignments should still be checked against the exact physical board revision before fabrication.
