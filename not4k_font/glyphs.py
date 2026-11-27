"""Draw the edition 1 glyphs from the final Regular and Bold measurements."""

from dataclasses import dataclass
from string import ascii_lowercase, digits

from shapely.affinity import rotate, scale
from shapely.ops import unary_union

from .geometry import (
    CORNER_HEIGHT,
    CORNER_RUN,
    DIAGONAL_COS,
    DIAGONAL_RUN,
    DIAGONAL_SIN,
    FALLING,
    LOWER_RIGHT,
    RISING,
    UPPER_LEFT,
    add_vector,
    at_left_origin,
    clip_to_box,
    diagonal_stroke,
    discard_small_pieces,
    keep_side,
    offset_edges,
    pieces_of,
    polygon,
    rectangle,
)

CHARACTERS = ascii_lowercase + digits


@dataclass(frozen=True)
class Weight:
    stem: int
    stacked_horizontal: int
    round_horizontal: int
    diagonal: int
    stencil_gap: int
    letter_space: int
    width_scale: float
    bowl_width: int

    def scaled_width(self, bold_width):
        return round(bold_width * self.width_scale)

    @property
    def corner_thickness(self):
        return self.stem * 0.93

    @property
    def diagonal_across(self):
        return self.diagonal / DIAGONAL_SIN

    @property
    def middle_bottom(self):
        return 50 - self.stacked_horizontal / 2

    @property
    def middle_top(self):
        return 50 + self.stacked_horizontal / 2

    @property
    def bowl_bottom(self):
        return 50 - self.stacked_horizontal / 2 - 4


REGULAR = Weight(
    stem=16,
    stacked_horizontal=14,
    round_horizontal=15,
    diagonal=14,
    stencil_gap=4,
    letter_space=12,
    width_scale=0.9,
    bowl_width=72,
)
BOLD = Weight(
    stem=30,
    stacked_horizontal=24,
    round_horizontal=26,
    diagonal=26,
    stencil_gap=6,
    letter_space=6,
    width_scale=1.0,
    bowl_width=88,
)


def ring(weight, width, y0, y1, top, bottom):
    outer = [
        (CORNER_RUN, y0),
        (width - CORNER_RUN, y0),
        (width, y0 + CORNER_HEIGHT),
        (width, y1 - CORNER_HEIGHT),
        (width - CORNER_RUN, y1),
        (CORNER_RUN, y1),
        (0, y1 - CORNER_HEIGHT),
        (0, y0 + CORNER_HEIGHT),
    ]
    inner = offset_edges(
        outer,
        [
            -bottom,
            -weight.corner_thickness,
            -weight.stem,
            -weight.corner_thickness,
            -top,
            -weight.corner_thickness,
            -weight.stem,
            -weight.corner_thickness,
        ],
    )
    return polygon(outer).difference(polygon(inner))


def bowl(weight, width, y0, y1, bottom, top):
    outer = [
        (0, y0),
        (width - CORNER_RUN, y0),
        (width, y0 + CORNER_HEIGHT),
        (width, y1 - CORNER_HEIGHT),
        (width - CORNER_RUN, y1),
        (0, y1),
    ]
    inner = offset_edges(
        outer,
        [
            -bottom,
            -weight.corner_thickness,
            -weight.stem,
            -weight.corner_thickness,
            -top,
            -weight.stem,
        ],
    )
    return polygon(outer).difference(polygon(inner))


def open_bowl(weight, width, left_cut, right_cut):
    """Draw the open bowl shared by U and J, with a square corner when its cut is zero."""
    points = [(0, 100)]
    edge_offsets = [-weight.stem]
    if left_cut:
        points += [(0, left_cut), (left_cut * DIAGONAL_RUN, 0)]
        edge_offsets.append(-weight.corner_thickness)
    else:
        points.append((0, 0))
    edge_offsets.append(-weight.round_horizontal)
    if right_cut:
        points += [(width - right_cut * DIAGONAL_RUN, 0), (width, right_cut)]
        edge_offsets.append(-weight.corner_thickness)
    else:
        points.append((width, 0))
    edge_offsets.append(-weight.stem)
    points.append((width, 100))
    edge_offsets.append(10)  # Extend the counter past the top to leave the bowl open.
    inner = offset_edges(points, edge_offsets)
    return polygon(points).difference(polygon(inner))


