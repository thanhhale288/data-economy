# Epic 3 Task #42 — Partner / official marketplace API spike

**Date:** 2026-07-27  
**ADR:** `docs/adr/0002-marketplace-live-strategy.md` Decision §3 (spike only) + §4 (reject anti-bot SaaS default)  
**Scope:** Research note only — **no** partner ingest implementation, no paid connector, no contract signed.

## Question

Is there an official / partner API path for Vietnam Shopee / TikTok Shop data that could replace fragile HTML scrape + session cookies for this đồ án?

## Findings (high-trust primary docs)

### Shopee Open Platform

- Portal: [https://open.shopee.com/documents](https://open.shopee.com/documents) (Developer Guide, last reviewed content ~2026-07-19).
- Account types: Individual Seller, Registered Business Seller, **Third-party Partner Platform (ISV)**.
- **VN seller eligibility** (own shop APIs): Preferred Sellers **or** Mall Sellers — not every listed manufacturer shop.
- **ISV / third-party:** requires registered business docs, **live** product with existing e-commerce integrations + trial account for Shopee QA, HTTPS/TLS ≥1.2, no “extract listings to enable off-platform transactions” (Platform Partner Rules). Approval ~**10 working days**.
- Sensitive data needs IP whitelist (+ pen-test for some markets). Chat API new third-party apps closed since 2024-11-18 — irrelevant for listing GMV but shows API surface is gated.
- **Fit for đồ án:** Poor without (a) owning/authorized seller shops for RAL/VNM peers, or (b) ISV app + business registration + live SaaS product under review. Public crawl of competitor shops is **out of** Open Platform intent.

### TikTok Shop Partner Center

- Partner center / Open API for authorized shops (orders, products, finance, affiliate scopes) after developer registration + shop OAuth; region (e.g. Vietnam) chosen at app create time.
- Typical flow: App Key/Secret → seller authorize → access/refresh tokens; production often needs **IP allowlist**.
- Public affiliate / partner APIs target **authorized** sellers/creators — not anonymous scrape of `@vinamilk` storefront HTML.
- **Fit for đồ án:** Same gate — need seller consent / self-developed app on shops we control or partner with. Not a drop-in for allowlist HTTP smoke.

### Data vendors / anti-bot SaaS

- Scraping proxies, captcha farms, “marketplace intelligence” SaaS: **rejected as default** (ADR-0002 §4) for ToS/cost/honesty of đồ án.
- Commercial GMV panels without seller auth: treat as out-of-scope unless a future task has citation + license + PROVENANCE (not this spike).

## Recommendation

| Option | For this project now | Reopen when |
|--------|----------------------|-------------|
| Allowlist + versioned cache (ADR default) | **Keep** | Always for demo stability |
| Session cookie ops | Documented in #42; **does not unlock** live HTML today | Cookie + browser automation revisit only if ops proves differently; still no SaaS |
| Shopee Open Platform / TikTok Partner API | **No implement** without contract + authorized shops | University/partner has seller auth or ISV approval + legal OK |
| Anti-bot SaaS | **Do not** | Never as default |

**Bottom line:** Official APIs exist but are **seller-/partner-gated**. They do not solve anonymous allowlist scrape for RAL×shopee / VNM×tiktok. Cookie ops smoke (#42) confirms scrape path remains blocked → cache path remains correct. Full partner ingest waits on a real contract and authorized shops — out of Phase 2 agent scope.

## Explicitly not done

- No new crawler module calling Open Platform / Partner Center.
- No credentials, app keys, or shop OAuth stored in repo.
- No Digital VA / GMV formula changes.
- No Task #41 cache refresh (no live parse to write).
