# Sidebar Navigation Implementation Plan (implemented)

## Overview
Collapsible sidebar navigation, flat clickable list (no section labels), four items:
- **Generate Images** (`generation`, default active)
- **Generate Captions** (`captions`)
- **View Outputs** (`outputs`)
- **Settings** (`settings`, bottom, divider above)

Sidebar collapses to a circular arrow toggle centered on the sidebar's bottom border. State persists in localStorage.
Settings lives in sidebar bottom item; `#section-settings` is a two-pane grid: **Prompt Bank (left) + Identity card (right)**.
Settings modal removed entirely.

---

## File Changes (implemented)

### 1. `index.html` — Structure

**Sidebar** (after `<div class="app">`, before toolbar):
```html
<aside class="sidebar" id="sidebar" role="navigation" aria-label="Main navigation">
  <nav class="sidebar-nav">
    <ul class="nav-items">
      <li><button class="nav-item active" data-section="generation" onclick="showSection('generation')">
        <span class="nav-icon"><svg …image icon…></svg></span>
        <span class="nav-label">Generate Images</span>
        <span class="nav-arrow"><svg …chevron-right 14x14…></svg></span>
      </button></li>
      <!-- captions, outputs: same pattern -->
    </ul>
    <ul class="nav-items nav-items-bottom">
      <li><button class="nav-item" data-section="settings" onclick="showSection('settings')">
        <span class="nav-icon"><svg …gear…></svg></span>
        <span class="nav-label">Settings</span>
        <span class="nav-arrow"><svg …chevron-right…></svg></span>
      </button></li>
    </ul>
  </nav>
</aside>
```
- No `nav-section` wrappers, no `nav-section-title` headers — strictly clickable items.
- No OFM brand in sidebar (removed per feedback).
- `nav-arrow` = chevron-right SVG (same `>` glyph style as `.section-header h4::before`), shown on hover/active.
- Floater (`#sidebar-floater`) mirrors the same 4 sections, no Prompt Bank item.

**Toggle button** (sibling after `</aside>`):
```html
<button class="sidebar-toggle" id="sidebar-toggle" aria-label="Collapse sidebar" aria-expanded="true" onclick="toggleSidebar()">
  <svg class="chevron" viewBox="0 0 24 24" width="16" height="16"><polyline points="15 18 9 12 15 6"/></svg>
</button>
```
Single binding: inline `onclick="toggleSidebar()"` only (no addEventListener — avoids double-toggle bug).

**`#section-settings`** (replaces placeholder; old settings-modal content moved here):
```html
<section id="section-settings" class="content-section" hidden>
  <div class="settings-grid">
    <div class="settings-pane prompt-bank-pane">
      <!-- banks-card (Export/Import/Create New Bank), settings-bank-list,
           active-bank-header, pool-editor-wrapper/pool-editor-list -->
    </div>
    <div class="settings-pane identity-pane">
      <!-- identity-card: avatar preview, name, URL input, upload-zone,
           settings-file-input, settings-new-preview, settings-status, Save -->
    </div>
  </div>
</section>
```
IDs preserved: `settings-avatar-preview`, `settings-identity-name`, `settings-avatar-url`,
`settings-bank-list`, `pool-editor-list`, `pool-editor-wrapper`, `active-bank-header`,
`settings-file-input`, `settings-upload-zone`, `settings-new-preview`, `settings-status`.

**Removed:** `#section-prompts` entirely (Prompt Bank moved into settings), `#settings-modal` (whole block).
Kept: `#new-bank-modal`, `#delete-bank-modal`.

### 2. `style.css` — Layout

**Nav:**
```css
.nav-items { list-style: none; margin: 0; padding: 0; }
.nav-items-bottom { margin-top: auto; padding-top: 8px; border-top: 1px solid var(--border); }
.nav-item { display: flex; align-items: center; gap: 10px; width: 100%; padding: 8px 10px;
  background: transparent; border: none; border-radius: var(--radius);
  color: var(--fg2); font-size: 13px; font-family: var(--font-mono); cursor: pointer; text-align: left;
  transition: background .15s, color .15s; }
.nav-item:hover { background: var(--row-hover); color: var(--fg); }
.nav-item.active { background: var(--accent-bg); color: var(--accent); }
.nav-icon { font-size: 16px; flex-shrink: 0; width: 24px; text-align: center; color: var(--fg2); }
.nav-arrow { margin-left: auto; flex-shrink: 0; display: flex; align-items: center;
  color: var(--fg3); opacity: 0; transform: translateX(-4px);
  transition: opacity .15s, transform .15s, color .15s; }
.nav-item:hover .nav-arrow, .nav-item.active .nav-arrow { opacity: 1; transform: translateX(0); }
.nav-item:hover .nav-arrow { color: var(--fg2); }
.nav-item.active .nav-arrow { color: var(--accent); }
.nav-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
```

