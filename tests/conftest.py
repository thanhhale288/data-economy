"""Root test hooks."""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_TESTS = Path(__file__).resolve().parent


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Tag ML/E2E suites so lean CI can run ``pytest -m 'not ml'``."""
    ml = pytest.mark.ml
    e2e = pytest.mark.e2e
    for item in items:
        try:
            rel = Path(item.path).resolve().relative_to(_REPO_TESTS)
        except (ValueError, AttributeError):
            path_s = str(getattr(item, "fspath", item.path)).replace("\\", "/")
            parts = path_s.split("/tests/")[-1].split("/")
        else:
            parts = rel.parts
        if not parts:
            continue
        if parts[0] == "ml":
            item.add_marker(ml)
        elif parts[0] == "e2e":
            item.add_marker(ml)
            item.add_marker(e2e)
