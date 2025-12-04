#!/usr/bin/env python3
"""
NameID Replacer Base Module

Centralized workflow display, styling, and processing flow logic for all NameID Replacer scripts.
Provides helper functions to reduce code duplication and ensure consistent styling across scripts.
"""

from fontTools.ttLib import TTFont
import FontCore.core_console_styles as cs
from FontCore.core_file_collector import collect_font_files
from FontCore.core_ttx_table_io import (
    load_ttx,
    count_mac_name_records_ttx,
    count_mac_name_records_binary,
)
from typing import Optional

# New imports for enhanced functionality
from FontCore.core_logging_config import get_logger
from FontCore.core_error_handling import (
    ErrorContext,
    ErrorInfo,
)

logger = get_logger(__name__)

# Get the themed console singleton
console = cs.get_console()


# ErrorContext enum is now imported from FontCore.core_error_handling


class ProcessingStats:
    """Collects processing statistics, warnings, and errors during font processing."""

    def __init__(self):
        self.updated = 0
        self.unchanged = 0
        self.errors = 0
        self.warnings = []
        self.error_messages = []

    def add_warning(
        self, name_id: int, filepath: str, message: str, warning_type: str = "general"
    ) -> None:
        """Add a warning to the collection."""
        self.warnings.append(
            {
                "name_id": name_id,
                "filepath": filepath,
                "message": message,
                "type": warning_type,
            }
        )

    def add_error(self, name_id: int, filepath: str, message: str) -> None:
        """Add an error to the collection."""
        self.error_messages.append(
            {"name_id": name_id, "filepath": filepath, "message": message}
        )

    def to_dict(self) -> dict:
        """Convert to dictionary format for BatchRunner."""
        return {
            "updated": self.updated,
            "unchanged": self.unchanged,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_messages": self.error_messages,
        }


def show_workflow_header(title: str, name_id: int, description: str, console) -> None:
    """Display formatted header for NameID processing workflow"""
    cs.fmt_header(f"{title} - Processing nameID={name_id} records", console)
    cs.emit("", console=console)


def show_file_list(font_files: list, console) -> None:
    """Display formatted list of files to be processed"""
    cs.StatusIndicator("info").add_message(
        f"Found {cs.fmt_count(len(font_files))} font file(s) to process:"
    ).emit(console=console)
    for file in font_files:
        cs.emit(f"  - {cs.fmt_file_compact(file)}", console=console)


def show_preflight_checklist(
    script_name: str, operations: list, console, active_flags: list = None
) -> None:
    """Display preflight checklist with operations that will be performed"""
    if active_flags:
        # Show active flags first
        cs.emit("", console=console)
        cs.StatusIndicator("info").add_message("Active Flags:").emit(console=console)

        for flag_info in active_flags:
            cs.emit(f"  {flag_info}", console=console)

        cs.emit("", console=console)

    cs.fmt_preflight_checklist(script_name, operations, console=console)


def check_and_show_mac_records(
    font_files: list, console, delete_mac_records: bool = False
) -> None:
    """Check all files for Mac records and display summary warning if found"""
    total_mac_records = 0
    files_with_mac = []

    for filepath in font_files:
        try:
            if filepath.lower().endswith(".ttx"):
                # TTX file
                tree, root, using_lxml = load_ttx(filepath)
                count = count_mac_name_records_ttx(root)
            else:
                # Binary font file
                font = TTFont(filepath)
                count = count_mac_name_records_binary(font)
                font.close()

            if count > 0:
                total_mac_records += count
                files_with_mac.append((filepath, count))
        except Exception:
            # Skip files that can't be read
            continue

    if total_mac_records > 0:
        cs.emit("", console=console)
        if delete_mac_records:
            cs.StatusIndicator("info").add_message(
                f"Found {cs.fmt_count(total_mac_records)} Mac name record(s) in {cs.fmt_count(len(files_with_mac))} file(s) - will be removed"
            ).emit(console)
        else:
            cs.StatusIndicator("warning").add_message(
                f"[warning]Macintosh name records detected in {cs.fmt_count(len(files_with_mac))} file(s)[/warning]"
            ).add_item(f"{cs.fmt_count(total_mac_records)} total records").add_item(
                "Use -dmr to remove them before processing for cleaner results"
            ).emit(console)
        cs.emit("", console=console)


def show_dry_run_notice(console) -> None:
    """Display dry-run mode notice"""
    cs.emit("", console=console)
    cs.StatusIndicator("warning").add_message(
        "[bold][warning]DRY RUN MODE[/bold] - no changes will be made.[/warning]"
    ).emit(console=console)


