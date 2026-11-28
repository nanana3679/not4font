"""Draw the punctuation, numeric operators, and key labels used in the game UI."""

import math

from shapely.affinity import scale, translate
from shapely.geometry import LineString, box
from shapely.ops import unary_union

from .geometry import (
    CORNER_HEIGHT, DIAGONAL_COS, DIAGONAL_RUN, DIAGONAL_SIN, offset_edges, pieces_of, polygon, rectangle,
)
from .glyphs import BOLD, REGULAR, draw_four, draw_s, draw_three, draw_two
from .spacing import cut_overlaps, symbol_pair_shift

TAIL_DEPTH = 12
TAIL_RUN = TAIL_DEPTH * DIAGONAL_RUN


def dot(weight):
    """A stem-wide square, shared by the points, the ! body and the ? neck."""
    return polygon(rectangle(0, 0, weight.stem, weight.stem))


def comma(weight):
    head = dot(weight)
    width = head.bounds[2]
    # The tail keeps the full width of the head and slants down to the left.
    tail = polygon([(0, 0), (width, 0), (width - TAIL_RUN, -TAIL_DEPTH), (-TAIL_RUN, -TAIL_DEPTH)])
    return head.union(tail)


def colon(weight, bottom):
    return unary_union([translate(bottom, yoff=14), translate(dot(weight), yoff=62)])


def horizontal_bar(weight, width, center=50):
    height = weight.stacked_horizontal
    return polygon(rectangle(0, center - height / 2, width, center + height / 2))


def frame(width, height, stroke):
    outside = polygon(rectangle(0, 0, width, height))
    return outside.difference(polygon(rectangle(stroke, stroke, width - stroke, height - stroke)))


def layered(weight, strokes):
    """Draw strokes in order; where a later stroke overlaps the ink so far, it wins and cuts that ink a stencil gap around it."""
    ink = strokes[0]
    for stroke in strokes[1:]:
        cut = cut_overlaps(ink, pieces_of(stroke), weight)
        ink = (ink if cut is None else cut).union(stroke)
    return ink


def diagonal_bar(height, thickness, bottom=0):
    run = height * DIAGONAL_RUN
    return polygon(
        [
            (0, bottom),
            (thickness, bottom),
            (run + thickness, bottom + height),
            (run, bottom + height),
        ]
    )


def reflect(shape):
    return scale(shape, xfact=-1, origin="center")


def plus(weight):
    width = 66
    left = (width - weight.stem) / 2
    upright = polygon(rectangle(left, 16, left + weight.stem, 84))
    return horizontal_bar(weight, width).union(upright)


def multiply(weight):
    rising = diagonal_bar(64, weight.diagonal_across * 0.72, bottom=18)
    return rising.union(reflect(rising))


def less_than(weight):
    """Draw an open chevron with the horizontal arrowhead's slope, centered at 50."""
    height = {REGULAR: 70, BOLD: 74}[weight]
    upper = diagonal_bar(height / 2, weight.diagonal_across, bottom=50)
    return upper.union(scale(upper, yfact=-1, origin=(0, 50)))


def dollar(weight):
    """Keep the S intact and attach the stem at its top and bottom."""
    body = draw_s(weight)
    center = body.bounds[2] / 2
    half_stem = weight.stacked_horizontal * 0.31
    left, right = center - half_stem, center + half_stem
    join = weight.stacked_horizontal / 2
    return unary_union([body, box(left, -12, right, join), box(left, 100 - join, right, 112)])


def caret(weight):
    """Use the horizontal chevron's stroke angle, with the tip just above cap height."""
    top = 104
    height = 46
    bottom = top - height
    run = height * DIAGONAL_RUN
    # Leave an open notch even in the short Bold caret.
    across = weight.diagonal_across * 0.65
    return polygon([
        (0, bottom), (run, top), (2 * run, bottom),
        (2 * run - across, bottom), (run, top - across / DIAGONAL_RUN), (across, bottom),
    ])


