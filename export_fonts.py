"""Build the edition 1 Regular and Bold fonts as TTF and WOFF2."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from string import ascii_uppercase

from fontTools.agl import UV2AGL
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.roundTools import otRound
from fontTools.misc.timeTools import timestampSinceEpoch
from fontTools.pens.ttGlyphPen import TTGlyphPen
from shapely.geometry.polygon import orient

from export_ed1 import CHARS, HERE, V72, V81


UNITS_PER_DESIGN_UNIT = 20
UNITS_PER_EM = 128 * UNITS_PER_DESIGN_UNIT
GLYPH_NAMES = {char: UV2AGL[ord(char.upper())] for char in CHARS}
WEIGHTS = (("Regular", V81.REGULAR, 400), ("Bold", V81.BOLD, 700))


def font_units(value):
    return otRound(value * UNITS_PER_DESIGN_UNIT)


def draw_glyph(shape):
    pen = TTGlyphPen(None)
    for polygon in getattr(shape, "geoms", (shape,)):
        polygon = orient(polygon, sign=-1)
        for ring in (polygon.exterior, *polygon.interiors):
            first, *rest = ring.coords[:-1]
            pen.moveTo(tuple(map(font_units, first)))
            for point in rest:
                pen.lineTo(tuple(map(font_units, point)))
            pen.closePath()
    return pen.glyph()


def add_kerning(font, bodies, letter_space, extra_kerning, metrics):
    rules = []
    for left, left_name in GLYPH_NAMES.items():
        advance, _ = metrics[left_name]
        for right, right_name in GLYPH_NAMES.items():
            shift = V72.least_shift(bodies[left], bodies[right], letter_space)
            shift += extra_kerning.get((left, right), 0)
            adjustment = font_units(shift) - advance
            if adjustment:
                rules.append(f"  pos {left_name} {right_name} {adjustment};")
    feature = "\n".join(["feature kern {", *rules, "} kern;"])
    addOpenTypeFeaturesFromString(font, feature)


def build_font(edition, style, weight, weight_class):
    glyphs, bodies, extra_kerning = V81.decided(weight)
    weight_record = edition["weights"][style.lower()]
    space_advance = font_units(edition["rules"]["space"])

    outlines = {name: TTGlyphPen(None).glyph() for name in (".notdef", "space")}
    metrics = {name: (space_advance, 0) for name in outlines}
    for char, name in GLYPH_NAMES.items():
        left, _, right, _ = weight_record["glyphs"][char.upper()]["spacingBody"]
        outlines[name] = draw_glyph(glyphs[char])
        metrics[name] = (font_units(right - left), font_units(glyphs[char].bounds[0]))

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
    add_kerning(builder.font, bodies, weight_record["numbers"]["letterSpace"], extra_kerning, metrics)
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
