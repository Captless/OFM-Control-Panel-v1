# OFM — Alina Sky Image & Video Generator

Personal pipeline for generating alt-girl aesthetic photos and TikTok videos via WaveSpeed AI. Web UI control panel at `http://localhost:8000`.

## Tech Stack

| Layer | Stack |
|-------|-------|
| Backend | Python 3, `http.server` (stdlib), `ThreadingHTTPServer` |
| Frontend | Vanilla HTML/CSS/JS, no framework, single-page app |
| AI API | WaveSpeed AI REST API (`nano-banana-2/edit` for images, `kling-v2.5-turbo-std` for video) |
| Output | PNG images (1K), MP4 videos (9:16) in `outputs/YYYY-MM-DD/` |

## File Structure

```
OFM/
├── AGENTS.md                          ★ THIS FILE (agents auto-load)
├── codemap.md                         ★ Repository atlas (read first!)
├── .gitignore
├── .github/workflows/ci.yml           Syntax + import checks on GitHub
├── UNUSED FILES/                      Git-ignored archive of retired assets (README.md)
├── core/                              Shared config, errors, day-path, text
│   ├── config.py                      API keys, avatar URL, PHOTO_PRICE, settings
│   ├── errors.py                      WaveSpeedError exception
│   ├── daybatch.py                    day_path() → outputs/YYYY-MM-DD/<subdir>
│   └── text_generator.py              Alt-girl text prompts
├── api/                               Reusable WaveSpeed REST client
│   └── wavespeed_client.py            WaveSpeed REST client (generate, enhance, batch)
├── webui/                             Web control panel
│   ├── server.py                      HTTP server (port 8000) + REST API
│   ├── dashboard.py                   Dashboard page generator
│   ├── wavespeed_tiktok_client.py     TikTok video pipeline client
│   ├── activity.json                  Run history log
│   ├── static/                        Frontend (index.html, style.css, js/)
│   └── fonts/                          TikTok Sans (gitignored binaries)
├── pipeline/                          Photo + video generation pipeline
│   ├── pipeline.py                    Photo generation entry point
│   ├── prompt_bank.py                 Prompt templates, job builder (v5)
│   └── alina_video_guide.md           Video prompt style guide
├── scripts/                           Utility entry points
│   ├── alina_textgen.py               Caption generator CLI (identity-locked pools)
│   ├── run_tiktok.py                  Batch TikTok generation CLI
│   ├── open_server.py                 Server launcher
│   └── open_dashboard.py              Dashboard viewer
├── docs/                              Style guides + identity reference
│   ├── alina_style_guide.md           Photo prompt style guide (Alina)
│   ├── wavespeed_identity_alina.md    Identity file (name, avatar URL, API key)
│   └── changelog.md                   Full change history (moved from AGENTS.md)
└── outputs/                           Generated media in YYYY-MM-DD/photos/ or /videos/
```

## Active Components (built & working)

### Web UI (`webui/static/`)
- **Modular JS**: frontend split into 10 module files in `static/js/` — `core.js`, `theme.js`, `layout.js`, `settings.js`, `promptBanks.js`, `captions.js`, `generation.js`, `outputs.js`, `apiProviders.js`, `init.js` (loaded in order via 10 script tags; `init.js` owns the single `DOMContentLoaded` entry point)
- **Top nav pill**: `position: fixed; top: 24px`, glassmorphism. Contains: brand "OFM", balance pill, Live indicator, **API nav trigger** (dot · user · balance · caret ▽), settings gear, dark mode toggle
- **API nav trigger**: Click toggles centered modal popup showing all WaveSpeed accounts with balances, editable names, status indicators, and Add New Provider button. ESC, outside-click, re-click closes. No page layout shift.
- **API status checking**: `checkApiStatus()` polls `/api/settings/key/status` every 30s with 10s AbortController timeout. AbortError → invalid dot + auto-retry.
- **Settings drawer**: Right-slide panel for API key management (add/remove/rename accounts, set active)
- **Generation panel**: Vibe/Camera/Lighting/Outfit/Time/Count controls, Generate button
- **Outputs table**: Grouped by date, hover preview, fullscreen, caption edit, download, delete
- **Balance display**: Per-account and total balance, auto-refresh every 60s
- **Caption Generator**: Card with platform pills (tiktok/reels/shorts/x/stories) + hook-type pills + count; `generateCaptions()`/`renderCaptions()`/`copyCaption()`/`copyAllCaptions()`/`clearCaptions()`; backed by `POST /api/captions/generate` → `scripts/alina_textgen.py` (identity-locked pools)

