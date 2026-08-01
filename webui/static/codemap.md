# webui/static/

## Responsibility
Single-page application frontend — retro terminal theme (phosphor green on deep terminal black) served by the Python HTTP server. Zero build step, zero CDN, pure vanilla HTML/CSS/JS. Uses OpenCode's system-native font stacks.

## Files
| File | Responsibility |
|------|---------------|
| `index.html` | SPA shell — toolbar (brand mark, balance, live indicator, API trigger, settings gear, dark toggle), generation card, outputs table, modals |
| `style.css` | All styles — CSS variables for dark/light, OpenCode font stacks, CRT scanlines + phosphor glow, 4px/6px radius scale, terminal window chrome on modals |
| `app.js` | All frontend logic — API polling (balance 60s, status 30s), generation flow, outputs CRUD, settings drawer, account management, keyboard access for API trigger |

## Design Tokens
- **Fonts** (OpenCode `theme.css` stacks): `--font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`; `--font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace`
- **Dark palette**: `--bg: #0a0f0a`, `--fg: #c8e8c8`, `--accent: #00ff88`, `--amber: #ffb000`, `--error: #ff6b6b`
- **Light palette**: warm paper `#f0f4f0` bg, deep terminal green `#007a33` accent
- **Radius**: `--radius: 4px`, `--radius-card: 6px` (square terminal corners)

## Key Features
- **Toolbar**: `position: fixed; top: 0; height: 48px` — full-width bar, brand with blinking `▊` terminal cursor, 1px bottom border + accent glow
- **Segmented controls**: Border-grouped radio buttons (`border-radius: 4px`, 1px divider), active = phosphor green bg + glow
- **CRT effects**: Scanline overlay (`body::after`, 3.5% green, transform-only drift), ambient radial phosphor glow, scanline row stripes in tables
- **API modal**: Centered popup with terminal window chrome (3 colored dots via `::before`) — accounts with balances + check marks
- **Settings drawer**: Right-slide panel for API key management (add/remove/rename)
- **Outputs table**: Grouped by date, hover preview, fullscreen, caption edit, download, delete, inline prompt toggle
- **Toasts**: Mono type with `[OK]`/`[ERR]`/`[WARN]`/`[INFO]` prefixes
- **Accessibility**: `color-scheme: dark/light`, focus-visible phosphor rings, aria-labels on icon buttons, `aria-expanded` + Enter/Space on API trigger, `role="dialog"` on modals, `prefers-reduced-motion` kills animations

## Integration
- **Consumed by**: `webui/server.py` (served at `/` and `/static/*`)
- **Depends on**: None (vanilla JS, no frameworks/CDN)
