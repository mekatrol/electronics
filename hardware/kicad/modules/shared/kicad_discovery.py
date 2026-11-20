"""Locate KiCad executables and standard libraries across installations."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

FIDUCIAL_RELATIVE_PATH = Path("Fiducial.pretty/Fiducial_1mm_Mask2mm.kicad_mod")
FLATPAK_APP_ID = "org.kicad.KiCad"
FLATPAK_FOOTPRINTS_ID = "org.kicad.KiCad.Library.Footprints"


def _flatpak_runtime_locations() -> list[Path]:
    """Return installed footprint runtime roots reported by Flatpak."""
    flatpak = shutil.which("flatpak")
    if not flatpak:
        return []
    locations: list[Path] = []
    for scope in ("--user", "--system"):
        completed = subprocess.run(
            [
                flatpak,
                scope,
                "info",
                "--show-location",
                FLATPAK_FOOTPRINTS_ID,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            locations.append(Path(completed.stdout.strip()))
    return locations


def _flatpak_active_runtime_locations() -> list[Path]:
    """Find active deployments if Flatpak itself cannot be queried."""
    roots = [Path.home() / ".local/share/flatpak", Path("/var/lib/flatpak")]
    locations: list[Path] = []
    for root in roots:
        runtime = root / "runtime" / FLATPAK_FOOTPRINTS_ID
        if runtime.is_dir():
            locations.extend(runtime.glob("*/*/active"))
    return locations


def find_fiducial_library_file(explicit: Path | None = None) -> Path:
    """Locate KiCad's standard 1 mm copper / 2 mm mask fiducial."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    footprint_dir = os.environ.get("KICAD10_FOOTPRINT_DIR")
    if footprint_dir:
        candidates.append(Path(footprint_dir) / FIDUCIAL_RELATIVE_PATH)
    candidates.extend(
        [
            Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
            / FIDUCIAL_RELATIVE_PATH,
            Path("/usr/share/kicad/footprints") / FIDUCIAL_RELATIVE_PATH,
            Path("/usr/local/share/kicad/footprints") / FIDUCIAL_RELATIVE_PATH,
            Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")
            / FIDUCIAL_RELATIVE_PATH,
        ]
    )
    for location in _flatpak_runtime_locations() + _flatpak_active_runtime_locations():
        candidates.append(location / "files/footprints" / FIDUCIAL_RELATIVE_PATH)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "KiCad 10 library footprint Fiducial:Fiducial_1mm_Mask2mm was not found; "
        "pass --fiducial-footprint or set KICAD10_FOOTPRINT_DIR"
    )


def find_kicad_cli(explicit: str | None = None) -> list[str] | None:
    """Return the command prefix for a native or Flatpak KiCad CLI."""
    if explicit:
        return [explicit]
    native = shutil.which("kicad-cli")
    if native:
        return [native]
    windows = Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
    if windows.is_file():
        return [str(windows)]
    flatpak = shutil.which("flatpak")
    if flatpak:
        completed = subprocess.run(
            [flatpak, "info", FLATPAK_APP_ID],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if completed.returncode == 0:
            return [flatpak, "run", "--command=kicad-cli", FLATPAK_APP_ID]
    return None
