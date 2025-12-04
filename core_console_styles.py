#!/usr/bin/env python3
"""
Shared console styling utilities for consistent output across scripts.

Primary API: StatusIndicator class for unified console output formatting.
Secondary APIs: Core formatting primitives and high-level helpers.

Usage:
from FontCore.core_console_styles import (
    RICH_AVAILABLE, UPDATED_LABEL, UNCHANGED_LABEL, ERROR_LABEL, WARNING_LABEL, INFO_LABEL,
    SAVED_LABEL, CREATED_LABEL, INPUT_LABEL, PARSING_LABEL, SUCCESS_LABEL,
    SKIPPED_LABEL, DUPLICATE_LABEL, CACHE_LABEL, DISCOVERED_LABEL, MAPPING_LABEL,
    INDENT, indent,
    fmt_change, fmt_field, fmt_file, fmt_file_compact, fmt_value, fmt_count,
    fmt_smart_underline, fmt_header,
    fmt_preflight_checklist, fmt_processing_summary, fmt_operation_description,
    emit, get_console, create_table, print_panel, print_session_header, status_message,
    create_progress_bar,
    prompt_input, prompt_confirm, prompt_text, prompt_select, QuitRequested,
    StatusIndicator,
)

These helpers auto-detect Rich. When Rich is available, they output styled markup;
otherwise, they fall back to plain text with no markup.

Demo and Testing:
    Run 'python CoreDemoTool.py console' to see a comprehensive showcase of all
    available labels, formatting helpers, and styling capabilities.

Maintenance Note:
    IMPORTANT: When adding new labels, formatting functions, or styling features to this module,
    you MUST update the _run_demo() function to showcase the new functionality.
    The demo is used by CoreDemoTool.py console subcommand and should always reflect
    the complete feature set of this module.
"""

from __future__ import annotations

import importlib.util as importlib_util
from typing import Optional
from pathlib import Path
import re

# Enhanced functionality import
from FontCore.core_logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# CONFIGURATION & AVAILABILITY
# ============================================================================
# Core configuration settings for console behavior and styling
CONSOLE_CONFIG = {
    "label_width": 11,  # width for labels (keeps alignment)
    "indent_size": 12,  # base indent spaces
    "use_rich": True,  # set False to force non-rich fallback
    "use_questionary": True,  # set False to force non-questionary fallback
    "theme_mode": "dark",  # "dark" or "light"
}

RICH_AVAILABLE: bool = (
    importlib_util.find_spec("rich") is not None
    if CONSOLE_CONFIG["use_rich"]
    else False
)

if RICH_AVAILABLE:
    from rich.console import Console as _Console
    from rich.theme import Theme
    from rich.panel import Panel
    from rich.table import Table as _Table
    from rich import box
    from rich.align import Align
    from rich.progress import (
        Progress as _Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeElapsedColumn,
    )

# ============================================================================
# THEME DEFINITION
# ============================================================================
# Custom Rich theme for consistent styling across all console output
if RICH_AVAILABLE:
    try:
        CUSTOM_THEME = Theme(
            {
                # Text colors
                "darktext": "#282a39",
                "lighttext": "grey100",
                # Label backgrounds
                "info": "dodger_blue1",
                "info.bright": "deep_sky_blue1",
                "updated": "magenta2",
                "unchanged": "turquoise2",
                "error": "red3",
                "warning": "gold1",
                "saved": "green",
                "created": "cornflower_blue",
                "removed": "medium_violet_red",
                "input": "cornsilk1",
                "parsing": "grey37",
                "success": "green_yellow",
                "preview": "gold3",
                "skipped": "orange1",
                "duplicate": "yellow3",
                "cache": "purple4",
                "discovered": "magenta",
                "mapping": "cyan3",
                "minimal": "cyan2",
                "moderate": "cyan3",
                "major": "turquoise4",
                "header": "deep_sky_blue1",
                # Content styling
                "value.before": "turquoise2",
                "value.after": "magenta2",
                "value.unchanged": "dim turquoise2",
                "file.name": "green",
                "file.path": "grey37",
                "count": "bold turquoise2",
                "field": "honeydew2",
                "field.number": "bold honeydew2",
                # Progress bar styling
                "bar.complete": "magenta3",
                "bar.finished": "magenta2",
                "bar.pulse": "medium_violet_red",
                "progress.description": "dodger_blue1",
                "progress.percentage": "bold turquoise2",
                "progress.elapsed": "dodger_blue3",
                "progress.remaining": "dodger_blue3",
                # These are Rich's internal fallback color names:
                "repr.number": "bold turquoise2",
                "repr.str": "grey100",
                "repr.bool_true": "italic spring_green3",
                "repr.bool_false": "italic deep_pink2",
                "repr.path": "grey37",
                "repr.filename": "green",
                "repr.file": "none",
                "repr.call": "none",
                "repr.tag_name": "hot_pink",
            }
        )
    except Exception as e:
        logger.error(f"Failed to initialize custom theme: {e}")
        # Fallback to default theme
        CUSTOM_THEME = Theme({})

    # Module-level console singleton
    _console_singleton: Optional[_Console] = None


# ============================================================================
# CONSOLE INFRASTRUCTURE
# ============================================================================
# Core console utilities used throughout the module


def get_console() -> Optional["_Console"]:
    """
    Get the Rich console instance if available, otherwise None.
    """
    global _console_singleton
    if RICH_AVAILABLE:
        if _console_singleton is None:
            try:
                _console_singleton = _Console(theme=CUSTOM_THEME)
            except Exception as e:
                logger.warning(f"Failed to initialize Rich console: {e}")
                return None
        return _console_singleton
    else:
        logger.debug("Rich not available, using plain text output")
    return None


