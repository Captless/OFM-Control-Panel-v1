# pipeline-tiktok/

## Responsibility
TikTok video generation pipeline with web UI control panel. Contains the HTTP server, WaveSpeed TikTok client, dashboard generator, and batch run script.

## Files
| File | Responsibility |
|------|---------------|
| `dashboard.py` | Static dashboard HTML generator — collects outputs, embeds images in b64, serves or writes |
| `run.py` | CLI batch runner — N TikTok clips with auto-text + auto-meta |
| `wavespeed_tiktok_client.py` | TikTok-specific WaveSpeed client (nano-banana-2 → kling-v2.5-turbo-std) |
| `text_generator.py` | Re-export shim from `core.text_generator` |
| `daybatch.py` | Re-export shim from `core.daybatch` |
| `activity.json` | Run history log (timestamps, prompt bank names, account switches) |

## Integration
- **Depends on**: `core/config.py`, `core/daybatch.py`, `core/errors.py`, `wavespeed-batch-api/wavespeed_client.py`
