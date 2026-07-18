# needGit — Git / libs dùng cho project

Manufacturing Data Economy Platform (VSIC Section C).  
Tài liệu tổng hợp: agent chống quên / hallucination / tiết kiệm token + crawl + train ML.

---

## A. Làm ngay (agent + foundation)

### 1. mattpocock/skills — chống quên domain, giảm hallucinate, ít token

**Repo:** https://github.com/mattpocock/skills  
**Vì sao:** Tạo `CONTEXT.md` + glossary (VSIC, IIP, Digital VA…) để agent không bịa và không dài dòng.  
**Trạng thái:** Đã cài (`.agents/skills/`).

**Cài:**

```bash
npx skills add mattpocock/skills
```

**Dùng:**

1. Trong Cursor/Claude Code: chạy `/setup-mattpocock-skills`
2. Chọn issue tracker (local files là ổn — `.scratch/`)
3. Feature lớn: `/grill-with-docs`
4. Hết session: `/handoff`
5. Bảo agent tạo `CONTEXT.md` với: VSIC↔ISIC, 10 DN, Digital VA, schema tables, lệnh chạy (`uvicorn`, seed, train)

---

### 2. colbymchenry/codegraph — code knowledge graph MCP (thay codebase-memory-mcp)

**Repo:** https://github.com/colbymchenry/codegraph  
**Docs:** https://colbymchenry.github.io/codegraph/  
**Vì sao:** Index cấu trúc code thành graph local; agent query call chain / impact thay vì đọc cả tree (ít token hơn).  
**Trạng thái:** Chưa cài. `codebase-memory-mcp` cũng **chưa** cài — bỏ hẳn, dùng CodeGraph thay.

**Cài:**

```bash
# 1) CLI (macOS / Linux)
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh

# hoặc nếu đã có Node:
# npm i -g @colbymchenry/codegraph

# 2) Wire MCP vào Cursor (mở terminal mới sau bước 1)
codegraph install --target=cursor --yes

# 3) Index project này
cd "/Users/hale/Code/AI in Data Economy"
codegraph init
```

**Dùng:**

1. Restart Cursor (MCP `codegraph` xuất hiện)
2. Hỏi kiểu: *"Trace call chain từ GSO crawl tới ML prediction"*, *"Impact nếu đổi schema companies"*
3. Upgrade sau: `codegraph upgrade`

---

### 3. AGENTS.md + CONTEXT.md (không clone — tự tạo trong repo)

**Vì sao:** Luôn load, ngắn, chống cold-start / quên kiến trúc.  
**Trạng thái:** Đã có ở root.

| File | Nội dung |
|------|----------|
| `AGENTS.md` | Stack, quick start, map thư mục, “đọc docs trước khi đoán công thức” |
| `CONTEXT.md` | Glossary domain + quyết định kiến trúc |

---

## B. Làm ngay (product: crawl + ML)

Đây là **library `pip install`**, không cần `git clone` cả repo.

### 4. SDMX / OECD (crawl OECD thật)

