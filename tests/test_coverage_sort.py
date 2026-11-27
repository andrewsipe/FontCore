"""The Coverage sorter moves the arrays that run parallel to a Coverage, so no glyph ends up with another glyph's data."""

from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import newTable
from fontTools.ttLib.tables import otTables as ot

from FontCore.core_coverage_sort import sort_coverage_tables_in_font


def _font():
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef", "A", "B", "C", "D"])
    fb.setupCharacterMap({65: "A"})
    return fb.font


def _gpos(font, subtable):
    lookup = ot.Lookup()
    lookup.LookupType, lookup.LookupFlag, lookup.SubTable, lookup.SubTableCount = 4, 0, [subtable], 1
    gpos = newTable("GPOS")
    gpos.table = ot.GPOS()
    gpos.table.LookupList = ot.LookupList()
    gpos.table.LookupList.Lookup, gpos.table.LookupList.LookupCount = [lookup], 1
    font["GPOS"] = gpos
    return gpos


def _cov(*glyphs):
    c = ot.Coverage()
    c.glyphs = list(glyphs)
    return c


def test_a_base_coverage_out_of_order_moves_its_base_records_with_it():
    font = _font()
    st = ot.MarkBasePos()
    st.Format = 1
    st.MarkCoverage = _cov("A")
    st.BaseCoverage = _cov("C", "B", "D")
    st.BaseArray = ot.BaseArray()
    st.BaseArray.BaseRecord = ["rec-C", "rec-B", "rec-D"]
    _gpos(font, st)
    _, sorted_count = sort_coverage_tables_in_font(font)
    assert sorted_count == 1
    assert st.BaseCoverage.glyphs == ["B", "C", "D"]
    assert st.BaseArray.BaseRecord == ["rec-B", "rec-C", "rec-D"]


def test_a_mark_coverage_out_of_order_moves_its_mark_records_with_it():
    font = _font()
    st = ot.MarkBasePos()
    st.Format = 1
    st.MarkCoverage = _cov("D", "A")
    st.MarkArray = ot.MarkArray()
    st.MarkArray.MarkRecord = ["rec-D", "rec-A"]
    st.BaseCoverage = _cov("B")
    st.BaseArray = ot.BaseArray()
    st.BaseArray.BaseRecord = ["rec-B"]
    _gpos(font, st)
    sort_coverage_tables_in_font(font)
    assert st.MarkCoverage.glyphs == ["A", "D"] and st.MarkArray.MarkRecord == ["rec-A", "rec-D"]


def test_a_coverage_whose_array_does_not_match_is_left_alone():
    font = _font()
    st = ot.MarkBasePos()
    st.Format = 1
    st.MarkCoverage = _cov("A")
    st.BaseCoverage = _cov("C", "B")
    st.BaseArray = ot.BaseArray()
    st.BaseArray.BaseRecord = ["only-one"]
    _gpos(font, st)
    _, sorted_count = sort_coverage_tables_in_font(font)
    assert sorted_count == 0 and st.BaseCoverage.glyphs == ["C", "B"]


def test_a_sorted_coverage_counts_as_nothing_to_do():
    font = _font()
    st = ot.MarkBasePos()
    st.Format = 1
    st.MarkCoverage = _cov("A")
    st.BaseCoverage = _cov("B", "C")
    st.BaseArray = ot.BaseArray()
    st.BaseArray.BaseRecord = ["rec-B", "rec-C"]
    _gpos(font, st)
    assert sort_coverage_tables_in_font(font)[1] == 0


def test_the_load_watch_sees_fonttools_repairing_an_unsorted_coverage():
    import logging

    from FontCore.core_coverage_sort import watch_unsorted_coverage

    with watch_unsorted_coverage() as watch:
        logging.getLogger("fontTools.ttLib.tables.otTables").warning("GSUB/GPOS Coverage is not sorted by glyph ids.")
    assert watch.fired
    with watch_unsorted_coverage() as quiet:
        pass
    assert not quiet.fired


def test_the_report_callback_gets_the_summary_line():
    font = _font()
    st = ot.MarkBasePos()
    st.Format = 1
    st.MarkCoverage = _cov("A")
    st.BaseCoverage = _cov("C", "B")
    st.BaseArray = ot.BaseArray()
    st.BaseArray.BaseRecord = ["rec-C", "rec-B"]
    _gpos(font, st)
    lines = []
    sort_coverage_tables_in_font(font, report=lines.append)
    assert any("sorted 1" in line for line in lines)
