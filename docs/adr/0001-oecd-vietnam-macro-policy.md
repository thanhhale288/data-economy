# ADR-0001: OECD Vietnam macro policy & frequency harmonization

## Status

Accepted — 2026-07-18

## Context

OECD does not publish MEI Industrial Production, Business Confidence, or ICT
investment GFCF for Vietnam (`VNM`). INDIGO (digital trade openness) does exist
for VNM as an **annual** series. The project focuses on Vietnamese manufacturing
firms and GSO IIP Section C as the primary macro target.

## Decision

1. **GSO-first for Vietnam macro.** IIP (and later shipment/inventory when PX-Web
   tables are wired) come from NSO/GSO NSDP. Never invent Vietnam OECD MEI/BCI/ICT.
2. **Keep real VNM INDIGO.** Persist under `country=VNM`, `source=OECD` (or
   `OECD_FALLBACK` from the sourced fixture).
3. **Peer leading indicator for forecasting only.** Fetch MEI_IP for **EA20**
   (Euro area), stored as `country=EA20`, `source=OECD_PEER`. Use it as an
   exogenous lag feature for IIP forecasting (export-demand channel). Do **not**
   use peer series for firm-to-firm VN comparison or as a stand-in for Vietnam.
4. **Frequency harmonization**
   - Quarterly → monthly: linear between quarter starts.
   - Annual → monthly (**INDIGO**): **step-hold** (same value for Jan–Dec).
     Linear annual interpolation is rejected because it invents false intra-year
     dynamics for a structural annual index.
5. **Provenance column.** `oecd_indicators.source` ∈
   `{OECD, OECD_FALLBACK, OECD_PEER}`.

## Consequences

- Feature engineering joins GSO `IIP_C` + VNM `INDIGO` + EA20 `MEI_IP` (as `mei_ip`).
- MEI_BCI / ICT_INVEST remain unavailable for VNM until OECD publishes them.
- GSO shipment (`E07.03`) and inventory (`E07.04`) come from PX-Web as **annual**
  series and are step-held to monthly at ingest (same policy as INDIGO).
