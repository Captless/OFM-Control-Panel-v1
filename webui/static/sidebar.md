# Sidebar Navigation Implementation Plan

## Overview
Replace current flat layout with collapsible sidebar navigation featuring three sections:
- **Image Generation** (Generate Images, Prompt Bank)
- **Caption Generation** (Generate Captions)
- **Outputs** (View Outputs)

Sidebar collapses to a floating toggle button (floater) outside the sidebar. State persists in localStorage.

---

## File Changes

### 1. `index.html` — Structure

**Add after `<div class="app">` (before toolbar):**
```html
<aside class="sidebar" id="sidebar" role="navigation" aria-label="Main navigation">
  <div class="sidebar-header">
    <span class="sidebar-brand">OFM</span>
    <button class="sidebar-toggle" id="sidebar-toggle" aria-label="Collapse sidebar" aria-expanded="true">
      <svg class="chevron" viewBox="0 0 24 24" width="16" height="16"><polyline points="15 18 9 12 15 6"/></svg>
    </button>
  </div>
  <nav class="sidebar-nav">
    <section class="nav-section">
      <h4 class="nav-section-title">Image Generation</h4>
      <ul class="nav-items">
        <li><button class="nav-item active" data-section="generation" onclick="showSection('generation')">
          <span class="nav-icon">🖼</span>
          <span class="nav-label">Generate Images</span>
        </button></li>
        <li><button class="nav-item" data-section="prompts" onclick="showSection('prompts')">
          <span class="nav-icon">📝</span>
          <span class="nav-label">Prompt Bank</span>
        </button></li>
      </ul>
    </section>
    <section class="nav-section">
      <h4 class="nav-section-title">Caption Generation</h4>
      <ul class="nav-items">
        <li><button class="nav-item" data-section="captions" onclick="showSection('captions')">
          <span class="nav-icon">✍️</span>
          <span class="nav-label">Generate Captions</span>
        </button></li>
      </ul>
    </section>
    <section class="nav-section">
      <h4 class="nav-section-title">Outputs</h4>
      <ul class="nav-items">
        <li><button class="nav-item" data-section="outputs" onclick="showSection('outputs')">
          <span class="nav-icon">📁</span>
          <span class="nav-label">View Outputs</span>
        </button></li>
      </ul>
    </section>
  </nav>
</aside>

<div class="sidebar-floater" id="sidebar-floater" role="navigation" aria-label="Quick navigation" hidden>
  <button class="floater-toggle" id="floater-toggle" aria-label="Expand sidebar" onclick="toggleFloaterMenu(event)">
    <svg viewBox="0 0 24 24" width="18" height="18"><polyline points="9 18 15 12 9 6"/></svg>
  </button>
  <div class="floater-menu" id="floater-menu">
    <button class="floater-item" data-section="generation" onclick="showSection('generation')">
      <span class="floater-icon">🖼</span>
      <span class="floater-label">Generate Images</span>
    </button>
    <button class="floater-item" data-section="prompts" onclick="showSection('prompts')">
      <span class="floater-icon">📝</span>
      <span class="floater-label">Prompt Bank</span>
    </button>
    <button class="floater-item" data-section="captions" onclick="showSection('captions')">
      <span class="floater-icon">✍️</span>
      <span class="floater-label">Generate Captions</span>
    </button>
    <button class="floater-item" data-section="outputs" onclick="showSection('outputs')">
      <span class="floater-icon">📁</span>
      <span class="floater-label">View Outputs</span>
    </button>
  </div>
</div>

<div class="sidebar-overlay" id="sidebar-overlay" hidden></div>
```

**Wrap main content in sections:**
```html
<main class="main" id="main-content">
  <section id="section-generation" class="content-section active">
    <!-- existing gen-layout + caption-gen-card -->
  </section>
  <section id="section-prompts" class="content-section" hidden>
    <!-- Prompt Bank editor UI (new dedicated UI, moved from Settings modal) -->
  </section>
  <section id="section-captions" class="content-section" hidden>
    <!-- existing caption-gen-card -->
  </section>
  <section id="section-outputs" class="content-section" hidden>
    <!-- existing outputs area -->
  </section>
</main>
```

---

### 2. `style.css` — Styles

**Add to end of file:**

