import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from export_ed1 import HERE, export_edition


class ExportEditionTest(unittest.TestCase):
    def test_edition_1_export_matches_the_frozen_glyphs_specimens_and_metadata(self):
        frozen = HERE / "ed1"
        with TemporaryDirectory() as directory:
            output = Path(directory)
            export_edition(output)
            expected_files = {
                path.relative_to(frozen) for path in frozen.rglob("*") if path.is_file()
            }
            actual_files = {
                path.relative_to(output) for path in output.rglob("*") if path.is_file()
            }
            self.assertEqual(actual_files, expected_files)
            for path in sorted(expected_files):
                with self.subTest(file=path):
                    self.assertEqual((output / path).read_bytes(), (frozen / path).read_bytes())