def remove_mac_records_ttx(filepath: str, dry_run: bool = False) -> int:
    """Remove Mac name records (platformID=1) from TTX file. Returns count of removed records."""
    try:
        tree, root, using_lxml = load_ttx(filepath)
        name_table = root.find(".//name")
        if name_table is None:
            return 0

        removed_count = 0
        to_remove = []

        for nr in list(name_table.findall("namerecord")):
            if nr.get("platformID") == "1":
                to_remove.append(nr)
                removed_count += 1

        if removed_count > 0 and not dry_run:
            for nr in to_remove:
                name_table.remove(nr)

            # Save the file
            if using_lxml:
                tree.write(
                    filepath, encoding="utf-8", xml_declaration=True, pretty_print=True
                )
            else:
                tree.write(filepath, encoding="utf-8", xml_declaration=True)

        return removed_count
    except Exception:
        return 0


def remove_mac_records_binary(filepath: str, dry_run: bool = False) -> int:
    """Remove Mac name records (platformID=1) from binary font file. Returns count of removed records."""
    try:
        font = TTFont(filepath)
        name_table = font["name"]

        removed_count = 0
        kept = []

        for record in list(name_table.names):
            if record.platformID == 1:
                removed_count += 1
            else:
                kept.append(record)

        if removed_count > 0 and not dry_run:
            name_table.names = kept
            font.save(filepath)

        font.close()
        return removed_count
    except Exception:
        return 0


def remove_mac_records_from_file(filepath: str, dry_run: bool = False) -> int:
    """Remove Mac name records from a font file. Returns count of removed records."""
    if filepath.lower().endswith(".ttx"):
        return remove_mac_records_ttx(filepath, dry_run)
    else:
        return remove_mac_records_binary(filepath, dry_run)


def prompt_confirmation(
    file_count: int, dry_run: bool, batch_context: bool, console
) -> bool:
    """Prompt user for confirmation. Returns True to proceed, False to cancel.
    Raises cs.QuitRequested if batch_context=True and user quits."""
    if not dry_run:
        if not cs.prompt_confirm(
            f"About to modify {cs.fmt_count(file_count)} file(s). Proceed?",
            allow_quit=batch_context,
        ):
            if batch_context:
                raise cs.QuitRequested("User cancelled batch operation")
            else:
                cs.StatusIndicator("info").add_message("Cancelled").emit(
                    console=console
                )
                return False
    return True


def show_processing_summary(
    updated: int, unchanged: int, errors: int, dry_run: bool, console
) -> None:
    """Display standardized processing summary"""
    cs.fmt_processing_summary(
        dry_run=dry_run,
        updated=updated,
        unchanged=unchanged,
        errors=errors,
        console=console,
    )


# ============================================================================
# CENTRALIZED STATUS MESSAGE HELPERS
# ============================================================================
# These functions encapsulate common StatusIndicator patterns to enable
# global style changes from a single location. Use these instead of direct
# StatusIndicator calls for consistent styling across all scripts.


def show_preview(filepath: str, dry_run: bool, console) -> None:
    """Display DRY-RUN MODE preview message for a file"""
    cs.StatusIndicator("preview", dry_run=dry_run).add_message(
        f"[bold][preview]DRY-RUN MODE[/bold] No changes will be saved to: {cs.fmt_file(filepath, filename_only=True)}[preview]"
    ).emit(console=console)


def show_parsing(filepath: str, dry_run: bool, console) -> None:
    """Display PARSING file message"""
    cs.StatusIndicator("parsing", dry_run=dry_run).add_file(
        filepath, filename_only=False
    ).emit(console=console)


def show_saved(filepath: str, dry_run: bool, console) -> None:
    """Display SAVED TO file message with reverse styling"""
    cs.StatusIndicator("saved", dry_run=dry_run).add_file(
        filepath, filename_only=False, style="reverse"
    ).emit(console=console)


def show_info(message: str, dry_run: bool, console) -> None:
    """Display INFO message (e.g., 'Variable font detected')"""
    cs.StatusIndicator("info", dry_run=dry_run).add_message(message).emit(
        console=console
    )


def show_warning(filepath: str, message: str, dry_run: bool, console) -> None:
    """Display WARNING message with explanation"""
    cs.StatusIndicator("warning", dry_run=dry_run).add_file(filepath).add_message(
        message
    ).emit(console=console)


def show_error(filepath: str, message: str, dry_run: bool, console) -> None:
    """Display ERROR message with explanation"""
    cs.StatusIndicator("error", dry_run=dry_run).add_file(filepath).add_message(
        message
    ).emit(console=console)


