"""FontMetadata records weight, slant and variable-ness so callers can tell whether two fonts could be copies of one face."""

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from FontCore.core_font_metadata import FontMetadata, extract_metadata


def make(path, *, weight=400, fs=0, mac=0):
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef"])
    fb.setupCharacterMap({})
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Probe", "styleName": "Regular"})
    fb.setupOS2(usWeightClass=weight, fsSelection=fs)
    fb.setupPost()
    fb.font["head"].macStyle = mac
    fb.save(path)
    return path


def test_weight_is_recorded(tmp_path):
    m = extract_metadata(make(tmp_path / "a.ttf", weight=700))
    assert m.weight_class == 700 and m.is_italic is False and m.is_variable is False


def test_italic_comes_from_fsselection_oblique_or_macstyle(tmp_path):
    assert extract_metadata(make(tmp_path / "a.ttf", fs=0x01)).is_italic is True
    assert extract_metadata(make(tmp_path / "b.ttf", fs=0x200)).is_italic is True
    assert extract_metadata(make(tmp_path / "c.ttf", mac=0x02)).is_italic is True


def test_old_saved_metadata_without_the_new_fields_still_loads():
    m = FontMetadata.from_dict(
        {"ps_name": "X", "font_revision": 1.0, "version_string": "", "file_size": 1, "glyph_count": 1,
         "head_created": None, "head_modified": None, "file_path": "x"}
    )
    assert m.weight_class is None and m.is_italic is None and m.is_variable is False
