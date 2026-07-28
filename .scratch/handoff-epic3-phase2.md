# Handoff — Epic 3 Phase 2 close audit + tour Task #40–#50

**Status:** Phase 2 **runnable scope CLOSED** (2026-07-28)  
**Branch (docs):** `cursor/epic3-phase2-close-audit`  
**Base:** `origin/main` @ `6063a36` (PR #35 Task #50 merged)  
**Scope chat:** phase-close audit + catch-up tour #40–#50 only — **không** reopen #41/#48/#49/#19b  
**Không invent:** Epic 3 Phase 3 (plan hiện không có phase đó)

---

## Bản đồ 30 giây

Epic 3 Phase 2 = **số thật nơi lấy được** trên mẫu ~28 DN niêm yết, cộng **honesty** (không nói quá), cộng **thiết kế scale** Section C (chưa đổ DN cả nước).

- **Đã chạy xong (open runnable):** #40, #42, #43, #45, #46, #47 (biên bản NO-GO), #50 — cộng #32–#39 + #51 từ trước.
- **Tạm dừng có chủ đích:** #41, #48, #49, #19b (chỉ reopen khi user Explicit).
- **Không còn là task / parked vô thời hạn:** ex-#44 (industry-ratio wire); phần **crawl** GRDP tỉnh×ngành (sau #47).
- **Demo honesty:** UI nói rõ Digital VA / số hóa = mẫu ~28; marketplace `live` có thể = cache; VA quốc gia ≠ Digital VA DN; vũ trụ DN stub vẫn `[]`.

Chi tiết từng task: **§ Tour Task #40–#50** dưới đây.

---

## Phase-close audit — Definition of Done

Nguồn DoD: `.scratch/epic3-phase2-plan.md` § Definition of Done Phase 2.

| DoD item | Kết luận | Evidence |
|----------|----------|----------|
| BCTC mẫu 28 ưu tiên CafeF/live; seed = fallback có nhãn | **DONE** | #32; FE #51 prefer CafeF + clickable `source_url` |
| Artifact audit URL/checkout cả mẫu | **DONE** | #33 + refresh #40 (`website_ok` 19→**27/28**) |
| Marketplace live strategy + listing chỉ tăng khi có nguồn | **DONE** (honest: live HTTP vẫn block) | ADR-0002; #34/#35; #42 cookie ≠ unlock |
| Ratio/GRDP: wire có nguồn **hoặc** deferred biên bản | **DONE (deferred path)** | Ratio `None` (ex-#44); #47 biên bản; national `VA_C` GO (#38/#45/#46) |
| Blueprint scale Section C (không copy seed) | **DONE** | ADR-0003; `data/raw/company_universe/rows.json` = `[]`; #50 coverage note |
| `docs/plan.md` checklist + handoff phase | **DONE (audit này)** | Checklist runnable `[x]`; file này = `handoff-epic3-phase2.md` |

### Phân loại đóng phase

| Loại | Tasks / mục |
|------|-------------|
| **DONE (runnable)** | #32–#40, #42, #43, #45, #46, #47 (NO-GO biên bản), #50, #51 |
| **Tạm dừng (có thể reopen)** | #41, #48, #49, #19b |
| **«Chưa làm được» vô thời hạn** | Industry-ratio wire (ex-#44); crawl GRDP tỉnh×ngành; IIP theo VSIC 2+; Benchmark xu hướng năm |
| **Không còn là task** | #44 (quyết định 2026-07-27) |

**Verdict:** Phase 2 **đủ DoD** theo đường “wired hoặc deferred có biên bản”. Không còn open runnable trong bảng «Phase 2 — còn mở». Không giả định Epic 3 Phase 3.

### Plan sync gaps đã xử lý / còn lưu ý

- Handoff phase trước đây **thiếu** → tạo file này.
- Local `main` đã ff tới `6063a36` trên branch audit.
- `handoff-task50.md` trên main vẫn ghi “PR open” trong khi PR #35 **đã merge** — nên sửa khi commit audit (hoặc lần ship sau).
- §6 «Tiến độ thực tế» (2026-07-20) vẫn cũ so với nhiều PR Epic 3 — **không** rewrite toàn bộ trong audit này; chỉ neo Phase 2 closed + link handoff.
- FE backlog P1 (chip URL fail / empty discovery) **không** chặn đóng Phase 2.

### Artifact missing (honest)

| File | Ghi chú |
|------|---------|
| `handoff-task41.md` | Không có — status từ `docs/plan.md` |
| `handoff-task44.md` | Không có — ex-task; research #30/#37 |
| `handoff-task48.md` / `49` | Không có — tạm dừng, chưa chạy |
| `handoff-task19b.md` | Không có trong audit set |

---

## Tour Task #40–#50

Giọng: giải thích cho người bỏ qua kiểm duyệt. Số liệu chỉ lấy từ handoff/biên bản — **không bịa**.

### Task #40 — Sửa domain website seed

1. **Mục đích một câu** — Audit #33 thấy nhiều URL website sai/hỏng; sửa domain thật để detector chạy được.
2. **Status** — **DONE** (PR #29).
3. **Đã làm được**
   - Đổi **8/9** URL trong `data/seeds/companies.json` (IDI, SBT, NKG, POM, TLH, DPR, CSV, DCM) sau khi probe HTTP 200 + SSL verify ON.
   - Re-audit: `website_ok` **19 → 27/28**.
   - GEE giữ `https://gelex-electric.com`, SSL fail hợp lệ, checkout `unknown`.
   - Biên bản: `.scratch/epic3-task40-website-domain-fix.md`.
4. **Chưa làm được / cố ý bỏ** — Tắt SSL verify; bịa checkout/GMV; FE chip “URL chưa verify” (P1 backlog, gần như chỉ còn GEE).
5. **Cách làm** — (1) Đọc audit #33 → (2) Tra domain công khai → (3) Probe httpx verify ON → (4) Chỉ ghi seed khi OK → (5) Re-audit + biên bản GEE.
6. **Ảnh hưởng demo / honesty** — Hầu hết DN mẫu mở được website; GEE vẫn fail rõ ràng, không giả “không có ecommerce”.
7. **Nợ sang task sau?** — GEE SSL + chip FE (backlog); không chặn wave sau.

### Task #41 — GMV backfill + refresh live-cache

1. **Mục đích một câu** — Điền `units_sold_est` / GMV chỉ từ live/cache/curation có PROVENANCE; làm mới snapshot cache.
2. **Status** — **Tạm dừng có chủ đích** (2026-07-27). `handoff-task41.md`: **chưa rõ từ artifact** (không có file).
3. **Đã làm được** — Không chạy trong wave Phase 2 sau quyết định tạm dừng. Kế hoạch còn trong `.scratch/epic3-phase2-plan.md` §41.
4. **Chưa làm được / cố ý bỏ** — Backfill units + overwrite cache JSON; vì #42 chứng minh cookie **không** mở được HTML live → không có capture thật để refresh trung thực.
5. **Cách làm** — «chưa rõ từ artifact» (chưa có handoff chạy).
6. **Ảnh hưởng demo / honesty** — Cache vẫn dạng demo-shaped (#35); badge `live` ≠ “fetch mạng lần này”.
7. **Nợ sang task sau?** — Giữ nguyên trên #41 khi user reopen; #42 khẳng định blocker live.

### Task #42 — Cookie ops smoke + partner API spike

1. **Mục đích một câu** — Kiểm chứng cookie session trong env có mở được scrape live không; ghi note đối tác API (không implement).
2. **Status** — **DONE** (PR #30).
3. **Đã làm được**
   - Cookie `SHOPEE_SESSION_COOKIE` / `TIKTOK_SESSION_COOKIE` `present=yes`.
   - `--no-cache` → **`live_ok=0`** (anti-bot/403); cache-on-fail → **`live_ok=2`**.
   - Artifacts: `.scratch/epic3-task42-cookie-ops-smoke.md` (+ nocache), `epic3-task42-partner-api-spike.md`.
   - Khẳng định ADR-0002: không anti-bot SaaS; partner cần hợp đồng.
4. **Chưa làm được / cố ý bỏ** — #41 refresh; ingest partner; commit secret.
5. **Cách làm** — (1) Kiểm env cookie → (2) Smoke cookie / no-cache / control → (3) Research partner → (4) Biên bản + docs/tests.
6. **Ảnh hưởng demo / honesty** — Demo phụ thuộc allowlist cache; UI không được nói “live scrape vừa thành công”.
7. **Nợ sang task sau?** — Live block → #41 vẫn tạm dừng cho đến khi có parse thật.

### Task #43 — Discovery crawl + fuzzy hygiene

1. **Mục đích một câu** — Có đường tìm shop trên sàn đưa vào cổng QA (#36); siết khớp tên sai (token ngắn).
2. **Status** — **DONE** (PR #33).
3. **Đã làm được**
   - `search_marketplace_shop_candidates` + feed QA gate trong `shop_finder.py`.
   - Live search **bị chặn** (anti-bot) → biên bản `.scratch/epic3-task43-discovery-crawl.md`.
   - Ops smoke: inject RAL → `qa_discovery`; git `discovery_allowlist.json` vẫn `entries: []`; discovery **OFF mặc định**.
   - Fuzzy: `MIN_TOKEN_CONTAINMENT_LEN=5`, noise `dong` (DPR ↛ rangdong).
4. **Chưa làm được / cố ý bỏ** — Unlock live search; bật discovery mặc định; invent shop.
5. **Cách làm** — (1) Explore gate/matcher → (2) Viết search path + hygiene → (3) Gate pipeline → (4) Pytest + spike live → (5) Biên bản.
6. **Ảnh hưởng demo / honesty** — Không tự thêm shop mới từ search; matcher ít false-positive hơn.
7. **Nợ sang task sau?** — Live search khi ToS/ops cho phép (không bắt buộc Phase 2).

### Task #44 (ex) — Industry-ratio wire

1. **Mục đích một câu** — Khi DN không có listing, ước online revenue = tỷ trọng ngành × doanh thu BCTC — **chỉ nếu** có citation CBCT đúng khái niệm.
2. **Status** — **Không còn là task** → mục «Chưa làm được…» (2026-07-27). `handoff-task44.md`: không có.
3. **Đã làm được** — Trước đó #30/#37 research: giữ `SOURCED_INDUSTRY_ECOMMERCE_RATIO=None` (code xác nhận). Biên bản: `.scratch/epic3-task30-industry-ratio-research.md`.
4. **Chưa làm được / cố ý bỏ** — Wire constant; cấm % KT số/GDP, VECOM all-sector, invent 0.15.
5. **Cách làm** — Research ở #30/#37; #44 bị hủy làm task roadmap vì thiếu citation.
6. **Ảnh hưởng demo / honesty** — Thiếu listing → `online_revenue=0` + log (không ước ngành).
7. **Nợ sang task sau?** — Parked vô thời hạn đến khi có bảng/figure + user Explicit reopen.

### Task #45 — Dashboard/API hiện VA quốc gia

1. **Mục đích một câu** — Đưa `VA_C` (giá trị gia tăng chế biến chế tạo quốc gia từ #38) lên Module 1, tách Digital VA mẫu DN.
2. **Status** — **DONE** (PR #31).
3. **Đã làm được**
   - `GET /api/dashboard/va`; summary `va_c_*` / nominal.
   - FE strip + chart; copy ≠ Digital VA; empty honest.
   - Tests + `npm run build` PASS (theo handoff).
4. **Chưa làm được / cố ý bỏ** — Redesign KPI grid; crawl mới (dùng data #38).
5. **Cách làm** — (1) Explore BE/FE → (2) Wire API/schema/FE → (3) Pytest + build → (4) Handoff.
6. **Ảnh hưởng demo / honesty** — User thấy VA macro riêng; MoM step-hold trong quý thường ~0 (trung thực).
7. **Nợ sang task sau?** — Pipeline wire → **#46** (đã nhận và DONE).

### Task #46 — Pipeline cleaning/features VA

1. **Mục đích một câu** — Đưa `VA_C` vào cleaned/features làm chuỗi phụ trợ; **không** đổi target dự báo IIP im lặng.
2. **Status** — **DONE** (PR #32).
3. **Đã làm được**
   - `va_c` / `va_c_nominal` + provenance trong cleaned parquet & features.
   - Clean honest: `max_gap=0`, không nội suy linear trên VA.
   - Manifest `forecast_target: "iip"`; VA = `va_auxiliary`.
4. **Chưa làm được / cố ý bỏ** — VA lags; ARIMA/LSTM exog đầy đủ; đổi target.
5. **Cách làm** — (1) Explore cleaning/features → (2) Wire + loại cột provenance khỏi XGB string → (3) Pytest → (4) Handoff.
6. **Ảnh hưởng demo / honesty** — ML vẫn dự báo IIP; VA có trong feature store khi DB có #38.
7. **Nợ sang task sau?** — Optional VA lags sau này (không silent target change).

### Task #47 — GRDP tỉnh×ngành re-gate

1. **Mục đích một câu** — Chốt lại: có crawl GRDP tỉnh×ngành được không, hay chỉ biên bản NO-GO.
2. **Status** — **DONE** dưới dạng **biên bản NO-GO/deferred**; phần **crawl = parked**.
3. **Đã làm được**
   - `.scratch/epic3-task47-grdp-deferred.md` (+ CSV): chưa table ID NSO tỉnh×ngành CBCT.
   - Cấm copy `VA_C` quốc gia → tỉnh; national VA #38/#45/#46 giữ.
   - Không thêm crawler.
4. **Chưa làm được / cố ý bỏ** — Crawl/wire tỉnh (cố ý).
5. **Cách làm** — (1) Rà spike #31/#38 → (2) Biên bản + sync docs → (3) Verify không regress VA → (4) Handoff.
6. **Ảnh hưởng demo / honesty** — Không có bản đồ GRDP tỉnh; chỉ VA quốc gia.
7. **Nợ sang task sau?** — Crawl nằm «Chưa làm được…»; task crawl **mới** chỉ khi có table ID (không reopen #47 để implement crawl).

### Task #48 — Universe nông ingest stub→thật

1. **Mục đích một câu** — Đổ vũ trụ DN Section C nông (shallow) vào stub #39 khi có nguồn thật.
2. **Status** — **Tạm hoãn (A)** — chưa nguồn. `handoff-task48.md`: không có.
3. **Đã làm được** — Không chạy; stub `rows.json` vẫn `[]` (#39/#50).
4. **Chưa làm được / cố ý bỏ** — Ingest; cấm invent/copy seed ~28 thành “cả nước”.
5. **Cách làm** — «chưa rõ từ artifact».
6. **Ảnh hưởng demo / honesty** — Coverage claim giữ `prototype_listed_sample` (#50).
7. **Nợ sang task sau?** — **Chặn #49**.

### Task #49 — Deep-sample expand có kiểm soát

1. **Mục đích một câu** — Mở rộng mẫu sâu (BCTC/digital) có kiểm soát **sau** khi #48 có nguồn.
2. **Status** — **Hoãn theo #48**. `handoff-task49.md`: không có.
3. **Đã làm được** — Không chạy.
4. **Chưa làm được / cố ý bỏ** — Expand trăm BCTC; invent.
5. **Cách làm** — «chưa rõ từ artifact».
6. **Ảnh hưởng demo / honesty** — Mẫu sâu vẫn ~28.
7. **Nợ sang task sau?** — Sau #48 + user reopen.

### Task #50 — UniverseCoverageNote API + FE

1. **Mục đích một câu** — API + banner nói rõ mức coverage (mẫu sâu vs vũ trụ) theo contract #39 / ADR-0003 — kể cả khi stub rỗng.
2. **Status** — **DONE** (PR #35 **merged** `main` @ `6063a36`).
3. **Đã làm được**
   - `GET /api/universe/coverage`; stub rỗng → `claim=prototype_listed_sample`, `universe_row_count=0`.
   - FE: `SampleHonestyBanner` nhận `coverageNote` trên Dashboard + Company detail.
   - Tests universe + FE contract; `rows.json` = `[]`.
4. **Chưa làm được / cố ý bỏ** — Invent universe; Alembic table; reopen paused tasks.
5. **Cách làm** — (1) Explore contract/FE → (2) API + FE → (3) Pytest + build → (4) Handoff.
6. **Ảnh hưởng demo / honesty** — User thấy ~28 **không** phải toàn Section C.
7. **Nợ sang task sau?** — Phase 2 open runnable hết → **phase-close** (chat này). #48 sau có thể đổi claim khi có rows.

### Neo liên quan ngoài dải #40–#50

#### Task #51 — FE honesty surface *(DONE, PR #28)*

Banner/badge mẫu ~28; Benchmark mọi warnings tiếng Việt; listing `null`≠0; note marketplace cache (ADR-0002); CafeF ưu tiên + link. Là mặt FE honesty mà #40/#42/#45/#50 “cắm” vào.

#### #19b — Proposal Mục 4

**Tạm dừng có chủ đích** (2026-07-27). Không handoff trong audit set. Cập nhật kết quả thật khi reopen — không invent số.

---

## Bảng tổng hợp một trang (#40–#50)

| # | Status | Làm được (1 dòng) | Chưa làm (1 dòng) | Ghi chú |
|---|--------|-------------------|-------------------|---------|
| 40 | DONE | website_ok **19→27/28**; 8 URL seed | GEE SSL; chip FE | PR #29 |
| 41 | Tạm dừng | — | GMV/cache refresh | Không handoff |
| 42 | DONE | cookie yes; live_ok **0** / cache **2** | partner impl; #41 | ADR-0002 |
| 43 | DONE | search path + fuzzy; live search block | discovery ON mặc định | PR #33 |
| 44 | Không còn task | ratio giữ `None` (#30/#37) | wire không citation | «Chưa làm được…» |
| 45 | DONE | `/dashboard/va` + FE strip/chart | redesign KPI | PR #31 |
| 46 | DONE | VA auxiliary; target vẫn `iip` | VA lags | PR #32 |
| 47 | DONE (NO-GO biên bản) | deferred + cấm copy VA→tỉnh | crawl tỉnh | crawl parked |
| 48 | Tạm dừng | — | universe ingest | chặn #49 |
| 49 | Hoãn theo #48 | — | deep expand | Không handoff |
| 50 | DONE | `/universe/coverage` stub=0 | invent universe | PR #35 merged |
| 51* | DONE | FE honesty P0 | — | *ngoài dải, liên quan* |
| 19b* | Tạm dừng | — | Proposal Mục 4 | *Phase 5* |

\* Ghi rõ ngoài dải số #40–#50 nhưng neo honesty / demo.

---

## Luồng end-to-end (sau Phase 2)

1. Seed ~28 + CafeF BCTC (#32) + website audit/fix (#33/#40).
2. Marketplace: listing có nguồn (#34) + chiến lược cache (#35/ADR-0002); cookie không mở live (#42).
3. Matcher/discovery có cổng; search path sẵn nhưng OFF + live search block (#36/#43).
4. Macro: `VA_C` quốc gia (#38) → Dashboard (#45) → cleaning/features phụ trợ (#46); GRDP tỉnh NO-GO (#47).
5. Scale: ADR-0003 stub rỗng (#39) + coverage note UI (#50); FE honesty (#51).
6. **Không** wire industry-ratio (ex-#44); **không** ingest vũ trụ (#48); **không** GMV backfill (#41) cho đến reopen.

---

## Testing / verify notes (audit)

| Check | Result |
|-------|--------|
| `origin/main` chứa #50 | **PASS** — tip `6063a36` Merge PR #35 |
| Plan checklist runnable #42/#43/#45/#46/#47/#50 | **PASS** — `[x]` |
| `SOURCED_INDUSTRY_ECOMMERCE_RATIO` | **PASS** — vẫn `None` |
| `#47` biên bản tồn tại; không crawler tỉnh | **PASS** (spot-check explore) |
| Handoffs #41/#44/#48/#49 | **Missing** — ghi «chưa rõ từ artifact» |
| Paused #41/#48/#49/#19b không implement trong chat | **PASS** |
| Epic 3 Phase 3 trong plan | **Không có** — không invent |

*(Audit docs-only — không chạy full pytest trong wave này; regression đã ghi trong từng handoff task.)*

---

## Task review — Epic 3 Phase 2 close

### Tiến độ
- Phase 2 runnable: **100% closed**
- Status: **CLOSED** (với paused + «chưa làm được» trung thực)
- Branch docs: `cursor/epic3-phase2-close-audit` · base `6063a36`

### Đã làm trong chat audit
- Tour #40–#50 (7 mục/task) + bảng tổng hợp
- Đối chiếu DoD Phase 2
- Handoff phase này; plan sync nhẹ (link + closed)

### Không làm
- Reopen #41/#48/#49/#19b
- Invent Epic 3 Phase 3 / universe / GRDP / GMV
- Commit/PR/milestone trừ khi user Explicit

---

## Next — options (không giả định Phase 3)

User chọn **một** hướng cho chat sau:

| Option | Nội dung |
|--------|----------|
| **A** | Reopen **một** paused task (#41 / #48 / #49 / #19b) — Explicit tên số |
| **B** | Viết **epic/phase mới** vào `docs/plan.md` khi user chọn chủ đề (vd. demo/slides, scale ingest…) — **không** tự đặt tên “Epic 3 Phase 3” |
| **C** | Đóng học kỳ / slides / báo cáo demo (ops + narrative, không invent số) |
| **D** | Dừng roadmap — chỉ maintain / merge audit docs |

Paste prompt sẵn: xem response cuối chat audit (có Waves).

---

## Do not

- Mở #41/#48/#49/#19b / invent Phase 3 trừ Explicit
- Copy `VA_C` → tỉnh; invent industry-ratio; treat ~28 = Section C
- Commit/push/PR/milestone trừ Explicit
