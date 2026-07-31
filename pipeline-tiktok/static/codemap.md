# pipeline-tiktok/static/

## Responsibility
Single-page application frontend — warm monochrome OpenCode-style UI served by the Python HTTP server. Zero build step, zero CDN, pure vanilla HTML/CSS/JS.

## Files
| File | Responsibility |
|------|---------------|
| `index.html` | SPA shell — toolbar (brand mark, balance, live indicator, API trigger, settings gear, dark toggle), generation card, outputs table |
| `style.css` | All styles — CSS variables for dark/light, flat surfaces (no glass), Geist + JetBrains Mono, 6px/8px radius scale |
| `app.js` | All frontend logic — API polling (balance 60s, status 30s), generation flow, outputs CRUD, settings drawer, account management |

## Key Features
- **Toolbar**: `position: fixed; top: 0; height: 48px` — full-width flat bar, brand left, controls right, 1px bottom border
- **Segmented controls**: Border-grouped radio buttons (`border-radius: 6px`, 1px divider between options)
- **API dropdown**: Flat dropdown (no glass) toggled by nav trigger — shows all accounts with balances + Use buttons
- **Settings drawer**: Right-slide flat panel for API key management (add/remove/rename)
- **Outputs table**: Grouped by date, hover preview, fullscreen, caption edit, download, delete, modal prompt popup
- **Modals**: Flat surfaces with 1px border, no `backdrop-filter` anywhere

## Integration
- **Consumed by**: `server.py` (served at `/` and `/static/*`)
- **Depends on**: None (vanilla JS, no frameworks/CDN)
