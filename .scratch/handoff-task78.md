# Handoff — Task #78 Feedback CafeF + manual

**Status:** DONE  
**Branch:** `cursor/epic5-phase4-task78-feedback-cafef-manual`  
**Date:** 2026-08-19  
**Base:** `origin/main` @ `5a30cce`  
**Worktree:** `.worktrees/t78`  

---

## What shipped

- **CafeF prefill:** after a successful «Nạp RAL/REE» load, Benchmark shows the existing confirm checkbox (`confirm-check`) and `banner-warn` lock. Confirm posts allowlisted field diffs with `source_type=cafef_prefill`. Compare stays disabled until the box is checked (same gate as DocAI). Origin is kept in `feedbackOrigin` so edits that clear `prefillSource` still classify as CafeF.
- **Manual entry:** first keystroke without extract/prefill snapshots the empty/original form. Compare (the confirm action for typed forms) posts diffs with `source_type=manual`. No extra lock; DocAI keep confirm-before-compare.
- **DocAI:** unchanged path — checkbox still required before Compare; `source_type` remains `extractMeta.source_type` or `docai_extract`.
- **Backend:** already accepted these `source_type` values. Tests now cover CafeF + manual POST/JSONL and still refuse raw PDF/secrets. Compare math in `benchmark_service.py` was not touched.

Files:

| Piece | Path |
|-------|------|
| FE confirm + source_type + one-post flag | `frontend/src/pages/Benchmark.jsx` |
| Service docstring | `backend/app/services/feedback_signal.py` |
| Tests | `tests/benchmark/test_feedback_signal.py` |

---

## Double-count rule (same session)

One confirm cycle posts **at most one** training signal.

1. `feedbackPostedRef` is set when `postFeedbackSignal` actually sends. A second call in that cycle returns immediately.
2. **Checkbox confirm posts first** (DocAI extract and CafeF prefill).
3. **Compare also calls `postFeedbackSignal`**, but it is a no-op if the checkbox already posted. Manual typing has no checkbox, so Compare is the single post.
4. Unchecking the box without editing does not post again; the flag stays true for those same values.
5. Any field edit starts a **new** cycle (flag cleared, DocAI/CafeF unconfirm) so a later confirm can record the new diffs — still one post per cycle, never checkbox **and** Compare for the same values.
6. A new extract, CafeF prefill, or insufficient-peer demo resets origin, snapshot, and the flag.

The frontend never sends `raw_pdf` / file bytes. The backend still drops those keys if a client adds them.

---

## Limitations

- Signals are stored only (JSONL). No retrain, no alias harvest (#79).
- CafeF confirm copy assumes prefill buttons (RAL/REE), not a live CafeF crawl in this task.
- Manual path does not add a second checkbox; Compare is the confirm so typed forms are not blocked.
- Confirm-before-compare remains required for DocAI; Compare is not auto-run.

---

## Testing results

```bash
cd /Users/hale/Code/AI in Data Economy/.worktrees/t78
source /Users/hale/Code/AI in Data Economy/.venv/bin/activate
PYTHONPATH=. pytest -q tests/benchmark/ -k feedback
# 9 passed, 73 deselected in 2.61s

cd frontend && npm run build
# vite build OK (844 modules; dist gitignored)
```

Pass/fail: **9 passed, 0 failed** (`-k feedback`). Frontend production build succeeded.