def arm(x_end, y0, y1):
    return polygon([(0, y0), (0, y1), (x_end, y1), (x_end - (y1 - y0) * DIAGONAL_RUN, y0)])


def band(bottom, top):
    (b0, b1, yb), (t0, t1, yt) = bottom, top
    return polygon([(b0, yb), (b1, yb), (t1, yt), (t0, yt)])


def stem(weight, x=0):
    return polygon(rectangle(x, 0, x + weight.stem, 100))


def four_bar_heights(weight):
    return (25 - weight.stacked_horizontal / 2, 25 + weight.stacked_horizontal / 2)


def four_strokes(weight, arm_extension):
    bar_bottom, bar_top = four_bar_heights(weight)
    stem_x = (100 - bar_bottom) * DIAGONAL_RUN
    axis_start = add_vector((0, bar_bottom), LOWER_RIGHT, weight.diagonal / 2)
    blade = diagonal_stroke(
        axis_start, add_vector(axis_start, RISING, 160), weight.diagonal, before=40
    )
    diagonal = clip_to_box(blade, y0=bar_bottom, y1=100, x1=stem_x + weight.stem)
    crossbar = keep_side(
        rectangle(-40, bar_bottom, stem_x + weight.stem + arm_extension, bar_top),
        (0, bar_bottom),
        (stem_x, 100),
        (stem_x, bar_bottom + 5),
    )
    upright = rectangle(stem_x, 0, stem_x + weight.stem, 100)
    return [polygon(diagonal), polygon(crossbar), polygon(upright)]


def draw_a(weight):
    run = 100 * DIAGONAL_RUN
    axis = add_vector((0, 0), LOWER_RIGHT, weight.diagonal / 2)
    diagonal = polygon(
        clip_to_box(
            diagonal_stroke(axis, add_vector(axis, RISING, 160), weight.diagonal, before=40),
            y0=0,
            y1=100,
            x1=run + weight.stem,
        )
    )
    b0, b1 = four_bar_heights(weight)
    crossbar = polygon(
        keep_side(rectangle(-40, b0, run + weight.stem, b1), (0, 0), (run, 100), (run, 5))
    )
    return unary_union([diagonal, crossbar, stem(weight, run)])


def draw_b(weight):
    width = weight.scaled_width(96)
    return unary_union(
        [
            bowl(
                weight,
                width,
                weight.middle_bottom,
                100,
                weight.stacked_horizontal,
                weight.stacked_horizontal,
            ),
            bowl(
                weight,
                width,
                0,
                weight.middle_top,
                weight.stacked_horizontal,
                weight.stacked_horizontal,
            ),
            stem(weight),
        ]
    )


def draw_c(weight):
    width = weight.scaled_width(96)
    return ring(weight, width, 0, 100, weight.round_horizontal, weight.round_horizontal).difference(
        polygon(
            rectangle(width / 2, weight.round_horizontal, width + 1, 100 - weight.round_horizontal)
        )
    )


def draw_d(weight):
    width = weight.scaled_width(100)
    outer = [
        (0, 0),
        (width - CORNER_RUN, 0),
        (width, CORNER_HEIGHT),
        (width, 100 - CORNER_HEIGHT),
        (width - CORNER_RUN, 100),
        (0, 100),
    ]
    inner = offset_edges(
        outer,
        [
            -weight.round_horizontal,
            -weight.corner_thickness,
            -weight.stem,
            -weight.corner_thickness,
            -weight.round_horizontal,
            -weight.stem,
        ],
    )
    return polygon(outer).difference(polygon(inner))


def draw_e(weight):
    width = weight.scaled_width(84)
    return unary_union(
        [
            stem(weight),
            arm(width, 100 - weight.stacked_horizontal, 100),
            arm(width - 8, weight.middle_bottom, weight.middle_top),
            arm(width, 0, weight.stacked_horizontal),
        ]
    )


def draw_f(weight):
    width = weight.scaled_width(82)
    return unary_union(
        [
            stem(weight),
            arm(width, 100 - weight.stacked_horizontal, 100),
            arm(width - 8, weight.middle_bottom, weight.middle_top),
        ]
    )