### API Endpoints (`webui/server.py`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serve static/index.html |
| GET | `/static/*` | Serve static assets (CSS, JS, images) |
| POST | `/api/prompts/generate` | Build prompt JSON from UI selections |
| POST | `/api/run/photo` | Start pipeline subprocess |
| GET | `/api/progress?run_id=` | Poll pipeline subprocess state |
| GET | `/api/balance` | Current active account balance |
| GET | `/api/balance/account?account=` | Per-label account balance |
| GET | `/api/balance/total` | Sum across all accounts |
| GET | `/api/outputs` | List media in outputs directory |
| POST | `/api/caption/edit` | Edit caption text file |
| POST | `/api/captions/generate` | Generate N captions (count 1-20, platform, hook_types, seed) |
| POST | `/api/media/delete` | Delete media + companion txt |
| GET/POST | `/api/settings/wavespeed/*` | CRUD for API key accounts |
| GET | `/api/settings/key/status` | Account list + active account |

### Photo Pipeline (`pipeline/pipeline.py`)

1. `pipeline.py --prompts <json>` loads jobs from JSON
2. Each job has a `"prompt"` string and `"filename"` (e.g., `001_a3f8b2.png`)
3. Calls `mode_photo(jobs)` → WaveSpeed client: submit → poll → download
4. Optional enhance pass with `wavespeed-ai/image-enhancer`
5. Saves to `outputs/YYYY-MM-DD/photos/`
6. Writes `meta.json` with labels per stem

### Prompt Bank (`pipeline/prompt_bank.py`)

- `build_jobs_multi(count, vibe, camera_style, lighting, time_of_day, outfit_style)`
- Randomized: scenes, framing, hair, tops, bottoms, poses, lighting, quality
- Camera modes: handheld selfie OR mirror selfie (with phone token)
- Elements: `{index:03d}_{time-based-md5-6chars}.png` — timestamp hash prevents same-day collisions

### WaveSpeed Client (`api/wavespeed_client.py`)

- `generate(prompt, image_url, resolution, format, aspect_ratio)` — submit + poll
- `enhance(image_url, scale, format)` — upscale 4x
- `batch_generate(jobs, ...)` — concurrent with checkpoint/resume + file lock
- API: `https://api-ondemand.wavespeed.ai/api/v3`

## Design Conventions

- **Glassmorphism**: `background: var(--glass)`, `backdrop-filter: blur(20px)`, `border: 1px solid var(--glass-border)`
- **Dark mode**: CSS variables in `:root`, light overrides in `body.light`
- **Pill-style nav**: `border-radius: 9999px`, `position: fixed; top: 24px`
- **No framework**: Zero build step, zero npm, zero CDN. Pure vanilla.

## Known Fixes (2026-07-29)

1. **Photo generation fix**: `server.py` _start_pipeline no longer passes `mode` arg (pipeline.py only accepts `--prompts`)
2. **Unique filenames**: `prompt_bank.py` hash uses `time.time()` — no same-day overwrites
3. **Nav integration**: API trigger moved into nav pill, glass dropdown replaces fixed tab, Checking fix (30s interval + timeout)

## Repository Map

A full codemap is available at `codemap.md` in the project root.

Before working on any task, read `codemap.md` to understand:
- Project architecture and entry points
- Directory responsibilities and design patterns
- Data flow and integration points between modules

