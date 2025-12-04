"""
Centralized ID policy helpers for constructing NameID values.

Scope (display-layer policy only):
- ID1 (Family), ID4 (Full), ID16 (Typographic Family), ID17 (Typographic Subfamily)
- Handles Variable naming overrides
- Applies style/slope normalization for ID1/ID4 using NameSubfamilyPolicies

Additional shared policies consolidated:
- ID2 subfamily mapping and RIBBI flag computation
- ID3 composition and sanitizers (version/vendor/filename)
- ID5 version string formatting
- ID6 PostScript name sanitization
- Family-level Regular-equivalent detection for non-standard families

Family-level Regular-equivalent detection:
    When a font family doesn't use "Regular" as the base weight, this module can
    identify which alternative term (Book, Normal, Medium, etc.) acts as the family's
    regular weight and apply standard Regular treatment (omit from ID1/ID4).

Demo and Testing:
    Run 'python CoreDemoTool.py policies --help' to see examples of NameID building,
    PostScript sanitization, and variable token stripping.

Maintenance Note:
    When adding new policy functions to this module, update CoreDemoTool.py to showcase
    the new functionality in the 'policies' subcommand.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional, Dict, List

# New imports for enhanced functionality
from FontCore.core_logging_config import get_logger
from FontCore.core_string_utils import normalize_empty, is_empty, join_nonempty

logger = get_logger(__name__)

DEFAULT_REGULAR_SYNONYMS_MODE = "regular_only"

# Canonical list of valid regular-equivalent terms
VALID_REGULAR_EQUIVALENTS = frozenset(
    [
        "Regular",
        "Roman",
        "Plain",
        "Normal",
        "Standard",
        "Book",
        "Text",
        "Medium",
        "Light",
    ]
)


class RegularEquivalentError(ValueError):
    """Raised when an invalid regular_equivalent value is provided."""

    pass


def validate_regular_equivalent(
    value: str | None, *, strict: bool = False
) -> str | None:
    """
    Validate regular_equivalent parameter.

    Args:
        value: The regular_equivalent value to validate
        strict: If True, raise exception on invalid values.
                If False, log warning and return None.

    Returns:
        Validated value or None if invalid

    Raises:
        RegularEquivalentError: If strict=True and value is invalid
    """
    normalized = normalize_empty(value)

    # None or empty is always valid
    if normalized is None:
        return None

    # Check against valid list (case-insensitive)
    if normalized.title() not in VALID_REGULAR_EQUIVALENTS:
        valid_list = ", ".join(sorted(VALID_REGULAR_EQUIVALENTS))
        error_msg = (
            f"Invalid regular_equivalent '{normalized}'. Must be one of: {valid_list}"
        )

        if strict:
            raise RegularEquivalentError(error_msg)
        else:
            logger.warning(f"{error_msg}. Ignoring this parameter.")
            return None

    # Return title-cased version for consistency
    return normalized.title()


def normalize_nfc(value: str | None) -> str | None:
    """Return Unicode NFC-normalized string; pass through None."""
    if value is None:
        return None
    try:
        return unicodedata.normalize("NFC", str(value))
    except Exception:
        return value


# Compound modifier detection for filename parsing warnings
COMPOUND_MODIFIERS = ["semi", "demi", "extra", "ultra", "super", "x"]


def detect_compound_modifier_patterns(
    family: str, style: str, slope: str = None
) -> tuple[bool, list]:
    """Detect compound modifier patterns across family, style, and slope.

    Catches PascalCase splits across ALL font attributes:

    WEIGHTS: "Extra Bold", "Semi Light", "Ultra Black"
    WIDTHS: "Semi Condensed", "Extra Condensed", "Ultra Expanded"
    SLOPES: "Ultra Italic", "Super Italic"

    Returns: (detected, list_of_instances)
    Each instance is: {"source": "family|style|slope", "modifier": "extra", "parsed_as": "Extra Bold"}
    """
    instances = []

    # Check family
    if family:
        words = family.lower().split()
        if len(words) >= 2 and words[0] in COMPOUND_MODIFIERS:
            instances.append(
                {"source": "family", "modifier": words[0], "parsed_as": family}
            )

    # Check style
    if style:
        words = style.lower().split()
        if len(words) >= 2 and words[0] in COMPOUND_MODIFIERS:
            instances.append(
                {"source": "style", "modifier": words[0], "parsed_as": style}
            )

    # Check slope
    if slope:
        words = slope.lower().split()
        if len(words) >= 2 and words[0] in COMPOUND_MODIFIERS:
            instances.append(
                {"source": "slope", "modifier": words[0], "parsed_as": slope}
            )

    return len(instances) > 0, instances


RE_REGULAR = re.compile(r"\b(Regular|Roman)\b", re.I)
RE_ITALIC = re.compile(r"\bItalic\b", re.I)
RE_OBLIQUE = re.compile(r"\bOblique\b", re.I)
RE_SLANTED = re.compile(r"\bSlanted\b", re.I)
RE_BOOK = re.compile(r"\bBook\b", re.I)
RE_NORMAL = re.compile(r"\bNormal\b", re.I)
RE_VARIABLE_TOKENS = re.compile(r"\b(Variable|VF|GX|Flex)\b", re.I)


def _strip_token(pattern: "re.Pattern[str]", text: str) -> tuple[str, bool]:
    new_text, count = pattern.subn("", text)
    new_text = " ".join(new_text.split())
    return new_text, count > 0


def _extract_slope_from_style(style: str) -> tuple[str, str | None]:
    """Extract slope term from style, returning (cleaned_style, slope)."""
    slope = None

    if RE_ITALIC.search(style):
        slope = "Italic"
        style, _ = _strip_token(RE_ITALIC, style)
    elif RE_OBLIQUE.search(style):
        slope = "Oblique"
        style, _ = _strip_token(RE_OBLIQUE, style)
    elif RE_SLANTED.search(style):
        slope = "Slanted"
        style, _ = _strip_token(RE_SLANTED, style)

    return style, slope


def _apply_regular_synonym_mode(
    style: str, mode: str, drop_book: bool | None, drop_normal: bool | None
) -> str:
    """Apply Book/Normal stripping based on mode and explicit flags."""
    # Explicit flags take precedence
    if drop_book is True:
        style, _ = _strip_token(RE_BOOK, style)
    if drop_normal is True:
        style, _ = _strip_token(RE_NORMAL, style)

    # Apply mode if no explicit flags
    if drop_book is None and drop_normal is None:
        mode_lower = (mode or DEFAULT_REGULAR_SYNONYMS_MODE).lower()

        if mode_lower == "loose":
            style, _ = _strip_token(RE_BOOK, style)
            style, _ = _strip_token(RE_NORMAL, style)
        elif mode_lower == "conservative":
            candidate = style.strip().lower()
            if candidate in {"book", "normal"}:
                style, _ = _strip_token(RE_BOOK, style)
                style, _ = _strip_token(RE_NORMAL, style)

    return style


def normalize_style_and_slope_for_id1_id4(
    subfamily_style: str | None,
    slope: str | None,
    *,
    regular_synonyms_mode: str = DEFAULT_REGULAR_SYNONYMS_MODE,
    drop_book: bool | None = None,
    drop_normal: bool | None = None,
    regular_equivalent: str | None = None,
) -> tuple[str | None, str | None]:
    """Normalize a style string for ID1/ID4 policy.

    - Remove Regular/Roman from style
    - If regular_equivalent is provided, also remove that term
    - If Italic/Oblique/Slanted appear in style, move them into slope when slope is not set
    - Idempotent: can be executed repeatedly safely
    """
    # Validate regular_equivalent
    regular_equivalent = validate_regular_equivalent(regular_equivalent, strict=False)

    # Normalize inputs
    subfamily_style = normalize_empty(subfamily_style)
    slope = normalize_empty(slope)

    if is_empty(subfamily_style):
        return None, slope

    style = subfamily_style
    style, _ = _strip_token(RE_REGULAR, style)

    # Strip regular-equivalent term if provided and valid
    if regular_equivalent and regular_equivalent.lower() != "regular":
        equiv_pattern = re.compile(rf"\b{re.escape(regular_equivalent)}\b", re.I)
        style, _ = _strip_token(equiv_pattern, style)

    # Extract and remove slope terms if slope not already set
    slope_norm = slope
    if is_empty(slope_norm):
        style, extracted_slope = _extract_slope_from_style(style)
        slope_norm = extracted_slope
    else:
        # Slope already set, just remove slope terms from style
        style, _ = _extract_slope_from_style(style)

    # Apply Book/Normal handling
    style = _apply_regular_synonym_mode(
        style, regular_synonyms_mode, drop_book, drop_normal
    )

    style = " ".join(style.split())
    return normalize_empty(style), slope_norm


def normalize_subfamily_term(
    term: str, axis_type: str = "unknown", stat_elidable_terms: Optional[set] = None
) -> str:
    """
    Normalize a subfamily term by cleaning up default/suppressible values.

    Args:
        term: The subfamily term to normalize (e.g., "Normal Thin", "Regular")
        axis_type: The axis type ("width", "weight", "slope", "unknown")
        stat_elidable_terms: Optional set of terms marked as elidable in STAT

    Returns:
        Normalized term with suppressible defaults removed

    Examples:
        >>> normalize_subfamily_term("Normal Thin", "weight")
        "Thin"
        >>> normalize_subfamily_term("Normal Regular", "weight")
        "Regular"
        >>> normalize_subfamily_term("Condensed", "width")
        "Condensed"
    """
    # Define suppressible terms per axis type
    WIDTH_SUPPRESSIBLE = {"regular", "normal", "standard", "roman"}
    SLOPE_SUPPRESSIBLE = {"roman", "upright", "normal", "regular"}

    # Clean the term
    cleaned = term.strip()
    cleaned_lower = cleaned.lower()

    # For width/slope: suppress if term matches suppressible list
    if axis_type == "width":
        if any(sup_term in cleaned_lower for sup_term in WIDTH_SUPPRESSIBLE):
            return ""
    elif axis_type == "slope":
        if any(sup_term in cleaned_lower for sup_term in SLOPE_SUPPRESSIBLE):
            return ""

    # For weight: clean up "Normal" prefix but never suppress weight terms
    if axis_type == "weight":
        if cleaned_lower.startswith("normal "):
            cleaned = cleaned[7:].strip()
        elif cleaned_lower == "normal":
            cleaned = "Regular"

    # Use STAT elidable info if provided
    if stat_elidable_terms and cleaned_lower in {
        t.lower() for t in stat_elidable_terms
    }:
        return ""

    return cleaned


def normalize_fvar_name(
    fvar_name: str,
    stat_values: Optional[Dict[str, Dict[float, str]]] = None,
    coordinates: Optional[Dict[str, float]] = None,
) -> str:
    """
    Normalize an fvar instance name using STAT-informed logic.

    Args:
        fvar_name: The fvar instance name (e.g., "Normal Thin", "Condensed Regular")
        stat_values: Optional STAT value mappings {axis_tag: {value: name}}
        coordinates: Optional instance coordinates for axis type detection

    Returns:
        Normalized name with suppressible terms removed

    Examples:
        >>> normalize_fvar_name("Normal Thin")
        "Thin"
        >>> normalize_fvar_name("Condensed Regular")
        "Condensed Regular"
        >>> normalize_fvar_name("Normal Regular")
        "Regular"
    """
    if not fvar_name or fvar_name == "Unknown":
        return fvar_name

    # Split into parts
    parts = fvar_name.split()
    normalized_parts = []

    # Try to classify each part by axis type
    for part in parts:
        part_lower = part.lower()

        # Classify based on common patterns
        # Width terms
        if part_lower in {
            "condensed",
            "compressed",
            "narrow",
            "extended",
            "expanded",
            "wide",
        }:
            axis_type = "width"
        # Weight terms
        elif part_lower in {
            "thin",
            "extralight",
            "light",
            "regular",
            "medium",
            "semibold",
            "bold",
            "extrabold",
            "black",
            "heavy",
        }:
            axis_type = "weight"
        # Slope terms
        elif part_lower in {"italic", "oblique", "slanted", "slant"}:
            axis_type = "slope"
        # Suppressible defaults (could be any axis)
        elif part_lower in {"normal", "standard", "roman", "upright"}:
            # Try to infer from position/context
            # If first word and followed by weight, it's likely width
            # If last word, it's likely slope
            # If standalone or with non-weight, suppress
            idx = parts.index(part)
            if idx == 0 and len(parts) > 1:
                axis_type = "width"  # Likely "Normal Thin" case
            elif idx == len(parts) - 1:
                axis_type = "slope"
            else:
                axis_type = "unknown"
        else:
            axis_type = "unknown"

        # Normalize the part
        normalized = normalize_subfamily_term(part, axis_type)
        if normalized:
            normalized_parts.append(normalized)

    # Join and return, or "Regular" if empty
    result = " ".join(normalized_parts)
    return result if result else "Regular"


def _sanitize_asterisk_for_id1_id4(text: str | None) -> str | None:
    """Sanitize asterisk characters for ID1/ID4 by replacing with space and collapsing.

    Replaces each * with a single space, collapses multiple consecutive spaces to single space,
    and strips leading/trailing spaces. Returns None if input is None.
    """
    if text is None:
        return None
    # Replace * with space
    result = text.replace("*", " ")
    # Collapse multiple spaces to single space
    result = re.sub(r" +", " ", result)
    # Strip leading/trailing spaces
    result = result.strip()
    return result if result else None


def build_id1(
    family: str,
    modifier: str | None,
    style: str | None,
    slope: str | None,
    *,
    is_variable: bool = False,
    variable_family_override: str | None = None,
    use_filename_normalization: bool = True,
    regular_synonyms_mode: str = DEFAULT_REGULAR_SYNONYMS_MODE,
    regular_equivalent: str | None = None,
) -> str:
    """Construct ID1 (Family) string with policy."""
    # Validate regular_equivalent
    regular_equivalent = validate_regular_equivalent(regular_equivalent, strict=False)

    # Variable font policy: Strip "Variable" tokens from family name
    if is_variable:
        base = variable_family_override if variable_family_override else family
        # Sanitize asterisk in base family name
        base = _sanitize_asterisk_for_id1_id4(base) or base
        return strip_variable_tokens(base) or base

    style_eff = style
    slope_eff = slope
    if use_filename_normalization:
        style_eff, slope_eff = normalize_style_and_slope_for_id1_id4(
            style_eff,
            slope_eff,
            regular_synonyms_mode=regular_synonyms_mode,
            regular_equivalent=regular_equivalent,
        )

    # ID1: omit slope if it's "Italic"
    if slope_eff and slope_eff.strip().lower() == "italic":
        slope_eff = None

    # Sanitize asterisk characters for ID1 (replace with space, collapse spaces)
    family = _sanitize_asterisk_for_id1_id4(family) or family
    modifier = _sanitize_asterisk_for_id1_id4(modifier)
    style_eff = _sanitize_asterisk_for_id1_id4(style_eff)
    slope_eff = _sanitize_asterisk_for_id1_id4(slope_eff)

    return join_nonempty(family, modifier, style_eff, slope_eff)


def build_id4(
    family: str,
    modifier: str | None,
    style: str | None,
    slope: str | None,
    *,
    is_variable: bool = False,
    variable_family_override: str | None = None,
    is_italic_font: bool | None = None,
    slope_from_filename: str | None = None,
    use_filename_normalization: bool = True,
    regular_synonyms_mode: str = DEFAULT_REGULAR_SYNONYMS_MODE,
    regular_equivalent: str | None = None,
) -> str:
    """Construct ID4 (Full) string with policy."""

    # Variable font policy: "Family Variable [Slope]"
    if is_variable:
        base = variable_family_override if variable_family_override else family
        # Sanitize asterisk in base family name
        base = _sanitize_asterisk_for_id1_id4(base) or base

        # Prefer explicit filename slope (more accurate)
        if slope_from_filename:
            slope_sanitized = (
                _sanitize_asterisk_for_id1_id4(slope_from_filename)
                or slope_from_filename
            )
            return join_nonempty(base, "Variable", slope_sanitized)

        # Fallback to italic detection
        suffix = "Variable Italic" if is_italic_font else "Variable"
        return join_nonempty(base, suffix)

    style_eff = style
    slope_eff = slope
    if use_filename_normalization:
        style_eff, slope_eff = normalize_style_and_slope_for_id1_id4(
            style_eff,
            slope_eff,
            regular_synonyms_mode=regular_synonyms_mode,
            regular_equivalent=regular_equivalent,
        )

    # Sanitize asterisk characters for ID4 (replace with space, collapse spaces)
    family = _sanitize_asterisk_for_id1_id4(family) or family
    modifier = _sanitize_asterisk_for_id1_id4(modifier)
    style_eff = _sanitize_asterisk_for_id1_id4(style_eff)
    slope_eff = _sanitize_asterisk_for_id1_id4(slope_eff)

    return join_nonempty(family, modifier, style_eff, slope_eff)


def build_id16(
    family: str,
    *,
    is_variable: bool = False,
    variable_family_override: str | None = None,
) -> str:
    """Construct ID16 (Typographic Family). Variable mode appends "Variable"."""

    # Variable font policy: Append "Variable" to family
    if is_variable:
        base = variable_family_override if variable_family_override else family
        return join_nonempty(base, "Variable")

    # Static font logic
    return family


def build_id17(
    modifier: str | None,
    style: str | None,
    slope: str | None,
) -> str:
    """Construct ID17 (Typographic Subfamily).

    ID17 retains Regular/Italic tokens; do not apply filename normalization here.
    Fallback to "Regular" if empty.
    """
    out = join_nonempty(modifier, style, slope)
    return out if out else "Regular"


__all__ = [
    "build_id1",
    "build_id4",
    "build_id16",
    "build_id17",
    "normalize_style_and_slope_for_id1_id4",
    "detect_compound_modifier_patterns",
    # ID2
    "allowed_id2_subfamilies",
    "map_metrics_to_id2_subfamily",
    "compute_ribbi_flags",
    # ID3
    "build_id3",
    "format_vendor_id",
    "is_bad_vendor",
    "prepare_vendor_for_achvendid",
    "sanitize_postscript",
    # ID5
    "format_version_number",
    "build_id5_version_string",
    # Family-level Regular-equivalent detection
    "REGULAR_FALLBACK_PRIORITY",
    "group_fonts_by_family_filename",
    "identify_family_regular_equivalent",
    "get_regular_equivalent_for_families",
    # Variable helpers
    "strip_variable_tokens",
    "variable_filename_fragment",
    "build_id17_variable_default",
    # CFF/CFF2 helpers
    "has_cff_table",
    "has_cff2_table",
    "get_name_string_win_english",
    "sync_cff_names_binary",
]


# ---------- ID2 (Subfamily) policies ----------

allowed_id2_subfamilies = {"Regular", "Italic", "Bold", "Bold Italic"}


def map_metrics_to_id2_subfamily(*, is_bold: bool, is_italic: bool) -> str:
    """Map boolean metrics to one of the allowed ID2 subfamilies."""
    if is_bold and is_italic:
        return "Bold Italic"
    if is_bold:
        return "Bold"
    if is_italic:
        return "Italic"
    return "Regular"


def compute_ribbi_flags(subfamily: str) -> tuple[int, int]:
    """Return (fsSelection, macStyle) integers based on RIBBI subfamily."""
    sub = (subfamily or "").strip().lower()
    is_bold = "bold" in sub
    is_italic = "italic" in sub

    fs_sel = 0
    if is_italic:
        fs_sel |= 0x0001
    if is_bold:
        fs_sel |= 0x0020
    if not is_bold and not is_italic:
        fs_sel |= 0x0040

    mac = 0
    if is_bold:
        mac |= 0x01
    if is_italic:
        mac |= 0x02
    return fs_sel, mac


# ---------- ID3 (Unique identifier) policies ----------

BAD_VENDOR_PATTERNS = {
    "NONE",
    "XXXX",
    "PYRS",
    "HL",
    "HL  ",
    "PFED",
    "TN",
    "TN  ",
}


def format_vendor_id(vendor_value: Any) -> str:
    """Format a vendor value (bytes or string) to a 4-char display string."""
    if vendor_value is None:
        return "UKWN"
    if isinstance(vendor_value, bytes):
        try:
            vendor_str = vendor_value.decode("ascii", errors="ignore")
        except Exception:
            vendor_str = ""
    else:
        vendor_str = str(vendor_value)
    vendor_str = vendor_str.replace("\x00", " ")
    return vendor_str.ljust(4)[:4]


def prepare_vendor_for_achvendid(vendor_str: str) -> bytes:
    """Prepare vendor for OS/2.achVendID (4 chars, spaces padded, ASCII)."""
    return vendor_str[:4].ljust(4).encode("ascii", errors="replace")


def is_bad_vendor(vendor_str: str | None) -> bool:
    if vendor_str is None:
        return True
    normalized = vendor_str.replace("\x00", " ").upper()
    if normalized.strip() == "":
        return True
    if normalized.strip() in BAD_VENDOR_PATTERNS:
        return True
    if set(normalized) <= {" "}:
        return True
    return False


def sanitize_postscript(name: str) -> str:
    """Sanitize PostScript-like names; keep '-', '_', '.', '?', '!', '&'; remove spaces; replace others with '-'."""
    name = name.replace(" ", "")
    return re.sub(r"[^A-Za-z0-9\-\._\?\!\&]", "-", name)


def build_id3(version: str, vendor: str, filename: str) -> str:
    """Compose ID3 content: version;vendor;filename (already sanitized upstream)."""
    return f"{version};{vendor};{filename}"


# ---------- ID5 (Version) policies ----------


def format_version_number(value: Any) -> str:
    """Format a version number to 'x.xxx' string (e.g., 1.0 -> '1.000')."""
    try:
        num = float(value)
        return f"{num:.3f}"
    except Exception:
        return str(value)


def build_id5_version_string(version: str | float) -> str:
    return f"Version {format_version_number(version)}"


# ---------- Family-level Regular-equivalent detection ----------

REGULAR_FALLBACK_PRIORITY = [
    "Roman",
    "Plain",
    "Normal",
    "Book",
    "Text",
    "Medium",
    "Light",
]


def group_fonts_by_family_filename(font_paths: list[str]) -> dict[str, list[str]]:
    """Group font file paths by family name extracted from filename."""
    try:
        from FontCore.core_filename_parts_parser import parse_filename
    except ImportError:
        return _group_fonts_fallback(font_paths)

    families: dict[str, list[str]] = {}
    for path in font_paths:
        parsed = parse_filename(path, strip_extension=True)
        fam = parsed.family if parsed.family else "Unknown"
        families.setdefault(fam, []).append(path)
    return families


def _group_fonts_fallback(font_paths: list[str]) -> dict[str, list[str]]:
    """Fallback grouping when parser not available."""
    import os

    families: dict[str, list[str]] = {}
    for path in font_paths:
        base = os.path.basename(path)
        base_no_ext = os.path.splitext(base)[0]
        fam = base_no_ext.split("-", 1)[0] if "-" in base_no_ext else base_no_ext
        families.setdefault(fam, []).append(path)
    return families


def _extract_weight_term_from_subfamily(subfamily: str) -> str | None:
    """Extract first recognized weight term from subfamily string."""
    if not subfamily:
        return None

    sub_lower = subfamily.lower()

    for term in REGULAR_FALLBACK_PRIORITY:
        if term.lower() in sub_lower:
            return term

    if "regular" in sub_lower:
        return "Regular"

    return None


def _check_text_standalone(subfamily: str) -> bool:
    """Check if 'Text' appears as a standalone optical size, not with weight terms."""
    if not subfamily or "text" not in subfamily.lower():
        return False

    sub_lower = subfamily.lower()

    # Exclude if combined with weight terms
    weight_disqualifiers = [
        "bold",
        "book",
        "normal",
        "medium",
        "black",
        "heavy",
        "extra",
        "semi",
        "demi",
    ]
    if any(w in sub_lower for w in weight_disqualifiers):
        return False

    # Remove slope tokens and see if we're left with just "text"
    temp = sub_lower
    temp = re.sub(r"\b(italic|oblique|slanted)\b", "", temp)
    temp = re.sub(r"[^a-z]+", "", temp)

    return temp == "text"


def _get_usweightclass_from_font(font_path: str) -> int | None:
    """Read usWeightClass from a font file without full table loading."""
    try:
        from fontTools.ttLib import TTFont

        font = TTFont(font_path, lazy=True)
        if "OS/2" in font:
            weight = font["OS/2"].usWeightClass
            font.close()
            return int(weight)
        else:
            logger.debug(f"Font '{font_path}' has no OS/2 table")
    except Exception as e:
        logger.warning(f"Failed to read usWeightClass from '{font_path}': {e}")
    return None


def _check_for_regular_in_filenames(family_paths: list[str]) -> bool:
    """Check if any font in family has 'Regular' in filename."""
    try:
        from FontCore.core_filename_parts_parser import parse_filename
    except ImportError:
        return False

    for path in family_paths:
        parsed = parse_filename(path, strip_extension=True)
        if parsed.subfamily and "regular" in parsed.subfamily.lower():
            return True
    return False


def _find_closest_to_400_weight_term(family_paths: list[str]) -> str | None:
    """Find regular-equivalent term by analyzing which term is closest to weight 400.

    Logic:
    1. For each recognized term (Roman, Plain, Normal, Book, etc.), find fonts with that term
    2. Get average weight for that term across all width variants
    3. Return term closest to 400
    4. On ties, use priority order (REGULAR_FALLBACK_PRIORITY)
    """
    try:
        from FontCore.core_filename_parts_parser import parse_filename
    except ImportError:
        return None

    # Build term -> list of weights mapping
    term_weights: Dict[str, List[int]] = {}

    for path in family_paths:
        weight = _get_usweightclass_from_font(path)
        if weight is None:
            continue

        parsed = parse_filename(path, strip_extension=True)
        if not parsed.subfamily:
            continue

        term = _extract_weight_term_from_subfamily(parsed.subfamily)
        if term:
            if term not in term_weights:
                term_weights[term] = []
            term_weights[term].append(weight)

    if not term_weights:
        return None

    # Calculate average weight for each term
    term_avg_weights: Dict[str, float] = {}
    for term, weights in term_weights.items():
        term_avg_weights[term] = sum(weights) / len(weights)

    # Find term(s) closest to 400
    closest_distance = float("inf")
    closest_terms = []

    for term, avg_weight in term_avg_weights.items():
        distance = abs(avg_weight - 400)
        if distance < closest_distance:
            closest_distance = distance
            closest_terms = [term]
        elif distance == closest_distance:
            closest_terms.append(term)

    # If single winner, return it
    if len(closest_terms) == 1:
        logger.debug(
            f"Found single closest term: {closest_terms[0]} (avg weight: {term_avg_weights[closest_terms[0]]:.1f}, distance: {closest_distance:.1f})"
        )
        return closest_terms[0]

    # Multiple terms at same distance - use priority order
    for candidate in REGULAR_FALLBACK_PRIORITY:
        if candidate in closest_terms:
            logger.debug(
                f"Tie resolved by priority: {candidate} (avg weight: {term_avg_weights[candidate]:.1f}, distance: {closest_distance:.1f})"
            )
            return candidate

    # Fallback to first term found
    result = closest_terms[0] if closest_terms else None
    if result:
        logger.debug(
            f"Fallback selection: {result} (avg weight: {term_avg_weights[result]:.1f}, distance: {closest_distance:.1f})"
        )
    return result


def _find_term_from_filenames(family_paths: list[str]) -> str | None:
    """Find fallback term from filenames by scanning in priority order."""
    try:
        from FontCore.core_filename_parts_parser import parse_filename
    except ImportError:
        return None

    term_counts: dict[str, int] = {}
    text_standalone_count = 0

    for path in family_paths:
        parsed = parse_filename(path, strip_extension=True)
        if not parsed.subfamily:
            continue

        if _check_text_standalone(parsed.subfamily):
            text_standalone_count += 1

        term = _extract_weight_term_from_subfamily(parsed.subfamily)
        if term:
            term_counts[term] = term_counts.get(term, 0) + 1

    # Return first term found in priority order
    for candidate in REGULAR_FALLBACK_PRIORITY:
        if candidate == "Text":
            if text_standalone_count > 0:
                return "Text"
        elif candidate in term_counts:
            return candidate

    return None


def identify_family_regular_equivalent(family_paths: list[str]) -> str | None:
    """Identify which weight term acts as "Regular" for this font family.

    Detection priority:
    1. Check filenames for "Regular"
    2. Check usWeightClass == 400 (must be exactly one match)
    3. Check filenames for fallback terms in priority order
    4. Special handling for "Text" (must be standalone optical size)
    """
    if not family_paths:
        return None

    logger.debug(f"Analyzing {len(family_paths)} fonts for regular equivalent")

    # Step 1: Check for "Regular" in filenames
    if _check_for_regular_in_filenames(family_paths):
        logger.debug("Found 'Regular' in filenames")
        return "Regular"

    # Step 2: Find term closest to weight 400 across all variants
    term = _find_closest_to_400_weight_term(family_paths)
    if term:
        logger.debug(f"Found closest-to-400 term: {term}")
        return term

    # Step 3: Check filenames for fallback terms
    term = _find_term_from_filenames(family_paths)
    if term:
        logger.debug(f"Found fallback term in filenames: {term}")
    else:
        logger.info(
            f"Could not determine regular equivalent for family with {len(family_paths)} fonts"
        )
    return term


def get_regular_equivalent_for_families(font_paths: list[str]) -> dict[str, str | None]:
    """Analyze font files and return per-family regular-equivalent mapping."""
    families = group_fonts_by_family_filename(font_paths)
    return {
        fam: identify_family_regular_equivalent(paths)
        for fam, paths in families.items()
    }


# ---------- Variable font helpers ----------


# Variable font detection functions are now imported from FontCore.core_variable_font_detection


def strip_variable_tokens(text: str | None) -> str | None:
    """Strip Variable/VF/GX/Flex tokens from text."""
    text = normalize_empty(text)
    if is_empty(text):
        return None

    s = str(text)
    s, _ = RE_VARIABLE_TOKENS.subn("", s)
    s = re.sub(r"(?i)(?:^|[-_\s])Variable(?:Italic)?(?=$|[-_\s])", " ", s)
    s = re.sub(r"(?i)(?:^|[-_\s])(VF|GX|Flex)(?=$|[-_\s])", " ", s)

    return normalize_empty(s)


def _strip_trailing_slope_tokens(text: str) -> str:
    s = re.sub(r"[-_\s]*(Italic|Oblique|Slanted)$", "", text, flags=re.I).strip()
    return s


def _collapse_hyphens(text: str) -> str:
    s = re.sub(r"-{2,}", "-", text)
    s = re.sub(r"[-_\s]+$", "", s)
    return s


def normalize_family_for_postscript(family_like: str) -> str:
    s = strip_variable_tokens(family_like) or family_like
    s = _strip_trailing_slope_tokens(s)
    s = _collapse_hyphens(s)
    return sanitize_postscript(s)


def variable_filename_fragment(family: str, is_italic: bool) -> str:
    suffix = "VariableItalic" if is_italic else "Variable"
    clean_family = normalize_family_for_postscript(family)
    return f"{clean_family}-{suffix}"


def build_id17_variable_default(
    is_italic: bool, slope_from_filename: str = None
) -> str:
    """Build ID17 for variable fonts, respecting filename-based slope over italic detection."""
    if slope_from_filename:
        # Use filename-based slope instead of italic detection
        return f"Regular {slope_from_filename}"
    else:
        # Fall back to italic detection only if no filename slope
        return "Regular Italic" if is_italic else "Regular"


def ensure_regular_prefix_for_pure_slope(subfamily: str | None) -> str | None:
    """If subfamily is just Italic/Oblique/Slanted, prefix with 'Regular '."""
    if not subfamily:
        return subfamily
    s = (subfamily or "").strip()
    if s.lower() in {"italic", "oblique", "slanted"}:
        return f"Regular {s}"
    return subfamily


# ---------- CFF/CFF2 helpers ----------


def has_cff_table(font: Any) -> bool:
    try:
        return "CFF " in font
    except Exception:
        return False


def has_cff2_table(font: Any) -> bool:
    try:
        return "CFF2" in font
    except Exception:
        return False


def get_name_string_win_english(font: Any, name_id: int) -> str | None:
    try:
        if "name" not in font:
            return None
        rec = font["name"].getName(name_id, 3, 1, 0x409)
        if rec is None:
            return None
        try:
            return rec.toUnicode()
        except Exception:
            return str(rec)
    except Exception:
        return None


def _update_cff_topdict_field(top, field_name: str, value: str) -> bool:
    """Update a single CFF TopDict field if different."""
    if not value:
        return False

    current = getattr(top, field_name, None)
    if current == value:
        return False

    try:
        setattr(top, field_name, value)
        return True
    except Exception:
        return False


def _sync_cff_table(
    font: Any, ps_name: str | None, full_name: str | None, family_name: str | None
) -> bool:
    """Sync CFF table names."""
    if not has_cff_table(font):
        return False

    changed = False
    try:
        cff_table = font["CFF "]
        cff = getattr(cff_table, "cff", None)
        if cff and hasattr(cff, "topDictIndex"):
            for top in cff.topDictIndex:  # type: ignore[attr-defined]
                if ps_name:
                    changed |= _update_cff_topdict_field(top, "FontName", ps_name)
                if full_name:
                    changed |= _update_cff_topdict_field(top, "FullName", full_name)
                if family_name:
                    changed |= _update_cff_topdict_field(top, "FamilyName", family_name)
    except Exception:
        pass

    return changed


def _sync_cff2_table(font: Any, ps_name: str | None) -> bool:
    """Sync CFF2 table names (FontName only)."""
    if not has_cff2_table(font):
        return False

    changed = False
    try:
        cff2_table = font["CFF2"]
        cff2 = getattr(cff2_table, "cff", None)
        if cff2 and hasattr(cff2, "topDictIndex"):
            for top in cff2.topDictIndex:  # type: ignore[attr-defined]
                if ps_name:
                    changed |= _update_cff_topdict_field(top, "FontName", ps_name)
    except Exception:
        pass

    return changed


def sync_cff_names_binary(font: Any) -> bool:
    """Sync CFF/CFF2 TopDict names from name table (ID 4, 6, 16/1)."""
    try:
        ps_name = get_name_string_win_english(font, 6)
        full_name = get_name_string_win_english(font, 4)
        family16 = get_name_string_win_english(font, 16)
        family1 = get_name_string_win_english(font, 1)
        family_name = family16 or family1

        changed = False
        changed |= _sync_cff_table(font, ps_name, full_name, family_name)
        changed |= _sync_cff2_table(font, ps_name)

        return changed
    except Exception:
        return False