def draw_g(weight):
    width = weight.scaled_width(104)
    body = ring(weight, width, 0, 100, weight.round_horizontal, weight.round_horizontal)
    body = body.difference(
        polygon(rectangle(width / 2, weight.middle_top, width + 1, 100 - weight.round_horizontal))
    )
    c = body.difference(
        polygon(
            rectangle(width / 2, weight.round_horizontal, width + 1, 100 - weight.round_horizontal)
        )
    )
    jaw = polygon(
        rectangle(
            width - weight.stem - 22,
            weight.middle_bottom,
            width - weight.stem + 1,
            weight.middle_top,
        )
    )
    right_stem = polygon(rectangle(width - weight.stem, 0, width, weight.middle_top))
    hook = unary_union([jaw, right_stem])
    c = c.difference(hook.buffer(weight.stencil_gap, join_style="mitre"))
    minimum_area = 200 * (weight.stem / 30) ** 2
    return unary_union(
        [discard_small_pieces(c, minimum_area), discard_small_pieces(hook, minimum_area)]
    )


def draw_h(weight):
    width = weight.scaled_width(100)
    return unary_union(
        [
            stem(weight),
            stem(weight, width - weight.stem),
            polygon(
                rectangle(
                    weight.stem - 1,
                    weight.middle_bottom,
                    width - weight.stem + 1,
                    weight.middle_top,
                )
            ),
        ]
    )


def draw_i(weight):
    return stem(weight)


def draw_j(weight):
    width = weight.scaled_width(88)
    return open_bowl(weight, width, left_cut=0, right_cut=40).difference(
        polygon(rectangle(-1, 40, width / 2, 101))
    )


def draw_k(weight):
    vertex = (weight.stem, 38)
    arm_axis = add_vector(vertex, UPPER_LEFT, weight.stem / 2)
    upper = clip_to_box(
        diagonal_stroke(arm_axis, add_vector(arm_axis, RISING, 120), weight.diagonal, before=40),
        x0=0,
        y1=100,
    )
    gap_at = add_vector(vertex, LOWER_RIGHT, weight.stencil_gap)
    leg_axis = (weight.stem + 24, 40)
    leg = clip_to_box(
        diagonal_stroke(
            add_vector(leg_axis, FALLING, -60), add_vector(leg_axis, FALLING, 120), weight.diagonal
        ),
        y0=0,
    )
    leg = keep_side(leg, gap_at, add_vector(gap_at, RISING, 50), (weight.stem + 60, 5))
    return unary_union([stem(weight), polygon(upper), polygon(leg)])


def draw_l(weight):
    width = weight.scaled_width(80)
    return unary_union([stem(weight), arm(width, 0, weight.stacked_horizontal)])


def draw_m(weight):
    width = 1.4 * weight.stem + 94

    def arm_of(start, direction):
        far = (start[0] + direction[0] * 200, start[1] + direction[1] * 200)
        return polygon(clip_to_box(diagonal_stroke(start, far, weight.diagonal, before=40), y1=100))

    left = arm_of((0.7 * weight.stem, 100), (DIAGONAL_COS, -DIAGONAL_SIN)).intersection(
        polygon(rectangle(-100, -100, width / 2, 200))
    )
    right = arm_of((width - 0.7 * weight.stem, 100), (-DIAGONAL_COS, -DIAGONAL_SIN)).intersection(
        polygon(rectangle(width / 2, -100, width + 100, 200))
    )
    v = unary_union([left, right]).intersection(polygon(rectangle(0, 0, width, 100)))
    room = v.buffer(weight.stencil_gap, join_style="mitre")
    return unary_union(
        [stem(weight).difference(room), stem(weight, width - weight.stem).difference(room), v]
    )


def draw_n(weight):
    width = 78 + 1.4 * weight.stem
    diagonal = polygon(
        clip_to_box(
            diagonal_stroke(
                (0.7 * weight.stem, 100),
                (width - 0.7 * weight.stem, 0),
                weight.diagonal,
                before=60,
                after=60,
            ),
            y0=0,
            y1=100,
        )
    )
    room = diagonal.buffer(weight.stencil_gap, join_style="mitre")
    return unary_union(
        [
            stem(weight).difference(room),
            stem(weight, width - weight.stem).difference(room),
            diagonal,
        ]
    )


def draw_o(weight):
    width = weight.scaled_width(104)
    return ring(weight, width, 0, 100, weight.round_horizontal, weight.round_horizontal)


def draw_p(weight):
    return unary_union(
        [
            stem(weight),
            bowl(
                weight,
                weight.bowl_width,
                weight.bowl_bottom,
                100,
                weight.stacked_horizontal,
                weight.round_horizontal,
            ),
        ]
    )