**Package đã chọn:** [`sdmx1`](https://github.com/sdmx-twg/sdmx1) (`import sdmx`) — đã có trong `requirements.txt`.  
**Không dùng** `pandasdmx`: bản hiện tại kéo `pydantic<1.8`, xung đột FastAPI (`pydantic` 2.x).

**Vì sao:** `crawlers/oecd/sdmx_client.py` cần SDMX thật cho MEI / BCI / INDIGO (không invent số).

**Cài:**

```bash
source .venv/bin/activate
pip install -r requirements.txt   # gồm sdmx1==2.26.0
```

**Dùng:** Refactor / giữ `crawlers/oecd/sdmx_client.py` với `import sdmx` — bỏ fallback random, lấy MEI / BCI / INDIGO qua SDMX.

---

### 5. ARIMA thật (statsmodels — đã trong requirements)

**Repo:** https://github.com/statsmodels/statsmodels  
**Vì sao:** `train_arima` trong `ml/models/trainer.py` hiện là EMA giả — proposal cần ARIMA(1,1,1) / SARIMAX thật.

**Cài:**

```bash
# đã trong requirements.txt
pip install statsmodels
```

**Dùng:** Sửa `ml/models/trainer.py` → `statsmodels.tsa.arima.model.ARIMA` / `SARIMAX`.

---

### 6. Playwright (đã trong requirements) — marketplace / website DN

**Repo:** https://github.com/microsoft/playwright-python  
**Vì sao:** Shopee/TikTok/Lazada / website DN nặng JS; httpx alone dễ block.

**Cài:**

```bash
pip install playwright
playwright install chromium
```

**Dùng:** Bổ sung cho `crawlers/marketplace/` và crawl website DN khi cần render JS.

---

## C. Để sau (khi MVP ổn / đúng phase)

| # | Repo / lib | Khi nào | Cài |
|---|------------|---------|-----|
| 7 | [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | Khi bắt đầu FE / BE / AI — **không cài full**, chỉ 1–3 agent đúng phase | `./scripts/install.sh --tool cursor --agent frontend-developer` (ví dụ) |
| 8 | [unit8co/darts](https://github.com/unit8co/darts) | ML Lab so sánh nhiều model 1 API | `pip install darts` |
| 9 | [scrapy](https://github.com/scrapy/scrapy) + [scrapy-playwright](https://github.com/scrapy-plugins/scrapy-playwright) | Scale crawl nhiều shop | `pip install scrapy scrapy-playwright` |
| 10 | [sentence-transformers](https://github.com/UKPLab/sentence-transformers) | Shop matcher tốt hơn RapidFuzz | `pip install sentence-transformers` |
| 11 | [camelot](https://github.com/camelot-dev/camelot) / [tabula-py](https://github.com/chezou/tabula-py) | Extract bảng BCTC PDF | `pip install camelot-py[cv]` |
| 12 | [PrefectHQ/prefect](https://github.com/PrefectHQ/prefect) | Thay `schedule` khi job phức tạp | `pip install prefect` |
| 13 | [great-expectations](https://github.com/great_expectations/great_expectations) | Validate IIP/schema trước train | `pip install great_expectations` |
| 14 | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | Graph docs+code nếu vẫn thiếu sau CodeGraph | `pip install graphifyy && graphify install` |
| 15 | [wbgapi](https://github.com/tgherzog/wbgapi) | World Bank bổ sung macro | `pip install wbgapi` |
| 16 | [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | BCTC scan tiếng Việt | khi cần OCR |

### Agency Agents — ghi chú quyết định

- **Ý tưởng phân role** (FE / BE / AI engineer) ổn; hữu ích khi chuyển phase.
- **Hiện tại (data):** không cài — dùng Matt Pocock skills + `CONTEXT.md` / `AGENTS.md`.
- **Khi làm FE:** cài chọn lọc `frontend-developer` (và tester nếu cần), `alwaysApply: false`, gọi `@...`.
- **Khi làm BE / AI:** thêm backend / ML-related agent tương ứng — vẫn không install toàn roster.
- Persona generic **không thay** domain rules (VSIC, Digital VA, không invent GSO/OECD).

---

## D. Không dùng (bỏ)

| Repo | Lý do |
|------|--------|
| [github/spec-kit](https://github.com/github/spec-kit) | Overlap mạnh với `to-spec` / `to-tickets` / `.scratch/` — thêm harness trùng, dễ lẫn nguồn sự thật |
| [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | Chưa cài; thay bằng [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) |
| [Nutlope/hallmark](https://github.com/Nutlope/hallmark) | Chỉ UI aesthetic |
| [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) | Catalog học, không gắn stack |
| [asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks) | Đọc prompt, không deploy |
| [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | Social scrape, lệch scope |
| [diegosouzapw/OmniRoute](https://github.com/diegosouzapw/OmniRoute) | Gateway API free — không cần nếu Cursor Pro đủ |
| [kunchenguid/no-mistakes](https://github.com/kunchenguid/no-mistakes) | Git gate PR — nặng lúc này |

---

## Checklist cài nhanh (~15 phút)

```bash
cd "/Users/hale/Code/AI in Data Economy"

# 1) Agent skills (đã xong nếu đã có .agents/skills/)
npx skills add mattpocock/skills

# 2) CodeGraph MCP (thay codebase-memory-mcp)
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
# mở terminal mới rồi:
codegraph install --target=cursor --yes
codegraph init

# 3) Product libs (đã gồm sdmx1 + statsmodels + playwright)
source .venv/bin/activate
pip install -r requirements.txt
```

Sau đó trong Cursor:

1. Restart Cursor
2. `/setup-mattpocock-skills` (nếu chưa)
3. Xác nhận MCP `codegraph` sẵn sàng
4. Giữ `AGENTS.md` + `CONTEXT.md` làm nguồn domain

---

## Cheat sheet — muốn gì thì dùng gì

| Muốn… | Dùng |
|-------|------|
| Agent đừng quên / đừng bịa domain | `CONTEXT.md` + `/grill-with-docs` |
| Ít token khi hỏi cấu trúc code | CodeGraph MCP (`codegraph init` + query) |
| Spec → tickets → implement | Matt skills: `/to-spec`, `/to-tickets`, `/implement` (không Spec Kit) |
| Vai FE/BE/AI chuyên biệt | Agency Agents — **sau**, chọn lọc theo phase |
| Chuyển việc sang session khác | `/handoff` |
| OECD dữ liệu thật | `sdmx1` trong `sdmx_client.py` |
| Forecast đúng proposal | statsmodels ARIMA + giữ XGB/LSTM |
| Marketplace JS-heavy | Playwright (sau: Scrapy) |
| Shop match tốt hơn | sentence-transformers (sau) |
| Orchestrate crawl hàng đêm | Prefect (sau) |
| Graph docs + papers | graphify (sau, nếu CodeGraph chưa đủ) |

---

## Map vào module project

```
crawlers/gso/          → giữ SDMX XML; có thể chuẩn hóa bằng sdmx1
crawlers/oecd/         → sdmx1  (ưu tiên #1 kỹ thuật)
crawlers/marketplace/  → Playwright sâu hơn → Scrapy+Playwright khi scale
crawlers/companies/    → Playwright / httpx + pdfplumber/camelot cho BCTC
pipeline/              → Prefect (sau) + great_expectations
ml/                    → statsmodels ARIMA thật + darts (so sánh model)
shop_matcher           → sentence-transformers (sau RapidFuzz)
frontend/              → Agency Agents frontend-developer (khi làm FE)
backend/               → Agency Agents backend (khi làm API sâu hơn)
```

---

## Đã review (tham khảo lịch sử)

| Repo | Quyết định |
|------|------------|
| mattpocock/skills | **Ngay** (đã cài) |
| colbymchenry/codegraph | **Ngay** (thay codebase-memory-mcp; chưa cài) |
| DeusData/codebase-memory-mcp | **Bỏ** (chưa từng cài) |
| github/spec-kit | **Bỏ** (trùng workflow Matt + `.scratch/`) |
| msitarzewski/agency-agents | **Để sau** — chọn lọc theo phase FE/BE/AI, không cài full |
| Graphify-Labs/graphify | Để sau (optional, sau CodeGraph) |
| Nutlope/hallmark | Bỏ |
| awesome-llm-apps | Bỏ |
| system_prompts_leaks | Bỏ |
| Agent-Reach | Bỏ |
| OmniRoute | Bỏ |
| no-mistakes | Bỏ |
