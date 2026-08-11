# OFM — Full Change History

Moved from AGENTS.md to keep main file lean. AGENTS.md keeps only last 4 entries.

---

### 2026-08-11 — Project restructure

**app.js split** ✓ — `webui/static/app.js` (2713 lines, flat globals) deleted; replaced by 10 module files in `webui/static/js/`: `core.js` (window.onerror/unhandledrejection, `setLive()`, `api()`, toast system `showToast`/`showError`/`showSuccess`/`showInfo`/`showWarning`/`_getToastContainer`/`_toastContainer`, `esc()`), `theme.js` (`_themes`, `setTheme`/`initTheme`/`toggleThemeModal`/`closeThemeModal`/`loadThemeList`/`selectTheme`/`handleThemeKeydown`, `motionQuery`/reduced-motion), `layout.js` (`_sidebarCollapsed`/`_activeSection`, `loadSidebarState`/`saveSidebarState`/`toggleSidebar`/`expandSidebar`/`closeFloaterMenu`/`showSection`/`loadSettingsUI`/`syncPanelHeights`/`_heightSyncTimer`), `settings.js` (`_pendingAvatarUrl`, `_setSettingsStatus`, `loadSettings`/`loadAvatarUrl`/`handleAvatarFile`/`saveIdentity` + avatar upload-zone DOMContentLoaded listeners), `promptBanks.js` (all bank state `_activeBankId`/`_savedBanks`/`_pendingDeleteId`/`_POOL_LABELS`/`_OVERRIDABLE_POOLS`/`_POOL_PURPOSES`/`_bankEditor*`, pool helpers, `renderBankList`, bank editor modal, new-bank clone, delete, `exportBanks`/`importBanks`), `captions.js` (`_captions`, `getSelectedCapPlatform`/`Hook`, `generateCaptions`/`renderCaptions`/`copyCaption`/`copyAllCaptions`/`clearCaptions`), `generation.js` (radio getters vibe/camera/lighting/time/outfit, `onVibeChange`/`onCameraChange`, `_balance`/`_perPhoto`/`_pendingJobs`, `fetchBalance`/`refreshBalance`/`updateCost`, `_btnTxt`/`_statusBadge`/`_renderGenStatus`/`_startGenAnim`/`_resetBtn`, `setControlsLocked`, `_previewDebounce`/`_genAnimTimer`/`_previewFetching`, `fetchPromptPreview`), `outputs.js` (`_outputsData`/`_preview`/`_viewMode`/`_showAll`, batch/item `editCaption`/`closeEdit`/`saveEdit`, `showPrompt`/`closePrompt`/`copyPrompt`, `closeFS`), `apiProviders.js` (`_selectedAccount`/`_lastIdentity`/`_lastApiCount`, validation/account API toggle/load), `init.js` (single DOMContentLoaded: `setLive`/`fetchBalance`/`refreshOutputs`/`syncViewToggle`/`checkApiStatus`/`preloadAccounts`/`preloadValidation`/`loadActiveBank`, 30s/60s intervals).

**index.html script tags** ✓ — single monolithic app.js tag replaced with 10 one-line `<script src="/static/js/{core,theme,layout,settings,promptBanks,captions,generation,outputs,apiProviders,init}.js">` tags in load order; `init.js` last.

**scratch/debug cleanup** ✓ — deleted root `_check.py`, `_swap.py`, `test_output2.html`, `_settings_debug.txt`; root + `webui/_srv.log`/`_srv_err.log`; all `__pycache__/`; `pipeline/promptbank_*.json`/`edited_prompts_*.json`; `outputs/*/checkpoint_*.json`.

**UNUSED FILES/ archive** ✓ — `UNUSED FILES/` is the git-ignored archive root with README.md; moved in: `.claude/skills/`, `.playwright-mcp/`, `.slim/`, `hot-take-influencer/`, `PLAN_bank_editor_redesign.md`, `PROMPT_BANK_REDESIGN_PLAN.md`, `scripts/backfill_prompts.py`, `scripts/save_meta.py`, `scripts/update_config.py`, `pipeline/wavespeed_i2v_client.py`, `webui/static/sidebar.md`.