def draw_q(weight, top=40):
    width = weight.scaled_width(104)
    body = ring(weight, width, 0, 100, weight.round_horizontal, weight.round_horizontal)
    across = weight.stacked_horizontal / DIAGONAL_SIN
    foot = (width - 20.6, width - 20.6 + across, 0)
    tail = band(foot, (foot[0] - top * DIAGONAL_RUN, foot[1] - top * DIAGONAL_RUN, top))
    return unary_union([body.difference(tail.buffer(weight.stencil_gap, join_style="mitre")), tail])


def draw_r(weight):
    upper = draw_p(weight)
    across = weight.diagonal_across
    right = 100
    run = 100 * DIAGONAL_RUN
    diagonal = polygon(
        [(right - across, 0), (right, 0), (right - run, 100), (right - across - run, 100)]
    )
    cut = diagonal.difference(upper.buffer(weight.stencil_gap, join_style="mitre"))
    leg = next(piece for piece in pieces_of(cut) if piece.bounds[1] < 1e-6)
    return unary_union([upper, leg]), upper


def draw_s(weight):
    width = weight.scaled_width(96)
    upper = ring(
        weight,
        width,
        weight.middle_bottom,
        100,
        weight.stacked_horizontal,
        weight.stacked_horizontal,
    ).difference(
        polygon(
            rectangle(
                width / 2, weight.middle_bottom - 1, width + 1, 100 - weight.stacked_horizontal
            )
        )
    )
    lower = ring(
        weight, width, 0, weight.middle_top, weight.stacked_horizontal, weight.stacked_horizontal
    ).difference(
        polygon(rectangle(-1, weight.stacked_horizontal, width / 2, weight.middle_top + 1))
    )
    return unary_union([upper, lower])


def cap_bar(width, thickness):
    bevel = thickness * DIAGONAL_RUN
    return polygon(
        [
            (0, 100),
            (width, 100),
            (width - bevel, 100 - thickness),
            (bevel, 100 - thickness),
        ]
    )


def draw_t(weight):
    width = weight.scaled_width(97)
    bar = cap_bar(width, weight.round_horizontal)
    left = (width - weight.stem) / 2
    return unary_union(
        [bar, polygon(rectangle(left, 0, left + weight.stem, 100 - weight.round_horizontal + 1))]
    )


def draw_u(weight):
    return open_bowl(weight, weight.scaled_width(100), left_cut=40, right_cut=0)


def draw_v(weight):
    run = 100 * DIAGONAL_RUN
    diagonal = band((run, run + weight.diagonal_across, 0), (0, weight.diagonal_across, 100))
    shape = unary_union([diagonal, stem(weight, run)]).intersection(
        polygon(rectangle(0, 0, run + weight.stem, 100))
    )
    cut = polygon(
        [
            (run, 0),
            (run + 300 * DIAGONAL_RUN, 300),
            (run + 600, 300),
            (run + 600, -10),
            (run - 10 * DIAGONAL_RUN, -10),
        ]
    )
    return shape.difference(cut)


def draw_w(weight):
    return scale(draw_m(weight), yfact=-1, origin=((1.4 * weight.stem + 94) / 2, 50))


def draw_x(weight):
    width = 78 + weight.diagonal_across
    falling = band((width - weight.diagonal_across, width, 0), (0, weight.diagonal_across, 100))
    rising = band((0, weight.diagonal_across, 0), (width - weight.diagonal_across, width, 100))
    return unary_union(
        [falling, rising.difference(falling.buffer(weight.stencil_gap, join_style="mitre"))]
    )


def draw_y(weight):
    width = 78 + weight.diagonal_across
    middle = width / 2
    left = band(
        (middle - weight.diagonal_across / 2, middle + weight.diagonal_across / 2, 50),
        (0, weight.diagonal_across, 100),
    ).intersection(polygon(rectangle(-1, 0, middle, 101)))
    right = band(
        (middle - weight.diagonal_across / 2, middle + weight.diagonal_across / 2, 50),
        (width - weight.diagonal_across, width, 100),
    ).intersection(polygon(rectangle(middle, 0, width + 1, 101)))
    arms = unary_union([left, right])
    return unary_union(
        [
            arms,
            polygon(
                rectangle(
                    middle - weight.stem / 2, 0, middle + weight.stem / 2, arms.bounds[1] + 12
                )
            ),
        ]
    )


