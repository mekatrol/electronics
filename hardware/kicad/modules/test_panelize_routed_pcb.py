import unittest
from pathlib import Path

from panelize_pcb import find_fiducial_library_file, load_fiducial_template, parse_sexpr
from panelize_routed_pcb import build_routed_panel


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "power_rail_mosfet_switch" / "power_rail_mosfet_switch.kicad_pcb"


class RoutedPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = parse_sexpr(SAMPLE.read_text(encoding="utf-8"))
        cls.fiducial = load_fiducial_template(find_fiducial_library_file())

    def test_sample_panel_geometry(self):
        panel, bounds = build_routed_panel(
            self.source, 2, 2, 2.0, 5.0, 5.0, 0.6, 0.25, self.fiducial
        )
        self.assertEqual(bounds.width, 52.0)
        self.assertEqual(bounds.height, 32.0)
        text = str(panel)
        self.assertIn("PFID1", text)
        self.assertIn("PFID4", text)
        self.assertIn("TH1", text)
        self.assertIn("TH4", text)
        self.assertIn("PanelToolingHole_2mm", text)
        self.assertIn("MouseBite", text)
        self.assertIn("/VOUT@X2Y2", text)

    def test_rejects_undersized_route_gap(self):
        with self.assertRaises(ValueError):
            build_routed_panel(self.source, 2, 2, 1.9, 5.0, 5.0, 0.6, 0.25, self.fiducial)


if __name__ == "__main__":
    unittest.main()
