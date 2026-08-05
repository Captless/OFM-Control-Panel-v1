# Technology Stack

**Analysis Date:** 2026-08-05

## Languages

**Primary:**
- Python 3.13.14 (local runtime, `py --version`) — all backend code: server, clients, pipelines, scripts
- CI pins Python 3.11 (`.github/workflows/ci.yml`)

**Secondary:**
- JavaScript (ES5-style, no modules) — `webui/static/app.js` (~2100 lines)
- HTML5 + CSS3 — `webui/static/index.html`, `webui/static/style.css` (~2600 lines)

## Runtime

**Environment:**
- CPython; zero build step, zero npm, zero bundler. Pure vanilla frontend.

**Package Manager:**
- `pip` only (not pinned in repo)
- No `requirements.txt` / `pyproject.toml` — single runtime dep is `requests` (installed manually; CI does `pip install requests`)
- Lockfile: none

## Frameworks

**Core:**
- None. Backend uses Python stdlib only: `http.server.ThreadingHTTPServer`, `urllib.request`, `json`, `concurrent.futures`, `threading`, `subprocess`, `re`, `queue`, `uuid`, `webbrowser`, `msvcrt`/`fcntl` (file locking), `base64`, `socketserver`

**Testing:**
- None (no test framework, no test files). CI only runs `py_compile` syntax checks + import smoke tests + `node --check`

**Build/Dev:**
- GitHub Actions (`.github/workflows/ci.yml`) — 3 jobs: syntax-check, import-test, frontend-lint
- FFmpeg — external binary, required by `webui/wavespeed_tiktok_client.py` for `drawtext` text overlay (stage 3 of TikTok pipeline). Searched via `shutil.which("ffmpeg")` then hardcoded Windows paths (`C:\ffmpeg\bin\ffmpeg.exe`, `%USERPROFILE%\ffmpeg\bin\ffmpeg.exe`)

## Key Dependencies

**Critical:**
- `requests` — used only in `api/wavespeed_client.py` (SSE streaming + binary upload), `webui/wavespeed_tiktok_client.py` (full REST client). All other HTTP uses stdlib `urllib.request`
- WaveSpeed AI REST API — external service, not a package

**Infrastructure:**
- `git` — repo at `C:\Users\User\Desktop\OFM`
- Fonts: local TTFs in `webui/fonts/` (gitignored binaries). No Google Fonts, no CDN `@import` in `style.css`

## Configuration

**Environment:**
- Primary: `core/settings.json` (gitignored, live keys) — `wavespeed_accounts` (label→key), `active_wavespeed_account`, `identity` (name + avatar_url), `prompt_banks`, `active_bank`, presets
- Template: `core/settings.json.example` (tracked, masked keys) — contains one example bank `d0942bb05db6`
- Legacy: `.env` (exists, gitignored — contains WaveSpeed API key + avatar URL; loaded via `os.environ` only for `IMAGE_MODEL`/`VIDEO_MODEL` defaults in `core/config.py:173-174`). Do not read contents.
- Legacy identity: `docs/wavespeed_identity_alina.md` — parsed by `core/config.py:_parse_identity_file()`, auto-migrated into `settings.json["identity"]` on first `get_identity()` read

**Build:**
- `.github/workflows/ci.yml` — py_compile on 18 files, import test on 4 packages, `node --check webui/static/app.js`, presence checks for HTML/CSS/JS

## Platform Requirements

**Development:**
- Windows (paths, `netstat` port kill, `msvcrt` locking, ANSI color enable all in `webui/server.py`); Python 3.11+; `requests` installed; FFmpeg on PATH for TikTok text overlay
- Not required but present: `.claude/skills/` (design skills), `.slim/` (codemap state), `.playwright-mcp/` (browser automation), `.planning/` (GSD state)

**Production:**
- None — personal local tool. Server binds `0.0.0.0:8000`, auto-opens browser, kills stale process on the port at boot (`webui/server.py:880-891`)

---

*Stack analysis: 2026-08-05*
