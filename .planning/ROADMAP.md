# Roadmap: OFM — Alina Sky Image & Video Generator

## Overview

OFM is a mature single-developer local pipeline: photo generation via WaveSpeed AI with a web UI control panel at `http://localhost:8000`. All 17 v1 requirements are already shipped (image-generation baseline). Video generation code files exist (`pipeline/wavespeed_i2v_client.py`, `scripts/run_tiktok.py`, `webui/wavespeed_tiktok_client.py`) but are NOT wired to server/UI — that is Phase 2, the real next feature. Later phases are reserved scaffolding where future implementations slot in via `/gsd-plan-phase` + `/gsd-execute-phase`.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Baseline (shipped)** - Current working system: photo pipeline, web UI control panel, settings/config
- [ ] **Phase 2: Video Generation** - Wire existing image-to-video clients into server + UI for TikTok-style 9:16 MP4 output
- [ ] **Phase 3: Future Enhancements (reserved)** - Placeholder for later feature work beyond the immediate next feature

## Phase Details

### Phase 1: Baseline (shipped)
**Goal**: Users can generate on-brand photo content through WaveSpeed's API and manage the full pipeline from the local web control panel
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: PHOTO-01, PHOTO-02, PHOTO-03, PHOTO-04, PHOTO-05, PHOTO-06, UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08, SET-01, SET-02, SET-03
**Success Criteria** (what must be TRUE):
  1. User generates batch photos from prompt jobs with real-time progress (SSE streaming, polling fallback) and optional enhance pass
  2. User manages multi-account WaveSpeed keys, balances, identity, prompt banks, and presets from the web UI
  3. User views and manages outputs (preview, fullscreen, caption edit, download, delete) grouped by date
  4. User toggles terminal/paper themes; controls lock during generation; UI warns when server shuts down
**Plans**: 0 (shipped before GSD tracking)

Plans:
- (None — baseline predates GSD planning; captured as shipped state)

**UI hint**: yes

### Phase 2: Video Generation
**Goal**: Wire the existing (orphaned) image-to-video clients into the server API and web UI so users generate TikTok-style 9:16 MP4 videos end-to-end
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: VIDEO-01 (image-to-video via `kling-v2.5-turbo-std`), VIDEO-02 (TikTok-style video pipeline w/ style guide)
**Success Criteria** (what must be TRUE):
  1. User triggers video generation from the web UI with a source image + prompt
  2. Server exposes a video generation endpoint (submit → poll/download via existing `wavespeed_i2v_client.py` / `wavespeed_tiktok_client.py`)
  3. Generated 9:16 MP4 videos land in `outputs/YYYY-MM-DD/videos/` and appear in the outputs table
  4. Video progress/status visible in UI during generation
**Plans**: TBD

### Phase 3: Future Enhancements (reserved)
**Goal**: Later feature work beyond video generation; filled only when real requirements are captured
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: (none yet — reserved)
**Success Criteria** (what must be TRUE):
  1. New requirements captured in REQUIREMENTS.md are mapped to this phase
  2. Feature is planned, executed, and verified through the standard GSD workflow
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Baseline (shipped) | — | Complete | 2026-08-05 |
| 2. Video Generation | 0/TBD | Not started | - |
| 3. Future Enhancements (reserved) | 0/TBD | Not started | - |
