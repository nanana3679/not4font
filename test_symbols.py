import math
import unittest

from shapely.geometry import LineString, Polygon, box

from export_fonts import WEIGHTS
from not4k_font.geometry import CORNER_HEIGHT, DIAGONAL_RUN, DIAGONAL_TAN, pieces_of
from not4k_font.glyphs import draw_three
from not4k_font.symbols import AMPERSAND_LEG_TOP, SYMBOLS, build_symbols

DIAGONAL_DEGREES = math.degrees(math.atan(DIAGONAL_TAN))
# Diagonal lines are the two edges of each slanted stroke or arrowhead, plus the stencil cuts the slash of % leaves on
# its rings. A corner cut would add a line. & is left out: it keeps the corner cuts of the 3 it is built from.
SQUARE_CORNERED_DIAGONAL_LINES = {
    **dict.fromkeys(".:·-—=+![]", 0),
    **dict.fromkeys("←→↑↓", 2),
    **dict.fromkeys("*%", 4),
}


def edges(shape):
    for polygon in pieces_of(shape):
        for ring in (polygon.exterior, *polygon.interiors):
            points = list(ring.coords)
            yield from zip(points, points[1:])


def edge_kind(start, end):
    angle = math.degrees(math.atan2(abs(end[1] - start[1]), abs(end[0] - start[0])))
    for kind, allowed in (("horizontal", 0), ("vertical", 90), ("diagonal", DIAGONAL_DEGREES)):
        if math.isclose(angle, allowed, abs_tol=1e-6):
            return kind
    return angle


def diagonal_lines(shape):
    lines = set()
    for start, end in edges(shape):
        if edge_kind(start, end) == "diagonal":
            rising = (end[0] - start[0]) * (end[1] - start[1]) > 0
            run = DIAGONAL_RUN if rising else -DIAGONAL_RUN
            lines.add((rising, round(start[0] - start[1] * run, 6)))
    return lines


def ink_width_at(shape, y):
    return LineString([(-1000, y), (1000, y)]).intersection(shape).length


