import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from generate_jlcpcb_panel import (
    archive_panel_files,
    export_panel_drills,
    remove_stale_panel_drill_files,
    validate_panel_name,
)


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

    def test_removes_only_stale_drills_for_this_panel(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            stale = directory / "panel.drl"
            separate = directory / "panel-PTH.drl"
            unrelated = directory / "other-panel.drl"
            for path in (stale, separate, unrelated):
                path.write_text("drill")

            remove_stale_panel_drill_files(directory, "panel")

            self.assertFalse(stale.exists())
            self.assertFalse(separate.exists())
            self.assertTrue(unrelated.exists())

    def test_exports_separate_plated_and_non_plated_drills(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            board = directory / "panel.kicad_pcb"
            with patch("generate_jlcpcb_panel.run") as mocked_run:
                export_panel_drills(board, ["kicad-cli"], directory)

            command = mocked_run.call_args.args[0]
            self.assertIn("--excellon-separate-th", command)
            self.assertEqual(command[-1], str(board))


if __name__ == "__main__":
    unittest.main()
