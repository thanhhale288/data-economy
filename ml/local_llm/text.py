"""Turn HTML into truncated visible text for the local LLM."""

from __future__ import annotations

from bs4 import BeautifulSoup

DEFAULT_MAX_CHARS = 8000


def html_to_text(html: str, *, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """Visible text only; scripts/styles dropped. Truncate, do not invent."""
    if not html or not str(html).strip():
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ", strip=True).split())
    if len(text) <= max_chars:
        return text
    return text[:max_chars]
