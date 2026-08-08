---
phase: 03-caption-generator-ui
plan: 01
subsystem: ui
tags: [vanilla-js, caption-generator, html, css, wavespeed]

# Dependency graph
requires:
  - phase: 02-caption-generator-api
    provides: POST /api/captions/generate endpoint (count, platform, hook_types, seed)
provides:
  - Caption Generator card in web UI consuming Phase 2 API contract
  - getSelectedCapPlatform/getSelectedCapHook/generateCaptions/renderCaptions/copyCaption/copyAllCaptions/clearCaptions JS handlers
  - .caption-gen-card/.caption-item/.cap-badge/.cap-actions theme-var CSS
affects: [caption-generator-verify, phase 4 milestone]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 2096   # chars/4 over realized diff (8384 chars, 18d2a12..HEAD webui/static/*)
  tasks: 4
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns: [pill radio pattern, photo-slider count, .btn .btn-text button-label, api()/showToast()/esc() helpers]

key-files:
  created: []
  modified:
    - webui/static/index.html
    - webui/static/app.js
    - webui/static/style.css

key-decisions:
  - "Caption card placed outside .gen-layout as full-width sibling so setControlsLocked / syncPanelHeights remain untouched"
  - "Generated markup uses esc() on every dynamic field (text, platform, hook_type, cta, hashtags) — no raw innerHTML of API strings"
  - "Hook type 'mixed' omits hook_types from request body per Phase 2 contract; all others send hook_types=[hook]"

patterns-established:
  - "Pattern: caption list items mirror .prompt-item pattern (badge head row + raw text block + meta + action)"
  - "Pattern: copy-by-index via module-level _captions array + inline onclick='copyCaption(N)'"

requirements-completed: [R1]

# Coverage metadata (#1602) — one entry per shipped deliverable.
coverage:
  - id: D1
    description: Caption Generator card renders with platform pills, hook-type pills, count slider, Generate Captions button, caption list, hidden Copy All/Clear actions
    requirement: R1
    verification:
      - kind: other
        ref: "grep caption-gen-card / btn-caption / 5x cap_platform / 6x cap_hook in webui/static/index.html; GET / returns 200 containing caption-gen-card + btn-caption"
        status: pass
    human_judgment: false
  - id: D2
    description: generateCaptions POSTs to /api/captions/generate and renders returned captions with per-caption copy, copy-all, and clear
    requirement: R1
    verification:
      - kind: integration
        ref: "POST /api/captions/generate {count:3,platform:tiktok,hook_types:[vulnerable],seed:1} -> ok:true, 3 captions; node --check webui/static/app.js clean"
        status: pass
    human_judgment: false
  - id: D3
    description: Copy/copy-all writes to clipboard and shows a toast
    verification:
      - kind: other
        ref: "navigator.clipboard.writeText in copyCaption + copyAllCaptions with showSuccess toasts (code inspection)"
        status: pass
    human_judgment: false

# Metrics
duration: 14min
completed: 2026-08-08
status: complete
---

# Phase 3 Plan 1: Caption Generator UI Card Summary

**Caption Generator card in the OFM SPA — platform/hook pills + count slider + Generate Captions button, consuming the Phase 2 `/api/captions/generate` endpoint, with per-caption copy, Copy All, and Clear, all XSS-safe via esc()**

## Performance

- **Duration:** 14 min
- **Started:** 2026-08-08T00:00:00Z
- **Completed:** 2026-08-08T00:14:00Z
- **Tasks:** 4 (3 file tasks + 1 verification task)
- **Files modified:** 3

