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
│   ├── static/                        Frontend (index.html, style.css, app.js)
│   └── fonts/                          TikTok Sans (gitignored binaries)
├── pipeline/                          Photo + video generation pipeline
│   ├── pipeline.py                    Photo generation entry point
│   ├── prompt_bank.py                 Prompt templates, job builder (v3)
│   ├── wavespeed_i2v_client.py        Image-to-video client
│   └── alina_video_guide.md           Video prompt style guide
├── scripts/                           Utility entry points
│   ├── run_tiktok.py                  Batch TikTok generation CLI
│   ├── open_server.py                 Server launcher
│   ├── open_dashboard.py              Dashboard viewer
│   ├── save_meta.py                   Meta.json saver
│   ├── update_config.py               OpenCode model-list updater (external)
│   └── backfill_prompts.py            Rebuild .prompt files from meta.json
├── docs/                              Style guides + identity reference
│   ├── alina_style_guide.md           Photo prompt style guide (Alina)
│   └── wavespeed_identity_alina.md    Identity file (name, avatar URL, API key)
├── outputs/                           Generated media in YYYY-MM-DD/photos/ or /videos/
└── hot-take-influencer/               Influencer workflow project
```

## Active Components (built & working)

### Web UI (`webui/static/`)
- **Top nav pill**: `position: fixed; top: 24px`, glassmorphism. Contains: brand "OFM", balance pill, Live indicator, **API nav trigger** (dot · user · balance · caret ▽), settings gear, dark mode toggle
- **API nav trigger**: Click toggles centered modal popup showing all WaveSpeed accounts with balances, editable names, status indicators, and Add New Provider button. ESC, outside-click, re-click closes. No page layout shift.
- **API status checking**: `checkApiStatus()` polls `/api/settings/key/status` every 30s with 10s AbortController timeout. AbortError → invalid dot + auto-retry.
- **Settings drawer**: Right-slide panel for API key management (add/remove/rename accounts, set active)
- **Generation panel**: Vibe/Camera/Lighting/Outfit/Time/Count controls, Generate button
- **Outputs table**: Grouped by date, hover preview, fullscreen, caption edit, download, delete
- **Balance display**: Per-account and total balance, auto-refresh every 60s

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

### 2026-08-04 — Settings tab: identity management + prompt banks + presets

**identity in settings** ✓ — `core/config.py`: `get_identity()`/`set_identity()` read/write `settings.json["identity"] = {name, avatar_url}` (auto-migrates from `docs/wavespeed_identity_alina.md`). `pipeline/pipeline.py` `_load_avatar_url()` reads identity first. `webui/server.py`: GET/POST `/api/settings/identity`, POST `/api/settings/identity/upload` (multipart, 5MB max, image/* only; parse BEFORE `_read_body()`). Toolbar gains `.settings-nav-trigger` (rightmost); `#settings-modal` with avatar preview, URL input, drag-drop upload zone, Save/Done. `style.css` `.settings-*` styles at EOF.

**local upload → public URL** ✓ — `_handle_identity_upload()` saves local copy to `outputs/identity/` AND auto-publishes via `WaveSpeedClient.upload_file()` → public cloudfront URL stored as `avatar_url` (required — WaveSpeed API needs public reference image, local paths fail). Graceful fallback + warning if publish fails. Frontend rejects non-http(s) URLs in URL field.

**custom prompt banks** ✓ — `core/prompt_banks.py`: banks `{id, name, description, pools}` + presets `{id, name, config}` persisted under `settings.json["prompt_banks"]`/`["presets"]`. `pipeline/prompt_bank.py` `build_jobs_multi(..., bank=None)` overrides pools via `_resolve_pool()` (lists + string pools: IDENTITY_LOCK, negatives). `webui/server.py`: `/api/settings/banks/{create,update,delete,view}`, `/api/settings/presets/{create,delete}`; `/api/prompts/generate` accepts `bank_id`, unwraps `found.get("pools")`. Generation panel gains `#bank-select` + preset row (save/load/delete) in index.html/app.js; `.bank-select`/`.preset-row` CSS.

**verified** ✓ — py_compile + node --check clean; live server: bank CRUD, preset CRUD, gen-with-bank uses custom pool, upload returns public cloudfront URL, mocked e2e confirmed avatar_url flows `get_identity()` → `_load_avatar_url()` → `mode_photo` → `batch_generate(avatar_url)` → WaveSpeed `"images":[url]`. Test artifacts cleaned; settings.json identity restored to real ibb.co URL.

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

### 2026-07-31 — API selector modal simplification (check marks only)