def emit(
    message: str, highlight=None, console: Optional["_Console"] = None, end: str = "\n"
) -> None:
    """
    Emit a message via Rich console if available, otherwise print().
    """
    if RICH_AVAILABLE:
        (console or get_console()).print(
            message, end=end, overflow="fold", no_wrap=False
        )
    else:
        clean_message = re.sub(r"\[/?[^\]]+\]", "", message)
        print(clean_message, end=end)


def indent(level: int = 1, additional: int = 0) -> str:
    """
    Generate indentation for hierarchical output with natural wrapping support.
    """
    if level <= 0:
        return ""

    base = CONSOLE_CONFIG.get("indent_size", 12)  # default 12 spaces
    level_spacing = (level - 1) * 2  # Each level adds 2 spaces
    total_spaces = base + level_spacing + additional

    return " " * total_spaces


def bullet(text: str, level: int = 1) -> str:
    """
    Render a simple bullet line at the given indentation level.
    """
    return f"{indent(level)}• {text}"


def bulleted_kv(key: str, value: str | int, level: int = 1) -> str:
    """
    Render an indented bullet with a key: value pair.
    """
    return f"{indent(level)}• {key}: {fmt_count(value) if isinstance(value, int) else value}"


# ============================================================================
# STATUS LABELS
# ============================================================================
# Pre-formatted status labels for consistent console output


def _build_status_label(
    text: str, foreground_theme_key: str, background_theme_key: str = "lighttext"
) -> str:
    """
    Build a formatted status label using theme colors.

    Args:
        text: The label text to display
        foreground_theme_key: Theme key for foreground color
        background_theme_key: Theme key for background color
    """
    width = CONSOLE_CONFIG.get("label_width", 11)
    if RICH_AVAILABLE:
        # Look up colors from the theme
        foreground_color = CUSTOM_THEME.styles.get(
            foreground_theme_key, "yellow1"
        )  # yellow1 is fallback foreground
        background_color = CUSTOM_THEME.styles.get(
            background_theme_key, "red3"
        )  # red3 is fallback background
        return f"[bold {foreground_color} on {background_color}]{text:<{width}}[/bold {foreground_color} on {background_color}]"
    return f"{text:<{width}}"


# Status label constants
INFO_LABEL: str = _build_status_label(" INFO", "lighttext", "info")
UPDATED_LABEL: str = _build_status_label(" UPDATED", "darktext", "updated")
UNCHANGED_LABEL: str = _build_status_label(" NO CHANGE", "darktext", "unchanged")
ERROR_LABEL: str = _build_status_label(" ERROR", "lighttext", "error")
WARNING_LABEL: str = _build_status_label(" WARNING", "darktext", "warning")
SAVED_LABEL: str = _build_status_label(" SAVED TO", "darktext", "saved")
CREATED_LABEL: str = _build_status_label(" CREATED", "lighttext", "created")
REMOVED_LABEL: str = _build_status_label(" REMOVED", "darktext", "removed")
INPUT_LABEL: str = _build_status_label(" INPUT", "darktext", "input")
PREVIEW_LABEL: str = _build_status_label(" PREVIEW", "darktext", "preview")
PARSING_LABEL: str = _build_status_label(" PARSING", "lighttext", "parsing")
SUCCESS_LABEL: str = _build_status_label(" SUCCESS", "darktext", "success")
SKIPPED_LABEL: str = _build_status_label(" SKIPPED", "darktext", "skipped")
DUPLICATE_LABEL: str = _build_status_label(" DUPLICATE", "darktext", "duplicate")
CACHE_LABEL: str = _build_status_label(" CACHE", "lighttext", "cache")
DISCOVERED_LABEL: str = _build_status_label(" FOUND", "darktext", "discovered")
MAPPING_LABEL: str = _build_status_label(" MAPPING", "darktext", "mapping")
MINIMAL_LABEL: str = _build_status_label(" MINIMAL", "darktext", "minimal")
MODERATE_LABEL: str = _build_status_label(" MODERATE", "darktext", "moderate")
MAJOR_LABEL: str = _build_status_label(" MAJOR", "lighttext", "major")

# Indentation constant
INDENT: str = " " * CONSOLE_CONFIG.get("indent_size", 12)


# ============================================================================
# CORE FORMATTING PRIMITIVES
# ============================================================================
# Basic formatting functions used by StatusIndicator and other components


def fmt_change(old_value: str, new_value: str) -> str:
    """
    Format a change as old → new with visual emphasis on what changed.

    Example:
        >>> fmt_change("Arial-Bold", "Helvetica-Bold")
        "Arial-Bold → Helvetica-Bold"  # (with color: before=turquoise, after=magenta)
    """
    if RICH_AVAILABLE:
        return f"[value.before]{old_value}[/value.before] → [value.after]{new_value}[/value.after]"
    return f"{old_value} -> {new_value}"


def fmt_field(field_name: str, value: str | int) -> str:
    """
    Format a field as name: value with automatic number styling.

    Example:
        >>> fmt_field("nameID", 1)
        "nameID: 1"  # (with field styling when Rich available)
    """
    if isinstance(value, int) and RICH_AVAILABLE:
        return f"[field]{field_name}[/field]: [field.number]{value}[/field.number]"
    return f"[field]{field_name}[/field]: {value}"


def fmt_value(value: str | int, style: str = "plain") -> str:
    """
    Format a value with different styling options.

    Args:
        value: The value to format
        style: "plain", "before", "after", "unchanged"

    Example:
        >>> fmt_value("MyFont-Bold")
        "MyFont-Bold"  # (plain text)
        >>> fmt_value("MyFont-Bold", "before")
        "MyFont-Bold"  # (with turquoise styling)
        >>> fmt_value("MyFont-Bold", "after")
        "MyFont-Bold"  # (with magenta styling)
        >>> fmt_value("MyFont-Bold", "unchanged")
        "MyFont-Bold"  # (with dim turquoise styling)
    """
    if not RICH_AVAILABLE:
        return str(value)

    if style == "before":
        return f"[value.before]{value}[/value.before]"
    elif style == "after":
        return f"[value.after]{value}[/value.after]"
    elif style == "unchanged":
        return f"[value.unchanged]{value}[/value.unchanged]"
    else:  # plain
        return str(value)


