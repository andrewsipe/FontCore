# FontCore

Shared utilities for the font tools: console output, file collection, filename and name-table policies, TTX helpers. It keeps the tools consistent with each other (same look, same file-collection rules, same naming decisions).

Declutter / product-pass notes: see `PRODUCT_REFINEMENT_NOTES.md`.

## How the tools use it

Each tool **vendors** the slice of FontCore it needs, so a tool installs from GitHub on its own: no symlink, no sibling clone, no extra install step. A tool lists its modules in its own `pyproject.toml`:

```toml
[tool.fontcore-vendor]
modules = ["core_console_styles", "core_file_collector"]
```

and `tools/vendor_fontcore.py` copies those modules, plus every FontCore module they import, into the tool's `FontCore/` folder and records which FontCore commit it came from in `FontCore/VENDOR.md`:

```bash
python tools/vendor_fontcore.py check            # every sibling project with the table (read-only)
python tools/vendor_fontcore.py check ../Ebrium  # one project
python tools/vendor_fontcore.py sync ../Ebrium   # copy, stamp, remove stale modules
```

`check` exits 1 when a project is out of sync. For each differing file it says whether the vendored copy is **BEHIND** FontCore (it matches an older revision) or has **LOCAL CHANGES** (it matches no revision; fold the fix back into FontCore). Never edit a vendored copy; fix it here, tag, and re-sync.

Workflow for a change: edit `src/FontCore/`, run the tests, bump `version` in `pyproject.toml` and `src/FontCore/__init__.py`, commit, tag `vX.Y.Z`, then `sync` the consumers whose modules changed (`check` shows which) and release them.

### Consumers (as of 2026-11-25, FontCore 0.7.0)

