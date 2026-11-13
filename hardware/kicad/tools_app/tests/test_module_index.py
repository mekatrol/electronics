"""Validate the executable allow-list used by the KiCad tools application."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema

APP_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = APP_DIR.parent
INDEX_PATH = APP_DIR / "module_index.json"
SCHEMA_PATH = APP_DIR / "schemas" / "module_index.schema.json"
DISALLOWED_PARTS = {"legacy", "tests"}
SUPPORT_MODULES = {
    "kicad_discovery.py",
    "kicad_ipc.py",
    "kicad_netlist_reader.py",
    "kicad_utils.py",
    "xlsx_reader.py",
}


class ModuleIndexTests(unittest.TestCase):
    """Enforce schema, path-safety, and command-construction invariants."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load the authoritative index and schema once for this test class."""
        cls.index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_index_conforms_to_schema(self) -> None:
        """Reject index fields that the backend cannot interpret safely."""
        jsonschema.Draft202012Validator(self.schema).validate(self.index)

    def test_module_ids_are_unique(self) -> None:
        """Ensure stable IDs identify exactly one executable definition."""
        identifiers = [module["id"] for module in self.index["modules"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_scripts_exist_inside_modules_directory(self) -> None:
        """Resolve each static path and reject missing or escaping scripts."""
        modules_root = (REPOSITORY_ROOT / "modules").resolve()
        for module in self.index["modules"]:
            script = (APP_DIR / module["script"]).resolve()
            with self.subTest(module=module["id"]):
                self.assertTrue(script.is_relative_to(modules_root))
                self.assertTrue(script.is_file())
                self.assertEqual(script.suffix, ".py")

    def test_tests_legacy_and_support_modules_are_not_exposed(self) -> None:
        """Keep non-entry-point Python code out of the executable allow-list."""
        for module in self.index["modules"]:
            script = Path(module["script"])
            with self.subTest(module=module["id"]):
                self.assertFalse(script.name.startswith("test_"))
                self.assertTrue(DISALLOWED_PARTS.isdisjoint(script.parts))
                self.assertNotIn(script.name, SUPPORT_MODULES)

    def test_parameter_names_and_flags_are_unique(self) -> None:
        """Prevent ambiguous request fields or duplicate CLI switches."""
        for module in self.index["modules"]:
            names = [parameter["name"] for parameter in module["parameters"]]
            flags = [
                parameter["flag"]
                for parameter in module["parameters"]
                if "flag" in parameter
            ]
            with self.subTest(module=module["id"]):
                self.assertEqual(len(names), len(set(names)))
                self.assertEqual(len(flags), len(set(flags)))

    def test_parameter_defaults_satisfy_constraints(self) -> None:
        """Check defaults against numeric, enum, and required-value metadata."""
        for module in self.index["modules"]:
            for parameter in module["parameters"]:
                default = parameter["default"]
                with self.subTest(module=module["id"], parameter=parameter["name"]):
                    if default is None:
                        continue
                    if "minimum" in parameter:
                        self.assertGreaterEqual(default, parameter["minimum"])
                    if "maximum" in parameter:
                        self.assertLessEqual(default, parameter["maximum"])
                    if "choices" in parameter:
                        self.assertIn(default, parameter["choices"])

    def test_enabled_modules_have_execution_safety_metadata(self) -> None:
        """Require descriptions, timeouts, and explicit risk on runnable entries."""
        for module in self.index["modules"]:
            if not module["enabled"]:
                continue
            with self.subTest(module=module["id"]):
                self.assertTrue(module["description"].strip())
                self.assertGreater(module["timeout_seconds"], 0)
                self.assertTrue(module["risk"]["summary"].strip())

    def test_system_control_is_disabled_by_default(self) -> None:
        """Never make process-control actions available without administrator review."""
        for module in self.index["modules"]:
            if module["execution_type"] == "system_control":
                self.assertFalse(module["enabled"])


if __name__ == "__main__":
    unittest.main()
