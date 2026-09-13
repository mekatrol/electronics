# KiCad Custom Library Restore / Reinstall

This repository contains custom KiCad footprints and 3D models.

The repository copy is the canonical copy. KiCad should use the files directly from the repository rather than copying them into the Flatpak data directory.

## Repository layout

```text
hardware/kicad/footprints/
├── README.md
├── setup-kicad-libs.sh
├── teardown-kicad-libs.sh
├── library-names.conf
├── kicad-libs.py
├── ESP32_board.pretty/
├── Extra.pretty/
├── MCU_RaspberryPi_and_Boards.pretty/
├── Mekatrol_Footprints.pretty/
├── Segmentum.pretty/
├── Toponelec_TY308.pretty/
└── Toponelec.3dshapes/
```

## Footprint inventory

Each `.pretty` directory is a separate KiCad footprint library. The setup script preserves existing nicknames; fresh installations use the names in the manual configuration table below.

### ESP32_board

- [LOLIN_ESP32_S2_Mini_Socket](ESP32_board.pretty/LOLIN_ESP32_S2_Mini_Socket.kicad_mod)
- [Waveshare_ESP32_S3_C6_Zero_Hybrid](ESP32_board.pretty/Waveshare_ESP32_S3_C6_Zero_Hybrid.kicad_mod)
- [Waveshare_ESP32_S3_C6_Zero_THT](ESP32_board.pretty/Waveshare_ESP32_S3_C6_Zero_THT.kicad_mod)
- [Waveshare_ESP32_S3_Zero_SMD](ESP32_board.pretty/Waveshare_ESP32_S3_Zero_SMD.kicad_mod)
- [Waveshare_ESP32_S3_Zero_THT](ESP32_board.pretty/Waveshare_ESP32_S3_Zero_THT.kicad_mod)
- [Waveshare_ESP32_S3_Zero_Unspecified](ESP32_board.pretty/Waveshare_ESP32_S3_Zero_Unspecified.kicad_mod)

### Extra

- [0603_1206_combined](Extra.pretty/0603_1206_combined.kicad_mod)

### MCU_RaspberryPi_and_Boards

- [RPi_Pico_SMD_TH](MCU_RaspberryPi_and_Boards.pretty/RPi_Pico_SMD_TH.kicad_mod)
- [RPi_Pico_SMD_TH_no_swd](MCU_RaspberryPi_and_Boards.pretty/RPi_Pico_SMD_TH_no_swd.kicad_mod)

### Mekatrol_Footprints

- [HXY2102EI_SOT-323_Drain2](Mekatrol_Footprints.pretty/HXY2102EI_SOT-323_Drain2.kicad_mod)

### Segmentum

- [Raspberry_Pi_Header_FaceDown](Segmentum.pretty/Raspberry_Pi_Header_FaceDown.kicad_mod)

### Toponelec_TY308

- [Toponelec_TY308-2.54-02P-14-00AH_1x02_P2.54mm_Horizontal](Toponelec_TY308.pretty/Toponelec_TY308-2.54-02P-14-00AH_1x02_P2.54mm_Horizontal.kicad_mod)
- [Toponelec_TY308-2.54-03P-14-00AH_1x03_P2.54mm_Horizontal](Toponelec_TY308.pretty/Toponelec_TY308-2.54-03P-14-00AH_1x03_P2.54mm_Horizontal.kicad_mod)
- [Toponelec_TY308-2.54-04P-14-00AH_1x04_P2.54mm_Horizontal](Toponelec_TY308.pretty/Toponelec_TY308-2.54-04P-14-00AH_1x04_P2.54mm_Horizontal.kicad_mod)

## Toponelec TY308 parts

| LCSC | Part |
|---|---|
| `C2840316` | TY308-2.54-02P-14-00AH — 2 position |
| `C2840317` | TY308-2.54-03P-14-00AH — 3 position |
| `C2840318` | TY308-2.54-04P-14-00AH — 4 position |

Pitch: **2.54 mm**

The STEP models retain their colour/style information. The 3-way and 4-way body colours were adjusted to match the 2-way model.

---

# Reinstall procedure

After reinstalling KiCad:

1. Clone the `electronics` repository.
2. Close KiCad and run the setup script below.
3. Start KiCad.
4. Verify every library in the footprint inventory appears in the Footprint Editor.
5. Open one of the footprints in the 3D Viewer and confirm the model loads correctly.

The setup uses a KiCad path variable named:

```text
MY_KICAD_LIBS
```

The Toponelec footprints reference their bundled STEP files like this:

```text
${MY_KICAD_LIBS}/Toponelec.3dshapes/<model>.step
```

Other footprints reference external models that are not bundled here:

| Library | Model path variable | Referenced models |
|---|---|---|
| `ESP32_board` | `KICAD9_3DMODEL_DIR` | Waveshare ESP32-S3-Zero SMD, THT and pin-1-aligned STEP models under `Module.3dshapes` |
| `Extra` | `KICAD10_3DMODEL_DIR` | `Capacitor_SMD.3dshapes/C_0603_1608Metric.step` |
| `Mekatrol_Footprints` | `KICAD9_3DMODEL_DIR` | `Package_TO_SOT_SMD.3dshapes/SOT-323_SC-70.wrl` |
| `Segmentum` | `KISYS3DMOD` | `Module.3dshapes/Raspberry_Pi_Zero_Socketed_THT_FaceDown_MountingHoles.wrl` |

