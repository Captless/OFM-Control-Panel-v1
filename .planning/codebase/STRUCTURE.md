# Codebase Structure

**Analysis Date:** 2026-08-05

## Directory Layout

```
OFM/
├── core/                      # Shared config, persistence, errors, text
│   ├── config.py              # settings.json CRUD, identity, accounts
│   ├── prompt_banks.py        # Custom prompt bank + preset persistence
│   ├── errors.py              # WaveSpeedError
│   ├── daybatch.py            # day_path() → outputs/YYYY-MM-DD/<subdir>
│   ├── text_generator.py      # Alt-girl paragraph text
│   ├── settings.json          # LIVE state (gitignored — keys inside)
│   └── settings.json.example  # Tracked template (masked keys)
├── api/                       # WaveSpeed REST client
│   └── wavespeed_client.py    # generate/enhance/batch/upload/balance/validate
├── webui/                     # Web control panel
│   ├── server.py              # HTTP server (port 8000) + REST API (824 lines)
│   ├── dashboard.py           # Static dashboard generator (423 lines)
│   ├── wavespeed_tiktok_client.py  # 3-stage TikTok pipeline client (543 lines)
│   ├── activity.json          # Run history (runtime, gitignored)
│   ├── static/                # SPA: index.html · app.js · style.css
│   └── fonts/                 # TikTok Sans TTFs (gitignored binaries)
├── pipeline/                  # Generation pipelines
│   ├── pipeline.py            # Photo pipeline CLI (--prompts <json>)
│   ├── prompt_bank.py         # Pool data + build_jobs_multi (v3)
│   ├── wavespeed_i2v_client.py# Image→video client
│   ├── alina_video_guide.md   # Video prompt style guide
│   └── *.json                 # Runtime: promptbank_*, edited_prompts_*, checkpoint_* (gitignored)
├── scripts/                   # Utility entry points
│   ├── run_tiktok.py          # Batch TikTok video CLI
│   ├── open_server.py         # Launch server + open browser
│   ├── open_dashboard.py      # Dashboard viewer
│   ├── save_meta.py           # meta.json writer
│   ├── backfill_prompts.py    # Rebuild .prompt files from meta.json
│   └── update_config.py       # OpenCode model-list updater (external)
├── docs/                      # Style guides + legacy identity
│   ├── alina_style_guide.md
│   └── wavespeed_identity_alina.md  # Legacy identity (migrated to settings.json)
├── outputs/                   # Generated media (gitignored)
│   └── YYYY-MM-DD/photos|videos/   # PNG/MP4 + meta.json + {stem}.prompt/.txt
├── hot-take-influencer/       # Separate mini-project (own client, 211 lines)
├── .github/workflows/ci.yml   # GitHub Actions: py_compile + imports + node --check
├── .env                       # Legacy env config (gitignored — do not read)
├── AGENTS.md                  # Agent guide (tech stack, fixes, history)
├── codemap.md                 # Repository atlas
└── .planning/                 # GSD state (this doc lives in codebase/)
```

## Directory Purposes

**`core/`:**
- Purpose: shared backend logic used by server, pipelines, and scripts
- Contains: settings persistence (`config.py`), bank persistence (`prompt_banks.py`), exception type (`errors.py`), path helper (`daybatch.py`), text generator (`text_generator.py`)
- Key files: `config.py` (identity migration from markdown, multi-account key store), `settings.json` (live state)
- Note: `core/settings.json` gitignored; `core/settings.json.example` is the tracked reference

**`api/`:**
- Purpose: reusable WaveSpeed REST client (single module)
- Contains: `wavespeed_client.py` — `WaveSpeedClient` (urllib + requests), `batch_generate` with checkpoint/lock, SSE streaming, media upload
- Key files: `wavespeed_client.py`

**`webui/`:**
- Purpose: web control panel — server + SPA + video pipeline client
- Contains: REST API server (`server.py`), static dashboard generator (`dashboard.py`), TikTok 3-stage client (`wavespeed_tiktok_client.py`), frontend (`static/`), run history (`activity.json`), fonts
- Key files: `server.py`, `static/app.js`, `static/index.html`, `static/style.css`