def draw_z(weight, *, angled_ends=False):
    width = 78 + weight.diagonal_across
    thickness = weight.stacked_horizontal
    diagonal = band((0, weight.diagonal_across, 0), (width - weight.diagonal_across, width, 100))
    room = diagonal.buffer(weight.stencil_gap, join_style="mitre")
    if angled_ends:
        top = cap_bar(width, thickness)
        bottom = rotate(top, 180, origin=(width / 2, 50))
    else:
        top = polygon(rectangle(0, 100 - thickness, width, 100))
        bottom = polygon(rectangle(0, 0, width, thickness))
    bars = [top.difference(room), bottom.difference(room)]
    return discard_small_pieces(unary_union(bars + [diagonal]), 200 * (weight.stem / 30) ** 2)


def draw_zero(weight):
    width = weight.scaled_width(92)
    body = ring(weight, width, 0, 100, weight.round_horizontal, weight.round_horizontal)
    outer = [
        (CORNER_RUN, 0),
        (width - CORNER_RUN, 0),
        (width, CORNER_HEIGHT),
        (width, 100 - CORNER_HEIGHT),
        (width - CORNER_RUN, 100),
        (CORNER_RUN, 100),
        (0, 100 - CORNER_HEIGHT),
        (0, CORNER_HEIGHT),
    ]
    counter = polygon(
        offset_edges(
            outer,
            [
                -weight.round_horizontal,
                -weight.corner_thickness,
                -weight.stem,
                -weight.corner_thickness,
                -weight.round_horizontal,
                -weight.corner_thickness,
                -weight.stem,
                -weight.corner_thickness,
            ],
        )
    ).buffer(-weight.stencil_gap, join_style="mitre")
    half = 10 * weight.stem / 30
    slash = band(
        (width / 2 - half + 50 * DIAGONAL_RUN / 2, width / 2 + half + 50 * DIAGONAL_RUN / 2, 25),
        (width / 2 - half - 50 * DIAGONAL_RUN / 2, width / 2 + half - 50 * DIAGONAL_RUN / 2, 75),
    )
    return unary_union([body, slash.intersection(counter)])


def draw_one(weight):
    diagonal, _, upright = four_strokes(weight, 0)
    shoulder = diagonal.intersection(polygon(rectangle(-100, 60, 300, 101)))
    return unary_union([shoulder, upright])


def draw_two(weight):
    width = weight.scaled_width(96)
    upper = ring(
        weight,
        width,
        weight.middle_bottom,
        100,
        weight.stacked_horizontal,
        weight.stacked_horizontal,
    ).difference(
        polygon(rectangle(-1, weight.middle_bottom - 1, width / 2, 100 - weight.stacked_horizontal))
    )
    run = (weight.middle_top - weight.stacked_horizontal) * DIAGONAL_RUN
    diagonal = band(
        (0, weight.diagonal_across, weight.stacked_horizontal - 1),
        (run, run + weight.diagonal_across, weight.middle_top),
    )
    joint = polygon(rectangle(run, weight.middle_bottom, width / 2 + 1, weight.middle_top))
    return unary_union([upper, arm(width, 0, weight.stacked_horizontal), diagonal, joint])


def draw_three(weight):
    width = weight.scaled_width(96)
    upper = ring(
        weight,
        width,
        weight.middle_bottom,
        100,
        weight.stacked_horizontal,
        weight.stacked_horizontal,
    ).difference(
        polygon(rectangle(-1, weight.middle_top, width / 2, 100 - weight.stacked_horizontal))
    )
    lower = ring(
        weight, width, 0, weight.middle_top, weight.stacked_horizontal, weight.stacked_horizontal
    ).difference(polygon(rectangle(-1, weight.stacked_horizontal, width / 2, weight.middle_bottom)))
    return unary_union([upper, lower]).difference(
        polygon(rectangle(-1, weight.middle_bottom - 1, 22, weight.middle_top + 1))
    )


def draw_four(weight, arm_extension=None):
    return unary_union(
        four_strokes(weight, weight.letter_space if arm_extension is None else arm_extension)
    )


def draw_five(weight):
    width = weight.scaled_width(96)
    lower = ring(
        weight, width, 0, weight.middle_top, weight.stacked_horizontal, weight.stacked_horizontal
    ).difference(
        polygon(rectangle(-1, weight.stacked_horizontal, width / 2, weight.middle_top + 1))
    )
    return unary_union(
        [
            lower,
            polygon(rectangle(0, weight.middle_bottom, weight.stem, 100)),
            arm(width, 100 - weight.stacked_horizontal, 100),
            polygon(rectangle(0, weight.middle_bottom, width / 2 + 1, weight.middle_top)),
        ]
    )


