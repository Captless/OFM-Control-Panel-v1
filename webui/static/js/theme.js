// theme.js — theme system + reduced-motion handling.
// ── Theme ──
var _themes = {
    terminal:   { name: 'Terminal',   color: '#00ff88', meta: '#0a0f0a', bg: '#0a0f0a', surface: '#0e150e' },
    paper:      { name: 'Paper',      color: '#007a33', meta: '#f0f4f0', bg: '#f0f4f0', surface: '#f7faf7' },
    'neon-pink':{ name: 'Rose Pink',  color: '#e880ad', meta: '#0a0a0a', bg: '#0a0a0a', surface: '#120a12' },
    amber:      { name: 'Amber',      color: '#ffb000', meta: '#0f0c06', bg: '#0f0c06', surface: '#16110a' },
    nord:       { name: 'Nord',       color: '#88c0d0', meta: '#10151b', bg: '#10151b', surface: '#161d26' },
    cyberpunk:  { name: 'Cyberpunk',  color: '#00e5ff', meta: '#06070c', bg: '#06070c', surface: '#0c0e18' }
};
function setTheme(name) {
    if (!_themes[name]) name = 'terminal';
    var root = document.documentElement;
    Object.keys(_themes).forEach(function(k) {
        root.classList.remove('theme-' + k);
    });
    root.classList.add('theme-' + name);
    // Force body::after repaint so gradient wave updates with new --accent-dim
    document.body.style.display = 'none';
    document.body.offsetHeight;
    document.body.style.display = '';
    var dot = document.getElementById('theme-nav-dot');
    var nm = document.getElementById('theme-nav-name');
    if (dot) dot.style.background = _themes[name].color;
    if (nm) nm.textContent = _themes[name].name;
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', _themes[name].meta);
    localStorage.setItem('ofm_theme', name);
    // Update modal if open
    if (document.getElementById('theme-modal')?.classList.contains('show')) {
        loadThemeList();
    }
}
function initTheme() {
    var saved = localStorage.getItem('ofm_theme');
    setTheme(_themes[saved] ? saved : 'terminal');
}
initTheme();
// ── Theme Modal ──
function toggleThemeModal() {
    var modal = document.getElementById('theme-modal');
    var trigger = document.getElementById('theme-nav-trigger');
    if (!modal || !trigger) return;
    if (modal.classList.contains('show')) {
        closeThemeModal();
    } else {
        modal.classList.add('show');
        trigger.setAttribute('aria-expanded', 'true');
        trigger.classList.add('open');
        loadThemeList();
        // Focus first row for keyboard nav
        setTimeout(function() {
            var first = document.querySelector('.theme-row');
            if (first) first.focus();
        }, 0);
    }
}
function closeThemeModal() {
    var modal = document.getElementById('theme-modal');
    var trigger = document.getElementById('theme-nav-trigger');
    if (modal) modal.classList.remove('show');
    if (trigger) {
        trigger.setAttribute('aria-expanded', 'false');
        trigger.classList.remove('open');
    }
}
function loadThemeList() {
    var list = document.getElementById('theme-list');
    if (!list) return;
    var active = localStorage.getItem('ofm_theme') || 'terminal';
    var html = '';
    Object.keys(_themes).forEach(function(key) {
        var t = _themes[key];
        var isActive = (key === active);
        html += '<div class="theme-row' + (isActive ? ' selected' : '') + '" data-theme="' + key + '" tabindex="0" role="radio" aria-checked="' + isActive + '" onclick="selectTheme(\'' + key + '\')" onkeydown="handleThemeKeydown(event, \'' + key + '\')">';
        html += '<span class="theme-swatch-lg" style="background:' + t.color + '"></span>';
        html += '<span class="theme-name">' + t.name + '</span>';
        html += '<span class="theme-radio" aria-hidden="true"></span>';
        html += '</div>';
    });
    list.innerHTML = html;
}
function selectTheme(name) {
    if (!_themes[name]) return;
    setTheme(name);
    closeThemeModal();
}
function handleThemeKeydown(e, name) {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        selectTheme(name);
    } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        var rows = document.querySelectorAll('.theme-row');
        var idx = Array.from(rows).findIndex(function(r) { return r.dataset.theme === name; });
        var dir = (e.key === 'ArrowDown') ? 1 : -1;
        var next = rows[(idx + dir + rows.length) % rows.length];
        if (next) next.focus();
    } else if (e.key === 'Escape') {
        closeThemeModal();
    }
}

// ESC closes theme modal
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        var modal = document.getElementById('theme-modal');
        if (modal && modal.classList.contains('show')) {
            closeThemeModal();
        }
    }
});

// Outside click closes theme modal
document.addEventListener('click', function(e) {
    var modal = document.getElementById('theme-modal');
    var trigger = document.getElementById('theme-nav-trigger');
    if (modal && modal.classList.contains('show') && !e.target.closest('#theme-modal-box') && !e.target.closest('#theme-nav-trigger')) {
        closeThemeModal();
    }
});
// ── Reduced motion listener ──
var motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
function handleMotionChange(e) {
    if (e.matches) { document.body.classList.add('reduce-motion'); }
    else { document.body.classList.remove('reduce-motion'); }
}
motionQuery.addEventListener('change', handleMotionChange);
if (motionQuery.matches) { document.body.classList.add('reduce-motion'); }
