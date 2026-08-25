"""Write PROVENANCE.md for NTA frame and gBizINFO silver labels."""

from __future__ import annotations

import json

from crawlers.jp_calibration.paths import (
    IDENTITY_FILE,
    LABELS_FILE,
    PROVENANCE_LABELS,
    PROVENANCE_NTA,
    SAMPLE_MANIFEST,
)
from crawlers.url_finder.identity import sha256_file, utcnow_iso


def write_provenance(
    *,
    nta_prefs: list[str],
    nta_zips: int | None,
    nta_rows: int | None,
) -> None:
    if nta_zips is not None and nta_rows is not None:
        _write_nta_provenance(nta_prefs=nta_prefs, nta_zips=nta_zips, nta_rows=nta_rows)
    _write_labels_provenance()


def _write_nta_provenance(*, nta_prefs: list[str], nta_zips: int, nta_rows: int) -> None:
    PROVENANCE_NTA.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_NTA.write_text(
        "\n".join(
            [
                "# PROVENANCE — 国税庁法人番号公表サイト (Evol-1 T08)",
                "",
                f"- Retrieved at (UTC): {utcnow_iso()}",
                "- Source: https://www.houjin-bangou.nta.go.jp/download/zenken/ (CSV Unicode, prefecture zips).",
                "- No API token. Monthly full-file POST download (file numbers change each month).",
                f"- Prefectures: {', '.join(nta_prefs)}",
                f"- Zip files saved: {nta_zips}",
                f"- Parsed latest / not-closed / KK·YK·GK rows: {nta_rows}",
                "",
                "## What this file is for",
                "",
                "Official legal name + address + 法人番号 (13 digits). **No website URL** in this source.",
                "English name / furigana become URL-finder aliases only.",
                "",
                "## Limits",
                "",
                "- Not an industry frame: NTA has no JSIC. Manufacturing filter is gBizINFO Division E.",
                "- Closed records (`closeDate` set) and `hihyoji=1` are dropped.",
                "- Snapshot is the monthly zenken file on retrieve day.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_labels_provenance() -> None:
    PROVENANCE_LABELS.parent.mkdir(parents=True, exist_ok=True)
    identity_hash = sha256_file(IDENTITY_FILE) if IDENTITY_FILE.exists() else "(not written yet)"
    labels_hash = sha256_file(LABELS_FILE) if LABELS_FILE.exists() else "(not written yet)"
    extra: list[str] = []
    if SAMPLE_MANIFEST.exists():
        extra.append(f"- Sample manifest: `{SAMPLE_MANIFEST}`")
        manifest = json.loads(SAMPLE_MANIFEST.read_text(encoding="utf-8"))
        extra.append(
            f"- Sample n={manifest.get('n')}, seed={manifest.get('seed')}, "
            f"nta_join_hits={manifest.get('nta_join_hits')}, "
            f"skipped_no_url={manifest.get('skipped_no_url')} "
            "(profile had no company_url — expected for many small firms)."
        )
        extra.append(f"- Stratum counts: {manifest.get('stratum_counts')}")
    PROVENANCE_LABELS.write_text(
        "\n".join(
            [
                "# PROVENANCE — gBizINFO silver website URLs (Evol-1 T08)",
                "",
                f"- Retrieved at (UTC): {utcnow_iso()}",
                "- Source: public gBizINFO search + profile pages (METI),",
                "  https://info.gbiz.go.jp/ (業種 checkbox **E 製造業**).",
                "- Bulk CSV / REST API were **not** used: both require a free API token",
                "  (`GBIZINFO_API_TOKEN`) which was not present in the environment.",
                "  Public search returns the same company_url field as the bulk file.",
                "",
                "## Split (anti-leak)",
                "",
                f"- Identity (finder input): `{IDENTITY_FILE}` — name, address, 法人番号, JSIC E, aliases.",
                "  **No URL fields.**",
                f"- Labels (evaluator only): `{LABELS_FILE}` — gBizINFO company_url (silver).",
                f"- identity sha256: `{identity_hash}`",
                f"- labels sha256: `{labels_hash}`",
                *extra,
                "",
                "## Silver, not gold",
                "",
                "URLs are self-reported to METI / 職場情報. They can be missing, stale, or point at a parent.",
                "T16 (~100 hand-checked Japan firms) measures that error; T08 treats the field as silver.",
                "",
                "## JSIC Division E",
                "",
                "Confirmed on the gBizINFO 業種 picker: checkbox value `E` = 製造業.",
                "Profile pages show `業種 E.製造業`. This matches proposal-v4 §4.1.",
                "",
                "## Limits",
                "",
                "- Search UI caps a query at 1,000 rows; T08 queries prefecture × employee band to stay under the cap.",
                "- Employee counts come from the profile (often 職場情報). Missing counts → stratum unknown, dropped from the 300.",
                "- Only 株式会社 (code 301) in 静岡 / 愛知 / 大阪.",
                "- Small-firm cells often lack a gBizINFO URL; remainder of n=300 is filled from leftover 51–300 / 301+ (cap 500 attempts). Large firms are slightly over-represented.",
                "- 1/300 identities missed the NTA join (no prefecture on that row).",
                "",
            ]
        ),
        encoding="utf-8",
    )
