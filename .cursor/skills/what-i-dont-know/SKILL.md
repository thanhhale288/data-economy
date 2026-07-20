---
name: what-i-dont-know
description: >-
  Explains completed roadmap work the user did not review: what each task
  included, step-by-step how it was done, remaining gaps, and how later tasks
  improved those gaps — in plain language. Explains unfamiliar English/domain
  terms missing from docs/knowledge.md. Use when the user says "cho tôi biết
  những gì tôi chưa biết", "catch me up", "giải thích task đã làm", "tôi bỏ qua
  kiểm duyệt", "hiểu workflow đến task 18", asks what agents did in Tasks
  #13–#18, or wants a plain-language tour of unreviewed phases before continuing.
---

# What I don’t know — catch-up tour

**Announce:** `Đang chạy skill what-i-dont-know — scope Task #<from>–#<to>.`

Chỉ **giải thích** (read-only). Không implement trừ khi user chọn bước tiếp sau tour.

## Default scope

- Không nói scope → **Task #13–#18**.
- Chỉ một task/phase → thu hẹp.
- “Cả project” → Phase 1–3 ngắn; chi tiết #13–#18 + Phase 5 đứng ở đâu.

## Nguồn sự thật

1. `.scratch/handoff-task13.md` … `handoff-task18.md` (+ phase handoff)
2. `docs/plan.md`
3. `.cursor/skills/project-roadmap/SKILL.md`
4. Code paths trong handoff nếu mơ hồ
5. `docs/knowledge.md` — term đã có
6. `CONTEXT.md` / `AGENTS.md`

Không bịa. Thiếu artifact → “chưa rõ từ artifact”.

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

- Có trong `docs/knowledge.md` → chỉ trỏ §, không giải thích dài.
- Chưa có → nghĩa + trong project + một câu nhớ.
- Hỏi có muốn append `knowledge.md` không; chỉ ghi khi user đồng ý.

### 3. Còn mở sau #18
### 4. Hỏi bước tiếp (a sâu task / b knowledge / c Phase 5 / d audit PR)

## Anti-patterns

Tour ≠ implement; bịa việc đã làm; bỏ “task sau cải thiện”; dump diff.

Chi tiết index/templates: [reference.md](reference.md).
