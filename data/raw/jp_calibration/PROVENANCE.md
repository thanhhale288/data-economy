# PROVENANCE — 国税庁法人番号公表サイト (Evol-1 T08)

- Retrieved at (UTC): 2026-08-25T11:38:50Z
- Source: https://www.houjin-bangou.nta.go.jp/download/zenken/ (CSV Unicode, prefecture zips).
- No API token. Monthly full-file POST download (file numbers change each month).
- Prefectures: 静岡県, 愛知県, 大阪府
- Zip files saved: 3
- Parsed latest / not-closed / KK·YK·GK rows: 690857

## What this file is for

Official legal name + address + 法人番号 (13 digits). **No website URL** in this source.
English name / furigana become URL-finder aliases only.

## Limits

- Not an industry frame: NTA has no JSIC. Manufacturing filter is gBizINFO Division E.
- Closed records (`closeDate` set) and `hihyoji=1` are dropped.
- Snapshot is the monthly zenken file on retrieve day.
