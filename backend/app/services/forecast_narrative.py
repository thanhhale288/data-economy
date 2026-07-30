"""Forecast narrative assistant (Task #62) — Vietnamese copy from forecast + artifacts only.

Rules-first templates cite numbers present on the forecast payload, registry
error metrics, and feature-importance artifact. Missing importance → nói thiếu;
never invent causal drivers. Optional LLM polish must pass the same honesty gate.
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from backend.app.services import ml_lab_service

_METRIC_KEYS: tuple[tuple[str, str], ...] = (
    ("mae", "MAE"),
    ("rmse", "RMSE"),
    ("mape", "MAPE"),
)

_TREE_MODELS = frozenset({"xgboost", "lightgbm"})
_LLM_ENV_KEYS = ("FORECAST_NARRATIVE_LLM_KEY", "OPENAI_API_KEY")
_TOP_DRIVERS = 3

_NUMBER_TOKEN_RE = re.compile(r"(?<![A-Za-z_])\d+(?:[.,]\d+)?%?")


def _llm_api_key() -> str | None:
    for name in _LLM_ENV_KEYS:
        raw = (os.environ.get(name) or "").strip()
        if raw:
            return raw
    return None


def _fmt_number(value: float, *, digits: int = 2) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.{digits}f}"


def _as_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _period_str(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    if isinstance(raw, date):
        return raw.isoformat()
    text = str(raw).strip()
    return text[:10] if text else None


def _normalize_forecast(payload: dict[str, Any]) -> dict[str, Any]:
    model = str(payload.get("model") or payload.get("model_name") or "").strip().lower()
    horizon = payload.get("horizon")
    if horizon is None:
        horizon = payload.get("horizon_months")
    horizon_f = _as_float(horizon)
    horizon_i = int(horizon_f) if horizon_f is not None else None

    points: list[dict[str, Any]] = []
    for row in payload.get("forecasts") or []:
        if not isinstance(row, dict):
            continue
        value = _as_float(row.get("predicted_value"))
        if value is None:
            continue
        points.append(
            {
                "period": _period_str(row.get("period")),
                "predicted_value": value,
            }
        )

    return {
        "model": model or "unknown",
        "horizon": horizon_i,
        "forecasts": points,
        "metrics": payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {},
    }


def _resolve_importance(
    model: str,
    importance: dict[str, Any] | None,
    *,
    load_importance: bool,
    artifact_dir: Path | str | None,
) -> dict[str, Any]:
    if isinstance(importance, dict) and importance:
        # Explicit payload (tests / client override) — do not invent.
        if "available" in importance:
            return importance
        gain = importance.get("gain")
        features = importance.get("features")
        if isinstance(features, list) and features:
            return {**importance, "available": True, "message": None}
        if isinstance(gain, dict) and gain:
            ranked = sorted(gain.items(), key=lambda kv: float(kv[1]), reverse=True)
            return {
                "available": True,
                "model_name": model,
                "gain": {str(k): float(v) for k, v in gain.items()},
                "features": [
                    {"feature": str(k), "gain": float(v)} for k, v in ranked
                ],
                "message": None,
            }
        return {
            "available": False,
            "model_name": model,
            "features": [],
            "gain": {},
            "message": importance.get("message")
            or "Thiếu feature importance trong payload — không bịa driver.",
        }

    if not load_importance:
        return {
            "available": False,
            "model_name": model,
            "features": [],
            "gain": {},
            "message": "Không tải feature importance — không suy diễn nguyên nhân.",
        }

    return ml_lab_service.get_feature_importance(model, artifact_dir=artifact_dir)


def collect_citeable_tokens(
    data: dict[str, Any],
    importance: dict[str, Any] | None = None,
) -> set[str]:
    """Closed set of numeric strings allowed to appear in narrative text."""
    tokens: set[str] = set()

    def add(value: float) -> None:
        tokens.add(_fmt_number(value, digits=2))
        tokens.add(_fmt_number(value, digits=4))
        tokens.add(_fmt_number(value, digits=1))
        tokens.add(str(int(round(value))))
        tokens.add(f"{value:.2f}")
        tokens.add(f"{value:.1f}")
        tokens.add(f"{value:.0f}")

    horizon = data.get("horizon")
    if horizon is not None:
        add(float(horizon))

    for point in data.get("forecasts") or []:
        value = _as_float(point.get("predicted_value"))
        if value is not None:
            add(value)
        period = point.get("period")
        if isinstance(period, str):
            for part in re.findall(r"\d+", period):
                tokens.add(part)
                tokens.add(part.lstrip("0") or "0")
                try:
                    add(float(part))
                except ValueError:
                    continue

    metrics = data.get("metrics") or {}
    if isinstance(metrics, dict):
        for key, _ in _METRIC_KEYS:
            v = _as_float(metrics.get(key))
            if v is not None:
                add(v)

    imp = importance or {}
    if imp.get("available"):
        features = imp.get("features") or []
        if isinstance(features, list):
            for row in features[:_TOP_DRIVERS]:
                if not isinstance(row, dict):
                    continue
                g = _as_float(row.get("gain"))
                if g is not None:
                    add(g)
        gain = imp.get("gain") or {}
        if isinstance(gain, dict):
            ranked = sorted(
                ((str(k), float(v)) for k, v in gain.items() if _as_float(v) is not None),
                key=lambda kv: kv[1],
                reverse=True,
            )
            for _, score in ranked[:_TOP_DRIVERS]:
                add(score)

    return tokens


def extract_number_tokens(text: str) -> list[str]:
    """Pull numeric tokens from narrative (strip trailing %)."""
    out: list[str] = []
    for match in _NUMBER_TOKEN_RE.finditer(text or ""):
        token = match.group(0).rstrip("%").replace(",", ".")
        out.append(token)
    return out


def narrative_numbers_are_honest(
    text: str,
    data: dict[str, Any],
    importance: dict[str, Any] | None = None,
) -> bool:
    """True iff every number token in ``text`` is citeable from payload/artifacts."""
    allowed = collect_citeable_tokens(data, importance)
    if not allowed and not extract_number_tokens(text):
        return True
    for token in extract_number_tokens(text):
        if token in allowed:
            continue
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


def _top_driver_rows(importance: dict[str, Any]) -> list[dict[str, Any]]:
    features = importance.get("features")
    rows: list[dict[str, Any]] = []
    if isinstance(features, list) and features:
        for row in features:
            if not isinstance(row, dict):
                continue
            name = row.get("feature")
            gain = _as_float(row.get("gain"))
            if not name or gain is None:
                continue
            if gain <= 0:
                continue
            rows.append({"feature": str(name), "gain": gain})
    else:
        gain_map = importance.get("gain") or {}
        if isinstance(gain_map, dict):
            for name, raw in gain_map.items():
                gain = _as_float(raw)
                if gain is None or gain <= 0:
                    continue
                rows.append({"feature": str(name), "gain": gain})
        rows.sort(key=lambda r: r["gain"], reverse=True)
    return rows[:_TOP_DRIVERS]


def _rules_paragraphs(
    data: dict[str, Any],
    importance: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    paragraphs: list[str] = []
    citations: list[dict[str, Any]] = []
    omitted: list[str] = []

    model = data.get("model") or "unknown"
    horizon = data.get("horizon")
    forecasts = data.get("forecasts") or []

    if horizon is not None:
        paragraphs.append(
            f"Dự báo IIP trên horizon {horizon} tháng bằng model «{model}»."
        )
        citations.append(
            {"field": "horizon", "value": int(horizon), "label": "Horizon (tháng)"}
        )
    else:
        omitted.append("horizon")
        paragraphs.append("Thiếu horizon trong kết quả forecast — không bịa độ dài dự báo.")

    if forecasts:
        value_bits: list[str] = []
        for idx, point in enumerate(forecasts):
            value = point["predicted_value"]
            value_txt = _fmt_number(value, digits=2)
            period = point.get("period")
            if period:
                # Prefer YYYY-MM for readability; year/month still citeable.
                label = str(period)[:7]
                value_bits.append(f"{label}: {value_txt}")
            else:
                value_bits.append(value_txt)
            citations.append(
                {
                    "field": f"forecasts[{idx}].predicted_value",
                    "value": value,
                    "label": f"Dự báo kỳ {idx + 1}",
                }
            )
        paragraphs.append(
            "Giá trị dự báo (từ forecast API): " + "; ".join(value_bits) + "."
        )
    else:
        omitted.append("forecasts")
        paragraphs.append("Thiếu chuỗi forecasts — không bịa đường dự báo.")

    metrics = data.get("metrics") or {}
    metric_parts: list[str] = []
    for key, label in _METRIC_KEYS:
        value = _as_float(metrics.get(key)) if isinstance(metrics, dict) else None
        if value is None:
            omitted.append(key)
            continue
        txt = _fmt_number(value, digits=2)
        if key == "mape":
            metric_parts.append(f"{label} = {txt}%")
        else:
            metric_parts.append(f"{label} = {txt}")
        citations.append({"field": f"metrics.{key}", "value": value, "label": label})

    if metric_parts:
        paragraphs.append(
            "Sai số trên holdout/registry (không phải khoảng tin cậy của đường dự báo): "
            + "; ".join(metric_parts)
            + "."
        )
    else:
        paragraphs.append(
            "Thiếu sai số MAE/RMSE/MAPE trong registry — không bịa độ chính xác."
        )

    if importance.get("available"):
        drivers = _top_driver_rows(importance)
        if drivers:
            bits = [
                f"{d['feature']} (gain = {_fmt_number(d['gain'], digits=2)})"
                for d in drivers
            ]
            paragraphs.append(
                "Driver chính theo feature importance (gain, không suy diễn nguyên nhân "
                "ngoài artifact): "
                + "; ".join(bits)
                + "."
            )
            for d in drivers:
                citations.append(
                    {
                        "field": f"importance.gain.{d['feature']}",
                        "value": d["gain"],
                        "label": f"Gain {d['feature']}",
                    }
                )
        else:
            omitted.append("importance_positive_gain")
            paragraphs.append(
                "Có artifact feature importance nhưng không có gain > 0 để xếp driver — "
                "không suy diễn nguyên nhân."
            )
    else:
        omitted.append("importance")
        msg = importance.get("message")
        if model in _TREE_MODELS:
            paragraphs.append(
                msg
                or (
                    f"Thiếu feature importance cho «{model}» "
                    f"({model}_importance.json) — không bịa driver."
                )
            )
        else:
            paragraphs.append(
                msg
                or (
                    f"Model «{model}» không có feature-importance artifact — "
                    "không suy diễn nguyên nhân từ importance."
                )
            )

    if not paragraphs:
        paragraphs.append(
            "Không có số liệu forecast để giải thích — không bịa horizon/sai số/driver."
        )

    return paragraphs, citations, omitted


def _try_llm_polish(
    paragraphs: list[str],
    data: dict[str, Any],
    importance: dict[str, Any],
) -> str | None:
    api_key = _llm_api_key()
    if not api_key:
        return None

    base_text = "\n".join(paragraphs)
    try:
        import httpx
    except ImportError:
        return None

    prompt = (
        "Viết lại đoạn tóm tắt dự báo IIP sau bằng tiếng Việt tự nhiên. "
        "CHỈ được dùng đúng các con số đã có trong đoạn gốc; tuyệt đối không thêm số mới "
        "và không bịa nguyên nhân ngoài feature importance đã nêu.\n\n"
        f"{base_text}"
    )
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": os.environ.get("FORECAST_NARRATIVE_LLM_MODEL", "gpt-4o-mini"),
                "temperature": 0,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You rewrite Vietnamese IIP forecast summaries. "
                            "Never invent numbers or causal drivers."
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
        if not narrative_numbers_are_honest(text, data, importance):
            return None
        return text
    except Exception:
        return None


def generate_forecast_narrative(
    forecast: dict[str, Any],
    *,
    metrics: dict[str, Any] | None = None,
    importance: dict[str, Any] | None = None,
    load_importance: bool = True,
    artifact_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Return Vietnamese narrative citing only forecast + metrics + importance numbers."""
    data = _normalize_forecast({**forecast, "metrics": metrics or forecast.get("metrics")})
    imp = _resolve_importance(
        data["model"],
        importance,
        load_importance=load_importance,
        artifact_dir=artifact_dir,
    )

    paragraphs, citations, omitted = _rules_paragraphs(data, imp)
    rules_text = "\n\n".join(paragraphs)

    method = "rules"
    narrative = rules_text
    warnings: list[str] = []

    llm_text = _try_llm_polish(paragraphs, data, imp)
    if llm_text is not None:
        method = "llm"
        narrative = llm_text
    elif _llm_api_key():
        warnings.append("llm_fallback_rules")

    if not narrative_numbers_are_honest(narrative, data, imp):
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
        "importance_available": bool(imp.get("available")),
        "message": (
            None
            if citations
            else "Không có số liệu forecast/importance để trích dẫn — không bịa."
        ),
    }
