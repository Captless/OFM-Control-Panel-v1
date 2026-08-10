# Plan: Prompt Bank Redesign

## Objective
Redesign the Prompt Bank UI in Settings with:
1. **"Add New Bank"** → auto-clones default pools, auto-generates name (e.g., "Bank 2", "Bank 3"), opens directly in editor
2. **Prominent USE button** → clear active bank switching affordance on each tile
3. Improved tile card layout with better visual hierarchy
4. Full a11y compliance (focus-visible, keyboard nav, ARIA, reduced-motion)

---

## Project Context (Discovered)

**Stack**: Python 3 (stdlib `http.server`), Vanilla HTML/CSS/JS, WaveSpeed AI REST API
**Structure**:
- `webui/server.py` — HTTP server + REST API endpoints
- `webui/static/index.html` — Single-page app
- `webui/static/app.js` — All client logic (~2600 lines)
- `webui/static/style.css` — All styles (~3150 lines)
- `core/prompt_banks.py` — Bank storage + sanitization

**Current Active Components**:
- Bank tiles masonry (`.bank-tiles` with `column-count: 2`)
- Bank Editor Modal (`#bank-editor-modal`) — 2-col: pool sidebar + textarea
- New Bank Modal (`#new-bank-modal`) — name input + create
- Delete Bank Modal (`#delete-bank-modal`)
- USE button only appears on non-active, non-builtin tiles

**API Endpoints** (working):
- `GET /api/settings/banks` — list all banks (+ builtin pseudo-bank)
- `GET /api/settings/banks/active` — get active bank ID
- `GET /api/settings/banks/pools/defaults` — builtin pool defaults
- `POST /api/settings/banks/create` — create new bank {name, pools}
- `POST /api/settings/banks/clone` — clone existing {source_id, name}
- `POST /api/settings/banks/update` — update {id, name?, pools}
- `POST /api/settings/banks/active` — set active {id}
- `POST /api/settings/banks/delete` — delete {id}

---

## Phase 1: Core Logic — New Bank Auto-Clone + USE Button Logic

### Deliverable
- `openNewBankModalFromDefault()` replaced with immediate create+open-editor flow
- `setActiveBank()` enhanced with optimistic UI + toast feedback
- New helper: `generateNextBankName()` for auto-naming

### Tasks

1. **File**: `[webui/static/app.js]` — `openNewBankModalFromDefault` replacement
   **Action**: Replace modal flow with: fetch defaults → generate name → POST create → on success, set as active → open editor modal directly (no intermediate modal)
   **Verify**: Click "New Bank" tile → new bank created, editor opens, bank appears in list with generated name

2. **File**: `[webui/static/app.js]` — `generateNextBankName()` helper
   **Action**: Add function that scans `_savedBanks` for highest "Bank N" suffix, returns next (e.g., "Bank 2", "Bank 3")
   **Verify**: Multiple creates produce sequential unique names

3. **File**: `[webui/static/app.js]` — `setActiveBank()` enhancement
   **Action**: Add optimistic UI (immediate badge swap), better toast, ensure active state persists across reload
   **Verify**: Click USE on any tile → active badge moves immediately, toast shows, reload preserves active

---

## Phase 2: Interface Layer — Tile Card Redesign

### Deliverable
- Redesigned bank tiles with: prominent USE/active indicator, clearer actions, better visual hierarchy
- New Bank tile as primary CTA (not just "+")
- Improved spacing, typography, focus states

### Tasks

1. **File**: `[webui/static/index.html]` — Settings bank pane toolbar
   **Action**: Keep Export/Import, replace "New Bank" button with enhanced tile (handled in JS render)
   **Verify**: Toolbar clean, no duplicate New Bank

2. **File**: `[webui/static/app.js]` — `renderBankList()` complete rewrite
   **Action**: 
   - New Bank tile: large `+` button style, `aria-label="Create new bank"`, click → auto-create+edit
   - Per-bank tile: 
     - Header: name (click→edit), ACTIVE pill (green, prominent) or USE button (primary style)
     - Pool chips row
     - Footer: pool count, Edit button, Delete button
   - Builtin tile: read-only styling, no USE/Delete
   **Verify**: All tiles render correctly, active state clear, USE button visible on inactive

