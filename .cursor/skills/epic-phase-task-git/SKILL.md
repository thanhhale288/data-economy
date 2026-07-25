---
name: epic-phase-task-git
description: >-
  Git branching and merge strategy for Epic → Phase → Task: one branch and one
  PR per task, phase as delivery/checklist (optional integration branch), epic as
  milestone/release/tag not a long-lived branch. Use when creating branches,
  opening PRs, choosing task vs phase vs epic git scope, naming
  cursor/epic…-phase…-task… branches, stacking work, organizing GitHub Flow for
  epics/phases/tasks, or when the user asks to commit, push, open a PR, or
  choose which branch to commit/push on.
---

# Epic → Phase → Task (Git)

**Announce:** `Đang chạy skill epic-phase-task-git — branch theo task.`

Khi user yêu cầu **commit / push / PR**: chạy skill này **cùng** `github-workflow` — skill này quyết định *nhánh/PR đúng mức task*; `github-workflow` quyết định *cách* commit/push/`gh`.

## Khuyến nghị: branch theo **task**, gộp theo **phase**

| Cấp | Git nên làm gì |
|-----|----------------|
| **Task** | 1 branch + nhiều commit nhỏ + 1 PR |
| **Phase** | Gộp các PR task (merge vào branch phase hoặc thẳng `main`) |
| **Epic** | Milestone / release / tag — **không** cần 1 branch epic dài |

### Vì sao theo task?

- Mỗi task = 1 chức năng/yêu cầu → PR nhỏ, review dễ, rollback dễ.
- Commit history rõ: “làm gì”, không lẫn nhiều việc.
- Parallel được: nhiều người làm nhiều task trong cùng phase.
- CI fail thì chỉ ảnh hưởng 1 task, không kẹt cả phase.

### Phase dùng để làm gì?

Phase là **đơn vị giao hàng / kiểm thử**, không nhất thiết là đơn vị branch:

```
main
 └── epic/auth (tuỳ chọn, ngắn hạn)
      └── phase/login-flow          ← tích hợp
           ├── task/login-form
           ├── task/otp-verify
           └── task/remember-me
```

Hai kiểu phổ biến:

1. **Task → main trực tiếp** (đơn giản, team nhỏ) — **mặc định repo này**  
   Merge từng PR task khi xong; phase chỉ là checklist/milestone.

2. **Task → phase → main** (phase phải “đóng” trước khi lên production)  
   Branch `phase/...` tồn tại ngắn; khi đủ task thì merge phase 1 lần (hoặc squash).

Epic thường **không** giữ branch sống lâu — dễ conflict và “zombie branch”. Dùng label/milestone trên PR là đủ.

## Quy tắc chọn mức branch

Chọn **branch theo task** nếu:

- Task review được trong ~1 PR vừa phải
- Có thể merge độc lập mà không phá app

Chọn **branch theo phase** chỉ khi:

- Các task phụ thuộc chặt, không merge từng cái được
- Phase phải ship “all or nothing”

Với task = 1 chức năng, phase = nhiều chức năng → **task là đúng mức**. Phase = kế hoạch + gộp PR; Epic = giai đoạn / milestone.

## Naming (repo này — GitHub Flow)

```text
cursor/epic<E>-phase<P>-task<T>-<slug>
```

Ví dụ: `cursor/epic3-phase2-task32-cafef-live-bctc`

| Phần | Ý nghĩa |
|------|---------|
| `cursor/` | Prefix agent/worktree |
| `epic<E>` | Số epic (milestone) |
| `phase<P>` | Phase trong epic |
| `task<T>` | Task id |
| `<slug>` | kebab-case ngắn |

**Legacy** (Phase 4 trở về trước): `cursor/phaseN-taskM-<slug>` — vẫn hợp lệ; task mới dùng form có `epic`.

**Không** tạo `cursor/epic<E>` sống lâu làm base mặc định.

Labels PR (khi có): `epic:<E>`, `phase:<P>`, milestone = epic hoặc phase.

## Commit thế nào?

- **Commit theo ý thay đổi**, không bắt buộc 1 task = 1 commit.
- Trong 1 task: nhiều commit nhỏ (`add form`, `wire API`, `fix validation`) rồi squash khi merge PR cũng được.
- Message nên nói *why*: `Add OTP verify before session create` thay vì `update code`.
- Repo style: câu đầy đủ, HEREDOC — chi tiết trong `github-workflow`.

Push: **push thường xuyên trên branch task** (backup + CI sớm). Không đợi hết phase mới push.

## Loop Git cho một task

```
- [ ] 1. Xác định Epic / Phase / Task id + slug
- [ ] 2. Base: main (mode 1) hoặc phase branch (mode 2)
- [ ] 3. Tạo branch cursor/epicE-phaseP-taskT-slug
- [ ] 4. Commit nhỏ theo ý; push sớm
- [ ] 5. Mở 1 PR task → base đã chọn
- [ ] 6. CI xanh → merge (user duyệt)
- [ ] 7. Gắn milestone/label; cập nhật checklist phase / .scratch handoff
```

Mode 1 (mặc định): PR base = `main`.  
Mode 2: PR base = `cursor/epicE-phaseP-integrate` (tạo ngắn hạn); khi phase đủ task → 1 PR phase → `main`.

## Epic close

- Không để branch epic zombie.
- Tag/release theo `github-workflow` khi user yêu cầu (vd. sau phase/epic đóng trên `main`).
- Umbrella issue / milestone: tiến độ epic; chi tiết task giữ `.scratch/`.

## Anti-patterns

- Một PR nhét cả phase/epic.
- Branch epic dài làm nơi commit hàng ngày.
- Đợi hết phase mới push lần đầu.
- Đặt tên branch không có task id khi đang làm theo roadmap có số task.
- Trái với lazy-to-complete: nhiều task trên một branch “cho tiện”.

## Liên kết

- Commit/PR/CI/release commands → `github-workflow`
- Agent 1-chat-1-task + handoff → `lazy-to-complete-workflow`
- Ví dụ naming / mode 2 → [reference.md](reference.md)