```css
/* ═══════════════════════════════════════════════════════════════
   Sidebar Navigation
   ═══════════════════════════════════════════════════════════════ */
:root {
  --sidebar-width: 260px;
}

.sidebar {
  position: fixed;
  left: 0; top: 48px; bottom: 0;
  width: var(--sidebar-width);
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 50;
  transition: width .25s cubic-bezier(.32,.72,0,1), transform .25s cubic-bezier(.32,.72,0,1);
}
.sidebar.collapsed {
  width: 0;
  overflow: hidden;
}
.sidebar.open { transform: translateX(0); }

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  min-height: 48px;
}
.sidebar-brand {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--accent);
  white-space: nowrap;
  overflow: hidden;
}
.sidebar-toggle {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  color: var(--fg2);
  cursor: pointer;
  transition: background .15s, color .15s;
}
.sidebar-toggle:hover { background: var(--btn-hover); color: var(--accent); }
.sidebar.collapsed .sidebar-toggle .chevron { transform: rotate(180deg); }

.sidebar-nav { flex: 1; overflow-y: auto; padding: 8px 0; }
.nav-section { padding: 0 12px 16px; }
.nav-section-title {
  font-size: 10px;
  font-family: var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--fg3);
  margin: 8px 0 6px;
  white-space: nowrap;
  overflow: hidden;
}
.nav-items { list-style: none; margin: 0; padding: 0; }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 8px 10px;
  background: transparent; border: none; border-radius: var(--radius);
  color: var(--fg2); font-size: 13px; font-family: var(--font-mono);
  cursor: pointer; text-align: left;
  transition: background .15s, color .15s;
}
.nav-item:hover { background: var(--row-hover); color: var(--fg); }
.nav-item.active { background: var(--accent-bg); color: var(--accent); }
.nav-icon { font-size: 16px; flex-shrink: 0; width: 24px; text-align: center; }
.nav-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sidebar.collapsed .nav-label { display: none; }

/* Floater */
.sidebar-floater {
  position: fixed;
  left: 8px; top: 64px; z-index: 55;
  display: none;
}
.sidebar-floater.visible { display: block; }
.floater-toggle {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  color: var(--accent); cursor: pointer;
  box-shadow: 0 2px 8px var(--shadow-lg);
  transition: background .15s, border-color .15s;
}
.floater-toggle:hover { background: var(--btn-hover); border-color: var(--accent-soft); }
.floater-menu {
  position: absolute; left: 48px; top: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-card);
  box-shadow: 0 4px 16px var(--shadow-lg);
  padding: 6px; min-width: 180px;
  opacity: 0; visibility: hidden; transform: translateX(-8px);
  transition: opacity .15s, transform .15s, visibility .15s;
}
.floater-menu.open { opacity: 1; visibility: visible; transform: translateX(0); }
.floater-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 8px 12px;
  background: transparent; border: none; border-radius: var(--radius);
  color: var(--fg); font-size: 13px; font-family: var(--font-mono);
  cursor: pointer; text-align: left;
  transition: background .15s, color .15s;
}
.floater-item:hover { background: var(--row-hover); color: var(--accent); }
.floater-item.active { background: var(--accent-bg); color: var(--accent); }
.floater-icon { font-size: 16px; width: 24px; text-align: center; }

/* Overlay (mobile) */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  z-index: 45;
}
.sidebar-overlay.visible { display: block; }

/* Main content adjustment */
.main { padding-left: calc(var(--sidebar-width) + 24px); transition: padding-left .25s cubic-bezier(.32,.72,0,1); }
.sidebar.collapsed ~ .main { padding-left: 24px; }

/* Content sections */
.content-section { display: none; }
.content-section.active { display: block; animation: fadeIn .15s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }

/* Responsive */
@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); width: 260px; }
  .sidebar.open { transform: translateX(0); }
  .sidebar.collapsed { width: 260px; transform: translateX(-100%); }
  .sidebar-floater.visible { display: block; }
  .main { padding-left: 16px; }
}
```

---

### 3. `app.js` — Logic

**Add state variables (near top):**
```javascript
var _sidebarCollapsed = false;
var _activeSection = 'generation';
```

