"""Sort GSUB, GPOS and GDEF Coverage tables by glyph ID, the way the OpenType spec wants them.

A Coverage table lists glyphs, and other arrays are indexed by position in that list (a base glyph's anchors, a pair's
kerning, a rule set). Sorting the glyphs alone would give each glyph its neighbour's data, so every array that runs parallel
to a Coverage is reordered with it. A subtable whose parallel array does not match its Coverage in length is left alone.

fontTools quietly repairs one kind of out-of-order Coverage when it reads a font (ranges whose start index is out of order),
so the font looks sorted in memory while the file on disk is not. :func:`watch_unsorted_coverage` reports that, so the
caller knows a save is needed.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Callable, Iterator, Optional, Tuple

from fontTools.ttLib import TTFont

from FontCore.core_gpos_repair import get_glyph_id, iter_expand_subtables, repair_pairpos_second_glyph_order


# Coverage attribute -> the arrays that run parallel to it (same index = same glyph). Sorting the Coverage alone would
# pair every glyph with its neighbour's data, so these are reordered with it. Each entry is an attribute on the subtable,
# or a (container, list) pair.
_PARALLEL = {
    "Coverage": ("PairSet", "Value", "SubRuleSet", "PosRuleSet", "ChainSubRuleSet", "ChainPosRuleSet", "EntryExitRecord"),
    "MarkCoverage": (("MarkArray", "MarkRecord"),),
    "BaseCoverage": (("BaseArray", "BaseRecord"),),
    "LigatureCoverage": (("LigatureArray", "LigatureAttach"),),
    "Mark1Coverage": (("Mark1Array", "MarkRecord"),),
    "Mark2Coverage": (("Mark2Array", "Mark2Record"),),
}


def _parallel_lists(owner, names):
    """The (container, attribute, list) of each parallel array that exists on ``owner``."""
    found = []
    for name in names:
        container, attr = (owner, name) if isinstance(name, str) else (getattr(owner, name[0], None), name[1])
        value = getattr(container, attr, None) if container is not None else None
        if isinstance(value, list):
            found.append((container, attr, value))
    return found


def sort_coverage_with_arrays(font: TTFont, owner, coverage_attr: str, names=None) -> bool:
    """Sort ``owner.<coverage_attr>`` by glyph ID and move its parallel arrays with it.

    Returns True when the order changed. A parallel array whose length does not match the Coverage is left alone and the
    Coverage is not touched either, so a damaged subtable is never made worse.
    """
    cov = getattr(owner, coverage_attr, None)
    if cov is None or not getattr(cov, "glyphs", None):
        return False
    old = list(cov.glyphs)
    order = sorted(range(len(old)), key=lambda i: get_glyph_id(font, old[i]))
    if order == list(range(len(old))):
        return False
    arrays = _parallel_lists(owner, _PARALLEL[coverage_attr] if names is None else names)
    if any(len(lst) != len(old) for _, _, lst in arrays):
        return False
    for container, attr, lst in arrays:
        setattr(container, attr, [lst[i] for i in order])
    cov.glyphs = [old[i] for i in order]
    return True


class _LoadWatch:
    fired = False


@contextmanager
def watch_unsorted_coverage() -> Iterator[_LoadWatch]:
    """Notes whether fontTools warned about an out-of-order Coverage while a font was read.

    fontTools repairs that quirk in memory, so the font looks sorted afterwards; the file on disk still has it until the
    font is saved. ``watch.fired`` tells the caller to save.
    """
    watch = _LoadWatch()

    class _Handler(logging.Handler):
        def emit(self, record):
            if "Coverage is not sorted" in record.getMessage():
                watch.fired = True

    logger = logging.getLogger("fontTools.ttLib.tables.otTables")
    handler, level, propagate = _Handler(), logger.level, logger.propagate
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    logger.propagate = False  # the caller says it once, in its own words
    try:
        yield watch
    finally:
        logger.removeHandler(handler)
        logger.setLevel(level)
        logger.propagate = propagate


def sort_coverage(font: TTFont, coverage) -> bool:
    """
    Sort a Coverage table by glyph IDs.

    Returns:
        True if sorting was needed (order changed), False otherwise
    """
    if not hasattr(coverage, "glyphs") or not coverage.glyphs:
        return False

    # Get current order
    old_glyphs = list(coverage.glyphs)

    # Get glyph IDs and sort
    glyph_data = [(get_glyph_id(font, g), g) for g in coverage.glyphs]
    glyph_data.sort(key=lambda x: x[0])
    coverage.glyphs = [g for _, g in glyph_data]

    # Check if order changed
    return old_glyphs != coverage.glyphs


def sort_class_def(font: TTFont, class_def) -> bool:
    """
    Sort a ClassDef table by glyph IDs.

    Returns:
        True if sorting was needed, False otherwise
    """
    if not hasattr(class_def, "classDefs") or not class_def.classDefs:
        return False

    # ClassDef is a dict, just ensure it's ordered by glyph ID
    old_items = list(class_def.classDefs.items())
    sorted_items = sorted(
        class_def.classDefs.items(), key=lambda x: get_glyph_id(font, x[0])
    )
    class_def.classDefs = dict(sorted_items)

    # Check if order changed (dict order matters in Python 3.7+)
    return old_items != sorted_items


def process_lookup(font: TTFont, lookup) -> int:
    """
    Process a single lookup and sort all its Coverage tables.

    Returns:
        Number of coverage tables sorted
    """
    sorted_count = 0

    if not hasattr(lookup, "SubTable"):
        return sorted_count

    for subtable in iter_expand_subtables(lookup.SubTable):
        cov = getattr(subtable, "Coverage", None)
        lig_keys = getattr(subtable, "ligatures", None)

        if lig_keys is not None and cov is not None and getattr(cov, "glyphs", None):
            # LigatureSubst keeps its sets in a dict keyed by glyph, so the Coverage can be sorted on its own
            try:
                if sort_coverage(font, cov):
                    sorted_count += 1
                subtable.ligatures = {g: subtable.ligatures[g] for g in cov.glyphs if g in subtable.ligatures}
            except (AttributeError, TypeError):
                pass
        else:
            for coverage_attr in _PARALLEL:
                if sort_coverage_with_arrays(font, subtable, coverage_attr):
                    sorted_count += 1

        if hasattr(subtable, "ClassDef"):
            sort_class_def(font, subtable.ClassDef)

        if hasattr(subtable, "BacktrackCoverage"):
            for c in subtable.BacktrackCoverage:
                if sort_coverage(font, c):
                    sorted_count += 1

        if hasattr(subtable, "InputCoverage"):
            for c in subtable.InputCoverage:
                if sort_coverage(font, c):
                    sorted_count += 1

        if hasattr(subtable, "LookAheadCoverage"):
            for c in subtable.LookAheadCoverage:
                if sort_coverage(font, c):
                    sorted_count += 1

    return sorted_count


def process_table(font: TTFont, table_tag: str) -> Tuple[int, int]:
    """
    Process GSUB or GPOS table.

    Returns:
        (total_coverage, sorted_count) tuple
    """
    total_coverage = 0
    sorted_count = 0

    if table_tag not in font:
        return total_coverage, sorted_count

    table = font[table_tag]

    if hasattr(table, "table"):
        table = table.table

    # Process all lookup lists
    if hasattr(table, "LookupList") and table.LookupList:
        for lookup in table.LookupList.Lookup:
            # Count coverage tables in this lookup
            if hasattr(lookup, "SubTable"):
                for subtable in lookup.SubTable:
                    # Count main Coverage
                    if hasattr(subtable, "Coverage") and hasattr(
                        subtable.Coverage, "glyphs"
                    ):
                        if subtable.Coverage.glyphs:
                            total_coverage += 1

                    for extra in ("MarkCoverage", "BaseCoverage", "LigatureCoverage", "Mark1Coverage", "Mark2Coverage"):
                        if getattr(getattr(subtable, extra, None), "glyphs", None):
                            total_coverage += 1

                    # Count contextual coverage
                    if hasattr(subtable, "BacktrackCoverage"):
                        total_coverage += len(subtable.BacktrackCoverage)
                    if hasattr(subtable, "InputCoverage"):
                        total_coverage += len(subtable.InputCoverage)
                    if hasattr(subtable, "LookAheadCoverage"):
                        total_coverage += len(subtable.LookAheadCoverage)

            # Sort coverage in this lookup
            sorted_count += process_lookup(font, lookup)

    return total_coverage, sorted_count


def process_gdef(font: TTFont) -> Tuple[int, int]:
    """
    Process GDEF table.

    Returns:
        (total_coverage, sorted_count) tuple
    """
    total_coverage = 0
    sorted_count = 0

    if "GDEF" not in font:
        return total_coverage, sorted_count

    gdef = font["GDEF"].table

    # LigCaretList and AttachList each keep one array in Coverage order
    for list_name, array in (("LigCaretList", "LigGlyph"), ("AttachList", "AttachPoint")):
        owner = getattr(gdef, list_name, None)
        if owner is not None and getattr(getattr(owner, "Coverage", None), "glyphs", None):
            total_coverage += 1
            if sort_coverage_with_arrays(font, owner, "Coverage", names=(array,)):
                sorted_count += 1

    # Sort MarkAttachClassDef
    if hasattr(gdef, "MarkAttachClassDef") and gdef.MarkAttachClassDef:
        sort_class_def(font, gdef.MarkAttachClassDef)

    # Sort GlyphClassDef
    if hasattr(gdef, "GlyphClassDef") and gdef.GlyphClassDef:
        sort_class_def(font, gdef.GlyphClassDef)

    return total_coverage, sorted_count


def sort_coverage_tables_in_font(font: TTFont, report: Optional[Callable[[str], None]] = None) -> Tuple[int, int]:
    """Sort every Coverage table in GSUB, GPOS and GDEF by glyph ID, moving the arrays that run parallel to each one.

    The font is changed in place. ``report`` (optional) gets one plain line per detail worth showing.

    Returns ``(total_coverage, sorted_count)``. ``(0, 0)`` means the font has no Coverage tables.
    """
    total_coverage = 0
    sorted_count = 0

    for tag in ("GSUB", "GPOS"):
        total, changed = process_table(font, tag)
        total_coverage += total
        sorted_count += changed
    total, changed = process_gdef(font)
    total_coverage += total
    sorted_count += changed

    pairpos_fixes = repair_pairpos_second_glyph_order(font)
    sorted_count += len(pairpos_fixes)

    if report is not None:
        for lookup_index, first_glyph, old_order, new_order in pairpos_fixes:
            report(f"GPOS Lookup[{lookup_index}] {first_glyph}: reordered pair targets {old_order} -> {new_order}")
        if total_coverage:
            report(f"Found {total_coverage} Coverage table(s), sorted {sorted_count}")

    return total_coverage, sorted_count


__all__ = [
    "sort_coverage_tables_in_font",
    "sort_coverage_with_arrays",
    "watch_unsorted_coverage",
]