For deep work on a specific folder, also read that folder's `codemap.md` (e.g. `webui/codemap.md`).

## Paths

| Key | Value |
|-----|-------|
| Server root | `webui/server.py` |
| Server port | `8000` |
| Photo pipeline | `pipeline/pipeline.py` |
| Prompt bank | `pipeline/prompt_bank.py` |
| Outputs root | `outputs/` (YYYY-MM-DD/photos/) |
| Settings | `core/settings.json` |
| Static UI | `webui/static/index.html` |
| Utility scripts | `scripts/` |

## Session Discipline

Auto-loaded protocol: `/docs/session-protocol.md`

**Rule:** After each implementation + verification milestone, the agent prompts:
> "Update AGENTS.md with these changes?"

If yes → append a dated entry to `## Recent Changes` below.
If no → skip.

This keeps AGENTS.md in sync with reality without re-running `/init-deep`.

---

## Recent Changes

### 2026-08-11 — Handheld poses + fixed framing + outfit category dropdowns

**HANDHELD_POSES pool** ✓ — `pipeline/prompt_bank.py` new `HANDHELD_POSES` list (10 detailed candid-handheld pose strings: chin tuck, mid-step, head cant, clavicle angle, etc.; no phone/scene/lighting/expression words). `build_jobs_multi` now picks `HANDHELD_POSES` for handheld camera mode, keeps `POSES` for mirror. Added to `OVERRIDABLE_POOLS` + `get_builtin_pools` (14 pools now). `core/prompt_banks.py` OVERRIDABLE_POOLS updated. `webui/static/js/promptBanks.js`: label "Handheld Poses" + purpose in `_POOL_LABELS`/`_OVERRIDABLE_POOLS`/`_POOL_PURPOSES`.

**FRAMING fixed** ✓ — `FRAMING` pool collapsed from 6 varied items to single consistent `"mid-shot crop, waist-up framing"` (every prompt identical mid-shot crop).

**Outfit category dropdowns** ✓ — 5 style keys (`sexy`/`date_night`/`night_club`/`baggy`/`lounge_sexy`) replaced with category→list dicts: `OUTFIT_TOPS_POOLS` = tank/tube/oversize_tee/bralette/bodysuit/cardigan/hoodie/blazer (10 detailed alt/goth items each), `OUTFIT_BOTTOMS_POOLS` = miniskirt/cargo_pants/sweatpants/pajama_shorts/leggings/denim_shorts/midi_skirt/biker_shorts (10 each; pajama_shorts = cute light colors, hello-kitty/sanrio style). `build_jobs_multi` signature changed `outfit_style=` → `top_category=`/`bottom_category=` (unknown category → flatten all). `list_presets` returns `top_categories`/`bottom_categories` (was `outfit_styles`). UI: 5 outfit radio pills → two `<select id="outfit-top">`/`<select id="outfit-bottom">` in `webui/static/index.html`; new `.outfit-select` CSS (mono font, accent focus, `.controls-locked` disabled). `webui/static/js/generation.js`: `getSelectedTopCategory()`/`getSelectedBottomCategory()` replace `getSelectedOutfitStyle()`; `_currentPreviewStateKey()` + API payload send `top_category`/`bottom_category`. `webui/server.py` `/api/prompts/generate`: reads `top_category` (default `tank`)/`bottom_category` (default `miniskirt`); promptbank filename stem + activity log include top/bottom. `promptBanks.js` `_POOL_PURPOSES` text updated.

**verified** ✓ — `py_compile` + `node --check` clean; 8×8 all-category build test + unknown-category fallback OK; server restarted (was PID 1800, stale cached module); live POST handheld (hoodie+pajama_shorts → "black tech windbreaker vest…" + "cream silk shorts…") + mirror (tube+cargo_pants) return new pools; served HTML has both selects, no `name="outfit_style"` radios.


### 2026-08-11 — Project restructure

