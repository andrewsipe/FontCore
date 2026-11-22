"""--weight-word / --weight-position: the user names the weight for styles that have none."""
import pytest

from FontCore.core_filename_parts_parser import (
    clear_weight_override,
    split_family_subfamily,
    set_weight_override,
    weight_override_note_silenced,
)
from FontCore.core_font_style_dictionaries import apply_weight_override


@pytest.fixture(autouse=True)
def _clean():
    clear_weight_override()
    yield
    clear_weight_override()


@pytest.mark.parametrize(
    "style, word, position, expected",
    [
        ("Carved", "Light", "last", "Carved Light"),
        ("Carved", "Light", "first", "Light Carved"),
        ("Carved Italic", "Light", "last", "Carved Light Italic"),
        ("Carved Italic", "Light", "first", "Light Carved Italic"),
        ("Condensed", "Book", "last", "Condensed Book"),
        ("", "Medium", "last", "Medium"),
        ("Italic", "Medium", "last", "Medium Italic"),
        ("Carved", "Semi Bold", "last", "Carved Semibold"),
        ("Carved", None, "last", "Carved"),
        ("Carved", "none", "last", "Carved"),
        ("Carved", "NONE", "first", "Carved"),
        ("Bold Carved", "Light", "last", "Bold Carved"),  # already has a weight: untouched
        ("Light", "Black", "last", "Light"),
    ],
)
def test_apply_weight_override(style, word, position, expected):
    assert apply_weight_override(style, word, position) == expected


def test_running_twice_changes_nothing():
    once = apply_weight_override("Carved Italic", "Light", "last")
    assert apply_weight_override(once, "Light", "last") == once


def test_the_filename_parser_uses_the_override_for_every_name():
    set_weight_override("Regular", "last")
    assert split_family_subfamily("PrismaLL-Carved.ttf") == ("Prisma LL", "Carved Regular")
    set_weight_override("Light", "first")
    assert split_family_subfamily("PrismaLL-Carved.ttf") == ("Prisma LL", "Light Carved")


def test_without_an_override_the_parser_is_unchanged():
    assert split_family_subfamily("PrismaLL-Carved.ttf") == ("Prisma LL", "Carved")


def test_none_silences_the_note_and_changes_nothing():
    set_weight_override("none", "last")
    assert weight_override_note_silenced()
    assert split_family_subfamily("PrismaLL-Carved.ttf")[1] == "Carved"


def test_a_bad_position_is_rejected():
    with pytest.raises(ValueError):
        set_weight_override("Light", "middle")
