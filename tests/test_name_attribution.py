"""Tests for copyright/trademark attribution resolution."""

from __future__ import annotations

from datetime import datetime

from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib.tables import _g_l_y_f as glyf_module

from FontCore.core_name_attribution import (
    combine_rights_holders,
    construct_copyright,
    construct_trademark,
    extract_year_from_copyright,
    is_explicit_rights_holder_override,
    resolve_copyright_year,
    resolve_family_name_binary,
    resolve_rights_holder_binary,
)


def _minimal_font() -> object:
    fb = FontBuilder(1024, isTTF=True)
    fb.setupGlyphOrder([".notdef"])
    fb.setupCharacterMap({})
    fb.setupGlyf({".notdef": glyf_module.Glyph()})
    fb.setupHorizontalMetrics({".notdef": (600, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupOS2()
    fb.setupPost()
    fb.setupNameTable({"familyName": "Test Family", "styleName": "Regular"})
    return fb.font


def _set_win_name(font, name_id: int, string: str) -> None:
    font["name"].setName(string, name_id, 3, 1, 0x0409)


class TestRightsHolderResolution:
    def test_combines_manufacturer_and_designer(self):
        font = _minimal_font()
        _set_win_name(font, 8, "Acme Foundry LLC")
        _set_win_name(font, 9, "Jane Designer")
        assert resolve_rights_holder_binary(font) == "Acme Foundry LLC & Jane Designer"

    def test_dedupes_identical_manufacturer_and_designer(self):
        assert combine_rights_holders("Acme LLC", "Acme LLC") == "Acme LLC"

    def test_falls_back_to_designer(self):
        font = _minimal_font()
        _set_win_name(font, 9, "Jane Designer")
        assert resolve_rights_holder_binary(font) == "Jane Designer"

    def test_explicit_override_wins(self):
        font = _minimal_font()
        _set_win_name(font, 8, "Acme Foundry LLC")
        assert resolve_rights_holder_binary(font, "Custom Holder") == "Custom Holder"

    def test_placeholder_override_is_not_explicit(self):
        assert not is_explicit_rights_holder_override("designer")
        assert is_explicit_rights_holder_override("Real Co")


class TestFamilyResolution:
    def test_prefers_id16_over_id1(self):
        font = _minimal_font()
        _set_win_name(font, 16, "Muller")
        _set_win_name(font, 1, "Muller Next Variable Roman")
        assert resolve_family_name_binary(font) == "Muller"

    def test_filename_stem_fallback(self):
        font = _minimal_font()
        font["name"].names[:] = [
            r for r in font["name"].names if r.nameID not in (1, 16)
        ]
        assert (
            resolve_family_name_binary(font, filepath="MullerNext-Bold.ttf")
            == "MullerNext-Bold"
        )


class TestConstructedStrings:
    def test_trademark_matches_common_notice(self):
        assert (
            construct_trademark("Muller", "Fontfabric LLC")
            == "Muller is a trademark of Fontfabric LLC."
        )

    def test_copyright_template(self):
        assert (
            construct_copyright(2022, "Fontfabric LLC")
            == "Copyright © 2022 by Fontfabric LLC. All rights reserved."
        )


class TestCopyrightYear:
    def test_extract_year_from_existing_notice(self):
        text = "Copyright © 2022 by Fontfabric LLC. All rights reserved."
        assert extract_year_from_copyright(text) == 2022

    def test_resolve_year_priority(self):
        now = datetime.now().year
        assert (
            resolve_copyright_year(
                manual_year=2019,
                head_year=2020,
                existing_copyright_year=2021,
                default_year=now,
            )
            == 2019
        )
        assert (
            resolve_copyright_year(
                head_year=2020,
                existing_copyright_year=2021,
                default_year=now,
            )
            == 2020
        )
        assert (
            resolve_copyright_year(
                existing_copyright_year=2021,
                default_year=now,
            )
            == 2021
        )