def show_error_with_context(
    filepath: str,
    message: str,
    context: ErrorContext,
    dry_run: bool,
    console,
    error_info: Optional[ErrorInfo] = None,  # NEW: optional parameter
) -> None:
    """
    Display error with precise failure point context.

    Args:
        filepath: File where error occurred
        message: Error message
        context: Error context
        dry_run: Whether in dry-run mode
        console: Console instance
        error_info: Optional full ErrorInfo for detailed logging

    Example output:
    ERROR [LOADING] filename.ttf
          Failed to parse TTX file: invalid XML syntax

    Note: Focus on WHERE failure occurred, not HOW to fix.
    User can investigate based on failure point context.
    """
    filename = filepath.split("/")[-1] if "/" in filepath else filepath
    context_str = context.value.upper()

    cs.StatusIndicator("error", dry_run=dry_run).add_file(
        f"[{context_str}] {filename}"
    ).add_message(message).emit(console=console)

    # Log full details if ErrorInfo provided
    if error_info:
        logger.debug(error_info.to_log_message())
        if error_info.stack_trace:
            logger.debug(f"Stack trace:\n{error_info.stack_trace}")


def show_updated(
    name_id: int, filepath: str, old_value: str, new_value: str, dry_run: bool, console
) -> None:
    """Display UPDATED nameID message with old → new values and new value on separate line"""
    cs.StatusIndicator("updated", dry_run=dry_run).add_field(
        "nameID", name_id
    ).add_file(filepath, filename_only=True).add_values(
        old_value=old_value, new_value=new_value
    ).add_item(f" {new_value}", indent_level=1, style="bold").emit(console=console)


def show_unchanged(
    name_id: int, filepath: str, value: str, dry_run: bool, console
) -> None:
    """Display NO CHANGE nameID message with current value"""
    cs.StatusIndicator("unchanged", dry_run=dry_run).add_field(
        "nameID", name_id
    ).add_file(filepath, filename_only=True).add_values(value=value, style="bold").emit(
        console=console
    )


def show_created(
    name_id: int, filepath: str, value: str, dry_run: bool, console
) -> None:
    """Display CREATED nameID message with new value"""
    cs.StatusIndicator("created", dry_run=dry_run).add_field(
        "nameID", name_id
    ).add_file(filepath, filename_only=True).add_values(new_value=value).emit(
        console=console
    )


def show_compound_modifier_warning(
    filepath: str, instances: list, dry_run: bool, console
) -> None:
    """Display compound modifier warning using StatusIndicator properly."""
    # Collect unique modifiers
    modifiers = list(set(instance["modifier"].title() for instance in instances))

    # Build warning using StatusIndicator with explicit chaining
    cs.StatusIndicator("warning", dry_run=dry_run).add_file(
        filepath, filename_only=True
    ).add_item(
        f"[warning]Compound modifier(s) detected:[/warning][bold] {', '.join(modifiers)}[/bold]"
    ).add_item(
        f'[warning]Filename parsed as:[/warning][bold] "{instances[0]["parsed_as"]}"[/bold]'
    ).add_item(
        "[warning]Results may be incorrect. Consider reformatting filename to avoid PascalCase splitting.[/warning]"
    ).add_item(
        "[warning]To fix: run Find-N-Replace with the RemoveModifierSpaces preset.[/warning]"
    ).emit(console=console)


# ============================================================================
# Variable Font Support
# ============================================================================


def is_variable_font_ttx(root) -> bool:
    """Check if TTX font has fvar table (indicates variable font)."""
    return root.find(".//fvar") is not None


def is_variable_font_binary(font: TTFont) -> bool:
    """Check if binary font has fvar table (indicates variable font)."""
    return "fvar" in font


def show_vf_detected(filepath: str, dry_run: bool, console) -> None:
    """Display optional info message when variable font is detected."""
    show_info("Variable font detected", dry_run, console)


def clean_variable_family_name(family: str) -> str:
    """Remove variable font tokens from family name.

    Useful when treating a VF like a static font for naming purposes.
    Example: "Roboto Variable" → "Roboto"

    Wraps core_name_policies.strip_variable_tokens()
    """
    from FontCore.core_name_policies import strip_variable_tokens

    return strip_variable_tokens(family) or family


