# Shared KiCad resources

This is the canonical location for reusable KiCad assets in this repository.

```text
kicad/
├── symbols/       KiCad and legacy schematic symbol libraries
├── footprints/    Footprint libraries (`*.pretty`)
├── plugins/       Installable KiCad action plugins
├── modules/       Reusable Python scripts and helper modules
└── tools/         Installation and maintenance scripts
```

Project `sym-lib-table` and `fp-lib-table` files should refer to these folders
with paths relative to `${KIPRJMOD}`. Do not add machine-specific absolute paths.

The `ESP32_board` symbol library and footprint library share the nickname
`ESP32_board`. See [ESP32_board.md](ESP32_board.md) for installation details.

## Known external libraries

Some older projects refer to libraries whose source files are not present in
this repository: `FootprintLibrary` and `Raspberry_Pi_Pico_W_SC0918`. Their
cached symbols and footprints remain embedded in the projects, but editing or
updating those library items requires recovering the original libraries.
