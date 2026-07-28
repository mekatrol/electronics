# Reflow Controller

Bare-metal firmware for:

- BIGTREETECH SKR 1.4 Turbo mainboard (`LPC1769`, Cortex-M3).
- BIGTREETECH Mini 12864 V1.0 display module.

The migration is phased in [AGENTS.md](AGENTS.md). The current Phase 1 scope is
the cross-platform build layout and a minimal SKR bring-up image containing an
inert Mini 12864 module. Reflow logic and peripherals are intentionally
migrated in later phases after the board foundations are verified.

The Mini 12864 is connected directly to the SKR and has no processor of its
own. There is only one firmware image.

## Prerequisites

Install:

- GNU Make.
- Arm GNU Toolchain containing `arm-none-eabi-gcc`,
  `arm-none-eabi-objcopy`, and `arm-none-eabi-size`.

Ensure those programs are on `PATH`. Use a terminal where GNU Make is named
`make`; on Windows this can be MSYS2, Chocolatey, Scoop, xPack, or another GNU
Make distribution.

### Windows PowerShell With WSL

Install the ARM cross-compiler and binary utilities in WSL:

```powershell
wsl sudo apt update
wsl sudo apt install gcc-arm-none-eabi binutils-arm-none-eabi
```

Then, from the project directory open in VS Code, verify the toolchain and
build the firmware:

```powershell
wsl make toolchain-check
wsl make clean all
```

The build output is:

```text
build/mainboard/btt_skr_1_4_turbo/firmware.bin
```

### VS Code IntelliSense Through WSL

The project compiler is installed inside WSL, so open the project in a WSL
VS Code window. From PowerShell in this directory:

```powershell
wsl code .
```

Alternatively, use the VS Code command palette and select:

```text
WSL: Reopen Folder in WSL
```

Install the recommended Microsoft C/C++, Makefile Tools, and WSL extensions
when prompted. The checked-in `.vscode/c_cpp_properties.json` selects
`/usr/bin/arm-none-eabi-gcc` and the project include directories.

If stale IntelliSense errors remain after reopening, run these commands from
the VS Code command palette:

```text
C/C++: Reset IntelliSense Database
Developer: Reload Window
```

## Build

From this directory:

```sh
make
```

`make mainboard` is an explicit alias for the default build.

Useful commands:

```sh
make clean
make print-config
```

Outputs:

- `build/mainboard/btt_skr_1_4_turbo/firmware.bin`

The image is linked after the factory BTT bootloader. Copy `firmware.bin` to a
FAT32 SD card, then follow the SKR update procedure. Do not flash or connect
heater power until the pin map and reset-state behavior have passed the bench
tests.

## Program The SKR Firmware

### Recommended: BTT SD-Card Bootloader

1. Run `wsl make clean all`.
2. Format a microSD card as FAT32.
3. Copy
   `build/mainboard/btt_skr_1_4_turbo/firmware.bin`
   to the card root as `firmware.bin`.
4. Turn off the SKR and disconnect heater power.
5. Insert the card, then power-cycle the SKR.
6. Check the card. A successful BTT bootloader update normally renames the
   file to `FIRMWARE.CUR`.

### ST-Link V2 And OpenOCD

The SKR 1.4 Turbo uses an NXP LPC1769. Use OpenOCD's `lpc17xx` target; do not
use STM32CubeProgrammer or `st-flash`.

Install OpenOCD and USB tools in WSL:

```powershell
wsl sudo apt update
wsl sudo apt install openocd usbutils
```

Wire the ST-Link V2 to the SKR SWD/JTAG programming header:

```text
ST-Link SWDIO -> SKR SWDIO
ST-Link SWCLK -> SKR SWCLK
ST-Link GND   -> SKR GND
ST-Link 3.3V  -> SKR 3.3V reference only
```

Verify the exact header labels and orientation on the board before applying
power. Do not connect the ST-Link 5 V pin. Power the SKR normally and keep
heater power disconnected.

#### First-Time WSL USB Setup

WSL needs each ST-Link USB device shared through `usbipd-win`. Install it from
an Administrator PowerShell terminal:

```powershell
winget install --interactive --exact dorssel.usbipd-win
```

Restart PowerShell after installation. Keep a WSL terminal running while
attaching USB devices:

```powershell
wsl
```

In a second Administrator PowerShell terminal, list the connected devices:

```powershell
usbipd list
```

Find the row named `STM32 STLink` with VID:PID `0483:3748`. Share its current
bus ID:

```powershell
usbipd bind --busid=<BUSID>
```

`bind` requires Administrator privileges. The equals-sign form shown above is
preferred. If `usbipd` reports that the bus ID does not exist, unplug and
reconnect the probe, rerun `usbipd list`, and use its new bus ID.

Binding is normally persistent for that USB device. Each time Windows, WSL, or
the probe restarts, attach it again from PowerShell:

```powershell
usbipd attach --wsl --busid=<BUSID>
wsl lsusb
```

`wsl lsusb` should show a line containing `0483:3748`. While attached to WSL,
the probe is unavailable to native Windows programming tools.

Confirm that `usbipd list` reports the probe as `Attached`, not merely
`Shared`:

```text
BUSID  VID:PID    DEVICE       STATE
7-1    0483:3748  STM32 STLink Attached
```

If the state is only `Shared`, attach it before running OpenOCD:

```powershell
usbipd attach --wsl --busid=<BUSID>
```

#### Add Another ST-Link

Repeat the list, bind, and attach process for every additional probe:

```powershell
usbipd list
usbipd bind --busid=<SECOND_BUSID>
usbipd attach --wsl --busid=<SECOND_BUSID>
wsl lsusb
```

Bus IDs describe USB ports and can change after moving or reconnecting a
probe. Always use the current value from `usbipd list`.

Build and program from the project directory:

```powershell
wsl make clean all
wsl make flash
```

Successful output includes:

```text
Info : STLINK V2...
Info : Target voltage: ...
Info : [lpc17xx.cpu] Cortex-M3 ... processor detected
** Programming Finished **
** Verified OK **
** Resetting Target **
shutdown command invoked
```

`** Verified OK **` confirms that OpenOCD read the programmed image back
successfully. An initial program-counter value in the LPC ROM area, such as
`0x1fff0080`, can appear when OpenOCD first halts the target and is not by
itself a programming failure.

The `flash` target programs and verifies the ELF through:

```text
interface/stlink.cfg
target/lpc17xx.cfg
```

The ELF is linked at `0x00004000`; the target does not intentionally overwrite
the first 16 KiB factory BTT bootloader region.

When multiple ST-Links are attached, obtain their serial numbers with:

```powershell
wsl lsusb -v -d 0483:3748
```

Then select one for OpenOCD with:

```powershell
wsl make flash STLINK_SERIAL=<STLINK_SERIAL_NUMBER>
```

Detach the probe from WSL when finished:

```powershell
usbipd detach --busid=<BUSID>
```

Detaching does not remove the persistent binding. Use `usbipd attach` again
for the next programming session.

## Current Safety Behavior

The Phase 1 SKR firmware performs no heater or display GPIO initialization. It
masks interrupts and exercises only placeholder Mini 12864 service calls. This
is a build/boot foundation, not functional oven firmware.

## Documentation

- [.codex/design.md](.codex/design.md) - architecture and safety design.
- [docs/MIGRATION.md](docs/MIGRATION.md) - legacy/reference migration map.
- [docs/BENCH_TESTS.md](docs/BENCH_TESTS.md) - hardware verification checklist.
