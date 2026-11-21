"""Every style carries a weight word: ID4 and ID17 add Regular when none is present.

House convention (DECISIONS.md, Q8, Q9, C1): `Italic` becomes `Regular Italic`, `Wide Italic`
becomes `Wide Regular Italic`, ID4 keeps Regular (`Probe Regular`, `Probe Regular Italic`). Roman and the
other equivalents count as weight words, so they are left alone.
"""

from __future__ import annotations

import pytest

from FontCore.core_font_style_dictionaries import ensure_weight_word, has_weight_word
from FontCore.core_name_policies import build_id4, build_id17


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Bold", True), ("Semibold", True), ("Extralight", True), ("UltraCondensed Semibold", True),
        ("Regular", True), ("Roman", True), ("Book", True), ("Normal", True), ("Plain", True),
        ("Medium", True), ("Light Italic", True), ("400", True), ("Text", True),
        ("Text Bold", True),
        ("Display Text", False),
        ("Condensed", False), ("SemiCondensed", False), ("Display", False), ("Italic", False),
        ("Wide Italic", False), ("Backslanted", False), ("Reverse Italic", False), ("", False),
    ],
)
def test_has_weight_word(text, expected):
    assert has_weight_word(text) is expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", "Regular"),
        ("Italic", "Regular Italic"),
        ("Wide", "Wide Regular"),
        ("Wide Italic", "Wide Regular Italic"),
        ("Display Condensed Italic", "Display Condensed Regular Italic"),
        ("Reverse Italic", "Regular Reverse Italic"),
        ("Condensed Reverse Italic", "Condensed Regular Reverse Italic"),
        # no slope vocabulary: only the exact word Italic is placed; anything else is a plain style word
        ("Oblique", "Oblique Regular"),
        ("Cursive", "Cursive Regular"),
        ("Bold Italic", "Bold Italic"),
        ("Light", "Light"),
        ("Roman", "Roman"),
        ("Regular Italic", "Regular Italic"),
        ("Text", "Text"),
        ("Display Text", "Display Text Regular"),
    ],
)
def test_ensure_weight_word(text, expected):
    assert ensure_weight_word(text) == expected
    assert ensure_weight_word(ensure_weight_word(text)) == expected


@pytest.mark.parametrize(
    "modifier, style, slope, expected",
    [
        (None, None, None, "Regular"),
        (None, "Regular", None, "Regular"),
        (None, "Italic", None, "Regular Italic"),
        (None, "Regular", "Italic", "Regular Italic"),
        (None, "Wide", "Italic", "Wide Regular Italic"),
        ("Condensed", None, "Italic", "Condensed Regular Italic"),
        (None, "Bold", "Italic", "Bold Italic"),
        (None, "Roman", None, "Roman"),
        (None, "Light", None, "Light"),
    ],
)
def test_id17_always_carries_a_weight(modifier, style, slope, expected):
    assert build_id17(modifier, style, slope) == expected


@pytest.mark.parametrize(
    "style, slope, expected",
    [
        (None, None, "Probe Regular"),
        ("Regular", None, "Probe Regular"),
        ("Regular", "Italic", "Probe Regular Italic"),
        (None, "Italic", "Probe Regular Italic"),
        ("Regular Italic", None, "Probe Regular Italic"),
        ("Bold", None, "Probe Bold"),
        ("Bold", "Italic", "Probe Bold Italic"),
        ("Light", None, "Probe Light"),
        ("Roman", None, "Probe Roman"),
        ("Condensed", None, "Probe Condensed Regular"),
    ],
)
def test_id4_keeps_regular(style, slope, expected):
    assert build_id4("Probe", None, style, slope) == expected