def draw_six(weight):
    width = weight.scaled_width(96)
    upper_outer = [
        (0, weight.middle_bottom),
        (width - CORNER_RUN, weight.middle_bottom),
        (width, weight.middle_bottom + CORNER_HEIGHT),
        (width, 100 - CORNER_HEIGHT),
        (width - CORNER_RUN, 100),
        (CORNER_RUN, 100),
        (0, 100 - CORNER_HEIGHT),
    ]
    upper_inner = offset_edges(
        upper_outer,
        [
            -weight.stacked_horizontal,
            -weight.corner_thickness,
            -weight.stem,
            -weight.corner_thickness,
            -weight.stacked_horizontal,
            -weight.corner_thickness,
            -weight.stem,
        ],
    )
    upper = (
        polygon(upper_outer)
        .difference(polygon(upper_inner))
        .difference(
            polygon(
                rectangle(
                    width / 2, weight.middle_bottom - 1, width + 1, 100 - weight.stacked_horizontal
                )
            )
        )
    )
    lower_outer = [
        (CORNER_RUN, 0),
        (width - CORNER_RUN, 0),
        (width, CORNER_HEIGHT),
        (width, weight.middle_top - CORNER_HEIGHT),
        (width - CORNER_RUN, weight.middle_top),
        (0, weight.middle_top),
        (0, CORNER_HEIGHT),
    ]
    lower_inner = offset_edges(
        lower_outer,
        [
            -weight.stacked_horizontal,
            -weight.corner_thickness,
            -weight.stem,
            -weight.corner_thickness,
            -weight.stacked_horizontal,
            -weight.stem,
            -weight.corner_thickness,
        ],
    )
    return unary_union([upper, polygon(lower_outer).difference(polygon(lower_inner))])


def draw_seven(weight):
    width = 96
    run = (100 - weight.stacked_horizontal) * DIAGONAL_RUN
    diagonal = band(
        (width - run - weight.diagonal_across, width - run, 0),
        (width - weight.diagonal_across, width, 100 - weight.stacked_horizontal + 1),
    )
    return unary_union(
        [polygon(rectangle(0, 100 - weight.stacked_horizontal, width, 100)), diagonal]
    )


def draw_eight(weight):
    width = weight.scaled_width(96)
    return unary_union(
        [
            ring(
                weight,
                width,
                weight.middle_bottom,
                100,
                weight.stacked_horizontal,
                weight.stacked_horizontal,
            ),
            ring(
                weight,
                width,
                0,
                weight.middle_top,
                weight.stacked_horizontal,
                weight.stacked_horizontal,
            ),
        ]
    )


def draw_nine(weight):
    return rotate(draw_six(weight), 180, origin=(weight.scaled_width(96) / 2, 50))


DRAW_GLYPH = {
    "a": draw_a,
    "b": draw_b,
    "c": draw_c,
    "d": draw_d,
    "e": draw_e,
    "f": draw_f,
    "g": draw_g,
    "h": draw_h,
    "i": draw_i,
    "j": draw_j,
    "k": draw_k,
    "l": draw_l,
    "m": draw_m,
    "n": draw_n,
    "o": draw_o,
    "p": draw_p,
    "q": draw_q,
    "s": draw_s,
    "t": draw_t,
    "u": draw_u,
    "v": draw_v,
    "w": draw_w,
    "x": draw_x,
    "y": draw_y,
    "z": draw_z,
    "0": draw_zero,
    "1": draw_one,
    "2": draw_two,
    "3": draw_three,
    "4": draw_four,
    "5": draw_five,
    "6": draw_six,
    "7": draw_seven,
    "8": draw_eight,
    "9": draw_nine,
}


def build_glyphs(weight):
    """Return the outlines and the bodies used to measure letter spacing."""
    outlines = {char: at_left_origin(draw(weight)) for char, draw in DRAW_GLYPH.items()}
    bodies = dict(outlines)
    outline_r, body_r = draw_r(weight)
    outlines["r"] = at_left_origin(outline_r)
    bodies["r"] = at_left_origin(body_r)
    bodies["4"] = at_left_origin(draw_four(weight, arm_extension=0))
    return outlines, bodies
