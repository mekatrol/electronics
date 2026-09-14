import tempfile
import unittest
import zipfile
from pathlib import Path

from generate_jlcpcb_panel import archive_panel_files, validate_panel_name


class PanelGeneratorTests(unittest.TestCase):
    def test_requires_panel_filename(self):
        with self.assertRaises(ValueError):
            validate_panel_name(Path("ordinary_board.kicad_pcb"))
        validate_panel_name(Path("ordinary_board_routed_panel_2x2.kicad_pcb"))

    def test_archive_includes_user_drawings_and_drill(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "panel-User_Drawings.gbr").write_text("score")
            (directory / "panel-Edge_Cuts.gm1").write_text("route")
            (directory / "panel.drl").write_text("drill")
            archive = directory / "panel-gerbers.zip"
            archive_panel_files(directory, archive)
            with zipfile.ZipFile(archive) as bundle:
                self.assertEqual(
                    set(bundle.namelist()),
                    {"panel-User_Drawings.gbr", "panel-Edge_Cuts.gm1", "panel.drl"},
                )


if __name__ == "__main__":
    unittest.main()
