---
name: lazy-to-complete-workflow
description: >-
  Runs the one-chat-one-task delivery loop for this repo: detect pasted handoff,
  pick next task, create one branch per task, check docs/needGit.md, implement
  via wave/subagent plan, verify, commit, update plan/handoff, write a detailed
  task review plus testing results (for progress tracking), then stop with a
  ready next-chat prompt (writing-coding-prompts + waves). Use when the user
  pastes a handoff (.scratch/handoff-*.md), starts a new chat after a phase/task
  close audit, says continue Phase N / Task #M, lazy-to-complete, or asks to
  finish the next roadmap task without carrying prior chat context.
---

# Lazy-to-complete workflow

**Scope:** đúng **một task** trong chat này. Hết task → handoff → **task review** → **testing results** → prompt chat sau → **dừng**. Không làm task kế trong cùng chat.

**Announce ngay** (dòng đầu response):  
`Đang chạy skill lazy-to-complete-workflow — Task #<N> only.`

Nếu không announce được vì thiếu handoff/task rõ → hỏi 1 câu rồi mới làm.

## Skills / docs luôn dùng

| Khi | Đọc / dùng |
|-----|------------|
| Mọi chat | `AGENTS.md`, `CONTEXT.md`, handoff đã dán / `.scratch/handoff-*.md` |
| Chọn task & AC | `.cursor/skills/project-roadmap/SKILL.md`, `docs/plan.md` |
| Git commit / push / PR | `.cursor/skills/github-workflow/SKILL.md` |
| Viết prompt chat sau | `writing-coding-prompts` — **bắt buộc** có mục **Waves / Subagents** |
| Đóng task | **Task review** + **Testing results** (chi tiết) — [reference.md](reference.md) |
| Chi tiết wave + templates | [reference.md](reference.md) |
| Repo / MCP / lib | `docs/needGit.md` — chỉ mục khớp task |
| Handoff artifact | `.scratch/handoff-task<N>.md` (+ phase handoff nếu đóng phase) — **không** ghi temp OS |

## Loop (một chat = một task)

```
Task Progress:
- [ ] 0. Announce skill + xác định Task #
- [ ] 1. Sync git / base branch
- [ ] 2. needGit check (chỉ cái cần)
- [ ] 3. Branch riêng cho task
- [ ] 4. Lập Waves / Subagents rồi implement + verify
- [ ] 5. Commit (khi user cho phép hoặc đã bảo hoàn tất task)
- [ ] 6. Push + PR task
- [ ] 7. Update plan / STATUS / handoff
- [ ] 8. Task review (what + how, chi tiết)
- [ ] 9. Testing results (lệnh, số pass/fail, ý nghĩa)
- [ ] 10. Prompt chat sau (writing-coding-prompts + Waves) → STOP
```

### 0. Xác định task

- Đọc handoff dán vào chat hoặc path user chỉ.
- Task hiện tại = task chưa DONE đầu tiên (roadmap), mọi blocker đã xong.
- **Không** reopen task/phase đã DONE trừ bug có chứng cứ.

### 1. Sync

```bash
git fetch origin
git status
```

- Base ưu tiên: `main` đã merge PR trước.
- Nếu PR trước chưa merge: base = tip đã ghi trong handoff.
- Không commit trên `main`.

### 2. needGit check

Đọc `docs/needGit.md`. Chỉ đề xuất / cài cái **khớp task**. Chi tiết: [reference.md](reference.md).

### 3. Branch (1 branch / 1 task)

```text
cursor/phase<N>-task<M>-<slug>
```

```bash
git checkout main && git pull --ff-only
git checkout -b cursor/phase<N>-task<M>-<slug>
```

### 4. Waves / Subagents rồi implement

**Waves = bước trong cùng một task** — không phải task roadmap khác.

| Wave | Vai trò mặc định | Output |
|------|------------------|--------|
| W1 Explore | Subagent `explore` (FE/BE, read-only) | Map file, API contract, gaps |
| W2 Implement | Agent chính trên branch task | Diff đúng AC |
| W3 Verify | Test/build; ghi **Testing results** | Bảng lệnh + pass/fail |
| W4 Ship | Commit/PR + handoff + review + testing + prompt | PR URL, paste prompt |

- Task nhỏ: gộp W1–W2 (“single wave”).
- Task rộng FE+BE: bắt buộc W1 trước; ưu tiên subagents song song.
- Không invent GSO/OECD/CafeF/marketplace/forecast numbers.

Verify tối thiểu: `PYTHONPATH=. pytest -q` (scope liên quan); FE → `cd frontend && npm run build`.

### 5–6. Commit, push, PR

Theo `github-workflow`. **Một PR = một task.**

### 7. Update plan + handoff

`.scratch/handoff-task<M>.md`: commit, PR, delivered, **Task review**, **Testing results**, next, **paste prompt** (có Waves).

### 8–9. Task review + Testing results

Templates đầy đủ: [reference.md](reference.md).

Thứ tự cuối chat: **handoff path → Task review → Testing results → paste prompt → STOP.**

### 10. Prompt chat sau

Dùng `writing-coding-prompts`. **Bắt buộc** có `## Waves / Subagents`.

## Phase close

Close audit → handoff phase + prompt phase sau → milestone/release chỉ khi user yêu cầu.

## Anti-patterns

- Làm task kế trong cùng chat; một branch cả phase.
- Prompt không có Waves; đóng chat thiếu review hoặc testing (hoặc chỉ “passed”).
- Cài hết needGit; handoff temp OS; coi skill là daemon overnight.

## Kỳ vọng “lazy”

| Có | Không |
|----|--------|
| Một chat ≈ hết một task | Xong cả project lúc ngủ |
| Cuối chat: review + testing + prompt | Tự mở chat mới |
