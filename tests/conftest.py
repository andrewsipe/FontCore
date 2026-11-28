import pytest


@pytest.fixture(autouse=True)
def no_personal_slope_overrides(monkeypatch, tmp_path):
    """The resolver reads the user's slope_overrides.txt; tests must not depend on it."""
    monkeypatch.setenv("FONTCORE_SLOPE_OVERRIDES", str(tmp_path / "no_such_overrides.txt"))