**app.js split** ✓ — `webui/static/app.js` (2713 lines, flat globals) deleted; replaced by 10 module files in `webui/static/js/`: `core.js` (window.onerror/unhandledrejection, `setLive()`, `api()`, toast system `showToast`/`showError`/`showSuccess`/`showInfo`/`showWarning`/`_getToastContainer`/`_toastContainer`, `esc()`), `theme.js` (`_themes`, `setTheme`/`initTheme`/`toggleThemeModal`/`closeThemeModal`/`loadThemeList`/`selectTheme`/`handleThemeKeydown`, `motionQuery`/reduced-motion), `layout.js` (`_sidebarCollapsed`/`_activeSection`, `loadSidebarState`/`saveSidebarState`/`toggleSidebar`/`expandSidebar`/`closeFloaterMenu`/`showSection`/`loadSettingsUI`/`syncPanelHeights`/`_heightSyncTimer`), `settings.js` (`_pendingAvatarUrl`, `_setSettingsStatus`, `loadSettings`/`loadAvatarUrl`/`handleAvatarFile`/`saveIdentity` + avatar upload-zone DOMContentLoaded listeners), `promptBanks.js` (all bank state `_activeBankId`/`_savedBanks`/`_pendingDeleteId`/`_POOL_LABELS`/`_OVERRIDABLE_POOLS`/`_POOL_PURPOSES`/`_bankEditor*`, pool helpers, `renderBankList`, bank editor modal, new-bank clone, delete, `exportBanks`/`importBanks`), `captions.js` (`_captions`, `getSelectedCapPlatform`/`Hook`, `generateCaptions`/`renderCaptions`/`copyCaption`/`copyAllCaptions`/`clearCaptions`), `generation.js` (radio getters vibe/camera/lighting/time/outfit, `onVibeChange`/`onCameraChange`, `_balance`/`_perPhoto`/`_pendingJobs`, `fetchBalance`/`refreshBalance`/`updateCost`, `_btnTxt`/`_statusBadge`/`_renderGenStatus`/`_startGenAnim`/`_resetBtn`, `setControlsLocked`, `_previewDebounce`/`_genAnimTimer`/`_previewFetching`, `fetchPromptPreview`), `outputs.js` (`_outputsData`/`_preview`/`_viewMode`/`_showAll`, batch/item `editCaption`/`closeEdit`/`saveEdit`, `showPrompt`/`closePrompt`/`copyPrompt`, `closeFS`), `apiProviders.js` (`_selectedAccount`/`_lastIdentity`/`_lastApiCount`, validation/account API toggle/load), `init.js` (single DOMContentLoaded: `setLive`/`fetchBalance`/`refreshOutputs`/`syncViewToggle`/`checkApiStatus`/`preloadAccounts`/`preloadValidation`/`loadActiveBank`, 30s/60s intervals).

**index.html script tags** ✓ — single monolithic app.js tag replaced with 10 one-line `<script src="/static/js/{core,theme,layout,settings,promptBanks,captions,generation,outputs,apiProviders,init}.js">` tags in load order; `init.js` last.

**scratch/debug cleanup** ✓ — deleted root `_check.py`, `_swap.py`, `test_output2.html`, `_settings_debug.txt`; root + `webui/_srv.log`/`_srv_err.log`; all `__pycache__/`; `pipeline/promptbank_*.json`/`edited_prompts_*.json`; `outputs/*/checkpoint_*.json`.

**UNUSED FILES/ archive** ✓ — `UNUSED FILES/` is the git-ignored archive root with README.md; moved in: `.claude/skills/`, `.playwright-mcp/`, `.slim/`, `hot-take-influencer/`, `PLAN_bank_editor_redesign.md`, `PROMPT_BANK_REDESIGN_PLAN.md`, `scripts/backfill_prompts.py`, `scripts/save_meta.py`, `scripts/update_config.py`, `pipeline/wavespeed_i2v_client.py`, `webui/static/sidebar.md`.

