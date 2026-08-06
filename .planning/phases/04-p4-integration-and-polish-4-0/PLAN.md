# Phase 4 Plan — Integration & Polish

## Files
- `webui/static/app.js` (MODIFY if needed)
- `.github/workflows/ci.yml` (MODIFY if needed)
- `codemap.md`, `AGENTS.md` (MODIFY)
- `webui/static/codemap.md` (MODIFY)

## Tasks
### T4.1 — Regression check
- Boot live server on :8000.
- Confirm existing endpoints work: `/api/ping`, `/api/presets`, `/api/outputs`, `/api/balance`.
- Confirm photo pipeline start still works (no server import break).

### T4.2 — CI
- Check `.github/workflows/ci.yml` path lists include `scripts/`. Add `scripts/alina_textgen.py` py_compile if the workflow uses explicit file lists.

### T4.3 — Docs
- codemap.md: add `scripts/alina_textgen.py` to file structure.
- AGENTS.md: add "Caption Generator" to Active Components (endpoint + UI card).
- Session protocol: prompt "Update AGENTS.md with these changes?" if user wants.

## Verify
- `python -m py_compile` on all touched Python files.
- `node --check` on app.js.
- Live server round-trip: generate captions via UI.

## Acceptance
- Live server test on :8000, existing endpoints intact, CI passes, docs updated.
