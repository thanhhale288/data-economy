## Handoff Task #54 + #55 (DocAI API + FE upload/prefill/confirm)

### Scope delivered
- Task #54: Added `POST /api/benchmark/extract` in `backend/app/api/benchmark.py` with multipart upload.
- Task #54: Reused existing `bctc_extract` service (`extract_bctc_dict`) from #52/#53, no parser/OCR duplication.
- Task #54: Added stable response contract schema `BenchmarkExtractResponse` in `backend/app/schemas/__init__.py`:
  - `fields`
  - `confidence`
  - `warnings`
  - `source_type`
- Task #54: Added API tests in `tests/benchmark/test_benchmark_api.py` for contract and empty-file rejection.
- Task #55: Added FE upload extract API in `frontend/src/api.js` (`benchmarkExtract`) with FormData-safe request headers.
- Task #55: Updated `frontend/src/pages/Benchmark.jsx`:
  - Upload BCTC file and prefill form from extract response
  - Highlight low-confidence extracted fields
  - Require human confirmation checkbox before compare
  - Keep benchmark math/compare logic unchanged

### Constraints check
- No DB write added in extract endpoint.
- No auto-compare or auto-submit on extract.
- Missing/unclear values remain null with warnings (service behavior reused).
- No out-of-scope task implementation added in this handoff file.

### Verification results
- Backend tests:
  - Command: `PYTHONPATH=. python3 -m pytest -q tests/benchmark/ -k "extract"`
  - Result: `17 passed, 4 skipped, 21 deselected`
- Frontend build:
  - Command: `cd frontend && npm run build`
  - Result: `vite build` succeeded

### Manual smoke status
- Upload PDF text fixture: Not run in this chat (manual UI step pending).
- Upload scan/image fixture: Not run in this chat (manual UI step pending).
- Prefill editable + confirm-before-compare UX: Implemented; manual click-through pending.

### Notes
- Working tree currently contains unrelated changes from other tasks/branches; this handoff only records Task #54/#55 scope.