def tilde(weight):
    """Join the rising ends with a vertical stroke, trimming the mitres to the same height."""
    half_stroke = weight.stacked_horizontal * 0.35
    half_height = 17 + half_stroke
    half_width = (half_height + 6) * DIAGONAL_RUN
    tip_rise = weight.stacked_horizontal
    tip_run = tip_rise * DIAGONAL_RUN
    path = LineString([
        (-tip_run, 44 - tip_rise), (half_width, 50 + half_height),
        (half_width, 50 - half_height), (2 * half_width + tip_run, 56 + tip_rise),
    ])
    ink = path.buffer(half_stroke, cap_style="flat", join_style="mitre")
    width = 2 * half_width
    wave = ink.intersection(box(0, 50 - half_height, width, 50 + half_height))

    # Extend each 52-degree flank to a point at its end's center, then flatten the lower/upper corner it leaves.
    tip_width = half_stroke / DIAGONAL_SIN
    tip_height = half_stroke / DIAGONAL_COS
    left = polygon([(-tip_width, 44), (0, 44 - tip_height), (0, 44 + tip_height)])
    cut = box(-tip_width, 0, tip_width, 44 - 2 * tip_height / 3)
    center = (half_width, 50)
    right = scale(left, xfact=-1, yfact=-1, origin=center)
    opposite_cut = scale(cut, xfact=-1, yfact=-1, origin=center)
    pointed = unary_union([wave, left, right]).difference(unary_union([cut, opposite_cut]))

    four = draw_four(weight)
    four_left, four_bottom, _, four_top = four.bounds
    edge = LineString([(four_left, four_bottom), (four_left, four_top)])
    four_tip = four.intersection(edge).bounds[1]
    aligned = translate(four, xoff=-tip_width - four_left, yoff=44 - four_tip)
    # At this cut, the 4's horizontal edge meets the inner flank of the wave.
    tip_region = box(-tip_width, 0, tip_width, 100)
    tip_cut = tip_region.difference(aligned)
    other_tip_cut = scale(tip_cut, xfact=-1, yfact=-1, origin=center)
    return pointed.difference(tip_cut.union(other_tip_cut))


def angular_ring(left, width, height, stroke):
    """Use the O's 52-degree corners and offset every edge by the same amount."""
    corner = height * (CORNER_HEIGHT / 100)
    run = corner * DIAGONAL_RUN
    bottom, top = 50 - height / 2, 50 + height / 2
    right = left + width
    outside = [
        (left + run, bottom), (right - run, bottom), (right, bottom + corner), (right, top - corner),
        (right - run, top), (left + run, top), (left, top - corner), (left, bottom + corner),
    ]
    return polygon(outside).difference(polygon(offset_edges(outside, -stroke)))


def at_sign(weight):
    """Join the inner O and the open outer ring at the O's bottom stroke."""
    outer_width, outer_ratio, inner_width, inner_ratio, stroke = {
        REGULAR: (78, 0.98, 38, 0.94, 9),
        BOLD: (84, 1, 36, 1, 14),
    }[weight]
    outer_height = outer_width / outer_ratio
    inner_height = inner_width / inner_ratio
    rim = angular_ring(0, outer_width, outer_height, stroke)
    core = angular_ring((outer_width - inner_width) / 2, inner_width, inner_height, stroke)
    bottom = core.bounds[1]

    # Open the lower-right rim and keep the tail level with the base of the O.
    rim = rim.difference(box(outer_width * 0.69, rim.bounds[1] - 1, outer_width + 1, bottom))
    tail_start = core.bounds[2] - inner_height * CORNER_HEIGHT / 100 * DIAGONAL_RUN
    tail = box(tail_start, bottom, outer_width - stroke / 2, bottom + stroke)
    return unary_union([rim, core, tail])


def percent(weight):
    width = weight.scaled_width(54)
    height = 50
    # The ring strokes are 1.5 times the first drawing's round(stem * 0.37) + 2.
    stroke = (round(weight.stem * 0.37) + 2) * 1.5
    ring = frame(width, height, stroke)
    thickness = weight.diagonal_across * 0.74
    slash = diagonal_bar(100, thickness)
    # Each ring reaches two stencil gaps into the slash, measured square to it, and the slash, drawn last, cuts it back.
    # The reach stops where the cut would leave less than half the ring stroke at the corner of the hole.
    corner = stroke * (DIAGONAL_SIN + DIAGONAL_COS)
    reach_gaps = min(2, (corner - stroke / 2) / weight.stencil_gap - 1)
    reach = weight.stencil_gap * reach_gaps / DIAGONAL_SIN
    upper_right = (100 - height) * DIAGONAL_RUN + reach
    lower_left = thickness + height * DIAGONAL_RUN - reach
    return layered(weight, [translate(ring, xoff=upper_right - width, yoff=100 - height), translate(ring, xoff=lower_left), slash])


def parenthesis(weight):
    turn = 22
    run = turn * DIAGONAL_RUN
    wall = round(weight.stem * 0.65) + 2
    return polygon(
        [
            (run, 0),
            (run + wall, 0),
            (wall, turn),
            (wall, 100 - turn),
            (run + wall, 100),
            (run, 100),
            (0, 100 - turn),
            (0, turn),
        ]
    )