**server.py cleanup** ✓ — `webui/server.py`: removed duplicate `export_banks, import_banks` in the line-34 import; removed unused `build_jobs` prompt_bank import (now `list_presets, build_jobs_multi, get_builtin_pools`); removed dead `_run_dashboard()`; removed duplicate unreachable `/api/settings/banks/export` GET + `/api/settings/banks/import` POST blocks; simplified `_start_pipeline(prompts)` (dropped unused `mode` param + dead `with_text` branch); caller updated to `_start_pipeline(prompts)`.

**ci.yml updated** ✓ — syntax-check no longer py_compiles retired files (`scripts/backfill_prompts.py`, `save_meta.py`, `update_config.py`, `pipeline/wavespeed_i2v_client.py`, `hot-take-influencer/scripts/wavespeed_client.py`); frontend-lint now checks `test -d webui/static/js` and `for f in webui/static/js/*.js; do node --check "$f"; done`.

**verified** ✓ — `python -m py_compile webui/server.py` clean.

---

### 2026-08-09 — Settings redesign: side-by-side panes + prompt bank tile cards

**settings HTML fixed** ✓ — `webui/static/index.html` `#section-settings` was severely malformed (missing `<div`/`<section`/`<h4` opening tags throughout). Rebuilt scratch: proper two-pane grid **IDENTITY (fixed 380px) | PROMPT BANKS**. Removed dead inline pool-editor markup (`pool-editor-wrapper`/`active-bank-header`/`saveAllPoolChanges`/`resetAllPoolsToBuiltin`) + 2 pre-existing stray `</div>`s. File now fully balanced (HTMLParser 0 errors).

**bank tile cards (masonry)** ✓ — `app.js` old pool-tile editor replaced. `.bank-tiles` CSS `column-count:2` masonry. Tiles: New Bank dashed tile (+ → `openNewBankModalFromDefault`), per-bank card = `.bt-head` (name clickable, ACTIVE badge), `.bt-pools` label chips (via `_POOL_LABELS`), `.bt-foot` (count + Edit/Use/Delete). Builtin tile read-only pseudo-bank. `setActiveBank(id)` → POST `/api/settings/banks/active`.

**bank editor modal** ✓ — `#bank-editor-modal` (z 1001, 760px, 2-col: 220px pool sidebar + textarea). Sidebar: `.be-pool-item` (label, count text, × remove), `+ List/Styles/Text Pool` buttons. Main: name input `#be-name`, `#be-pool-name` + `.pool-badge` type (styles/text/list), `#be-textarea`, `#be-hint`, Reset Pool / Save Bank. Dict pools serialized `style: item1, item2` per line; list = line per item; str = plain. Value-type helpers `_poolValType`/`_poolCopy`/`_poolToText`/`_textToPool`/`_poolCountText`/`_poolHintText`. Builtin = view-only. ESC + outside-click close.

**custom pools** ✓ — `core/prompt_banks.py` `_sanitize_bank` now keeps custom UPPERCASE pool keys (was: only 13 OVERRIDABLE_POOLS). Custom pools persist + edit via modal; only builtin-named pools affect generation (new OUTFIT dict style keys get picked up via flatten fallback).

**verified** ✓ — py_compile + node --check clean; HTML parser balanced; live server restarted: custom pool `OCCASIONS` create→save→restore on bank `prompt v2`, `/api/settings/banks`, `/api/settings/banks/pools/defaults` (13 pools) all 200; served HTML has modal + tiles, no old pool-editor refs.

---

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

### 2026-08-05 — Prompt bank v5: working-example handheld redesign (supersedes v4)

**v4 rolled back** ✓ — `pipeline/prompt_bank.py` is now v5 (`# v5` docstring). Working-example formula (user-verified variations) proved phone/arm-in-frame tokens caused mirror-like composition. Removed `HANDHELD_SELFIE_CAMERA` pool + `QUALITY_POOLS` dict + all their logic (`handheld_token`/`quality_pools` refs). Handheld intro is now a fixed `"Front-facing handheld selfie, vertical 9:16, no phone visible"` (phone held out of frame). Added constant `"neutral expression, not smiling"` to positive. Mirror mode stays distinct (`Front-facing mirror selfie` + `black iPhone visible in hand` + `black iPhone` footer line; `MIRROR_NEGATIVE` has no "mirror selfie"/"phone visible").

