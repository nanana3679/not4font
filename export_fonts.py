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
from shapely.ops import unary_union

from export_ed1 import CHARS, HERE, V72, V81


UNITS_PER_DESIGN_UNIT = 20
UNITS_PER_EM = 128 * UNITS_PER_DESIGN_UNIT
GLYPH_NAMES = {char: UV2AGL[ord(char.upper())] for char in CHARS}
WEIGHTS = (("Regular", V81.REGULAR, 400), ("Bold", V81.BOLD, 700))


def font_units(value):
    return otRound(value * UNITS_PER_DESIGN_UNIT)


def draw_glyph(shape):
    pen = TTGlyphPen(None)
    if shape.is_empty:
        return pen.glyph()
    for polygon in getattr(shape, "geoms", (shape,)):
        polygon = orient(polygon, sign=-1)
        for ring in (polygon.exterior, *polygon.interiors):
            first, *rest = ring.coords[:-1]
            pen.moveTo(tuple(map(font_units, first)))
            for point in rest:
                pen.lineTo(tuple(map(font_units, point)))
            pen.closePath()
    return pen.glyph()


def kerning_feature(pair_shifts, metrics, clipped_names):
    forms = {
        name: (name, clipped_names[name]) if name in clipped_names else (name,)
        for name in GLYPH_NAMES.values()
    }
    rules = []
    for (left, right), shift in pair_shifts.items():
        left_name, right_name = GLYPH_NAMES[left], GLYPH_NAMES[right]
        adjustment = font_units(shift) - metrics[left_name][0]
        if adjustment:
            for left_form in forms[left_name]:
                for right_form in forms[right_name]:
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


def add_clipped_glyphs(glyphs, pair_shifts, weight, tabular_names, outlines, metrics):
    r_name = GLYPH_NAMES["r"]
    r_pieces = V72.V69.pieces_of(glyphs["r"])
    r_advance = metrics[r_name][0] / UNITS_PER_DESIGN_UNIT
    min_area = 200 * (weight.s / 30) ** 2
    candidates = {
        name: (glyphs[char], pair_shifts["r", char])
        for char, name in GLYPH_NAMES.items()
    }
    for digit in digits:
        name = GLYPH_NAMES[digit]
        tabular = tabular_names[name]
        offset = (metrics[tabular][1] - metrics[name][1]) / UNITS_PER_DESIGN_UNIT
        candidates[tabular] = (translate(glyphs[digit], xoff=offset), r_advance)

    names = {}
    for name, (shape, shift) in candidates.items():
        positioned = translate(shape, xoff=shift)
        # Use the specimen compositor's overlap and small-piece thresholds.
        winners = [piece for piece in r_pieces if piece.intersection(positioned).area > 0.5]
        if not winners:
            continue
        cut = positioned.difference(unary_union(winners).buffer(weight.g, join_style="mitre"))
        kept = unary_union([piece for piece in V72.V69.pieces_of(cut) if piece.area >= min_area])
        glyph = draw_glyph(translate(kept, xoff=-shift))
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


def build_font(edition, style, weight, weight_class):
    glyphs, bodies, extra_kerning = V81.decided(weight)
    weight_record = edition["weights"][style.lower()]
    letter_space = weight_record["numbers"]["letterSpace"]
    space_advance = font_units(edition["rules"]["space"])

    outlines = {name: TTGlyphPen(None).glyph() for name in (".notdef", "space")}
    metrics = {name: (space_advance, 0) for name in outlines}
    for char, name in GLYPH_NAMES.items():
        left, _, right, _ = weight_record["glyphs"][char.upper()]["spacingBody"]
        outlines[name] = draw_glyph(glyphs[char])
        metrics[name] = (font_units(right - left), font_units(glyphs[char].bounds[0]))
    tabular_names = add_tabular_digits(outlines, metrics, letter_space)
    pair_shifts = {
        (left, right): V72.least_shift(bodies[left], bodies[right], letter_space) + extra_kerning.get((left, right), 0)
        for left in GLYPH_NAMES
        for right in GLYPH_NAMES
    }
    clipped_names = add_clipped_glyphs(glyphs, pair_shifts, weight, tabular_names, outlines, metrics)

    cmap = {ord(char): GLYPH_NAMES[char.lower()] for char in CHARS + ascii_uppercase}
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
    kern = kerning_feature(pair_shifts, metrics, clipped_names)
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
