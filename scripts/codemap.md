# scripts/

## Responsibility
Convenience entry points for common operations — server launch, dashboard access, metadata management.

## Files
| File | Responsibility |
|------|---------------|
| `open_server.py` | Launches `server.py` as subprocess and opens browser at `localhost:8000` |
| `open_dashboard.py` | Runs `pipeline-tiktok/dashboard.py --all` with optional `--serve` for phone access |
| `save_meta.py` | CLI utility: reads prompts JSON, writes `meta.json` with labels to output directory |
| `update_config.py` | Fetches live model list from OmniRoute API and writes to OpenCode config (external tool) |
| `backfill_prompts.py` | Scans all `outputs/*/meta.json`, reconstructs full prompts from `prompt_bank` pools using label parsing + stem hash seed, writes to meta.json + `.prompt` companion files |

## Usage
```powershell
py scripts/open_server.py
py scripts/open_dashboard.py --serve
py scripts/save_meta.py prompts.json outputs/batch_name
py scripts/backfill_prompts.py        # backfill existing outputs with prompt data
```

## Integration
- **Depends on**: `server.py`, `pipeline-tiktok/dashboard.py`, `pipeline-photovideo/prompt_bank.py`
- **Not consumed by**: Other modules (user-facing convenience scripts)
