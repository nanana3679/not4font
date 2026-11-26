import json
import unittest
from pathlib import Path
from string import digits
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fontTools.ttLib import TTFont
from shapely.affinity import translate
from shapely.geometry import Polygon
from shapely.ops import unary_union

from export_fonts import FONT_CHARACTERS, GLYPH_NAMES, HERE, UNITS_PER_DESIGN_UNIT, WEIGHTS, font_units, main
from not4k_font.glyphs import CHARACTERS, build_glyphs
from not4k_font.spacing import compose_line, edition_kerning, least_shift, ra_clearance


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


def glyph_geometry(glyph):
    shells, holes = [], []
    start = 0
    for end in glyph.endPtsOfContours:
        contour = Polygon([
            (x / UNITS_PER_DESIGN_UNIT, y / UNITS_PER_DESIGN_UNIT)
            for x, y in glyph.coordinates[start:end + 1]
        ])
        parts = holes if contour.exterior.is_ccw else shells
        parts.append(contour.buffer(0))
        start = end + 1
    return unary_union(shells).difference(unary_union(holes))


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
        expected_chars = set(FONT_CHARACTERS + FONT_CHARACTERS.upper() + " ")
        for style, _, weight_class in WEIGHTS:
            for extension in ("ttf", "woff2"):
                with self.subTest(style=style, extension=extension):
                    with TTFont(self.output / f"NOT4K-{style}.{extension}") as font:
                        cmap = font.getBestCmap()
                        self.assertEqual({chr(codepoint) for codepoint in cmap}, expected_chars)
                        self.assertEqual(font["OS/2"].usWeightClass, weight_class)
                        self.assertEqual(font["OS/2"].sCapHeight / font["head"].unitsPerEm, 100 / 128)
                        self.assertEqual(font["hmtx"].metrics[cmap[ord(" ")]], (font_units(40), 0))
                        for char in CHARACTERS:
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
            glyphs, bodies = build_glyphs(weight)
            extra_ra = ra_clearance(glyphs, bodies, weight.letter_space) * 0.25
            self.assertGreater(extra_ra, 0)
            with TTFont(self.output / f"NOT4K-{style}.woff2") as font:
                for right, extra in (("a", extra_ra), ("x", 0)):
                    with self.subTest(style=style, pair=f"R{right.upper()}"):
                        expected = least_shift(bodies["r"], bodies[right], weight.letter_space) + extra
                        advance, _ = font["hmtx"].metrics["R"]
                        actual = advance + pair_adjustment(font, "R", GLYPH_NAMES[right])
                        self.assertEqual(actual, font_units(expected))

    def test_tnum_centers_all_digits_at_the_widest_outline_plus_letter_space(self):
        for style, weight, _ in WEIGHTS:
            for extension in ("ttf", "woff2"):
                with self.subTest(style=style, extension=extension):
                    with TTFont(self.output / f"NOT4K-{style}.{extension}") as font:
                        self.check_tabular_digits(font, weight.letter_space)

    def check_tabular_digits(self, font, letter_space):
        self.assertIn("GSUB", font)
        gsub = font["GSUB"].table
        feature = next(record.Feature for record in gsub.FeatureList.FeatureRecord if record.FeatureTag == "tnum")
        substitutions = {
            source: target
            for index in feature.LookupListIndex
            for subtable in gsub.LookupList.Lookup[index].SubTable
            for source, target in subtable.mapping.items()
        }
        cmap = font.getBestCmap()
        base_digits = {cmap[ord(digit)] for digit in digits}
        self.assertEqual(set(substitutions), base_digits)

        glyphs = font["glyf"]
        metrics = font["hmtx"].metrics
        widest = max(glyphs[name].xMax - glyphs[name].xMin for name in base_digits)
        expected_advance = widest + font_units(letter_space)
        self.assertGreater(len({metrics[name][0] for name in base_digits}), 1)

        for base, tabular in substitutions.items():
            with self.subTest(glyph=base):
                self.assertNotIn(tabular, base_digits)
                advance, left = metrics[tabular]
                base_glyph, tabular_glyph = glyphs[base], glyphs[tabular]
                right = advance - tabular_glyph.xMax
                self.assertEqual(advance, expected_advance)
                self.assertEqual(left, tabular_glyph.xMin)
                self.assertLessEqual(abs(left - right), 1)
                shift = tabular_glyph.xMin - base_glyph.xMin
                self.assertEqual(list(tabular_glyph.coordinates), [(x + shift, y) for x, y in base_glyph.coordinates])
                for adjacent in substitutions.values():
                    self.assertEqual(pair_adjustment(font, tabular, adjacent), 0)

    def test_calt_builds_the_edition_1_overlap_pairs_and_keeps_their_advances(self):
        overlaps_by_style = {
            "Regular": "abdefhijklmnprwxz2347",
            "Bold": "abdefhijklmnprwxz247",
        }
        for style, weight, _ in WEIGHTS:
            glyphs, bodies = build_glyphs(weight)
            kerns = edition_kerning(glyphs, bodies, weight.letter_space)
            with self.subTest(style=style), TTFont(self.output / f"NOT4K-{style}.woff2") as font:
                gsub = font["GSUB"].table
                features = {record.FeatureTag: record.Feature for record in gsub.FeatureList.FeatureRecord}
                self.assertLess(max(features["tnum"].LookupListIndex), min(features["calt"].LookupListIndex))
                self.assertEqual(gsub.LookupList.Lookup[features["calt"].LookupListIndex[0]].LookupType, 6)

                outlines = font["glyf"]
                metrics = font["hmtx"].metrics
                alternates = {char for char, name in GLYPH_NAMES.items() if f"{name}.afterR" in outlines}
                self.assertEqual(alternates, set(overlaps_by_style[style]))
                for right in sorted(alternates):
                    with self.subTest(pair=f"R{right.upper()}"):
                        name = GLYPH_NAMES[right]
                        alternate = f"{name}.afterR"
                        self.assertEqual(metrics[alternate], (metrics[name][0], outlines[alternate].xMin))
                        self.assertEqual(pair_adjustment(font, "R", alternate), pair_adjustment(font, "R", name))

                        shift = least_shift(bodies["r"], bodies[right], weight.letter_space) + kerns.get(("r", right), 0)
                        original_pair = compose_line(f"r{right}", glyphs, bodies, weight, kerns)
                        expected = translate(original_pair.difference(glyphs["r"]), xoff=-shift)
                        deviation = glyph_geometry(outlines[alternate]).symmetric_difference(expected).area
                        self.assertLess(deviation, expected.length / UNITS_PER_DESIGN_UNIT)

    def test_clipped_r_keeps_kerning_and_clipped_tabular_two_keeps_its_width(self):
        for style, _, _ in WEIGHTS:
            with self.subTest(style=style), TTFont(self.output / f"NOT4K-{style}.woff2") as font:
                self.assertEqual(pair_adjustment(font, "R.afterR", "R.afterR"), pair_adjustment(font, "R", "R"))
                self.assertEqual(pair_adjustment(font, "R.afterR", "A.afterR"), pair_adjustment(font, "R", "A"))
                self.assertEqual(pair_adjustment(font, "E.afterR", "A"), pair_adjustment(font, "E", "A"))
                metrics = font["hmtx"].metrics
                self.assertEqual(metrics["two.tnum.afterR"][0], metrics["two.tnum"][0])
                self.assertEqual(pair_adjustment(font, "R", "two.tnum.afterR"), 0)

    def test_ui_symbols_have_nonempty_outlines_in_both_weights_and_formats(self):
        required = ".,:;-/%+()'\"!?#&×·—…=←→↑↓[]\\`*◇"
        for style, weight, _ in WEIGHTS:
            for extension in ("ttf", "woff2"):
                with self.subTest(style=style, extension=extension):
                    with TTFont(self.output / f"NOT4K-{style}.{extension}") as font:
                        cmap = font.getBestCmap()
                        glyphs = font["glyf"]
                        metrics = font["hmtx"].metrics
                        for char in required:
                            with self.subTest(char=char):
                                name = cmap[ord(char)]
                                self.assertGreater(glyphs[name].numberOfContours, 0)
                                self.assertGreater(metrics[name][0], 0)
                        for left, right in (("R", "period"), ("four", "exclam"), ("period", "quotesingle")):
                            shift = metrics[left][0] + pair_adjustment(font, left, right)
                            self.assertEqual(shift, glyphs[left].xMax + font_units(weight.letter_space))
