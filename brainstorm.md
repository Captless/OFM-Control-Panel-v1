# Brainstorm: Configuration & Workflow Optimizations

## Tool Usage Patterns

### Bash: Use `workdir` instead of `cd`
- **Current**: `bash "cd /path && cmd"` or separate `cd` calls
- **Better**: `bash "cmd", workdir="/path"`
- **Why**: Cleaner, avoids shell state issues, works reliably in PowerShell/CMD, no quoting hell

### Read: Use `read` tool for file content
- **Current**: `bash "cat file"` or `python -c "open(...).read()"`
- **Better**: `read filePath="..."` with `limit`/`offset` for large files
- **Why**: Native encoding handling, no subprocess overhead, proper truncation

### Write: Use `write` tool for new files
- **Current**: `bash "echo '...' > file"` or python file writes
- **Better**: `write filePath="...", content="..."`
- **Why**: Atomic, handles encoding, no shell escaping issues

---

## OFM-Specific Configuration Improvements

### 1. Server Restart Automation
- **Problem**: HTML served fresh per request (fixed), but JS/CSS need no restart. Still manual restart for Python changes.
- **Fix**: Add file watcher (`watchdog`) for `webui/server.py`, `core/*.py` → auto-reload via graceful restart or `importlib.reload` on module.

### 2. Settings Persistence Layer
- **Current**: `core/settings.json` — flat JSON, manual reads/writes
- **Improve**: Light wrapper (`config.py`) with:
  - Typed accessors (`get_bank(id)`, `set_active_bank(id)`)
  - Atomic writes (temp file + rename)
  - Schema validation (pydantic or simple dict validation)
  - Change callbacks (for live UI sync without reload)

### 3. Bank Storage Normalization
- **Current**: `prompt_banks` dict in settings.json with UUID keys
- **Consider**: Separate `banks/` directory (one JSON per bank) for:
  - Git-friendly diffs (one file per bank change)
  - Easier backup/restore
  - Concurrent edit safety (file locks)

### 4. API Key Management
- **Current**: WaveSpeed keys in settings.json (plaintext)
- **Improve**: 
  - Optional encryption at rest (fernet, key from env var)
  - Key rotation UI (show last used, expiry warning)
  - Per-account rate limit tracking

### 5. Generation Pipeline Config
- **Current**: Hardcoded in `pipeline/prompt_bank.py` (model names, aspect ratios, params)
- **Extract**: `generation.yaml` or `config.toml`:
  ```yaml
  photo:
    model: "nano-banana-2/edit"
    resolution: "1K"
    format: "png"
  video:
    model: "kling-v2.5-turbo-std"
    aspect_ratio: "9:16"
  ```
- **Benefit**: Change models/params without code edit; per-bank overrides possible

### 6. Output Directory Structure
- **Current**: `outputs/YYYY-MM-DD/photos|videos/`
- **Add**: Optional subdir by bank name or vibe for organization
- **Index**: Maintain `outputs/index.json` (stem → metadata) for fast listing without filesystem walk

### 7. Dev/Prod Config Split
- **Add**: `config.dev.json` / `config.prod.json` with:
  - Dev: mock API, verbose logging, smaller batches
  - Prod: real API, structured logging, full batches
- **Load**: Based on `OFM_ENV` env var

### 8. Type Hints & Validation
- **Add**: `py.typed` + type stubs for core modules
- **CI**: `mypy --strict` in GitHub Actions
- **Runtime**: `pydantic` models for API request/response shapes

### 9. Logging Standardization
- **Current**: `print()` / `console.log` scattered
- **Unify**: Python `logging` + JS `console.debug/info/warn/error` with levels
- **Config**: `LOG_LEVEL` env var controls verbosity

### 10. Frontend Build Step (Optional)
- **Current**: Zero build (vanilla HTML/JS/CSS) — *keep this*
- **If needed**: Vite/ESBuild for:
  - JS modules (import/export instead of global functions)
  - CSS nesting, variables, minification
  - TypeScript for type safety
- **Decision**: Only if JS grows >2000 lines or team expands

---

## Quick Wins (Low Effort, High Impact)

| Change | Effort | Impact |
|--------|--------|--------|
| `workdir` in all bash calls | 5 min | Reliability |
| Atomic JSON writes | 15 min | Data safety |
| `generation.yaml` extraction | 30 min | Flexibility |
| Type hints on `core/` | 1 hr | Maintainability |
| Structured logging | 1 hr | Debugging |

---

## Non-Goals (Explicitly NOT Doing)

- Database (SQLite/Postgres) — overkill for single-user JSON
- Full frontend framework (React/Vue) — vanilla is intentional
- Docker/k8s — local single-process is fine
- Tests framework — assert-based self-checks sufficient for now

---

## Next Steps

1. Apply `workdir` pattern to all future bash calls
2. Extract `generation.yaml` from `prompt_bank.py` constants
3. Add atomic write helper to `core/config.py`
4. Add `LOG_LEVEL` support to server.py

---

*Generated during session — review and prioritize.*