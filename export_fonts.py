"""Build the edition 1 Regular and Bold fonts as TTF and WOFF2."""

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from string import ascii_uppercase, digits

from fontTools.agl import UV2AGL
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.roundTools import otRound
from fontTools.misc.timeTools import timestampSinceEpoch
from fontTools.pens.ttGlyphPen import TTGlyphPen
from shapely.affinity import translate
from shapely.geometry.polygon import orient

from not4k_font.geometry import pieces_of
from not4k_font.glyphs import BOLD, CHARACTERS, REGULAR, build_glyphs, draw_z
from not4k_font.spacing import clear_ink, cut_overlaps, edition_kerning, least_shift
from not4k_font.symbols import SYMBOLS, TAIL_OVERHANGS, build_symbols


HERE = Path(__file__).parent
UNITS_PER_DESIGN_UNIT = 20
UNITS_PER_EM = 128 * UNITS_PER_DESIGN_UNIT
FONT_CHARACTERS = CHARACTERS + SYMBOLS
GLYPH_NAMES = {
    char: UV2AGL.get(ord(char.upper()), f"uni{ord(char.upper()):04X}")
    for char in FONT_CHARACTERS
}
WEIGHTS = (("Regular", REGULAR, 400), ("Bold", BOLD, 700))


def font_units(value):
    return otRound(value * UNITS_PER_DESIGN_UNIT)


def draw_glyph(shape):
    pen = TTGlyphPen(None)
    if shape.is_empty:
        return pen.glyph()
    for polygon in pieces_of(shape):
        polygon = orient(polygon, sign=-1)
        for ring in (polygon.exterior, *polygon.interiors):
            first, *rest = ring.coords[:-1]
            pen.moveTo(tuple(map(font_units, first)))
            for point in rest:
                pen.lineTo(tuple(map(font_units, point)))
            pen.closePath()
    return pen.glyph()


def kerning_feature(pair_shifts, metrics, clipped_names, tabular_adjustments):
    def forms(name):
        return (name, clipped_names[name]) if name in clipped_names else (name,)

    adjustments = {
        (GLYPH_NAMES[left], GLYPH_NAMES[right]): font_units(shift) - metrics[GLYPH_NAMES[left]][0]
        for (left, right), shift in pair_shifts.items()
    }
    adjustments.update(tabular_adjustments)
    rules = []
    for (left_name, right_name), adjustment in adjustments.items():
        if adjustment:
            for left_form in forms(left_name):
                for right_form in forms(right_name):
                    rules.append(f"  pos {left_form} {right_form} {adjustment};")
    return "\n".join(["feature kern {", *rules, "} kern;"])


def add_tabular_digits(outlines, metrics, letter_space):
    bounds = {
        GLYPH_NAMES[digit]: outlines[GLYPH_NAMES[digit]].coordinates.calcIntBounds()
        for digit in digits
    }
    # Keep the widest outline inside the cell, including the crossbar of 4.
    advance = max(right - left for left, _, right, _ in bounds.values()) + font_units(letter_space)
    names = {}
    for name, (left, _, right, _) in bounds.items():
        tabular_name = f"{name}.tnum"
        side_bearing = (advance - (right - left)) // 2
        tabular_glyph = deepcopy(outlines[name])
        tabular_glyph.coordinates.translate((side_bearing - left, 0))
        outlines[tabular_name] = tabular_glyph
        metrics[tabular_name] = (advance, side_bearing)
        names[name] = tabular_name
    return names


def tabular_outlines(glyphs, tabular_names, metrics):
    """Return each tabular digit outline in design units, placed in its cell."""
    shapes = {}
    for digit in digits:
        name = GLYPH_NAMES[digit]
        tabular = tabular_names[name]
        offset = (metrics[tabular][1] - metrics[name][1]) / UNITS_PER_DESIGN_UNIT
        shapes[tabular] = translate(glyphs[digit], xoff=offset)
    return shapes


def tabular_mark_kerning(glyphs, tabular_names, metrics, letter_space):
    """Move comma tails apart from tabular digits, which take no other kerning, keeping the cells fixed."""
    adjustments = {}
    for tabular, digit in tabular_outlines(glyphs, tabular_names, metrics).items():
        for char in TAIL_OVERHANGS:
            mark = GLYPH_NAMES[char]
            for left, right, left_shape, right_shape in (
                (tabular, mark, digit, glyphs[char]),
                (mark, tabular, glyphs[char], digit),
            ):
                advance = metrics[left][0] / UNITS_PER_DESIGN_UNIT
                shift = clear_ink(left_shape, right_shape, advance, letter_space)
                adjustment = font_units(shift) - metrics[left][0]
                if adjustment > 0:
                    adjustments[left, right] = adjustment
    return adjustments


def add_clipped_glyphs(glyphs, pair_shifts, weight, tabular_names, outlines, metrics):
    r_name = GLYPH_NAMES["r"]
    r_pieces = pieces_of(glyphs["r"])
    r_advance = metrics[r_name][0] / UNITS_PER_DESIGN_UNIT
    candidates = {
        name: (glyphs[char], pair_shifts["r", char])
        for char, name in GLYPH_NAMES.items()
    }
    for tabular, shape in tabular_outlines(glyphs, tabular_names, metrics).items():
        candidates[tabular] = (shape, r_advance)

    names = {}
    for name, (shape, shift) in candidates.items():
        positioned = translate(shape, xoff=shift)
        cut = cut_overlaps(positioned, r_pieces, weight)
        if cut is None:
            continue
        glyph = draw_glyph(translate(cut, xoff=-shift))
        clipped_name = f"{name}.afterR"
        outlines[clipped_name] = glyph
        metrics[clipped_name] = (metrics[name][0], glyph.coordinates.calcIntBounds()[0])
        names[name] = clipped_name
    return names


