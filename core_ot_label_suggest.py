#!/usr/bin/env python3
"""
Conservative OpenType stylistic-set label suggestions from lookup coverage.

Only returns a string when the substitution set is unambiguously a single
readable character family. Wide alphabets, opaque glyph names, and contextual
lookups yield None — never a guess.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from fontTools.ttLib import TTFont

from FontCore.core_logging_config import get_logger
from FontCore.core_ot_label_scanner import find_feature_record

logger = get_logger(__name__)

# Above this many distinct input glyphs, a stylistic set is too broad to name.
_MAX_CLEAR_COVERAGE = 4

_RE_OPAQUE = re.compile(r"^(?:glyph\d+|gid\d+|uni[0-9A-Fa-f]{4,}|\.notdef)$", re.I)
_RE_BASE_STEM = re.compile(
    r"^([A-Za-z]|afii\d+|uni[0-9A-Fa-f]{4})(?:[._].*)?$"
)


def suggest_styleset_label(
    font: TTFont,
    *,
    table: str,
    feature_tag: str,
) -> Optional[str]:
    """
    Return a Fill suggestion for an unlabeled ss## feature, or None when unclear.
    """
    try:
        pairs = _single_subst_pairs(font, table=table, feature_tag=feature_tag)
    except Exception as exc:
        logger.debug("Suggest walk failed for %s/%s: %s", table, feature_tag, exc)
        return None
    if not pairs:
        return None
    if len(pairs) > _MAX_CLEAR_COVERAGE:
        return None

    glyph_to_char = _cmap_best_chars(font)
    bases: Set[str] = set()
    for src, _dst in pairs:
        if _RE_OPAQUE.match(src):
            return None
        char = glyph_to_char.get(src)
        if char and char.isprintable() and not char.isspace():
            bases.add(char)
            continue
        stem = _readable_stem(src)
        if stem is None:
            return None
        bases.add(stem)

    if len(bases) != 1:
        return None
    base = next(iter(bases))
    if len(base) == 1:
        return f"Alternate {base}"
    return f"Alternate {base}"


def _single_subst_pairs(
    font: TTFont,
    *,
    table: str,
    feature_tag: str,
) -> List[Tuple[str, str]]:
    """Collect (src, dst) from SingleSubst lookups only. Empty if mixed/complex."""
    rec = find_feature_record(font, table, feature_tag)
    if rec is None:
        return []
    ot_table = font[table].table
    lookup_list = getattr(ot_table, "LookupList", None)
    if lookup_list is None:
        return []
    indices = list(getattr(rec.Feature, "LookupListIndex", None) or [])
    if not indices:
        return []

    pairs: List[Tuple[str, str]] = []
    for lookup_index in indices:
        try:
            lookup = lookup_list.Lookup[lookup_index]
        except (IndexError, TypeError, AttributeError):
            return []
        # GSUB Single = type 1. Anything else is "unclear" for naming.
        if getattr(lookup, "LookupType", None) != 1:
            return []
        for subtable in lookup.SubTable or []:
            mapping = getattr(subtable, "mapping", None)
            if not isinstance(mapping, dict) or not mapping:
                return []
            for src, dst in mapping.items():
                pairs.append((str(src), str(dst)))
    # De-dupe while preserving order
    seen: Set[Tuple[str, str]] = set()
    unique: List[Tuple[str, str]] = []
    for pair in pairs:
        if pair in seen:
            continue
        seen.add(pair)
        unique.append(pair)
    return unique


def _cmap_best_chars(font: TTFont) -> Dict[str, str]:
    """Map glyph name → best Unicode character (prefer BMP printable)."""
    out: Dict[str, str] = {}
    try:
        cmap = font.getBestCmap() or {}
    except Exception:
        return out
    for codepoint, glyph in cmap.items():
        try:
            char = chr(int(codepoint))
        except (TypeError, ValueError, OverflowError):
            continue
        if not char.isprintable() or char.isspace():
            continue
        name = str(glyph)
        # Prefer single BMP letter mappings when colliding.
        existing = out.get(name)
        if existing is None or (len(char) == 1 and len(existing) > 1):
            out[name] = char
    return out


def _readable_stem(glyph_name: str) -> Optional[str]:
    if _RE_OPAQUE.match(glyph_name):
        return None
    # Common production: a.ss01, g.alt → "a" / "g"
    base = glyph_name.split(".", 1)[0].split("_", 1)[0]
    if not base or _RE_OPAQUE.match(base):
        return None
    if len(base) == 1 and base.isalpha():
        return base
    if re.fullmatch(r"[A-Za-z]{1,8}", base):
        return base
    return None


__all__ = ["suggest_styleset_label"]
