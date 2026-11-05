import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kicad_discovery import FIDUCIAL_RELATIVE_PATH, find_fiducial_library_file


class KiCadDiscoveryTests(unittest.TestCase):
    def test_environment_override(self):
        with tempfile.TemporaryDirectory() as directory:
            footprint = Path(directory) / FIDUCIAL_RELATIVE_PATH
            footprint.parent.mkdir(parents=True)
            footprint.touch()
            with patch.dict(os.environ, {"KICAD10_FOOTPRINT_DIR": directory}):
                self.assertEqual(find_fiducial_library_file(), footprint.resolve())

    def test_flatpak_runtime_location(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            footprint = runtime / "files/footprints" / FIDUCIAL_RELATIVE_PATH
            footprint.parent.mkdir(parents=True)
            footprint.touch()
            with patch.dict(os.environ, {}, clear=True), patch(
                "kicad_discovery._flatpak_runtime_locations", return_value=[runtime]
            ), patch(
                "kicad_discovery._flatpak_active_runtime_locations", return_value=[]
            ):
                self.assertEqual(find_fiducial_library_file(), footprint.resolve())


if __name__ == "__main__":
    unittest.main()
