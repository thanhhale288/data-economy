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
| Chọn task & AC | `.cursor/skills/project-roadmap/SKILL.md`, `docs/plan.md` (hot; không đọc `plan-archive` trừ khi cần checklist cũ) |
| Git commit / push / PR | `.cursor/skills/github-workflow/SKILL.md` |
| Viết prompt chat sau | `writing-coding-prompts` — **bắt buộc** có mục **Waves / Subagents** |
| Đóng task | **Task review** + **Testing results** (chi tiết) — [reference.md](reference.md) |
| Chi tiết wave + templates | [reference.md](reference.md) |
| Repo / MCP / lib | `docs/needGit.md` — chỉ mục khớp task |
| Handoff artifact | Chỉ **một** `.scratch/handoff-task<M>.md` mới (+ phase handoff đang active nếu cần). Xóa handoff task cũ trước khi ghi — [reference.md](reference.md) |

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
- [ ] 7. Cleanup handoff cũ → update plan / handoff mới
- [ ] 8. Task review (what + how, chi tiết)
- [ ] 9. Testing results (lệnh, số pass/fail, ý nghĩa)
- [ ] 10. Prompt chat sau (writing-coding-prompts + Waves) → STOP
```

### 0. Xác định task

- Ưu tiên **block prompt đã dán** trong chat; nếu cần file thì chỉ đọc **một** handoff path user chỉ (thường `.scratch/handoff-task*.md` mới nhất hoặc phase active).
- **Không** glob đọc hàng loạt `handoff-task*.md` cũ — chúng phải đã bị xóa sau mỗi task.
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

Theo `.cursor/skills/epic-phase-task-git/SKILL.md`:

```text
cursor/epic<E>-phase<P>-task<T>-<slug>
```

Legacy (ổn nếu đang dùng): `cursor/phase<N>-task<M>-<slug>`.

```bash
git checkout main && git pull --ff-only
git checkout -b cursor/epic<E>-phase<P>-task<T>-<slug>
```

Không nhét nhiều task vào một branch.

### 4. Waves / Subagents rồi implement

**Waves = bước trong cùng một task** — không phải task roadmap khác.

| Wave | Vai trò mặc định | Output |
|------|------------------|--------|
| W1 Explore | Subagent `explore` (FE/BE, read-only) | Map file, API contract, gaps |
| W2 Implement | Agent chính trên branch task | Diff đúng AC |
| W3 Verify | Test/build; ghi **Testing results** | Bảng lệnh + pass/fail |
| W4 Ship | Cleanup handoff cũ → Commit/PR + handoff mới + review + testing + prompt | PR URL, paste prompt |

- Task nhỏ: gộp W1–W2 (“single wave”).
- Task rộng FE+BE: bắt buộc W1 trước; ưu tiên subagents song song.
- Không invent GSO/OECD/CafeF/marketplace/forecast numbers.

Verify tối thiểu: `PYTHONPATH=. pytest -q` (scope liên quan); FE → `cd frontend && npm run build`.

### 5–6. Commit, push, PR

Theo `github-workflow`. **Một PR = một task.**

### 7. Cleanup handoff cũ → plan + handoff mới

**Mục tiêu:** luôn chỉ giữ handoff cần cho chat sau — tránh chồng file DONE tốn token.

Thứ tự bắt buộc:

1. **Xóa handoff task đã hoàn thành** (trước khi ghi file mới):

```bash
# Xóa mọi handoff task cũ; giữ lại sẽ ghi đè/tạo handoff-task<M>.md ngay sau
rm -f .scratch/handoff-task*.md
```

   - Chỉ xóa `.scratch/handoff-task*.md` — **không** xóa `.scratch/_local_backup/`, report, STATUS, hay file không phải handoff.
   - Nếu đang sửa/ghi đè đúng `handoff-task<M>.md` của task này: xóa các `handoff-task*.md` **khác** `<M>`, rồi ghi `<M>`.

2. **Phase handoff (token thrift):**
   - Khi cập nhật/ tạo `.scratch/handoff-phase*.md` cho phase **tiếp theo**: xóa các `handoff-phase*.md` đã DONE / không còn là “next session focus”.
   - Giữ tối đa: 1 phase handoff active (next) + 1 task handoff vừa viết.

3. Ghi `.scratch/handoff-task<M>.md` (DONE): commit, PR, delivered, **Task review**, **Testing results**, next, **paste prompt** (có Waves).  
   Nội dung phải **tự chứa** context cần cho task sau (không dựa vào handoff task cũ đã xóa).

4. Cập nhật `docs/plan.md` / STATUS nếu có.

5. Trong tin nhắn đóng chat: liệt kê ngắn file handoff đã xóa (paths).

Lịch sử lâu dài: git commits, PR, `docs/plan.md` — không tích lũy handoff.

### 8–9. Task review + Testing results

Templates đầy đủ: [reference.md](reference.md).

Thứ tự cuối chat: **handoff path → Task review → Testing results → paste prompt → STOP.**

### 10. Prompt chat sau

Dùng `writing-coding-prompts`. **Bắt buộc** có `## Waves / Subagents`.

## Phase close

Close audit → xóa phase handoff DONE thừa → ghi handoff phase sau (+ prompt) → milestone/release chỉ khi user yêu cầu.

## Anti-patterns

- Làm task kế trong cùng chat; một branch cả phase.
- Prompt không có Waves; đóng chat thiếu review hoặc testing (hoặc chỉ “passed”).
- **Giữ chồng** `handoff-task*.md` DONE “để xem lại” — xóa trước khi ghi mới.
- Cài hết needGit; handoff temp OS; coi skill là daemon overnight.
- Xóa nhầm `.scratch/_local_backup/` hoặc report không phải handoff.

## Kỳ vọng “lazy”

| Có | Không |
|----|--------|
| Một chat ≈ hết một task | Xong cả project lúc ngủ |
| Cuối chat: review + testing + prompt | Tự mở chat mới |
