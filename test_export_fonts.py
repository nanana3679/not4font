import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fontTools.ttLib import TTFont

from export_fonts import CHARS, GLYPH_NAMES, HERE, V72, V81, WEIGHTS, font_units, main


def pair_adjustment(font, left, right):
    for lookup in font["GPOS"].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            if left not in subtable.Coverage.glyphs:
                continue
            index = subtable.Coverage.glyphs.index(left)
            for record in subtable.PairSet[index].PairValueRecord:
                if record.SecondGlyph == right:
                    return record.Value1.XAdvance
    return 0


class ExportFontsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        output = TemporaryDirectory()
        cls.addClassCleanup(output.cleanup)
        cls.output = Path(output.name)
        cls.edition = json.loads((HERE / "ed1" / "font-ed1.json").read_text())
        with patch("sys.argv", ["export_fonts.py", output.name]):
            main()

    def test_two_formats_map_both_cases_and_give_space_40_units(self):
        expected_chars = set(CHARS + CHARS.upper() + " ")
        for style, _, weight_class in WEIGHTS:
            for extension in ("ttf", "woff2"):
                with self.subTest(style=style, extension=extension):
                    with TTFont(self.output / f"NOT4K-{style}.{extension}") as font:
                        cmap = font.getBestCmap()
                        self.assertEqual({chr(codepoint) for codepoint in cmap}, expected_chars)
                        self.assertEqual(font["OS/2"].usWeightClass, weight_class)
                        self.assertEqual(font["OS/2"].sCapHeight / font["head"].unitsPerEm, 100 / 128)
                        self.assertEqual(font["hmtx"].metrics[cmap[ord(" ")]], (font_units(40), 0))
                        for char in CHARS:
                            glyph = cmap[ord(char)]
                            self.assertEqual(glyph, cmap[ord(char.upper())])
                            self.assertGreater(font["glyf"][glyph].numberOfContours, 0)

    def test_r_and_four_keep_ink_outside_the_spacing_body(self):
        for style, _, _ in WEIGHTS:
            with TTFont(self.output / f"NOT4K-{style}.woff2") as font:
                glyphs = self.edition["weights"][style.lower()]["glyphs"]
                for char in ("r", "4"):
                    with self.subTest(style=style, char=char):
                        name = GLYPH_NAMES[char]
                        left, _, right, _ = glyphs[char.upper()]["spacingBody"]
                        advance, lsb = font["hmtx"].metrics[name]
                        self.assertEqual(advance, font_units(right - left))
                        self.assertEqual(lsb, 0)
                        self.assertGreater(font["glyf"][name].xMax, advance)

    def test_ra_adds_25_percent_of_clearance_and_rx_uses_default_gap(self):
        for style, weight, _ in WEIGHTS:
            glyphs, bodies, _ = V81.decided(weight)
            extra_ra = V72.full_kern(weight, glyphs, bodies, "r", "a") * 0.25
            self.assertGreater(extra_ra, 0)
            with TTFont(self.output / f"NOT4K-{style}.woff2") as font:
                for right, extra in (("a", extra_ra), ("x", 0)):
                    with self.subTest(style=style, pair=f"R{right.upper()}"):
                        expected = V72.least_shift(bodies["r"], bodies[right], weight.sp) + extra
                        advance, _ = font["hmtx"].metrics["R"]
                        actual = advance + pair_adjustment(font, "R", GLYPH_NAMES[right])
                        self.assertEqual(actual, font_units(expected))
