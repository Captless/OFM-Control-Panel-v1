# Plan: Bank Editor Modal Redesign (Option 1: Guided Editor)

## Objective
Redesign the Bank Editor modal (`#bank-editor-modal`) into a guided editor with searchable pool sidebar, inline pool purpose descriptions, custom pool badges, and visible built-in defaults. Remove the template feature. Improve discoverability of pool formats and custom vs built-in distinction.

## Project Context (Discovered)
- **Stack**: Python 3 stdlib HTTP server + Vanilla HTML/CSS/JS (no framework)
- **Structure**: `webui/static/index.html` (modal HTML), `webui/static/app.js` (modal logic), `webui/static/style.css` (modal styles)
- **Conventions**: Glassmorphism cards, CSS variables for theming, `var(--font-mono)` for technical text, pill-style buttons, fixed modals with `aria-modal="true"`
- **Active Components**:
  - Modal HTML at lines 163-206 in `index.html`
  - JS logic: `openBankEditor()`, `renderBankEditor()`, `_syncPoolUi()`, `selectBankPool()`, `addCustomPool()`, `saveBankFromModal()` in `app.js`
  - CSS at lines 2812-2982 in `style.css`
  - Pool definitions in `pipeline/prompt_bank.py` (13 OVERRIDABLE_POOLS)
  - Pool labels in `app.js:_POOL_LABELS` (13 entries)

## Phases

### Phase 1: HTML Structure & Accessibility
**Deliverable**: Modal HTML updated with search input, pool purpose area, custom pool indicator, built-in default badges. All new elements have proper ARIA.

**Tasks**:
1. **File**: `webui/static/index.html` (lines 163-206)
   **Action**: Replace modal body with new structure:
   - Add search input above pool list: `<input type="search" id="be-pool-search" placeholder="Search pools..." aria-label="Filter pools">`
   - Add pool purpose description in editor header: `<div class="be-pool-purpose" id="be-pool-purpose" aria-live="polite"></div>`
   - Add custom pool badge in pool list items: `<span class="be-pool-item-badge" aria-hidden="true"></span>`
   - Add built-in default indicator in pool list for non-overridden pools
   - Keep existing: bank name input, pool listbox, textarea, hint, actions
   **Verify**: `node --check webui/static/app.js` passes; HTML renders without console errors

2. **File**: `webui/static/index.html`
   **Action**: Add `data-purpose` attribute to each pool item in `renderBankEditor()` output for CSS tooltip
   **Verify**: Pool items render with `data-purpose="..."` attribute

---

### Phase 2: CSS Styling
**Deliverable**: New visual design implemented — search input styled, pool purpose visible, custom badges colored, built-in default badges subtle, responsive layout.

**Tasks**:
1. **File**: `webui/static/style.css` (after line 2982, before Prompt Bank Redesign section)
   **Action**: Add styles for:
   - `#be-pool-search` — full-width, mono font, accent border on focus
   - `.be-pool-purpose` — mono, fg3 color, margin-bottom 8px, min-height 1.4em
   - `.be-pool-item-badge.custom` — amber background, mono 8px, "CUSTOM" text
   - `.be-pool-item-badge.builtin` — fg3 background, mono 8px, "DEFAULT" text
   - `.be-pool-item[data-purpose]::after` — tooltip with purpose text (reuse existing pool-badge tooltip pattern)
   - Search filter: `.be-pool-item.hidden { display: none; }`
   **Verify**: Server restarted; modal opens; search input visible; custom/builtin badges render on pool items

2. **File**: `webui/static/style.css`
   **Action**: Ensure responsive: sidebar stays 220px min, editor flexes, purpose text wraps
   **Verify**: Resize window < 700px — layout stacks (existing `@media` handles)

---

### Phase 3: JavaScript Logic — Search & Pool Data
**Deliverable**: Pool search filters list in real-time; pool purpose descriptions loaded from map; custom vs built-in detection works.

**Tasks**:
1. **File**: `webui/static/app.js` (near `_POOL_LABELS`, ~line 182)
   **Action**: Add pool purpose map:
   ```javascript
   var _POOL_PURPOSES = {
     'INDOOR_SCENES': 'Indoor photo locations (bedroom, bathroom, living room)',
     'MIRROR_SCENES': 'Mirror selfie locations (bathroom mirror, wardrobe mirror)',
     'OUTDOOR_SCENES': 'Outdoor locations (alley, street, rooftop, graffiti)',
     'FRAMING': 'Camera angle & crop (tilted, off-center, motion blur)',
     'HAIR': 'Hair state (wet, messy, damp, braided, bedhead)',
     'POSES': 'Body posture (weight shift, hip tilt, hand on hip, candid)',
     'QUALITY': 'iPhone aesthetic (grain, noise, compression, raw sensor)',
     'OUTFIT_TOPS_POOLS': 'Top clothing by style (sexy, date_night, night_club, baggy, lounge_sexy)',
     'OUTFIT_BOTTOMS_POOLS': 'Bottom clothing by style (same style keys as tops)',
     'LIGHTING_POOLS': 'Lighting mood by type (warm, cool, dimlit, flash, screen, mixed)',
     'DEFAULT_NEGATIVE': 'What to avoid in handheld shots (phone, lamp, smiling, jewelry)',
     'MIRROR_NEGATIVE': 'What to avoid in mirror shots (lamp, smiling, jewelry)',
     'IDENTITY_LOCK': 'Identity consistency prompt (hair/lip color match)'
   };
   ```
   **Verify**: No syntax errors; `console.log(_POOL_PURPOSES.INDOOR_SCENES)` returns string

