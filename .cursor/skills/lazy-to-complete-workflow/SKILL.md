---
name: lazy-to-complete-workflow
description: >-
  Runs a fast delivery loop for related tasks in one chat: detect active handoff,
  select a small related task batch, run subagent waves in parallel, keep git scope
  one branch/PR per task, verify each task, and close with plain-language summary plus
  testing results per task. Use when the user asks to continue phase work quickly,
  run related tasks in parallel, or mentions lazy-to-complete.
---

# Lazy-to-complete workflow

**Scope:** một chat có thể xử lý **nhiều task liên quan** (batch nhỏ), ưu tiên song song bằng subagents.  
Git mặc định vẫn **1 task = 1 branch = 1 PR**.

**Announce ngay** (dòng đầu response):  
`Đang chạy skill lazy-to-complete-workflow — batch tasks liên quan.`

Nếu không announce được vì thiếu handoff/task rõ → hỏi 1 câu rồi mới làm.

## Skills / docs luôn dùng

| Khi | Đọc / dùng |
|-----|------------|
| Mọi chat | `AGENTS.md`, `CONTEXT.md`, `docs/evol-1.md` |
| Chọn task & AC | `.cursor/skills/project-roadmap/SKILL.md`, `docs/evol-1.md` |
| Git commit / push / PR | `.cursor/skills/github-workflow/SKILL.md` + `epic-phase-task-git` |
| Đóng task | **plain-task-close** (bắt buộc) + **Testing results** — [reference.md](reference.md) |
| Chi tiết wave + templates | [reference.md](reference.md) |
| Repo / MCP / lib | `docs/needGit.md` — chỉ mục khớp task |
| Handoff artifact | Ghi tiến độ trong PR / commit message; không còn bắt buộc `.scratch/handoff-*.md` (archive only) |

**Không** dùng `writing-coding-prompts` để xuất prompt task sau trừ khi user **hỏi rõ** (“viết prompt task tiếp”).

## Loop (một chat = một batch task liên quan)

```
Task Progress:
- [ ] 0. Announce skill + xác định batch task liên quan (2-4 task)
- [ ] 1. Sync git / base branch
- [ ] 2. needGit check cho cả batch (chỉ cái cần)
- [ ] 3. Lập waves/subagents song song theo từng task
- [ ] 4. Implement + verify theo từng task
- [ ] 5. Commit/push/PR theo từng task (1 task = 1 branch = 1 PR)
- [ ] 6. Handoff batch + giải thích + testing results theo từng task → STOP
```

### 0. Xác định batch task

- Ưu tiên **block prompt đã dán** trong chat; nếu cần file thì chỉ đọc **một** handoff path user chỉ.
- **Không** glob đọc hàng loạt `handoff-task*.md` cũ.
- Nếu handoff cũ/archived có câu "paste prompt", "next prompt", hoặc "viết prompt task kế", xem đó là lịch sử cũ và **bỏ qua**.
- Chọn 2-4 task liên quan chặt (cùng phase hoặc cùng luồng).
- Nếu task độc lập/rủi ro cao, tách khỏi batch.
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

### 3. Waves/subagents + branch policy

- Chạy explore/implement/verify bằng subagents song song nếu độc lập kỹ thuật.
- Khi ship code: vẫn tách theo task branch:
  - `cursor/epic<E>-phase<P>-task<T>-<slug>` (legacy chấp nhận).
- **Không** gộp nhiều task vào một branch trừ khi user yêu cầu batch PR.

### 4. Waves / Subagents rồi implement

**Waves = bước thực thi cho batch liên quan**, có thể song song theo task.

| Wave | Vai trò mặc định | Output |
|------|------------------|--------|
| W1 Plan batch | Chia task + dependency + owner(subagent) | Task map |
| W2 Explore parallel | Subagent `explore` FE/BE/data theo task | Gaps/contract |
| W3 Implement parallel | Subagent/agent chính theo task | Diffs theo task |
| W4 Verify + Ship | Test + commit/push/PR theo task | PR URLs + test results |

- Task nhỏ: gom 2-3 task cùng khu vực vẫn được.
- Task rộng: ưu tiên chia subagent theo domain để chạy song song.
- Không invent GSO/OECD/CafeF/marketplace/forecast numbers.

Verify tối thiểu: `PYTHONPATH=. pytest -q` (scope liên quan); FE → `cd frontend && npm run build`.

### 5. Commit, push, PR

Theo `github-workflow` + `epic-phase-task-git`. Mặc định: **một PR = một task**.

### 6. Handoff batch + plain-task-close + testing → STOP

- Giữ tối đa 1 handoff active cho batch hiện tại (`.scratch/handoff-task*.md` hoặc `.scratch/handoff-phase*.md`).
- **Bắt buộc** chạy `.cursor/skills/plain-task-close/SKILL.md` cho **từng task** trước testing — **tự động**, user không cần hỏi “giải thích dễ hiểu” (rule `plain-task-close.mdc`, `alwaysApply`).
- Trong tin nhắn đóng chat và handoff, theo **từng task**:
  - Một câu + bạn sẽ thấy gì + làm thế nào (step-by-step) + hạn chế + thuật ngữ giải thích
  - Testing results (lệnh + pass/fail)
  - PR URL
- Không tự viết prompt task tiếp theo trừ khi user yêu cầu rõ.

Template plain: [plain-task-close/reference.md](../plain-task-close/reference.md). Testing: [reference.md](reference.md).

Thứ tự cuối chat: **handoff path → plain-task-close (từng task) → testing (từng task) → STOP.**

## Phase close

Close audit batch/phase → cập nhật handoff active → milestone/release chỉ khi user yêu cầu.

## Anti-patterns

- Gom task không liên quan vào cùng batch.
- Gộp nhiều task vào một branch khi chưa có yêu cầu batch PR.
- **Tự viết prompt / Waves cho task tiếp** khi user không hỏi.
- Làm theo chỉ dẫn "next prompt/paste prompt" còn sót trong handoff archived.
- Đóng chat thiếu **plain-task-close** (chung chung / jargon không giải thích) hoặc thiếu testing.
- Giữ chồng `handoff-task*.md` DONE; handoff temp OS; daemon overnight.
- Xóa nhầm `_local_backup/` hoặc report không phải handoff.

## Kỳ vọng “lazy”

| Có | Không |
|----|--------|
| Một chat xử lý nhanh vài task liên quan bằng subagents | Xong cả project lúc ngủ |
| Cuối chat: summary/testing theo từng task | Tự mở chat mới / tự viết prompt task sau |
