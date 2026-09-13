# KiCad Custom Library Restore / Reinstall

This repository contains custom KiCad footprints and 3D models.

The repository copy is the canonical copy. KiCad should use the files directly from the repository rather than copying them into the Flatpak data directory.

## Repository layout

```text
hardware/kicad/footprints/
├── README.md
├── ESP32_board.pretty/
├── Extra.pretty/
├── MCU_RaspberryPi_and_Boards.pretty/
├── Mekatrol_Footprints.pretty/
├── Segmentum.pretty/
├── Toponelec_TY308.pretty/
└── Toponelec.3dshapes/
```

## Footprint inventory

Each `.pretty` directory is a separate KiCad footprint library. Use its directory name without `.pretty` as the library nickname.

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

Save this as `setup-kicad-libs.sh`, or copy/paste it into a terminal.

```bash
#!/usr/bin/env bash
set -euo pipefail

# Change this only if the electronics repository is cloned somewhere else.
REPO_ROOT="${HOME}/repos/electronics"

LIB_ROOT="${REPO_ROOT}/hardware/kicad/footprints"
shopt -s nullglob
FP_LIBS=("${LIB_ROOT}"/*.pretty)

KICAD_CONFIG="${HOME}/.var/app/org.kicad.KiCad/config/kicad/10.0"
FP_TABLE="${KICAD_CONFIG}/fp-lib-table"
COMMON_CONFIG="${KICAD_CONFIG}/kicad_common.json"

echo "KiCad custom library setup"
echo
echo "Repository root : ${REPO_ROOT}"
echo "Library root    : ${LIB_ROOT}"
echo "Footprint libs  : ${#FP_LIBS[@]}"
echo

if (( ${#FP_LIBS[@]} == 0 )); then
    echo "ERROR: No .pretty footprint libraries found:"
    echo "  ${LIB_ROOT}"
    echo
    echo "Clone the electronics repository first, or edit REPO_ROOT in this script."
    exit 1
fi

if [[ ! -d "${LIB_ROOT}/Toponelec.3dshapes" ]]; then
    echo "ERROR: 3D model directory not found:"
    echo "  ${LIB_ROOT}/Toponelec.3dshapes"
    exit 1
fi

mkdir -p "${KICAD_CONFIG}"

echo "Checking footprint model paths..."

if grep -R -q '/home/dad' "${LIB_ROOT}" --include='*.kicad_mod'; then
    echo "ERROR: Absolute /home/dad path found inside footprint files."
    echo "Fix these before continuing:"
    grep -R -n '/home/dad' "${LIB_ROOT}" --include='*.kicad_mod'
    exit 1
fi

if ! grep -R -q '\${MY_KICAD_LIBS}/Toponelec.3dshapes' "${LIB_ROOT}" --include='*.kicad_mod'; then
    echo "WARNING: Expected MY_KICAD_LIBS model paths were not found."
    echo "Current model references:"
    grep -R -n '(model ' "${LIB_ROOT}" --include='*.kicad_mod' || true
fi

echo "Footprint files look portable."
echo

# ----------------------------------------------------------------------
# Configure MY_KICAD_LIBS in KiCad's common configuration.
#
# KiCad stores path variables in kicad_common.json. We use Python here so
# the JSON is edited safely rather than with sed.
# ----------------------------------------------------------------------

python3 - "${COMMON_CONFIG}" "${LIB_ROOT}" <<'PY'
import json
import sys
from pathlib import Path

cfg_path = Path(sys.argv[1])
lib_root = sys.argv[2]

if cfg_path.exists():
    try:
        data = json.loads(cfg_path.read_text())
    except Exception as exc:
        raise SystemExit(f"ERROR: Could not parse {cfg_path}: {exc}")
else:
    data = {}

env = data.setdefault("environment", {})
vars_ = env.setdefault("vars", {})
vars_["MY_KICAD_LIBS"] = lib_root

cfg_path.parent.mkdir(parents=True, exist_ok=True)
cfg_path.write_text(json.dumps(data, indent=2) + "\n")

print(f"Configured MY_KICAD_LIBS = {lib_root}")
PY

# ----------------------------------------------------------------------
# Register every .pretty footprint library in the repository.
# ----------------------------------------------------------------------

if [[ ! -f "${FP_TABLE}" ]]; then
    cat > "${FP_TABLE}" <<'EOF'
(fp_lib_table
)
EOF
fi

cp -a "${FP_TABLE}" "${FP_TABLE}.backup-before-custom-libs"

python3 - "${FP_TABLE}" "${LIB_ROOT}" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()

libraries = sorted(Path(sys.argv[2]).glob("*.pretty"))
nicknames = {library.stem for library in libraries}
entries = [
    f'  (lib (name "{library.stem}")(type "KiCad")'
    f'(uri "${{MY_KICAD_LIBS}}/{library.name}")(options "")(descr ""))'
    for library in libraries
]

# Replace existing entries for these libraries to avoid duplicates.
lines = [
    line for line in text.splitlines()
    if not any(f'(name "{nickname}")' in line for nickname in nicknames)
]

# Also remove the old accidental alias if it pointed to the same library.
lines = [
    line for line in lines
    if not (
        '(name "Terminal Blocks")' in line
        and 'Toponelec_TY308.pretty' in line
    )
]

# Insert before final closing parenthesis.
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == ")":
        lines[i:i] = entries
        break
else:
    raise SystemExit("ERROR: Could not find closing ')' in fp-lib-table")

path.write_text("\n".join(lines) + "\n")

for library in libraries:
    print(f"Registered footprint library: {library.stem}")
PY

echo
echo "Setup complete."
echo
echo "Verify with:"
echo
echo "  grep -R '(model ' \"${LIB_ROOT}\" --include='*.kicad_mod'"
echo
echo "Then start KiCad and open a Toponelec footprint in the 3D Viewer."
```

## Make the script executable

```bash
chmod +x setup-kicad-libs.sh
```

Then run:

```bash
./setup-kicad-libs.sh
```

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
| `Toponelec_TY308` | `${MY_KICAD_LIBS}/Toponelec_TY308.pretty` |

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