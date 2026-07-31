# core/

## Responsibility
Shared configuration, error handling, and utility layer consumed by all pipeline modules. Centralizes API key management, multi-account support, day-path generation, and alt-girl text prompt generation.

## Files
| File | Responsibility |
|------|---------------|
| `config.py` | API key CRUD, multi-account (wavespeed_accounts), env/identity migration, balance test |
| `errors.py` | `WaveSpeedError` exception class with code/status attributes |
| `daybatch.py` | `day_path()` → `outputs/YYYY-MM-DD/<subdir>` with auto-create |
| `text_generator.py` | 10 alt-girl topic banks (situationship, self_worth, late_nights, etc.), `random_text()` / `batch_texts()` |
| `settings.json` | Persistent JSON store for API keys + active account |

## Integration
- **Consumed by**: `webui/server.py`, `pipeline/pipeline.py`, `scripts/run_tiktok.py`, `scripts/backfill_prompts.py`
- **Depends on**: stdlib only (os, json, pathlib, random)