**server.py cleanup** ✓ — `webui/server.py`: removed duplicate `export_banks, import_banks` in the line-34 import; removed unused `build_jobs` prompt_bank import (now `list_presets, build_jobs_multi, get_builtin_pools`); removed dead `_run_dashboard()`; removed duplicate unreachable `/api/settings/banks/export` GET + `/api/settings/banks/import` POST blocks; simplified `_start_pipeline(prompts)` (dropped unused `mode` param + dead `with_text` branch); caller updated to `_start_pipeline(prompts)`.

**ci.yml updated** ✓ — syntax-check no longer py_compiles retired files (`scripts/backfill_prompts.py`, `save_meta.py`, `update_config.py`, `pipeline/wavespeed_i2v_client.py`, `hot-take-influencer/scripts/wavespeed_client.py`); frontend-lint now checks `test -d webui/static/js` and `for f in webui/static/js/*.js; do node --check "$f"; done`.

**docs synced** ✓ — `codemap.md`/`webui/codemap.md`/`AGENTS.md` updated (structure, modular JS, removed retired paths); `docs/changelog.md` gets this entry.

**verified** ✓ — `python -m py_compile webui/server.py` clean.

### 2026-08-10 — Bank editor modal redesign: guided editor (search + purposes + built-in overrides)

**search** ✓ — `webui/static/index.html` `#be-pool-search` input above `#be-pool-list` in modal sidebar; `app.js` DOMContentLoaded listener filters `.be-pool-item` by `data-name` (case-insensitive, reuses `.hidden` helper); pool-list keyboard nav skips hidden items. Search value reset on `openBankEditor()`/`openNewBankFromDefault()`.

**pool purposes** ✓ — `app.js` `_POOL_PURPOSES` map (13 keys, plain-English purpose per built-in pool) + `_OVERRIDABLE_POOLS` array (13 names). New `#be-pool-purpose` line under `#be-pool-head` (set in `_syncPoolUi()`, `aria-live="polite"`); pool items carry `title` tooltip with purpose.

**custom vs builtin badges** ✓ — pool list items get amber `custom` badge (`_OVERRIDABLE_POOLS.indexOf(name)===-1` && !readOnly). **Available built-ins** section in sidebar for custom banks: lists the 13 `_OVERRIDABLE_POOLS` not yet overridden, each with an Override button → `addBuiltinPool(name)` pulls the built-in value from `_bankEditorDefaults` (now fetched once and stored in both `openBankEditor` + `openNewBankFromDefault`), re-renders.

**CSS** ✓ — `style.css` new block: `#be-pool-search` (mono, accent focus ring), `.be-pool-purpose`, `.be-pool-item-badge.custom` (amber), `.be-avail-head`/`.be-avail-item`/`.be-avail-add` (dashed divider, hover + focus-visible). Template feature (Option 1 sketch) deliberately NOT implemented.

**verified** ✓ — `node --check` clean; HTML parser balanced; live :8000 serves `/` with `be-pool-search`+`be-pool-purpose`, `/static/app.js` with `_POOL_PURPOSES`/`addBuiltinPool`/`be-avail-add`, `/static/style.css` with `.be-pool-purpose`.

### 2026-08-09 — Prompt bank: New Bank auto-clone + USE button redesign

**New Bank auto-clone** ✓ — `#new-bank-modal` (name-input modal) removed entirely. New Bank tile is now a large `<button>` CTA (`.bt-new-sub` "Clone defaults & edit"). Click → `openNewBankFromDefault()`: `generateNextBankName()` scans `_savedBanks` for highest `Bank N` suffix → GET `/api/settings/banks/pools/defaults` → POST create {name, pools} → set active → render list → open editor immediately. Name can be changed via inline dblclick rename or editor `#be-name`. Removed dead JS: `openNewBankModalFromDefault`, `submitNewBank`, `closeNewBankModal`, `_createBankWithName`, `_newBankSource`; removed dead CSS (`#new-bank-modal*`, `.new-bank-body`, `.bank-input`, `.new-bank-status`; kept `.new-bank-footer` shared by delete modal); removed toolbar New Bank button (tile is the CTA).