def substitution_features(tabular_names, clipped_names):
    base_digits = " ".join(tabular_names)
    tabular_digits = " ".join(tabular_names.values())
    r = GLYPH_NAMES["r"]
    base = " ".join(clipped_names)
    clipped = " ".join(clipped_names.values())
    # Run tnum first, so calt cuts the outline that will actually be drawn.
    return (
        f"feature tnum {{ sub [{base_digits}] by [{tabular_digits}]; }} tnum;\n"
        f"feature calt {{ sub [{r} {clipped_names[r]}] [{base}]' by [{clipped}]; }} calt;"
    )


def pair_shifts_for(glyphs, bodies, letter_space, extra_kerning):
    shifts = {}
    for left in GLYPH_NAMES:
        for right in GLYPH_NAMES:
            if left in SYMBOLS or right in SYMBOLS:
                # Keep short marks in reading order. Letters are measured by their ink to clear the
                # overhangs of R and 4, and marks by their bodies so that comma tails hang outside.
                edge = bodies[left] if left in SYMBOLS else glyphs[left]
                shift = edge.bounds[2] - bodies[right].bounds[0] + letter_space
                # Move a hanging tail apart from its neighbour when the inks come closer than the letter space.
                shift = clear_ink(glyphs[left], glyphs[right], shift, letter_space)
            else:
                shift = least_shift(bodies[left], bodies[right], letter_space)
                shift += extra_kerning.get((left, right), 0)
            shifts[left, right] = shift
    return shifts


def build_font(edition, style, weight, weight_class):
    glyphs, bodies = build_glyphs(weight)
    glyphs["z"] = bodies["z"] = draw_z(weight, angled_ends=True)
    letter_space = weight.letter_space
    extra_kerning = edition_kerning(glyphs, bodies, letter_space)
    symbol_outlines, symbol_bodies = build_symbols(weight)
    glyphs.update(symbol_outlines)
    bodies.update(symbol_bodies)
    weight_record = edition["weights"][style.lower()]
    space_advance = font_units(edition["rules"]["space"])

    outlines = {name: TTGlyphPen(None).glyph() for name in (".notdef", "space")}
    metrics = {name: (space_advance, 0) for name in outlines}
    for char, name in GLYPH_NAMES.items():
        if char in SYMBOLS:
            left, _, right, _ = bodies[char].bounds
        else:
            left, _, right, _ = weight_record["glyphs"][char.upper()]["spacingBody"]
        outlines[name] = draw_glyph(glyphs[char])
        metrics[name] = (font_units(right - left), font_units(glyphs[char].bounds[0]))
    tabular_names = add_tabular_digits(outlines, metrics, letter_space)
    pair_shifts = pair_shifts_for(glyphs, bodies, letter_space, extra_kerning)
    clipped_names = add_clipped_glyphs(glyphs, pair_shifts, weight, tabular_names, outlines, metrics)
    tabular_adjustments = tabular_mark_kerning(glyphs, tabular_names, metrics, letter_space)

    cmap = {ord(char): GLYPH_NAMES[char.lower()] for char in FONT_CHARACTERS + ascii_uppercase}
    cmap[ord(" ")] = "space"
    family = "NOT4K"
    ps_name = f"{family}-{style}"
    bold = style == "Bold"
    frozen = datetime.fromisoformat(edition["frozen"]).replace(tzinfo=timezone.utc)
    timestamp = timestampSinceEpoch(frozen.timestamp())
    ascent, descent = font_units(112), font_units(-16)

    builder = FontBuilder(UNITS_PER_EM)
    builder.updateHead(created=timestamp, modified=timestamp, macStyle=int(bold))
    builder.setupGlyphOrder(list(outlines))
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(outlines)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=ascent, descent=descent)
    builder.setupNameTable({
        "familyName": family,
        "styleName": style,
        "uniqueFontIdentifier": f"{ps_name};1.000",
        "fullName": f"{family} {style}",
        "psName": ps_name,
        "version": "Version 1.000",
    })
    builder.setupOS2(
        version=4,
        usWeightClass=weight_class,
        fsSelection=0x80 | (0x20 if bold else 0x40),
        sTypoAscender=ascent,
        sTypoDescender=descent,
        usWinAscent=ascent,
        usWinDescent=-descent,
        sCapHeight=font_units(100),
        sxHeight=font_units(100),
    )
    builder.setupPost()
    kern = kerning_feature(pair_shifts, metrics, clipped_names, tabular_adjustments)
    substitutions = substitution_features(tabular_names, clipped_names)
    addOpenTypeFeaturesFromString(builder.font, f"{kern}\n{substitutions}")
    return builder.font


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=HERE / "out" / "fonts")
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    edition = json.loads((HERE / "ed1" / "font-ed1.json").read_text())
    for style, weight, weight_class in WEIGHTS:
        font = build_font(edition, style, weight, weight_class)
        font.save(output / f"NOT4K-{style}.ttf")
        font.flavor = "woff2"
        font.save(output / f"NOT4K-{style}.woff2")


if __name__ == "__main__":
    main()