Configure these variables to model directories containing the referenced files if needed. The setup script only configures `MY_KICAD_LIBS`; it does not install external models or configure their variables. The LOLIN socket, S3/C6 THT and hybrid variants, and both Pico footprints have no model references.

No `/home/dad/...` absolute path is stored inside the committed footprint files.

---

# Setup script

Run [setup-kicad-libs.sh](setup-kicad-libs.sh) with Bash 4 or newer and Python 3 installed. It locates the footprint libraries relative to the script, so it works from any working directory.

Close KiCad before applying changes. From this directory:

```bash
./setup-kicad-libs.sh --dry-run
./setup-kicad-libs.sh
```

The default configuration directory matches this machine's KiCad 10 Flatpak installation:
`~/.var/app/org.kicad.KiCad/config/kicad/10.0`.
For another installation or version, specify its configuration directory:

```bash
./setup-kicad-libs.sh --config-dir ~/.config/kicad/10.0
```

The script discovers every `.pretty` directory and configures `MY_KICAD_LIBS`. It preserves existing library nicknames, descriptions, options, disabled/hidden flags, and unrelated settings. Preferred nicknames are Bash variables in [library-names.conf](library-names.conf). Edit the values in `LIBRARY_NAMES` to change them; the Toponelec entry currently uses `Connectors`. Newly added directories without an entry use their directory name without `.pretty`. Setup preserves an existing nickname until you tear down its registration.

Directory comparisons expand configured path variables and shell variables and resolve symlinks, `..`, and trailing slashes. Matching registrations use `${MY_KICAD_LIBS}/<library>.pretty`. Duplicate aliases for a repository directory are merged when their other settings agree; the preferred nickname wins, otherwise the first existing entry wins. Removed aliases are printed so any project references using those aliases can be updated. Conflicting settings or nicknames stop the script before it writes either configuration file. Unrelated duplicate directories are reported and left unchanged. Unresolved variables and relative global paths cannot be compared reliably; they are left unchanged, and nickname conflicts still stop the script.

Repeated runs make no changes once configured. Only changed files are written, using atomic replacement per file. Existing files receive a one-time `.backup-before-custom-libs` backup that subsequent runs preserve. `--dry-run` does not write files or create backups.

## Change names and reinstall

Close KiCad, then run these commands from this directory:

```bash
./teardown-kicad-libs.sh --dry-run
./teardown-kicad-libs.sh
# Edit the nickname values in library-names.conf, then:
./setup-kicad-libs.sh --dry-run
./setup-kicad-libs.sh
```

Both scripts accept `--config-dir`; use the same directory for teardown and setup. They share the implementation in `kicad-libs.py`.

Teardown removes all registrations pointing to the repository's current `.pretty` directories, including aliases, regardless of the nickname variables. You can therefore edit the names before or after teardown. It preserves unrelated libraries, footprint/model files, and `MY_KICAD_LIBS` (existing boards may still use it for 3D models). It creates a separate one-time `fp-lib-table.backup-before-custom-libs-teardown` backup and is idempotent. With no existing configuration, teardown creates nothing.

Reinstalling creates fresh registrations with the configured names and default options. Teardown removes any per-library descriptions, options and disabled/hidden flags along with those registrations; the backup retains them. Existing schematic and board footprint references are not renamed automatically.

## Manual KiCad equivalent

If the script ever stops working with a future KiCad version, configure these manually.

### Preferences → Configure Paths

Add:

```text
Name: MY_KICAD_LIBS
Path: <repo>/hardware/kicad/footprints
```

For the current machine that is:

```text
/home/dad/repos/electronics/hardware/kicad/footprints
```

This absolute path is local KiCad configuration only. It is not stored inside the committed footprints.

### Preferences → Manage Footprint Libraries → Global Libraries

Add each library below with type `KiCad`:

| Nickname | Library path |
|---|---|
| `ESP32_board` | `${MY_KICAD_LIBS}/ESP32_board.pretty` |
| `Extra` | `${MY_KICAD_LIBS}/Extra.pretty` |
| `MCU_RaspberryPi_and_Boards` | `${MY_KICAD_LIBS}/MCU_RaspberryPi_and_Boards.pretty` |
| `Mekatrol_Footprints` | `${MY_KICAD_LIBS}/Mekatrol_Footprints.pretty` |
| `Segmentum` | `${MY_KICAD_LIBS}/Segmentum.pretty` |
| `Connectors` | `${MY_KICAD_LIBS}/Toponelec_TY308.pretty` |

## Verification

Check that the committed footprint files contain no machine-specific paths:

```bash
cd ~/repos/electronics

grep -R --include='*.kicad_mod' '/home/dad' hardware/kicad/footprints \
    && echo "WARNING: machine-specific path found" \
    || echo "GOOD: no /home/dad paths found"
```

Check the portable 3D model references:

```bash
grep -R 'MY_KICAD_LIBS' hardware/kicad/footprints/Toponelec_TY308.pretty
```

Expected form:

```text
${MY_KICAD_LIBS}/Toponelec.3dshapes/C2840316_....step
```

## Important

Do not treat this Flatpak directory as the master library:

```text
~/.var/app/org.kicad.KiCad/data/kicad/10.0/3rdparty/
```

The Git repository is the master copy. Make footprint/model changes in the repository and commit them.
