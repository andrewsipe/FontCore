# Core Library

Shared utilities library used by all font processing scripts in this project.

## Overview

The `core/` directory contains reusable modules that provide consistent functionality across all scripts:

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

## Demo Tool

Run `CoreDemoTool.py` to see examples of all core functionality:

```bash
python CoreDemoTool.py console    # Console styling demo
python CoreDemoTool.py sorter     # Font sorting demo
python CoreDemoTool.py parser     # Filename parsing demo
python CoreDemoTool.py all        # Run all demos
```

## Dependencies

See `requirements.txt` for dependencies:
- `fonttools` - Font file manipulation
- `rich` - Console styling (optional but recommended)

## Usage in Scripts

All scripts in this project import from core:

```python
import FontCore.core_console_styles as cs
from FontCore.core_file_collector import collect_font_files
from FontCore.core_filename_parts_parser import parse_filename
```

The core modules are designed to be imported directly. In standalone repositories, the `core/` directory is included directly in each project repository.