def bracket(weight):
    height = weight.stacked_horizontal
    wall = round(weight.stem * 0.65) + 2
    return unary_union(
        [
            polygon(rectangle(0, 0, wall, 100)),
            horizontal_bar(weight, 37, height / 2),
            horizontal_bar(weight, 37, 100 - height / 2),
        ]
    )


def quote(weight):
    shape = comma(weight)
    return translate(shape, yoff=100 - shape.bounds[3])


def exclamation(weight):
    point = dot(weight)
    width = point.bounds[2]
    upright = polygon(rectangle(0, 44, width, 100))
    return point.union(upright)


def question(weight):
    """Take 2 down to the bottom of its middle bar and hang a neck and the point under the middle of the ink.

    The middle bar is shortened from its left end, keeping the slant of that end, until its bottom-left corner
    meets the column of the neck and point, so nothing of the hook sticks out to the left of it.
    """
    two = draw_two(weight)
    cut, bar_top = weight.middle_bottom, weight.middle_top
    upper = two.intersection(polygon(rectangle(-1, cut, two.bounds[2] + 1, 101)))
    left, _, right, _ = upper.bounds
    column = (left + right - weight.stem) / 2

    def bar_left_at(y):
        return LineString([(-1, y), (right + 1, y)]).intersection(upper).bounds[0]

    low, high = cut + 1, bar_top - 1
    slant = (bar_left_at(high) - bar_left_at(low)) / (high - low)
    shortened = polygon(
        [(-1, cut - 1), (column - slant, cut - 1), (column + slant * (bar_top + 0.5 - cut), bar_top + 0.5), (-1, bar_top + 0.5)]
    )
    point = translate(dot(weight), xoff=column)
    # A stem-square neck if it fits above the point with a stencil gap; dropped if less than a stencil gap of it is left.
    neck_bottom = max(cut - weight.stem, point.bounds[3] + weight.stencil_gap)
    parts = [upper.difference(shortened), point]
    if cut - neck_bottom >= weight.stencil_gap:
        parts.append(polygon(rectangle(column, neck_bottom, column + weight.stem, cut)))
    return unary_union(parts)


def number_sign(weight):
    """Cross two bars with two diagonals at 0.8 of the letter diagonal weight, stood up to 68 degrees."""
    angle = math.radians(68)
    across = weight.diagonal * 0.8 / math.sin(angle)
    run = 88 / math.tan(angle)
    stem = polygon([(0, 6), (across, 6), (run + across, 94), (run, 94)])
    # The gap between the diagonals, measured square to them, stays what it was at 52 degrees.
    gap = (30 - weight.diagonal_across / 2) * DIAGONAL_SIN / math.sin(angle)
    step = across + gap
    width = stem.bounds[2] + step
    return unary_union(
        [
            stem,
            translate(stem, xoff=step),
            horizontal_bar(weight, width, 32),
            horizontal_bar(weight, width, 68),
        ]
    )


# The owner set the & leg with the live tuner on 2026-11-27. Its outer edge crosses the baseline this far right of the
# first drawing's place (the 3's right edge + scaled_width(14) + a stencil gap), and its upper end is this high less
# a stencil gap; its lower end is a stencil gap below the baseline.
AMPERSAND_LEG_SHIFT = {REGULAR: 1.8, BOLD: 11.4}
AMPERSAND_LEG_TOP = 69.1


def ampersand(weight):
    """Mirror 3 and cross it last with a 52-degree leg from its middle out below the baseline at the right."""
    three = draw_three(weight)
    body = scale(three, xfact=-1, origin=(three.bounds[2] / 2, 50))
    right = body.bounds[2] + weight.scaled_width(14) + weight.stencil_gap + AMPERSAND_LEG_SHIFT[weight]
    low, top = -weight.stencil_gap, AMPERSAND_LEG_TOP - weight.stencil_gap
    across = weight.diagonal_across

    def outer(y):
        return right - y * DIAGONAL_RUN

    leg = polygon([(outer(low) - across, low), (outer(low), low), (outer(top), top), (outer(top) - across, top)])
    return layered(weight, [body, leg])


def asterisk(weight):
    """Cross two 52-degree arms and a bar, all at 0.8 of the letter diagonal weight, as tall as the multiply sign up to cap height."""
    height = 64
    middle = 100 - height / 2
    thickness = weight.diagonal * 0.8
    rising = diagonal_bar(height, thickness / DIAGONAL_SIN, bottom=middle - height / 2)
    cross = rising.union(reflect(rising))
    left, _, right, _ = cross.bounds
    bar = polygon(rectangle(left, middle - thickness / 2, right, middle + thickness / 2))
    return cross.union(bar)