**`pipeline/`:**
- Purpose: generation pipelines + prompt data
- Contains: photo pipeline CLI (`pipeline.py`), prompt pools + job builder (`prompt_bank.py`), i2v client (`wavespeed_i2v_client.py`), style guide (`alina_video_guide.md`), runtime job JSONs
- Key files: `pipeline.py`, `prompt_bank.py`
- Note: 20+ `edited_prompts_*.json` and `promptbank_*.json` runtime artifacts present (gitignored) — regenerated on demand

**`scripts/`:**
- Purpose: CLI utility entry points
- Contains: `run_tiktok.py` (video batch), `open_server.py` / `open_dashboard.py` (launchers), `save_meta.py`, `backfill_prompts.py`, `update_config.py` (external OpenCode model-list updater)

**`outputs/`:**
- Purpose: generated media store (gitignored)
- Contains: `YYYY-MM-DD/photos/` (PNG 1K 9:16), video dirs (MP4), `meta.json` per date, `{stem}.prompt` companion files, `{stem}.txt` captions, `identity/` (uploaded avatars)

**`hot-take-influencer/`:**
- Purpose: separate opinion/talking-head persona workflow project (own `scripts/wavespeed_client.py`, 211 lines, its own codemap + SKILL.md)
- Not wired into main server

**`.claude/skills/`, `.slim/`, `.playwright-mcp/`, `.planning/`:**
- Purpose: agent tooling — design skills, codemap state, browser automation, GSD workflow state. Not application code.

## Key File Locations

**Entry Points:**
- `webui/server.py`: HTTP server (port 8000) — serves `/` + `/static/*` + REST API; kills stale port, opens browser
- `scripts/open_server.py`: launcher for the server (subprocess)
- `pipeline/pipeline.py`: photo pipeline CLI (`--prompts <json>` required)
- `scripts/run_tiktok.py`: TikTok batch video CLI (`py scripts/run_tiktok.py 5 [--fast]`)
- `pipeline/prompt_bank.py`: job builder CLI (`py pipeline/prompt_bank.py 3 [vibe] [camera] [tod]`)
- `webui/dashboard.py`: dashboard generator (`--all`, `--serve`)

**Configuration:**
- `core/settings.json` (live, gitignored): API key accounts, active account, identity, prompt banks, active bank, presets
- `core/settings.json.example` (tracked): masked template
- `.github/workflows/ci.yml`: CI config (Python 3.11, py_compile, import tests, node --check)
- `.gitignore`: excludes `__pycache__`, `.env`, `outputs/`, runtime pipeline JSONs, `webui/fonts/*.ttf`, `core/settings.json`, `webui/activity.json`

**Core Logic:**
- `webui/server.py`: REST routing (`do_GET`/`do_POST` path matching), `_collect()` output aggregation, `_start_pipeline` subprocess orchestration, `_handle_identity_upload` multipart parsing
- `api/wavespeed_client.py`: `WaveSpeedClient.batch_generate` — concurrency, checkpoint resume, `.batch.lock`
- `pipeline/prompt_bank.py`: `build_jobs_multi` — pool randomization, bank override resolution (`_resolve_pool`)
- `pipeline/pipeline.py`: `mode_photo` — key/avatar loading, batch orchestration, meta merge
- `core/config.py`: settings persistence + identity migration + account CRUD

**Testing:**
- None (no test files). Verification is: `py_compile` (CI), import smoke test (CI), `node --check` (CI), manual live-server checks. No pytest/vitest/jest config exists.

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (`wavespeed_client.py`, `prompt_bank.py`, `run_tiktok.py`)
- Frontend: lowercase kebab (`index.html`, `style.css`, `app.js` — static dir)
- Runtime job JSONs: `promptbank_{vibe}_{camera}_{lighting}_{time}_{outfit}_{count}[_{bank_id}].json` (`webui/server.py:643-646`), `edited_prompts_{uuid8}.json`, `checkpoint_photo.json` / `checkpoint.json`
- Style docs: `*_guide.md` (`alina_style_guide.md`, `alina_video_guide.md`)

