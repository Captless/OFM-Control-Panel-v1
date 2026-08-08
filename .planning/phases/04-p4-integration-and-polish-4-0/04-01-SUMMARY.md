---
phase: 4
plan: 04-01
status: complete
subsystem: integration-polish
tags: [ci, docs, codemap, agents-md, regression]
depends_on:
  requires: [03-01]
  provides: [04-02]
  affects: [.github/workflows/ci.yml, codemap.md, scripts/codemap.md, webui/codemap.md, AGENTS.md]
tech-stack:
  added: []
  patterns: []
key-files:
  created: []
  modified:
    - .github/workflows/ci.yml
    - codemap.md
    - scripts/codemap.md
    - webui/codemap.md
    - AGENTS.md
decisions:
  - "PowerShell curl inline -d JSON mangles quoting → use --data-binary @file for POST body checks"
  - "scripts/codemap.md 'Not consumed by' was factually wrong (server.py consumes batch_generate) → corrected to 'Consumed by'"
actuals:
  tokens: 7800
  tasks: 5
  commits: 3
---

# Phase [4] Plan [04-01]: Integration & Polish (caption generator docs + CI) Summary

## One-liner

CI + repo docs integration for the caption generator feature: scripts/alina_textgen.py wired into `.github/workflows/ci.yml` syntax-check + import-test, codemaps (root, scripts, webui) and AGENTS.md updated, and a live regression pass proving all pre-existing :8000 endpoints intact.

## What Was Done

### Task 1 — Regression check on :8000 (PASSED)
Verified against the running server (PID 23588, started 2026-08-08 11:47:45, post-phase-3 code):

| Endpoint | Result |
|----------|--------|
| GET /api/ping | `{"ok": true}` |
| GET /api/presets | JSON: vibes, camera_styles, outfit_styles, lighting (6 incl flash/screen/mixed), time_of_day |
| GET /api/outputs | JSON: date-grouped output batches |
| GET /api/balance | `{"balance":0.01,"per_photo":0.07}` |
| POST /api/captions/generate `{"count":3,"platform":"tiktok","seed":1}` | HTTP 200, `ok:true`, 3 captions |
| GET / | 200, contains `caption-gen-card` |

No regressions. All endpoints intact.

**Note (not a deviation):** initial inline `curl.exe -d '{"count":...}'` POST attempts from PowerShell returned HTTP 000 / empty responses because PowerShell mangles inline JSON quoting → the server's `json.loads()` raises uncaught → thread connection reset. Re-sending the identical body via `--data-binary @file` (UTF-8/ASCII file) returns HTTP 200 instantly. Server-side handler (`webui/server.py` `_read_body` + `/api/captions/generate` route) is correct — verified standalone `batch_generate` (m0017) and file-based round trips (count=3 seed=1, count=2 seed=7). This is a shell-quoting artifact, not a server regression.

### Task 2 — CI coverage (PASSED)
`.github/workflows/ci.yml`:
- syntax-check job: added `python -m py_compile scripts/alina_textgen.py` (after run_tiktok.py, alphabetical-ish placement).
- import-test job: added `python -c "import sys; sys.path.insert(0, 'scripts'); import alina_textgen; print('scripts OK')"` after the api OK line (scripts/ has no `__init__.py`, mirrors runtime resolution).
- YAML validated via `yaml.safe_load` — 3 jobs intact, both additions confirmed. No other workflow changes.

### Task 3 — Codemap docs (PASSED)
- `codemap.md`: scripts/ directory-table file count `6 files` → `7 files` (responsibility string unchanged).
- `scripts/codemap.md`: Files table `alina_textgen.py` row ("Identity-locked caption generator CLI - N captions for platform (tiktok/reels/shorts/x/stories), seed, prints to stdout"); Usage line `py scripts/alina_textgen.py 10 tiktok --seed 42    # 10 TikTok captions (identity-locked)`.
- `scripts/codemap.md` Integration: corrected factually-wrong "**Not consumed by**: Other modules" → "**Consumed by**: `webui/server.py` (`batch_generate` for `POST /api/captions/generate`)" — phase 2 wired the server to this module, so the old line was false.
- `webui/codemap.md`: server.py row Responsibility appended `, caption generation (`POST /api/captions/generate`)` (trivial addition).

