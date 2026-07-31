# Repository Atlas: OFM — Alina Sky Image & Video Generator

## Project Responsibility
Personal pipeline for generating alt-girl aesthetic photos and TikTok videos via WaveSpeed AI. Serves a web UI control panel at `localhost:8000` with account management, generation controls, and output browsing. No build step, zero npm, pure vanilla.

## System Entry Points
- `server.py`: HTTP server (port 8000) — serves UI + REST API
- `scripts/open_server.py`: Launcher — opens browser + starts server subprocess
- `scripts/open_dashboard.py`: Dashboard viewer launcher

## Directory Map
| Directory | Responsibility | File Count | Map |
|-----------|---------------|------------|-----|
| `core/` | Shared config, error types, day-path utility, text generation | 6 files | [View](core/codemap.md) |
| `pipeline-tiktok/` | TikTok video pipeline — dashboard, client, static UI, run scripts | 9 files | [View](pipeline-tiktok/codemap.md) |
| `pipeline-tiktok/static/` | Frontend (HTML/CSS/JS) — warm monochrome UI, no framework | 3 files | [View](pipeline-tiktok/static/codemap.md) |
| `pipeline-photovideo/` | Photo/video generation pipeline — prompt bank, text gen, i2v client | 6 files | [View](pipeline-photovideo/codemap.md) |
| `wavespeed-batch-api/` | Reusable WaveSpeed REST client (generate, enhance, batch) | 1 file | [View](wavespeed-batch-api/codemap.md) |
| `hot-take-influencer/` | Opinion/talking-head video persona workflow | 2 files | [View](hot-take-influencer/codemap.md) |
| `scripts/` | Utility entry points (server launcher, dashboard opener, meta backfill, saver) | 4 files | [View](scripts/codemap.md) |

## Configuration
- `core/settings.json` — API keys, active account, multi-account store
- `.env` — WaveSpeed API key + avatar URL (loaded via `os.environ`)
- `wavespeed_identity_alina.md` — Legacy identity file (name, avatar URL, API key)

## Key Dependencies
- **None** (zero build step, stdlib only on backend, vanilla JS on frontend)
- External: WaveSpeed AI REST API (`api-ondemand.wavespeed.ai/api/v3`)
