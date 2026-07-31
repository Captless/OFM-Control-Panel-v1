# scripts/

## Responsibility
Convenience entry points for common operations — server launch, dashboard access, metadata management, batch generation.

## Files
| File | Responsibility |
|------|---------------|
| `run_tiktok.py` | Batch TikTok video generation CLI — N clips into today's output folder with auto-text + auto-meta |
| `open_server.py` | Launches `webui/server.py` as subprocess and opens browser at `localhost:8000` |
| `open_dashboard.py` | Runs `webui/dashboard.py --all` with optional `--serve` for phone access |
| `save_meta.py` | CLI utility: reads prompts JSON, writes `meta.json` with labels to output directory |
| `update_config.py` | Fetches live model list from OmniRoute API and writes to OpenCode config (external tool) |
| `backfill_prompts.py` | Scans all `outputs/*/meta.json`, reconstructs full prompts from `prompt_bank` pools using label parsing + stem hash seed, writes to meta.json + `.prompt` companion files |

## Usage
```powershell
py scripts/run_tiktok.py 5            # 5 TikTok clips
py scripts/open_server.py
py scripts/open_dashboard.py --serve
py scripts/save_meta.py prompts.json outputs/batch_name
py scripts/backfill_prompts.py        # backfill existing outputs with prompt data
```

## Integration
- **Depends on**: `webui/server.py`, `webui/dashboard.py`, `webui/wavespeed_tiktok_client.py`, `pipeline/prompt_bank.py`, `core/*`
- **Not consumed by**: Other modules (user-facing convenience scripts)
</content>
