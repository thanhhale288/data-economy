"""Benchmark narrative assistant (Task #61) — Vietnamese copy from BenchmarkResult only.

Rules-first templates cite numbers present on the payload. Missing metrics are
skipped or called out as thiếu — never invented. Optional LLM path (env key)
must pass the same number-honesty check or fall back to rules.
"""

from __future__ import annotations

import os
import re
from typing import Any

from backend.app.schemas import BenchmarkResult

# Core ratios the assistant explains (percentile / ROA / ROE focus).
_FOCUS_METRICS: tuple[tuple[str, str], ...] = (
    ("roa", "ROA (tỷ suất sinh lời trên tài sản)"),
    ("roe", "ROE (tỷ suất sinh lời trên vốn chủ sở hữu)"),
)

_COMPARISON_VI = {
    "above_average": "cao hơn trung bình ngành",
    "below_average": "thấp hơn trung bình ngành",
    "average": "xấp xỉ trung bình ngành",
    "insufficient_peers": "chưa đủ peer để so sánh",
}

_LLM_ENV_KEYS = ("BENCHMARK_NARRATIVE_LLM_KEY", "OPENAI_API_KEY")


def _llm_api_key() -> str | None:
    for name in _LLM_ENV_KEYS:
        raw = (os.environ.get(name) or "").strip()
        if raw:
            return raw
    return None


def _as_dict(result: BenchmarkResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(result, BenchmarkResult):
        return result.model_dump()
    if isinstance(result, dict):
        return result
    raise TypeError("result must be BenchmarkResult or dict")


def _fmt_ratio_pct(value: float) -> str:
    """Present unitless ratio as percent with 2 decimals (e.g. 0.0623 → 6.23)."""
    return f"{value * 100:.2f}"


def _fmt_number(value: float, *, digits: int = 2) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.{digits}f}"


def _metric_value(data: dict[str, Any], key: str) -> float | None:
    raw = data.get(key)
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def collect_citeable_tokens(data: dict[str, Any]) -> set[str]:
    """Closed set of numeric strings allowed to appear in narrative text."""
    tokens: set[str] = set()

    def add(value: float) -> None:
        tokens.add(_fmt_number(value, digits=2))
        tokens.add(_fmt_number(value, digits=4))
        tokens.add(_fmt_number(value, digits=1))
        tokens.add(str(int(round(value))))
        # Ratio-as-percent forms commonly used in Vietnamese copy.
        tokens.add(_fmt_ratio_pct(value))
        tokens.add(f"{value * 100:.1f}")
        tokens.add(f"{value * 100:.0f}")

    for key, _ in _FOCUS_METRICS:
        v = _metric_value(data, key)
        if v is not None:
            add(v)

    for mapping_key in ("percentiles", "industry_averages"):
        mapping = data.get(mapping_key) or {}
        if not isinstance(mapping, dict):
            continue
        for key, _ in _FOCUS_METRICS:
            v = mapping.get(key)
            if v is None:
                continue
            try:
                add(float(v))
            except (TypeError, ValueError):
                continue

    peer_count = data.get("peer_count")
    if peer_count is not None:
        try:
            add(float(peer_count))
        except (TypeError, ValueError):
            pass

    peer_scope = data.get("peer_scope")
    if isinstance(peer_scope, str):
        match = re.search(r"vsic_division:(\d+)", peer_scope, flags=re.IGNORECASE)
        if match:
            try:
                add(float(match.group(1)))
            except (TypeError, ValueError):
                pass

    return tokens


_NUMBER_TOKEN_RE = re.compile(r"(?<![A-Za-z_])\d+(?:[.,]\d+)?%?")


def extract_number_tokens(text: str) -> list[str]:
    """Pull numeric tokens from narrative (strip trailing %)."""
    out: list[str] = []
    for match in _NUMBER_TOKEN_RE.finditer(text or ""):
        token = match.group(0).rstrip("%").replace(",", ".")
        out.append(token)
    return out


def narrative_numbers_are_honest(text: str, data: dict[str, Any]) -> bool:
    """True iff every number token in ``text`` is citeable from ``data``."""
    allowed = collect_citeable_tokens(data)
    if not allowed and not extract_number_tokens(text):
        return True
    for token in extract_number_tokens(text):
        if token in allowed:
            continue
        # Also accept exact float parse equality against citeable floats.
        try:
            token_f = float(token)
        except ValueError:
            return False
        matched = False
        for a in allowed:
            try:
                if abs(float(a) - token_f) <= 1e-9:
                    matched = True
                    break
            except ValueError:
                continue
        if not matched:
            return False
    return True


