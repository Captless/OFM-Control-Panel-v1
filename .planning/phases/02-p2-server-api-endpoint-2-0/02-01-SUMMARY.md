---
phase: 02-server-api-endpoint
plan: 01
subsystem: api
tags: [captions, server, endpoint, post, validation, alina-textgen]

# Dependency graph
requires:
  - phase: 01-alina-caption-generator
    provides: scripts/alina_textgen.py batch_generate + PLATFORM_CONFIG
provides:
  - POST /api/captions/generate endpoint on webui/server.py (count/platform/hook_types/seed params)
  - Validated request handling (400s) + ValueError/Exception error mapping
  - Import path wiring: server -> scripts/alina_textgen (SCRIPTS_DIR sys.path insert)
affects: [web-ui, phase-3-captions-ui-card]

# Actuals (#2632)
actuals:
  tokens: 620       # (421 + 2056 diff chars) / 4 over webui/server.py (only file changed)
  tasks: 3
  commits: 2        # Task 3 was live-test only, no file changes -> no commit

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SCRIPTS_DIR sys.path.insert pattern mirroring existing API_DIR/PIPELINE_DIR blocks
    - early-return 400 validation branch in do_POST before identity handler
    - batch_generate wrapped ValueError -> 400, generic Exception -> 500

key-files:
  created: []
  modified:
    - webui/server.py

key-decisions:
  - "Bool values rejected as count/seed (isinstance bool guard) — JSON true would otherwise coerce to 1 via int subclass"
  - "count clamped 1-20 after int validation; defaults count=10, platform=tiktok per plan spec"
  - "Task 3 produced no commit: live-test-only task with zero file changes (server.py fully covered by Tasks 1-2)"

patterns-established:
  - "Endpoint handlers follow existing do_POST branch style: read body, validate with early return 400, respond via self._json"
  - "Cross-directory imports in server.py always paired with explicit sys.path.insert above the import"

requirements-completed: [R1]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "webui/server.py imports batch_generate + PLATFORM_CONFIG from scripts/alina_textgen via SCRIPTS_DIR sys.path insert — server module imports cleanly with no side effects"
    requirement: R1
    verification:
      - kind: other
        ref: "python -c \"import sys; sys.path.insert(0,'.'); sys.path.insert(0,'webui'); import server\" — exit 0, no output"
        status: pass
    human_judgment: false
  - id: D2
    description: "POST /api/captions/generate handler — reads count (int, clamp 1-20), platform (must be in PLATFORM_CONFIG), hook_types (list or None), seed (int or None); non-int count / unknown platform / bad hook_types / bad seed return 400"
    requirement: R1
    verification:
      - kind: other
        ref: "python -m py_compile webui/server.py — exit 0; grep acceptance: '\"/api/captions/generate\"' + validation branches present"
        status: pass
    human_judgment: false
  - id: D3
    description: "Live endpoint behavior — happy path 3 captions with all 5 contract keys, {} defaults to 10 tiktok captions, {\"count\":\"abc\"} -> 400, {\"platform\":\"nope\"} -> 400; server terminates after test and is restarted to restore prior running-server state"
    requirement: R1
    verification:
      - kind: other
        ref: "Invoke-RestMethod / Invoke-WebRequest POST http://localhost:8000/api/captions/generate — T1 ok=True count=3 keys=text,platform,hook_type,cta,hashtags; T2 ok=True count=10 platform=tiktok; T3 status=400 'count must be an integer'; T4 status=400 'unknown platform'"
        status: pass
    human_judgment: false

# Metrics
duration: 9min
completed: 2026-08-08
status: complete
---

# Phase 2 Plan 1: Server API Endpoint Summary

**POST /api/captions/generate wired into webui/server.py — imports batch_generate + PLATFORM_CONFIG from scripts/alina_textgen.py via a SCRIPTS_DIR sys.path insert, validates count/platform/hook_types/seed (400 on bad input), clamps count 1-20, maps ValueError→400 / Exception→500, and passes live tests for happy path, defaults, and both 400 cases**

## Performance

- **Duration:** 9 min
- **Started:** 2026-08-08T11:25:00Z
- **Completed:** 2026-08-08T11:34:03Z
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments
- `webui/server.py` imports `batch_generate, PLATFORM_CONFIG` from `scripts/alina_textgen.py` (SCRIPTS_DIR sys.path.insert after API_DIR block, mirroring existing pattern)
- New `POST /api/captions/generate` branch at top of `do_POST` (before identity handler): count defaults 10, must be int (bool rejected), clamped 1-20; platform defaults tiktok, must exist in PLATFORM_CONFIG; hook_types must be list or None; seed must be int or None
- Error mapping: `ValueError` (dedup cap exhaustion, empty platforms) → 400 with message; any other `Exception` → 500 with message; validation failures → 400 early-return
- Live-verified all 4 plan cases: `{"count":3,"platform":"tiktok"}` → 200 with 3 captions each carrying the 5 contract keys (text/platform/hook_type/cta/hashtags); `{}` → 200 with 10 tiktok captions; `{"count":"abc"}` → 400 "count must be an integer"; `{"platform":"nope"}` → 400 "unknown platform"

## Task Commits

Each task was committed atomically:

1. **Task 1: Import batch_generate from scripts** - `989c587` (feat)
2. **Task 2: Add POST /api/captions/generate handler** - `19c2f5b` (feat)
3. **Task 3: Live-test endpoint** - no commit (test-only, zero file changes)

**Plan metadata:** `02-01-SUMMARY.md` (docs: complete plan)

## Files Created/Modified
- `webui/server.py` - SCRIPTS_DIR import block + PLATFORM_CONFIG import (4 lines); `/api/captions/generate` POST handler with validation + error mapping (32 lines added)

## Decisions Made
- **Bool rejected as count/seed:** `isinstance(count, bool)` guard added — JSON `true` is an int subclass in Python and would otherwise silently coerce to count=1 / seed=True. Cheap correctness win, aligned with plan's "reject non-int" intent.
- **Count clamp 1-20** applied exactly as plan spec'd (validate first, then clamp) — validation errors 400 before clamping.
- **Task 3 uncommitted:** live-test task produced no diff; server.py changes lived entirely in Tasks 1-2. No empty commit created.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- **Port 8000 occupied by stale server:** PID 13176 was a pre-existing `python server.py` instance running code from before this plan (no captions handler). Killed it to load new code, tested, then restarted a fresh background server (PID 16492) so the user's prior running-server state on :8000 is preserved with the updated handler.
- **First start attempt failed:** `Start-Process python -ArgumentList "server.py"` from repo root — file lives at `webui/server.py` post-reorg, so the process exited immediately (file not found). Re-ran with `webui/server.py`; server bound :8000 correctly.
- **PowerShell 5.1 lacks `-SkipHttpErrorCheck`** on Invoke-WebRequest — used try/catch reading `$_.Exception.Response` stream to assert 400 status + body.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `POST /api/captions/generate` live and verified — Phase 3 (web UI caption card) can consume it directly
- API contract confirmed on the wire: `{ok:true, captions:[{text, platform, hook_type, cta, hashtags}]}`; errors `{ok:false, error}` with 400/500
- Server on :8000 running with the new handler

---
*Phase: 02-server-api-endpoint*
*Completed: 2026-08-08*

## Self-Check: PASSED
