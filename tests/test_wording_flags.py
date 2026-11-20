"""The flag list shown before a run names the real flags and shows the ones that were set."""

from __future__ import annotations

import builtins
import re
from types import SimpleNamespace

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

import FontCore.core_console_styles as cs
from FontCore.core_nameid_replacer_base import run_workflow


def _font(path, mac=False):
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef"])
    fb.setupCharacterMap({})
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph()})
    fb.setupHorizontalMetrics({".notdef": (500, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Probe", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    if mac:
        for name_id, text in ((1, "Probe"), (2, "Regular")):
            fb.font["name"].setName(text, name_id, 1, 0, 0)
    fb.save(path)
    return path


def _run(tmp_path, capsys, **flags):
    font = _font(tmp_path / "Probe-Regular.ttf")
    args = SimpleNamespace(
        dry_run=True,
        yes=True,
        recursive=False,
        filename_parser=False,
        delete_mac_records=False,
        empty_fields_only=False,
        **flags,
    )
    run_workflow(
        file_paths=[str(font)],
        script_args=args,
        process_file_fn=lambda *a, **k: False,
        title="Name ID 8 Replacer",
        name_id=8,
        description="Manufacturer",
        operations=["Replace nameID 8 (Manufacturer) with: Acme"],
    )
    return capsys.readouterr().out


def test_active_flags_use_the_real_flag_names(tmp_path, capsys):
    out = _run(tmp_path, capsys, **{})  # dry_run, yes
    assert "-n, --dry-run" in out
    assert "-y, --yes" in out
    assert not re.search(r"(?<!-)-dry\b", out)  # "-dry" was never a flag
    assert "--confirm" not in out


def test_recursive_is_listed_as_lowercase_r(tmp_path, capsys):
    font = _font(tmp_path / "Probe-Regular.ttf")
    args = SimpleNamespace(
        dry_run=True, yes=True, recursive=True, filename_parser=False,
        delete_mac_records=False, empty_fields_only=False,
    )
    run_workflow([str(font)], args, lambda *a, **k: False, "T", 8, "Manufacturer", [])
    out = capsys.readouterr().out
    assert "-r, --recursive" in out
    assert "-R," not in out


def test_unset_flags_are_not_listed(tmp_path, capsys, monkeypatch):
    font = _font(tmp_path / "Probe-Regular.ttf")
    args = SimpleNamespace(
        dry_run=False, yes=False, recursive=False, filename_parser=False,
        delete_mac_records=False, empty_fields_only=False,
    )
    # not dry-run and not -y: the run stops at the confirmation, where we answer no
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "n")
    run_workflow([str(font)], args, lambda *a, **k: False, "T", 8, "Manufacturer", [])
    out = capsys.readouterr().out
    assert "--dry-run" not in out
    assert "--yes" not in out


def test_plain_text_prompt_prints_no_markup(monkeypatch, capsys):
    monkeypatch.setattr(cs, "RICH_AVAILABLE", False)
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "y")
    assert cs.prompt_confirm("About to change 2 files.", allow_quit=True) is True
    out = capsys.readouterr().out
    assert "About to change 2 files." in out
    assert "(y/N/q)" in out
    assert "[input]" not in out and "[bold]" not in out and "[/" not in out


# --- wording: header, plan block, deletion summary -------------------------------------------


def test_header_names_the_record_not_the_script(tmp_path, capsys):
    out = _run(tmp_path, capsys)
    assert "Manufacturer (nameID 8)" in out
    assert "Processing nameID=" not in out
    assert "Replacer" not in out


def test_plan_block_has_no_script_line_for_replacers(tmp_path, capsys):
    out = _run(tmp_path, capsys)
    assert "Before starting:" in out
    assert "This will:" in out
    assert "Script:" not in out and "Pre-flight" not in out and "Operations to perform" not in out


def test_plan_block_can_name_a_task(capsys):
    cs.fmt_preflight_checklist("Catalog Metadata Apply", ["Fill nameID 8"])
    out = capsys.readouterr().out
    assert "Task: Catalog Metadata Apply" in out
    assert "1. Fill nameID 8" in out


def test_mac_and_flag_wording_drops_platform_ids_from_status_lines(tmp_path, capsys):
    font = _font(tmp_path / "Probe-Regular.ttf")
    args = SimpleNamespace(
        dry_run=True, yes=True, recursive=False, filename_parser=False,
        delete_mac_records=True, empty_fields_only=True,
    )
    run_workflow([str(font)], args, lambda *a, **k: False, "T", 8, "Manufacturer", [])
    out = " ".join(capsys.readouterr().out.split())  # the console wraps long lines
    assert "Mac name records will be removed" in out
    assert "platformID" not in out
    assert "remove all Mac name records (platform 1) before processing" in out
    assert "fill only the blank Windows English name records; leave existing text alone" in out


def test_deletion_summary_uses_one_name_for_mac_records():
    text = cs.fmt_deletion_operation(name_ids=[1, 2], mac_records=True, windows_english_only=True)
    assert "Mac name records (platform 1)" in text
    assert "Macintosh" not in text
    assert (
        "every name record except Windows English (platform 3, encoding 1, language 0x409)"
        in text
    )


# --- plurals, prompt and summary wording ----------------------------------------------------


def _plain(text):
    return " ".join(text.split())


def test_fmt_plural_picks_the_right_form(monkeypatch):
    monkeypatch.setattr(cs, "RICH_AVAILABLE", False)
    assert cs.fmt_plural(1, "file") == "1 file"
    assert cs.fmt_plural(0, "file") == "0 files"
    assert cs.fmt_plural(3, "Mac name record") == "3 Mac name records"
    assert cs.fmt_plural(2, "family", "families") == "2 families"
    assert cs.fmt_plural(1, "family", "families") == "1 family"


def test_no_file_s_placeholders_in_a_run(tmp_path, capsys):
    font = _font(tmp_path / "Probe-Regular.ttf", mac=True)
    args = SimpleNamespace(
        dry_run=True, yes=True, recursive=False, filename_parser=False,
        delete_mac_records=True, empty_fields_only=False,
    )
    run_workflow([str(font)], args, lambda *a, **k: False, "T", 8, "Manufacturer", [])
    out = _plain(capsys.readouterr().out)
    assert "(s)" not in out
    assert "Found 1 font file:" in out
    assert "Found 2 Mac name records in 1 file - will be removed" in out
    assert "Would remove 2 Mac name records in total" in out


def test_mac_warning_without_dmr(tmp_path, capsys):
    font = _font(tmp_path / "Probe-Regular.ttf", mac=True)
    args = SimpleNamespace(
        dry_run=True, yes=True, recursive=False, filename_parser=False,
        delete_mac_records=False, empty_fields_only=False,
    )
    run_workflow([str(font)], args, lambda *a, **k: False, "T", 8, "Manufacturer", [])
    out = _plain(capsys.readouterr().out)
    assert "Found 2 Mac name records in 1 file" in out
    assert "Use -dmr to remove them before processing." in out
    assert "Macintosh" not in out and "cleaner results" not in out


def test_confirmation_asks_proceed_once(tmp_path, capsys, monkeypatch):
    font = _font(tmp_path / "Probe-Regular.ttf")
    args = SimpleNamespace(
        dry_run=False, yes=False, recursive=False, filename_parser=False,
        delete_mac_records=False, empty_fields_only=False,
    )
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "n")
    run_workflow([str(font)], args, lambda *a, **k: False, "T", 8, "Manufacturer", [])
    out = _plain(capsys.readouterr().out)
    assert "About to modify 1 file." in out
    assert out.count("Proceed?") == 1


