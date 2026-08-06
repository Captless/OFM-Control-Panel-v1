# Phase 3 Plan — Caption Generator UI Card

## Files
- `webui/static/index.html` (MODIFY)
- `webui/static/app.js` (MODIFY)
- `webui/static/style.css` (MODIFY)

## Tasks
### T3.1 — HTML card
- Insert after the `.gen-layout` div (after Image Generation + Prompt Preview two-column layout), before Outputs header.
- New `<div class="card" id="caption-gen-card">` matching existing card styles:
  - `<h3>Caption Generator</h3>`
  - Platform pills (radio `name="cap_platform"`): TikTok (checked), Reels, Shorts, X/Twitter, Stories.
  - Hook Type pills (radio `name="cap_hook"`): Vulnerable (checked), Confident, Playful, Aesthetic, Relatable, Mixed.
  - Count slider `#cap-count` (min 1, max 20, value 5) + label `#cap-count-label`.
  - Generate button `#btn-caption` with `.btn-text` span.
  - Caption list container `#caption-list` (max-height, scroll).
  - Actions row: Copy All button + Clear button.

### T3.2 — JS
- `getSelectedCapPlatform()`, `getSelectedCapHook()` helpers (mirror existing getSelected* pattern).
- `generateCaptions()`: POST `/api/captions/generate` with selected options (hook "mixed" → omit hook_types). Render list. Disable button while fetching.
- `renderCaptions(caps)`: each item card with text, hook/platform badges, copy button (navigator.clipboard).
- `copyAllCaptions()`: join texts with "\n\n", clipboard, toast.
- `clearCaptions()`: empty list, toast.
- Reuse existing `api()`, `showToast`, `esc` helpers.

### T3.3 — CSS
- `.caption-item`, `.caption-item-head`, `.caption-text-raw`, `.cap-badge`, `.cap-actions`.
- Style with theme vars (--surface, --border, --accent, --radius-card) to match terminal/retro theme.
- Responsive: full-width on mobile.

## Verify
- `node --check webui/static/app.js`
- Live server :8000 → card renders, generates captions, copy works.

## Acceptance
- UI renders, generates captions via Phase 2 endpoint, copy buttons work, node --check clean.
