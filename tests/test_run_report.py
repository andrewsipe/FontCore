"""RunReporter: tools report facts; one place prints them in a fixed order, counts them and decides the exit code."""

import io

import pytest
from rich.console import Console

import FontCore.core_console_styles as cs
from FontCore.core_run_report import FileReport, Line, RunReporter


def console():
    buf = io.StringIO()
    return Console(file=buf, force_terminal=False, width=100, theme=cs.CUSTOM_THEME if hasattr(cs, "CUSTOM_THEME") else None), buf


def text(buf):
    return "\n".join(l.rstrip() for l in buf.getvalue().splitlines())


def test_a_file_block_is_header_then_changes_then_result():
    con, buf = console()
    r = RunReporter(console=con, total=3)
    report = FileReport(
        name="A-Regular.otf",
        changes=[("OS/2", ["- fsType: 4 -> 0"]), ("glyphs", ["- nbsp_width: 168 -> 188"])],
        lines=[Line("unchanged", "Already compliant: kern"), Line("saved", file="A-Regular.otf")],
        outcome="updated",
    )
    r.file(1, report)
    lines = [l for l in text(buf).splitlines() if l.strip()]
    kinds = [l.split()[0] for l in lines]
    assert kinds[0] == "PARSING" and "File 1 of 3" in lines[0] and "A-Regular.otf" in lines[0]
    assert [l for l in lines if l.lstrip().startswith("UPDATED")] and "- fsType: 4 -> 0" in text(buf)
    assert text(buf).index("UPDATED") < text(buf).index("NO CHANGE") < text(buf).index("SAVED TO")


def test_header_and_body_can_be_printed_separately_for_a_sequential_run():
    con, buf = console()
    r = RunReporter(console=con, total=2)
    r.header(1, "A.otf")
    assert "PARSING" in text(buf) and "SAVED" not in text(buf)
    r.body(FileReport(name="A.otf", lines=[Line("saved", file="A.otf")], outcome="updated"))
    assert "SAVED TO" in text(buf)


def test_counts_and_exit_code():
    con, _ = console()
    r = RunReporter(console=con, total=4)
    for i, outcome in enumerate(["updated", "updated", "unchanged", "error"], 1):
        r.file(i, FileReport(name=f"{i}.otf", outcome=outcome, lines=[Line("error", "bad", file=f"{i}.otf")] if outcome == "error" else []))
    assert r.counts == {"updated": 2, "unchanged": 1, "skipped": 0, "error": 1}
    assert r.exit_code() == 1


def test_a_clean_run_exits_zero():
    con, _ = console()
    r = RunReporter(console=con, total=1)
    r.file(1, FileReport(name="a.otf", outcome="updated"))
    assert r.exit_code() == 0


def test_the_summary_is_one_sentence_and_one_chip():
    con, buf = console()
    r = RunReporter(console=con, total=5)
    for i, o in enumerate(["updated"] * 3 + ["unchanged", "error"], 1):
        r.file(i, FileReport(name=f"{i}.otf", outcome=o))
    buf.truncate(0); buf.seek(0)
    r.summary()
    out = " ".join(text(buf).split())
    assert "Updated 3, unchanged 1, 1 problem." in out
    r2_con, r2_buf = console()
    r2 = RunReporter(console=r2_con, total=1)
    r2.file(1, FileReport(name="a", outcome="updated"))
    r2_buf.truncate(0); r2_buf.seek(0)
    r2.summary()
    assert "Updated 1, unchanged 0, no problems." in " ".join(text(r2_buf).split())


def test_summary_words_can_be_the_tools_own():
    con, buf = console()
    r = RunReporter(console=con, total=2, verbs={"updated": "Renamed", "unchanged": "kept", "skipped": "skipped", "error": "problem"})
    r.file(1, FileReport(name="a", outcome="updated"))
    r.file(2, FileReport(name="b", outcome="skipped"))
    buf.truncate(0); buf.seek(0)
    r.summary()
    assert "Renamed 1, kept 0, skipped 1, no problems." in " ".join(text(buf).split())


def test_nothing_is_printed_until_asked_and_no_ansi_when_not_a_terminal():
    con, buf = console()
    r = RunReporter(console=con, total=1)
    assert buf.getvalue() == ""
    r.file(1, FileReport(name="a.otf", outcome="updated", changes=[("OS/2", ["- x: 1 -> 2"])]))
    assert "\x1b[" not in buf.getvalue()


def test_extra_notes_print_inside_the_block():
    con, buf = console()
    r = RunReporter(console=con, total=1)
    r.file(1, FileReport(name="a.otf", outcome="updated", lines=[Line("info", "kern table removed")]))
    out = text(buf)
    assert out.index("PARSING") < out.index("kern table removed")


@pytest.mark.parametrize("bad", ["weird", ""])
def test_an_unknown_outcome_is_an_error_not_a_crash(bad):
    con, _ = console()
    r = RunReporter(console=con, total=1)
    r.file(1, FileReport(name="a", outcome=bad))
    assert r.counts["error"] == 1 and r.exit_code() == 1


def test_processing_summary_is_one_sentence_and_warns_on_errors():
    import io
    from rich.console import Console
    import FontCore.core_console_styles as cs

    def render(**kw):
        buf = io.StringIO()
        cs.fmt_processing_summary(console=Console(file=buf, width=100, force_terminal=False), **kw)
        return buf.getvalue()

    clean = render(updated=2, unchanged=4, errors=0)
    assert "Updated 2, unchanged 4, no problems." in clean and "SUCCESS" in clean
    bad = render(updated=0, unchanged=2, errors=2, skipped=1)
    assert "Updated 0, unchanged 2, skipped 1, 2 problems." in bad and "WARNING" in bad
    preview = render(dry_run=True, updated=3, unchanged=1, errors=1)
    assert "Would update 3, unchanged 1, 1 problem." in preview


def test_run_sentence_matches_reporter():
    import FontCore.core_console_styles as cs
    from FontCore.core_run_report import RunReporter

    assert cs.fmt_run_sentence(1, 2, 0) == "Updated 1, unchanged 2, no problems."
    r = RunReporter(total=1)
    r.counts.update(updated=1, unchanged=2)
    assert r.sentence() == cs.fmt_run_sentence(1, 2, 0)
