#!/usr/bin/env python3
"""
Core Libraries Demo Tool

Showcases all core library functions with consistent console styling.
Supports real file processing and subcommand-based interface.

Usage:
    python core_demo_tool.py <subcommand> [options] [files...]

Subcommands:
    sorter      Demo font sorting with real files
    parser      Demo name parsing with real files
    collector   Demo file collection
    policies    Demo name policies
    ttx         Demo TTX operations
    console     Demo console styling capabilities
    all         Run all demos (with dummy data)

Examples:
    python core_demo_tool.py sorter /path/to/fonts/ --superfamily --info
    python core_demo_tool.py parser "Helvetica-Bold.otf" "Times-Italic.ttf"
    python core_demo_tool.py console
    python core_demo_tool.py all
"""

import argparse
from pathlib import Path
from typing import List

import FontCore.core_console_styles as cs
from FontCore.core_font_sorter import FontSorter, create_font_info_from_paths
from FontCore.core_filename_parts_parser import parse_filename, format_pascal_words
from FontCore.core_file_collector import collect_font_files, SUPPORTED_EXTENSIONS
from FontCore.core_name_policies import (
    build_id1,
    build_id4,
    sanitize_postscript,
    strip_variable_tokens,
)

console = cs.get_console()


def demo_console_styles():
    """Demo console styling capabilities."""
    cs.print_panel("Console Styles Demo", title="Console Styles Demo")

    """Print a comprehensive showcase of all labels and formatting helpers."""
    console = cs.get_console()

    # Header
    cs.fmt_header("Console Styles Demo - Complete Feature Showcase", console)
    cs.emit("")

    # All Labels
    cs.emit(
        "\n\n[bold deep_sky_blue1]═══ All Available Labels ═══[/bold deep_sky_blue1]\n"
        if cs.RICH_AVAILABLE
        else "=== All Available Labels ==="
    )
    cs.emit(f"{cs.INFO_LABEL} Information message")
    cs.emit(f"{cs.UPDATED_LABEL} Record updated successfully")
    cs.emit(f"{cs.UNCHANGED_LABEL} No changes detected")
    cs.emit(f"{cs.ERROR_LABEL} Error condition occurred")
    cs.emit(f"{cs.WARNING_LABEL} Warning message")
    cs.emit(f"{cs.SAVED_LABEL} File saved successfully")
    cs.emit(f"{cs.CREATED_LABEL} New record created")
    cs.emit(f"{cs.INPUT_LABEL} User input prompt")
    cs.emit(f"{cs.PARSING_LABEL} {cs.fmt_file('font.otf')}")
    cs.emit(f"{cs.SUCCESS_LABEL} Operation completed successfully")
    cs.emit(f"{cs.SKIPPED_LABEL} Font file skipped")
    cs.emit(f"{cs.DUPLICATE_LABEL} Duplicate detected (same size)")
    cs.emit(f"{cs.CACHE_LABEL} Processing cache buffer")
    cs.emit(f"{cs.DISCOVERED_LABEL} Font mapping discovered")
    cs.emit(f"{cs.MAPPING_LABEL} Applying name from CSS")
    cs.emit("")

    # Indentation Hierarchy
    cs.emit(
        "\n\n[bold deep_sky_blue1]═══ Indentation Hierarchy ═══[/bold deep_sky_blue1]\n"
        if cs.RICH_AVAILABLE
        else "=== Indentation Hierarchy ==="
    )
    cs.emit(f"{cs.INFO_LABEL} Root level item")
    cs.emit(f"{cs.indent(1)}→ Level 1: immediate details (12 spaces)")
    cs.emit(f"{cs.indent(2)}→ Level 2: sub-items (14 spaces)")
    cs.emit(f"{cs.indent(3)}→ Level 3: sub-sub-items (16 spaces)")
    cs.emit(f"{cs.indent(1, 4)}→ Level 1 with 4 extra spaces (16 total)")
    cs.emit("")

    # Change Formatting
    cs.emit(
        "\n\n[bold deep_sky_blue1]═══ Change Highlighting ═══[/bold deep_sky_blue1]\n"
        if cs.RICH_AVAILABLE
        else "=== Change Highlighting ==="
    )
    cs.emit(
        f"{cs.UPDATED_LABEL} Font family: {cs.fmt_change('OldName-Bold', 'NewName-Bold')}"
    )
    cs.emit(f"{cs.UPDATED_LABEL} Version string: {cs.fmt_change('1.000', '2.000')}")
    cs.emit(f"{cs.UPDATED_LABEL} Vendor ID: {cs.fmt_change('UKWN', 'CSTM')}")
    cs.emit("")

    # File Path Formatting
    cs.emit(
        "\n\n[bold deep_sky_blue1]═══ File Path Formatting ═══[/bold deep_sky_blue1]\n"
        if cs.RICH_AVAILABLE
        else "=== File Path Formatting ==="
    )
    cs.emit(
        f"  Basename only: {cs.fmt_file('/long/path/to/MyFont-Bold.otf', filename_only=True)}"
    )
    cs.emit(
        f"  Full path: {cs.fmt_file('/long/path/to/MyFont-Bold.otf', filename_only=False)}"
    )
    cs.emit(
        f"  Compact (alias): {cs.fmt_file_compact('/long/path/to/MyFont-Bold.otf')}"
    )
    cs.emit("")

    # Field and Value Pairs
    cs.emit(
        "\n\n[bold deep_sky_blue1]═══ Field:Value Pairs ═══[/bold deep_sky_blue1]\n"
        if cs.RICH_AVAILABLE
        else "=== Field:Value Pairs ==="
    )
    cs.emit(f"  {cs.fmt_field('nameID', 1)}")  # Integer gets field_value_number styling
    cs.emit(
        f"  {cs.fmt_field('platformID', 3)}"
    )  # Integer gets field_value_number styling
    cs.emit(f"  {cs.fmt_field('Vendor', 'UKWN')}")  # String remains plain
    cs.emit(f"  {cs.fmt_field('Version', '1.000')}")  # String remains plain
    cs.emit("")

    # Value Formatting
    cs.emit(
        "\n\n[bold deep_sky_blue1]═══ Value Emphasis ═══[/bold deep_sky_blue1]\n"
        if cs.RICH_AVAILABLE
        else "=== Value Emphasis ==="
    )
    cs.emit(f"  Plain value: {cs.fmt_value('RegularValue')}")
    cs.emit(f"  Changed value: {cs.fmt_value('ChangedValue', changed=True)}")
    cs.emit(f"  Count emphasis: Found {cs.fmt_count(42)} files")
    cs.emit(f"  Number emphasis: {cs.fmt_count(123)} records processed")
    cs.emit("")

    # Smart Underlining
    cs.emit(
        "\n\n[bold deep_sky_blue1]═══ Smart Underlining ═══[/bold deep_sky_blue1]\n"
        if cs.RICH_AVAILABLE
        else "=== Smart Underlining ==="
    )
    cs.emit("  Smart underline (skips descenders):")
    cs.emit(f"    {cs.fmt_smart_underline('Typography is groovy')}\n")
    cs.emit("  Smart underline on longer text:")
    cs.emit(
        f"    {cs.fmt_smart_underline('Foxy jump-jiving pygmies quickly gave a judge puzzling gifts')}\n"
    )
    cs.emit("  Smart underline on mixed case:")
    cs.emit(f"    {cs.fmt_smart_underline('glyph processing gjpqgy and Q')}\n")
    cs.emit("")

    # Real-World Examples
    cs.emit(
        "\n\n[bold deep_sky_blue1]═══ Real-World Usage Examples ═══[/bold deep_sky_blue1]\n"
        if cs.RICH_AVAILABLE
        else "=== Real-World Usage Examples ==="
    )
    cs.emit(f"{cs.PARSING_LABEL} {cs.fmt_file_compact('/fonts/Kalliope-Bold.otf')}")
    cs.emit(
        f"{cs.UPDATED_LABEL} {cs.fmt_field('nameID', 1)} in {cs.fmt_file_compact('/fonts/Kalliope-Bold.otf')}: {cs.fmt_change('Kalliope Bold', 'Kalliope')}"
    )
    cs.emit(
        f"{cs.UPDATED_LABEL} {cs.fmt_field('nameID', 3)} in {cs.fmt_file_compact('/fonts/Kalliope-Bold.otf')}: {cs.fmt_change('1.000;UKWN;Kalliope-Bold', '2.000;CSTM;Kalliope-Bold')}"
    )
    cs.emit(
        f"{cs.UNCHANGED_LABEL} {cs.fmt_field('nameID', 4)} in {cs.fmt_file_compact('/fonts/Kalliope-Bold.otf')}"
    )
    cs.emit(
        f"{cs.SAVED_LABEL} Changes written to {cs.fmt_file_compact('/fonts/Kalliope-Bold.otf')}"
    )
    cs.emit("")

    # Summary Statistics
    cs.emit(
        "\n\n[bold deep_sky_blue1]═══ Summary Statistics ═══[/bold deep_sky_blue1]\n"
        if cs.RICH_AVAILABLE
        else "=== Summary Statistics ==="
    )
    cs.emit(f"{cs.SUCCESS_LABEL} {cs.fmt_smart_underline('Processing Complete!')}")
    cs.emit(f"{cs.indent(1)}Files found: {cs.fmt_count(42)}")
    cs.emit(f"{cs.indent(1)}Files processed: {cs.fmt_count(38)}")
    cs.emit(f"{cs.indent(1)}Files updated: {cs.fmt_count(35)}")
    cs.emit(f"{cs.indent(1)}Files unchanged: {cs.fmt_count(3)}")
    cs.emit(
        f"{cs.indent(1)}Success rate: {cs.fmt_count(38)}/{cs.fmt_count(42)} ({cs.fmt_count('90%')})"
    )
    cs.emit("")

    # Panel Example
    if cs.RICH_AVAILABLE:
        cs.emit(
            "\n\n[bold deep_sky_blue1]═══ Panel Example ═══[/bold deep_sky_blue1]\n"
        )
        cs.print_panel(
            "This is a boxed message panel.\nUseful for important notices, warnings, or summaries.\nSupports multi-line content with Rich markup.",
            title="📋 Notice",
            border_style="dodger_blue1",
            console=console,
        )
        cs.emit("")

    # Table Example
    if cs.RICH_AVAILABLE:
        cs.emit(
            "\n\n[bold deep_sky_blue1]═══ Table Example ═══[/bold deep_sky_blue1]\n"
        )
        table = cs.create_table(title="Font Name Records", row_styles=["", "dim"])
        if table:
            table.add_column("nameID", style="cyan", justify="right")
            table.add_column("Description", style="grey100")
            table.add_column("Value", style="green")
            table.add_row("1", "Font Family", "Kalliope")
            table.add_row("2", "Font Subfamily", "Bold")
            table.add_row("3", "Unique ID", "2.000;CSTM;Kalliope-Bold")
            table.add_row("4", "Full Font Name", "Kalliope Bold")
            table.add_row("6", "PostScript Name", "Kalliope-Bold")
            console.print(table)
        cs.emit("")

    # Status Message Examples
    cs.emit(
        "\n\n[bold deep_sky_blue1]═══ Status Messages ═══[/bold deep_sky_blue1]\n"
        if cs.RICH_AVAILABLE
        else "=== Status Messages ==="
    )
    cs.status_message(cs.INFO_LABEL, f"Found {cs.fmt_count(5)} font families", console)
    cs.status_message(cs.WARNING_LABEL, "Macintosh name records detected", console)
    cs.status_message(
        cs.ERROR_LABEL, f"Failed to process {cs.fmt_file('broken.otf')}", console
    )
    cs.status_message(cs.SUCCESS_LABEL, "All files validated successfully", console)
    cs.emit("")

    # End
    cs.fmt_header("Demo Complete - All Features Displayed", console)


