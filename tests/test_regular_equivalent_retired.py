"""The family-relative "regular equivalent" convention is retired (DECISIONS.md, revised Q5/F3).

ID1 drops only Regular (the RIBBI word). Roman, Book, Normal, Plain, Medium, Light and Text are ordinary
style words and stay, whether or not the family has a Regular. There is no nearest-neighbor pick and no
--regular-synonyms modes.
"""

from __future__ import annotations

import inspect

import pytest

import FontCore.core_name_policies as policies
from FontCore.core_name_policies import (
    build_id1,
    normalize_style_and_slope_for_id1_id4 as normalize,
)

REMOVED = [
    "identify_family_regular_equivalent",
    "get_regular_equivalent_for_families",
    "group_fonts_by_family_filename",
    "validate_regular_equivalent",
    "RegularEquivalentError",
    "VALID_REGULAR_EQUIVALENTS",
    "REGULAR_FALLBACK_PRIORITY",
    "DEFAULT_REGULAR_SYNONYMS_MODE",
    "_apply_regular_synonym_mode",
]


@pytest.mark.parametrize("name", REMOVED)
def test_regular_equivalent_machinery_is_gone(name):
    assert not hasattr(policies, name)


def test_no_regular_equivalent_parameters_are_left():
    for fn in (normalize, build_id1, policies.build_id4):
        params = set(inspect.signature(fn).parameters)
        assert not params & {"regular_equivalent", "regular_synonyms_mode", "drop_book", "drop_normal"}


@pytest.mark.parametrize(
    "style, expected",
    [
        ("Regular", (None, None)),
        ("Regular Italic", (None, "Italic")),
        ("Roman", ("Roman", None)),
        ("Roman Italic", ("Roman", "Italic")),
        ("Book", ("Book", None)),
        ("Normal", ("Normal", None)),
        ("Plain", ("Plain", None)),
        ("Medium", ("Medium", None)),
        ("Light", ("Light", None)),
        ("Text", ("Text", None)),
        ("Light Italic", ("Light", "Italic")),
        ("Book Oblique", ("Book", "Oblique")),
    ],
)
def test_id1_style_drops_only_regular(style, expected):
    assert normalize(style, None) == expected


@pytest.mark.parametrize("word", ["Roman", "Book", "Normal", "Plain", "Medium", "Light"])
def test_equivalents_stay_in_id1(word):
    assert build_id1("Probe", None, word, None) == f"Probe {word}"
