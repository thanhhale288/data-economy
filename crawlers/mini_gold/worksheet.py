"""Build human worksheet from T05 cascade JSONL (fetch_ok only)."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crawlers.mini_gold.paths import (
    ALL_FIELDS,
    BOOL_FIELDS,
    CASCADE_JSONL,
    CASCADE_MANIFEST,
    LANG_FIELD,
    PAYMENT_FIELD,
    PRESENCE_FIELDS,
    PROVENANCE_MD,
    ROOT,
    SAMPLE_MANIFEST,
    WORKSHEET_CSV,
)

GOLD_EMPTY = ""


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _presence(value: Any) -> bool:
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


def _fmt_payment(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return ""
    return ",".join(str(x) for x in value)


def _fmt_links_brief(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return ""
    parts: list[str] = []
    for item in value[:5]:
        if isinstance(item, dict):
            plat = item.get("platform") or "?"
            url = item.get("url") or ""
            parts.append(f"{plat}:{url}" if url else str(plat))
        else:
            parts.append(str(item))
    extra = len(value) - 5
    if extra > 0:
        parts.append(f"+{extra}")
    return " | ".join(parts)


def _tier2_field(tier2: dict[str, Any] | None, name: str) -> dict[str, Any]:
    if not isinstance(tier2, dict):
        return {"value": None, "abstain": True, "confidence": 0.0, "reason": "missing_tier2"}
    raw = tier2.get(name)
    if not isinstance(raw, dict):
        return {"value": None, "abstain": True, "confidence": 0.0, "reason": "missing_field"}
    return raw


def _pre_t2_bool(f2: dict[str, Any]) -> str:
    if f2.get("abstain"):
        return "abstain"
    val = f2.get("value")
    if val is None:
        return "null"
    return "true" if bool(val) else "false"


def _pre_t2_presence(f2: dict[str, Any]) -> str:
    if f2.get("abstain"):
        return "abstain"
    return "true" if _presence(f2.get("value")) else "false"


def _pre_t2_payment(f2: dict[str, Any]) -> str:
    if f2.get("abstain"):
        return "abstain"
    return _fmt_payment(f2.get("value"))


def _pre_t2_lang(f2: dict[str, Any]) -> str:
    if f2.get("abstain"):
        return "abstain"
    val = f2.get("value")
    return "" if val is None else str(val)


def load_fetch_ok_firms(jsonl_path: Path = CASCADE_JSONL) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if not rec.get("fetch_ok"):
                continue
            rows.append(rec)
    rows.sort(key=lambda r: (r.get("source_cohort") or "", r.get("firm_id") or ""))
    return rows


def firm_to_worksheet_row(rec: dict[str, Any]) -> dict[str, str]:
    tier1 = rec.get("tier1") or {}
    tier2 = rec.get("tier2")
    row: dict[str, str] = {
        "firm_id": str(rec.get("firm_id") or ""),
        "website_url": str(rec.get("website_url") or ""),
        "source_cohort": str(rec.get("source_cohort") or ""),
        "fetch_ok": "true",
        "tier2_decision": str(rec.get("tier2_decision") or ""),
        "model_id": str(rec.get("model_id") or ""),
    }
    # Tier-1 pre
    row["pre_t1_has_product_catalog"] = (
        "true" if tier1.get("has_product_catalog") else "false"
    )
    row["pre_t1_has_order_cart"] = "true" if tier1.get("has_order_cart") else "false"
    row["pre_t1_payment_methods"] = _fmt_payment(tier1.get("payment_methods"))
    row["pre_t1_social_links"] = (
        "true" if _presence(tier1.get("social_links")) else "false"
    )
    row["pre_t1_social_links_detail"] = _fmt_links_brief(tier1.get("social_links"))
    row["pre_t1_marketplace_links"] = (
        "true" if _presence(tier1.get("marketplace_links")) else "false"
    )
    row["pre_t1_marketplace_links_detail"] = _fmt_links_brief(
        tier1.get("marketplace_links")
    )
    row["pre_t1_website_language"] = str(tier1.get("website_language") or "")

    # Tier-2 pre
    for name in BOOL_FIELDS:
        row[f"pre_t2_{name}"] = _pre_t2_bool(_tier2_field(tier2, name))
    row["pre_t2_payment_methods"] = _pre_t2_payment(_tier2_field(tier2, PAYMENT_FIELD))
    for name in PRESENCE_FIELDS:
        row[f"pre_t2_{name}"] = _pre_t2_presence(_tier2_field(tier2, name))
    row["pre_t2_website_language"] = _pre_t2_lang(_tier2_field(tier2, LANG_FIELD))
    row["pre_t2_reason_catalog"] = str(
        _tier2_field(tier2, "has_product_catalog").get("reason") or ""
    )[:200]
    row["pre_t2_reason_cart"] = str(
        _tier2_field(tier2, "has_order_cart").get("reason") or ""
    )[:200]

    # Gold blanks for human
    for name in ALL_FIELDS:
        row[f"gold_{name}"] = GOLD_EMPTY
    row["reviewed"] = "false"
    row["annotator"] = ""
    row["labeled_at"] = ""
    row["notes"] = ""
    return row


def worksheet_fieldnames() -> list[str]:
    base = [
        "firm_id",
        "website_url",
        "source_cohort",
        "fetch_ok",
        "tier2_decision",
        "model_id",
        "pre_t1_has_product_catalog",
        "pre_t1_has_order_cart",
        "pre_t1_payment_methods",
        "pre_t1_social_links",
        "pre_t1_social_links_detail",
        "pre_t1_marketplace_links",
        "pre_t1_marketplace_links_detail",
        "pre_t1_website_language",
        "pre_t2_has_product_catalog",
        "pre_t2_has_order_cart",
        "pre_t2_payment_methods",
        "pre_t2_social_links",
        "pre_t2_marketplace_links",
        "pre_t2_website_language",
        "pre_t2_reason_catalog",
        "pre_t2_reason_cart",
    ]
    gold = [f"gold_{name}" for name in ALL_FIELDS]
    return base + gold + ["reviewed", "annotator", "labeled_at", "notes"]


def build_worksheet_rows(
    jsonl_path: Path = CASCADE_JSONL,
) -> list[dict[str, str]]:
    return [firm_to_worksheet_row(r) for r in load_fetch_ok_firms(jsonl_path)]


def write_worksheet(
    rows: list[dict[str, str]] | None = None,
    *,
    jsonl_path: Path = CASCADE_JSONL,
    out_csv: Path = WORKSHEET_CSV,
) -> dict[str, Any]:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = rows if rows is not None else build_worksheet_rows(jsonl_path)
    fields = worksheet_fieldnames()
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})

    cohort_counts: dict[str, int] = {}
    for row in rows:
        c = row.get("source_cohort") or "unknown"
        cohort_counts[c] = cohort_counts.get(c, 0) + 1

    cascade_sha = _sha256_file(jsonl_path) if jsonl_path.exists() else ""
    manifest_sha = (
        _sha256_file(CASCADE_MANIFEST) if CASCADE_MANIFEST.exists() else ""
    )
    worksheet_sha = _sha256_file(out_csv)

    def rel(p: Path) -> str:
        try:
            return str(p.resolve().relative_to(ROOT))
        except ValueError:
            return str(p)

    meta = {
        "task": "evol1-t06-handbook-mini-gold",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_fetch_ok": len(rows),
        "cohort_counts": cohort_counts,
        "cascade_jsonl": rel(jsonl_path),
        "cascade_jsonl_sha256": cascade_sha,
        "cascade_manifest_sha256": manifest_sha,
        "worksheet_csv": rel(out_csv),
        "worksheet_sha256": worksheet_sha,
        "note": (
            "Gold columns are blank. Humans fill gold_* and set reviewed=true. "
            "pre_* columns are machine hints only — not gold."
        ),
    }

    manifest_path = out_csv.parent / SAMPLE_MANIFEST.name
    provenance_path = out_csv.parent / PROVENANCE_MD.name
    manifest_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    provenance_path.write_text(_render_provenance(meta), encoding="utf-8")
    return meta


def _render_provenance(meta: dict[str, Any]) -> str:
    counts = meta.get("cohort_counts") or {}
    count_lines = "\n".join(f"- {k}: {v}" for k, v in sorted(counts.items()))
    return f"""# PROVENANCE — Mini gold worksheet (Evol-1 T06)

- Generated at (UTC): {meta.get("generated_at")}
- Firms (`fetch_ok` from T05): {meta.get("n_fetch_ok")}
- Cohort counts:
{count_lines}
- Cascade JSONL sha256: `{meta.get("cascade_jsonl_sha256")}`
- Cascade manifest sha256: `{meta.get("cascade_manifest_sha256")}`
- Worksheet sha256: `{meta.get("worksheet_sha256")}`

## Method

1. Take every firm with `fetch_ok=true` from T05 `indicators_raw.jsonl` (no subsample).
2. Copy tier-1 / tier-2 outputs into `pre_*` hint columns.
3. Leave `gold_*` blank for **human** annotation per `docs/annotation-handbook-v1.md`.
4. After humans set `reviewed=true`, run `python -m crawlers.mini_gold eval`.

## Limits

- Pre-labels are **not** gold. Do not treat LLM/rules as ground truth.
- Mini gold on pilot cohort only — not a national estimate.
- T05 HTML page cache may be absent; annotators open live URLs.
"""
