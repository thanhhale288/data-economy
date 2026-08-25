# PROVENANCE — gBizINFO silver website URLs (Evol-1 T08)

- Retrieved at (UTC): 2026-08-25T11:52:44Z
- Source: public gBizINFO search + profile pages (METI),
  https://info.gbiz.go.jp/ (業種 checkbox **E 製造業**).
- Bulk CSV / REST API were **not** used: both require a free API token
  (`GBIZINFO_API_TOKEN`) which was not present in the environment.
  Public search returns the same company_url field as the bulk file.

## Split (anti-leak)

- Identity (finder input): `/Users/hale/Code/AI in Data Economy-t08/data/raw/jp_calibration/identity_300.json` — name, address, 法人番号, JSIC E, aliases.
  **No URL fields.**
- Labels (evaluator only): `/Users/hale/Code/AI in Data Economy-t08/data/raw/jp_labels/labels_300.json` — gBizINFO company_url (silver).
- identity sha256: `8542b9f01b7d96e540f286910151185cc88ac1b7d79050472178ff1e867cb860`
- labels sha256: `01fdbd74832cd402ada914393c0ad5be5f23acd44f44444761fc9b47a903c531`
- Sample manifest: `/Users/hale/Code/AI in Data Economy-t08/data/processed/jp_calibration/sample_manifest.json`
- Sample n=300, seed=20260825, nta_join_hits=299, skipped_no_url=623 (profile had no company_url — expected for many small firms).
- Stratum counts: {'0-20': 56, '21-50': 75, '51-300': 88, '301+': 81}

## Silver, not gold

URLs are self-reported to METI / 職場情報. They can be missing, stale, or point at a parent.
T16 (~100 hand-checked Japan firms) measures that error; T08 treats the field as silver.

## JSIC Division E

Confirmed on the gBizINFO 業種 picker: checkbox value `E` = 製造業.
Profile pages show `業種 E.製造業`. This matches proposal-v4 §4.1.

## Limits

- Search UI caps a query at 1,000 rows; T08 queries prefecture × employee band to stay under the cap.
- Employee counts come from the profile (often 職場情報). Missing counts → stratum unknown, dropped from the 300.
- Only 株式会社 (code 301) in 静岡 / 愛知 / 大阪.
- Small-firm cells often lack a gBizINFO URL; remainder of n=300 is filled from leftover 51–300 / 301+ (cap 500 attempts). Large firms are slightly over-represented.
- 1/300 identities missed the NTA join (no prefecture on that row).