class SymbolShapeTest(unittest.TestCase):
    def test_every_symbol_edge_is_horizontal_vertical_or_52_degrees(self):
        for style, weight, _ in WEIGHTS:
            outlines, _ = build_symbols(weight)
            # ? reuses the upper half of 2, whose diagonal starts one unit inside its bottom bar (about 52.7 degrees).
            # ◇ and ◆ keep the 5:1 aspect of the game's trill note, which the owner chose over 52-degree edges.
            # # stands its diagonals up to 68 degrees, which the owner chose.
            for char in SYMBOLS.replace("?", "").replace("◇", "").replace("◆", "").replace("#", ""):
                with self.subTest(style=style, char=char):
                    for start, end in edges(outlines[char]):
                        self.assertIn(edge_kind(start, end), ("horizontal", "vertical", "diagonal"))

    def test_square_cornered_symbols_have_diagonals_only_on_strokes(self):
        for style, weight, _ in WEIGHTS:
            outlines, _ = build_symbols(weight)
            for char, count in SQUARE_CORNERED_DIAGONAL_LINES.items():
                with self.subTest(style=style, char=char):
                    self.assertEqual(len(diagonal_lines(outlines[char])), count)

    def test_comma_tail_keeps_the_head_width_down_to_12_below_the_baseline(self):
        for style, weight, _ in WEIGHTS:
            outlines, _ = build_symbols(weight)
            comma = outlines[","]
            head = outlines["."].bounds[2]
            with self.subTest(style=style):
                self.assertEqual(comma.bounds[1], -12)
                for y in (head / 2, -1, -6, -11):
                    self.assertAlmostEqual(ink_width_at(comma, y), head)

    def test_comma_family_bodies_are_the_heads_and_the_tails_hang_outside(self):
        for style, weight, _ in WEIGHTS:
            outlines, bodies = build_symbols(weight)
            tail_run = 12 * DIAGONAL_RUN
            for char, (before, after) in {",": (tail_run, 0), ";": (tail_run, 0), "'": (tail_run, 0), '"': (tail_run, 0), "`": (0, tail_run)}.items():
                with self.subTest(style=style, char=char):
                    outline, body = outlines[char].bounds, bodies[char].bounds
                    self.assertEqual(body[0], 0)
                    self.assertAlmostEqual(body[0] - outline[0], before)
                    self.assertAlmostEqual(outline[2] - body[2], after)

    def test_percent_rings_reach_into_the_slash_and_its_stencil_cut_separates_them(self):
        for style, weight, _ in WEIGHTS:
            outlines, _ = build_symbols(weight)
            low_ring, slash, high_ring = sorted(pieces_of(outlines["%"]), key=lambda piece: piece.bounds[1])
            with self.subTest(style=style):
                self.assertEqual(slash.bounds[3] - slash.bounds[1], 100)
                for ring in (low_ring, high_ring):
                    left, bottom, right, top = ring.bounds
                    self.assertAlmostEqual(right - left, weight.scaled_width(54))
                    self.assertAlmostEqual(top - bottom, 50)
                    self.assertEqual(len(ring.interiors), 1)
                    hole_left, hole_bottom, hole_right, hole_top = Polygon(ring.interiors[0]).bounds
                    self.assertGreaterEqual(min(hole_right - hole_left, hole_top - hole_bottom), weight.stencil_gap)
                    # The ring reaches as far into the slash as leaves half its stroke at the cut corner.
                    stroke = (round(weight.stem * 0.37) + 2) * 1.5
                    corner_ink = Polygon(ring.interiors[0]).exterior.distance(Polygon(ring.exterior.coords).exterior)
                    self.assertAlmostEqual(corner_ink, stroke / 2)
                    # The cut leaves one 52-degree edge on the ring, a stencil gap from the slash.
                    self.assertEqual(len(diagonal_lines(ring)), 1)
                    self.assertAlmostEqual(ring.distance(slash), weight.stencil_gap)
                self.assertGreater(low_ring.distance(high_ring), weight.stencil_gap)

    def test_later_strokes_of_ampersand_and_percent_keep_a_stencil_gap_from_earlier_ink(self):
        for style, weight, _ in WEIGHTS:
            outlines, _ = build_symbols(weight)
            for char in "&%":
                pieces = list(pieces_of(outlines[char]))
                with self.subTest(style=style, char=char):
                    for index, piece in enumerate(pieces):
                        for other in pieces[index + 1:]:
                            self.assertGreaterEqual(piece.distance(other), weight.stencil_gap - 1e-9)

    def test_trill_diamonds_are_5_to_1_and_as_wide_as_h_with_a_third_high_hole_in_the_hollow_one(self):
        for style, weight, _ in WEIGHTS:
            outlines, _ = build_symbols(weight)
            for char, holes in (("◆", 0), ("◇", 1)):
                diamond = outlines[char]
                left, bottom, right, top = diamond.bounds
                with self.subTest(style=style, char=char):
                    self.assertEqual(right - left, weight.scaled_width(100))
                    self.assertAlmostEqual((right - left) / (top - bottom), 5)
                    self.assertAlmostEqual((top + bottom) / 2, 50)
                    self.assertEqual(len(diamond.interiors), holes)
                    if holes:
                        _, hole_bottom, _, hole_top = Polygon(diamond.interiors[0]).bounds
                        self.assertAlmostEqual(hole_top - hole_bottom, (top - bottom) / 3)

    def test_ampersand_keeps_the_top_of_its_mirrored_3_whole_and_runs_its_leg_below_the_baseline(self):
        for style, weight, _ in WEIGHTS:
            outlines, _ = build_symbols(weight)
            ampersand = outlines["&"]
            top = box(-1000, 100 - CORNER_HEIGHT, 1000, 101)
            leg = max(pieces_of(ampersand), key=lambda piece: piece.bounds[2])
            with self.subTest(style=style):
                self.assertAlmostEqual(ampersand.intersection(top).area, draw_three(weight).intersection(top).area)
                # The leg the owner set in the tuner: a stencil gap below the baseline up to 69.1 less a stencil gap.
                self.assertAlmostEqual(leg.bounds[1], -weight.stencil_gap)
                self.assertAlmostEqual(leg.bounds[3], AMPERSAND_LEG_TOP - weight.stencil_gap)

    def test_points_the_exclamation_body_and_the_question_neck_share_the_stem_width(self):
        for style, weight, _ in WEIGHTS:
            outlines, _ = build_symbols(weight)
            with self.subTest(style=style):
                self.assertEqual(outlines["."].bounds, (0, 0, weight.stem, weight.stem))
                for piece in pieces_of(outlines["!"]):
                    self.assertAlmostEqual(piece.bounds[2] - piece.bounds[0], weight.stem)
                question = outlines["?"]
                point = min(pieces_of(question), key=lambda piece: piece.bounds[1])
                self.assertAlmostEqual(point.bounds[2] - point.bounds[0], weight.stem)
                self.assertAlmostEqual(point.bounds[3] - point.bounds[1], weight.stem)
                # The point and the neck hang under the middle of the ink.
                self.assertAlmostEqual((point.bounds[0] + point.bounds[2]) / 2, (question.bounds[0] + question.bounds[2]) / 2)
                neck = LineString([(-1000, weight.middle_bottom - 0.01), (1000, weight.middle_bottom - 0.01)]).intersection(question)
                if neck.is_empty:
                    # Bold has no room for a neck a stencil gap tall above its stem-high point.
                    self.assertLess(weight.middle_bottom - weight.stem - weight.stencil_gap, weight.stencil_gap)
                else:
                    self.assertAlmostEqual(neck.bounds[0], point.bounds[0])
                    self.assertAlmostEqual(neck.bounds[2], point.bounds[2])

    def test_number_sign_has_68_degree_diagonals_at_0_8_of_the_letter_weight_and_square_bars(self):
        for style, weight, _ in WEIGHTS:
            outlines, _ = build_symbols(weight)
            angles = set()
            for start, end in edges(outlines["#"]):
                angles.add(round(math.degrees(math.atan2(abs(end[1] - start[1]), abs(end[0] - start[0]))), 6))
            with self.subTest(style=style):
                self.assertEqual(angles, {0, 90, 68})
                # Each diagonal is 0.8 of the letter diagonal weight thick, measured square to it.
                across = LineString([(-1000, 10), (1000, 10)]).intersection(outlines["#"])
                for piece in getattr(across, "geoms", [across]):
                    self.assertAlmostEqual(piece.length * math.sin(math.radians(68)), weight.diagonal * 0.8)

    def test_question_middle_bar_is_shortened_from_the_left_to_the_neck_and_point_column(self):
        for style, weight, _ in WEIGHTS:
            outlines, _ = build_symbols(weight)
            question = outlines["?"]
            point = min(pieces_of(question), key=lambda piece: piece.bounds[1])
            column_left = point.bounds[0]
            bar_bottom = LineString([(-1000, weight.middle_bottom + 1e-6), (1000, weight.middle_bottom + 1e-6)]).intersection(question)
            with self.subTest(style=style):
                # Probed 1e-6 above the bar bottom, on the slanted end.
                self.assertAlmostEqual(bar_bottom.bounds[0], column_left, places=5)
                # Below the top of the middle bar, nothing sticks out to the left of the column.
                self.assertAlmostEqual(question.intersection(box(-1000, 0, column_left, weight.middle_top)).area, 0)
