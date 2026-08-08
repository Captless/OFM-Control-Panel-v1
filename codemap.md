# Repository Atlas: OFM — Alina Sky Image & Video Generator

## Project Responsibility
Personal pipeline for generating alt-girl aesthetic photos and TikTok videos via WaveSpeed AI. Serves a web UI control panel at `localhost:8000` with account management, generation controls, and output browsing. No build step, zero npm, pure vanilla.

## System Entry Points
- `webui/server.py`: HTTP server (port 8000) — serves UI + REST API
- `scripts/open_server.py`: Launcher — opens browser + starts server subprocess
- `scripts/open_dashboard.py`: Dashboard viewer launcher
- `pipeline/pipeline.py`: Photo generation entry point (CLI `--prompts <json>`)
- `scripts/run_tiktok.py`: TikTok batch video generation CLI

## Directory Map
| Directory | Responsibility | File Count | Map |
|-----------|---------------|------------|-----|
| `core/` | Shared config, error types, day-path utility, text generation | 6 files | [View](core/codemap.md) |
| `api/` | Reusable WaveSpeed REST client (generate, enhance, batch) | 1 file | [View](api/codemap.md) |
| `webui/` | Web control panel — HTTP server, TikTok client, dashboard generator | 5 files | [View](webui/codemap.md) |
| `webui/static/` | Frontend (HTML/CSS/JS) — warm monochrome UI, no framework | 3 files | [View](webui/static/codemap.md) |
| `pipeline/` | Photo/video generation pipeline — prompt bank, i2v client | 4 files | [View](pipeline/codemap.md) |
| `scripts/` | Utility entry points (server launcher, dashboard opener, meta backfill, saver) | 7 files | [View](scripts/codemap.md) |
| `hot-take-influencer/` | Opinion/talking-head video persona workflow | 2 files | [View](hot-take-influencer/codemap.md) |
| `docs/` | Loose style guides + identity reference (Alina) | 2 files | — |

## Configuration
- `core/settings.json` — API keys, active account, multi-account store
- `.env` — WaveSpeed API key + avatar URL (loaded via `os.environ`)
- `docs/wavespeed_identity_alina.md` — Legacy identity file (name, avatar URL, API key)

## Key Dependencies
- **None** (zero build step, stdlib only on backend, vanilla JS on frontend)
- External: WaveSpeed AI REST API (`api-ondemand.wavespeed.ai/api/v3`)
</content>