def run_workflow(
    file_paths: list,
    script_args,
    process_file_fn,
    title: str,
    name_id: int,
    description: str,
    operations: list,
    batch_context: bool = False,
) -> dict:
    """
    Complete workflow orchestration for NameID replacer scripts.

    Args:
        file_paths: List of font file paths to process
        script_args: Parsed arguments namespace
        process_file_fn: Function to call for each file (filepath, script_args, dry_run, stats) -> bool
        title: Script title for header
        name_id: NameID number being processed
        description: Description of the nameID (e.g., "Unique ID")
        operations: List of operation descriptions for preflight checklist
        batch_context: True when called from BatchRunner (enables quit)

    Returns:
        dict: Statistics dictionary with exit_code, updated, unchanged, errors, warnings, error_messages
    """
    # Initialize stats collector
    stats = ProcessingStats()

    # Discover files
    recursive = getattr(script_args, "recursive", False)
    font_files = collect_font_files(file_paths, recursive)
    if not font_files:
        cs.StatusIndicator("error").add_message("No font files found to process.").emit(
            console=console
        )
        stats.errors = 1
        return {"exit_code": 1, **stats.to_dict()}

    # Display header
    show_workflow_header(title, name_id, description, console)

    # Show file list (suppress when called from BatchRunner)
    if not batch_context:
        show_file_list(font_files, console)

    # Check for Mac records flag
    delete_mac_records = getattr(script_args, "delete_mac_records", False)

    # Build active flags list
    active_flags = []

    # Check for common flags
    if getattr(script_args, "dry_run", False):
        active_flags.append("-dry, --dry-run : Preview mode - no changes will be saved")

    if getattr(script_args, "confirm", False):
        active_flags.append("-yes, --confirm : Auto-confirm all prompts")

    if getattr(script_args, "recursive", False):
        active_flags.append("-R, --recursive : Process directories recursively")

    if getattr(script_args, "filename_parser", False):
        active_flags.append("-fp, --filename-parser : Derive values from font filename")

    if delete_mac_records:
        active_flags.append(
            "-dmr, --delete-mac-records : Remove all Mac name records (platformID=1) before processing"
        )

    # Add Mac record removal to operations if requested
    if delete_mac_records:
        operations.append("Mac name records will be removed (platformID=1)")

    # Show preflight checklist
    show_preflight_checklist(
        f"NameID {name_id} Replacer", operations, console, active_flags
    )

    # Check for Mac records
    check_and_show_mac_records(font_files, console, delete_mac_records)

    # Show dry run indicator
    if script_args.dry_run:
        show_dry_run_notice(console)

    # Confirm (skip in dry-run mode or if auto-confirm is set)
    if not script_args.yes:
        if not prompt_confirmation(
            len(font_files), script_args.dry_run, batch_context, console
        ):
            return {"exit_code": 2, **stats.to_dict()}

    cs.emit("", console=console)

    # Remove Mac records if requested
    if delete_mac_records:
        if script_args.dry_run:
            cs.StatusIndicator("info").add_message(
                "Would remove Mac name records..."
            ).emit(console=console)
        else:
            cs.StatusIndicator("info").add_message("Removing Mac name records...").emit(
                console=console
            )

        total_removed = 0
        for file in font_files:
            removed_count = remove_mac_records_from_file(file, script_args.dry_run)
            if removed_count > 0:
                total_removed += removed_count
                if script_args.dry_run:
                    cs.StatusIndicator("preview").add_file(
                        file, filename_only=True
                    ).add_message(
                        f"Would remove {cs.fmt_count(removed_count)} Mac record(s)"
                    ).emit(console=console)
                else:
                    cs.StatusIndicator("updated").add_file(
                        file, filename_only=True
                    ).add_message(
                        f"Removed {cs.fmt_count(removed_count)} Mac record(s)"
                    ).emit(console=console)

        if total_removed > 0:
            if script_args.dry_run:
                cs.StatusIndicator("info").add_message(
                    f"Would remove {cs.fmt_count(total_removed)} Mac record(s) total"
                ).emit(console=console)
            else:
                cs.StatusIndicator("info").add_message(
                    f"Removed {cs.fmt_count(total_removed)} Mac record(s) total"
                ).emit(console=console)
        else:
            cs.StatusIndicator("info").add_message(
                "No Mac records found to remove"
            ).emit(console=console)

        cs.emit("", console=console)

    # Process files with stats collection
    for file in font_files:
        try:
            if process_file_fn(file, script_args, script_args.dry_run, stats):
                stats.updated += 1
            else:
                stats.unchanged += 1
        except Exception as e:
            stats.errors += 1
            stats.add_error(name_id, file, f"Processing error: {e}")

    # Use standardized summary
    show_processing_summary(
        dry_run=script_args.dry_run,
        updated=stats.updated,
        unchanged=stats.unchanged,
        errors=stats.errors,
        console=console,
    )

    return {"exit_code": 0, **stats.to_dict()}
