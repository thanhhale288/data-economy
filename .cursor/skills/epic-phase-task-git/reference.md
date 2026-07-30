# epic-phase-task-git — reference

## Mode 1 — Task → main (default)

```bash
git fetch origin
git checkout main && git pull --ff-only
git checkout -b cursor/epic3-phase2-task32-cafef-live-bctc
# … commits …
git push -u origin HEAD
gh pr create --base main --title "…" --body "…"
```

PR: một task, labels/milestone epic+phase nếu dùng.

## Mode 2 — Task → phase → main

Chỉ khi user/AC đòi “all or nothing”.

```bash
# Phase integrate (ngắn hạn)
git checkout main && git pull --ff-only
git checkout -b cursor/epic3-phase2-integrate

# Mỗi task
git checkout -b cursor/epic3-phase2-task32-cafef-live-bctc
git push -u origin HEAD
gh pr create --base cursor/epic3-phase2-integrate

# Khi đủ task + CI
gh pr create --base main --head cursor/epic3-phase2-integrate
# Sau merge: xóa branch integrate
```

## Map lazy-to-complete

| lazy-to-complete | epic-phase-task-git |
|------------------|---------------------|
| 1 chat = many related tasks | still 1 branch + 1 PR per task (default) |
| `cursor/phaseN-taskM-slug` | Prefer `cursor/epicE-phaseP-taskT-slug` |
| Push+PR cuối task | Push sớm + PR khi sẵn sàng review |

## Checklist phase (không phải branch)

Dùng milestone GitHub hoặc `.scratch/handoff-phase*.md`:

- [ ] Task a merged
- [ ] Task b merged
- [ ] Smoke/E2E phase
- [ ] Docs/plan updated
- [ ] (Optional) release tag

## Khi nào phá lệ

Gộp 2 task một PR chỉ khi user xác nhận rõ và hai thay đổi không tách review được — ghi lý do trong PR body.