**USE button** ✓ — every tile header shows either `.bt-active-pill` "ACTIVE" (green pill, active bank) or `.bt-use-btn` primary "Use" button (inactive custom banks) → `setActiveBank(id)`. Builtin tile shows "Use Default" → `setActiveBank('')` (restores builtin defaults). Prominent accent-styled button, hover/active states.

**keyboard nav** ✓ — new `DOMContentLoaded` handler on `#settings-bank-list`: ArrowDown/Up roving focus across `.bank-tile-new` + `.bt-name` buttons.

**simplified** ✓ — removed whole-tile div onclick + `event.stopPropagation()` (tiles no longer clickable as one unit; name button + Edit are the entry points). Removed `#new-bank-modal-box` from overscroll group. ESC/outside-click handler now only covers bank-editor + delete modals.

**verified** ✓ — `node --check app.js` + `py_compile` clean; HTMLParser 0 unclosed/0 errors; server restarted; served `/` has bank-editor-modal + bank-tiles, NO new-bank-modal; `/static/app.js` has `openNewBankFromDefault`/`generateNextBankName`/`bt-use-btn`/`bt-active-pill`, no `submitNewBank`; live round-trip create (13 pools) → set active → delete → restore `prompt v2` all ok.

### 2026-08-09 — Prompt bank redesign: a11y + web interface guidelines

**semantic HTML** ✓ — bank tile name is now a real `<button>` (was `<span>` in clickable `<div>`); New Bank tile is a `<button>`; modals use `aria-labelledby`/`aria-describedby` (bank-editor-title/subtitle, new-bank-title/subtitle, delete-bank-title/subtitle); all modal close buttons + pool delete buttons have `aria-label` + `aria-hidden` svgs; bank list container `aria-live="polite"` + `aria-labelledby`.

**pool listbox keyboard nav** ✓ — `#be-pool-list` is `role="listbox"`; `.be-pool-item` options carry `role="option"` + `aria-selected` + roving `tabindex`; ArrowUp/Down/Home/End + Enter/Space navigate/select via keydown handler.

**button states** ✓ — Save Bank/Create Bank/Delete show `Saving…`/`Creating…`/`Deleting…` while request in flight (disabled).

**CSS** ✓ — appended `Prompt Bank Redesign` block: `.visually-hidden` helper; `touch-action: manipulation` on tiles/pool items/buttons; `:focus-visible` for `.bank-tile`/`.be-pool-item`/import label; `.bt-name`/`.bt-chip` ellipsis truncation; `text-wrap: balance` on headers; tile hover lift via transform (compositor-friendly); `overscroll-behavior: contain` on modals + pool list; `.bank-tile-new` button reset (font:inherit, display:flex); `prefers-reduced-motion` disable.

**simplified** ✓ — removed redundant duplicate ESC/outside-click handlers block (primary handler at ~line 547 already covered new/delete bank modals); kept rename trigger = dblclick on name (click opens editor).

**verified** ✓ — node --check clean; HTML parser 0 errors/unclosed; live: served `/` has new modal ARIA + no pool-editor-wrapper; end-to-end API flow passed (create → update name+custom pool OCCASIONS → set active → delete); active bank restored to `prompt v2` (afd1a20efe3e).

### 2026-08-09 — Settings redesign: side-by-side panes + prompt bank tile cards

**settings HTML fixed** ✓ — `webui/static/index.html` `#section-settings` was severely malformed (missing `<div`/`<section`/`<h4` opening tags throughout). Rebuilt scratch: proper two-pane grid **IDENTITY (fixed 380px) | PROMPT BANKS**. Removed dead inline pool-editor markup (`pool-editor-wrapper`/`active-bank-header`/`saveAllPoolChanges`/`resetAllPoolsToBuiltin`) + 2 pre-existing stray `</div>`s. File now fully balanced (HTMLParser 0 errors).

