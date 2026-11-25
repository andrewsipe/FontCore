"""Extension checks (DECISIONS.md, area 4)."""

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

from FontCore.core_font_extension import (
    describe_extension_mismatch,
    detect_font_format,
    is_readable,
    validate_and_fix_extension,
)


def make(path, *, cff=False, flavor=None):
    fb = FontBuilder(1000, isTTF=not cff)
    fb.setupGlyphOrder([".notdef"])
    fb.setupCharacterMap({})
    if cff:
        fb.setupCFF("P", {"FullName": "P"}, {".notdef": T2CharStringPen(500, None).getCharString()}, {})
    else:
        fb.setupGlyf({".notdef": TTGlyphPen(None).glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "P", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    if flavor:
        fb.font.flavor = flavor
    fb.save(path)
    return path


def test_a_wrong_extension_is_fixed(tmp_path):
    ok, new = validate_and_fix_extension(make(tmp_path / "a.otf"))
    assert (ok, new.name) == (False, "a.ttf")
    ok, new = validate_and_fix_extension(make(tmp_path / "b.ttf", cff=True))
    assert (ok, new.name) == (False, "b.otf")


def test_a_name_clash_gets_the_tilde_suffix(tmp_path):
    make(tmp_path / "c.ttf", cff=True)
    (tmp_path / "c.otf").write_bytes(b"x")
    ok, new = validate_and_fix_extension(tmp_path / "c.ttf")
    assert new.name == "c~001.otf"


def test_a_collection_is_never_renamed_into_an_extension_the_tools_skip(tmp_path):
    ttc = tmp_path / "coll.ttf"
    ttc.write_bytes(b"ttcf" + b"\0" * 20)
    ok, new = validate_and_fix_extension(ttc)
    assert ok is False and new is None and ttc.exists()  # left alone
    assert not (tmp_path / "coll.ttc").exists()
    assert "collection" in describe_extension_mismatch(ttc)


def test_describe_extension_mismatch(tmp_path):
    assert describe_extension_mismatch(make(tmp_path / "x.ttf")) is None
    msg = describe_extension_mismatch(make(tmp_path / "y.otf"))
    assert "TTF" in msg and ".otf" in msg


def test_describe_does_not_rename(tmp_path):
    f = make(tmp_path / "z.otf")
    describe_extension_mismatch(f)
    assert f.exists()


def test_a_readable_font_is_readable(tmp_path):
    assert is_readable(make(tmp_path / "r.ttf")) == (True, None)
    assert is_readable(make(tmp_path / "w.woff", flavor="woff")) == (True, None)


def test_a_valid_header_with_nothing_behind_it_is_damaged_not_valid(tmp_path):
    bad = tmp_path / "bad.ttf"
    bad.write_bytes(b"\x00\x01\x00\x00" + b"\0" * 40)
    assert detect_font_format(bad) == "TTF"  # the header alone still says TTF
    ok, reason = is_readable(bad)
    assert ok is False and reason


@pytest.mark.parametrize("data", [b"", b"abc", b"\x00\x01\x00\x00"])
def test_empty_and_tiny_files_are_damaged(tmp_path, data):
    f = tmp_path / "t.ttf"
    f.write_bytes(data)
    assert is_readable(f)[0] is False


def test_a_missing_file_is_not_readable(tmp_path):
    ok, reason = is_readable(tmp_path / "nope.ttf")
    assert ok is False and "exist" in reason.lower()