def test_summary_says_finished_without_an_exclamation_mark(tmp_path, capsys):
    font = _font(tmp_path / "Probe-Regular.ttf")
    args = SimpleNamespace(
        dry_run=False, yes=True, recursive=False, filename_parser=False,
        delete_mac_records=False, empty_fields_only=False,
    )
    run_workflow([str(font)], args, lambda *a, **k: False, "T", 8, "Manufacturer", [])
    out = capsys.readouterr().out
    assert "Finished" in out
    assert "Completed!" not in out


def test_no_fonts_found_message(tmp_path, capsys):
    args = SimpleNamespace(
        dry_run=True, yes=True, recursive=False, filename_parser=False,
        delete_mac_records=False, empty_fields_only=False,
    )
    run_workflow([str(tmp_path)], args, lambda *a, **k: False, "T", 8, "Manufacturer", [])
    out = _plain(capsys.readouterr().out)
    assert "No font files found." in out
    assert "to process" not in out


def test_error_summary_does_not_shout():
    from FontCore.core_error_handling import ErrorContext, ErrorInfo

    info = ErrorInfo(context=ErrorContext.FILE_IO, message="could not read", recoverable=False)
    text = info.to_log_message()
    assert "Recoverable: no" in text
    assert "Recoverable: NO" not in text
