"""Join survey form rows to extraction-cascade web flags. No invented websites."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from crawlers.survey_join.estimate import estimate_online_revenue
from crawlers.survey_join.paths import (
    JOINED_CSV_NAME,
    JOINED_JSONL_NAME,
    SUMMARY_JSON_NAME,
    SURVEY_COLUMNS,
    WEB_FLAG_FIELDS,
)

MatchVia = str  # "mst" | "frame_pilot" | "ticker"


class SurveyJoinError(ValueError):
    """Empty/missing survey or invalid input — never invent rows."""


def normalize_mst(raw: Any) -> str:
    """Strip all whitespace; keep hyphen branch suffix (e.g. 0101552800-003)."""
    if raw is None:
        return ""
    return "".join(str(raw).split())


def normalize_ticker(raw: Any) -> str:
    return str(raw or "").strip().upper()


def parse_survey_bool(raw: Any) -> bool | None:
    text = str(raw or "").strip().lower()
    if text in {"", "na", "n/a", "null", "unknown"}:
        return None
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def payment_methods_present(raw: Any) -> bool | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        tokens = [str(x).strip().lower() for x in raw if str(x).strip()]
    else:
        text = str(raw).strip()
        if not text:
            return None
        tokens = [p.strip().lower() for p in text.split(",") if p.strip()]
    nonempty = [t for t in tokens if t not in {"none", "no", "false", "0"}]
    return len(nonempty) > 0


def _fmt_csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if value == 0:
            return "0"
        if value.is_integer():
            return str(int(value))
        return repr(value)
    return str(value)


def load_survey_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SurveyJoinError(f"survey file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        raise SurveyJoinError(f"survey file is empty: {path}")
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise SurveyJoinError(f"survey file has no header: {path}")
        fields = [h.strip() for h in reader.fieldnames if h is not None]
        missing = [c for c in SURVEY_COLUMNS if c not in fields]
        if missing:
            raise SurveyJoinError(
                "survey file missing required columns: " + ", ".join(missing)
            )
        rows: list[dict[str, str]] = []
        for rec in reader:
            rows.append({c: str(rec.get(c) or "") for c in SURVEY_COLUMNS})
    if not rows:
        raise SurveyJoinError(f"survey file has no data rows: {path}")
    return rows


def load_cascade_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SurveyJoinError(f"cascade jsonl not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if isinstance(rec, dict):
                rows.append(rec)
    return rows


def load_frame_tax_codes(path: Path | None) -> set[str]:
    if path is None or not path.exists():
        return set()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "tax_code" not in reader.fieldnames:
            return set()
        out: set[str] = set()
        for rec in reader:
            mst = normalize_mst(rec.get("tax_code"))
            if mst:
                out.add(mst)
        return out


def index_cascade(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """First record wins per normalized firm_id."""
    by_id: dict[str, dict[str, Any]] = {}
    for rec in records:
        firm_id = normalize_mst(rec.get("firm_id"))
        if not firm_id:
            continue
        by_id.setdefault(firm_id, rec)
        ticker_key = normalize_ticker(rec.get("firm_id"))
        if ticker_key and ticker_key not in by_id:
            by_id[ticker_key] = rec
    return by_id


def match_cascade(
    *,
    mst: str,
    ticker: str,
    cascade_by_id: dict[str, dict[str, Any]],
    frame_tax_codes: set[str],
) -> tuple[dict[str, Any] | None, MatchVia | None]:
    """Match order: (1) survey MST == cascade.firm_id, (2) frame_pilot tax_code, (3) ticker.

    Frame-pilot firms use tax_code as cascade ``firm_id``. When the MST is in
    ``frame_pilot.tax_code``, (2) maps that tax_code onto the cascade row and
    records ``web_match_via=frame_pilot`` (otherwise (1) would always win).
    In-frame but not in cascade → no website invented; fall through to ticker.
    """
    # (1) Direct cascade firm_id. Skip when the MST is a frame_pilot tax_code so
    # (2) can record web_match_via=frame_pilot (same row; tax_code IS firm_id).
    if mst and mst in cascade_by_id and mst not in frame_tax_codes:
        return cascade_by_id[mst], "mst"
    if mst and mst in frame_tax_codes:
        mapped = cascade_by_id.get(mst)
        if mapped is not None:
            return mapped, "frame_pilot"
    if ticker and ticker in cascade_by_id:
        return cascade_by_id[ticker], "ticker"
    return None, None


def _tier1_bool(tier1: dict[str, Any] | None, key: str) -> bool | None:
    if not isinstance(tier1, dict) or key not in tier1:
        return None
    return bool(tier1.get(key))


def _tier1_list_present(tier1: dict[str, Any] | None, key: str) -> bool | None:
    if not isinstance(tier1, dict) or key not in tier1:
        return None
    value = tier1.get(key)
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


def _tier1_payment_csv(tier1: dict[str, Any] | None) -> str | None:
    if not isinstance(tier1, dict):
        return None
    value = tier1.get("payment_methods")
    if not isinstance(value, list) or not value:
        return ""
    return ",".join(str(x) for x in value)


def _marketplace_names(tier1: dict[str, Any] | None) -> str | None:
    if not isinstance(tier1, dict):
        return None
    value = tier1.get("marketplace_links")
    if not isinstance(value, list) or not value:
        return ""
    names: list[str] = []
    seen: set[str] = set()
    for item in value:
        if isinstance(item, dict):
            plat = str(item.get("platform") or "").strip()
        else:
            plat = str(item).strip()
        if plat and plat.lower() not in seen:
            seen.add(plat.lower())
            names.append(plat)
    return ",".join(names)


def web_flags_from_cascade(rec: dict[str, Any] | None) -> dict[str, Any]:
    empty = {
        "web_firm_id": None,
        "web_source_cohort": None,
        "web_website_url": None,
        "web_fetch_ok": None,
        "web_has_website": None,
        "web_has_product_catalog": None,
        "web_has_order_cart": None,
        "web_payment_methods": None,
        "web_has_payment_methods": None,
        "web_has_social_links": None,
        "web_has_marketplace_links": None,
        "web_marketplace_names": None,
    }
    if rec is None:
        return empty
    fetch_ok = bool(rec.get("fetch_ok"))
    out = {
        "web_firm_id": rec.get("firm_id"),
        "web_source_cohort": rec.get("source_cohort"),
        "web_website_url": rec.get("website_url") or None,
        "web_fetch_ok": fetch_ok,
        "web_has_website": fetch_ok,
        "web_has_product_catalog": None,
        "web_has_order_cart": None,
        "web_payment_methods": None,
        "web_has_payment_methods": None,
        "web_has_social_links": None,
        "web_has_marketplace_links": None,
        "web_marketplace_names": None,
    }
    if not fetch_ok:
        return out
    tier1 = rec.get("tier1")
    if not isinstance(tier1, dict):
        return out
    out["web_has_product_catalog"] = _tier1_bool(tier1, "has_product_catalog")
    out["web_has_order_cart"] = _tier1_bool(tier1, "has_order_cart")
    out["web_payment_methods"] = _tier1_payment_csv(tier1)
    out["web_has_payment_methods"] = _tier1_list_present(tier1, "payment_methods")
    out["web_has_social_links"] = _tier1_list_present(tier1, "social_links")
    out["web_has_marketplace_links"] = _tier1_list_present(tier1, "marketplace_links")
    out["web_marketplace_names"] = _marketplace_names(tier1)
    return out


def _disagree(survey: bool | None, web: bool | None) -> bool | None:
    if survey is None or web is None:
        return None
    return survey != web


def disagreements(
    survey_row: dict[str, str],
    web: dict[str, Any],
    *,
    fetch_ok: bool,
) -> dict[str, bool | None]:
    keys = {f"disagree_{name}": None for name in WEB_FLAG_FIELDS}
    if not fetch_ok:
        return keys
    survey_payment = payment_methods_present(survey_row.get("payment_methods"))
    return {
        "disagree_has_website": _disagree(
            parse_survey_bool(survey_row.get("has_website")),
            web.get("web_has_website"),
        ),
        "disagree_has_product_catalog": _disagree(
            parse_survey_bool(survey_row.get("has_product_catalog")),
            web.get("web_has_product_catalog"),
        ),
        "disagree_has_order_cart": _disagree(
            parse_survey_bool(survey_row.get("has_order_cart")),
            web.get("web_has_order_cart"),
        ),
        "disagree_has_social_links": _disagree(
            parse_survey_bool(survey_row.get("has_social_links")),
            web.get("web_has_social_links"),
        ),
        "disagree_has_marketplace_links": _disagree(
            parse_survey_bool(survey_row.get("has_marketplace_links")),
            web.get("web_has_marketplace_links"),
        ),
        "disagree_has_payment_methods": _disagree(
            survey_payment,
            web.get("web_has_payment_methods"),
        ),
    }


OUTPUT_COLUMNS: tuple[str, ...] = (
    *SURVEY_COLUMNS,
    "mst_normalized",
    "ticker_normalized",
    "web_match",
    "web_match_via",
    "in_frame_pilot",
    "web_firm_id",
    "web_source_cohort",
    "web_website_url",
    "web_fetch_ok",
    "web_has_website",
    "web_has_product_catalog",
    "web_has_order_cart",
    "web_payment_methods",
    "web_has_payment_methods",
    "web_has_social_links",
    "web_has_marketplace_links",
    "web_marketplace_names",
    "disagree_has_website",
    "disagree_has_product_catalog",
    "disagree_has_order_cart",
    "disagree_has_social_links",
    "disagree_has_marketplace_links",
    "disagree_has_payment_methods",
    "bin_midpoint",
    "estimated_online_revenue",
    "estimate_skipped_reason",
    "estimate_caveat",
)


def join_rows(
    survey_rows: list[dict[str, str]],
    cascade_records: list[dict[str, Any]],
    frame_tax_codes: set[str],
) -> list[dict[str, Any]]:
    cascade_by_id = index_cascade(cascade_records)
    joined: list[dict[str, Any]] = []
    for survey in survey_rows:
        mst = normalize_mst(survey.get("mst"))
        ticker = normalize_ticker(survey.get("ticker"))
        rec, via = match_cascade(
            mst=mst,
            ticker=ticker,
            cascade_by_id=cascade_by_id,
            frame_tax_codes=frame_tax_codes,
        )
        web_match = rec is not None
        web = web_flags_from_cascade(rec)
        fetch_ok = bool(web.get("web_fetch_ok")) if web_match else False
        disag = disagreements(survey, web, fetch_ok=web_match and fetch_ok)
        est = estimate_online_revenue(
            revenue_vnd=survey.get("revenue_vnd"),
            online_revenue_share_bin=survey.get("online_revenue_share_bin"),
        )
        row: dict[str, Any] = {c: survey.get(c, "") for c in SURVEY_COLUMNS}
        row.update(
            {
                "mst_normalized": mst or None,
                "ticker_normalized": ticker or None,
                "web_match": web_match,
                "web_match_via": via,
                "in_frame_pilot": bool(mst) and mst in frame_tax_codes,
                **web,
                **disag,
                "bin_midpoint": est.midpoint,
                "estimated_online_revenue": est.estimated_online_revenue,
                "estimate_skipped_reason": est.skipped_reason,
                "estimate_caveat": est.caveat,
            }
        )
        joined.append(row)
    return joined


def summarize_join(
    rows: list[dict[str, Any]],
    *,
    survey_path: Path,
    cascade_path: Path,
    frame_pilot_path: Path | None,
    frame_pilot_loaded: bool,
) -> dict[str, Any]:
    via_counts = {"mst": 0, "frame_pilot": 0, "ticker": 0}
    skip_reasons: dict[str, int] = {}
    disagree_counts = {f"disagree_{name}": 0 for name in WEB_FLAG_FIELDS}
    n_matched = 0
    n_fetch_ok = 0
    n_estimated = 0
    for row in rows:
        if row.get("web_match"):
            n_matched += 1
            via = row.get("web_match_via")
            if via in via_counts:
                via_counts[via] += 1
        if row.get("web_fetch_ok"):
            n_fetch_ok += 1
        if row.get("estimated_online_revenue") is not None:
            n_estimated += 1
        reason = row.get("estimate_skipped_reason")
        if reason:
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
        for name in WEB_FLAG_FIELDS:
            key = f"disagree_{name}"
            if row.get(key) is True:
                disagree_counts[key] += 1
    return {
        "n_survey_rows": len(rows),
        "n_web_matched": n_matched,
        "n_web_unmatched": len(rows) - n_matched,
        "n_matched_via": via_counts,
        "n_fetch_ok": n_fetch_ok,
        "n_estimated": n_estimated,
        "n_estimate_skipped": sum(skip_reasons.values()),
        "skip_reasons": skip_reasons,
        "n_disagree": disagree_counts,
        "survey_path": str(survey_path),
        "cascade_path": str(cascade_path),
        "frame_pilot_path": str(frame_pilot_path) if frame_pilot_path else None,
        "frame_pilot_loaded": frame_pilot_loaded,
        "real_survey_responses_exist": False,
        "used_seed_financials": False,
        "caveat": (
            "Synthetic or caller-supplied survey CSV only. "
            "Real 100–200 manufacturing-firm responses do not exist yet. "
            "Unmatched rows keep web_match=false and null web flags "
            "(no invented websites). "
            "estimated_online_revenue uses survey revenue_vnd × bin midpoint "
            "and is null when revenue is missing/non-positive or the bin is "
            "unknown/refuse/invalid. Never filled from data/seeds/companies.json."
        ),
    }


def write_outputs(
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
    out_dir: Path,
) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / JOINED_CSV_NAME
    jsonl_path = out_dir / JOINED_JSONL_NAME
    summary_path = out_dir / SUMMARY_JSON_NAME
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(OUTPUT_COLUMNS), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _fmt_csv_cell(row.get(k)) for k in OUTPUT_COLUMNS})
    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in rows:
            payload = {k: row.get(k) for k in OUTPUT_COLUMNS}
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "joined_csv": csv_path,
        "joined_jsonl": jsonl_path,
        "summary_json": summary_path,
    }


def join_survey(
    *,
    survey_path: Path,
    out_dir: Path,
    cascade_path: Path,
    frame_pilot_path: Path | None = None,
) -> dict[str, Any]:
    survey_rows = load_survey_csv(survey_path)
    cascade_records = load_cascade_jsonl(cascade_path)
    frame_loaded = frame_pilot_path is not None and frame_pilot_path.exists()
    frame_tax_codes = load_frame_tax_codes(frame_pilot_path)
    rows = join_rows(survey_rows, cascade_records, frame_tax_codes)
    summary = summarize_join(
        rows,
        survey_path=survey_path,
        cascade_path=cascade_path,
        frame_pilot_path=frame_pilot_path,
        frame_pilot_loaded=frame_loaded,
    )
    paths = write_outputs(rows, summary, out_dir)
    return {"rows": rows, "summary": summary, "paths": paths}
