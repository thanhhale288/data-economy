# Epic 3 Task #40 — Website domain fix + honesty guard

**Date (UTC probe):** 2026-07-27  
**Branch:** `cursor/epic3-phase2-task40-website-domain-fix`  
**Prior evidence:** `.scratch/epic3-task33-website-url-audit.md` (`website_ok=19/28`)  
**SSL policy:** verify ON (httpx default). **No** global `verify=False`.

## Method

1. Look up public HOSE / Vietstock / company profile websites for each failing ticker.
2. Probe candidates with DNS + HTTPS (or HTTP when HTTPS cert is broken) via httpx `verify=True`.
3. On HTTP 200: run `website_detector.analyze_html` → set seed `has_checkout` from detector only.
4. On continued fail: keep best-known official URL + record reason; audit `has_checkout=unknown` (never invent checkout).

## Per-ticker conclusions

| Ticker | Seed before | Seed after | Probe | Evidence | `has_checkout` |
|--------|-------------|------------|-------|----------|----------------|
| IDI | `https://idi.com.vn` (DNS fail) | `https://idiseafood.com` | **OK 200** | Vietstock + BSC list idiseafood.com; live fetch OK | `false` (measured) |
| SBT | `https://ttcsugar.com.vn` (DNS fail) | `https://ttcagris.com.vn` | **OK 200** | TTC AgriS corporate site (SBT); old sugar domain NXDOMAIN | `false` (measured) |
| NKG | `https://namkimgroup.vn` (timeout) | `https://tonnamkim.com` | **OK 200** | Brand site “Tôn Nam Kim”; email still `@namkimgroup.vn` | `false` (measured) |
| POM | `https://pomina-steel.com` (SSL weak key) | `http://www.pomina-steel.com` | **OK 200** | Same host; HTTPS EE key too weak; Vietstock lists `http://` | `false` (measured) |
| TLH | `https://tienlensteel.com.vn` (SSL issuer) | `https://www.tienlengroup.vn` | **OK 200** | Title “Tập đoàn Thép Tiến Lên”; steel.com.vn still SSL-broken | `true` (measured) |
| GEE | `https://gelexelectric.com.vn` (self-signed) | `https://gelex-electric.com` | **FAIL SSL** | Annual report lists gelex-electric.com; both `.vn` and `.com` fail issuer/self-signed | **unknown** (not measured) |
| DPR | `https://dpr.com.vn` (self-signed) | `https://doruco.com.vn` | **OK 200** | Vietstock / Cophieu68 website = doruco.com.vn | `false` (measured) |
| CSV | `https://hcb.com.vn` (hostname mismatch) | `https://sochemvn.com` | **OK 200** | Vietstock website = sochemvn.com | `true` (measured) |
| DCM | `https://damcamau.vn` (conn reset) | `https://www.pvcfc.com.vn` | **OK 200** | Vietstock = pvcfc.com.vn; bare host redirects to OWA — use `www` | `false` (measured) |

### GEE biên bản (still fail)

| URL tried | Result |
|-----------|--------|
| `https://gelexelectric.com.vn` | SSL: self-signed certificate |
| `https://gelex-electric.com` | SSL: unable to get local issuer certificate |
| `https://www.gelex-electric.com` | DNS NXDOMAIN |
| `https://gelex.vn` (group) | SSL: unable to get local issuer certificate |

**Decision:** keep best-known official URL `https://gelex-electric.com` (GEE annual report). Do **not** disable SSL verify. Seed `has_checkout=false` is a storage default only — live audit must report `unknown` until a verified fetch succeeds. Not a conclusion of “no ecommerce”.

### Rejected alternatives

| Ticker | Candidate | Why not |
|--------|-----------|---------|
| POM | `https://pomina-flat-steel.com` | Subsidiary (flat steel), not listed POM corp site |
| DCM | `https://pvcfc.com.vn` (no www) | Redirects to Exchange OWA login page |

## Seed fields touched

For each ticker: `website_url` **and** `digital_presence[channel_type=website].url` kept in sync; `digital_channels.website=true`. Checkout updated only when probe returned HTTP 200 + detector ran.

## Expected audit delta

| Metric | Task #33 | After #40 (target) |
|--------|----------|---------------------|
| `website_ok` | 19/28 | **27/28** (GEE remains fail) |
| `website_fail` | 9 | **1** (GEE) |
| Checkout on fails | unknown | GEE still `unknown` |

Re-audit command:

```bash
PYTHONPATH=. python scripts/audit_website_marketplace.py --no-db
```

Report artifacts refreshed under `.scratch/epic3-task33-website-url-audit.{md,csv}` (script default stem) plus this note.
