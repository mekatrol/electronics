"""Run with python3 -m unittest discover -s footprints/tests."""
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'setup-kicad-libs.sh'


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name)
        self.common = self.config / 'kicad_common.json'
        self.table = self.config / 'fp-lib-table'
        self.common.write_text(json.dumps({'environment': {'vars': {'OTHER': str(ROOT)}}, 'keep': [1, 2]}))

    def run_script(self, *args, success=True, teardown=False):
        env = dict(os.environ)
        env.pop('MY_KICAD_LIBS', None)
        script = getattr(self, 'script', SCRIPT)
        if teardown:
            script = script.with_name('teardown-kicad-libs.sh')
        result = subprocess.run(['bash', str(script), '--config-dir', str(self.config), *args],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def snapshot(self):
        return {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.config.iterdir() if p.is_file()}

    def test_fresh_and_idempotent(self):
        self.run_script()
        table = self.table.read_text()
        for lib in ROOT.glob('*.pretty'):
            self.assertEqual(table.count('${MY_KICAD_LIBS}/' + lib.name), 1)
        self.assertIn('(name "Connectors")', table)
        self.assertEqual(json.loads(self.common.read_text())['keep'], [1, 2])
        before = self.snapshot()
        self.run_script()
        self.assertEqual(before, self.snapshot())

    def test_aliases_symlinks_multiline_and_settings(self):
        alias = self.config / 'link'
        alias.symlink_to(ROOT / 'Extra.pretty', target_is_directory=True)
        self.table.write_text(f'''(fp_lib_table
  (version 7)
  (lib (name "Extra") (type "KiCad")
    (uri "${{OTHER}}/Extra.pretty/../Extra.pretty/")
    (options "x=y") (descr "A (custom) footprint") (disabled))
  (lib (name "Alias") (type "KiCad") (uri "{alias}")
    (options "x=y") (descr "A (custom) footprint") (disabled))
  (lib (name "Unrelated") (type "KiCad") (uri "/elsewhere") (hidden))
)\n''')
        self.run_script()
        text = self.table.read_text()
        self.assertNotIn('(name "Alias")', text)
        self.assertIn('(options "x=y") (descr "A (custom) footprint") (disabled)', text)
        self.assertIn('(lib (name "Unrelated") (type "KiCad") (uri "/elsewhere") (hidden))', text)
        before = self.snapshot()
        self.run_script()
        self.assertEqual(before, self.snapshot())

    def test_custom_nickname_preserved(self):
        self.table.write_text(f'(fp_lib_table (lib (name "My parts") (type "KiCad") (uri "{ROOT}/Extra.pretty")))')
        self.run_script()
        self.assertIn('(name "My parts")', self.table.read_text())
        self.assertNotIn('(name "Extra")', self.table.read_text())

    def test_dry_run(self):
        before = self.snapshot()
        self.run_script('--dry-run')
        self.assertEqual(before, self.snapshot())

    def test_conflicts_and_malformed_input_do_not_write(self):
        examples = [
            '(fp_lib_table (lib (name "Extra") (type "KiCad") (uri "/elsewhere")))',
            '(fp_lib_table (lib (name "unterminated)))',
            f'''(fp_lib_table
              (lib (name "Extra") (type "KiCad") (uri "{ROOT}/Extra.pretty") (disabled))
              (lib (name "Alias") (type "KiCad") (uri "{ROOT}/Extra.pretty")))''',
        ]
        for text in examples:
            with self.subTest(text=text):
                self.table.write_text(text)
                before = self.snapshot()
                self.run_script(success=False)
                self.assertEqual(before, self.snapshot())

    def test_teardown_rename_and_readd(self):
        # Copy the entry points so this test edits the actual Bash variables.
        bundle = self.config / 'bundle'
        bundle.mkdir()
        for name in ('setup-kicad-libs.sh', 'teardown-kicad-libs.sh', 'kicad-libs.py', 'library-names.conf'):
            shutil.copy2(ROOT / name, bundle / name)
        for library in ROOT.glob('*.pretty'):
            (bundle / library.name).symlink_to(library, target_is_directory=True)
        self.script = bundle / 'setup-kicad-libs.sh'
        self.table.write_text('(fp_lib_table (lib (name "Unrelated") (type "KiCad") (uri "/elsewhere")))')
        self.run_script()
        old_table = self.table.read_bytes()
        old_common = self.common.read_bytes()
        names = bundle / 'library-names.conf'
        names.write_text(names.read_text().replace('="Connectors"', '="My connectors"'))
        before = self.snapshot()
        self.run_script('--dry-run', teardown=True)
        self.assertEqual(before, self.snapshot())
        self.run_script(teardown=True)
        self.assertNotIn('Connectors', self.table.read_text())
        self.assertNotIn('MY_KICAD_LIBS', self.table.read_text())
        self.assertIn('(name "Unrelated")', self.table.read_text())
        self.assertEqual(old_common, self.common.read_bytes())
        self.assertEqual(old_table, (self.config / 'fp-lib-table.backup-before-custom-libs-teardown').read_bytes())
        before = self.snapshot()
        self.run_script(teardown=True)
        self.assertEqual(before, self.snapshot())
        self.run_script()
        self.assertIn('(name "My connectors")', self.table.read_text())
        self.assertNotIn('(name "Connectors")', self.table.read_text())
        before = self.snapshot()
        self.run_script()
        self.assertEqual(before, self.snapshot())

    def test_teardown_without_configuration_does_not_create_files(self):
        self.common.unlink()
        self.run_script(teardown=True)
        self.assertEqual({}, self.snapshot())

    def test_null_variables(self):
        self.common.write_text('{"environment": {"vars": null}}')
        self.run_script()
        self.assertEqual(json.loads(self.common.read_text())['environment']['vars']['MY_KICAD_LIBS'], str(ROOT))


if __name__ == '__main__':
    unittest.main()
