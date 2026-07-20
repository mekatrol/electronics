# Home Automation Electronics

This repository contains the electronics, embedded firmware, support software, and reference material for a collection of home-automation and workshop projects. Hardware designs are primarily created with KiCad, firmware targets Raspberry Pi Pico/Pico W and MicroPython-compatible boards, and the host-side controller tools are written in .NET, C++, and Python.

## Repository layout

```text
.
├── firmware/              Embedded C/C++, Arduino, and MicroPython projects
├── hardware/              KiCad projects, libraries, footprints, and 3D models
├── software/              Desktop, command-line, monitoring, and test tools
├── irrigation_wiring.txt  Irrigation wiring notes
└── README.md              Repository overview
```

Generated build output, IDE state, KiCad backup/session files, and caches are excluded by `.gitignore`.

## Hardware projects

Each board directory contains its KiCad project (`.kicad_pro`), schematic (`.kicad_sch`), and PCB layout (`.kicad_pcb`) where applicable. Some projects also include manufacturing Gerber archives or exported 3D models.

| Project | Location | Description |
| --- | --- | --- |
| Basic controller | `hardware/basic_controller/` | General-purpose controller board with a hierarchical CPU schematic. |
| IW-8 expansion | `hardware/iw-8-expansion/` | Expansion board with separate power and output schematic sheets. |
| LED controller | `hardware/led_controller/` | Controller board for LED loads. |
| Output board | `hardware/output_board/` | Standalone output-control board. |
| Pico controller | `hardware/pico/controller/` | Raspberry Pi Pico-based controller with CPU, input, output, power, and control-panel designs. |
| Pico IW-8 controller | `hardware/pico/iw-8-controller/` | Pico-based IW-8 controller with input, output, power, and CPU sheets. |
| Pico output controller | `hardware/pico/output_controller/` | Pico output controller with two output banks and supporting input and power circuitry. |
| RS-485 board | `hardware/rs485_board/` | RS-485 interface board. |
| Temperature controller | `hardware/temperature_controller/` | Temperature-control PCB and exported 3D model. |
| Triac/FET module | `hardware/triac_fet_module/` | Mains-load switching module using an optically isolated zero-cross triac, with KiCad design rules and Gerber/CNC manufacturing files. |
| WS2812 segment | `hardware/ws2812_segment/` | PCB segment for WS2812 addressable LEDs. |

Shared hardware resources include:

- `hardware/kicad/` — the canonical KiCad resource tree, containing symbols, footprints, Python modules, and action plugins.
- `hardware/fusion360_modules/` — Fusion 360 helper scripts.
- `hardware/pcb-checklist.xlsx` — PCB design/review checklist.

Open a hardware project by loading its `.kicad_pro` file in KiCad. Keep the repository layout intact so that relative library and 3D-model references continue to resolve.

## Firmware projects

### Raspberry Pi Pico SDK

The root `firmware/CMakeLists.txt` configures a Pico W build using CMake and the Raspberry Pi Pico SDK. It currently includes these targets:

| Target | Location | Purpose |
| --- | --- | --- |
| `iw_8_controller` | `firmware/iw_8_controller/` | Main C++ IW-8 controller firmware, including messaging, flows, storage, RTC, and PIO-driven outputs. |
| `memory_management_testing` | `firmware/memory_management_testing/` | Test target for the custom memory-management implementation. |
| `uart_testing` | `firmware/uart_testing/` | Test target for serial/UART communication. |

Reusable Pico code lives in `firmware/common/` and covers communication, memory management, PIO, RTC, flash storage, CRC, I2C, inter-core synchronization, and general utilities.

To configure and build the Pico SDK targets:

```sh
export PICO_SDK_PATH=/path/to/pico-sdk
cmake -S firmware -B firmware/build
cmake --build firmware/build
```

The project requires Pico SDK 1.3.0 or later and uses C11 and C++17.

### MicroPython and Python device firmware

| Project | Location | Description |
| --- | --- | --- |
| Garage monitor | `firmware/garage_monitor/` | Networked garage monitor with mmWave sensing and NeoPixel support. |
| IW-8 controller prototype | `firmware/iw_8_controller_python/` | Python implementation/prototype of the IW-8 controller. |
| mmWave sensor | `firmware/mmwave_sensor/` | Networked mmWave sensor firmware with MQTT and NeoPixel support. |
| Simple controller | `firmware/simple_controller/` | Small networked controller with sensor and NeoPixel helpers. |
| Wall sensor | `firmware/wall_sensor/` | Wall-sensor firmware with WLAN, I2C, and NeoPixel helpers. |

Device-specific `config.py` files hold each firmware project's configuration. Review these before deploying to a board and avoid committing private credentials.

### Arduino projects

| Project | Location | Description |
| --- | --- | --- |
| Fish feeder | `firmware/fish_feeder/` | Fish-feeder control using a stepper motor; Arduino and Python implementations are present. |
| Reflow controller | `firmware/reflow_controller/` | Reflow-oven controller with temperature sensing, PID control, stages, plotting, learning, and LCD/UI code. |

### Development and protocol tools

- `firmware/bluetooth_test/` contains Python Bluetooth client and server test programs.
- `firmware/rp2040_registers.docx` is an RP2040 register reference.
- `firmware/common/communication/` defines the device communication and message protocol shared by firmware components.

## Support software

### .NET controller tools

`software/Controller/Controller.sln` is a Visual Studio/.NET 6 solution containing:

| Project | Description |
| --- | --- |
| `HomeAutomation.Common` | Shared configuration, dependency-injection, logging, serial communication, protocol, and message implementations. |
| `HomeAutomation.ControllerCLI` | Command-line controller application built on the common library. |
| `HomeAutomation.Monitor` | Configurable monitoring process; includes application settings and a service definition. |
| `HomeAutomation.Terminal` | Serial terminal utility. |

Build the solution with:

```sh
dotnet build software/Controller/Controller.sln
```

### Other tools

- `software/CodeTestHarness/` is a Visual C++ test harness for native code experiments.
- `software/mmwave_sensor/` is a Python serial/data-analysis utility using `pyserial` and `numpy`.

Install the Python utility dependencies with:

```sh
python -m pip install -r software/mmwave_sensor/requirements.txt
```

## Reference material

- `irrigation_wiring.txt` documents irrigation-system wiring.
- Project-specific VS Code configuration and workspace files are retained where they provide useful build, debugging, or MicroPython tooling settings.
- Fabrication ZIP, Gerber, drill, and CNC files are retained where they represent deliberate manufacturing outputs; automatic KiCad backups, local history, lock files, and session state are ignored.

## Working in this repository

- Preserve the existing directory structure because firmware, KiCad libraries, and 3D models may use relative paths.
- Do not commit generated `build`, `bin`, `obj`, cache, or automatic backup directories.
- Review hardware changes with `hardware/pcb-checklist.xlsx` before ordering boards.
- Treat device configuration and application settings as potentially environment-specific and check them for secrets before committing.
