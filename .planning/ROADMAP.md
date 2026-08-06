# OFM Roadmap Alina Caption Generator

## Milestone: M1 — Caption Generator for Alina Social Content

Goal: identity-locked caption generator (`scripts/alina_textgen.py`) + web UI card so the operator can generate platform-optimized on-screen captions for Alina's alt-girl content with zero manual text writing.

### Phase 1: p1 Alina Text Generator Module 1.0

**Goal:** Standalone pool-based caption generator grounded in Alina Sky identity (5 hook types: vulnerable/confident/playful/aesthetic/relatable, platform CTA + hashtag configs). CLI: `python scripts/alina_textgen.py 10 [tiktok|reels|shorts|x|stories] [--seed N]`. Output to stdout only. Zero deps. 2x pools (~20 openers / 12 middles / 12 closers per hook type).
**Requirements:** TBD
**Depends on:** Phase 0
**Plans:** 1/1 plans complete
Plans:

- [x] 01-01-PLAN.md
- [ ] TBD (run /gsd-plan-phase 1 to break down)

### Phase 2: p2 Server API Endpoint 2.0

**Goal:** Wire generator into `webui/server.py`. POST `/api/captions/generate` — request `{count, platform, hook_types[], seed}`, response `{ok, captions:[{text, platform, hook_type, cta, hashtags}]}`. Import from scripts dir. Malformed body → 400.
**Requirements:** TBD
**Depends on:** Phase 1
**Plans:** 0 plans
Plans:

- [ ] TBD (run /gsd-plan-phase 2 to break down)

### Phase 3: p3 Caption Generator UI Card 3.0

**Goal:** New card in `webui/static/index.html` below Image Generation: platform pills, hook-type pills, count slider, Generate button, caption list with per-caption copy + copy-all + clear. JS in `app.js`, styles in `style.css`. Matches existing retro-terminal theme.
**Requirements:** TBD
**Depends on:** Phase 2
**Plans:** 0 plans
Plans:

- [ ] TBD (run /gsd-plan-phase 3 to break down)

### Phase 4: p4 Integration and Polish 4.0

**Goal:** Verify full flow (UI → endpoint → generator), confirm no regressions in existing photo pipeline, add `scripts/` to CI import path if needed, update codemap/AGENTS.md.
**Requirements:** TBD
**Depends on:** Phase 3
**Plans:** 0 plans
Plans:

- [ ] TBD (run /gsd-plan-phase 4 to break down)
