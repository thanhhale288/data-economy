# lazy-to-complete-workflow — reference

## Branch & PR (multi-task chat)

| Unit | Git |
|------|-----|
| 1 task | 1 branch `cursor/epicE-phaseP-taskT-slug` (legacy: `cursor/phaseN-taskM-slug`) |
| 1 task done | 1 PR → `main` (default) |
| Phase done | Mọi task PR của phase đã merge + handoff phase |

## Waves vs tabs vs Task tool

| Cơ chế | Khi dùng |
|--------|----------|
| Task tool subagents cùng chat | W1 explore FE/BE song song |
| Nhiều tab Cursor | Mỗi tab = một wave trong prompt **đầu** chat (user dán) |
| Single wave | Task rất hẹp |

Waves dùng để chia và chạy **nhiều task liên quan** trong cùng chat. Ship code vẫn tách branch/PR theo task.

## Default wave templates (trong lúc làm task)

### FE + API

```markdown
## Waves / Subagents
- **W1 Explore (parallel, read-only):** (a) FE (b) BE — map + gaps.
- **W2 Implement:** mỗi subagent bám 1 task hoặc 1 cụm file.
- **W3 Verify:** pytest / build; ghi Testing results.
- **W4 Ship:** PR theo từng task → tổng hợp giải thích/testing theo task → STOP.
```

### Pipeline / ML / Docs

Cùng W4: **không** append prompt task tiếp.

## Giải thích dễ hiểu (cuối batch — theo từng task)

```markdown
## Task #<M> — tóm tắt dễ hiểu

### Đã làm được gì
- <bullet thường, 3–6 ý: user/demo thấy gì, API/trang nào, dữ liệu thật vs fallback>
- Branch / PR: `…` / <url>

### Hạn chế / chưa làm được
- <thiếu nguồn, sample nhỏ, chưa live scrape, UI N/A khi thiếu peer, …>
- <phạm vi cố ý không làm trong task này>

### Ghi chú một dòng (tuỳ chọn)
- Task kế trên roadmap: #<M+1> — chỉ khi user muốn làm tiếp mới mở chat mới.
```

Cấm: block `# Task` / `## Waves` / paste-prompt cho task sau trừ khi user yêu cầu riêng.

## Testing results template (theo từng task)

```markdown
## Testing results — Task #<M>

### Tóm tắt
- Overall: PASS | PASS-with-skips | FAIL
- Ý nghĩa: …

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
.scratch/handoff-taskM.md     # có thể ghi nhiều task trong một file batch, nhưng phải chia rõ theo task
.scratch/handoff-phaseN.md    # phase active / next (nếu có)
```

```bash
rm -f .scratch/handoff-task*.md   # rồi ghi handoff batch mới
```

**Giữ tối đa:** 1× handoff task/batch active + 0–1× phase handoff active.

Handoff sections: Status, Branches/PRs theo task, Delivered, **Giải thích dễ hiểu theo task**, **Testing results theo task**, Do not reopen.  
**Không** nhét paste-prompt task sau vào handoff.

Đóng chat: nêu paths đã `rm`.

## needGit filter

Đọc `docs/needGit.md`. Chỉ cài cái AC đòi. Không invent số.

## Verify cheatsheet

```bash
PYTHONPATH=. pytest -q
cd frontend && npm run build
```