**pools rewritten** ✓ — FRAMING 6 example variants (slightly tilted/low/off-center uneven framing, motion blur, head-to-waist crop); POSES 15 subtle torso/weight-only (no phone-in-hand, no arm-in-frame); INDOOR_SCENES 10 example-style ("standing casually in a dim bedroom near an open closet", clutter kept); MIRROR_SCENES 4 (mirror + tiled/wardrobe context, phone covering face); OUTDOOR_SCENES 10 (dropped "facing camera" suffix, clutter kept); HAIR 15 (added wet slicked-back/damp braid/air-dried frizz example variants); LIGHTING_POOLS simplified (concise "dim warm indoor lighting, soft shadows, deep blacks, moody, imperfect exposure" style per key, no quality-scene duplication); QUALITY 5 tightened (iPhone 15 Pro Max, visible pores, film grain, amateur snapchat, non-AI, photorealistic); DEFAULT_NEGATIVE concise 176 chars: `phone visible, mirror selfie, lamp visible, smiling, overly posed, studio lighting, symmetry, CGI skin, unrealistic texture, accessories, jewelry, necklaces, earrings, cleavage`.

**sync** ✓ — `core/prompt_banks.py` OVERRIDABLE_POOLS 15→13 (dropped HANDHELD_SELFIE_CAMERA, QUALITY_POOLS); `pipeline/prompt_bank.py` OVERRIDABLE_POOLS + `get_builtin_pools()` match (13, verified equal sets). `webui/static/app.js` `_POOL_LABELS` −2, `_isDictPool()` no longer includes QUALITY_POOLS. Saved bank `d0942bb05db6` (OUTFIT_TOPS/BOTTOMS/LIGHTING overrides) still valid — no migration. Server restarted to load v5.

**verified** ✓ — py_compile (prompt_bank, prompt_banks) + node --check clean; CLI gen handheld shows no-phone-visible + not-smiling + concise negative; mirror isolated (black iPhone, no "no phone visible"); live `/api/prompts/generate`: 3/3 jobs no phone-in-frame tokens, not-smiling present, negative contains "phone visible"; bank_id generation composes overrides.

---

### 2026-08-05 — Prompt bank v4 pools: nano-banana-2 realism overhaul ⚠️ SUPERSEDED by v5 (see above; v4 tokens caused mirror-like output)

**pools expanded** ✓ — `pipeline/prompt_bank.py`: QUALITY 1→6 variants (iPhone snapshot/ISO-noise/compression realism); new `QUALITY_POOLS` dict (flash/screen lighting-keyed — specific variant per lighting, else random from QUALITY); new `HANDHELD_SELFIE_CAMERA` (6 authentic phone-in-hand tokens: arm angle, thumb/pinky grip, shake); POSES 12→20 (subtle hand-on-neck/hip/cheek, hair-graze, phone-at-chest — safe for one-hand grip); NEGATIVE added anti-AI terms (waxy/airbrushed/beauty filter/facetune/poreless/centered/professional/staged/3d render/cg) + removed "phone visible" from DEFAULT (handheld now shows phone); LIGHTING_POOLS +flash/screen/mixed (9 new); HAIR +5 bedhead; INDOOR_SCENES +6 cluttered/lived-in; OUTDOOR_SCENES +5 urban clutter. `_build_prompt()` takes `handheld_token` (mirror mode stays distinct: mirror intro + black iPhone line, no handheld token). `build_jobs_multi()` picks handheld token per job + quality-by-lighting. `list_presets()` lighting now 6 options.

**settings sync** ✓ — `core/prompt_banks.py` OVERRIDABLE_POOLS tuple +2 (`HANDHELD_SELFIE_CAMERA`, `QUALITY_POOLS`); sanitizer drops unknown pool keys. `pipeline/prompt_bank.py` OVERRIDABLE_POOLS + `get_builtin_pools()` mirror both new pools.

**UI** ✓ — `webui/static/index.html` lighting pills +Flash/Screen/Mixed (user-selectable). `webui/static/app.js` `_POOL_LABELS` +2, `_isDictPool()` includes QUALITY_POOLS.

