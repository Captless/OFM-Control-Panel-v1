<!-- refreshed: 2026-08-05 -->
# Architecture

**Analysis Date:** 2026-08-05

## System Overview

```text
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (SPA, vanilla)                    │
│            `webui/static/index.html` · `app.js` · `style.css`     │
└──────────────────────────────┬───────────────────────────────────┘
                               │ fetch() JSON, /api/*, no CORS issue (same origin)
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│               CONTROL PLANE — HTTP Server (port 8000)             │
│                    `webui/server.py` (ThreadingHTTPServer)         │
│   REST API handlers · prompt building · account/identity/banks    │
│   `_pipeline_runs` state · balance cache · activity log           │
└───────────────┬──────────────────────────────┬────────────────────┘
                │ subprocess Popen             │ in-process calls
                ▼                              ▼
┌───────────────────────────────┐   ┌────────────────────────────────────┐
│  WORKERS (subprocess CLI)     │   │  SHARED CORE + CLIENTS              │
│  `pipeline/pipeline.py`       │   │  `core/config.py` settings CRUD     │
│  `scripts/run_tiktok.py`      │   │  `core/prompt_banks.py` banks       │
│  `webui/dashboard.py`         │   │  `api/wavespeed_client.py`          │
│  progress via @P stdout lines │   │  `pipeline/wavespeed_i2v_client.py` │
└───────────────┬───────────────┘   │  `webui/wavespeed_tiktok_client.py` │
                │                   └───────────────┬────────────────────┘
                ▼                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│   EXTERNAL — WaveSpeed AI REST API `api.wavespeed.ai/api/v3`     │
│   + FFmpeg (drawtext) + public image hosting                     │
└──────────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────┐
│   STORE — `outputs/YYYY-MM-DD/photos|videos/` + `core/settings.json` │
└──────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| HTTP server | Serve SPA + REST API, run pipeline subprocess, aggregate outputs | `webui/server.py` |
| Frontend SPA | Controls, prompt config, progress polling, media browser | `webui/static/app.js` + `index.html` |
| Settings/config | API key accounts, identity, banks, presets persistence | `core/config.py`, `core/prompt_banks.py` |
| WaveSpeed image client | Submit/poll/SSE image gen, enhance, batch, media upload | `api/wavespeed_client.py` |
| Photo pipeline | CLI entry: load jobs → batch generate → save PNGs + meta | `pipeline/pipeline.py` |
| Prompt bank | Pool data + job builder (v3, camera modes, bank overrides) | `pipeline/prompt_bank.py` |
| i2v client | Image→video (kling) poll client | `pipeline/wavespeed_i2v_client.py` |
| TikTok client | 3-stage frame→video→FFmpeg overlay batch client | `webui/wavespeed_tiktok_client.py` |
| Dashboard | Static dashboard generator from outputs | `webui/dashboard.py` |
| Utils | Launchers, meta saver, backfill, config updater | `scripts/` |
| Errors | Shared `WaveSpeedError` (code/status) | `core/errors.py` |
| Day path | `outputs/YYYY-MM-DD/<subdir>` helper | `core/daybatch.py` |
| Text generator | Alt-girl paragraph text for TikTok overlays | `core/text_generator.py` |

## Pattern Overview

**Overall:** Local web control plane + subprocess worker + external AI API. Monolithic stdlib HTTP server serving both SPA and REST API; generation runs as a child process whose stdout is parsed into a progress state dict polled by the browser. Zero framework, file-based state.

**Key Characteristics:**
- Sync HTTP handlers; long-running work delegated to `subprocess.Popen` daemon threads — HTTP requests never block on generation
- File system as state: `settings.json` (read whole file per call), `meta.json`, checkpoint JSONs, lock files
- Progress protocol `@P <stage>|<detail>` over subprocess stdout (`webui/server.py:291-317`)
- `sys.path.insert(0, ...)` path bootstrapping at import time in every runnable module
- Threads: one per HTTP request (`ThreadingHTTPServer`), daemon pipeline threads, `ThreadPoolExecutor` (batch gen: max 3-5 workers), `_state_lock` for run state

## Layers

**Frontend (SPA):**
- Purpose: user control panel
- Location: `webui/static/` (index.html, app.js, style.css)
- Contains: generation controls, API account modal, settings drawer, outputs table, theme toggles
- Depends on: REST API endpoints (35+ `fetch`/`api()` calls in `app.js`), nothing else — no CDN, no framework
- Used by: browser via `/` and `/static/*`

**Control Plane (server):**
- Purpose: REST API + static serving + orchestration
- Location: `webui/server.py`
- Contains: `Handler(BaseHTTPRequestHandler)` with `do_GET`/`do_POST` routing (path string matching), `_get_balance` (60s cache), `_collect()` output aggregation, `_start_pipeline`, `_handle_identity_upload` (multipart parser), `_log_activity`
- Depends on: `core/config.py`, `core/prompt_banks.py`, `pipeline/prompt_bank.py`, `api/wavespeed_client.py`
- Used by: browser; `scripts/open_server.py`

**Core:**
- Purpose: shared config, persistence, text, errors
- Location: `core/`
- Contains: settings CRUD + identity migration (`config.py`), bank/preset persistence (`prompt_banks.py`), `WaveSpeedError` (`errors.py`), `day_path()` (`daybatch.py`), paragraph generator (`text_generator.py`)
- Depends on: stdlib only (lazy import of client in `test_wavespeed_account`)
- Used by: server, both pipelines, scripts

**API Clients:**
- Purpose: WaveSpeed REST wrappers
- Location: `api/wavespeed_client.py`, `pipeline/wavespeed_i2v_client.py`, `webui/wavespeed_tiktok_client.py`
- Contains: submit/poll/SSE, batch with checkpoint+lock, upload, balance, validate; i2v; 3-stage TikTok
- Depends on: `core/errors.py`, `requests`, stdlib
- Used by: server (`WaveSpeedClient`), pipeline, scripts

**Pipelines:**
- Purpose: CLI generation entry points
- Location: `pipeline/pipeline.py` (photo), `scripts/run_tiktok.py` (video), `pipeline/prompt_bank.py` (job building)
- Contains: job loading, key/avatar loading, batch orchestration, meta merge, progress printing
- Depends on: clients, `core.daybatch`, `core.config`, `core.text_generator`
- Used by: server subprocess, direct CLI

**Output Store:**
- Purpose: generated media + metadata
- Location: `outputs/` (gitignored)
- Contains: `YYYY-MM-DD/photos/*.png`, video dirs, `meta.json`, `{stem}.prompt`, `{stem}.txt`, `identity/`, checkpoint JSONs

## Data Flow

### Primary Request Path (photo generation)

1. Browser POSTs selections → `/api/prompts/generate` (`webui/server.py:620`) with vibe/camera/lighting/time/outfit/count/bank_id
2. Server calls `build_jobs_multi(count, ..., bank=pools)` (`pipeline/prompt_bank.py:328`) — randomizes pools, builds `{prompt, filename, labels, negative_prompt, guidance_scale}` jobs; filename `{NNN}_{md5(time)6}.png`
3. Jobs JSON written to `pipeline/promptbank_*.json` (or `edited_prompts_*.json` for raw lists); returns jobs to browser
4. Browser shows preview → POST `/api/run/photo` with jobs list (`webui/server.py:603`)
5. Server writes jobs JSON again, calls `_start_pipeline` → `subprocess.Popen([python, pipeline/pipeline.py, --prompts, file])` (`webui/server.py:320-390`)
6. `pipeline.py:mode_photo` (`pipeline/pipeline.py:80`) loads active key from `settings.json`, avatar URL from identity, `day_path(subdir="photos")`, then `WaveSpeedClient.batch_generate(..., max_concurrent=3, stream=True, checkpoint_path)`
7. `batch_generate` (`api/wavespeed_client.py:274`): acquire `.batch.lock` (O_EXCL, 10-min stale), ThreadPoolExecutor → `_generate_one`: `generate()` → SSE stream (`/google/nano-banana-2/edit/stream`) with polling fallback → optional `enhance()` 4x → `download()` to `outputs/YYYY-MM-DD/photos/`; checkpoint JSON updated per success; explicit-flag → cancel remaining
8. On success `pipeline.py` merges `meta.json` (`_merge_meta`) + writes `{stem}.prompt` companion files
9. Browser polls `/api/progress?run_id=` every ~1-2s (`app.js:1074`); server parses `@P` stdout lines into `_pipeline_runs[run_id]`; terminal states (`@P failed|...`) set `done`
10. UI refreshes outputs via `/api/outputs` → `_collect()` (`webui/server.py:196`) groups media by date, reads meta/.prompt/.txt, dedupes stems

### Balance Display

1. Browser polls `/api/balance` (60s) and `/api/balance/total`
2. `_get_balance(account_label=None)` (`webui/server.py:145`) — cache 60s for active; per-label bypasses cache; missing key → 0.0; errors → 0.0
3. `WaveSpeedClient.get_balance()` → `GET /balance`

### Identity Avatar Upload

1. POST multipart → `/api/settings/identity/upload` (`webui/server.py:580`)
2. Raw body parsed BEFORE `_read_body()` (manual boundary splitter `_extract_file_part`); 5MB max, image/* only
3. Saved to `outputs/identity/<uuid12>.<ext>`; then `WaveSpeedClient.upload_file()` → public cloudfront URL; fallback warning if upload fails
4. `set_identity(avatar_url=...)` persists to `settings.json`
5. Flow downstream: `get_identity()` → `pipeline.py:_load_avatar_url()` → `batch_generate(avatar_url)` → WaveSpeed `"images":[url]`

### TikTok Video Path (CLI)

1. `scripts/run_tiktok.py <n> [--fast]` builds jobs from `core/text_generator` topics
2. `WaveSpeedTikTokClient.batch_generate` (`webui/wavespeed_tiktok_client.py:494`) — 3 stages per job: `generate_frame` (nano-banana-2/edit) → `generate_video` (kling-v2.5-turbo-std) → FFmpeg `drawtext` paragraph overlay (`burn_paragraph_overlay`), cross-platform file locking (`msvcrt`/`fcntl`)
3. Outputs to `outputs/YYYY-MM-DD/`; `save_meta` + dashboard regen

**State Management:**
- File-based: `core/settings.json` is the single source of truth (rewritten whole on every mutation)
- In-memory: `_pipeline_runs` (module dict, pruned to 50 done runs), `_balance_cache` (60s), `HOMEPAGE_HTML` (loaded once at import), `activity.json` (last 50 entries)
- Concurrency guards: `_state_lock` around run state; `.batch.lock` O_EXCL file lock per output dir; stale lock cleanup at boot (`_clean_stale_locks`)

## Key Abstractions

**WaveSpeedClient** (`api/wavespeed_client.py`):
- Purpose: shared REST client for image gen/enhance/batch/upload/balance/validate
- Examples: used by `webui/server.py` (balance, validate-all, upload), `pipeline/pipeline.py`
- Pattern: single-class facade over `urllib.request` + `requests`; `_request()` normalizes errors into `WaveSpeedError`

**Job dict** (`pipeline/prompt_bank.py:391-399`):
- Purpose: canonical unit of generation work — `{prompt, filename, labels, video_prompt, negative_prompt, guidance_scale, duration}`
- Flow: built by `build_jobs_multi` → serialized to JSON file → consumed by `batch_generate` → summarized into `meta.json` by stem

**Prompt bank override composition**:
- Purpose: user banks partially override built-in pools
- Pattern: `_resolve_pool(name, default, bank)` (`pipeline/prompt_bank.py:317`) — bank dict wins over `get_builtin_pools()` default; whitelisted pool keys in `core/prompt_banks.py:OVERRIDABLE_POOLS`

**Progress protocol `@P`**:
- Purpose: subprocess → server progress channel
- Format: `@P <stage>|<detail>` (2 parts) or `@P failed|<error_type>|<detail>` (3 parts); `[n/total] message` lines for counters (`webui/server.py:291-317`)

## Entry Points

| Entry point | Location | Triggers | Responsibilities |
|-------------|----------|----------|------------------|
| Control server | `webui/server.py` (port 8000) | `py webui/server.py` / `scripts/open_server.py` | SPA + REST API, kills stale port process, opens browser |
| Photo pipeline | `pipeline/pipeline.py` | CLI `--prompts <json>`; server subprocess | Batch photo generation |
| TikTok batch | `scripts/run_tiktok.py` | CLI `<n> [--fast]` | Video generation + text overlay + meta |
| Dashboard | `webui/dashboard.py` | CLI `--all` / `--serve`; server `_run_dashboard` | Static dashboard HTML from outputs |
| Prompt bank | `pipeline/prompt_bank.py` | CLI `n [vibe] [camera] [tod]` | Generate + save promptbank JSON |
| Utils | `scripts/open_dashboard.py`, `scripts/save_meta.py`, `scripts/backfill_prompts.py`, `scripts/update_config.py` | CLI | Launchers, meta writes, prompt backfill, external OpenCode model-list updater |

## Architectural Constraints

- **Threading:** `ThreadingHTTPServer` — new thread per request (unbounded); generation runs in daemon threads that never outlive server; `ThreadPoolExecutor` for batch concurrency; no async anywhere
- **Global state:** `_pipeline_runs` dict + `_balance_cache` at module level in `webui/server.py`; `HOMEPAGE_HTML` loaded at import; settings read from disk on every access (no in-memory settings cache) — mutating code must write `settings.json` atomically-ish (read-modify-write)
- **Path bootstrap:** every runnable module inserts repo/`api`/`core`/`pipeline` dirs into `sys.path` at import time (`webui/server.py:32-41`, `pipeline/pipeline.py:18-21`, `scripts/run_tiktok.py:17-19`, lazy in `core/config.py:149-157`) — run scripts from repo root or rely on these inserts; adding a module to an existing package requires no path change, adding a new package does
- **Single active API key:** generation always uses `active_wavespeed_account` key; `webui/server.py` cache must be invalidated on account switch (`_balance_cache` reset at `:709`)
- **Port 8000 exclusivity:** server kills any process listening on 8000 at boot (Windows `netstat`/`taskkill` via `os.kill(pid, 9)`)
- **No auth:** server binds 0.0.0.0 with no authentication; `Access-Control-Allow-Origin: *` on JSON responses — LAN-accessible by design (personal tool)

## Anti-Patterns

### `sys.path.insert` hackery at import time

**What happens:** Every runnable module bootstraps its own import path (`webui/server.py:32`, `pipeline/pipeline.py:18-19`, `core/config.py:149-157`, `scripts/*`), sometimes lazily inside functions (`config.py:test_wavespeed_account`).
**Why it's wrong:** Fragile ordering — import order matters; shadowing risk (`prompt_bank` vs `prompt_banks` module names coexist and are easy to confuse); breaks if files move (the 2026-08-01 reorg required fixing all of them).
**Do this instead:** Run as installed packages (`python -m webui.server` with `__init__.py` present, which they now have), or add repo root to `sys.path` once in a single bootstrap module.

### File read-modify-write races on settings.json

**What happens:** `core/config.py:_load_settings()` reads the whole file, mutates, `_save_settings()` rewrites it. Concurrent HTTP threads (ThreadingHTTPServer) mutating accounts/banks/identity can interleave and lose writes.
**Why it's wrong:** Silent data loss under parallel requests (e.g., validate-all thread + account add).
**Do this instead:** A settings module-level lock or a single writer thread.

### Subprocess-based generation instead of in-process

**What happens:** `webui/server.py` spawns `pipeline.py` as a subprocess and reverse-parses its stdout.
**Why it's wrong:** Protocol fragility (`@P` parsing), extra process overhead, error messages tunneled as text.
**Do this instead:** Import `pipeline.pipeline` and run in a thread; keep stdout protocol only if subprocess isolation is deliberately required (crash containment).

### Mojibake in source comments

**What happens:** `webui/server.py` header comment and `# ──` section separators are mojibake (`â”€â”€`) — UTF-8 box characters decoded as Latin-1 at some point.
**Why it's wrong:** Readability, and it signals an encoding round-trip bug that can corrupt string literals if files are rewritten with the wrong encoding.
**Do this instead:** Keep source files strict UTF-8; fix the corrupted separators when editing nearby code.

### Duplicate/divergent client implementations

**What happens:** Three WaveSpeed clients with overlapping logic (`api/wavespeed_client.py` vs `pipeline/wavespeed_i2v_client.py` vs `webui/wavespeed_tiktok_client.py`); `core/config.py:IMAGE_MODEL` env default (`stable-diffusion-v1.5`) disagrees with client constant (`google/nano-banana-2/edit`); tiktok docstring model name disagrees with code.
**Why it's wrong:** A change to error handling or endpoint URL must be made in 3 places.
**Do this instead:** One base client class; subclasses only for model-specific payloads.

## Error Handling

**Strategy:** Hybrid — shared `WaveSpeedError(message, code, status)` (`core/errors.py`) raised by clients; server maps to HTTP 400/404/500 via `_json(data, status)`; pipeline CLI catches and prints `@P failed|...` then `sys.exit(1)`; batch failures collected per-job in `failed_list` with checkpoint resume.

**Patterns:**
- API error normalization: `WaveSpeedClient._request` raises `WaveSpeedError(f"HTTP {code}: ...", status=e.code)` on HTTPError; body `code` check; `poll()` distinguishes `explicit_content_flagged` / `generation_failed` / `polling_timeout` (`api/wavespeed_client.py:52-90`)
- Explicit content: marker match cancels whole batch (`api/wavespeed_client.py:325-328`), pipeline exits 1 with `explicit_content` error type
- HTTP handler: `_read_body()` JSON parse raises → 500 caught at call sites; path traversal guarded via `Path.resolve()` + `relative_to(OUTPUTS.resolve())` for caption/delete (`webui/server.py:663-665`, `679-681`)
- Client-side: `app.js` polling gets terminal shape on missing run ("run not found (server restarted?)") to stop infinite polling (`webui/server.py:468-475`)

## Cross-Cutting Concerns

**Logging:** Python `logging` in clients (debug); activity log JSON (50 entries) for user-visible history; server access log suppressed.
**Validation:** Server-side: identity upload (5MB, image/* MIME), caption/delete path containment, bank pool key whitelist (`core/prompt_banks.py:_sanitize_bank`), account label/key presence. Client-side: pill input validation, avatar URL http(s) check.
**Authentication:** None (local tool); API keys masked in UI responses; `.env`/`settings.json` gitignored.

---

*Architecture analysis: 2026-08-05*