### Task 4 — AGENTS.md (PASSED)
- File Structure tree: `├── alina_textgen.py   Caption generator CLI (identity-locked pools)` under scripts/, before run_tiktok.py (tree alignment kept).
- Active Components → Web UI: "Caption Generator" bullet (platform/hook pills, count, `generateCaptions()`/`renderCaptions()`/`copyCaption()`/`copyAllCaptions()`/`clearCaptions()`, backed by `POST /api/captions/generate` → `scripts/alina_textgen.py`).
- API Endpoints table: `POST /api/captions/generate` row (count 1-20, platform, hook_types, seed).
- Recent Changes: `### 2026-08-06 — Caption generator feature (phases 1-4)` entry at top (generator module / server endpoint / UI card / CI + docs / verified, established terse `**…** ✓` style).

### Task 5 — Final verification (PASSED)
- `python -m py_compile scripts/alina_textgen.py webui/server.py` → exit 0.
- `node --check webui/static/app.js` → exit 0.
- Live round-trip POST count=2 seed=7 → HTTP 200, `ok:true`, 2 captions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] scripts/codemap.md "Not consumed by" factually wrong**
- **Found during:** Task 3
- **Issue:** Integration section claimed scripts are "Not consumed by: Other modules (user-facing convenience scripts)" — false since phase 2 wired `webui/server.py` → `batch_generate` from `scripts/alina_textgen.py` via `sys.path`.
- **Fix:** Replaced with "**Consumed by**: `webui/server.py` (`batch_generate` for `POST /api/captions/generate`)".
- **Files modified:** scripts/codemap.md
- **Commit:** 42e9f85

**2. [Rule 3 - Tooling] PowerShell inline curl JSON POST body mangled**
- **Found during:** Task 1
- **Issue:** `curl.exe -d '{"count":3,...}'` from PowerShell produced HTTP 000 / empty responses (connection reset) — server-side `json.loads()` raised on a mangled body → uncaught exception killed the request thread. Misread initially as a possible caption-endpoint regression.
- **Fix:** Verified endpoint healthy via `--data-binary @file` (HTTP 200, correct JSON). Documented the PowerShell quoting pattern for future checks. No code change (server.py untouched per phase constraints).
- **Files modified:** none
- **Commit:** none (diagnostic only)

## Verification Results

| Check | Command | Result |
|-------|---------|--------|
| Live ping | `curl http://localhost:8000/api/ping` | `{"ok": true}` |
| Live presets | `curl http://localhost:8000/api/presets` | JSON presets list (6 lighting keys) |
| Live outputs | `curl http://localhost:8000/api/outputs` | JSON date-grouped batches |
| Live balance | `curl http://localhost:8000/api/balance` | `{"balance":0.01,"per_photo":0.07}` |
| Live captions | `POST /api/captions/generate {"count":3,"platform":"tiktok","seed":1}` | HTTP 200, ok:true, 3 captions |
| Live index | `curl http://localhost:8000/` | 200, contains caption-gen-card |
| py_compile | `python -m py_compile scripts/alina_textgen.py webui/server.py` | exit 0 |
| node --check | `node --check webui/static/app.js` | exit 0 |
| CI YAML | `yaml.safe_load(.github/workflows/ci.yml)` | valid, both additions present |

## Commits

| Hash | Message |
|------|---------|
| 8ab29c5 | `ci(04-01): add scripts/alina_textgen.py to syntax and import checks` |
| 42e9f85 | `docs(04-01): update codemap and AGENTS.md` |
| (final) | `docs(04-01): complete integration polish plan (SUMMARY.md)` |

## Self-Check: PASSED

- Files exist: `.github/workflows/ci.yml` (alina_textgen.py × 2 lines), `codemap.md` (7 files), `scripts/codemap.md` (row + usage + consumed-by), `webui/codemap.md` (server.py row), `AGENTS.md` (tree + bullet + table + Recent Changes).
- Commits exist: `8ab29c5`, `42e9f85` in `git log`.
- No application code modified (server.py / index.html / app.js / style.css untouched — verified `git show --stat` per commit).
- STATE.md / ROADMAP.md untouched (orchestrator-owned).