def horizontal_arrow(weight):
    width, head = 96, 34
    thickness = weight.stacked_horizontal
    tip = polygon(
        [
            (width, 50),
            (width - head, 50 + head / DIAGONAL_RUN),
            (width - head, 50 - head / DIAGONAL_RUN),
        ]
    )
    return horizontal_bar(weight, width - head + thickness).union(tip)


def vertical_arrow(weight):
    width, height = 64, 90
    left = (width - weight.stem) / 2
    head_height = width / 2 / DIAGONAL_RUN
    shaft = polygon(rectangle(left, 5, left + weight.stem, height - head_height + 2))
    tip = polygon([(width / 2, height), (width, height - head_height), (0, height - head_height)])
    return shaft.union(tip)


def trill_diamond(weight):
    """Fill a diamond with the trill note's 5:1 aspect, about as wide as a capital."""
    width = weight.scaled_width(100)
    height = width / 5
    return polygon([(0, 50), (width / 2, 50 - height / 2), (width, 50), (width / 2, 50 + height / 2)])


def hollow_trill_diamond(weight):
    """Outline the trill diamond so that its hole is a third of its height."""
    diamond = trill_diamond(weight)
    left, bottom, right, top = diamond.bounds
    width, height = right - left, top - bottom
    stroke = height / 3 / math.hypot(1, height / width)
    return diamond.difference(diamond.buffer(-stroke, join_style="mitre"))


SYMBOLS = ".…,:;-/%+()'\"!?#&×·—=←→↑↓[]\\`*◇◆<>$^~@"

# Comma tails hang outside the spacing body, on the (left, right), so spacing is measured from the heads.
TAIL_OVERHANGS = {",": (TAIL_RUN, 0), ";": (TAIL_RUN, 0), "'": (TAIL_RUN, 0), '"': (TAIL_RUN, 0), "`": (0, TAIL_RUN)}


def build_symbols(weight):
    """Return the outlines and the bodies used to measure symbol spacing."""
    point = dot(weight)
    period_step = symbol_pair_shift(point, point, point, point, weight.letter_space)
    apostrophe = quote(weight)
    paren = parenthesis(weight)
    square = bracket(weight)
    slash = diagonal_bar(100, weight.diagonal_across)
    right = horizontal_arrow(weight)
    up = vertical_arrow(weight)
    less = less_than(weight)
    shapes = {
        ".": point,
        "…": unary_union([translate(point, xoff=index * period_step) for index in range(3)]),
        ",": comma(weight),
        ":": colon(weight, point),
        ";": colon(weight, comma(weight)),
        "-": horizontal_bar(weight, 46),
        "/": slash,
        "%": percent(weight),
        "+": plus(weight),
        "(": paren,
        ")": reflect(paren),
        "'": apostrophe,
        '"': apostrophe.union(
            translate(apostrophe, xoff=apostrophe.bounds[2] + weight.stencil_gap * 2)
        ),
        "!": exclamation(weight),
        "?": question(weight),
        "#": number_sign(weight),
        "&": ampersand(weight),
        "×": multiply(weight),
        "·": translate(point, yoff=50 - point.bounds[3] / 2),
        "—": horizontal_bar(weight, 108),
        "=": horizontal_bar(weight, 64, 34).union(horizontal_bar(weight, 64, 66)),
        "←": reflect(right),
        "→": right,
        "↑": up,
        "↓": scale(up, yfact=-1, origin=(0, 50)),
        "[": square,
        "]": reflect(square),
        "\\": reflect(slash),
        "`": reflect(apostrophe),
        "*": asterisk(weight),
        "◇": hollow_trill_diamond(weight),
        "◆": trill_diamond(weight),
        "<": less,
        ">": reflect(less),
        "$": dollar(weight),
        "^": caret(weight),
        "~": tilde(weight),
        "@": at_sign(weight),
    }
    outlines, bodies = {}, {}
    for char, shape in shapes.items():
        left, bottom, right, top = shape.bounds
        before, after = TAIL_OVERHANGS.get(char, (0, 0))
        body = shape.intersection(box(left + before, bottom, right - after, top)) if before or after else shape
        outlines[char] = translate(shape, -body.bounds[0])
        bodies[char] = translate(body, -body.bounds[0])
    return outlines, bodies
