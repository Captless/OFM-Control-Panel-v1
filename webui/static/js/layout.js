// layout.js — sidebar, section switching, equal-height panels.
// ── Sidebar state ──
var _sidebarCollapsed = false;
var _activeSection = 'generation';

document.addEventListener('DOMContentLoaded', function() {
    // ── Sidebar initialization ──
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
}

function closeFloaterMenu() {
  var menu = document.getElementById('floater-menu');
  if (menu) menu.classList.remove('open');
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
  else if (sectionId === 'settings') loadSettingsUI();
}

// ── Settings UI (Identity + Prompt Bank cards, rendered in #section-settings) ──
function loadSettingsUI() {
  loadSettings();
}