**bank tile cards (masonry)** ✓ — `app.js` old pool-tile editor replaced. `.bank-tiles` CSS `column-count:2` masonry. Tiles: New Bank dashed tile (+ → `openNewBankModalFromDefault`), per-bank card = `.bt-head` (name clickable, ACTIVE badge), `.bt-pools` label chips (via `_POOL_LABELS`), `.bt-foot` (count + Edit/Use/Delete). Builtin tile read-only pseudo-bank. `setActiveBank(id)` → POST `/api/settings/banks/active`.

**bank editor modal** ✓ — `#bank-editor-modal` (z 1001, 760px, 2-col: 220px pool sidebar + textarea). Sidebar: `.be-pool-item` (label, count text, × remove), `+ List/Styles/Text Pool` buttons. Main: name input `#be-name`, `#be-pool-name` + `.pool-badge` type (styles/text/list), `#be-textarea`, `#be-hint`, Reset Pool / Save Bank. Dict pools serialized `style: item1, item2` per line; list = line per item; str = plain. Value-type helpers `_poolValType`/`_poolCopy`/`_poolToText`/`_textToPool`/`_poolCountText`/`_poolHintText`. Builtin = view-only. ESC + outside-click close.

**custom pools** ✓ — `core/prompt_banks.py` `_sanitize_bank` now keeps custom UPPERCASE pool keys (was: only 13 OVERRIDABLE_POOLS). Custom pools persist + edit via modal; only builtin-named pools affect generation (new OUTFIT dict style keys get picked up via flatten fallback).

**verified** ✓ — py_compile + node --check clean; HTML parser balanced; live server restarted: custom pool `OCCASIONS` create→save→restore on bank `prompt v2`, `/api/settings/banks`, `/api/settings/banks/pools/defaults` (13 pools) all 200; served HTML has modal + tiles, no old pool-editor refs.

---

