# Requirements: OFM — Alina Sky Image & Video Generator

**Defined:** 2026-08-05

**Core Value:** Reliably generate on-brand photo/video content at low cost through WaveSpeed's API with a simple local control panel — generation works end-to-end even as models/endpoints change.

## v1 Requirements

### Photo Generation

- [x] **PHOTO-01**: Generate batch photos from prompt jobs (submit → poll/download via WaveSpeed API)
- [x] **PHOTO-02**: Real-time progress via SSE streaming, with automatic fallback to polling when stream endpoint fails
- [x] **PHOTO-03**: Optional enhance pass (`wavespeed-ai/image-enhancer`) on generated images
- [x] **PHOTO-04**: Outputs saved to `outputs/YYYY-MM-DD/photos/` with unique timestamp-hashed filenames
- [x] **PHOTO-05**: Prompt bank generates randomized prompts (scene, framing, hair, outfit, pose, lighting, quality)
- [x] **PHOTO-06**: Companion `.prompt` file saved alongside each image

### Web UI Control Panel

- [x] **UI-01**: Generation panel with Vibe/Camera/Lighting/Outfit/Time/Count controls
- [x] **UI-02**: Outputs table grouped by date with preview, fullscreen, caption edit, download, delete
- [x] **UI-03**: Multi-account WaveSpeed key management (add/remove/rename, set active) via settings drawer
- [x] **UI-04**: API selector modal with balance display, per-account and total, auto-refresh
- [x] **UI-05**: Identity management (name + avatar) with local upload → public URL publish
- [x] **UI-06**: Custom prompt banks + presets CRUD
- [x] **UI-07**: Retro-terminal theme (terminal/paper), dark/light toggle, controls lock during generation
- [x] **UI-08**: Auto-detect server shutdown → "Close this tab" message

### Settings & Config

- [x] **SET-01**: API keys stored in gitignored `core/settings.json`, tracked masked template `core/settings.json.example`
- [x] **SET-02**: Balance tracking via `PHOTO_PRICE` (0.07)
- [x] **SET-03**: Settings persistence (identity, accounts, prompt banks, presets)

## v2 Requirements (Deferred)

### Not yet implemented — video generation not wired (code files exist, no server/UI integration)

- [ ] **VIDEO-01**: Image-to-video generation via `kling-v2.5-turbo-std` (9:16 MP4) — `pipeline/wavespeed_i2v_client.py` + `scripts/run_tiktok.py` exist but are not wired to server/UI; no video generation endpoint in `webui/server.py`
- [ ] **VIDEO-02**: TikTok-style video pipeline with prompt style guide (`pipeline/alina_video_guide.md`)

### Not yet tracked — future feature ideas slot here as new implementations begin

- **FEAT-01**: TBD — pending feature ideas (use `/gsd-progress --do` or `/gsd-quick` to capture)
- **FEAT-02**: TBD

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-user / auth | Personal local tool, single operator |
| Cloud deployment | Localhost only; dev mode, repo not public yet |
| Social posting automation | Generation only; posting manual |
| Framework migration | Stdlib http.server + vanilla JS by design |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PHOTO-01..06 | Phase 1 (Baseline) | Done |
| VIDEO-01..02 | v2 (deferred, not implemented) | Pending |
| UI-01..08 | Phase 1 (Baseline) | Done |
| SET-01..03 | Phase 1 (Baseline) | Done |
| FEAT-01..02 | Phase 2 (reserved, when defined) | Pending |

**Coverage:**
- v1 requirements: 17 total (all shipped baseline)
- Mapped phases: Phase 1 (Baseline) — 17/17 ✓
- Reserved placeholders: Phase 2 (Next Feature), Phase 3 (Future Enhancements) — filled as requirements are captured
- Unmapped: 0

---
