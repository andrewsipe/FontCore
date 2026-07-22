"""Tests for the silent binary name-record writer."""

from __future__ import annotations

from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib.tables import _g_l_y_f as glyf_module
from fontTools.ttLib.tables._n_a_m_e import NameRecord

from FontCore.core_namerecord_writer import (
    apply_name_values_binary,
    is_blank_name_value,
    upsert_win_en_name_binary,
)


def _minimal_font():
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


def _win_value(font, name_id):
    for record in font["name"].names:
        if (
            record.nameID == name_id
            and record.platformID == 3
            and record.platEncID == 1
            and record.langID == 0x409
        ):
            return record.toUnicode()
    return None


def test_create_new_record():
    font = _minimal_font()
    result = upsert_win_en_name_binary(font, 8, "Dave Rowland Type")
    assert result.created is True
    assert result.changed is True
    assert result.old_value is None
    assert _win_value(font, 8) == "Dave Rowland Type"


def test_update_existing_record():
    font = _minimal_font()
    font["name"].setName("Old Mfg", 8, 3, 1, 0x409)
    result = upsert_win_en_name_binary(font, 8, "New Mfg")
    assert result.created is False
    assert result.changed is True
    assert result.old_value == "Old Mfg"
    assert _win_value(font, 8) == "New Mfg"


def test_unchanged_when_value_matches():
    font = _minimal_font()
    font["name"].setName("Same", 8, 3, 1, 0x409)
    result = upsert_win_en_name_binary(font, 8, "Same")
    assert result.changed is False
    assert result.created is False
    assert result.old_value == "Same"


def test_empty_fields_only_preserves_existing():
    font = _minimal_font()
    font["name"].setName("Keep Me", 9, 3, 1, 0x409)
    result = upsert_win_en_name_binary(font, 9, "Override", empty_fields_only=True)
    assert result.changed is False
    assert _win_value(font, 9) == "Keep Me"


def test_empty_fields_only_fills_blank():
    font = _minimal_font()
    font["name"].setName("   ", 9, 3, 1, 0x409)
    result = upsert_win_en_name_binary(font, 9, "Designer", empty_fields_only=True)
    assert result.changed is True
    assert _win_value(font, 9) == "Designer"


def test_dedupe_on_write():
    font = _minimal_font()
    for _ in range(3):
        rec = NameRecord()
        rec.nameID = 10
        rec.platformID = 3
        rec.platEncID = 1
        rec.langID = 0x409
        rec.string = "dupe"
        font["name"].names.append(rec)
    upsert_win_en_name_binary(font, 10, "Description")
    matches = [
        r
        for r in font["name"].names
        if r.nameID == 10 and r.platformID == 3 and r.platEncID == 1 and r.langID == 0x409
    ]
    assert len(matches) == 1
    assert _win_value(font, 10) == "Description"


def test_apply_name_values_binary_multiple():
    font = _minimal_font()
    results = apply_name_values_binary(
        font,
        {8: "Foundry", 9: "Designer", 10: "Desc"},
    )
    assert {r.name_id for r in results} == {8, 9, 10}
    assert all(r.changed for r in results)
    assert _win_value(font, 8) == "Foundry"
    assert _win_value(font, 9) == "Designer"
    assert _win_value(font, 10) == "Desc"


def test_apply_skips_none_values():
    font = _minimal_font()
    results = apply_name_values_binary(font, {8: "Foundry"})
    assert len(results) == 1


def test_is_blank_name_value():
    assert is_blank_name_value(None)
    assert is_blank_name_value("   ")
    assert not is_blank_name_value("x")
