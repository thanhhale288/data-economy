# Evol-1 T08 — Japan URL-finder calibration (gBizINFO silver)

Status: done (eval 2026-08-25; search blocked HTTP 202; hit 21/300)

## Goal

Run the T03 URL-finder on ~300 Japanese manufacturing firms with government
website URLs, **without leaking those URLs into the finder**. Locale config
only; record any logic change as RQ3.

## DoD

- NTA prefecture frame (Shizuoka / Aichi / Osaka) + PROVENANCE
- gBizINFO silver labels in `data/raw/jp_labels/` (not in identity)
- identity hash in the eval manifest
- JSIC Division E confirmed (製造業)
- Stratified n≈300 by employment band
- P/R/abstain vs T03 n=28
- Worksheet of 30 mismatches for human silver-vs-pipeline review

## Branch

`cursor/evol1-task08-jp-calibration-pilot` — base `main` (T07 merged, PR #85)

## Commands

```bash
PYTHONPATH=. python3 -m crawlers.jp_calibration download-nta
PYTHONPATH=. python3 -m crawlers.jp_calibration sample
PYTHONPATH=. python3 -m crawlers.jp_calibration eval
```

Eval `--limit 20` is a smoke path. Full run is the 300.