**verified** ✓ — py_compile all 5 files + node --check clean; live server: presets return 6 lighting, generate(flash)→flash quality + handheld token in prompt, generate(screen)→screen quality, mirror isolated (no handheld token, black iPhone line), `/api/settings/banks/pools/defaults` = 15 pools, `_sanitize_bank` accepts new keys / drops bogus. Note: bank `e99f325aeb11` ("wdasder") still carries old single-entry QUALITY list override → falls back to list (works, no new variants).

---

### 2026-08-05 — settings.json data re-entered after merge loss

**restored from git history** ✓ — After merge/pull wiped `core/settings.json`, recovered full data from pre-deindex commit `78a3c20` (via `git show 78a3c20:core/settings.json`): 5 WaveSpeed accounts (smileypvp4, eduardtojong8, alinaskyfp, captlessgaming [active], motivationalaltruist), 2 prompt banks (`d0942bb05db6` "test" = active, `e99f325aeb11` "wdasder") with all pools intact, `active_bank`. Preserved current avatar_url (newer ibb.co upload) over old. Re-merged with python keeping current identity. Verified live: `/api/settings/wavespeed/accounts` returns 5 masked keys, `/api/settings/banks` returns both banks, `/api/balance/total` = $1.82 live.

---

### 2026-08-05 — Real WaveSpeed API progress tracking

**real API progress on Generate button** ✓ — `api/wavespeed_client.py`: `poll()` now reports `status_callback(status, elapsed, data)` on every tick incl. terminal (real status, server-measured elapsed, `timings.inference`, verbatim `error`); `batch_generate` wraps `status_callback`/`on_event` job-bound (`(job, ...)`); `_generate_one` emits `submitting`/`enhancing`/`saved` milestones. `pipeline/pipeline.py`: thread-safe per-image state; emits `@P image|<file>|<status>|<elapsed>s|<detail>` (5s throttle on identical non-terminal status); flagged error verbatim (double-prefix dedup). `webui/server.py`: parses `@P image|` → `state["images"]` dict; adds server-measured run `elapsed` (from `started_at`); `/api/progress` returns `images` + `elapsed`. `index.html`: `#gen-status-strip` under Generate button. `app.js`: `_renderGenStatus()` per-image strip (filename · Queued/Processing/Done/Error badge · server elapsed · detail); button shows server `p.elapsed` not local timer; flagged warning includes verbatim API error (pulled from failed image detail). `style.css`: `.gen-status-strip`/`.gs-row`/`.gs-badge` theme-var styles (processing = pulsing amber, done = accent, error = red, detail wraps for errors). Phase 2 video = deferred/hidden (not planned); video code stays orphaned.

