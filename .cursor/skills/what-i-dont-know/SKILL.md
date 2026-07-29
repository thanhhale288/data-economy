---
name: what-i-dont-know
description: >-
  Explains completed roadmap work the user did not review: what each task
  included, step-by-step how it was done, remaining gaps, and how later tasks
  improved those gaps — in plain language. Explains unfamiliar English/domain
  terms using CONTEXT.md (never docs/knowledge.md). Use when the user says
  "cho tôi biết những gì tôi chưa biết", "catch me up", "giải thích task đã làm",
  "tôi bỏ qua kiểm duyệt", "hiểu workflow đến task 18", asks what agents did in
  Tasks #13–#18, or wants a plain-language tour of unreviewed phases before
  continuing.
---

# What I don’t know — catch-up tour

**Announce:** `Đang chạy skill what-i-dont-know — scope Task #<from>–#<to>.`

Chỉ **giải thích** (read-only). Không implement trừ khi user chọn bước tiếp sau tour.

## Default scope

- Không nói scope → **Task #13–#18**.
- Chỉ một task/phase → thu hẹp.
- “Cả project” → Phase 1–3 ngắn; chi tiết #13–#18 + Phase 5 đứng ở đâu.

## Nguồn sự thật

1. Block prompt / **một** handoff active (`.scratch/handoff-task*.md` hoặc phase next) — lazy-to-complete **xóa** handoff task cũ mỗi lần đóng task; không kỳ vọng còn đủ chuỗi #13–#18
2. `docs/plan.md`
3. `.cursor/skills/project-roadmap/SKILL.md`
4. Git history / PR + code paths nếu handoff cũ đã xóa
5. `CONTEXT.md` / `AGENTS.md` / `docs/adr/` — thuật ngữ
6. **Cấm:** `docs/knowledge.md` (`.cursorignore`; human-only)

Không bịa. Thiếu artifact → “chưa rõ từ artifact” + dùng plan/PR.

## Output bắt buộc

### 0. Bản đồ 30 giây
### 1. Tour từng task (#13→#18)

Với mỗi task:

```markdown
## Task #<N> — <tên dễ hiểu>
**Một câu:** …

### Bao gồm gì
### Làm như thế nào (step-by-step)
### Khoảng trống / chưa hoàn thiện lúc đóng task
### Task sau cải thiện thế nào
```

Cuối: **Luồng end-to-end** 5–8 bước.

### 2. Thuật ngữ có thể chưa biết

- Có trong `CONTEXT.md` / ADR → trỏ §, giải thích ngắn.
- Chưa có → nghĩa + trong project + một câu nhớ.
- **Không** đọc/ghi `docs/knowledge.md`. User tự cập nhật glossary nếu muốn.

### 3. Còn mở sau #18
### 4. Hỏi bước tiếp (a sâu task / b term khác / c Phase 5 / d audit PR)

## Anti-patterns

Tour ≠ implement; bịa việc đã làm; bỏ “task sau cải thiện”; dump diff; mở `knowledge.md`.

Chi tiết index/templates: [reference.md](reference.md).