| Tool | Version | FontCore it carries | Modules declared → vendored |
|---|---|---|---|
| [FontNameID](https://github.com/andrewsipe/FontNameID) (`fontnameid`) | 0.7.1 | 0.7.0 | 12 → 16 |
| [FontFixer](https://github.com/andrewsipe/FontFixer) | 1.4.3 | 0.7.0 | 4 → 4 |
| [Filename_Tools](https://github.com/andrewsipe/Filename_Tools) (`filenametools`) | 0.4.1 | 0.7.0 | 3 → 5 |
| [Ebrium](https://github.com/andrewsipe/Ebrium) | 4.1.0 | 0.7.0 | 6 → 6 |
| [FontCatalyst](https://github.com/andrewsipe/FontCatalyst) | 1.4.0 | 0.7.0 | 5 → 5 |
| [FileRenamer](https://github.com/andrewsipe/FileRenamer) (`fontrenamer`) | 0.4.1 | 0.7.0 | 9 → 14 |
| [FontExtractor2](https://github.com/andrewsipe/FontExtractor2) | 0.2.2 | 0.2.1 (behind) | 8 → 14 |

Run `python tools/vendor_fontcore.py check` for the live answer; this table is a snapshot.

### Conventions that the tests enforce

- **Fonts keep their `head.modified` timestamp.** fontTools stamps the current time on every save unless the font was opened with `recalcTimestamp=False`. `tests/test_timestamp_guard.py` fails when a `TTFont(...)` open omits the flag; read-only opens are listed by function name in that test.
- **Python 3.10+, `fonttools` and `rich` only.** No optional prompt UI packages (the old `use_questionary` setting is `False` and unused).

## Layout

Installable package under `src/FontCore/` (import name **`FontCore`**, distribution name **`fontcore`**):

```
FontCore/
  pyproject.toml
  src/FontCore/          # import package: core_*.py
  tests/
  tools/vendor_fontcore.py
  CoreDemoTool.py
```

## Developing FontCore itself

```bash
cd FontCore
python3 -m pip install -e ".[dev]"
pytest
```

### Wording

The words people read (help text, messages, prompts, docs) follow the rules in `.claude/skills/cli-writing/SKILL.md`: who the reader is, the voice, standard flag wording, and a short list of preferred terms. It applies to every tool in the set.

Not on PyPI. A tool under development can use this checkout directly with `pip install -e ../FontCore`; released tools use their vendored copy instead.

## Overview

Modules live in `src/FontCore/` as `core_*.py`:

- **Console styling** - Unified output formatting with rich text support
- **File collection** - Font file discovery and filtering
- **Font parsing** - Filename and metadata parsing utilities
- **Name policies** - Font naming conventions and sanitization
- **Error handling** - Consistent error tracking and reporting
- **Font sorting** - Font family organization and sorting
- **TTX operations** - XML-based font table manipulation

## Modules

### `core_console_styles.py`
Primary console output module providing:
- `StatusIndicator` class for unified status messages
- Formatted tables, panels, and progress bars
- Color-coded labels (updated, unchanged, error, warning, etc.)
- Automatic Rich library detection with fallback to plain text

**Usage:**
```python
import FontCore.core_console_styles as cs
console = cs.get_console()
cs.StatusIndicator("updated").add_message("File processed").emit(console)
```

### `core_file_collector.py`
Font file discovery and collection:
- Recursive directory scanning
- Support for TTF, OTF, WOFF, WOFF2 formats
- File filtering and validation
- Iterator and list-based collection methods

**Usage:**
```python
from FontCore.core_file_collector import collect_font_files
fonts = collect_font_files("/path/to/fonts", recursive=True)
```

### `core_filename_parts_parser.py`
Parses font filenames into structured components:
- Family name extraction
- Style name parsing
- Width, weight, and optical size detection
- Variable font token handling

**Usage:**
```python
from FontCore.core_filename_parts_parser import parse_filename
parts = parse_filename("Helvetica-Bold.otf")
# Returns: FontParts object with family, style, etc.
```

### `core_font_sorter.py`
Font family organization and sorting:
- Groups fonts by family
- Sorts by weight, width, and style
- Creates FontInfo objects for metadata access

**Usage:**
```python
from FontCore.core_font_sorter import FontSorter, create_font_info_from_paths
sorter = FontSorter()
fonts = create_font_info_from_paths(["/path/to/font.otf"])
sorted_families = sorter.sort_fonts(fonts)
```

### `core_name_policies.py`
Font naming conventions and sanitization:
- PostScript name generation
- NameID table value builders
- Unicode normalization
- Variable font token stripping

**Usage:**
```python
from FontCore.core_name_policies import build_id1, sanitize_postscript
family_name = build_id1("Helvetica", "Bold")
ps_name = sanitize_postscript("Helvetica-Bold")
```

### `core_ttx_table_io.py`
TTX (XML) table manipulation:
- Read/write font tables as XML
- NameID record deduplication
- Table validation and repair

### `core_nameid_replacer_base.py`
Base classes for NameID replacement scripts:
- Common processing workflow
- Statistics tracking
- Error handling patterns

### `core_error_handling.py`
Error tracking and context management:
- ErrorTracker class for batch operations
- ErrorContext for detailed error reporting

### `core_logging_config.py`
Logging configuration:
- Structured logging setup
- Verbosity levels
- Log file management

### `core_string_utils.py`
String manipulation utilities:
- Empty string normalization
- Non-empty string joining
- Unicode handling

### `core_variable_font_detection.py`
Variable font detection and analysis:
- Variable font identification
- Axis extraction
- Instance enumeration

### `core_font_style_dictionaries.py`
Style word dictionaries:
- Width terms (Condensed, Extended, etc.)
- Weight terms (Light, Bold, etc.)
- Optical size terms
- Compound word normalizations

### Other modules

| Module | Purpose |
|---|---|
| `core_cli_help.py` | Rich-styled `--help` building blocks shared by FontFixer, Ebrium and FontCatalyst |
| `core_console_config.py` | Console theme, labels and settings used by `core_console_styles` |
| `core_font_extension.py` | Detect the real font format from magic bytes; validate and fix file extensions |
| `core_font_metadata.py` | Extract PostScript names, version, vendor ID and format from font files |
| `core_font_utils.py` | Validate PostScript names; sanitize folder and filename strings |
| `core_gpos_repair.py` | GPOS PairPos repairs needed by the fontTools varLib instancer |
| `core_metadata_catalog.py` | Load and query typographer.com family metadata JSON catalogs |
| `core_name_attribution.py` | Resolve copyright and trademark attribution from metadata and CLI overrides |
| `core_nameid_allocator.py` | NameID audit and allocation for variable-font STAT/fvar editing |
| `core_namerecord_matcher.py` | Match name records in TTX and binary fonts through one interface |
| `core_namerecord_writer.py` | Silent, library-friendly writers for Windows English (3/1/0x409) name records |
| `core_ot_label_reflow.py` | Scan, classify, remap and patch OpenType feature-label nameIDs in GSUB/GPOS |
| `core_ot_label_scanner.py` | Walk GSUB/GPOS FeatureParams for feature-label nameIDs |
| `core_ot_label_suggest.py` | Conservative stylistic-set label suggestions (returns `None` rather than guess) |
| `core_stat_builder.py` | Write STAT axis values, fvar named instances and related name entries |
| `core_variable_filename_parser.py` | Parse variable-font filenames into semantic slots (static-aligned and legacy dialects) |

## Demo Tool

Run `CoreDemoTool.py` from the FontCore repo root (with the package on `PYTHONPATH` or installed editable):

```bash
PYTHONPATH=src python CoreDemoTool.py console
PYTHONPATH=src python CoreDemoTool.py sorter /path/to/fonts/
PYTHONPATH=src python CoreDemoTool.py parser "Helvetica-Bold.otf"
PYTHONPATH=src python CoreDemoTool.py all
```

## Usage in tools

```python
import FontCore.core_console_styles as cs
from FontCore.core_file_collector import collect_font_files
from FontCore.core_filename_parts_parser import parse_filename
```

Inside a tool this import resolves to the tool's own vendored `FontCore/` folder.