**identity in settings** ✓ — `core/config.py`: `get_identity()`/`set_identity()` read/write `settings.json["identity"] = {name, avatar_url}` (auto-migrates from `docs/wavespeed_identity_alina.md`). `pipeline/pipeline.py` `_load_avatar_url()` reads identity first. `webui/server.py`: GET/POST `/api/settings/identity`, POST `/api/settings/identity/upload` (multipart, 5MB max, image/* only; parse BEFORE `_read_body()`). Toolbar gains `.settings-nav-trigger` (rightmost); `#settings-modal` with avatar preview, URL input, drag-drop upload zone, Save/Done. `style.css` `.settings-*` styles at EOF.

**local upload → public URL** ✓ — `_handle_identity_upload()` saves local copy to `outputs/identity/` AND auto-publishes via `WaveSpeedClient.upload_file()` → public cloudfront URL stored as `avatar_url` (required — WaveSpeed API needs public reference image, local paths fail). Graceful fallback + warning if publish fails. Frontend rejects non-http(s) URLs in URL field.

**custom prompt banks** ✓ — `core/prompt_banks.py`: banks `{id, name, description, pools}` + presets `{id, name, config}` persisted under `settings.json["prompt_banks"]`/`["presets"]`. `pipeline/prompt_bank.py` `build_jobs_multi(..., bank=None)` overrides pools via `_resolve_pool()` (lists + string pools: IDENTITY_LOCK, negatives). `webui/server.py`: `/api/settings/banks/{create,update,delete,view}`, `/api/settings/presets/{create,delete}`; `/api/prompts/generate` accepts `bank_id`, unwraps `found.get("pools")`. Generation panel gains `#bank-select` + preset row (save/load/delete) in index.html/app.js; `.bank-select`/`.preset-row` CSS.

**verified** ✓ — py_compile + node --check clean; live server: bank CRUD, preset CRUD, gen-with-bank uses custom pool, upload returns public cloudfront URL, mocked e2e confirmed avatar_url flows `get_identity()` → `_load_avatar_url()` → `mode_photo` → `batch_generate(avatar_url)` → WaveSpeed `"images":[url]`. Test artifacts cleaned; settings.json identity restored to real ibb.co URL.

---

### 2026-08-01 — Repo reorganization: github-ready layout

**restructured** ✓ — Applied approved 10-step reorg, preserving local behavior:
- `pipeline-tiktok/` → `webui/` (web control panel: server.py, dashboard.py, wavespeed_tiktok_client.py, activity.json, static/, fonts/)
- `pipeline-photovideo/` → `pipeline/` (pipeline.py, prompt_bank.py, wavespeed_i2v_client.py, alina_video_guide.md)
- `wavespeed-batch-api/` → `api/` (wavespeed_client.py)
- root `server.py` → `webui/server.py`; `pipeline-tiktok/run.py` → `scripts/run_tiktok.py`
- `alina_style_guide.md` + `wavespeed_identity_alina.md` → `docs/`
- Deleted 3 shims (daybatch/text_generator), style.css.backup.css, 13 runtime JSON files, __pycache__

**imports fixed** ✓ — `webui/server.py` BASE=parent.parent, dir vars renamed (PIPELINE_DIR/WEBUI_DIR/API_DIR); `pipeline/pipeline.py` uses `core.daybatch` + `../api`; `scripts/run_tiktok.py` imports from webui/ + core; `core/config.py` identity → `docs/`, lazy path → `../api`; scripts paths updated.

**packages** ✓ — Added `__init__.py` to webui/, pipeline/, api/ so `import webui.server` etc. work. CI now has valid package imports + `pip install requests` + new path lists. `.gitignore` updated for webui/fonts + runtime promptbank/checkpoint JSONs. Fixed latent `NameError: random` in run_tiktok.py (was never imported).

**docs** ✓ — Rewrote root codemap.md + all folder codemaps (webui, static, pipeline, api, scripts, core) and SKILL.md frontmatter (webui, pipeline, api). AGENTS.md File Structure/Paths/Active Components updated. Stripped UTF-8 BOM from static/index.html.

**verified** ✓ — py_compile all 18 files clean; full import graph resolves; live boot on :8765 returns 200 for `/`, `/static/style.css`, `/api/ping`, `/api/presets`, `/api/outputs`.

---

### 2026-07-31 — API selector modal simplification (check marks only)

**rename removed** ✓ — `pipeline-tiktok/static/app.js`: `.provider-name` in `loadApiProviderList()` no longer has `onclick="startRenameApi(...)"` / `title="Click to rename"`. Deleted the `startRenameApi()` function entirely (dead code). Settings drawer rename (`startRename`) preserved.

**hover-reveal removed** ✓ — `.provider-key` in the modal no longer carries `data-full` / `title="Hover to reveal"`; keys stay masked. Deleted the document-level `mouseover`/`mouseout` reveal delegation.

**check-marks-only** ✓ — `pipeline-tiktok/static/style.css`: replaced `.provider-radio` circle buttons with `.provider-check` (plain 28px icon button, no circle border, `svg` always visible). Active = emerald `var(--accent)` check (disabled, default cursor); inactive = gray `var(--fg3)` check (pointer, hover → emerald + subtle tint). Responsive block updated `.provider-radio` → `.provider-check`.

**key/name affordances** ✓ — `#api-provider-list .provider-name` dropped `cursor: text`; `.provider-key` dropped `cursor: help` + `:hover` color shift.

**verified** ✓ — `node --check` clean; live server serves updated app.js (no `startRenameApi`) / style.css (no `provider-radio`); `/api/settings/wavespeed/accounts` returns 4 accounts, `captlessgaming` active.

---

### 2026-07-31 — API selector modal redesign + toolbar label sync

**selected-account state** ✓ — `pipeline-tiktok/static/app.js`: new `_selectedAccount` / `_lastIdentity` / `_lastApiCount` globals + `updateApiLabel()` sets `#api-user` with priority: `_selectedAccount` → identity → `N API(s)` → 'No API keys'. `checkApiStatus()` no longer writes the label directly (only dot + balance); it clears stale `_selectedAccount` when the account disappears and falls back to `active`. `loadApiProviderList()` + `confirmSwitchApi()` set `_selectedAccount` and refresh the label. Toolbar now shows the modal account name (e.g. `captlessgaming`), NOT the API identity (`Alina Sky`).

**modal table redesign** ✓ — `pipeline-tiktok/static/style.css` `#api-provider-list`: rows 56px min-height (14px/16px padding, 12px gap); selected row gets 3px emerald left accent bar + `rgba(5,150,105,.05)` tint; account name Geist 14px/500, balance + API key JetBrains Mono 12px (balance tabular-nums, right-aligned 80px); API key masked `••••••••abcd` with hover-reveal (`data-full` + document-level mouseover/mouseout delegation); status = 6px colored dot + label (green #4caf50 / red #dc2626); actions 28px — radio/checkmark (`_checkSvg`) for active, 28px circle radio to switch, X `_delSvg2` for delete with red hover. `.provider-header` uppercase 10px/16px.

**toolbar label type** ✓ — `.api-nav-user` → 14px/500 sans; `.api-nav-bal` → 12px JetBrains Mono tabular-nums.

**responsive** ✓ — `@media (max-width:600px)`: full-width modal, tightened row gaps/paddings, smaller columns.

**verified** ✓ — `node --check` clean; server serves `/`, `/static/app.js`, `/static/style.css`; `/api/settings/key/status` returns accounts + active label. Settings drawer intentionally unchanged.

---

### 2026-07-31 — Controls lock during generation

**controls-locked** ✓ — `pipeline-tiktok/static/style.css` + `app.js`: new `setControlsLocked(locked)` toggles `.controls-locked` class on `.gen-layout .card` (55% opacity) and disables all card inputs (Vibe/Camera/Lighting/Outfit/Time pills + count slider). Lock fires at top of `startPromptGeneration()` (immediately on Generate click, stays locked through prompt review → confirm → pipeline). Unlock lives inside `_resetBtn()`, covering every terminal path: success, error, stall-retry failure, and Cancel. Locked elements use `pointer-events: none` (normal arrow cursor, no not-allowed icon); pill hover states suppressed while locked.

---

### 2026-07-31 — Prompt preview equal-height fix

**equal-height panels** ✓ — `pipeline-tiktok/static/style.css` + `app.js`: `.gen-layout` uses `align-items: stretch`; new `syncPanelHeights()` measures `.gen-layout .card` offsetHeight and sets `.gen-preview` height to match (cleared <768px). Hooked on load, debounced resize, `document.fonts.ready`, and prompt-state transitions (startPromptGeneration/_resetPromptList). Text window expands to fill card via nested flex (preview → body → prompt-item → pre/textarea all `flex: 1`). `.gen-preview-actions` reserves `min-height: 44px` so buttons appearing don't shift layout. `#btn-photo` locked to `height: 44px` + ellipsis so polling text changes don't resize the card. Pre/textarea box models already identical → edit mode height-stable. Mobile: `.gen-preview` min 260px, body `max-height: 420px`.

---

### 2026-07-30 — Initial state capture

**connect-light-outfit-prompts** ✓ — `pipeline-photovideo/prompt_bank.py`: split LIGHTING/OUTFIT pools into style-keyed dicts (warm/cool/dimlit, fem/street/grunge/academia), expanded POSES 6→12, wired `lighting` + `outfit_style` params into `build_jobs_multi()`. ~60 new strings. 1 file.

**style guides added** ✓ — `alina_style_guide.md` (63 lines, photo prompts) + `pipeline-photovideo/alina_video_guide.md` (video prompts).

**scripts added** ✓ — `open_dashboard.py`, `update_meta.py`, `save_meta.py`, `update_config.py`.

**MCP dirs** ✓ — `.codegraph/` (code intelligence index), `.playwright-mcp/` (browser automation).

**outputs** ✓ — `outputs/2026-07-30/` (today), `outputs/alina_tiktok_b1/`, `outputs/tiktok_b1/`, `outputs/dashboard.html`.

---

### 2026-07-30 — OpenSlimedit installed

**openslimedit** ✓ — Added `"openslimedit@latest"` to `~/.config/opencode/opencode.jsonc` plugin array. Reduces token usage by ~25-45% via tool description compression, compact read output, and line-range edit expansion. Zero config, activates on next OpenCode restart.

---

### 2026-07-30 — Taste-skill installed + frontend redesign

**taste-skill** ✓ — Installed `design-taste-frontend`, `redesign-existing-projects`, `high-end-visual-design`, `minimalist-ui` skills to `.claude/skills/`. Agents should load relevant skill when working on the OFM frontend.

**frontend redesign** ✓ — Applied taste-skill audit fixes: swapped accent from AI-purple indigo (`#6366f1`) to deep emerald (`#059669`), removed outer glow on CTAs, added spring cubic-bezier transitions, cleaned up 25+ lines of dead legacy CSS, added meta tags + SVG favicon + skip-to-content link, fixed broken textarea tag, added tabular-nums on balance display.

---

### 2026-07-30 — Cleanup + Codemap

**cleanup** ✓ — Deleted 34 generated promptbank_*.json files, test prompts, empty logs, old batch output dirs (alina_tiktok_b1, tiktok_b1), __pycache__ dirs (5 locations), outputs/dashboard.html, broken .codegraph junction.

**scripts moved** ✓ — Moved open_server.py, open_dashboard.py, save_meta.py, update_config.py from root to scripts/. Fixed path references in open_server.py/open_dashboard.py (one level up for __file__).

**.gitignore** ✓ — Created with excludes for __pycache__, .env, outputs, fonts/*.ttf, logs, OS/IDE files.

**codemap** ✓ — Initialized .slim/codemap.json tracking 43 files. Generated 9 codemap.md files (root, core, pipeline-tiktok, static, pipeline-photovideo, wavespeed-batch-api, hot-take-influencer, hot-take-influencer/scripts, scripts). Added Repository Map section to AGENTS.md. Next sessions load codemap instead of scanning 100+ junk files.

---

### 2026-07-30 — OpenCode Web redesign

**style.css full rewrite** ✓ — Warm monochrome palette (`#141413` dark / `#f4f2ee` light), removed all `backdrop-filter`/glassmorphism, Geist + JetBrains Mono via Google Fonts `@import`, consistent `border-radius: 6px`/`8px` across all elements, flat surfaces with 1px borders, new `.toolbar`/`.card`/segmented control styles, amber-tinted ambient glow.

**index.html restructured** ✓ — `<nav class="top-nav">` → `<header class="toolbar">` (fixed full-width, 48px), 3-bar SVG brand mark, removed `panel-shell`/`panel-core` nesting → single `<div class="card">`, theme-color updated to `#141413`.

**app.js updated** ✓ — `.top-nav` → `.toolbar` selector, padding `120px` → `64px` for new toolbar height.

**codemap updated** ✓ — Reflected static file changes in codemap.

---

### 2026-07-30 — Prompt Used inline + backfill

**server moved to root** ✓ — Moved `pipeline-tiktok/server.py` → `server.py`. Auto-opens browser on start. Run: `py server.py`.

**Prompt inline toggle** ✓ — Replaced Description labels + modal popup with clickable "Prompt Used" that toggles an inline `<pre>` box preserving exact prompt formatting. Deleted 60+ lines of orphaned modal CSS/HTML/JS.

**backfill_prompts.py** ✓ — `scripts/backfill_prompts.py` scans all `outputs/*/meta.json`, parses labels (`"scene · pose"`), reconstructs full prompts via deterministic seed from stem hash using `prompt_bank` pools. 38 entries backfilled across 5 existing meta.json files.

**companion .prompt files** ✓ — `pipeline-photovideo/pipeline.py` saves `{stem}.prompt` alongside each image on every batch generation. `server.py` `_collect()` reads `.prompt` files as priority source over meta.json. Future outputs automatically get prompt data.

**codemap updated** ✓ — Updated 6 codemap.md files (root, pipeline-tiktok, static, pipeline-photovideo, scripts). Now tracking 44 files in `.slim/codemap.json`.

---

### 2026-07-31 — Taste-skill table redesign + cleanup

**premium table redesign** ✓ — Merged `pr`+`cp` columns into single `info` column: caption (2-line clamp, 500 weight) + meta row (Prompt Used monospace link · format badge pill). Row padding 6px→10px, hover gets 2px accent left border, row separators via 1px border, action buttons 26px→28px with 4px gaps, batch title 600 weight.

**Guidance Scale removed** ✓ — Stripped from prompt modal HTML + JS + hidden data attributes.

**checklist/used system removed** ✓ — Deleted `toggleStatus`, checkbox column, `batchUsed`/`b-used` spans, `tr-used` CSS, `b-spacer` CSS. Clean rows, no usage tracking.

**caption auto-refresh** ✓ — `saveEdit()` now calls `refreshOutputs()` after saving caption.

**auto-close tab on shutdown** ✓ — `/api/ping` endpoint + JS polling every 3s. When server goes down, shows "Server stopped. Close this tab." message.

---

### 2026-07-30 — Cleanup + Codemap (duplicate entry)

**cleanup** ✓ — Deleted 34 generated promptbank_*.json files, test prompts, empty logs, old batch output dirs (alina_tiktok_b1, tiktok_b1), __pycache__ dirs (5 locations), outputs/dashboard.html, broken .codegraph junction.

**scripts moved** ✓ — Moved open_server.py, open_dashboard.py, save_meta.py, update_config.py from root to scripts/. Fixed path references in open_server.py/open_dashboard.py (one level up for __file__).

**.gitignore** ✓ — Created with excludes for __pycache__, .env, outputs, fonts/*.ttf, logs, OS/IDE files.

**codemap** ✓ — Initialized .slim/codemap.json tracking 43 files. Generated 9 codemap.md files (root, core, pipeline-tiktok, static, pipeline-photovideo, wavespeed-batch-api, hot-take-influencer, hot-take-influencer/scripts, scripts). Added Repository Map section to AGENTS.md. Next sessions load codemap instead of scanning 100+ junk files.

---

### 2026-07-30 — OpenCode Web redesign (duplicate entry)

**style.css full rewrite** ✓ — Warm monochrome palette (`#141413` dark / `#f4f2ee` light), removed all `backdrop-filter`/glassmorphism, Geist + JetBrains Mono via Google Fonts `@import`, consistent `border-radius: 6px`/`8px` across all elements, flat surfaces with 1px borders, new `.toolbar`/`.card`/segmented control styles, amber-tinted ambient glow.

**index.html restructured** ✓ — `<nav class="top-nav">` → `<header class="toolbar">` (fixed full-width, 48px), 3-bar SVG brand mark, removed `panel-shell`/`panel-core` nesting → single `<div class="card">`, theme-color updated to `#141413`.

**app.js updated** ✓ — `.top-nav` → `.toolbar` selector, padding `120px` → `64px` for new toolbar height.

**codemap updated** ✓ — Reflected static file changes in codemap.

---

### 2026-07-30 — Prompt Used inline + backfill (duplicate entry)

**server moved to root** ✓ — Moved `pipeline-tiktok/server.py` → `server.py`. Auto-opens browser on start. Run: `py server.py`.

**Prompt inline toggle** ✓ — Replaced Description labels + modal popup with clickable "Prompt Used" that toggles an inline `<pre>` box preserving exact prompt formatting. Deleted 60+ lines of orphaned modal CSS/HTML/JS.

**backfill_prompts.py** ✓ — `scripts/backfill_prompts.py` scans all `outputs/*/meta.json`, parses labels (`"scene · pose"`), reconstructs full prompts via deterministic seed from stem hash using `prompt_bank` pools. 38 entries backfilled across 5 existing meta.json files.

**companion .prompt files** ✓ — `pipeline-photovideo/pipeline.py` saves `{stem}.prompt` alongside each image on every batch generation. `server.py` `_collect()` reads `.prompt` files as priority source over meta.json. Future outputs automatically get prompt data.

**codemap updated** ✓ — Updated 6 codemap.md files (root, pipeline-tiktok, static, pipeline-photovideo, scripts). Now tracking 44 files in `.slim/codemap.json`.