**Directories:**
- `kebab-case` for app dirs (`hot-take-influencer`); single-word `core`/`api`/`webui`/`pipeline`/`scripts`/`docs`/`outputs`
- Output date dirs: `YYYY-MM-DD` (ISO), with `photos/` or `videos/` subdirs

**Generated media:**
- Photos: `{NNN:03d}_{md5(time.time())6}.png` (`pipeline/prompt_bank.py:388-389`) — timestamp hash prevents same-day collisions
- Videos: `{NNN:03d}_tiktok.mp4` (`scripts/run_tiktok.py:80`)
- Companion files share stem: `{stem}.prompt` (prompt text), `{stem}.txt` (caption)

**API endpoints:**
- REST paths grouped: `/api/run/*` (execution), `/api/settings/*` (CRUD), `/api/balance/*`, `/api/prompts/*`, `/api/progress`, `/api/outputs`, `/api/caption/*`, `/api/media/*` — see endpoint table in `webui/server.py` (GET `do_GET`, POST `do_POST`)

## Where to Add New Code

**New Feature (endpoint):**
- Primary code: `webui/server.py` — add route branch in `do_GET` (`:406`) or `do_POST` (`:578`); return via `self._json(data, status)`
- Frontend: `webui/static/app.js` — add `fetch`/`api()` call + UI in `index.html` + styles in `style.css`
- Test: none (add py_compile check to `.github/workflows/ci.yml` if new module)

**New Component/Module:**
- Implementation: put in the layer that owns it —
  - shared settings/persistence → `core/` (expose via `core/config.py` or new module, import from `core.`)
  - WaveSpeed API logic → `api/` (or subclass existing client)
  - pipeline/job logic → `pipeline/`
  - server-only orchestration → `webui/`
- Wiring: add `sys.path` insert only if module lives outside existing package dirs; prefer package imports (`from core.x import y`) since `__init__.py` files exist in `webui/`, `pipeline/`, `api/`, `core/`

**Utilities:**
- Shared helpers: `core/` (e.g., `daybatch.py` day_path, `errors.py` WaveSpeedError)
- Standalone CLI: `scripts/` — follow `run_tiktok.py` pattern: `BASE = dirname(dirname(abspath(__file__)))`, `sys.path.insert(0, BASE)`, argparse `main()`

**New prompt content:**
- Pools: `pipeline/prompt_bank.py` (list or style-keyed dict, e.g. `OUTFIT_TOPS_POOLS`, `LIGHTING_POOLS`); register override keys in `core/prompt_banks.py:OVERRIDABLE_POOLS` if users should be able to override them via the settings tab
- Presets/UI choices: `list_presets()` in `pipeline/prompt_bank.py:466`

**New output type:**
- Write into `outputs/YYYY-MM-DD/<subdir>/` via `core/daybatch.py:day_path(subdir=...)`; `_collect()` in `webui/server.py` auto-discovers any `*.png`/`*.jpg`/`*.mp4` (extend suffix list at `:200` for new formats)

## Special Directories

**`outputs/`:**
- Purpose: generated media + metadata
- Generated: Yes (runtime)
- Committed: No (`.gitignore:10`)

**`webui/fonts/`:**
- Purpose: TikTok Sans font binaries for FFmpeg drawtext overlay
- Generated: No (downloaded assets)
- Committed: No (`.gitignore:18-20`)

**`webui/static/`:**
- Purpose: SPA assets
- Generated: No
- Committed: Yes

**`pipeline/*.json` (promptbank_*, edited_prompts_*, checkpoint_*):**
- Purpose: runtime job/checkpoint artifacts
- Generated: Yes (every generation run)
- Committed: No (`.gitignore:13-15`)

**`.planning/`, `.slim/`, `.claude/`, `.playwright-mcp/`:**
- Purpose: GSD workflow state, codemap index, agent skills, browser automation
- Generated: Yes (tooling)
- Committed: `.planning/` yes (GSD), `.slim/deepwork/` no (`.gitignore:35`)

---

*Structure analysis: 2026-08-05*
