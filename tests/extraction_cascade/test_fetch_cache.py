"""Page cache helpers for extraction cascade."""

from __future__ import annotations

from pathlib import Path

from crawlers.extraction_cascade.fetch import (
    cache_key,
    load_cached_page,
    save_cached_page,
)
from crawlers.extraction_cascade.schema import RenderedPage


def test_cache_roundtrip(tmp_path: Path):
    page = RenderedPage(
        url="https://example.com/",
        final_url="https://example.com/",
        ok=True,
        detail="ok",
        html="<html><body>Giỏ hàng VNPay</body></html>",
        text="Giỏ hàng VNPay",
        status_code=200,
    )
    save_cached_page("DEMO", page, cache_dir=tmp_path)
    loaded = load_cached_page("DEMO", "https://example.com/", cache_dir=tmp_path)
    assert loaded is not None
    assert loaded.ok is True
    assert "Giỏ hàng" in loaded.html
    assert cache_key("DEMO", "https://example.com/").startswith("DEMO_")