**Toggle** (circular arrow centered on bottom border):
```css
.sidebar-toggle {
  position: fixed; left: var(--sidebar-width); bottom: 20px; transform: translateX(-50%);
  z-index: 51; background: var(--surface); border: 1px solid var(--border-strong);
  border-radius: 50%; width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center; color: var(--fg2); cursor: pointer;
  transition: left .25s cubic-bezier(.32,.72,0,1), transform .25s cubic-bezier(.32,.72,0,1),
    background .15s, color .15s, border-color .15s;
  box-shadow: 0 2px 8px var(--shadow-lg);
}
.sidebar-toggle:hover { background: var(--btn-hover); color: var(--accent); border-color: var(--accent-soft); }
.sidebar.collapsed ~ .sidebar-toggle { left: 0; }
.sidebar-toggle .chevron { transition: transform .25s cubic-bezier(.32,.72,0,1); }
.sidebar.collapsed ~ .sidebar-toggle .chevron { transform: rotate(180deg); }
```
Chevron: points left when sidebar open (collapse direction), rotates 180° → points right when collapsed/hidden.

**Settings two-pane:**
```css
.settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
.settings-grid .settings-pane { min-width: 0; }
@media (max-width: 900px) { .settings-grid { grid-template-columns: 1fr; } }
```

### 3. `app.js` — Logic

- `toggleSidebar()` flips `_sidebarCollapsed`, toggles `.collapsed`, sets `aria-expanded`, shows/hides floater, persists, `syncPanelHeights()`. Only inline `onclick` binding.
- `showSection(sectionId)`:
  ```js
  document.querySelectorAll('.nav-item, .floater-item').forEach(btn => btn.classList.toggle('active', btn.dataset.section === sectionId));
  document.querySelectorAll('.content-section').forEach(sec => { var a = sec.id === 'section-'+sectionId; sec.hidden = !a; sec.classList.toggle('active', a); });
  _activeSection = sectionId; saveSidebarState(); closeFloaterMenu();
  // mobile: close sidebar+overlay
  if (sectionId === 'outputs') refreshOutputs();
  else if (sectionId === 'generation') fetchBalance();
  else if (sectionId === 'settings') loadSettingsUI();
  syncPanelHeights();
  ```
- `loadSettingsUI()` → `loadSettings()` (renders identity into `#settings-avatar-preview`/`#settings-identity-name`/`#settings-avatar-url`, then `loadBankEditor()` renders banks+pool editor into `#settings-bank-list`/`#pool-editor-list`).
- **Removed:** `toggleSettingsModal`, `closeSettingsModal`, `_setSettingsExpanded`, settings-modal ESC/outside-click/DOMContentLoaded handlers, `loadPromptBankUI`, `'prompts'` branch in `showSection`.
- `saveIdentity()` no longer closes a modal — resets `#settings-new-preview` + `#settings-file-input`, clears `_pendingAvatarUrl`, shows toast, reloads.
- ESC handler keeps only new-bank / delete-bank modal close.
- Outside-click handler keeps only new-bank / delete-bank modal close.
- DOMContentLoaded: settings-modal click-close block removed; `settings-file-input` change + `settings-upload-zone` drag/drop bindings retained (elements now in `#section-settings`).

---

## Verification
- `node --check webui/static/app.js` clean.
- Server restarted (HOMEPAGE_HTML cached at import) — `/` serves new HTML (`nav-arrow` present, `settings-modal` absent), CSS has `.nav-arrow`/`.settings-grid`, JS has no `settings-modal`/`loadPromptBankUI`, `saveIdentity` new branch present.
- `/api/settings/identity`, `/api/settings/banks` respond 200.