def demo_font_sorter(files: List[str], args: argparse.Namespace):
    """Demo font sorting capabilities with real files."""
    cs.print_panel("Font Sorter Demo", title="Font Sorter Demo")

    if not files:
        cs.emit(f"{cs.WARNING_LABEL} No files provided, using dummy data")
        # Use dummy data
        example_paths = [
            "/fonts/Helvetica-Regular.otf",
            "/fonts/Helvetica-Bold.otf",
            "/fonts/Helvetica-Italic.otf",
            "/fonts/Helvetica-BoldItalic.otf",
            "/fonts/Times-Roman.otf",
            "/fonts/Times-Bold.otf",
            "/fonts/Arial-Regular.ttf",
            "/fonts/Arial-Bold.ttf",
            "/fonts/AdobeGaramond-Regular.otf",
            "/fonts/AdobeGaramond-Bold.otf",
            "/fonts/AdobeGaramondPro-Regular.otf",
            "/fonts/AdobeGaramondPro-Bold.otf",
        ]
        font_infos = create_font_info_from_paths(example_paths, extract_metadata=False)
    else:
        # Use real files
        cs.emit(f"{cs.INFO_LABEL} Processing {cs.fmt_count(len(files))} provided paths")

        # Collect font files from paths
        try:
            font_files = collect_font_files(
                files, recursive=getattr(args, "recursive", False)
            )
            if not font_files:
                cs.emit(f"{cs.ERROR_LABEL} No font files found in provided paths")
                return
            cs.emit(
                f"{cs.SUCCESS_LABEL} Found {cs.fmt_count(len(font_files))} font files"
            )
        except Exception as e:
            cs.emit(f"{cs.ERROR_LABEL} Error collecting font files: {e}")
            return

        # Create font info objects
        font_infos = create_font_info_from_paths(font_files, extract_metadata=True)

    sorter = FontSorter(font_infos)

    # Show detailed info if requested
    if getattr(args, "info", False):
        cs.emit(f"\n{cs.INFO_LABEL} {cs.fmt_smart_underline('Font Metadata')}")
        for font_info in font_infos:
            cs.emit(f"\n{Path(font_info.path).name}:")
            cs.emit(f"  Path: {font_info.path}")
            cs.emit(f"  Family: {font_info.family_name}")
            if font_info.vendor:
                cs.emit(f"  Manufacturer: {font_info.vendor}")
            if font_info.vendor_id:
                cs.emit(f"  Vendor ID: {font_info.vendor_id}")
            if font_info.designer:
                cs.emit(f"  Designer: {font_info.designer}")
            if font_info.style:
                cs.emit(f"  Style: {font_info.style}")

    # Choose grouping method based on args
    if getattr(args, "superfamily", False):
        cs.emit(f"\n{cs.INFO_LABEL} {cs.fmt_smart_underline('Superfamily Grouping')}")
        groups = sorter.group_by_superfamily(
            ignore_terms=getattr(args, "ignore_term", []),
            exclude_families=getattr(args, "exclude_family", []),
        )
        group_type = "superfamily"
    else:
        cs.emit(f"\n{cs.INFO_LABEL} {cs.fmt_smart_underline('Family Grouping')}")
        groups = sorter.group_by_family()
        group_type = "family"

    # Apply forced groups if specified
    if getattr(args, "group", []):
        forced_groups = args.group
        cs.emit(f"\n{cs.INFO_LABEL} {cs.fmt_smart_underline('Forced Grouping')}")
        cs.emit(f"Applying forced groups: {forced_groups}")
        groups = sorter.group_by_family(forced_groups=forced_groups)
        group_type = "family"

    # Show summary
    summary = sorter.get_grouping_summary(groups, group_type)
    cs.emit(
        f"\n{cs.INFO_LABEL} Found {cs.fmt_count(summary['num_groups'])} {group_type} group(s) with {cs.fmt_count(summary['total_fonts'])} total fonts"
    )

    # Show groups
    cs.emit(f"\n{cs.INFO_LABEL} {cs.fmt_smart_underline('Grouping Results')}")
    for group_name, fonts in groups.items():
        cs.emit(f"\n{group_name} ({len(fonts)} fonts):")
        for font in sorted(fonts, key=lambda f: f.path):
            cs.emit(f"  - {Path(font.path).name}")


