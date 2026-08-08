# webui/

## Responsibility
Web control panel for the OFM pipeline. Contains the HTTP server (port 8000), the TikTok-specific WaveSpeed client, the dashboard generator, and the run history log.

## Files
| File | Responsibility |
|------|---------------|
| `server.py` | HTTP server + REST API (port 8000) — serves static UI, prompt building, pipeline subprocess orchestration, output browsing, multi-account management, caption generation (`POST /api/captions/generate`) |
| `dashboard.py` | Static dashboard HTML generator — collects outputs, embeds images in b64, serves or writes |
| `wavespeed_tiktok_client.py` | TikTok-specific WaveSpeed client (nano-banana-2 → kling-v2.5-turbo-std) |
| `activity.json` | Run history log (timestamps, prompt bank names, account switches) |
| `static/` | Frontend SPA (index.html, style.css, app.js) — see `static/codemap.md` |
| `fonts/` | TikTok Sans typeface (gitignored binaries) |

## Integration
- **Depends on**: `core/config.py`, `core/daybatch.py`, `core/errors.py`, `api/wavespeed_client.py`
- **Depends on**: `pipeline/prompt_bank.py` (imports `list_presets`, `build_jobs`, `build_jobs_multi`)
- **Runs**: `pipeline/pipeline.py` as subprocess (photo gen), `dashboard.py --all` (dashboard rebuild)
</content>