## Accomplishments
- New `div.card.caption-gen-card` inserted between `.gen-layout` and the Outputs header — full-width sibling, so `setControlsLocked` (targets `.gen-layout .card.controls-locked`) and equal-height `syncPanelHeights` are completely unaffected
- 5 platform pills (tiktok/reels/shorts/x/stories) + 6 hook pills (vulnerable/confident/playful/aesthetic/relatable/mixed) using the existing `.vibe-pills`/`.pill` radio pattern with `pill:has(input:checked)` CSS (no JS highlight needed)
- Count slider 1-20 (`#cap-count` + live `#cap-count-label`), `#btn-caption` Generate Captions button following the `.btn` + `.btn-text` span pattern
- 7 JS functions added in the Photo Generation Controls section: `getSelectedCapPlatform`, `getSelectedCapHook`, `generateCaptions`, `renderCaptions`, `copyCaption`, `copyAllCaptions`, `clearCaptions` — all using existing `api()`/`showToast()`/`showError()`/`showSuccess()`/`esc()` helpers
- 9 CSS rules appended (`.caption-gen-card`, `.caption-list`, `.caption-item`, `.caption-item-head`, `.cap-badge`, `.caption-text-raw`, `.caption-meta`, `.cap-actions`, `.caption-empty`) + 768px responsive wrap, all theme-var based
- Live verified against :8000: endpoint returns `ok:true` with 3 captions for the exact plan test payload; all three static assets serve 200 with the new content

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Caption Generator card HTML** - `592b9dd` (feat)
2. **Task 2: JS generator handlers** - `2e1a012` (feat)
3. **Task 3: CSS for caption card** - `40fa233` (feat)

**Plan metadata:** no docs commit — orchestrator handles `.planning/` tracking (Task 4 was verification-only, no files changed)

## Files Created/Modified
- `webui/static/index.html` - Caption Generator card markup (platform pills, hook pills, count slider, Generate Captions button, `#caption-list`, hidden Copy All + Clear buttons)
- `webui/static/app.js` - Caption Generator Controls section: radio readers, generate/render/copy/clear handlers, `_captions` module var
- `webui/static/style.css` - Caption Generator section: card, list, item, badge, raw text, meta, actions, empty-state, responsive block

## Decisions Made
- Card placed **outside** `.gen-layout` as a full-width sibling — keeps `setControlsLocked` (`.gen-layout .card.controls-locked`) and `syncPanelHeights` untouched, per plan constraint
- Every dynamic value esc()'d in `renderCaptions` (text, platform, hook_type, cta, hashtags) — satisfies Phase 1 security review requirement, no raw innerHTML of API strings
- `hook_types` omitted from request body when hook === 'mixed'; otherwise `hook_types: [hook]` — matches verified Phase 2 contract
- Button text swap handled inline (`btn.querySelector('.btn-text').textContent`) rather than reusing `_btnTxt()` — `_btnTxt` is hardcoded to `#btn-photo .btn-text`
- Per-item Copy button uses inline `onclick="copyCaption(N)"` with index into `_captions` — mirrors existing inline-onclick style (`startPromptGeneration()`, `copyAllCaptions()`, `clearCaptions()`)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- **Stale homepage served after edits:** server.py loads `HOMEPAGE_HTML = _load_homepage()` at module import (line 973), so `/` served the pre-edit index.html even though app.js/style.css (read from disk per request) were fresh. Resolved by restarting the server (killed PID 16492, started `python webui/server.py` background) — an operational step the plan's Task 4 explicitly anticipates ("restart if dead"). No code changes needed; server.py untouched (py_compile clean confirms).

## Verification Results (Task 4)

| Check | Result |
|-------|--------|
| `node --check webui/static/app.js` | PASS (exit 0) |
| `python -m py_compile webui/server.py` | PASS (exit 0, no server change) |
| POST `/api/captions/generate` `{count:3,platform:tiktok,hook_types:[vulnerable],seed:1}` | PASS — `ok:true`, 3 captions with text/cta/hashtags |
| GET `/` | PASS — 200, contains `caption-gen-card` + `btn-caption` |
| GET `/static/app.js` | PASS — 200, contains `generateCaptions` |
| GET `/static/style.css` | PASS — 200, contains `.caption-gen-card` |
| Undefined-helper smoke (all called fns defined: api, showToast, showError, showSuccess, esc, 7 new fns) | PASS |
| Card between gen-layout and Outputs header | PASS (index.html line 345-381) |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Caption Generator card fully functional against the live Phase 2 endpoint; ready for UI verification / UAT
- Server on :8000 restarted and serving the new card — no further manual action needed
- No blockers

---
*Phase: 03-caption-generator-ui*
*Completed: 2026-08-08*

## Self-Check: PASSED
- Files exist: `webui/static/index.html` (FOUND, card at line 347), `webui/static/app.js` (FOUND, 7 fns at 837-922), `webui/static/style.css` (FOUND, section at 2792)
- Commits exist: `592b9dd`, `2e1a012`, `40fa233` (all in `git log`)
- All 5 live HTTP checks + endpoint POST pass (table above)
