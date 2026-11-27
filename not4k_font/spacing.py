"""Place glyphs by their spacing bodies and cut overlaps around earlier ink."""

from shapely.affinity import translate
from shapely.ops import unary_union

from .geometry import discard_small_pieces, pieces_of

SPACE_WIDTH = 40
RA_CLEARANCE_FRACTION = 0.25


def least_shift(before, body, gap):
    """Find the horizontal offset that puts the next body at the requested gap."""
    return first_clear_shift(before, body, gap, before.bounds[0] - body.bounds[2], before.bounds[2] + gap + 1)


def clear_ink(before, after, shift, gap):
    """Move the ink of `after` right of `shift` until it is at least `gap` from the ink of `before`."""
    if before.distance(translate(after, shift, 0)) >= gap - 1e-9:
        return shift
    # Search only to the right of `shift`, so a mark never settles inside a counter.
    return first_clear_shift(before, after, gap, shift, before.bounds[2] - after.bounds[0] + gap)


def first_clear_shift(before, body, gap, low, high):
    for _ in range(60):
        middle = (low + high) / 2
        if before.distance(translate(body, middle, 0)) >= gap - 1e-9:
            high = middle
        else:
            low = middle
    return high


def ra_clearance(glyphs, bodies, letter_space):
    return least_shift(glyphs["r"], bodies["a"], letter_space) - least_shift(
        bodies["r"], bodies["a"], letter_space
    )


def edition_kerning(glyphs, bodies, letter_space):
    return {("r", "a"): RA_CLEARANCE_FRACTION * ra_clearance(glyphs, bodies, letter_space)}


def cut_overlaps(drawn, earlier_pieces, weight):
    """Return a cut outline if it overlaps earlier ink by more than the area tolerance."""
    winners = [piece for piece in earlier_pieces if piece.intersection(drawn).area > 0.5]
    if not winners:
        return None
    room = unary_union(winners).buffer(weight.stencil_gap, join_style="mitre")
    minimum_area = 200 * (weight.stem / 30) ** 2
    return discard_small_pieces(drawn.difference(room), minimum_area)


def compose_line(text, glyphs, bodies, weight, kerning):
    placed = []
    previous = None
    after_space = None
    for char in text:
        if char == " ":
            right_edge = unary_union([body for _, body in placed]).bounds[2] if placed else 0
            after_space = right_edge + SPACE_WIDTH
            previous = None
            continue

        glyph, body = glyphs[char], bodies[char]
        if not placed:
            shift = 0
        elif after_space is not None:
            shift = after_space
        else:
            before = unary_union([placed_body for _, placed_body in placed])
            shift = least_shift(before, body, weight.letter_space) + kerning.get(
                (previous, char), 0
            )

        drawn = translate(glyph, shift, 0)
        earlier_pieces = (piece for outline, _ in placed for piece in pieces_of(outline))
        cut = cut_overlaps(drawn, earlier_pieces, weight)
        placed.append((drawn if cut is None else cut, translate(body, shift, 0)))
        after_space = None
        previous = char

    # Close hairline seams between contours that touch.
    joined = unary_union([outline for outline, _ in placed])
    return joined.buffer(0.01, join_style="mitre").buffer(-0.01, join_style="mitre")
