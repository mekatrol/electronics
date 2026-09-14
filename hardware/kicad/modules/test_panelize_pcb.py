import hashlib
import unittest
from pathlib import Path

from panelize_pcb import build_panel, dump_sexpr, edge_bounds, parse_sexpr


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "power_rail_mosfet_switch" / "power_rail_mosfet_switch.kicad_pcb"


class PanelizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_text = SAMPLE.read_text(encoding="utf-8")
        cls.source = parse_sexpr(cls.source_text)

    def test_sample_bounds(self):
        bounds = edge_bounds(self.source)
        self.assertAlmostEqual(bounds.width, 20.0)
        self.assertAlmostEqual(bounds.height, 10.0)

    def test_panel_size_fiducials_and_outline(self):
        panel, bounds = build_panel(self.source, 3, 2, 5.0, 2.0)
        text = dump_sexpr(panel)
        self.assertAlmostEqual(bounds.width, 74.0)
        self.assertAlmostEqual(bounds.height, 32.0)
        self.assertEqual(text.count('"PFID'), 3)
        self.assertEqual(text.count('(layer "Edge.Cuts")'), 4)
        self.assertEqual(text.count('(layer "Dwgs.User")'), 10)
        self.assertIn('(net "/VOUT@X1Y1")', text)
        self.assertIn('(net "/VOUT@X3Y2")', text)
        self.assertNotIn('(net "/VOUT")', text)
        parse_sexpr(text)

    def test_build_does_not_change_source(self):
        before = hashlib.sha256(dump_sexpr(self.source).encode()).digest()
        build_panel(self.source, 2, 2, 5.0)
        after = hashlib.sha256(dump_sexpr(self.source).encode()).digest()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
