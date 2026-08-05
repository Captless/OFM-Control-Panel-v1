# External Integrations

**Analysis Date:** 2026-08-05

## APIs & External Services

**WaveSpeed AI REST API (primary):**
- Used for all image + video generation, balance, model validation, and binary media upload
- Base URL: `https://api.wavespeed.ai/api/v3` — defined in `api/wavespeed_client.py:17`, `pipeline/wavespeed_i2v_client.py:19`; `webui/wavespeed_tiktok_client.py:29-30` builds it as `https://api.wavespeed.ai` + `/api/v3`
  - Note: `AGENTS.md` / `codemap.md` document `api-ondemand.wavespeed.ai/api/v3` — actual code uses `api.wavespeed.ai`. Docs are stale.
- Auth: `Authorization: Bearer <wsk_live_...>` key per request. Keys stored in `core/settings.json["wavespeed_accounts"]` (label→key), selected via `active_wavespeed_account`
- SDK/Client: 3 hand-rolled clients (no official SDK):
  - `api/wavespeed_client.py` — `WaveSpeedClient`: image gen (`google/nano-banana-2/edit`), enhance (`wavespeed-ai/image-enhancer`), SSE stream gen, batch gen, media upload. Uses `urllib.request` + `requests` (SSE/upload only)
  - `pipeline/wavespeed_i2v_client.py` — `WaveSpeedI2VClient`: image-to-video (`kwaivgi/kling-v2.5-turbo-std/image-to-video`), poll-based
  - `webui/wavespeed_tiktok_client.py` — `WaveSpeedTikTokClient`: 3-stage TikTok pipeline (frame → video → FFmpeg overlay), `requests`-based
- Endpoints used:
  - `GET /balance` — account balance (`WaveSpeedClient.get_balance`)
  - `GET /models` — key validation (`WaveSpeedClient.validate`, 401 = bad key)
  - `POST /{model}` — submit async task, returns `{id}`
  - `GET /predictions/{id}/result` — poll task status; `status` ∈ completed/failed
  - `POST /{model}/stream` — SSE streaming generation (fallback to polling if stream yields no output)
  - `POST /media/upload/binary` — multipart upload → returns public `data.download_url` (cloudfront URL) used as reference `avatar_url` (WaveSpeed requires public URLs for `images:[url]`)
- Models:
  - Image: `google/nano-banana-2/edit` (`api/wavespeed_client.py:18`, tiktok client `:32`) — note `core/config.py:173` env default differs (`stable-diffusion-v1.5`, unused by clients)
  - Enhance: `wavespeed-ai/image-enhancer` (4x upscale)
  - Video: `kwaivgi/kling-v2.5-turbo-std/image-to-video` (`pipeline/wavespeed_i2v_client.py:20`, tiktok client `:33`; tiktok docstring mentions `kling-video-o3-pro` — code wins)
- Content policy: explicit-content flag detection via marker substring match (`"sensitive"`, `"explicit"`, `"flagged"`) in `_is_explicit_flag` (`api/wavespeed_client.py:21-26`) — aborts batch, surfaces `explicit_content_flagged` error

**Image hosting:**
- Avatar/reference image URL hosted at `i.ibb.co` (see `core/settings.json.example` identity) — external dependency for generation reference images; identity uploads instead publish to WaveSpeed cloudfront URLs

## Data Storage

**Databases:**
- None. File-based JSON state only

**File Storage:**
- Local filesystem: generated media in `outputs/YYYY-MM-DD/photos/` (PNG 1K 9:16) and `outputs/YYYY-MM-DD/` / `videos/` (MP4 9:16)
- Companion metadata: `meta.json` per batch dir (stem → labels/prompt/negative_prompt/guidance_scale), `{stem}.prompt` files (priority over meta), `{stem}.txt` captions, identity uploads in `outputs/identity/`
- Remote: WaveSpeed `/media/upload/binary` returns public download URL for reference images (`webui/server.py:_handle_identity_upload`)

**Caching:**
- In-memory `_balance_cache` (60s TTL) in `webui/server.py:43`
- Batch checkpoint JSON (`checkpoint_photo.json`, `checkpoint.json`) for resume across runs (`api/wavespeed_client.py:281-296`)
- `.batch.lock` files with 10-min staleness (`LOCK_STALE_SECONDS`), stale locks cleaned at server boot (`webui/server.py:129-142`) and on contention

## Authentication & Identity

**Auth Provider:**
- None (local tool, no users). API-key auth to WaveSpeed only
- Multi-account store: `core/settings.json["wavespeed_accounts"]` — CRUD via `core/config.py` (`set_wavespeed_account`, `remove_wavespeed_account`, `rename_wavespeed_account`, `set_active_wavespeed_account`, `test_wavespeed_account` via `GET /models`). Keys masked `abcd****wxyz` when served to UI (`list_wavespeed_accounts`)
- Identity (Alina Sky): `settings.json["identity"]` = {name, avatar_url}, managed via `/api/settings/identity` + upload endpoint

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- `webui/activity.json` — run history (last 50 entries, HH:MM + message), appended by `_log_activity` (`webui/server.py:182-189`)
- Pipeline progress: `@P <stage>|<detail>` protocol on stdout, parsed into `_pipeline_runs` state by `_update_progress` (`webui/server.py:291-317`), polled via `/api/progress`
- Python `logging` in clients (debug level); server HTTP logging silenced (`log_message` pass)

## CI/CD & Deployment

**Hosting:**
- Localhost only (`0.0.0.0:8000`, `webui/server.py:908`)

**CI Pipeline:**
- GitHub Actions `.github/workflows/ci.yml`: py_compile all modules → import smoke test (`pip install requests`; import `core`, `pipeline`, `webui`, `api` packages) → `node --check` on `app.js` + static file presence

## Environment Configuration

**Required env vars:**
- `IMAGE_MODEL`, `VIDEO_MODEL` — optional overrides, defaults in `core/config.py:173-174` (only env-var usage in codebase)
- `.env` exists (gitignored) — legacy WaveSpeed key + avatar URL. Do not read contents.

**Secrets location:**
- `core/settings.json` (gitignored; `.gitignore:38`) — live API keys
- `docs/wavespeed_identity_alina.md` — legacy API key + avatar URL (parsed, migrated to settings.json)
- `.env` — legacy environment config
- Keys are never logged (masked previews only)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None (polling + SSE only; no webhook registrations with WaveSpeed)

---

*Integration audit: 2026-08-05*