def demo_name_parser(files: List[str], args: argparse.Namespace):
    """Demo name parsing with real files."""
    cs.print_panel("Name Parser Demo", title="Name Parser Demo")

    if not files:
        cs.emit(f"{cs.WARNING_LABEL} No files provided, using dummy data")
        # Use dummy data
        example_filenames = [
            "QueenSansExtra-ExtralightItalic",
            "KWAKGrotesk-ExtraBold",
            "UIUXKit-Regular",
            "ABCD-Bold",
            "NoHyphenName",
            "HelveticaNeue-LightItalic",
            "AdobeGaramondPro-BookItalic",
            "ABC_EFG-Regular",
            "ABC_EFGRegular-Bold",
        ]
    else:
        # Use real filenames
        example_filenames = [
            Path(f).stem for f in files
        ]  # Get filename without extension
        cs.emit(
            f"{cs.INFO_LABEL} Parsing {cs.fmt_count(len(example_filenames))} real filenames"
        )

    for filename in example_filenames:
        parsed = parse_filename(filename)
        family_words = format_pascal_words(parsed.family)
        subfamily_words = (
            format_pascal_words(parsed.subfamily) if parsed.subfamily else ""
        )

        cs.emit(f"  {cs.fmt_file(filename)}")
        cs.emit(f"    Family: {cs.fmt_field('family', family_words)}")
        if subfamily_words:
            cs.emit(f"    Subfamily: {cs.fmt_field('subfamily', subfamily_words)}")
        cs.emit("")

    # Demo PascalCase formatting
    cs.emit(
        f"{cs.INFO_LABEL} {cs.fmt_smart_underline('PascalCase Formatting Examples')}"
    )

    pascal_examples = [
        "QueenSansExtra",
        "KWAKGrotesk",
        "UIUXKit",
        "ABCD",
        "XMLHttpRequest",
        "UI2Kit",
        "ABC_EFG",
        "ABC_EFGRegular",
        "_ABC_EFG_",
    ]

    for example in pascal_examples:
        formatted = format_pascal_words(example)
        cs.emit(f"  {cs.fmt_value(example)} → {cs.fmt_change(example, formatted)}")