3. **File**: `[webui/static/style.css]` — Tile card styles rewrite
   **Action**: 
   - `.bank-tile` — card with clear active state (accent border + bg)
   - `.bank-tile-new` — large CTA button appearance
   - `.bt-use-btn` — primary button style for inactive banks
   - `.bt-active-pill` — green pill replacing badge
   - Focus-visible on all interactive elements
   - Touch-action manipulation
   **Verify**: Visual match design, focus rings visible, hover/tap states work

---

## Phase 3: Bank Editor Modal — Polish

### Deliverable
- Editor modal works seamlessly with new auto-create flow
- Pool listbox keyboard nav preserved
- Save/Create/Delete button loading states

### Tasks

1. **File**: `[webui/static/app.js]` — `openBankEditor()` integration
   **Action**: Ensure auto-created bank opens editor immediately after create (already in Phase 1)
   **Verify**: New bank → editor opens with defaults loaded

2. **File**: `[webui/static/app.js]` — Button loading states
   **Action**: Confirm `saveBankFromModal`, `submitNewBank`, `executeDeleteBank` show "Saving…"/"Creating…"/"Deleting…" with disabled state
   **Verify**: Buttons show loading text during API calls

---

## Phase 4: A11y & Polish

### Deliverable
- Full keyboard navigation (tiles, pool listbox, modals)
- ARIA labels/roles on all interactive elements
- Focus-visible outlines
- Reduced-motion support
- No div-onclick (semantic buttons)
- Overscroll-behavior contain in modals

### Tasks

1. **File**: `[webui/static/index.html]` — ARIA on new elements
   **Action**: 
   - New Bank tile: `<button>` with `aria-label`
   - USE button: `aria-pressed` when active
   - Bank tiles: `role="listitem"` in `role="list"` container
   **Verify**: Screen reader announces correctly

2. **File**: `[webui/static/app.js]` — Keyboard nav on bank tiles
   **Action**: Add keydown handler on `#settings-bank-list` for ArrowLeft/Right/Up/Down between tiles, Enter/Space to activate
   **Verify**: Tab to list, arrow keys navigate, Enter opens editor

3. **File**: `[webui/static/style.css]` — A11y CSS
   **Action**: 
   - `.visually-hidden` utility (already exists)
   - `focus-visible` on `.bank-tile`, `.bt-use-btn`, `.bt-name`, `.bt-del`
   - `@media (prefers-reduced-motion)` disable transforms/transitions
   - `overscroll-behavior: contain` on modal content
   **Verify**: Tab navigation clear, no motion when reduced-motion enabled

4. **File**: `[webui/static/app.js]` — Simplify: Remove redundant ESC handler block
   **Action**: Delete duplicate ESC/outside-click handler (lines ~731-753) — primary handler at ~553 covers all modals
   **Verify**: ESC closes modals, no duplicate handlers

---

## Risk Areas

- **Auto-create name collision**: `generateNextBankName()` must handle gaps (deleted banks)
- **Active bank persistence**: Server stores active in `settings.json` — verify reload works
- **Builtin pseudo-bank**: Not creatable/deletable, no USE button — special case in render
- **Stale HTML cache**: `server.py` now reads index.html per-request (fixed in prior work) — no restart needed for JS/CSS

---

## Verification Checklist

- [ ] `node --check webui/static/app.js` — clean
- [ ] `python -m py_compile webui/server.py core/prompt_banks.py` — clean
- [ ] HTMLParser — 0 errors, 0 unclosed tags
- [ ] Server starts, `/api/ping` → 200
- [ ] Served `/` contains: `bank-editor-modal`, `bank-tiles`, NO `pool-editor-wrapper`
- [ ] Click "New Bank" tile → creates "Bank N", opens editor, shows in list
- [ ] Click USE on inactive tile → becomes active, badge moves, toast
- [ ] Click active tile's name → opens editor
- [ ] Double-click name → inline rename, Enter saves
- [ ] Tab navigation: tiles → pool listbox → modal controls
- [ ] ESC closes modals, outside-click closes modals
- [ ] `prefers-reduced-motion` disables tile hover lift
- [ ] Round-trip: create → edit pools → save → set active → delete → list updates

---

## Implementation Notes (Simplify Principles)

- **Reuse existing patterns**: `api()` helper, `showSuccess/error`, `esc()` for HTML escaping
- **Minimal new code**: `generateNextBankName()` ~10 lines, tile render ~50 lines
- **Delete dead code**: Remove old `openNewBankModalFromDefault` modal flow, duplicate ESC handler
- **Preserve behavior**: Builtin bank read-only, custom pools persist, sanitization unchanged
- **Explicit over clever**: Clear function names, inline comments for complex logic