def _rules_paragraphs(data: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    """Build Vietnamese paragraphs + citation records + omitted metric keys."""
    paragraphs: list[str] = []
    citations: list[dict[str, Any]] = []
    omitted: list[str] = []

    peer_count = data.get("peer_count")
    try:
        peer_n = int(peer_count) if peer_count is not None else None
    except (TypeError, ValueError):
        peer_n = None
    peer_scope = data.get("peer_scope")
    warnings = list(data.get("warnings") or [])

    if peer_n is not None:
        scope_bit = f" ({peer_scope})" if peer_scope else ""
        if peer_n == 0:
            paragraphs.append(
                f"Chưa có doanh nghiệp đối chiếu trong mẫu{scope_bit} "
                f"(peer_count = {peer_n}) — không suy diễn phân vị hay trung bình ngành."
            )
        else:
            paragraphs.append(
                f"Đang đối chiếu với {peer_n} doanh nghiệp trong mẫu{scope_bit}."
            )
        citations.append(
            {
                "field": "peer_count",
                "value": peer_n,
                "label": "Số peer",
            }
        )

    if "insufficient_peers" in warnings:
        paragraphs.append(
            "Cảnh báo insufficient_peers: thiếu peer đủ số liệu nên phân vị có thể trống — "
            "không bịa phân vị trung vị."
        )

    percentiles = data.get("percentiles") or {}
    averages = data.get("industry_averages") or {}
    comparison = data.get("comparison") or {}

    for key, label in _FOCUS_METRICS:
        value = _metric_value(data, key)
        if value is None:
            omitted.append(key)
            paragraphs.append(f"Thiếu {label} trong kết quả so sánh — bỏ qua, không bịa số.")
            continue

        value_pct = _fmt_ratio_pct(value)
        parts = [f"{label} của doanh nghiệp là {value_pct}%."]
        citations.append({"field": key, "value": value, "label": label})

        pct_raw = percentiles.get(key) if isinstance(percentiles, dict) else None
        if pct_raw is not None:
            try:
                pct = float(pct_raw)
            except (TypeError, ValueError):
                pct = None
            if pct is not None:
                pct_txt = _fmt_number(pct, digits=1)
                parts.append(
                    f"Phân vị {pct_txt}: cao hơn khoảng {pct_txt}% doanh nghiệp cùng ngành trong mẫu."
                )
                citations.append(
                    {
                        "field": f"percentiles.{key}",
                        "value": pct,
                        "label": f"Phân vị {key.upper()}",
                    }
                )
        else:
            parts.append("Chưa có phân vị (thiếu peer) — không suy diễn xếp hạng.")

        avg_raw = averages.get(key) if isinstance(averages, dict) else None
        if avg_raw is not None:
            try:
                avg = float(avg_raw)
            except (TypeError, ValueError):
                avg = None
            if avg is not None:
                avg_pct = _fmt_ratio_pct(avg)
                parts.append(f"Trung bình ngành trong mẫu: {avg_pct}%.")
                citations.append(
                    {
                        "field": f"industry_averages.{key}",
                        "value": avg,
                        "label": f"TB ngành {key.upper()}",
                    }
                )

        comp = comparison.get(key) if isinstance(comparison, dict) else None
        if isinstance(comp, str) and comp:
            vi = _COMPARISON_VI.get(comp, comp)
            parts.append(f"Nhận xét so với trung bình: {vi}.")

        paragraphs.append(" ".join(parts))

    if not paragraphs:
        paragraphs.append(
            "Không có chỉ số BenchmarkResult để giải thích — không bịa ROA/ROE/phân vị."
        )

    return paragraphs, citations, omitted


def _try_llm_polish(paragraphs: list[str], data: dict[str, Any]) -> str | None:
    """Optional LLM rewrite. Returns None when key missing or call/honesty fails."""
    api_key = _llm_api_key()
    if not api_key:
        return None

    base_text = "\n".join(paragraphs)
    # Keep optional path dependency-light: httpx already in requirements.
    try:
        import httpx
    except ImportError:
        return None

    prompt = (
        "Viết lại đoạn giải thích benchmark sau bằng tiếng Việt tự nhiên. "
        "CHỈ được dùng đúng các con số đã có trong đoạn gốc; tuyệt đối không thêm số mới.\n\n"
        f"{base_text}"
    )
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": os.environ.get("BENCHMARK_NARRATIVE_LLM_MODEL", "gpt-4o-mini"),
                "temperature": 0,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You rewrite Vietnamese financial benchmark explanations. "
                            "Never invent numbers."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
        text = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )
        if not isinstance(text, str) or not text.strip():
            return None
        text = text.strip()
        if not narrative_numbers_are_honest(text, data):
            return None
        return text
    except Exception:
        return None


def generate_benchmark_narrative(
    result: BenchmarkResult | dict[str, Any],
) -> dict[str, Any]:
    """Return Vietnamese narrative payload citing only BenchmarkResult numbers."""
    data = _as_dict(result)
    paragraphs, citations, omitted = _rules_paragraphs(data)
    rules_text = "\n\n".join(paragraphs)

    method = "rules"
    narrative = rules_text
    warnings: list[str] = []

    llm_text = _try_llm_polish(paragraphs, data)
    if llm_text is not None:
        method = "llm"
        narrative = llm_text
    elif _llm_api_key():
        warnings.append("llm_fallback_rules")

    # Final honesty gate (rules path is constructed from citations; still verify).
    if not narrative_numbers_are_honest(narrative, data):
        narrative = rules_text
        method = "rules"
        warnings.append("honesty_rewrite_rejected")

    return {
        "narrative": narrative,
        "paragraphs": paragraphs,
        "method": method,
        "citations": citations,
        "omitted": omitted,
        "warnings": warnings,
        "message": (
            None
            if citations
            else "Không có số liệu trong BenchmarkResult để trích dẫn — không bịa."
        ),
    }
