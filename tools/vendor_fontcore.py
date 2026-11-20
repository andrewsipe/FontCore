#!/usr/bin/env python3
"""Vendor a FontCore subset into a project, or check that it still matches.

A project lists the FontCore modules it uses in its own pyproject.toml:

    [tool.fontcore-vendor]
    modules = ["core_console_styles", "core_file_collector"]

This script copies those modules, plus every FontCore module they import
(transitively), into <project>/FontCore/, and writes a VENDOR.md that records
exactly which FontCore commit the copy came from.

Usage:
    python tools/vendor_fontcore.py sync  ../Ebrium
    python tools/vendor_fontcore.py check ../Ebrium ../FontFixer ../FontCatalyst
    python tools/vendor_fontcore.py check            # every sibling project with the table

`check` is read-only. It exits 1 when any project differs, and for each
differing file says whether the vendored copy is BEHIND canonical (it matches
an older FontCore revision) or has LOCAL CHANGES (it matches no revision;
a fix may need to be folded back into FontCore).
"""

from __future__ import annotations

import argparse
import ast
import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        sys.exit("Python 3.11+ (or `pip install tomli`) is required to read pyproject.toml")

FONTCORE_ROOT = Path(__file__).resolve().parent.parent
CANONICAL = FONTCORE_ROOT / "src" / "FontCore"
TABLE = "fontcore-vendor"
DEST_NAME = "FontCore"


# --------------------------------------------------------------------------- #
# Module graph
# --------------------------------------------------------------------------- #


def available_modules() -> set[str]:
    return {p.stem for p in CANONICAL.glob("*.py") if p.stem != "__init__"}


