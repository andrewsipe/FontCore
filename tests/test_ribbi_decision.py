"""ID2 is one of Regular, Italic, Bold, Bold Italic, decided by name, then flag, then angle.

House convention (DECISIONS.md, Q7 revisited): the word Bold decides Bold; the word Italic or a measured
angle outside +-2 degrees (forward or back) decides Italic. Flags confirm, and decide only when the style says
nothing. usWeightClass is not trusted. A name that says Italic is never demoted by a near-zero angle.
"""

from __future__ import annotations

import pytest

from FontCore.core_name_policies import ITALIC_ANGLE_FLOOR, decide_ribbi

FS_ITALIC, FS_BOLD, FS_REGULAR = 0x01, 0x20, 0x40
MAC_BOLD, MAC_ITALIC = 0x01, 0x02


def d(style, fs=0, mac=0, angle=0.0):
    return decide_ribbi(style, fs_selection=fs, mac_style=mac, italic_angle=angle)


def test_the_floor_is_two_degrees():
    assert ITALIC_ANGLE_FLOOR == 2.0


@pytest.mark.parametrize(
    "style, expected",
    [
        ("Regular", "Regular"),
        ("Bold", "Bold"),
        ("Condensed Bold", "Bold"),
        ("Light", "Regular"),
        ("Semibold", "Regular"),
        ("Extrabold", "Regular"),
        ("Black", "Regular"),
        ("Italic", "Italic"),
        ("Regular Italic", "Italic"),
        ("Bold Italic", "Bold Italic"),
        ("Light Italic", "Italic"),
    ],
)
def test_the_name_decides(style, expected):
    assert d(style).subfamily == expected


def test_usweightclass_is_not_used():
    # decide_ribbi takes no weight class at all
    assert "weight" not in str(decide_ribbi.__code__.co_varnames).lower()


@pytest.mark.parametrize(
    "style, angle, expected",
    [
        ("Oblique", -12.0, "Italic"),
        ("Backslanted", 10.0, "Italic"),
        ("Cursive", -9.0, "Italic"),
        ("Bold Oblique", -10.0, "Bold Italic"),
        ("Regular", -2.0, "Regular"),  # name wins: a slanted upright-named design stays Regular
        ("Regular", 2.0, "Regular"),
        ("Bold", 9.0, "Bold"),
        ("Light Condensed", 9.0, "Regular"),
        ("", 9.0, "Italic"),  # nothing in the name: the angle decides
        ("Regular", 1.9, "Regular"),
        ("Regular", -1.9, "Regular"),
        ("Regular", 0.0, "Regular"),
    ],
)
def test_the_angle_adds_italic_in_either_direction(style, angle, expected):
    assert d(style, angle=angle).subfamily == expected


def test_a_name_that_says_italic_is_not_demoted_by_a_flat_angle():
    result = d("Italic", angle=0.0)
    assert result.subfamily == "Italic"
    assert any("angle" in note for note in result.notes)


def test_flags_decide_only_when_the_style_says_nothing():
    assert d("", fs=FS_BOLD).subfamily == "Bold"
    assert d("", mac=MAC_BOLD).subfamily == "Bold"
    assert d("", fs=FS_ITALIC).subfamily == "Italic"
    assert d("", mac=MAC_ITALIC | MAC_BOLD).subfamily == "Bold Italic"
    assert d(None, fs=FS_REGULAR).subfamily == "Regular"


def test_a_stale_flag_does_not_override_a_clear_name():
    assert d("Light", fs=FS_ITALIC | FS_BOLD, mac=MAC_ITALIC | MAC_BOLD).subfamily == "Regular"
    assert d("Semibold", fs=FS_BOLD, mac=MAC_BOLD).subfamily == "Regular"


def test_a_stale_italic_flag_is_overruled_by_an_upright_angle():
    assert d("Regular", fs=FS_ITALIC, angle=0.0).subfamily == "Regular"


def test_missing_angle_is_treated_as_unknown():
    assert decide_ribbi("Light", fs_selection=0, mac_style=0, italic_angle=None).subfamily == "Regular"
    assert decide_ribbi("Italic", fs_selection=0, mac_style=0, italic_angle=None).subfamily == "Italic"
