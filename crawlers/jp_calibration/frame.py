"""Join NTA frame + gBizINFO silver labels, sample 300, split URL immediately."""

from __future__ import annotations

import json
import logging
import random
from collections import defaultdict
from typing import Any, Iterable

from crawlers.jp_calibration.gbizinfo import (
    GbizInfoClient,
    STRATA,
    cache_fingerprint,
    search_pool,
)
from crawlers.jp_calibration.identity import load_jp_identity
from crawlers.jp_calibration.nta import extract_csvs, load_nta_frame
from crawlers.jp_calibration.paths import (
    DEFAULT_PREFECTURES,
    IDENTITY_FILE,
    LABELS_FILE,
    PROCESSED_DIR,
    SAMPLE_MANIFEST,
    SAMPLE_N,
    SAMPLE_SEED,
    SEARCH_POOL_FILE,
)
from crawlers.jp_calibration.romaji import kana_to_romaji
from crawlers.url_finder.domain import registrable_domain
from crawlers.url_finder.identity import assert_no_url_fields, sha256_file, utcnow_iso, write_json

logger = logging.getLogger(__name__)

OVERSAMPLE = 40  # unused; cells are shuffled and walked with an attempt cap
MAX_ATTEMPTS_PER_CELL = 120


def _aliases(nta: dict[str, Any] | None, profile: dict[str, Any]) -> list[str]:
    values: list[str] = []
    if nta:
        if nta.get("en_name"):
            values.append(str(nta["en_name"]))
        if nta.get("furigana"):
            romaji = kana_to_romaji(str(nta["furigana"]))
            if romaji:
                values.append(romaji)
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def split_identity_and_label(
    *,
    corporate_number: str,
    nta: dict[str, Any] | None,
    profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """URL goes only to the label row. Identity is what the finder may read."""
    url = str(profile.get("company_url") or "").strip()
    if not url:
        raise ValueError("split requires a company_url on the profile")
    prefecture = (
        (nta or {}).get("prefecture")
        or profile.get("prefecture")
        or ""
    )
    address = str((nta or {}).get("address") or profile.get("address") or "").strip()
    legal = str((nta or {}).get("legal_name") or profile.get("legal_name") or "").strip()
    identity = {
        "ticker": corporate_number,
        "corporate_number": corporate_number,
        "legal_name": legal,
        "tax_id": corporate_number,
        "address": address,
        "province": prefecture,
        "prefecture": prefecture,
        "aliases": _aliases(nta, profile),
        "jsic_raw": profile.get("jsic_raw") or "",
        "jsic_division": profile.get("jsic_division") or "",
        "employee_stratum": profile.get("employee_stratum") or "",
        "source_nta": bool(nta),
        "source_gbizinfo": True,
    }
    assert_no_url_fields(identity, context="jp_calibration.split")
    label = {
        "ticker": corporate_number,
        "gold_url": url,
        "gold_domain": registrable_domain(url),
        "employee_stratum": profile.get("employee_stratum") or "",
        "prefecture": prefecture,
        "employee_number": profile.get("employee_number"),
        "note": "gBizINFO company_url (silver). Not hand-verified; T16 gold comes later.",
    }
    return identity, label


def _pick_cell(
    pool: list[dict[str, str]],
    *,
    prefecture: str,
    stratum: str,
    rng: random.Random,
    k: int,
) -> list[dict[str, str]]:
    cell = [
        row
        for row in pool
        if row.get("prefecture") == prefecture and row.get("search_stratum") == stratum
    ]
    if len(cell) <= k:
        return cell
    return rng.sample(cell, k)


def build_sample(
    *,
    n: int = SAMPLE_N,
    seed: int = SAMPLE_SEED,
    prefectures: Iterable[str] = DEFAULT_PREFECTURES,
    nta_csv_dir=None,
    gbiz: GbizInfoClient | None = None,
    fetch_profiles: bool = True,
) -> dict[str, Any]:
    prefs = tuple(prefectures)
    pool = search_pool(prefs, client=gbiz)
    SEARCH_POOL_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEARCH_POOL_FILE.write_text(
        json.dumps(pool, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    nta = load_nta_frame() if (nta_csv_dir is None) else load_nta_frame(nta_csv_dir)
    rng = random.Random(seed)
    cells = [(p, s["id"]) for p in prefs for s in STRATA]
    per_cell = max(1, n // max(len(cells), 1))
    identities: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    skipped_no_url: list[str] = []
    skipped_not_mfg: list[str] = []
    seen_ids: set[str] = set()
    owns = gbiz is None
    client = gbiz or GbizInfoClient()
    try:
        for pref, stratum_id in cells:
            cell = [
                row
                for row in pool
                if row.get("prefecture") == pref and row.get("search_stratum") == stratum_id
            ]
            rng.shuffle(cell)
            kept = 0
            attempts = 0
            for row in cell:
                if kept >= per_cell:
                    break
                if attempts >= MAX_ATTEMPTS_PER_CELL:
                    break
                attempts += 1
                if kept >= per_cell:
                    break
                number = row["corporate_number"]
                if number in seen_ids:
                    continue
                if fetch_profiles:
                    profile = client.fetch_profile(number)
                else:
                    profile = {
                        **row,
                        "company_url": row.get("company_url") or "",
                        "is_manufacturing": True,
                        "jsic_raw": "E.製造業",
                        "jsic_division": "E",
                        "employee_stratum": stratum_id,
                    }
                if not profile.get("is_manufacturing", True):
                    skipped_not_mfg.append(number)
                    continue
                if not str(profile.get("company_url") or "").strip():
                    skipped_no_url.append(number)
                    continue
                identity, label = split_identity_and_label(
                    corporate_number=number,
                    nta=nta.get(number),
                    profile=profile,
                )
                identities.append(identity)
                labels.append(label)
                seen_ids.add(number)
                kept += 1
            logger.info(
                "sample cell %s %s kept=%s target=%s pool=%s attempts=%s",
                pref,
                stratum_id,
                kept,
                per_cell,
                len(cell),
                attempts,
            )
        if len(identities) < n:
            leftover = [row for row in pool if row["corporate_number"] not in seen_ids]
            large = [r for r in leftover if r.get("search_stratum") in {"51-300", "301+"}]
            small = [r for r in leftover if r.get("search_stratum") not in {"51-300", "301+"}]
            rng.shuffle(large)
            rng.shuffle(small)
            leftover = large + small
            logger.info("filling remainder %s from leftover pool %s", n - len(identities), len(leftover))
            fill_attempts = 0
            for row in leftover:
                if len(identities) >= n:
                    break
                if fill_attempts >= 500:
                    break
                fill_attempts += 1
                if len(identities) >= n:
                    break
                number = row["corporate_number"]
                if number in seen_ids:
                    continue
                if fetch_profiles:
                    profile = client.fetch_profile(number)
                else:
                    continue
                if not profile.get("is_manufacturing", True):
                    skipped_not_mfg.append(number)
                    continue
                if not str(profile.get("company_url") or "").strip():
                    skipped_no_url.append(number)
                    continue
                identity, label = split_identity_and_label(
                    corporate_number=number,
                    nta=nta.get(number),
                    profile=profile,
                )
                identities.append(identity)
                labels.append(label)
                seen_ids.add(number)
    finally:
        if owns:
            client.close()

    # If some cells were short, fill from leftover identities is already the list.
    if len(identities) > n:
        identities = identities[:n]
        labels = labels[:n]

    write_json(IDENTITY_FILE, identities)
    write_json(LABELS_FILE, labels)
    # Fence: re-load identity and refuse if a URL leaked.
    loaded = load_jp_identity(IDENTITY_FILE)
    assert len(loaded) == len(identities)

    counts: dict[str, int] = defaultdict(int)
    for row in identities:
        counts[str(row.get("employee_stratum") or "unknown")] += 1
    manifest = {
        "task": "evol1-t08-jp-calibration-pilot",
        "n": len(identities),
        "seed": seed,
        "prefectures": list(prefs),
        "jsic_division": "E",
        "jsic_division_confirmed": (
            "gBizINFO search checkbox labels manufacturing as Division E (製造業); "
            "profile 業種 field uses the same E.製造業 string."
        ),
        "identity_sha256": sha256_file(IDENTITY_FILE),
        "labels_sha256": sha256_file(LABELS_FILE),
        "search_pool_n": len(pool),
        "search_pool_sha256": cache_fingerprint(pool),
        "nta_join_hits": sum(1 for r in identities if r.get("source_nta")),
        "skipped_no_url": len(skipped_no_url),
        "skipped_not_manufacturing": len(skipped_not_mfg),
        "stratum_counts": dict(counts),
        "generated_at": utcnow_iso(),
        "label_path": str(LABELS_FILE),
        "identity_path": str(IDENTITY_FILE),
        "leak_fence": (
            "Finder reads identity_300.json only. Silver URLs live in "
            "data/raw/jp_labels/labels_300.json and are opened after predictions."
        ),
    }
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def ensure_nta_extracted(zip_paths: Iterable | None = None) -> None:
    if zip_paths:
        extract_csvs(zip_paths)
