# KiCad Custom Library Restore / Reinstall

This repository contains custom KiCad footprints and 3D models.

The repository copy is the canonical copy. KiCad should use the files directly from the repository rather than copying them into the Flatpak data directory.

## Repository layout

```text
hardware/kicad/footprints/
├── README.md
├── Toponelec_TY308.pretty/
└── Toponelec.3dshapes/
```

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
2. Run the setup script below.
3. Start KiCad.
4. Verify the library appears as `Toponelec_TY308`.
5. Open one of the footprints in the 3D Viewer and confirm the model loads correctly.

The setup uses a KiCad path variable named:

```text
MY_KICAD_LIBS
```

The footprints reference their STEP files like this:

```text
${MY_KICAD_LIBS}/Toponelec.3dshapes/<model>.step
```

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
FP_LIB="${LIB_ROOT}/Toponelec_TY308.pretty"

KICAD_CONFIG="${HOME}/.var/app/org.kicad.KiCad/config/kicad/10.0"
FP_TABLE="${KICAD_CONFIG}/fp-lib-table"
COMMON_CONFIG="${KICAD_CONFIG}/kicad_common.json"

echo "KiCad custom library setup"
echo
echo "Repository root : ${REPO_ROOT}"
echo "Library root    : ${LIB_ROOT}"
echo "Footprint lib   : ${FP_LIB}"
echo

if [[ ! -d "${FP_LIB}" ]]; then
    echo "ERROR: Footprint library not found:"
    echo "  ${FP_LIB}"
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

if grep -R -q '/home/dad' "${FP_LIB}" --include='*.kicad_mod'; then
    echo "ERROR: Absolute /home/dad path found inside footprint files."
    echo "Fix these before continuing:"
    grep -R -n '/home/dad' "${FP_LIB}" --include='*.kicad_mod'
    exit 1
fi

if ! grep -R -q '\${MY_KICAD_LIBS}/Toponelec.3dshapes' "${FP_LIB}" --include='*.kicad_mod'; then
    echo "WARNING: Expected MY_KICAD_LIBS model paths were not found."
    echo "Current model references:"
    grep -R -n '(model ' "${FP_LIB}" --include='*.kicad_mod' || true
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
# Register the footprint library.
# ----------------------------------------------------------------------

if [[ ! -f "${FP_TABLE}" ]]; then
    cat > "${FP_TABLE}" <<'EOF'
(fp_lib_table
)
EOF
fi

cp -a "${FP_TABLE}" "${FP_TABLE}.backup-before-toponelec"

python3 - "${FP_TABLE}" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()

nickname = "Toponelec_TY308"
entry = '  (lib (name "Toponelec_TY308")(type "KiCad")(uri "${MY_KICAD_LIBS}/Toponelec_TY308.pretty")(options "")(descr "Toponelec TY308 2.54mm terminal blocks"))'

# Remove existing Toponelec_TY308 entries so we do not create duplicates.
lines = [
    line for line in text.splitlines()
    if '(name "Toponelec_TY308")' not in line
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
        lines.insert(i, entry)
        break
else:
    raise SystemExit("ERROR: Could not find closing ')' in fp-lib-table")

path.write_text("\n".join(lines) + "\n")

print("Registered footprint library: Toponelec_TY308")
PY

echo
echo "Setup complete."
echo
echo "Verify with:"
echo
echo "  grep -R 'MY_KICAD_LIBS' \"${FP_LIB}\"/*.kicad_mod"
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

Add:

```text
${MY_KICAD_LIBS}/Toponelec_TY308.pretty
```

Nickname:

```text
Toponelec_TY308
```

## Verification

Check that the committed footprint files contain no machine-specific paths:

```bash
cd ~/repos/electronics

grep -R '/home/dad' hardware/kicad/footprints \
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