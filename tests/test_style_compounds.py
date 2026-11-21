"""Weight compounds are one word; width and other compounds are joined without a space.

House convention (DECISIONS.md, Q4): weights are one lowercase-joined word (Semibold, Extralight),
widths and other compounds join with no space and keep their capitals (SemiCondensed). The one
exception is Smallcaps. Family names are never touched.
"""

from __future__ import annotations

import pytest

from FontCore.core_filename_parts_parser import parse_filename, split_family_subfamily
from FontCore.core_font_style_dictionaries import join_style_compounds


@pytest.mark.parametrize(
    "text, expected",
    [
        # weights: one word
        ("Semi Bold", "Semibold"),
        ("Demi Bold", "Demibold"),
        ("Extra Bold", "Extrabold"),
        ("Ultra Bold", "Ultrabold"),
        ("Extra Light", "Extralight"),
        ("Ultra Light", "Ultralight"),
        ("Semi Light", "Semilight"),
        ("Extra Black", "Extrablack"),
        ("Ultra Black", "Ultrablack"),
        ("Extra Thin", "Extrathin"),
        ("Super Heavy", "Superheavy"),
        # widths: joined, capitals kept
        ("Semi Condensed", "SemiCondensed"),
        ("Extra Condensed", "ExtraCondensed"),
        ("Ultra Expanded", "UltraExpanded"),
        ("Extra Wide", "ExtraWide"),
        ("XX Condensed", "XXCondensed"),
        ("X Wide", "XWide"),
        # both in one name
        ("Ultra Condensed Semi Bold", "UltraCondensed Semibold"),
        ("Semi Condensed Extra Light Italic", "SemiCondensed Extralight Italic"),
        ("Condensed Extra Bold", "Condensed Extrabold"),
        # the one capitalization exception
        ("Small Caps", "Smallcaps"),
        ("Small Caps Italic", "Smallcaps Italic"),
        # left alone
        ("Bold", "Bold"),
        ("Bold Condensed", "Bold Condensed"),
        ("Semibold", "Semibold"),
        ("SemiCondensed", "SemiCondensed"),
        ("Light Italic", "Light Italic"),
        ("Extra", "Extra"),
        ("Semi", "Semi"),
        ("Regular Italic", "Regular Italic"),
        ("Condensed Italic", "Condensed Italic"),
        ("Display Bold", "Display Bold"),
        ("", ""),
    ],
)
def test_join_style_compounds(text, expected):
    assert join_style_compounds(text) == expected


def test_join_style_compounds_is_idempotent():
    for text in ("Ultra Condensed Semi Bold", "Extra Light", "Small Caps"):
        once = join_style_compounds(text)
        assert join_style_compounds(once) == once


@pytest.mark.parametrize(
    "filename, family, subfamily",
    [
        ("Probe-SemiBold.otf", "Probe", "Semibold"),
        ("Probe-ExtraBold.otf", "Probe", "Extrabold"),
        ("Probe-DemiBold.otf", "Probe", "Demibold"),
        ("Probe-ExtraLight.otf", "Probe", "Extralight"),
        ("Probe-ExtraLightItalic.otf", "Probe", "Extralight Italic"),
        ("Probe-UltraBlack.otf", "Probe", "Ultrablack"),
        ("Probe-SemiCondensedBold.otf", "Probe", "SemiCondensed Bold"),
        ("Probe-CondensedSemiBold.otf", "Probe", "Condensed Semibold"),
        ("Probe-UltraCondensedSemiBold.otf", "Probe", "UltraCondensed Semibold"),
        ("Probe-ExtraWide.otf", "Probe", "ExtraWide"),
        ("Probe-XXCondensedBold.otf", "Probe", "XXCondensed Bold"),
        ("Probe-SmallCapsItalic.otf", "Probe", "Smallcaps Italic"),
        # already in house style
        ("Probe-Semibold.otf", "Probe", "Semibold"),
        ("Probe-Regular.otf", "Probe", "Regular"),
        ("Probe-BoldItalic.otf", "Probe", "Bold Italic"),
        ("Probe-BoldCondensed.otf", "Probe", "Bold Condensed"),
        # family names are not rewritten
        ("ExtraBoldSans-Regular.otf", "Extra Bold Sans", "Regular"),
        ("SemiSerif-Bold.otf", "Semi Serif", "Bold"),
    ],
)
def test_filename_parsing_joins_compounds_in_the_subfamily(filename, family, subfamily):
    assert split_family_subfamily(filename) == (family, subfamily)
    parsed = parse_filename(filename)
    assert (parsed.family, parsed.subfamily) == (family, subfamily)
