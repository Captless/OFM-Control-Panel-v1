// theme.js — Theme switching, modal.

var _themes = [
  { id: 'creative', label: 'Creative', color: '#e880ad', bg: '#141010' },
  { id: 'paper', label: 'Paper', color: '#c2547e', bg: '#faf6f4' },
  { id: 'nord', label: 'Nord', color: '#88c0d0', bg: '#12161e' },
  { id: 'terminal', label: 'Terminal', color: '#00ff88', bg: '#0a0f0a' },
  { id: 'noir', label: 'Noir', color: '#e8e8ea', bg: '#0d0d0f' },
  { id: 'violet', label: 'Violet', color: '#a78bfa', bg: '#13101c' },
  { id: 'ocean', label: 'Ocean', color: '#2dd4bf', bg: '#081016' },
  { id: 'latte', label: 'Latte', color: '#8c5a3c', bg: '#f5efe6' },
  { id: 'rose', label: 'Rose', color: '#e0627d', bg: '#fbf4f5' },
];

var _currentTheme = 'creative';
try { _currentTheme = localStorage.getItem('ofm_theme') || 'creative'; } catch(e) {}

function setTheme(id) {
  _currentTheme = id;
  document.documentElement.className = 'theme-' + id;
  try { localStorage.setItem('ofm_theme', id); } catch(e) {}
  var dot = document.getElementById('theme-nav-dot');
  if (dot) {
    var t = _themes.find(function(x) { return x.id === id; });
    dot.style.background = t ? t.color : 'var(--accent)';
  }
  // Update theme list selection
  document.querySelectorAll('.theme-row').forEach(function(r) {
    r.classList.toggle('selected', r.dataset.theme === id);
  });
}

function initTheme() {
  setTheme(_currentTheme);
}

function toggleThemeModal() {
  var m = document.getElementById('theme-modal');
  if (!m) return;
  var isOpen = m.classList.contains('show');
  if (isOpen) { closeThemeModal(); } else { openThemeModal(); }
}

function openThemeModal() {
  var m = document.getElementById('theme-modal');
  if (!m) return;
  renderThemeList();
  m.classList.add('show');
  var trigger = document.getElementById('theme-nav-trigger');
  if (trigger) trigger.classList.add('open');
}

function closeThemeModal() {
  var m = document.getElementById('theme-modal');
  if (m) m.classList.remove('show');
  var trigger = document.getElementById('theme-nav-trigger');
  if (trigger) trigger.classList.remove('open');
}

function renderThemeList() {
  var list = document.getElementById('theme-list');
  if (!list) return;
  var html = '';
  for (var i = 0; i < _themes.length; i++) {
    var t = _themes[i];
    var sel = t.id === _currentTheme ? ' selected' : '';
    html += '<div class="theme-row' + sel + '" data-theme="' + t.id + '" onclick="selectTheme(\'' + t.id + '\')">'
      + '<span class="theme-swatch" style="background:' + t.color + ';box-shadow:0 0 8px ' + t.color + '33"></span>'
      + '<span class="theme-name">' + esc(t.label) + '</span>'
      + '<span class="theme-radio"></span>'
      + '</div>';
  }
  list.innerHTML = html;
}

function selectTheme(id) {
  setTheme(id);
  closeThemeModal();
}

// ESC to close
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    var m = document.getElementById('theme-modal');
    if (m && m.classList.contains('show')) closeThemeModal();
  }
});