def fmt_count(value: int | str) -> str:
    """
    Format a count or aggregate number with emphasis.

    Accepts both integers and strings (e.g., "90%" for percentages).

    Example:
        >>> fmt_count(42)
        "42"  # (with bold turquoise styling when Rich available)
        >>> fmt_count("90%")
        "90%"  # (with bold turquoise styling when Rich available)
    """
    return f"[count]{value}[/count]" if RICH_AVAILABLE else str(value)


def fmt_file(path: str, filename_only: bool = True) -> str:
    """
    Format a file path with consistent styling.

    Example:
        >>> fmt_file("/path/to/MyFont-Bold.otf")
        "MyFont-Bold.otf"  # (with green filename styling when Rich available)
    """
    if not RICH_AVAILABLE:
        return Path(path).name if filename_only else path

    if filename_only:
        return f"[file.name]{Path(path).name}[/file.name]"
    else:
        path_obj = Path(path)
        parent = str(path_obj.parent) + "/" if path_obj.parent != Path(".") else ""
        return f"[file.path]{parent}[/file.path][file.name]{path_obj.name}[/file.name]"


def fmt_file_compact(path: str) -> str:
    """
    Format a file path with dimmed directory and emphasized filename for easier scanning.

    Example:
        >>> fmt_file_compact("/path/to/MyFont-Bold.otf")
        "/path/to/MyFont-Bold.otf"  # (with dimmed path + green filename)
    """
    return fmt_file(path, filename_only=False)


def fmt_smart_underline(text: str) -> str:
    """
    Apply intelligent underlining that skips lowercase descenders for better typography.

    Example:
        >>> fmt_smart_underline("Typography is groovy")
        "Typography is groovy"  # (with smart underlines, skips descenders)
    """
    if not RICH_AVAILABLE:
        return text

    lowercase_descenders = set("gjpqyQ")

    result = []

    for char in text:
        if char in lowercase_descenders:
            result.append(char)
        else:
            result.append(f"[underline]{char}[/underline]")

    return "".join(result)


def fmt_header(text: str, console: Optional["_Console"] = None) -> None:
    """
    Create a centered header with panel styling.

    Example:
        >>> fmt_header("PROCESSING SUMMARY")
        # Creates a centered panel with the text
    """
    if RICH_AVAILABLE:
        console = console or get_console()
        centered_text = Align.center(text)
        panel = Panel(
            centered_text,
            box=box.HORIZONTALS,
            border_style="dodger_blue1",
            style="bold grey100",
            padding=0,
            expand=True,
        )

        console.print(panel)
    else:
        print(f"=== {text} ===")


# ============================================================================
# MAIN API - STATUS INDICATOR CLASS
# ============================================================================
# Primary interface for all console output formatting


