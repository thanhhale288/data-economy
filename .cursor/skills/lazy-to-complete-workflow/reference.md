# lazy-to-complete-workflow — reference

## Branch & PR (strategy B)

| Unit | Git |
|------|-----|
| 1 task | 1 branch `cursor/epicE-phaseP-taskT-slug` (legacy: `cursor/phaseN-taskM-slug`) |
| 1 task done | 1 PR → `main` |
| Phase done | Mọi task PR của phase đã merge + handoff phase |

## Waves vs tabs vs Task tool

| Cơ chế | Khi dùng |
|--------|----------|
| Task tool subagents cùng chat | W1 explore FE/BE song song |
| Nhiều tab Cursor | Mỗi tab = một wave trong prompt |
| Single wave | Task rất hẹp |

`writing-coding-prompts` = khung mục. Skill này **bắt** thêm `## Waves / Subagents`.

## Default wave templates

### FE + API

```markdown
## Waves / Subagents
- **W1 Explore (parallel, read-only):** (a) FE (b) BE — map + gaps.
- **W2 Implement:** chỉ Task #<M> trên `cursor/epicE-phaseP-taskT-slug`.
- **W3 Verify:** pytest / build; ghi Testing results (lệnh + số liệu).
- **W4 Ship:** PR → handoff → task review → testing results → prompt → STOP.
```

### Pipeline / ML

```markdown
## Waves / Subagents
- **W1 Explore:** train/eval + tests + artifacts.
- **W2 Implement:** đúng AC; không fake series.
- **W3 Verify:** pytest + Testing results.
- **W4 Ship:** … → review → testing → prompt → STOP.
```

### Docs-only / nhỏ

```markdown
## Waves / Subagents
- **Single wave:** sửa → verify → ship → review → testing → prompt → STOP.
```

## Task review template

```markdown
## Task review — #<M> <title>

### Tiến độ
- Ước lượng hoàn thành AC: …
- Status: DONE | DONE-with-gaps | BLOCKED
- Phase · Branch · Tip · PR

### Đã làm được gì (đối chiếu AC)
| Acceptance criterion | Status | Ghi chú |
|----------------------|--------|---------|
| … | done / partial / skipped | … |

Deliverable chính:
- …

### Làm thế nào
- Waves: …
- Subagents/tabs: …
- File chính: `path` — …
- Quyết định / trade-off: …
- So với plan: …

### Còn lại / rủi ro (không làm trong chat này)
- …
```

## Testing results template

```markdown
## Testing results — Task #<M>

### Tóm tắt
- Overall: PASS | PASS-with-skips | FAIL
- Ý nghĩa tiến độ: …

### Lệnh đã chạy
| # | Command | Scope | Result | Notes |
|---|---------|-------|--------|-------|
| 1 | `…` | … | `N passed` | … |

### Failures (nếu có)
| Test | Error ngắn | Đã fix? | Còn lại |
|------|------------|---------|---------|
| … | … | … | … |

### Skipped / chưa chạy
| Kiểm tra | Lý do | Cần task sau? |
|----------|-------|---------------|
| … | … | … |

### CI (nếu có PR)
- Checks: …
```

## Handoff layout + cleanup

```
.scratch/handoff-taskM.md     # chỉ giữ bản của task vừa xong
.scratch/handoff-phaseN.md    # chỉ giữ phase active / next (nếu có)
```

### Cleanup trước khi ghi handoff mới

```bash
# Task handoffs: xóa mọi bản cũ rồi ghi handoff-task<M>.md
rm -f .scratch/handoff-task*.md

# Phase: chỉ xóa phase DONE/superseded khi đã có handoff phase next mới
# (không xóa phase next đang là nguồn cho chat sau)
```

**Giữ tối đa:** 1× `handoff-task*.md` + 0–1× `handoff-phase*.md` active.

Handoff task sections: Status, Branch, Commit, PR, Delivered, **Task review**, **Testing results**, Do not reopen, Next, **Paste prompt** (có Waves).  
Phải standalone — chat sau không được cần file task handoff đã xóa.

Đóng chat: nêu paths đã `rm`.

## needGit filter

Đọc `docs/needGit.md`. Chỉ cài cái AC đòi. Không invent số. CodeGraph optional nếu đã cài.

## Prompt chat sau — skeleton

```markdown
# Task
Implement Task #<M> — <outcome>.

## Context
- Handoff: `.scratch/handoff-task<prev>.md`
- Read: AGENTS.md, CONTEXT.md, docs/plan.md, project-roadmap, lazy-to-complete-workflow

## Requirements
- …

## Constraints
- One task; branch `cursor/epicE-phaseP-taskT-slug`
- No invent numbers

## Non-goals
- Other tasks

## Waves / Subagents
- **W1 …**
- **W2 …**
- **W3 …**
- **W4 …**

## Verification
- …

## Deliverable
Waves → PR → handoff → Task review → Testing results → next prompt → STOP.
```

## Verify cheatsheet

```bash
PYTHONPATH=. pytest -q
cd frontend && npm run build
```
