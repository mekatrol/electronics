import unittest
from pathlib import Path

from kicad_discovery import find_fiducial_library_file
from panelize_routed_pcb import (
    Bounds,
    build_routed_panel,
    load_fiducial_template,
    parse_sexpr,
    validation_summary,
)

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "power_rail_mosfet_switch" / "power_rail_mosfet_switch.kicad_pcb"


class RoutedPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = parse_sexpr(SAMPLE.read_text(encoding="utf-8"))
        cls.fiducial = load_fiducial_template(find_fiducial_library_file())

    def test_sample_panel_geometry(self):
        panel, bounds = build_routed_panel(
            self.source, 2, 2, 2.0, 5.0, 5.0, 0.6, 0.4, self.fiducial
        )
        self.assertEqual(bounds.width, 56.0)
        self.assertEqual(bounds.height, 36.0)
        self.assertEqual(bounds.left, 120.5)
        self.assertEqual(bounds.top, 87.0)
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
            build_routed_panel(
                self.source, 2, 2, 1.9, 5.0, 5.0, 0.6, 0.4, self.fiducial
            )

    def test_rejects_obsolete_mouse_bite_clearance(self):
        with self.assertRaises(ValueError):
            build_routed_panel(
                self.source, 2, 2, 2.0, 5.0, 5.0, 0.6, 0.25, self.fiducial
            )

    def test_validation_summary_is_self_contained(self):
        summary = validation_summary(
            source_path=Path("source.kicad_pcb"),
            output_path=Path("source_routed_panel_2x2.kicad_pcb"),
            source_bounds=Bounds(0, 0, 20, 10),
            panel_bounds=Bounds(0, 0, 52, 32),
            count_x=2,
            count_y=2,
            gap=2.0,
            rail=5.0,
            tab_width=5.0,
            bite_diameter=0.6,
            bite_clearance=0.4,
            fiducial_path=Path("Fiducial_1mm_Mask2mm.kicad_mod"),
            drc_checked=True,
        )
        self.assertIn("2 columns x 2 rows = 4 identical PCBs", summary)
        self.assertIn("Breakaway tabs: 8 total", summary)
        self.assertIn("Mouse bites: 5 holes/tab, 40 holes total", summary)
        self.assertIn("NPTH mouse bites do not require it", summary)
        self.assertIn("KiCad panel DRC: PASS", summary)
        self.assertIn("Source-file integrity: PASS", summary)


if __name__ == "__main__":
    unittest.main()
