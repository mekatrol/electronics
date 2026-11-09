import tempfile
import unittest
import zipfile
import csv
from pathlib import Path
from unittest.mock import patch

from generate_jlcpcb_panel import (
    archive_panel_files,
    default_output_directory,
    export_panel_drills,
    remove_stale_panel_drill_files,
    validate_panel_name,
)
from generate_jlcpcb import validate_assembly_references, write_board_bom


class PanelGeneratorTests(unittest.TestCase):
    def test_default_output_uses_one_manufacture_directory(self):
        self.assertEqual(
            default_output_directory(Path("project/panel.kicad_pcb")),
            Path("project/manufacture"),
        )
        self.assertEqual(
            default_output_directory(Path("project/manufacture/panel.kicad_pcb")),
            Path("project/manufacture"),
        )

    def test_writes_panel_bom_from_embedded_footprint_properties(self):
        board_text = """(kicad_pcb
          (footprint "Diode_SMD:D_SOD-123"
            (property "Reference" "D1_X1Y1")
            (property "Value" "1N4148W")
            (property "LCSC Part #" "C81598"))
          (footprint "Diode_SMD:D_SOD-123"
            (property "Reference" "D1_X2Y1")
            (property "Value" "1N4148W")
            (property "LCSC Part #" "C81598"))
          (footprint "MountingHole:MountingHole_2mm"
            (property "Reference" "H1")
            (property "Value" "MountingHole")
            (attr board_only exclude_from_bom)))"""
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            board = directory / "panel.kicad_pcb"
            bom = directory / "panel-bom.csv"
            board.write_text(board_text)

            references = write_board_bom(board, bom)

            self.assertEqual(references, {"D1_X1Y1", "D1_X2Y1"})
            with bom.open(newline="") as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(
                rows,
                [
                    ["Comment", "Designator", "Footprint", "LCSC Part #"],
                    ["1N4148W", "D1_X1Y1,D1_X2Y1", "D_SOD-123", "C81598"],
                ],
            )

    def test_requires_every_bom_reference_in_positions(self):
        validate_assembly_references({"D1_X1Y1"}, {"D1_X1Y1", "J1_X1Y1"})
        with self.assertRaisesRegex(ValueError, "D1_X2Y1"):
            validate_assembly_references(
                {"D1_X1Y1", "D1_X2Y1"}, {"D1_X1Y1"}
            )

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
            (directory / "other-panel-Edge_Cuts.gm1").write_text("other")
            archive = directory / "panel-gerbers.zip"
            archive_panel_files(directory, archive, "panel")
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
