# OFM — Alina Sky Image & Video Generator

## What This

Personal pipeline for generating alt-girl aesthetic photos and TikTok-style videos via WaveSpeed AI. Web UI control panel runs at `http://localhost:8000` (Python stdlib `http.server`, vanilla frontend, no framework). Produces PNG images (1K) and MP4 videos (9:16) into `outputs/YYYY-MM-DD/`. Operated by a single developer in dev mode (not public).

## Core Value

Reliably generate on-brand photo/video content at low cost through WaveSpeed's API with a simple local control panel — generation works end-to-end even as models/endpoints change.

## Requirements

### Validated

- Photo generation pipeline (submit → poll/download, SSE streaming with polling fallback) — working
- Web UI control panel (:8000) with generation controls, outputs table, captions, delete — working
- Multi-account WaveSpeed key management in settings UI — working
- Identity (name/avatar) + prompt banks + presets managed in settings — working
- TikTok-style video generation pipeline — working

### Active

- (None — baseline captured; new work routed via /gsd-progress --do or /gsd-quick)

### Out of Scope

- Multi-user / auth — personal local tool, single operator
- Cloud deployment — localhost only, dev mode, repo not public yet
- Social media posting automation — generation only, posting manual
- Trading/optimizing API keys for profit — cost control is a constraint, not a product

## Context

- Backend: Python 3, `ThreadingHTTPServer`, no framework. Frontend: vanilla HTML/CSS/JS single-page app. Zero build step, zero npm (except dev tooling), zero CDN.
- WaveSpeed AI REST: `nano-banana-2/edit` images, `kling-v2.5-turbo-std` video. API base `https://api-ondemand.wavespeed.ai/api/v3`.
- Photos: `pipeline/pipeline.py` + `pipeline/prompt_bank.py`; videos: `pipeline/wavespeed_i2v_client.py`; API client `api/wavespeed_client.py`; config `core/config.py` (keys in gitignored `core/settings.json`).
- Outputs grouped by day in `outputs/YYYY-MM-DD/photos|videos/`.
- UI theme is retro-terminal phosphor green (`--accent:#00ff88` on `#0a0f0a`), themes `terminal`/`paper`.

## Constraints

- **Tech stack**: Python 3 stdlib http.server + vanilla JS — no framework migration, per design conventions.
- **API cost**: WaveSpeed is pay-per-generation; prompts/queries kept minimal, `PHOTO_PRICE` tracked in `core/config.py`.
- **Secrets**: WaveSpeed API keys live only in gitignored `core/settings.json`; `core/settings.json.example` (masked) is the tracked template. Repo must never commit live keys.
- **Compatibility**: Windows (win32), Python 3.11, git-bash for GSD shell blocks.
- **CI**: `.github/workflows/ci.yml` runs py_compile + import + node --check on push/PR to main.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SSE streaming with polling fallback | Real-time progress; resilient to stream endpoint failure | ✅ Good |
| stdlib http.server, no framework | Zero deps, simple local tool | ✅ Good |
| Keys in gitignored settings.json (not env) | WebUI multi-account CRUD writes them; env would break account switching | ✅ Good |
| `core/settings.json` untracked + `.example` template | Stops live-key commits; local file keeps working | ✅ Good |
| GSD `.planning/` committed to git | Planning artifacts tracked with code | ✅ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-05 after /gsd-new-project baseline onboarding*
