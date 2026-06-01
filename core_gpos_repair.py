"""GPOS PairPos repairs needed by fontTools varLib instancer."""

from __future__ import annotations

from typing import Iterator, List, Tuple

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot


def get_glyph_id(font: TTFont, glyph_name: str) -> int:
    try:
        return font.getGlyphID(glyph_name)
    except (KeyError, ValueError, AttributeError):
        return 2**31 - 1


def iter_expand_subtables(subtables) -> Iterator:
    """Yield subtables, recursing into ExtensionPos wrappers."""
    for subtable in subtables:
        ext = getattr(subtable, "ExtSubTable", None)
        if ext is not None:
            yield from iter_expand_subtables([ext])
        else:
            yield subtable


def repair_pairpos_second_glyph_order(
    font: TTFont,
) -> List[Tuple[int, str, List[str], List[str]]]:
    """
    Sort PairPos Format 1 PairValueRecord entries by second-glyph glyph ID.

    fontTools' varLib instancer requires this order when flattening kerning
    subtables during static instance generation.

    Returns:
        List of (lookup_index, first_glyph, old_second_glyphs, new_second_glyphs).
    """
    if "GPOS" not in font:
        return []

    fixes: List[Tuple[int, str, List[str], List[str]]] = []
    table = font["GPOS"].table

    for lookup_index, lookup in enumerate(table.LookupList.Lookup):
        if lookup.LookupType != 9:
            continue
        for subtable in iter_expand_subtables(lookup.SubTable):
            if not isinstance(subtable, ot.PairPos) or subtable.Format != 1:
                continue
            if not subtable.Coverage or not subtable.Coverage.glyphs:
                continue
            for first_glyph, pairset in zip(subtable.Coverage.glyphs, subtable.PairSet):
                records = getattr(pairset, "PairValueRecord", None)
                if not records or len(records) < 2:
                    continue
                old_order = [record.SecondGlyph for record in records]
                records.sort(key=lambda record: get_glyph_id(font, record.SecondGlyph))
                new_order = [record.SecondGlyph for record in records]
                if new_order != old_order:
                    fixes.append((lookup_index, first_glyph, old_order, new_order))
    return fixes