class StatusIndicator:
    """
    Universal status indicator for consistent message formatting.

    Builds messages in layers:
    - Level 1: Base label (UPDATED, ERROR, etc.)
    - Level 2: Context (file, field, etc.)
    - Level 3: Values/changes based on status type
    - Level 4: Additional details with indentation

    Features:
    - Chainable builder pattern for composing complex messages
    - Automatic indentation for hierarchical output
    - Preview/dry-run mode conversion
    - Processing summary formatting
    - Support for 18 status types (updated, created, error, warning, etc.)
    - Style overrides for all builder methods (e.g., style="bold hot_pink")

    Usage:
        # Simple message
        StatusIndicator("info").add_message("Processing files").emit()

        # File operation with details
        StatusIndicator("updated")
            .add_field("nameID", 1)
            .add_file("font.otf")
            .add_values(old_value="Old", new_value="New")
            .add_item("Additional context")
            .emit()

        # File with custom styling
        StatusIndicator("saved")
            .add_file("font.otf", style="reverse")
            .emit()

        # Style overrides for emphasis
        StatusIndicator("unchanged")
            .add_field("nameID", 1, style="bold turquoise2")
            .add_file("font.otf")
            .add_values(value="CurrentValue", style="bold")
            .emit()

        # Preview mode
        StatusIndicator("updated", dry_run=True)
            .add_file("font.otf")
            .emit()

        # Processing summary
        StatusIndicator("success")
            .add_message("Processing Completed!")
            .with_summary_block(updated=10, unchanged=2, errors=0)
            .emit()

        # Dry-Run Mode:
            Pass dry_run=True to enable preview mode:
            - Dims operational labels (updated, created, deleted, parsing)
            - Suppresses 'saved' messages entirely
            - Info/warning/error labels remain normal

            Usage:
                StatusIndicator("updated", dry_run=True)
                    .add_file("font.otf")
                    .emit()

        # Style Parameter:
            All builder methods accept an optional style parameter:
            - Use Rich style names: "bold", "hot_pink", "bold turquoise2"
            - Respects Rich limitations (can't combine custom theme names with modifiers)
            - Falls back gracefully when Rich is unavailable

            Examples:
                .add_message("Important!", style="bold hot_pink")
                .add_field("nameID", 1, style="bold")
                .add_values(value="NewValue", style="bold")
                .with_explanation("Error details", style="dim")
                .add_item("Note", style="bold red")
    """

    STATUS_THEMES = {
        "updated": {
            "label": UPDATED_LABEL,
            "template": "{context}",
            "value_style": "after",
            "show_change": True,
        },
        "created": {
            "label": CREATED_LABEL,
            "template": "{context}",
            "value_style": "after",
            "show_change": False,
        },
        "unchanged": {
            "label": UNCHANGED_LABEL,
            "template": "{context}",
            "value_style": "unchanged",
            "show_change": False,
        },
        "deleted": {
            "label": REMOVED_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "parsing": {
            "label": PARSING_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "saved": {
            "label": SAVED_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "success": {
            "label": SUCCESS_LABEL,
            "template": "{context}{details}",
            "value_style": "plain",
            "show_change": False,
        },
        "info": {
            "label": INFO_LABEL,
            "template": "{context}{details}",
            "value_style": "plain",
            "show_change": False,
        },
        "warning": {
            "label": WARNING_LABEL,
            "template": "{context}{details}",
            "value_style": "plain",
            "show_change": False,
        },
        "error": {
            "label": ERROR_LABEL,
            "template": "{context}: {details}",
            "value_style": "plain",
            "show_change": False,
        },
        "skipped": {
            "label": SKIPPED_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "duplicate": {
            "label": DUPLICATE_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "cache": {
            "label": CACHE_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "discovered": {
            "label": DISCOVERED_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "mapping": {
            "label": MAPPING_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "minimal": {
            "label": MINIMAL_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "moderate": {
            "label": MODERATE_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "major": {
            "label": MAJOR_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
        "preview": {
            "label": PREVIEW_LABEL,
            "template": "{context}",
            "value_style": "plain",
            "show_change": False,
        },
    }

    # --- STAGE 1: INITIALIZATION ---
    def __init__(self, status: str, dry_run: bool = False):
        if status not in self.STATUS_THEMES:
            available = ", ".join(sorted(self.STATUS_THEMES.keys()))
            raise ValueError(f"Unknown status: '{status}'. Available: {available}")
        self.status = status
        self.theme = self.STATUS_THEMES[status]
        self.context_parts = []
        self.explanation = None
        self.old_value = None
        self.new_value = None
        self.value = None
        self.value_style_override = None
        self.dry_run = dry_run

    # --- STAGE 2: CORE CONTEXT BUILDERS (Builds Left-to-Right) ---
    def _apply_style(self, content: str, style: str = None) -> str:
        """Wrap content in Rich markup if style provided and Rich available."""
        if style and RICH_AVAILABLE:
            return f"[{style}]{content}[/{style}]"
        return content

    def add_message(self, message: str, style: str = None):
        """Add a simple message to the main context line.

        Args:
            message: The message text to add
            style: Optional Rich style to apply (e.g., "bold", "hot_pink", "bold turquoise2")
        """
        self.context_parts.append(self._apply_style(message, style))
        return self

    def add_file(self, filepath: str, filename_only: bool = True, style: str = None):
        """
        Add file context to the main message line.

        Args:
            filepath: Path to the file
            filename_only: If True, show only filename; if False, show full path
            style: Optional Rich style to apply to the file path (e.g., "reverse")
        """
        if style:
            # Apply custom style to the file path
            if filename_only:
                filename = Path(filepath).name
                if RICH_AVAILABLE:
                    self.context_parts.append(f"[{style}]{filename}[/{style}]")
                else:
                    self.context_parts.append(filename)
            else:
                path_obj = Path(filepath)
                parent = (
                    str(path_obj.parent) + "/" if path_obj.parent != Path(".") else ""
                )
                if RICH_AVAILABLE:
                    full_path = f"[file.path]{parent}[/file.path][file.name]{path_obj.name}[/file.name]"
                    self.context_parts.append(f"[{style}]{full_path}[/{style}]")
                else:
                    self.context_parts.append(filepath)
        else:
            self.context_parts.append(fmt_file(filepath, filename_only))
        return self

    def add_field(self, field_name: str, value: int, style: str = None):
        """Add a structured field (e.g., 'nameID: 1') to the main message.

        Args:
            field_name: The field name (e.g., "nameID")
            value: The field value (typically an integer)
            style: Optional Rich style to apply (e.g., "bold", "hot_pink", "bold turquoise2")
        """
        field_text = fmt_field(field_name, value)
        self.context_parts.append(self._apply_style(field_text, style))
        return self

    # --- STAGE 3: VALUE SPECIFIERS ---
    def add_values(
        self,
        old_value: str = None,
        new_value: str = None,
        value: str = None,
        style: str = None,
    ):
        """Add value context (e.g., a change from old to new).

        Args:
            old_value: The original value (for change displays)
            new_value: The new value (for change displays)
            value: A single value (for unchanged/created displays)
            style: Optional Rich style to apply to the value(s) (e.g., "bold", "hot_pink")
        """
        if self.theme["show_change"] and old_value and new_value:
            self.old_value = old_value
            self.new_value = new_value
        elif value:
            self.value = value
        if style:
            self.value_style_override = style
        return self

    # --- STAGE 4: DETAIL APPENDERS (Builds Top-to-Bottom) ---
    def with_explanation(self, message: str, style: str = None):
        """
        Add a primary trailing message or reason.

        Often used with 'error' or 'info' statuses to provide context.

        Args:
            message: The explanation text
            style: Optional Rich style to apply (e.g., "dim", "bold red")
        """
        self.explanation = self._apply_style(message, style)
        return self

    def add_item(self, text: str, indent_level: int = 1, style: str = None):
        """
        Add an indented, subordinate line of information.

        Useful for itemizing changes or adding notes beneath the main message.

        Args:
            text: The item text to add
            indent_level: Indentation level (1=12 spaces, 2=14 spaces, etc.)
            style: Optional Rich style to apply (e.g., "bold red", "dim")
        """
        styled_text = self._apply_style(text, style)
        self.context_parts.append(f"\n{indent(indent_level)}{styled_text}")
        return self

    def add_step_log(self, step_log: list):
        """
        Add a step-by-step log of operations applied.

        Args:
            step_log: List of (operation_name, name_before, name_after) tuples
        """
        self._step_log = step_log
        return self

    def with_summary_block(
        self,
        updated: int = 0,
        unchanged: int = 0,
        errors: int = 0,
        additional_info: list = None,
    ):
        """
        Append a final, formatted block of statistics.
        """
        summary_parts = [
            fmt_field("updated", updated),
            fmt_field("unchanged", unchanged),
            fmt_field("errors", errors),
        ]
        summary = " | ".join(summary_parts)
        self.context_parts.append(f"\n{INDENT}{summary}")

        if additional_info:
            for info in additional_info:
                self.context_parts.append(f"\n{INDENT}{info}")
        return self

    def add_indent(self, level: int = 1, additional: int = 0):
        """Add indentation for hierarchical output."""
        self.context_parts.append(f"\n{indent(level, additional)}")
        return self

    # --- STAGE 5: FINALIZERS & STATE MODIFIERS ---
    def build(self) -> str:
        """Build the final formatted status message."""
        # Suppress 'saved' messages in dry-run mode
        if self.dry_run and self.status == "saved":
            return ""

        label = self.theme["label"]

        # Dim operational labels in dry-run mode (not info/warning/error)
        if self.dry_run and self.status not in ["info", "warning", "error", "parsing"]:
            label = f"[dim]{label}[/dim]"

        context = " ".join(self.context_parts)
        # Ensure a single space between context and details when both present
        details = self.explanation or ""
        if (
            details
            and not details.startswith(" ")
            and context
            and "{context}{details}" in self.theme["template"]
        ):
            details = f" {details}"
        message = self.theme["template"].format(context=context, details=details)

        if self.theme["show_change"] and self.old_value and self.new_value:
            change_text = fmt_change(self.old_value, self.new_value)
            if self.value_style_override:
                change_text = f"[{self.value_style_override}]{change_text}[/{self.value_style_override}]"
            message += f"\n{INDENT} {change_text}"
        elif hasattr(self, "value") and self.value:
            style = self.value_style_override or self.theme.get("value_style", "plain")
            value_text = fmt_value(self.value, style)
            if self.value_style_override and style == "plain":
                # Only wrap if we're overriding plain style
                value_text = f"[{self.value_style_override}]{self.value}[/{self.value_style_override}]"
            message += f"\n{INDENT} {value_text}"

        # Add step log if present
        if hasattr(self, "_step_log") and self._step_log:
            for op_name, before, after in self._step_log:
                # Only show if there's an actual change
                if before != after:
                    # Extract just the stem for cleaner display
                    before_stem = Path(before).stem
                    after_stem = Path(after).stem

                    # Use fmt_change to highlight differences
                    change_display = fmt_change(before_stem, after_stem)
                    step_text = f"• {op_name}: {change_display}"
                    message += f"\n{INDENT}  {step_text}"

        return f"{label} {message}"

    def emit(self, console=None):
        """Build and emit the message in one call."""
        _emit = emit
        _emit(self.build(), console=console)


# ============================================================================
# HIGH-LEVEL HELPERS
# ============================================================================
# Convenience functions that use StatusIndicator internally for common patterns


def fmt_preflight_checklist(script_name: str, operations: list, console=None) -> None:
    """
    Display a standardized pre-flight checklist showing what the script will do.

    Args:
        script_name: Name of the script (e.g., "NameID 1 Replacer")
        operations: List of operation descriptions
        console: Optional console instance

    Example:
        >>> fmt_preflight_checklist("NameID 1 Replacer", ["Replace nameID 1", "Update family names"])
        # Displays formatted checklist with script name and operations
    """
    if console is None:
        console = get_console()

    emit("")
    StatusIndicator("info").add_message("Pre-flight checklist:").emit(console)
    emit(f"  Script: {script_name}", console=console)
    emit("  Operations to perform:", console=console)
    for i, operation in enumerate(operations, 1):
        emit(f"    {i}. {operation}", console=console)


def fmt_processing_summary(
    dry_run: bool = False,
    updated: int = 0,
    unchanged: int = 0,
    errors: int = 0,
    console=None,
    additional_info: list = None,
) -> None:
    """
    Display a standardized processing summary.

    Args:
        dry_run: Whether this was a dry run
        updated: Number of files that were updated
        unchanged: Number of files that were unchanged
        errors: Number of files that had errors
        console: Optional console instance
        additional_info: Optional list of additional info lines to display

    Example:
        >>> fmt_processing_summary(dry_run=False, updated=35, unchanged=3, errors=2)
        # Displays "Processing Completed! updated: 35 | unchanged: 3 | errors: 2"
    """
    if console is None:
        console = get_console()

    emit("")
    label = "Preview" if dry_run else "Processing Completed!"
    StatusIndicator("success", dry_run=dry_run).add_message(label).with_summary_block(
        updated=updated,
        unchanged=unchanged,
        errors=errors,
        additional_info=additional_info,
    ).emit(console)


def fmt_operation_description(operation_type: str, details: str) -> str:
    """
    Format a standardized operation description for pre-flight checklist.

    Args:
        operation_type: Type of operation (e.g., "Replace", "Delete", "Create")
        details: Specific details about what will be done

    Returns:
        Formatted operation description

    Example:
        >>> fmt_operation_description("Replace", "nameID 1 (Font Family)")
        "Replace nameID 1 (Font Family)"
    """
    return f"{operation_type} {details}"


def fmt_deletion_operation(
    name_ids: list = None,
    mac_records: bool = False,
    fontsquirrel: bool = False,
    windows_english_only: bool = False,
) -> str:
    """
    Format a deletion operation description.

    Args:
        name_ids: List of name IDs to delete
        mac_records: Whether to delete Macintosh records
        fontsquirrel: Whether to delete FontSquirrel records
        windows_english_only: Whether to keep only Windows/English/Latin records

    Returns:
        Formatted deletion operation description

    Example:
        >>> fmt_deletion_operation(name_ids=[1, 2])
        "Delete nameID 1, 2"
    """
    parts = []
    if name_ids:
        parts.append(f"nameID {', '.join(map(str, sorted(name_ids)))}")
    if mac_records:
        parts.append("Macintosh records (platformID=1)")
    if fontsquirrel:
        parts.append("FontSquirrel records (nameIDs: 200,201,202,203,55555)")
    if windows_english_only:
        parts.append(
            "non-Windows/English/Latin records (keep only platformID=3, platEncID=1, langID=0x409)"
        )

    return f"Delete {', '.join(parts)}"


def fmt_replacement_operation(
    name_id: int, description: str, source: str = None
) -> str:
    """
    Format a replacement operation description.

    Args:
        name_id: The name ID being replaced
        description: Description of the name ID
        source: Source of the replacement value (e.g., "filename parser", "user input")

    Returns:
        Formatted replacement operation description

    Example:
        >>> fmt_replacement_operation(1, "Font Family", "filename parser")
        "Replace nameID 1 (Font Family) using filename parser"
    """
    base = f"Replace nameID {name_id} ({description})"
    if source:
        base += f" using {source}"
    return base


# ============================================================================
# USER INTERACTION
# ============================================================================
# Interactive prompt functions for user input


class QuitRequested(Exception):
    """Exception raised when user requests to quit during batch operations."""

    pass


def prompt_input(message: str, console: Optional["_Console"] = None) -> str:
    """
    Render an INPUT-labeled prompt and return user input using a two-line layout.
    """
    emit("")  # Leading newline for spacing
    result = ""
    try:
        if RICH_AVAILABLE:
            console_instance = console or get_console()
            # 1. Print the informational message
            console_instance.print(f"{INPUT_LABEL} {message}")
            # 2. Print the input prompt on the next line
            console_instance.print(f"{INPUT_LABEL} ", end="")
            result = input()
        else:
            print(f"{INPUT_LABEL} {message}")
            print(f"{INPUT_LABEL} ", end="")
            result = input()

    except (EOFError, KeyboardInterrupt):
        # Return an empty string on interruption
        result = ""
    finally:
        # Ensures a trailing newline
        emit("")

    return result


def prompt_confirm(
    message: str,
    action_prompt: str = "Proceed?",
    default: bool = False,
    allow_quit: bool = False,
) -> bool:
    """
    Yes/no/quit confirmation with a consistent two-line layout.
    Accepts a main message and a separate action prompt for the second line.
    Supports 'q' or 'quit' to raise QuitRequested exception when allow_quit=True.
    """
    emit("")  # Leading newline for spacing

    if allow_quit:
        default_str = "Y/n/q" if default else "y/N/q"
    else:
        default_str = "Y/n" if default else "y/N"
    response_val = default

    try:
        if RICH_AVAILABLE:
            console_instance = get_console()
            # 1. Print the informational message on its own line
            console_instance.print(f"{INPUT_LABEL} {message}")
            # 2. Print the action prompt on the next line
            console_instance.print(
                f"{INPUT_LABEL} {action_prompt} [input][bold]({default_str}): [/bold][/input]",
                end="",
            )
        else:
            print(f"{INPUT_LABEL} {message}")
            print(
                f"{INPUT_LABEL} {action_prompt} [input][bold]({default_str}): [/bold][/input]",
                end="",
            )

        response = input().strip().lower()

        if response in ["y", "yes"]:
            response_val = True
        elif response in ["n", "no", "s", "skip"]:
            response_val = False
        elif response in ["q", "quit", "exit"]:
            if allow_quit:
                raise QuitRequested("User requested to quit batch operation")
            else:
                # In standalone mode, treat 'q' as 'no'
                response_val = False

    except (EOFError, KeyboardInterrupt):
        response_val = False
    finally:
        emit("")

    return response_val


def prompt_text(message: str, default: str = "") -> str:
    """
    Text input using vanilla Python with Rich styling.
    """
    emit("")
    emit(f"{INPUT_LABEL} {message}", console=get_console())

    try:
        if default:
            result = prompt_input(f"[{default}]").strip()
            return result if result else default
        else:
            result = prompt_input(":").strip()
            return result
    except (EOFError, KeyboardInterrupt):
        return default
    finally:
        emit("")


def prompt_select(message: str, choices: list, default=None) -> str:
    """
    Simple numbered selection using vanilla Python with Rich styling.
    """
    emit("")
    emit(f"{INPUT_LABEL} {message}", console=get_console())

    for i, choice in enumerate(choices, 1):
        emit(f"  {i}. {choice}", console=get_console())

    while True:
        try:
            selection = prompt_input("Enter number").strip()
            idx = int(selection) - 1
            if 0 <= idx < len(choices):
                emit("")
                return choices[idx]
            emit(
                f"{WARNING_LABEL} Please select 1-{len(choices)}", console=get_console()
            )
        except (ValueError, EOFError, KeyboardInterrupt):
            emit("")
            return default or choices[0]


# ============================================================================
# STRUCTURED OUTPUT HELPERS
# ============================================================================
# Rich components for complex output layouts


def print_panel(
    message: str,
    title: Optional[str] = None,
    border_style: str = "dodger_blue1",
    console: Optional["_Console"] = None,
) -> None:
    """
    Print a message in a Rich panel (box). Falls back to simple print if Rich unavailable.
    """
    if RICH_AVAILABLE:
        panel = Panel(message, title=title, border_style=border_style)
        (console or get_console()).print(panel)
    else:
        if title:
            print(f"=== {title} ===")
        print(message)
        if title:
            print("=" * (len(title) + 8))


def status_message(
    label: str, details: str = "", console: Optional["_Console"] = None
) -> None:
    """
    Print a status message with a label and optional details.
    """
    if details:
        emit(f"{label} {details}", console=console)
    else:
        emit(label, console=console)


def print_session_header(url: str, console: Optional["_Console"] = None) -> None:
    """
    Print a prominent session header when starting a new site/page.
    """
    if not RICH_AVAILABLE:
        print(f"\n{'=' * 80}")
        print(f"  SESSION: {url}")
        print(f"{'=' * 80}\n")
        return

    console_instance = console or get_console()

    console_instance.print()
    console_instance.print(f"[info.bright]{'═' * 80}[/info.bright]")
    console_instance.print(
        f"[bold][info]  SESSION:[/info][bold] [lighttext][bold]{url}[/lighttext][bold]"
    )
    console_instance.print(f"[info.bright]{'═' * 80}[/info.bright]")
    console_instance.print()


def create_table(
    title: Optional[str] = None,
    show_header: bool = True,
    console: Optional["_Console"] = None,
    row_styles: Optional[list] = None,
) -> Optional["_Table"]:
    """
    Create a Rich Table with consistent styling.
    """
    if not RICH_AVAILABLE:
        return None

    from rich.table import Table

    return Table(
        title=title,
        title_justify="center",
        title_style="bold deep_sky_blue1",
        show_header=show_header,
        header_style="bold dodger_blue1",
        border_style="dim",
        highlight="True",
        row_styles=row_styles,
    )


def create_progress_bar(console: Optional[_Console] = None) -> _Progress:
    """Create a standardized progress bar for consistent styling across scripts."""
    if not RICH_AVAILABLE:
        logger.error("Rich is required for progress bars but not available")
        raise ImportError(
            "Rich is required for progress bars. Install with: pip install rich"
        )

    if console is None:
        console = get_console()
        if console is None:
            logger.error("Failed to get console instance for progress bar")
            raise RuntimeError("Console instance not available")

    try:
        return _Progress(
            SpinnerColumn("dots2", style="dodger_blue1"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        )
    except Exception as e:
        logger.error(f"Failed to create progress bar: {e}")
        raise


# ============================================================================
# DEMO & TESTING
# ============================================================================
# Comprehensive showcase of all console styling features


def _run_demo():
    """
    Comprehensive showcase of all console styling features.

    Run with: python core_console_styles.py
    or: python CoreDemoTool.py console
    """
    console = get_console()

    # ========== STATUS LABELS ==========
    fmt_header("STATUS LABELS", console=console)
    emit(f"{INFO_LABEL} Information message", console=console)
    emit(f"{UPDATED_LABEL} Record updated successfully", console=console)
    emit(f"{UNCHANGED_LABEL} No changes detected", console=console)
    emit(f"{ERROR_LABEL} Error condition occurred", console=console)
    emit(f"{WARNING_LABEL} Warning message", console=console)
    emit(f"{SAVED_LABEL} File saved successfully", console=console)
    emit(f"{CREATED_LABEL} New record created", console=console)
    emit(f"{INPUT_LABEL} User input prompt", console=console)
    emit(f"{PARSING_LABEL} {fmt_file('font.otf')}", console=console)
    emit(f"{SUCCESS_LABEL} Operation completed successfully", console=console)
    emit(f"{SKIPPED_LABEL} Font file skipped", console=console)
    emit(f"{DUPLICATE_LABEL} Duplicate detected (same size)", console=console)
    emit(f"{CACHE_LABEL} Processing cache buffer", console=console)
    emit(f"{DISCOVERED_LABEL} Font mapping discovered", console=console)
    emit(f"{MAPPING_LABEL} Applying name from CSS", console=console)
    emit("", console=console)

    # ========== INDENTATION ==========
    fmt_header("INDENTATION HIERARCHY", console=console)
    emit(f"{INFO_LABEL} Root level item", console=console)
    emit(f"{indent(1)}→ Level 1: immediate details (12 spaces)", console=console)
    emit(f"{indent(2)}→ Level 2: sub-items (14 spaces)", console=console)
    emit(f"{indent(3)}→ Level 3: sub-sub-items (16 spaces)", console=console)
    emit(f"{indent(1, 4)}→ Level 1 with 4 extra spaces (16 total)", console=console)
    emit("", console=console)

    # ========== VALUE FORMATTING ==========
    fmt_header("VALUE FORMATTING", console=console)
    emit(f"  Change: {fmt_change('OldValue', 'NewValue')}", console=console)
    emit(f"  Field: {fmt_field('nameID', 1)}", console=console)
    emit(f"  Count: {fmt_count(42)}", console=console)
    emit(f"  Value (plain): {fmt_value('RegularValue')}", console=console)
    emit(f"  Value (before): {fmt_value('BeforeValue', 'before')}", console=console)
    emit(f"  Value (after): {fmt_value('AfterValue', 'after')}", console=console)
    emit(
        f"  Value (unchanged): {fmt_value('UnchangedValue', 'unchanged')}",
        console=console,
    )
    emit("", console=console)

    # ========== FILE & PATH FORMATTING ==========
    fmt_header("FILE & PATH FORMATTING", console=console)
    emit(
        f"  Filename only: {fmt_file('/long/path/to/MyFont-Bold.otf', filename_only=True)}",
        console=console,
    )
    emit(
        f"  Full path with filename: {fmt_file('/long/path/to/MyFont-Bold.otf', filename_only=False)}",
        console=console,
    )
    emit("", console=console)

    # ========== TEXT STYLING ==========
    fmt_header("TEXT STYLING", console=console)
    emit("  Smart underline (skips descenders):", console=console)
    emit(f"    {fmt_smart_underline('Typography is groovy')}", console=console)
    emit("", console=console)

    # ========== STRUCTURED OUTPUT ==========
    if RICH_AVAILABLE:
        fmt_header("STRUCTURED OUTPUT", console=console)
        print_panel(
            "This is a boxed message panel.\nUseful for important notices, warnings, or summaries.\nSupports multi-line content with Rich markup.",
            title="📋 Notice",
            border_style="dodger_blue1",
            console=console,
        )
        emit("", console=console)

        table = create_table(title="Font Name Records", row_styles=["", "dim"])
        if table:
            table.add_column("nameID", style="cyan", justify="right")
            table.add_column("Description", style="lighttext")
            table.add_column("Value", style="green")
            table.add_row("1", "Font Family", "Kalliope")
            table.add_row("2", "Font Subfamily", "Bold")
            table.add_row("3", "Unique ID", "2.000;CSTM;Kalliope-Bold")
            table.add_row("4", "Full Font Name", "Kalliope Bold")
            table.add_row("6", "PostScript Name", "Kalliope-Bold")
            console.print(table)
        emit("", console=console)

    # ========== NAMERECORD FORMATTERS ==========
    fmt_header("NAMERECORD FORMATTERS", console=console)
    emit(
        StatusIndicator("updated")
        .add_field("nameID", 1)
        .add_file("font.otf", filename_only=False)
        .add_values(old_value="OldName", new_value="NewName")
        .build(),
        console=console,
    )
    emit(
        StatusIndicator("created")
        .add_field("nameID", 2)
        .add_file("font.otf", filename_only=False)
        .add_values(value="CreatedName")
        .build(),
        console=console,
    )

    # Legacy formatter equivalents using StatusIndicator:
    emit(
        StatusIndicator("parsing")
        .add_file("/path/to/font.otf", filename_only=False)
        .build(),
        console=console,
    )
    emit(StatusIndicator("info").add_message("CurrentValue").build(), console=console)
    emit(
        StatusIndicator("unchanged")
        .add_field("nameID", 1)
        .add_file("font.otf")
        .build(),
        console=console,
    )
    emit(
        StatusIndicator("updated").add_field("nameID", 1).add_file("font.otf").build(),
        console=console,
    )
    emit(
        StatusIndicator("created").add_field("nameID", 1).add_file("font.otf").build(),
        console=console,
    )
    emit(
        StatusIndicator("updated")
        .add_values(old_value="OldValue", new_value="NewValue")
        .build(),
        console=console,
    )
    emit(
        StatusIndicator("created").add_values(value="NewValue").build(), console=console
    )
    emit(
        StatusIndicator("deleted").add_field("nameID", 1).add_file("font.otf").build(),
        console=console,
    )
    emit(
        StatusIndicator("saved")
        .add_file("/path/to/font.otf", filename_only=False, style="reverse")
        .build(),
        console=console,
    )
    emit(
        StatusIndicator("info").add_message("achVendID: UKWN").build(), console=console
    )
    emit(
        StatusIndicator("updated")
        .add_message("achVendID")
        .add_values(old_value="UKWN", new_value="CSTM")
        .build(),
        console=console,
    )
    emit("", console=console)

    # ========== STATUS INDICATOR SHOWCASE ==========
    fmt_header("STATUS INDICATOR CLASS", console=console)
    emit("  New unified approach for all status messages:", console=console)
    emit("", console=console)

    # Basic examples
    emit("  Basic usage:", console=console)
    emit(
        f"    {StatusIndicator('updated').add_file('font.otf').build()}",
        console=console,
    )
    emit(
        f"    {StatusIndicator('error').add_file('font.otf').with_explanation('permission denied').build()}",
        console=console,
    )
    emit(
        f"    {StatusIndicator('success').add_file('font.otf').build()}",
        console=console,
    )
    emit("", console=console)

    # NameID examples
    emit("  NameID operations:", console=console)
    emit(
        f"    {StatusIndicator('updated').add_field('nameID', 1).add_file('font.otf').add_values('OldName', 'NewName').build()}",
        console=console,
    )
    emit(
        f"    {StatusIndicator('created').add_field('nameID', 2).add_file('font.otf').add_values(value='NewName').build()}",
        console=console,
    )
    emit(
        f"    {StatusIndicator('unchanged').add_field('nameID', 3).add_file('font.otf').add_values(value='CurrentName').build()}",
        console=console,
    )
    emit("", console=console)

    # Style override examples
    emit("  Style overrides:", console=console)
    emit(
        f"    {StatusIndicator('unchanged').add_field('nameID', 1, style='bold turquoise2').add_file('font.otf').add_values(value='CurrentValue', style='bold').build()}",
        console=console,
    )
    emit(
        f"    {StatusIndicator('info').add_message('Important!', style='bold hot_pink').build()}",
        console=console,
    )
    emit(
        f"    {StatusIndicator('warning').add_file('font.otf').with_explanation('Missing records', style='dim').add_item('nameID 1 not found', style='bold red').build()}",
        console=console,
    )
    emit("", console=console)

    # All status types
    emit("  All 15 status types:", console=console)
    for status in [
        "updated",
        "created",
        "unchanged",
        "deleted",
        "parsing",
        "saved",
        "success",
        "info",
        "warning",
        "error",
        "skipped",
        "duplicate",
        "cache",
        "discovered",
        "mapping",
    ]:
        emit(
            f"    {StatusIndicator(status).add_file('font.otf').build()}",
            console=console,
        )
    emit("", console=console)

    # ========== HIGH-LEVEL HELPERS ==========
    fmt_header("HIGH-LEVEL HELPERS", console=console)
    fmt_preflight_checklist(
        "NameID 1 Replacer",
        [
            fmt_operation_description("Replace", "nameID 1 (Font Family)"),
            fmt_operation_description("Update", "family names from filename"),
        ],
        console=console,
    )
    emit("", console=console)

    # ========== SUMMARY ==========
    fmt_processing_summary(
        dry_run=False,
        updated=35,
        unchanged=3,
        errors=2,
        console=console,
        additional_info=["Demo completed successfully"],
    )


if __name__ == "__main__":
    _run_demo()
