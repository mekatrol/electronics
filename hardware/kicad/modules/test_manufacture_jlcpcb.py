import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from manufacture_jlcpcb import manufacture, project_board


class ManufactureJlcpcbTests(unittest.TestCase):
    def test_requires_board_named_after_project_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "tiny-board"
            project.mkdir()
            with self.assertRaisesRegex(FileNotFoundError, "tiny-board.kicad_pcb"):
                project_board(project)

    def test_runs_panelizer_then_exporter_into_manufacture(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "tiny-board"
            project.mkdir()
            board = project / "tiny-board.kicad_pcb"
            board.write_text("(kicad_pcb)")

            with patch("manufacture_jlcpcb.run") as mocked_run:
                output = manufacture(project, 3, 2, "/opt/kicad-cli")

            self.assertEqual(output, project / "manufacture")
            self.assertEqual(mocked_run.call_count, 2)
            panel_command = mocked_run.call_args_list[0].args[0]
            export_command = mocked_run.call_args_list[1].args[0]
            panel = project / "manufacture/tiny-board_routed_panel_3x2.kicad_pcb"
            self.assertIn(str(panel), panel_command)
            self.assertIn("--force", panel_command)
            self.assertEqual(export_command[-4:-2], ["--output-dir", str(output)])
            self.assertEqual(export_command[-2:], ["--kicad-cli", "/opt/kicad-cli"])


if __name__ == "__main__":
    unittest.main()
