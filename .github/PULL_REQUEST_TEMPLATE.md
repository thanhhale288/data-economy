## Summary

- Phase / scope:
- What changed (1–3 bullets):

## Scratch / docs

- Spec or status: `.scratch/...`
- ADR touched? (Digital VA / OECD policy): 

## Test plan

- [ ] `PYTHONPATH=. pytest -q`
- [ ] `cd frontend && npm run build` (if UI changed)
- [ ] Manual check (API/UI) if behavior changed:
- [ ] No invented GSO/OECD/CafeF/marketplace numbers; fallbacks recorded if used

## Checklist

- [ ] Branch named `cursor/phaseN-...` or clear feature slug
- [ ] Did not commit `.env`, secrets, large raw dumps, or model binaries
- [ ] Formula/domain changes updated `CONTEXT.md` (+ ADR under `docs/adr/` if needed)
