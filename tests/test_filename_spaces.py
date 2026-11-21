"""Filenames that already contain spaces split at the spaces; the bench found 'Walkway Expand Bold'
becoming 'W alkway  E xpand  Bold' because the PascalCase splitter was fed text that was already spaced."""

from __future__ import annotations

import pytest

from FontCore.core_filename_parts_parser import format_pascal_words, parse_filename, split_family_subfamily


@pytest.mark.parametrize(
    "value, expected",
    [
        ("Walkway Expand Bold", "Walkway Expand Bold"),
        ("Times New Roman Cyr Bold Italic", "Times New Roman Cyr Bold Italic"),
        ("Unique Light ITALIC", "Unique Light ITALIC"),
        ("Wacky Action BTN Bold", "Wacky Action BTN Bold"),
        ("Walkway UltraExpand", "Walkway Ultra Expand"),
        ("Probe  Sans", "Probe Sans"),
        ("ProbeSans", "Probe Sans"),
        ("ABC_EFGRegular", "ABC EFG Regular"),
    ],
)
def test_spaces_are_word_breaks(value, expected):
    assert format_pascal_words(value) == expected


def test_a_hyphenated_name_with_spaces_in_the_family():
    assert split_family_subfamily("Probe Sans-Bold.otf") == ("Probe Sans", "Bold")
    parsed = parse_filename("Probe Sans-SemiBold.otf")
    assert (parsed.family, parsed.subfamily) == ("Probe Sans", "Semibold")


def test_a_name_without_a_hyphen_is_all_family():
    assert split_family_subfamily("Walkway Expand Bold.otf") == ("Walkway Expand Bold", "")