**rename removed** ✓ — `pipeline-tiktok/static/app.js`: `.provider-name` in `loadApiProviderList()` no longer has `onclick="startRenameApi(...)"` / `title="Click to rename"`. Deleted the `startRenameApi()` function entirely (dead code). Settings drawer rename (`startRename`) preserved.

**hover-reveal removed** ✓ — `.provider-key` in the modal no longer carries `data-full` / `title="Hover to reveal"`; keys stay masked. Deleted the document-level `mouseover`/`mouseout` reveal delegation.

**check-marks-only** ✓ — `pipeline-tiktok/static/style.css`: replaced `.provider-radio` circle buttons with `.provider-check` (plain 28px icon button, no circle border, `svg` always visible). Active = emerald `var(--accent)` check (disabled, default cursor); inactive = gray `var(--fg3)` check (pointer, hover → emerald + subtle tint). Responsive block updated `.provider-radio` → `.provider-check`.

**key/name affordances** ✓ — `#api-provider-list .provider-name` dropped `cursor: text`; `.provider-key` dropped `cursor: help` + `:hover` color shift.

**verified** ✓ — `node --check` clean; live server serves updated app.js (no `startRenameApi`) / style.css (no `provider-radio`); `/api/settings/wavespeed/accounts` returns 4 accounts, `captlessgaming` active.

### 2026-07-31 — API selector modal redesign + toolbar label sync

**selected-account state** ✓ — `pipeline-tiktok/static/app.js`: new `_selectedAccount` / `_lastIdentity` / `_lastApiCount` globals + `updateApiLabel()` sets `#api-user` with priority: `_selectedAccount` → identity → `N API(s)` → 'No API keys'. `checkApiStatus()` no longer writes the label directly (only dot + balance); it clears stale `_selectedAccount` when the account disappears and falls back to `active`. `loadApiProviderList()` + `confirmSwitchApi()` set `_selectedAccount` and refresh the label. Toolbar now shows the modal account name (e.g. `captlessgaming`), NOT the API identity (`Alina Sky`).

