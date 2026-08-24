"""HTML → truncated visible text for local LLM."""

from __future__ import annotations

from ml.local_llm.text import html_to_text


def test_strips_script_and_truncates():
    html = "<html><script>evil()</script><body>" + ("xin chào " * 2000) + "</body></html>"
    text = html_to_text(html, max_chars=100)
    assert "evil" not in text
    assert len(text) <= 100
    assert "xin chào" in text


def test_empty_html():
    assert html_to_text("") == ""
    assert html_to_text(None) == ""  # type: ignore[arg-type]
