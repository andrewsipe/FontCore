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

1. **Public package** — `pyproject.toml` + `src/FontCore/` layout landed (distribution `fontcore`). Still not published to PyPI; consumers can path/git install.
2. **README drift** — Addressed: modules live under `src/FontCore/` as `core_*.py`.
3. **Module map** — Generate/keep an explicit “who imports what” table for release docs (OT label trio is VarFontStudio/TableEditor-oriented; `core_gpos_repair` used by Variable_Instancer).
4. **Test coverage** — Expand beyond name/catalog; OT reflow/scanner/suggest still lightly tested.
5. **`raw_github_urls.txt`** — PushCore noise.

## Known open items (2026-10 migration review)

- **1 failing test:** `tests/test_variable_name_policies.py::test_parse_variable_filename_fixtures[FL_Rare-VariableCursive.ttf…]` — fixture expects `Cursive` as `bespoke`, parser returns it as `slope` (`Cursive` is in the slope dictionary in `core_font_style_dictionaries.py`). Decide which is right, then fix the fixture or the dictionary. Pre-existing; not caused by the `src/` move.
- **Consumers still pinned to the old flat layout:** older submodule pins (e.g. `Variable_Instancer`) predate `src/FontCore/`. Use the editable install below instead of submodules.
- Not on PyPI; install from a sibling clone with `pip install -e ../FontCore`.

## Do not lose

- Name policies + variable filename dialects (static-aligned vs legacy width-in-family).
- Console `StatusIndicator` contract used across CLIs.
- TTX/binary name + fvar/STAT helpers used by NameID / VFS tooling.
- CoreDemoTool expectation when extending modules (docstring convention).