**modal table redesign** ✓ — `pipeline-tiktok/static/style.css` `#api-provider-list`: rows 56px min-height (14px/16px padding, 12px gap); selected row gets 3px emerald left accent bar + `rgba(5,150,105,.05)` tint; account name Geist 14px/500, balance + API key JetBrains Mono 12px (balance tabular-nums, right-aligned 80px); API key masked `••••••••abcd` with hover-reveal (`data-full` + document-level mouseover/mouseout delegation); status = 6px colored dot + label (green #4caf50 / red #dc2626); actions 28px — radio/checkmark (`_checkSvg`) for active, 28px circle radio to switch, X `_delSvg2` for delete with red hover. `.provider-header` uppercase 10px/16px.

**toolbar label type** ✓ — `.api-nav-user` → 14px/500 sans; `.api-nav-bal` → 12px JetBrains Mono tabular-nums.

**responsive** ✓ — `@media (max-width:600px)`: full-width modal, tightened row gaps/paddings, smaller columns.

**verified** ✓ — `node --check` clean; server serves `/`, `/static/app.js`, `/static/style.css`; `/api/settings/key/status` returns accounts + active label. Settings drawer intentionally unchanged.

### 2026-07-31 — Controls lock during generation

**controls-locked** ✓ — `pipeline-tiktok/static/style.css` + `app.js`: new `setControlsLocked(locked)` toggles `.controls-locked` class on `.gen-layout .card` (55% opacity) and disables all card inputs (Vibe/Camera/Lighting/Outfit/Time pills + count slider). Lock fires at top of `startPromptGeneration()` (immediately on Generate click, stays locked through prompt review → confirm → pipeline). Unlock lives inside `_resetBtn()`, covering every terminal path: success, error, stall-retry failure, and Cancel. Locked elements use `pointer-events: none` (normal arrow cursor, no not-allowed icon); pill hover states suppressed while locked.

### 2026-07-31 — Prompt preview equal-height fix

**equal-height panels** ✓ — `pipeline-tiktok/static/style.css` + `app.js`: `.gen-layout` uses `align-items: stretch`; new `syncPanelHeights()` measures `.gen-layout .card` offsetHeight and sets `.gen-preview` height to match (cleared <768px). Hooked on load, debounced resize, `document.fonts.ready`, and prompt-state transitions (startPromptGeneration/_resetPromptList). Text window expands to fill card via nested flex (preview → body → prompt-item → pre/textarea all `flex: 1`). `.gen-preview-actions` reserves `min-height: 44px` so buttons appearing don't shift layout. `#btn-photo` locked to `height: 44px` + ellipsis so polling text changes don't resize the card. Pre/textarea box models already identical → edit mode height-stable. Mobile: `.gen-preview` min 260px, body `max-height: 420px`.

### 2026-07-30 — Initial state capture

**connect-light-outfit-prompts** ✓ — `pipeline-photovideo/prompt_bank.py`: split LIGHTING/OUTFIT pools into style-keyed dicts (warm/cool/dimlit, fem/street/grunge/academia), expanded POSES 6→12, wired `lighting` + `outfit_style` params into `build_jobs_multi()`. ~60 new strings. 1 file.

**style guides added** ✓ — `alina_style_guide.md` (63 lines, photo prompts) + `pipeline-photovideo/alina_video_guide.md` (video prompts).

**scripts added** ✓ — `open_dashboard.py`, `update_meta.py`, `save_meta.py`, `update_config.py`.

**MCP dirs** ✓ — `.codegraph/` (code intelligence index), `.playwright-mcp/` (browser automation).

**outputs** ✓ — `outputs/2026-07-30/` (today), `outputs/alina_tiktok_b1/`, `outputs/tiktok_b1/`, `outputs/dashboard.html`.

### 2026-07-30 — OpenSlimedit installed

**openslimedit** ✓ — Added `"openslimedit@latest"` to `~/.config/opencode/opencode.jsonc` plugin array. Reduces token usage by ~25-45% via tool description compression, compact read output, and line-range edit expansion. Zero config, activates on next OpenCode restart.

### 2026-07-30 — Taste-skill installed + frontend redesign

**taste-skill** ✓ — Installed `design-taste-frontend`, `redesign-existing-projects`, `high-end-visual-design`, `minimalist-ui` skills to `.claude/skills/`. Agents should load relevant skill when working on the OFM frontend.

**frontend redesign** ✓ — Applied taste-skill audit fixes: swapped accent from AI-purple indigo (`#6366f1`) to deep emerald (`#059669`), removed outer glow on CTAs, added spring cubic-bezier transitions, cleaned up 25+ lines of dead legacy CSS, added meta tags + SVG favicon + skip-to-content link, fixed broken textarea tag, added tabular-nums on balance display.

### 2026-07-30 — Cleanup + Codemap

**cleanup** ✓ — Deleted 34 generated promptbank_*.json files, test prompts, empty logs, old batch output dirs (alina_tiktok_b1, tiktok_b1), __pycache__ dirs (5 locations), outputs/dashboard.html, broken .codegraph junction.

**scripts moved** ✓ — Moved open_server.py, open_dashboard.py, save_meta.py, update_config.py from root to scripts/. Fixed path references in open_server.py/open_dashboard.py (one level up for __file__).

**.gitignore** ✓ — Created with excludes for __pycache__, .env, outputs, fonts/*.ttf, logs, OS/IDE files.

**codemap** ✓ — Initialized .slim/codemap.json tracking 43 files. Generated 9 codemap.md files (root, core, pipeline-tiktok, static, pipeline-photovideo, wavespeed-batch-api, hot-take-influencer, hot-take-influencer/scripts, scripts). Added Repository Map section to AGENTS.md. Next sessions load codemap instead of scanning 100+ junk files.

### 2026-07-30 — OpenCode Web redesign

**style.css full rewrite** ✓ — Warm monochrome palette (`#141413` dark / `#f4f2ee` light), removed all `backdrop-filter`/glassmorphism, Geist + JetBrains Mono via Google Fonts `@import`, consistent `border-radius: 6px`/`8px` across all elements, flat surfaces with 1px borders, new `.toolbar`/`.card`/segmented control styles, amber-tinted ambient glow.

**index.html restructured** ✓ — `<nav class="top-nav">` → `<header class="toolbar">` (fixed full-width, 48px), 3-bar SVG brand mark, removed `panel-shell`/`panel-core` nesting → single `<div class="card">`, theme-color updated to `#141413`.

**app.js updated** ✓ — `.top-nav` → `.toolbar` selector, padding `120px` → `64px` for new toolbar height.

**codemap updated** ✓ — Reflected static file changes in codemap.

### 2026-07-30 — Prompt Used inline + backfill

**server moved to root** ✓ — Moved `pipeline-tiktok/server.py` → `server.py`. Auto-opens browser on start. Run: `py server.py`.

**Prompt inline toggle** ✓ — Replaced Description labels + modal popup with clickable "Prompt Used" that toggles an inline `<pre>` box preserving exact prompt formatting. Deleted 60+ lines of orphaned modal CSS/HTML/JS.

**backfill_prompts.py** ✓ — `scripts/backfill_prompts.py` scans all `outputs/*/meta.json`, parses labels (`"scene · pose"`), reconstructs full prompts via deterministic seed from stem hash using `prompt_bank` pools. 38 entries backfilled across 5 existing meta.json files.

**companion .prompt files** ✓ — `pipeline-photovideo/pipeline.py` saves `{stem}.prompt` alongside each image on every batch generation. `server.py` `_collect()` reads `.prompt` files as priority source over meta.json. Future outputs automatically get prompt data.

**codemap updated** ✓ — Updated 6 codemap.md files (root, pipeline-tiktok, static, pipeline-photovideo, scripts). Now tracking 44 files in `.slim/codemap.json`.

### 2026-07-31 — Taste-skill table redesign + cleanup

**premium table redesign** ✓ — Merged `pr`+`cp` columns into single `info` column: caption (2-line clamp, 500 weight) + meta row (Prompt Used monospace link · format badge pill). Row padding 6px→10px, hover gets 2px accent left border, row separators via 1px border, action buttons 26px→28px with 4px gaps, batch title 600 weight.

**Guidance Scale removed** ✓ — Stripped from prompt modal HTML + JS + hidden data attributes.

**checklist/used system removed** ✓ — Deleted `toggleStatus`, checkbox column, `batchUsed`/`b-used` spans, `tr-used` CSS, `b-spacer` CSS. Clean rows, no usage tracking.

**caption auto-refresh** ✓ — `saveEdit()` now calls `refreshOutputs()` after saving caption.

**auto-close tab on shutdown** ✓ — `/api/ping` endpoint + JS polling every 3s. When server goes down, shows "Server stopped. Close this tab." message.

### 2026-07-30 — Cleanup + Codemap

**cleanup** ✓ — Deleted 34 generated promptbank_*.json files, test prompts, empty logs, old batch output dirs (alina_tiktok_b1, tiktok_b1), __pycache__ dirs (5 locations), outputs/dashboard.html, broken .codegraph junction.

**scripts moved** ✓ — Moved open_server.py, open_dashboard.py, save_meta.py, update_config.py from root to scripts/. Fixed path references in open_server.py/open_dashboard.py (one level up for __file__).

**.gitignore** ✓ — Created with excludes for __pycache__, .env, outputs, fonts/*.ttf, logs, OS/IDE files.

**codemap** ✓ — Initialized .slim/codemap.json tracking 43 files. Generated 9 codemap.md files (root, core, pipeline-tiktok, static, pipeline-photovideo, wavespeed-batch-api, hot-take-influencer, hot-take-influencer/scripts, scripts). Added Repository Map section to AGENTS.md. Next sessions load codemap instead of scanning 100+ junk files.

### 2026-07-30 — OpenCode Web redesign

**style.css full rewrite** ✓ — Warm monochrome palette (`#141413` dark / `#f4f2ee` light), removed all `backdrop-filter`/glassmorphism, Geist + JetBrains Mono via Google Fonts `@import`, consistent `border-radius: 6px`/`8px` across all elements, flat surfaces with 1px borders, new `.toolbar`/`.card`/segmented control styles, amber-tinted ambient glow.

**index.html restructured** ✓ — `<nav class="top-nav">` → `<header class="toolbar">` (fixed full-width, 48px), 3-bar SVG brand mark, removed `panel-shell`/`panel-core` nesting → single `<div class="card">`, theme-color updated to `#141413`.

**app.js updated** ✓ — `.top-nav` → `.toolbar` selector, padding `120px` → `64px` for new toolbar height.

**codemap updated** ✓ — Reflected static file changes in codemap.

### 2026-07-30 — Prompt Used inline + backfill

**server moved to root** ✓ — Moved `pipeline-tiktok/server.py` → `server.py`. Auto-opens browser on start. Run: `py server.py`.

**Prompt inline toggle** ✓ — Replaced Description labels + modal popup with clickable "Prompt Used" that toggles an inline `<pre>` box preserving exact prompt formatting. Deleted 60+ lines of orphaned modal CSS/HTML/JS.

**backfill_prompts.py** ✓ — `scripts/backfill_prompts.py` scans all `outputs/*/meta.json`, parses labels (`"scene · pose"`), reconstructs full prompts via deterministic seed from stem hash using `prompt_bank` pools. 38 entries backfilled across 5 existing meta.json files.

**companion .prompt files** ✓ — `pipeline-photovideo/pipeline.py` saves `{stem}.prompt` alongside each image on every batch generation. `server.py` `_collect()` reads `.prompt` files as priority source over meta.json. Future outputs automatically get prompt data.

**codemap updated** ✓ — Updated 6 codemap.md files (root, pipeline-tiktok, static, pipeline-photovideo, scripts). Now tracking 44 files in `.slim/codemap.json`.