2. **File**: `webui/static/app.js` — `renderBankEditor()`
   **Action**: 
   - Add search input event listener: `input` → filter `#be-pool-list` children by name match (case-insensitive)
   - For each pool item, set `data-purpose` from `_POOL_PURPOSES[name]` or empty
   - Add custom/builtin badge: check if pool name in `OVERRIDABLE_POOLS` (from prompt_bank.py) and if bank is custom (not builtin) and pool not in builtin defaults → "CUSTOM", else if in builtin defaults but not overridden → "DEFAULT"
   **Verify**: Type in search → list filters; inspect pool items → have `data-purpose` and badge span

3. **File**: `webui/static/app.js` — `_syncPoolUi()`
   **Action**: Update `#be-pool-purpose` textContent from `_POOL_PURPOSES[_bankEditorPool]` or empty
   **Verify**: Click different pools → purpose text updates in editor header

---

### Phase 4: JavaScript Logic — Built-in Defaults Visibility
**Deliverable**: When editing a custom bank, built-in pools not yet overridden show as "(DEFAULT)" badges and can be added via "Override" action.

**Tasks**:
1. **File**: `webui/static/app.js` — `openBankEditor()`
   **Action**: Fetch built-in defaults via `/api/settings/banks/pools/defaults` (already done). For custom banks, compute which OVERRIDABLE_POOLS are not in `bank.pools`. Store as `_bankEditorMissingBuiltins`.
   **Verify**: `console.log(_bankEditorMissingBuiltins)` shows array of missing pool names

2. **File**: `webui/static/app.js` — `renderBankEditor()`
   **Action**: After rendering overridden pools, append "Available Built-ins" section (collapsible) listing missing pools with "Override" button each. Click → adds pool to draft with built-in value, re-renders.
   **Verify**: Custom bank with 5 pools → shows 8 available built-ins; click "Override" on FRAMING → FRAMING appears in pool list with built-in values

3. **File**: `webui/static/app.js` — `addCustomPool()`
   **Action**: Keep existing but update to use new pool type names (list/styles/text) consistently. No prompt() modal change needed per requirements.
   **Verify**: Click "+ List Pool" → prompt for name → pool added to list

---

### Phase 5: Polish & Edge Cases
**Deliverable**: Modal fully functional, accessible, no regressions.

**Tasks**:
1. **File**: `webui/static/app.js` — `saveBankFromModal()`
   **Action**: Ensure custom pools persist; built-in overrides saved; missing built-ins not saved unless overridden. No behavior change.
   **Verify**: Create bank → add custom pool → override FRAMING → save → reopen → both present

2. **File**: `webui/static/app.js` — Keyboard navigation
   **Action**: Ensure search input doesn't trap arrow keys (pool list keydown handler should only activate when list focused). Add `tabindex="0"` to search input.
   **Verify**: Tab through modal → search → pool list → textarea → actions → close button

3. **File**: `webui/static/style.css`
   **Action**: Add focus-visible styles for search input, pool items, override buttons. Ensure reduced-motion respected.
   **Verify**: Tab navigation visible; `prefers-reduced-motion` disables transitions

4. **Test**: Full regression
   - Open builtin bank → read-only, no edit actions
   - Open custom bank → edit, add, override, delete pools
   - Create new bank from default → 13 pools present
   - Save → banks list updates → active bank indicator works
   - Export/import → custom pools preserved
   **Verify**: All flows work; no console errors

---

## Risk Areas
- **Pool purpose map sync**: Must match `OVERRIDABLE_POOLS` in `pipeline/prompt_bank.py` exactly (13 keys)
- **Built-in defaults API**: `/api/settings/banks/pools/defaults` must return all 13 pools
- **Custom pool detection**: Logic must distinguish "user created this pool" vs "overrode built-in" vs "using built-in default"
- **Search performance**: Trivial (<20 items) but debounce not needed

---

## Verification Checklist
- [ ] `node --check webui/static/app.js` passes
- [ ] `python -m py_compile webui/server.py` passes
- [ ] Modal opens for builtin (read-only), custom (editable), new (editable)
- [ ] Search filters pool list in real-time
- [ ] Pool purpose shows in editor header on selection
- [ ] Custom pools show "CUSTOM" badge (amber)
- [ ] Non-overridden built-ins show "DEFAULT" badge (muted) in available section
- [ ] Override button adds built-in pool to editor
- [ ] Save preserves all pools; reload shows them
- [ ] Keyboard navigation: Tab order, Escape closes, arrows in pool list
- [ ] All 6 themes render correctly
- [ ] Mobile (< 700px) stacks correctly

---

## Strict Rules
- NEVER assume specific frameworks — vanilla JS/CSS only
- NEVER implement — only plan
- ALWAYS reference actual file paths discovered
- ALWAYS prefer minimal changes over rewrites
- NO template feature (explicitly excluded)