**Add functions (after existing helpers):**
```javascript
// ── Sidebar persistence ──
function loadSidebarState() {
  try {
    var collapsed = localStorage.getItem('ofm_sidebar_collapsed');
    if (collapsed === 'true') _sidebarCollapsed = true;
    var section = localStorage.getItem('ofm_active_section');
    if (section) _activeSection = section;
  } catch(e) {}
}

function saveSidebarState() {
  try {
    localStorage.setItem('ofm_sidebar_collapsed', _sidebarCollapsed);
    localStorage.setItem('ofm_active_section', _activeSection);
  } catch(e) {}
}

// ── Sidebar toggle ──
function toggleSidebar() {
  var sidebar = document.getElementById('sidebar');
  var floater = document.getElementById('sidebar-floater');
  var toggle = document.getElementById('sidebar-toggle');
  _sidebarCollapsed = !_sidebarCollapsed;
  sidebar.classList.toggle('collapsed', _sidebarCollapsed);
  toggle.setAttribute('aria-expanded', !_sidebarCollapsed);
  if (_sidebarCollapsed) {
    floater.classList.add('visible');
    closeFloaterMenu();
  } else {
    floater.classList.remove('visible');
  }
  saveSidebarState();
  syncPanelHeights();
}

function expandSidebar() {
  var sidebar = document.getElementById('sidebar');
  var floater = document.getElementById('sidebar-floater');
  var toggle = document.getElementById('sidebar-toggle');
  _sidebarCollapsed = false;
  sidebar.classList.remove('collapsed');
  sidebar.classList.remove('open');
  floater.classList.remove('visible');
  toggle.setAttribute('aria-expanded', 'true');
  closeFloaterMenu();
  saveSidebarState();
  syncPanelHeights();
}

function closeFloaterMenu() {
  var menu = document.getElementById('floater-menu');
  if (menu) menu.classList.remove('open');
}

function toggleFloaterMenu(e) {
  if (e) e.stopPropagation();
  var menu = document.getElementById('floater-menu');
  if (menu) menu.classList.toggle('open');
}

// ── Section switching ──
function showSection(sectionId) {
  document.querySelectorAll('.nav-item, .floater-item').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.section === sectionId);
  });
  document.querySelectorAll('.content-section').forEach(function(sec) {
    var isActive = sec.id === 'section-' + sectionId;
    sec.hidden = !isActive;
    sec.classList.toggle('active', isActive);
  });
  _activeSection = sectionId;
  saveSidebarState();
  closeFloaterMenu();
  if (window.innerWidth < 768) {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebar-overlay').classList.remove('visible');
  }
  if (sectionId === 'outputs') refreshOutputs();
  else if (sectionId === 'generation') fetchBalance();
  else if (sectionId === 'prompts') loadPromptBankUI(); // new function for Prompt Bank UI
  syncPanelHeights();
}
```

**Add to `DOMContentLoaded`:**
```javascript
document.addEventListener('DOMContentLoaded', function() {
  // ... existing init ...
  loadSidebarState();
  
  // Apply persisted state
  var sidebar = document.getElementById('sidebar');
  var floater = document.getElementById('sidebar-floater');
  var toggle = document.getElementById('sidebar-toggle');
  if (_sidebarCollapsed) {
    sidebar.classList.add('collapsed');
    floater.classList.add('visible');
    toggle.setAttribute('aria-expanded', 'false');
  }
  showSection(_activeSection); // activates correct section
  
  // Sidebar toggle
  document.getElementById('sidebar-toggle')?.addEventListener('click', toggleSidebar);
  
  // Floater toggle button
  document.getElementById('floater-toggle')?.addEventListener('click', toggleFloaterMenu);
  
  // Close floater on outside click
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.sidebar-floater')) closeFloaterMenu();
  });
  
  // Mobile overlay
  if (window.innerWidth < 768) {
    var overlay = document.getElementById('sidebar-overlay');
    overlay.onclick = function() {
      document.getElementById('sidebar').classList.remove('open');
      overlay.classList.remove('visible');
    };
  }
  
  // Keyboard: Escape closes floater
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeFloaterMenu();
  });
});
```

---

## Todo List

- [ ] **HTML**: Add sidebar + floater markup to `index.html`
- [ ] **HTML**: Wrap main content in 4 `<section id="section-*">` blocks
- [ ] **HTML**: Move Caption Generator card into `#section-captions`
- [ ] **HTML**: Move Outputs area into `#section-outputs`
- [ ] **HTML**: Move Image Generation card + Prompt Preview into `#section-generation`
- [ ] **HTML**: Create new Prompt Bank UI in `#section-prompts` (extract from Settings modal)
- [ ] **CSS**: Append sidebar/floater/overlay/styles to `style.css`
- [ ] **JS**: Add state vars (`_sidebarCollapsed`, `_activeSection`)
- [ ] **JS**: Add persistence functions (`loadSidebarState`, `saveSidebarState`)
- [ ] **JS**: Add sidebar/floater functions (`toggleSidebar`, `expandSidebar`, `toggleFloaterMenu`, `closeFloaterMenu`)
- [ ] **JS**: Add `showSection(sectionId)` with active state management
- [ ] **JS**: Wire up DOMContentLoaded listeners for sidebar toggle, floater, overlay
- [ ] **JS**: Create `loadPromptBankUI()` for dedicated Prompt Bank section
- [ ] **Verify**: `node --check webui/static/app.js` passes
- [ ] **Verify**: Manual test — collapse/expand, section switching, floater click, persist on reload, mobile drawer

---

## Notes

- **Prompt Bank UI**: Extract pool editor from Settings modal (`loadPoolEditor`, `renderPoolEditor`, etc.) into standalone `loadPromptBankUI()` — keep Settings modal for identity/upload only
- **Toolbar**: Unchanged (balance, API selector, theme, settings remain fixed top)
- **Floater behavior**: Click on floater toggle button → opens menu → click item → navigates + closes menu
- **Persist keys**: `ofm_sidebar_collapsed` (boolean), `ofm_active_section` (string)