def demo_file_collector(files: List[str], args: argparse.Namespace):
    """Demo file collection."""
    cs.print_panel("File Collector Demo", title="File Collector Demo")

    cs.emit(f"{cs.INFO_LABEL} {cs.fmt_smart_underline('Supported Extensions')}")
    for ext in sorted(SUPPORTED_EXTENSIONS):
        descriptions = {
            ".ttf": "TrueType Font",
            ".otf": "OpenType Font",
            ".woff": "Web Open Font Format",
            ".woff2": "Web Open Font Format 2",
            ".ttx": "TrueType XML",
        }
        cs.emit(
            f"  {cs.fmt_field('extension', ext)}: {descriptions.get(ext, 'Font Format')}"
        )

    if files:
        cs.emit(
            f"\n{cs.INFO_LABEL} {cs.fmt_smart_underline('Collection from Provided Paths')}"
        )
        cs.emit(f"Processing {cs.fmt_count(len(files))} provided paths:")
        for path in files:
            cs.emit(f"  {cs.fmt_file(path)}")

        # Collect font files from paths
        try:
            collected = collect_font_files(
                files, recursive=getattr(args, "recursive", False)
            )
            cs.emit(
                f"\n{cs.SUCCESS_LABEL} Collected {cs.fmt_count(len(collected))} font files:"
            )
            for path in collected:
                cs.emit(f"  {cs.fmt_file(path)}")
        except Exception as e:
            cs.emit(f"{cs.ERROR_LABEL} Error collecting font files: {e}")
    else:
        cs.emit(f"\n{cs.WARNING_LABEL} No paths provided, showing example collection")
        # Show example collection
        example_paths = [
            "/fonts/Helvetica-Regular.otf",
            "/fonts/Helvetica-Bold.ttf",
            "/fonts/README.txt",  # Should be filtered out
            "/fonts/subdir/Arial.woff",
            "/fonts/subdir/Arial.woff2",
        ]

        cs.emit(f"{cs.INFO_LABEL} Example paths to collect:")
        for path in example_paths:
            console.print(f"  {cs.fmt_file(path)}")

        # Simulate collection results
        collected = [
            p for p in example_paths if Path(p).suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        cs.emit(
            f"\n{cs.SUCCESS_LABEL} Collected {cs.fmt_count(len(collected))} font files:"
        )
        for path in collected:
            console.print(f"  {cs.fmt_file(path)}")


def demo_name_policies(files: List[str], args: argparse.Namespace):
    """Demo name policies."""
    cs.print_panel("Name Policies Demo", title="Name Policies Demo")

    # Demo ID building
    cs.emit(f"{cs.INFO_LABEL} {cs.fmt_smart_underline('NameID Building Examples')}")

    examples = [
        {
            "family": "Helvetica",
            "subfamily": "Bold",
            "slope": "Italic",
            "description": "ID1 (Family) - removes Regular, handles Bold",
        },
        {
            "family": "Helvetica",
            "subfamily": "Regular",
            "slope": None,
            "description": "ID1 (Family) - removes Regular",
        },
        {
            "family": "Helvetica",
            "subfamily": "Bold",
            "slope": "Italic",
            "description": "ID4 (Full) - includes all style info",
        },
    ]

    for example in examples:
        id1_result = build_id1(
            family=example["family"],
            modifier=None,
            style=example["subfamily"],
            slope=example["slope"],
        )
        id4_result = build_id4(
            family=example["family"],
            modifier=None,
            style=example["subfamily"],
            slope=example["slope"],
        )

        input_str = f"{example['family']} {example['subfamily']}"
        if example["slope"]:
            input_str += f" {example['slope']}"

        cs.emit(f"  Input: {cs.fmt_value(input_str)}")
        cs.emit(f"    ID1: {cs.fmt_field('id1', id1_result)}")
        cs.emit(f"    ID4: {cs.fmt_field('id4', id4_result)}")
        cs.emit(f"    {example['description']}")
        cs.emit("")

    # Demo PostScript sanitization
    cs.emit(f"{cs.INFO_LABEL} {cs.fmt_smart_underline('PostScript Name Sanitization')}")

    ps_examples = [
        "Helvetica-Bold",
        "Helvetica Bold",  # Space should become hyphen
        "Helvetica:Italic",  # Colon should be removed
        "Helvetica/Path",  # Slash should be removed
        "Helvetica*Bold",  # Asterisk should be removed
    ]

    for example in ps_examples:
        sanitized = sanitize_postscript(example)
        cs.emit(f"  {cs.fmt_value(example)} → {cs.fmt_change(example, sanitized)}")

    # Demo variable token stripping
    cs.emit(f"\n{cs.INFO_LABEL} {cs.fmt_smart_underline('Variable Token Stripping')}")

    var_examples = [
        "Helvetica-Variable",
        "Helvetica-VF",
        "Helvetica-VariableItalic",
        "Helvetica-VF-Bold",
    ]

    for example in var_examples:
        stripped = strip_variable_tokens(example)
        cs.emit(f"  {cs.fmt_value(example)} → {cs.fmt_change(example, stripped)}")


def demo_ttx_operations(files: List[str], args: argparse.Namespace):
    """Demo TTX operations."""
    cs.print_panel("TTX Operations Demo", title="TTX Operations Demo")

    cs.emit(f"{cs.INFO_LABEL} {cs.fmt_smart_underline('TTX Operation Capabilities')}")

    capabilities = [
        "Load TTX files with lxml or fallback to ElementTree",
        "Find name table elements in TTX structure",
        "Locate specific namerecords by ID and platform",
        "Update namerecord values with minimal diff",
        "Create new namerecords when missing",
        "Deduplicate duplicate namerecords",
        "Write TTX files preserving structure/whitespace",
    ]

    for i, capability in enumerate(capabilities, 1):
        console.print(f"  {cs.fmt_count(i)}. {capability}")

    cs.emit(
        f"\n{cs.INFO_LABEL} {cs.fmt_smart_underline('Platform/Encoding Constants')}"
    )

    constants = [
        ("PID_WIN", "3", "Windows Platform ID"),
        ("EID_UNICODE_BMP", "1", "Unicode BMP Encoding ID"),
        ("LANG_EN_US_HEX", "0x409", "English US Language ID (hex)"),
        ("LANG_EN_US_INT", "1033", "English US Language ID (int)"),
    ]

    for const_name, value, description in constants:
        cs.emit(
            f"  {cs.fmt_field('constant', const_name)}: {cs.fmt_value(value)} - {description}"
        )

    cs.emit(f"\n{cs.INFO_LABEL} {cs.fmt_smart_underline('Binary Font Operations')}")

    binary_ops = [
        "Open font files with fontTools",
        "Update namerecords in binary fonts",
        "Deduplicate namerecords in binary fonts",
        "Preserve all other font data unchanged",
    ]

    for i, op in enumerate(binary_ops, 1):
        console.print(f"  {cs.fmt_count(i)}. {op}")


def run_all_demos():
    """Run all demos with dummy data."""
    cs.print_session_header("Core Libraries Demo Tool")

    # Run each demo with empty file lists
    demo_font_sorter([], argparse.Namespace())
    console.print()

    demo_name_parser([], argparse.Namespace())
    console.print()

    demo_file_collector([], argparse.Namespace())
    console.print()

    demo_name_policies([], argparse.Namespace())
    console.print()

    demo_ttx_operations([], argparse.Namespace())
    console.print()

    cs.emit(f"\n{cs.SUCCESS_LABEL} All core library demos completed!")
    cs.emit(
        f"{cs.INFO_LABEL} These libraries provide the foundation for all font processing scripts."
    )


def create_parser():
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        description="Demo tool for core font processing libraries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python core_demo_tool.py sorter /path/to/fonts/ --superfamily --info
  python core_demo_tool.py parser "Helvetica-Bold.otf" "Times-Italic.ttf"
  python core_demo_tool.py collector /path/to/fonts/ --recursive
  python core_demo_tool.py console
  python core_demo_tool.py all
        """,
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Font sorter subcommand
    font_parser = subparsers.add_parser(
        "sorter", help="Demo font sorting with real files"
    )
    font_parser.add_argument(
        "files", nargs="*", help="Font files or directories to process"
    )
    font_parser.add_argument(
        "--superfamily",
        action="store_true",
        help="Group by superfamily (common prefixes)",
    )
    font_parser.add_argument(
        "--info", action="store_true", help="Show detailed font metadata"
    )
    font_parser.add_argument(
        "--recursive", "-r", action="store_true", help="Process directories recursively"
    )
    font_parser.add_argument(
        "--ignore-term",
        "-it",
        action="append",
        help="Ignore token during superfamily clustering",
    )
    font_parser.add_argument(
        "--exclude-family",
        "-ef",
        action="append",
        help="Exclude families from superfamily clustering",
    )
    font_parser.add_argument(
        "--group",
        "-g",
        action="append",
        help="Force families to merge (comma-separated)",
    )

    # Name parser subcommand
    parser_parser = subparsers.add_parser(
        "parser", help="Demo name parsing with real files"
    )
    parser_parser.add_argument(
        "files", nargs="*", help="Font files to parse names from"
    )

    # File collector subcommand
    collector_parser = subparsers.add_parser("collector", help="Demo file collection")
    collector_parser.add_argument(
        "files", nargs="*", help="Files or directories to collect from"
    )
    collector_parser.add_argument(
        "--recursive", "-r", action="store_true", help="Process directories recursively"
    )

    # Name policies subcommand
    policies_parser = subparsers.add_parser("policies", help="Demo name policies")
    policies_parser.add_argument(
        "files", nargs="*", help="Font files (not used in this demo)"
    )

    # TTX operations subcommand
    ttx_parser = subparsers.add_parser("ttx", help="Demo TTX operations")
    ttx_parser.add_argument(
        "files", nargs="*", help="TTX files (not used in this demo)"
    )

    # Console styles subcommand
    console_parser = subparsers.add_parser(
        "console", help="Demo console styling capabilities"
    )
    console_parser.add_argument(
        "files", nargs="*", help="Files (not used in this demo)"
    )

    # All demos subcommand
    all_parser = subparsers.add_parser("all", help="Run all demos with dummy data")
    all_parser.add_argument("files", nargs="*", help="Files (not used in this demo)")

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        return

    files = getattr(args, "files", [])

    if args.subcommand == "sorter":
        demo_font_sorter(files, args)
    elif args.subcommand == "parser":
        demo_name_parser(files, args)
    elif args.subcommand == "collector":
        demo_file_collector(files, args)
    elif args.subcommand == "policies":
        demo_name_policies(files, args)
    elif args.subcommand == "ttx":
        demo_ttx_operations(files, args)
    elif args.subcommand == "console":
        demo_console_styles()
    elif args.subcommand == "all":
        run_all_demos()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
