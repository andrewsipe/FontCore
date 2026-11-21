"""The version in pyproject.toml and in the package must match: vendored copies are stamped from the package."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_and_package_versions_match():
    pyproject = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M).group(1)
    package = re.search(r'__version__ = "([^"]+)"', (ROOT / "src/FontCore/__init__.py").read_text()).group(1)
    assert pyproject == package
