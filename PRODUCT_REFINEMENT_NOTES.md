# Product refinement notes — FontCore

Captured during the 2026-08-21 declutter pass. Use for a later product/release pass. **Not** user-facing docs.

## Declutter verdict

**Nothing to archive.** FontCore is the shared library every Python tool depends on. Modules are either imported by sibling projects, used by other core modules, demoted via `CoreDemoTool.py`, or covered by `tests/`.

| Keep | Role |
|------|------|
| `core_*.py` | Shared APIs (console, files, names, TTX, VF, OT labels, STAT, …) |
| `CoreDemoTool.py` | Interactive showcase / smoke for core APIs (referenced from module docstrings) |
| `tests/` | Policies, catalog, namerecord, preserve-low-IDs |
| `README.md` | Library overview |

## Product-pass refinements (deferred)

1. **Distribution** — Done 2026-11-20: tools vendor the FontCore slice they need (`tools/vendor_fontcore.py`, `[tool.fontcore-vendor]` in each tool's `pyproject.toml`). Seven consumers; see the README table. Still not on PyPI, by design: a tool installs from GitHub with no FontCore step.
2. **README drift** — Addressed 2026-11-20: vendoring workflow, consumers table, the 16 previously undocumented modules.
3. **Module map** — The README now lists every module. Still missing: an explicit "who imports what" table (OT label trio is VarFontStudio/TableEditor-oriented; `core_gpos_repair` is used by Variable_Instancer). `vendor_fontcore.py` already computes the import closure and could print it.
4. **Test coverage** — Expand beyond name/catalog; OT reflow/scanner/suggest still lightly tested. `tests/test_timestamp_guard.py` now enforces `recalcTimestamp=False`.
5. **`raw_github_urls.txt`** — PushCore noise; lists the pre-`src/` flat layout. Safe to delete. (File removed and gitignored 2026-11-20.)
6. **Pins** — Done 2026-11-20: `rich` cap `<14` removed (`rich>=13`); the 95 tests pass on rich 15 and on 13. `fonttools>=4.40.0,<5` stays.
7. **`core_name_policies` / dictionaries** — `Cursive` is a slope in `core_font_style_dictionaries.py` (a style after the hyphen). A `Cursive` inside a family name never reaches the variable-filename parser. Revisit if the family-name case needs handling.

## Known open items (2026-11-20)

- **Out-of-repo consumers:** older submodule pins (e.g. `Variable_Instancer`) predate `src/FontCore/` and the vendor workflow. Use `pip install -e ../FontCore` or adopt `[tool.fontcore-vendor]`. Not checked in this pass.
- **FontExtractor2** no longer depends on a `fontcore` wheel; it vendors 14 modules like the others.
- **Version stamps:** FontFixer, Ebrium, FontCatalyst and FileRenamer still say FontCore v0.2.0 in `FontCore/VENDOR.md`; their module contents are identical to v0.2.1 (`check` reports in sync).

## Do not lose

- Name policies + variable filename dialects (static-aligned vs legacy width-in-family).
- Console `StatusIndicator` contract used across CLIs.
- TTX/binary name + fvar/STAT helpers used by NameID / VFS tooling.
- CoreDemoTool expectation when extending modules (docstring convention).