**stale HTML cache fixed** ✓ — `webui/server.py` previously cached `HOMEPAGE_HTML = _load_homepage()` at import, so HTML edits needed a server restart (app.js/CSS were served fresh from disk → new JS + old HTML mismatch = removed-func ReferenceErrors: `saveAllPoolChanges`/`startInlineRename`, missing `bank-editor-modal`). Now `_serve_homepage` calls `_load_homepage()` per request. Removed module-level `HOMEPAGE_HTML`. **Bank UX upgrades**: whole `.bank-tile` clickable → `openBankEditor` (cursor pointer, `stopPropagation` on inner buttons); `.bt-name` click → inline rename input (`.bt-rename-input`), Enter/blur → POST update {id,name}; `saveBankFromModal` closes modal on success. **Layout**: `.settings-grid` fixed `380px 620px` + `justify-content:center` (panes don't move when sidebar toggles; collapses to 1fr < 900px). Bank name restored to `prompt v2` after a test rename artifact.

**verified** ✓ — py_compile + node --check clean; Node harness (`scripts/_bank_test.js`, deleted after use) ran full bank flows: tiles render w/ prompt v2, editor opens (name/pools/textarea), save + setActive POST correctly; server restarted, served `/` = bank-editor-modal+bank-tiles present, pool-editor-wrapper absent; `/static/app.js` = startBankRename/commitBankRename present; live POST update {id,name:'prompt v2'} + active + 13 defaults all 200.

### 2026-08-06 — Caption generator feature (phases 1-4)

**generator module** ✓ — `scripts/alina_textgen.py`: zero-dependency, identity-locked pool-based caption generator (Alina alt-girl tone). `OPENERS`/`MIDDLES`/`CLOSERS` pools × 5 hook types (vulnerable/confident/playful/aesthetic/relatable), `PLATFORM_CONFIG` per-platform CTA + hashtags (tiktok/reels/shorts/x/stories), seed-reproducible `generate_caption`/`batch_generate` with text dedup, argparse CLI (`py scripts/alina_textgen.py 10 tiktok --seed 42`).

**server endpoint** ✓ — `webui/server.py` `POST /api/captions/generate`: body `{count (1-20), platform, hook_types, seed}`; ValueError→400, Exception→500; imports `batch_generate` from scripts via `sys.path` (scripts/ has no `__init__.py`).

**UI card** ✓ — `webui/static/` caption-gen-card in `index.html`, `app.js` `generateCaptions()`/`renderCaptions()`/`copyCaption()`/`copyAllCaptions()`/`clearCaptions()`, `.caption-*` styles.

**CI + docs** ✓ — `.github/workflows/ci.yml` syntax-check includes `scripts/alina_textgen.py` py_compile + import-test `sys.path.insert(0,'scripts')` line; `codemap.md`/`scripts/codemap.md`/`AGENTS.md` document the feature.

**verified** ✓ — py_compile clean; live POST count=3 → `ok:true` 3 captions; GET `/` serves caption-gen-card; all existing endpoints regression-passed on :8000.

---

### 2026-08-06 — Output batch grouping fixed + prompt bank export/import

**batch grouping bug fixed** ✓ — `webui/server.py` `_collect()` grouped output batches by directory **mtime** instead of directory **name**. After dirs `2026-07-27`…`2026-08-03` were bulk-touched (`mtime` 8/4 01:26), all collapsed into one mislabeled "August 04" batch (49 items, wrong dates). Fix: date_key parsed from `entry.name` (`%Y-%m-%d`), mtime fallback only for non-date-named dirs; batch label from date_key. Verified: 11 correct date batches (was 4 merged). `py_compile` clean.

**prompt bank export/import** ✓ — `core/prompt_banks.py`: `export_banks()` → `{version, exported_at, active_bank, banks}`; `import_banks(data)` → merge (skip existing IDs + entries w/o valid name/pools), sanitize pools via `_sanitize_bank()`, set active_bank if present+valid, returns `{imported, skipped, active_bank_set}`. `webui/server.py`: `GET /api/settings/banks/export` (attachment `prompt_banks_YYYY-MM-DD.json`), `POST /api/settings/banks/import` (`{data: export}` body). `webui/static/index.html` Saved Banks header: Export button + Import label/file-input. `webui/static/app.js`: `exportBanks()` (blob download) + `importBanks()` (FileReader → POST → `renderBankList()` + toast counts). Verified: py_compile + node --check clean; unit test imported 1/skipped 2/active set; live round-trip import of own export → 0 imported, banks unchanged.

---

### 2026-08-05 — Reactive prompt preview (non-locking Generate)

**refactored** ✓ — `webui/static/app.js`: extracted `fetchPromptPreview(silent)` helper (fetch `/api/prompts/generate` + render `.prompt-item` list + show Confirm/Cancel/Edit). `startPromptGeneration()` no longer locks controls/button — shows `Generating prompts…`, renders preview, button → `Update Preview` (was `Review prompts → confirm`). Controls stay interactive after Generate.

**reactive refresh** ✓ — new `schedulePreviewRefresh()` (300ms debounce) wired into `updateCost()` — fires on vibe/camera/lighting/outfit/time/count changes; re-renders preview with new selections, silent (no error UI). Skipped until first preview (`_pendingJobs` guard). `#bank-select` behavior unchanged (no refresh trigger). Double-click guard `_previewFetching`.

**lock moved** ✓ — `confirmGeneration()` now calls `setControlsLocked(true)` + `btn.disabled/loading` at confirmation only. `cancelGeneration()` simplified (resets list + `_btnTxt('Generate')`, no `_resetBtn`).

**animated button text** ✓ — `_startGenAnim()` cycles `Generating.` → `Generating..` → `Generating...` at 500ms; `_resetBtn()` + `_fail` + both terminal poll branches + start-fail branch `clearInterval(_genAnimTimer)` so OK/FAIL text isn't clobbered. Button states: `Generate` → `Update Preview` → animated → done `Generate`.

**verified** ✓ — `node --check` clean; live server serves `/static/app.js` with `Update Preview` present. No restart needed (JS-only, served from disk).

---

*Full history: see `docs/changelog.md`*