def direct_imports(module: str) -> set[str]:
    """FontCore modules imported by `module` (including lazy, in-function imports)."""
    tree = ast.parse((CANONICAL / f"{module}.py").read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "FontCore" and len(parts) > 1:
                    found.add(parts[1])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                parts = node.module.split(".")
                if parts[0] == "FontCore":
                    if len(parts) > 1:
                        found.add(parts[1])
                    else:  # from FontCore import core_x
                        found.update(a.name for a in node.names)
            elif node.level == 1:  # from .core_x import y / from . import core_x
                if node.module:
                    found.add(node.module.split(".")[0])
                else:
                    found.update(a.name for a in node.names)
    return {m for m in found if m in available_modules()}


def closure(requested: list[str]) -> list[str]:
    known = available_modules()
    unknown = [m for m in requested if m not in known]
    if unknown:
        sys.exit(f"Unknown FontCore module(s): {', '.join(unknown)}")
    seen: set[str] = set()
    stack = list(requested)
    while stack:
        mod = stack.pop()
        if mod in seen:
            continue
        seen.add(mod)
        stack.extend(direct_imports(mod) - seen)
    return sorted(seen)


# --------------------------------------------------------------------------- #
# Project config
# --------------------------------------------------------------------------- #


def load_project(project: Path) -> tuple[str, list[str]]:
    pyproject = project / "pyproject.toml"
    if not pyproject.is_file():
        sys.exit(f"{project}: no pyproject.toml")
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    table = data.get("tool", {}).get(TABLE)
    if not table or "modules" not in table:
        sys.exit(f"{project}: pyproject.toml has no [tool.{TABLE}] modules list")
    name = data.get("project", {}).get("name", project.name)
    return name, list(table["modules"])


def discover_projects() -> list[Path]:
    found = []
    for pyproject in sorted(FONTCORE_ROOT.parent.glob("*/pyproject.toml")):
        proj = pyproject.parent
        if proj == FONTCORE_ROOT:
            continue
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except Exception:
            continue
        if TABLE in data.get("tool", {}):
            found.append(proj)
    return found


# --------------------------------------------------------------------------- #
# Git helpers (stamp + ahead/behind detection)
# --------------------------------------------------------------------------- #


def git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(FONTCORE_ROOT), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def fontcore_version() -> str:
    init = (CANONICAL / "__init__.py").read_text(encoding="utf-8")
    for line in init.splitlines():
        if line.startswith("__version__"):
            return line.split("=", 1)[1].strip().strip("\"'")
    return "unknown"


def source_stamp() -> str:
    """e.g. 'v0.2.0' or 'v0.2.0-3-gabc1234' (+ '-dirty' if uncommitted changes)."""
    desc = git("describe", "--tags", "--always", "--dirty")
    return desc or git("rev-parse", "--short", "HEAD") or "unknown"


def historical_blobs(rel: str) -> set[str]:
    """Blob ids of every committed revision of a canonical file."""
    blobs = set()
    for commit in git("log", "--format=%H", "--", rel).splitlines():
        blob = git("rev-parse", f"{commit}:{rel}")
        if blob:
            blobs.add(blob)
    return blobs


def classify_difference(module_file: str, vendored: Path) -> str:
    rel = f"src/FontCore/{module_file}"
    vendored_blob = git("hash-object", str(vendored))
    if vendored_blob and vendored_blob in historical_blobs(rel):
        return "BEHIND (matches an older FontCore revision)"
    return "LOCAL CHANGES (matches no FontCore revision; fold back into FontCore?)"


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def render_init(name: str) -> str:
    return (
        f'"""Vendored FontCore subset used by {name}. Managed by tools/vendor_fontcore.py."""\n'
        f'\n__fontcore_version__ = "{fontcore_version()}"\n'
        f'__fontcore_source__ = "{source_stamp()}"\n'
    )


def render_vendor_md(name: str, requested: list[str], modules: list[str]) -> str:
    pulled = [m for m in modules if m not in requested]
    lines = [
        "# Vendored FontCore subset",
        "",
        f"{name} ships a minimal copy of [FontCore](https://github.com/andrewsipe/FontCore)",
        "so it installs without the full library, a submodule, or a symlink.",
        "",
        f"**Source:** FontCore {fontcore_version()} (`{source_stamp()}`)",
        "",
        "**Do not edit these files here.** Fix them in FontCore, then re-sync.",
        "",
        "## Declared modules",
        "",
        *[f"- `{m}.py`" for m in requested],
    ]
    if pulled:
        lines += ["", "## Pulled in as imports of the above", "", *[f"- `{m}.py`" for m in pulled]]
    lines += [
        "",
        "## Refresh",
        "",
        "From a FontCore checkout:",
        "",
        "```bash",
        f"python tools/vendor_fontcore.py sync ../{name}",
        "```",
        "",
        f"The module list lives in `[tool.{TABLE}]` in this project's `pyproject.toml`.",
        "",
    ]
    return "\n".join(lines)


def cmd_sync(project: Path, dry_run: bool) -> int:
    name, requested = load_project(project)
    modules = closure(requested)
    dest = project / DEST_NAME
    print(f"{name}: {len(requested)} declared -> {len(modules)} modules ({source_stamp()})")
    if source_stamp().endswith("-dirty") and not dry_run:
        print("  warning: FontCore has uncommitted changes; the stamp in VENDOR.md will not be reproducible")
    if dry_run:
        for m in modules:
            print(f"  would write {m}.py")
        return 0
    dest.mkdir(exist_ok=True)
    for m in modules:
        shutil.copyfile(CANONICAL / f"{m}.py", dest / f"{m}.py")
    for stale in sorted(dest.glob("*.py")):
        if stale.stem != "__init__" and stale.stem not in modules:
            print(f"  removed stale {stale.name}")
            stale.unlink()
    (dest / "__init__.py").write_text(render_init(name), encoding="utf-8")
    (dest / "VENDOR.md").write_text(render_vendor_md(name, requested, modules), encoding="utf-8")
    print(f"  wrote {len(modules)} modules + __init__.py + VENDOR.md")
    return 0


def cmd_check(project: Path) -> int:
    name, requested = load_project(project)
    modules = closure(requested)
    dest = project / DEST_NAME
    problems: list[str] = []
    for m in modules:
        f = f"{m}.py"
        vendored = dest / f
        if not vendored.is_file():
            problems.append(f"  MISSING   {f}")
        elif not filecmp.cmp(CANONICAL / f, vendored, shallow=False):
            problems.append(f"  DIFFERS   {f}: {classify_difference(f, vendored)}")
    if dest.is_dir():
        for extra in sorted(dest.glob("*.py")):
            if extra.stem != "__init__" and extra.stem not in modules:
                problems.append(f"  EXTRA     {extra.name}: not declared or imported by a declared module")
    if problems:
        print(f"{name}: OUT OF SYNC")
        print("\n".join(problems))
        return 1
    print(f"{name}: in sync ({len(modules)} modules)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["sync", "check"])
    ap.add_argument("projects", nargs="*", type=Path, help="project directories (default: all siblings with the table)")
    ap.add_argument("-n", "--dry-run", action="store_true", help="sync: show what would be written")
    args = ap.parse_args()

    projects = [p.resolve() for p in args.projects] or discover_projects()
    if not projects:
        sys.exit(f"No projects given and none found with [tool.{TABLE}] next to FontCore")
    status = 0
    for project in projects:
        status |= cmd_sync(project, args.dry_run) if args.command == "sync" else cmd_check(project)
    return status


if __name__ == "__main__":
    sys.exit(main())
