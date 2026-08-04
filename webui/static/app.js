// ── MUST be first: catch all JS errors and show on page ──
window.onerror = function(msg, url, line, col, err) {
    var el = document.getElementById('js-error');
    if (el) { el.style.display = 'block'; el.textContent = 'JS Error: ' + msg + ' (line ' + line + ')'; }
    console.error('JS Error:', msg, 'at', url, line);
    return false;
};
// Also catch unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    var el = document.getElementById('js-error');
    if (el) { el.style.display = 'block'; el.textContent = 'Unhandled Promise: ' + e.reason; }
    console.error('Unhandled Promise:', e.reason);
});

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

// ── Settings Modal ──
var _pendingAvatarUrl = '';

function _setSettingsExpanded(open) {
    var t = document.getElementById('settings-nav-trigger');
    if (t) {
        t.setAttribute('aria-expanded', open ? 'true' : 'false');
        t.classList.toggle('open', open);
    }
}

function _setSettingsStatus(msg, type) {
    var el = document.getElementById('settings-status');
    if (!el) return;
    if (!msg) { el.textContent = ''; el.className = 'settings-status'; return; }
    el.textContent = msg;
    el.className = 'settings-status' + (type ? ' ' + type : '');
}

function toggleSettingsModal() {
    var modal = document.getElementById('settings-modal');
    if (!modal) return;
    if (modal.classList.contains('show')) {
        closeSettingsModal();
    } else {
        modal.classList.add('show');
        _setSettingsExpanded(true);
        _setSettingsStatus('');
        loadSettings();
        setTimeout(function() {
            var input = document.getElementById('settings-avatar-url');
            if (input) input.focus();
        }, 50);
    }
}

function closeSettingsModal() {
    var nb = document.getElementById('new-bank-modal');
    var db = document.getElementById('delete-bank-modal');
    if ((nb && nb.classList.contains('show')) || (db && db.classList.contains('show'))) return;
    var modal = document.getElementById('settings-modal');
    if (modal) modal.classList.remove('show');
    _setSettingsExpanded(false);
    var newPreview = document.getElementById('settings-new-preview');
    if (newPreview) { newPreview.style.display = 'none'; newPreview.removeAttribute('src'); }
    var input = document.getElementById('settings-file-input');
    if (input) input.value = '';
    _pendingAvatarUrl = '';
    _setSettingsStatus('');
}

async function loadSettings() {
    var r = await api('/api/settings/identity');
    if (!r || !r.ok) { _setSettingsStatus('Failed to load settings', 'error'); return; }
    var identity = r.identity || {};
    var name = document.getElementById('settings-identity-name');
    if (name) name.textContent = identity.name || 'Unnamed identity';
    var preview = document.getElementById('settings-avatar-preview');
    if (preview) {
        if (identity.avatar_url) {
            preview.src = identity.avatar_url;
            preview.style.display = 'block';
        } else {
            preview.removeAttribute('src');
            preview.style.display = 'none';
        }
    }
    var urlInput = document.getElementById('settings-avatar-url');
    if (urlInput) {
        urlInput.value = identity.avatar_url || '';
        urlInput.placeholder = identity.avatar_url ? '' : 'https://\u2026';
    }
    await loadBankEditor();
}

// ── Prompt bank editor (single pane, collapsed pool cards) ──

var _activeBankId = '';
var _savedBanks = {};
var _poolDefaults = {};
var _poolActive = {};
var _newBankSource = 'builtin';
var _pendingDeleteId = null;

var _POOL_LABELS = {
    'INDOOR_SCENES': 'Indoor Scenes',
    'MIRROR_SCENES': 'Mirror Scenes',
    'OUTDOOR_SCENES': 'Outdoor Scenes',
    'FRAMING': 'Framing',
    'HAIR': 'Hair',
    'POSES': 'Poses',
    'QUALITY': 'Quality',
    'OUTFIT_TOPS_POOLS': 'Outfit Tops',
    'OUTFIT_BOTTOMS_POOLS': 'Outfit Bottoms',
    'LIGHTING_POOLS': 'Lighting',
    'DEFAULT_NEGATIVE': 'Default Negative',
    'MIRROR_NEGATIVE': 'Mirror Negative',
    'IDENTITY_LOCK': 'Identity Lock'
};

function _isDictPool(name) {
    return name === 'OUTFIT_TOPS_POOLS' || name === 'OUTFIT_BOTTOMS_POOLS' || name === 'LIGHTING_POOLS';
}

function _isStrPool(name) {
    return name === 'DEFAULT_NEGATIVE' || name === 'MIRROR_NEGATIVE' || name === 'IDENTITY_LOCK';
}

function _poolLabel(name) {
    return _POOL_LABELS[name] || name;
}

function _poolTypeBadge(name) {
    if (_isDictPool(name)) return 'styles';
    if (_isStrPool(name)) return 'text';
    return 'list';
}

function _poolSummary(name, val) {
    if (val == null) return 'empty';
    if (_isDictPool(name)) return Object.keys(val).length + ' style' + (Object.keys(val).length !== 1 ? 's' : '');
    if (_isStrPool(name)) {
        var s = String(val).trim();
        return s.length > 42 ? s.substring(0, 42) + '\u2026' : (s || 'empty');
    }
    return (Array.isArray(val) ? val.length : 0) + ' item' + ((Array.isArray(val) && val.length !== 1) ? 's' : '');
}

function _poolToText(name, val) {
    if (_isDictPool(name)) {
        var obj = val || {};
        var lines = [];
        Object.keys(obj).forEach(function(k) {
            var items = (Array.isArray(obj[k]) ? obj[k] : []).join(', ');
            lines.push(k + ': ' + items);
        });
        return lines.join('\n');
    }
    if (_isStrPool(name)) return String(val == null ? '' : val);
    return (Array.isArray(val) ? val : []).join('\n');
}

function _poolValToString(name, val) {
    if (val == null) return '';
    if (_isDictPool(name)) return JSON.stringify(val || {});
    if (_isStrPool(name)) return String(val);
    return JSON.stringify(val || []);
}

async function loadActiveBank() {
    var data = await api('/api/settings/banks/active');
    _activeBankId = (data && data.active) || '';
}

function getSelectedBankId() {
    return _activeBankId;
}

function toggleActiveBankEditor() {
    var header = document.getElementById('active-bank-header');
    var wrap = document.getElementById('pool-editor-wrapper');
    if (!header || !wrap) return;
    var closed = wrap.classList.toggle('closed');
    header.classList.toggle('open', !closed);
    header.setAttribute('aria-expanded', closed ? 'false' : 'true');
}

function updateActiveBankHeader() {
    var nameEl = document.getElementById('active-bank-name');
    if (!nameEl) return;
    nameEl.textContent = _activeBankId ? ((_savedBanks[_activeBankId] && _savedBanks[_activeBankId].name) || _activeBankId) : 'Default';
}

function setActiveBankFromRadio(el) {
    var id = (el.dataset && el.dataset.bankId) || '';
    if (id === 'builtin') id = '';
    if (id === _activeBankId) return;
    api('/api/settings/banks/active', {id: id}).then(function(r) {
        if (r && r.ok) {
            _activeBankId = (r.active || '');
            showSuccess(id ? 'Active prompt bank set' : 'Using Default prompt bank');
            loadPoolEditor();
            renderBankList();
        } else {
            showError((r && (r.error || r.output)) || 'Failed to set active bank');
            renderBankList();
        }
    });
}

async function loadPoolEditor() {
    var defRes = await api('/api/settings/banks/pools/defaults');
    var actRes = await api('/api/settings/banks/active/pools');
    _poolDefaults = (defRes && defRes.pools) ? defRes.pools : {};
    _poolActive = (actRes && actRes.pools) ? actRes.pools : {};
    renderPoolEditor();
}

function renderPoolEditor() {
    var list = document.getElementById('pool-editor-list');
    if (!list) return;
    var names = Object.keys(_poolDefaults);
    if (!names.length) { list.innerHTML = '<div class="settings-hint">No pools available</div>'; return; }
    var readOnly = !_activeBankId;
    var html = '';
    if (readOnly) {
        html += '<div id="pool-editor-note" class="pool-editor-note">Default (read-only) \u2014 create a new bank to edit pools.</div>';
    }
    for (var i = 0; i < names.length; i++) {
        var name = names[i];
        var val = (_poolActive && _poolActive[name] !== undefined) ? _poolActive[name] : _poolDefaults[name];
        var text = _poolToText(name, val);
        html += '<div class="pool-card" data-pool="' + name + '">';
        html += '<div class="pool-card-header">';
        html += '<span class="pool-name">' + _poolLabel(name) + '</span>';
        html += '<span class="pool-badge">' + _poolTypeBadge(name) + '</span>';
        html += '<span class="pool-summary">' + esc(_poolSummary(name, val)) + '</span>';
        html += '</div>';
        html += '<div class="pool-card-body">';
        html += '<div class="settings-hint">' + (_isDictPool(name) ? 'One style per line: style_name: item1, item2' : (_isStrPool(name) ? 'Single text line (wraps in editor)' : 'One item per line')) + '</div>';
        if (_isStrPool(name)) {
            html += '<textarea class="pool-input pool-input-str" data-pool="' + name + '" spellcheck="false" rows="3"' + (readOnly ? ' readonly' : '') + '>' + esc(text) + '</textarea>';
        } else {
            html += '<textarea class="pool-input" data-pool="' + name + '" spellcheck="false" rows="5"' + (readOnly ? ' readonly' : '') + '>' + esc(text) + '</textarea>';
        }
        html += '</div>';
        html += '</div>';
    }
    list.innerHTML = html;
    setPoolEditorVisible();
}

function resetPoolToBuiltin(name) {
    var card = document.querySelector('.pool-card[data-pool="' + name + '"]');
    var input = card ? card.querySelector('.pool-input') : null;
    if (input) input.value = _poolToText(name, _poolDefaults[name]);
}

function resetAllPoolsToBuiltin() {
    var cards = document.querySelectorAll('.pool-card');
    for (var i = 0; i < cards.length; i++) {
        var name = cards[i].dataset.pool;
        var input = cards[i].querySelector('.pool-input');
        if (input) input.value = _poolToText(name, _poolDefaults[name]);
    }
    showInfo('Pools reset \u2014 remember to Save Changes');
}

function collectPoolChanges() {
    var pools = {};
    var cards = document.querySelectorAll('.pool-card');
    for (var i = 0; i < cards.length; i++) {
        var name = cards[i].dataset.pool;
        var input = cards[i].querySelector('.pool-input');
        if (!input) continue;
        var val;
        try {
            val = _textToPool(name, input.value);
        } catch (e) {
            return {error: name + ': ' + e.message};
        }
        if (_poolValToString(name, val) !== _poolValToString(name, _poolDefaults[name])) {
            pools[name] = val;
        }
    }
    return pools;
}

function _textToPool(name, text) {
    if (_isDictPool(name)) {
        var obj = {};
        (text || '').split('\n').forEach(function(line) {
            line = line.trim();
            if (!line) return;
            var idx = line.indexOf(':');
            if (idx === -1) throw new Error('expected "style_name: item1, item2" per line');
            var key = line.substring(0, idx).trim();
            if (!key) throw new Error('missing style name');
            obj[key] = line.substring(idx + 1).split(',').map(function(s) { return s.trim(); }).filter(Boolean);
        });
        return obj;
    }
    if (_isStrPool(name)) return text.trim().split(/\s+/).join(' ');
    return text.split('\n').map(function(s) { return s.trim(); }).filter(Boolean);
}

async function saveAllPoolChanges() {
    var pools = collectPoolChanges();
    if (pools.error) { showError('Invalid ' + pools.error); return; }
    var keys = Object.keys(pools);
    if (!keys.length) { showInfo('No changes to save'); return; }
    if (_activeBankId) {
        var r = await api('/api/settings/banks/update', {id: _activeBankId, pools: pools});
        if (r && r.ok) { showSuccess('Changes saved'); await loadPoolEditor(); renderBankList(); }
        else { showError((r && (r.error || r.output)) || 'Save failed'); }
    } else {
        openNewBankModalFromDefault();
    }
}

async function createBankFromCurrent() {
    openNewBankModalFromDefault();
}

function openNewBankModalFromDefault() {
    _newBankSource = 'builtin';
    var modal = document.getElementById('new-bank-modal');
    if (!modal) return;
    var h4 = modal.querySelector('.modal-header h4');
    var p = modal.querySelector('.modal-header p');
    if (h4) h4.textContent = 'Create Prompt Bank';
    if (p) p.textContent = 'Starts with default pools \u2014 customize from there';
    var input = document.getElementById('new-bank-name');
    if (input) input.value = '';
    var st = document.getElementById('new-bank-status');
    if (st) { st.textContent = ''; st.className = 'new-bank-status'; }
    modal.classList.add('show');
    setTimeout(function() { if (input) input.focus(); }, 30);
}

function closeNewBankModal() {
    var modal = document.getElementById('new-bank-modal');
    if (modal) modal.classList.remove('show');
}

function _createBankWithName(name) {
    if (_newBankSource === 'builtin') {
        return api('/api/settings/banks/create', {name: name, pools: _poolDefaults});
    }
    if (_activeBankId) {
        return api('/api/settings/banks/clone', {source_id: _activeBankId, name: name});
    }
    return api('/api/settings/banks/create', {name: name, pools: _poolDefaults});
}

async function submitNewBank() {
    var input = document.getElementById('new-bank-name');
    var st = document.getElementById('new-bank-status');
    var name = (input.value || '').trim();
    if (!name) {
        if (st) { st.textContent = 'Enter a bank name'; st.className = 'new-bank-status error'; }
        if (input) input.focus();
        return;
    }
    var r = await _createBankWithName(name);
    if (r && r.ok) {
        _activeBankId = r.bank.id;
        closeNewBankModal();
        showSuccess('Bank created: ' + name);
        await loadPoolEditor(); renderBankList();
    } else {
        if (st) { st.textContent = (r && (r.error || r.output)) || 'Create failed'; st.className = 'new-bank-status error'; }
    }
}

function setPoolEditorVisible() {
    var wrap = document.getElementById('pool-editor-wrapper');
    if (!wrap) return;
    var readOnly = !_activeBankId;
    wrap.classList.toggle('readonly', readOnly);
    var actions = document.querySelector('.pool-editor-actions');
    if (actions) actions.classList.toggle('hidden', readOnly);
    var note = document.getElementById('pool-editor-note');
    if (note) note.classList.toggle('hidden', !readOnly);
}

async function loadBankEditor() {
    await loadActiveBank();
    await Promise.all([loadPoolEditor(), renderBankList()]);
}

async function renderBankList() {
    var list = document.getElementById('settings-bank-list');
    if (!list) return;
    var data = await api('/api/settings/banks');
    var banks = (data && data.banks) ? data.banks : {};
    _savedBanks = banks;
    var ids = Object.keys(banks);
    var html = '';
    for (var i = 0; i < ids.length; i++) {
        var b = banks[ids[i]] || {};
        var poolCount = Object.keys(b.pools || {}).length;
        var isBuiltin = (ids[i] === 'builtin');
        var isActive = isBuiltin ? (!_activeBankId) : (ids[i] === _activeBankId);
        html += '<div class="bank-row' + (isActive ? ' active' : '') + (isBuiltin ? ' is-builtin' : '') + '">';
        html += '<div class="bank-row-main">';
        html += '<div class="bank-name-wrap">';
        html += '<button type="button" class="bank-name' + (isBuiltin ? ' is-builtin' : '') + '" onclick="startInlineRename(\'' + esc(ids[i]) + '\', this)"' + (isBuiltin ? '' : ' title="Click to rename"') + ' aria-label="Rename ' + esc(b.name || ids[i]) + '">' + esc(b.name || ids[i]) + '</button>';
        html += '<input type="text" class="bank-rename-input" data-bank-id="' + esc(ids[i]) + '" hidden>';
        html += '</div>';
        html += '<span class="bank-count">' + (isBuiltin ? 'Default' : poolCount + ' override' + (poolCount !== 1 ? 's' : '')) + '</span>';
        html += '</div>';
        html += '<div class="bank-row-select">';
        html += '<label class="provider-toggle" title="' + (isActive ? 'Active prompt bank' : 'Set as active') + '">';
        html += '<input type="radio" name="active-bank" data-bank-id="' + esc(ids[i]) + '"' + (isActive ? ' checked' : '') + ' onchange="setActiveBankFromRadio(this)">';
        html += '<span class="toggle-slider"></span>';
        html += '</label>';
        html += '</div>';
        html += '<div class="bank-row-actions">';
        if (!isBuiltin) {
            html += '<button type="button" class="btn btn-sm btn-outline" onclick="event.stopPropagation(); confirmDeleteBank(\'' + esc(ids[i]) + '\')" aria-label="Delete ' + esc(b.name || ids[i]) + '">Delete</button>';
        }
        html += '</div></div>';
    }
    list.innerHTML = html || '<div class="settings-hint empty-state">No saved banks yet. <button type="button" class="btn-link" onclick="event.stopPropagation(); openNewBankModalFromDefault()">Create your first bank</button></div>';
    updateActiveBankHeader();
    setPoolEditorVisible();
}

function startInlineRename(id, btn) {
    if (id === 'builtin') { showInfo('Default pools are read-only'); return; }
    var wrap = btn.parentElement;
    var input = wrap.querySelector('.bank-rename-input');
    if (!input) return;
    var old = btn.textContent.trim();
    input.value = old;
    input.hidden = false;
    btn.style.display = 'none';
    input.focus();
    input.select();
    var done = false;
    var finish = function(save) {
        if (done) return;
        done = true;
        var val = input.value.trim();
        if (save && val && val !== old) {
            api('/api/settings/banks/update', {id: id, name: val}).then(function(r) {
                if (r && r.ok) { showSuccess('Bank renamed'); renderBankList(); }
                else { showError((r && (r.error || r.output)) || 'Rename failed'); renderBankList(); }
            });
        } else {
            input.hidden = true;
            btn.style.display = '';
        }
    };
    input.onkeydown = function(e) {
        if (e.key === 'Enter') { e.preventDefault(); finish(true); }
        else if (e.key === 'Escape') { e.preventDefault(); finish(false); }
    };
    input.onblur = function() { finish(true); };
}

function confirmDeleteBank(id) {
    _pendingDeleteId = id;
    var b = _savedBanks[id] || {};
    var nameEl = document.querySelector('#delete-bank-modal .delete-bank-name');
    if (nameEl) nameEl.textContent = b.name || id;
    var modal = document.getElementById('delete-bank-modal');
    if (modal) modal.classList.add('show');
}

function closeDeleteBankModal() {
    _pendingDeleteId = null;
    var modal = document.getElementById('delete-bank-modal');
    if (modal) modal.classList.remove('show');
}

async function executeDeleteBank() {
    var id = _pendingDeleteId;
    if (!id) return;
    var r = await api('/api/settings/banks/delete', {id: id});
    closeDeleteBankModal();
    if (r && r.ok) {
        if (_activeBankId === id) _activeBankId = '';
        showSuccess('Bank deleted');
        await loadActiveBank();
        await loadPoolEditor(); renderBankList();
    } else {
        showError((r && (r.error || r.output)) || 'Delete failed');
    }
}

function loadAvatarUrl() {
    var input = document.getElementById('settings-avatar-url');
    var url = (input.value || '').trim();
    if (!url) { _setSettingsStatus('Enter an image URL first', 'error'); return; }
    if (!/^https?:\/\//i.test(url)) {
        _setSettingsStatus('Must be a public http(s) URL (local paths won\u2019t reach WaveSpeed)', 'error');
        return;
    }
    _pendingAvatarUrl = url;
    var preview = document.getElementById('settings-new-preview');
    preview.onerror = function() {
        _setSettingsStatus('Could not load image from that URL', 'error');
        preview.style.display = 'none';
    };
    preview.onload = function() {
        preview.style.display = 'block';
        _setSettingsStatus('Ready to save', 'ok');
    };
    preview.style.display = 'block';
    _setSettingsStatus('Loading image\u2026', '');
    preview.src = url + (url.indexOf('?') === -1 ? '?' : '&') + '_t=' + Date.now();
}

async function handleAvatarFile(file) {
    if (!file) return;
    if (!file.type || file.type.indexOf('image/') !== 0) {
        _setSettingsStatus('Invalid file type: images only', 'error');
        return;
    }
    if (file.size > 5 * 1024 * 1024) {
        _setSettingsStatus('File too large: max 5MB', 'error');
        return;
    }
    var zone = document.getElementById('settings-upload-zone');
    if (zone) zone.classList.remove('drag-over');
    _setSettingsStatus('Uploading\u2026', '');
    var fd = new FormData();
    fd.append('file', file);
    try {
        var resp = await fetch('/api/settings/identity/upload', { method: 'POST', body: fd });
        var data = await resp.json();
        if (!data.ok) {
            _setSettingsStatus(data.error || 'Upload failed', 'error');
            return;
        }
        _pendingAvatarUrl = data.avatar_url || data.url;
        var preview = document.getElementById('settings-new-preview');
        preview.onerror = null;
        preview.onload = function() { preview.style.display = 'block'; };
        preview.style.display = 'block';
        preview.src = data.url + (data.url.indexOf('?') === -1 ? '?' : '&') + '_t=' + Date.now();
        if (data.uploaded) {
            _setSettingsStatus('Uploaded \u2014 public WaveSpeed URL ready. Save to apply.', 'ok');
        } else {
            _setSettingsStatus('Saved locally. ' + (data.warning || 'Paste a public URL for generation.'), 'error');
        }
    } catch(e) {
        _setSettingsStatus('Upload error: ' + e.message, 'error');
    }
}

async function saveIdentity() {
    if (!_pendingAvatarUrl) { closeSettingsModal(); return; }
    var r = await api('/api/settings/identity', { avatar_url: _pendingAvatarUrl });
    if (r && r.ok) {
        closeSettingsModal();
        showSuccess('Identity saved');
        loadSettings();
    } else {
        _setSettingsStatus((r && (r.error || r.output)) || 'Failed to save identity', 'error');
    }
}

// ESC closes settings modal
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        var db = document.getElementById('delete-bank-modal');
        if (db && db.classList.contains('show')) { closeDeleteBankModal(); return; }
        var nb = document.getElementById('new-bank-modal');
        if (nb && nb.classList.contains('show')) { closeNewBankModal(); return; }
        var modal = document.getElementById('settings-modal');
        if (modal && modal.classList.contains('show')) {
            closeSettingsModal();
        }
    }
});

// Outside click closes settings modal
document.addEventListener('click', function(e) {
    var modal = document.getElementById('settings-modal');
    var trigger = document.getElementById('settings-nav-trigger');
    var nb = document.getElementById('new-bank-modal');
    var db = document.getElementById('delete-bank-modal');
    if (db && db.classList.contains('show') && !e.target.closest('#delete-bank-modal-box')) {
        closeDeleteBankModal();
        return;
    }
    if (nb && nb.classList.contains('show') && !e.target.closest('#new-bank-modal-box')) {
        closeNewBankModal();
        return;
    }
    if (modal && modal.classList.contains('show') && !e.target.closest('#settings-modal-box') && !e.target.closest('#settings-nav-trigger')) {
        closeSettingsModal();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    var modal = document.getElementById('settings-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) closeSettingsModal();
        });
    }
    var fileInput = document.getElementById('settings-file-input');
    var zone = document.getElementById('settings-upload-zone');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            handleAvatarFile(fileInput.files[0]);
        });
    }
    if (zone) {
        zone.addEventListener('click', function() { if (fileInput) fileInput.click(); });
        zone.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); if (fileInput) fileInput.click(); }
        });
        zone.addEventListener('dragover', function(e) {
            e.preventDefault();
            zone.classList.add('drag-over');
        });
        zone.addEventListener('dragleave', function() {
            zone.classList.remove('drag-over');
        });
        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            zone.classList.remove('drag-over');
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
                handleAvatarFile(e.dataTransfer.files[0]);
            }
        });
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

// ── Status tracking (localStorage) ──
// ── API helpers ──
function setLive(state, msg) {
    var el = document.getElementById('live-indicator');
    var dt = document.getElementById('live-dot');
    var tx = document.getElementById('live-text');
    if (!el) return;
    el.className = 'live';
    if (state === 'ok') { el.classList.add('ok'); dt.style.background = '#00ff88'; tx.textContent = msg || 'Live'; }
    else if (state === 'loading') { el.classList.add('loading'); dt.style.background = '#ffb000'; tx.textContent = msg || 'Loading...'; }
    else { el.classList.add('error'); dt.style.background = '#ff6b6b'; tx.textContent = msg || 'Error'; }
}

async function api(url, body) {
    try {
        var r = await fetch(url, {
            method: body ? 'POST' : 'GET',
            headers: body ? {'Content-Type': 'application/json'} : {},
            body: body ? JSON.stringify(body) : undefined,
        });
        if (!r.ok) { setLive('error', r.status); return {ok: false, output: 'HTTP ' + r.status}; }
        var data = await r.json();
        setLive('ok', 'Live');
        return data;
    } catch (e) {
        setLive('error', 'Offline');
        console.error('API error:', url, e);
        return {ok: false, output: 'Network error: ' + e.message};
    }
}

// ── Photo Generation Controls ──

function getSelectedVibe() {
    var radios = document.querySelectorAll('input[name="vibe"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "indoor";
}

function getSelectedCamera() {
    var radios = document.querySelectorAll('input[name="camera_style"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "handheld";
}

function getSelectedLighting() {
    var radios = document.querySelectorAll('input[name="lighting"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "warm";
}

function getSelectedTime() {
    var radios = document.querySelectorAll('input[name="time_of_day"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "day";
}

function getSelectedOutfitStyle() {
    var radios = document.querySelectorAll('input[name="outfit_style"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "any";
}

function onVibeChange() {
    updateCost();
}

function onCameraChange() {
    var camera = getSelectedCamera();
    var vibe = getSelectedVibe();
    var outdoorPill = document.querySelector('input[name="vibe"][value="outdoor"]');
    if (camera === "mirror" && vibe === "outdoor") {
        // Auto-switch to "indoor" when mirror + outdoor conflict
        var indoorPill = document.querySelector('input[name="vibe"][value="indoor"]');
        if (indoorPill) indoorPill.checked = true;
    }
    // Grey out/outdoor pill when mirror is selected
    if (outdoorPill) {
        outdoorPill.disabled = (camera === "mirror");
        if (camera === "mirror") {
            outdoorPill.parentElement.style.opacity = "0.4";
            outdoorPill.parentElement.style.pointerEvents = "none";
        } else {
            outdoorPill.parentElement.style.opacity = "1";
            outdoorPill.parentElement.style.pointerEvents = "auto";
        }
    }
    updateCost();
}

var _balance = 0;
var _perPhoto = 0.07;
var _pendingJobs = null;

async function fetchBalance() {
    var data = await api('/api/balance');
    if (data && typeof data.balance === 'number') {
        _balance = data.balance;
        _perPhoto = data.per_photo || 0.07;
    }
    var bpActive = document.getElementById('bp-active');
    if (bpActive) bpActive.textContent = '$' + _balance.toFixed(2);
    try {
        var r = await fetch('/api/balance/total');
        var totalData = await r.json();
        var bpTotal = document.getElementById('bp-total');
        if (bpTotal && typeof totalData.total === 'number') {
            bpTotal.textContent = '$' + totalData.total.toFixed(2) + ' total';
        }
    } catch(e) {
        console.error('fetchBalance total error:', e);
    }
    var slider = document.getElementById('photo-count');
    var label = document.getElementById('photo-count-label');
    if (slider && _perPhoto > 0) {
        var maxCount = Math.min(Math.floor(_balance / _perPhoto), 30);
        slider.max = Math.max(maxCount, 1);
        if (parseInt(slider.value) > maxCount) {
            slider.value = maxCount;
            if (label) label.textContent = maxCount;
        }
    }
    updateCost();
}

async function refreshBalance() {
    var btn = document.getElementById('bp-refresh');
    if (btn) btn.classList.add('spin');
    await fetchBalance();
    if (btn) setTimeout(function() { btn.classList.remove('spin'); }, 500);
}

function updateCost() {
    var count = parseInt(document.getElementById('photo-count').value) || 0;
    var total = (count * _perPhoto).toFixed(2);
    var el = document.getElementById('cost-tracker');
    if (!el) return;
    el.textContent = '$' + total + ' · $' + _balance.toFixed(2);
}

function _btnTxt(t) { var e = document.querySelector('#btn-photo .btn-text'); if (e) e.textContent = t; }

function _resetBtn() { var btn = document.getElementById('btn-photo'); if (btn) { btn.classList.remove('loading'); btn.disabled = false; } _btnTxt('Generate'); setControlsLocked(false); }

function setControlsLocked(locked) {
    var card = document.querySelector('.gen-layout .card');
    if (!card) return;
    card.classList.toggle('controls-locked', locked);
    var inputs = card.querySelectorAll('input');
    for (var i = 0; i < inputs.length; i++) {
        inputs[i].disabled = locked;
    }
}

// ── Toast notifications ──

var _toastContainer = null;

function _getToastContainer() {
    if (!_toastContainer) _toastContainer = document.getElementById('toast-container');
    return _toastContainer;
}

function showToast(message, type, duration) {
    var c = _getToastContainer();
    if (!c) return;
    type = type || 'info';
    duration = duration || 4000;
    var t = document.createElement('div');
    t.className = 'toast ' + type;
    t.setAttribute('role', 'alert');
    var msg = document.createElement('span');
    msg.className = 'toast-msg';
    msg.textContent = message;
    var close = document.createElement('span');
    close.className = 'toast-close';
    close.textContent = '\u00d7';
    close.title = 'Dismiss';
    t.appendChild(msg);
    t.appendChild(close);
    c.appendChild(t);
    var remove = function() {
        if (!t.parentNode) return;
        t.classList.add('out');
        setTimeout(function() { if (t.parentNode) t.parentNode.removeChild(t); }, 250);
    };
    close.addEventListener('click', remove);
    var timer = setTimeout(remove, duration);
    t.addEventListener('mouseenter', function() { clearTimeout(timer); });
    t.addEventListener('mouseleave', function() { timer = setTimeout(remove, duration); });
}

function showError(message, duration) { showToast(message, 'error', duration || 6000); }
function showSuccess(message, duration) { showToast(message, 'success', duration || 4000); }
function showInfo(message, duration) { showToast(message, 'info', duration || 4000); }
function showWarning(message, duration) { showToast(message, 'warning', duration || 5000); }

async function startPromptGeneration() {
    var btn = document.getElementById('btn-photo');
    var vibe = getSelectedVibe();
    var camera_style = getSelectedCamera();
    var lighting = getSelectedLighting();
    var time_of_day = getSelectedTime();
    var outfit_style = getSelectedOutfitStyle();
    var count = parseInt(document.getElementById('photo-count').value) || 6;
    setControlsLocked(true);
    btn.disabled = true;
    btn.classList.add('loading'); _btnTxt('Generating prompts\u2026');
    var r = await api('/api/prompts/generate', {vibe: vibe, camera_style: camera_style, lighting: lighting, time_of_day: time_of_day, outfit_style: outfit_style, count: count, bank_id: getSelectedBankId()});
    if (!r.ok) {
        _btnTxt('FAIL: ' + (r.error || 'error'));
        showError('Prompt build failed: ' + (r.error || 'error'));
        fetchBalance();
        setTimeout(_resetBtn, 3000);
        return;
    }
    _pendingJobs = r.jobs;
    var list = document.getElementById('prompt-list');
    var html = '';
    for (var i = 0; i < r.jobs.length; i++) {
        var prompt = r.jobs[i].prompt || '';
        html += '<div class="prompt-item" data-idx="' + i + '">';
        html += '<span class="pnum">PROMPT</span>';
        html += '<pre>' + esc(prompt) + '</pre>';
        html += '<textarea>' + prompt + '</textarea>';
        html += '</div>';
    }
    list.innerHTML = html;
    document.getElementById('confirm-gen-btn').style.display = 'inline-block';
    document.getElementById('confirm-gen-btn').disabled = false;
    document.getElementById('cancel-gen-btn').style.display = 'inline-block';
    document.getElementById('edit-prompts-btn').style.display = 'inline-block';
    _btnTxt('Review prompts \u2192 confirm');
    syncPanelHeights();
}

function _resetPromptList() {
    document.getElementById('prompt-list').innerHTML = '<div class="prompt-empty">' +
        '<span class="prompt-empty-icon"><svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V4z"/><line x1="2" y1="10" x2="6" y2="10"/><line x1="2" y1="7" x2="5" y2="7"/></svg></span>' +
        '<p>No prompts yet</p>' +
        '<p class="prompt-empty-sub">Select options and click Generate to build prompts for review and editing before confirming generation.</p>' +
        '</div>';
    document.getElementById('confirm-gen-btn').style.display = 'none';
    document.getElementById('cancel-gen-btn').style.display = 'none';
    document.getElementById('edit-prompts-btn').style.display = 'none';
    document.getElementById('edit-prompts-btn').textContent = 'Edit';
    document.getElementById('confirm-gen-btn').disabled = false;
    syncPanelHeights();
}

async function confirmGeneration() {
    var btn = document.getElementById('btn-photo');
    var items = document.querySelectorAll('.prompt-item');
    var jobs = [];
    for (var i = 0; i < items.length; i++) {
        var ta = items[i].querySelector('textarea');
        var prompt = ta ? ta.value : '';
        if (prompt.trim()) {
            var orig = _pendingJobs && _pendingJobs[i] ? _pendingJobs[i] : {};
            jobs.push({
                prompt: prompt,
                filename: orig.filename || String(i + 1).padStart(3, '0') + '_' + Date.now().toString(36) + '.png'
            });
        }
    }
    if (!jobs.length) return;
    _resetPromptList();
    btn.disabled = true;
    btn.classList.add('loading'); _btnTxt('Generating ' + jobs.length + '\u2026');
    var r2 = await api('/api/run/photo', {prompts: jobs});
    if (!r2.ok) {
        _btnTxt('FAIL: ' + (r2.output || 'error'));
        showError('Failed to start generation: ' + (r2.output || 'error'));
        fetchBalance();
        setTimeout(_resetBtn, 3000);
        return;
    }
    var runId = r2.run_id;
    var _startTs = Date.now();
    var _lastDetail = '';
    var _lastChangeTime = Date.now();
    var _retryCount = 0;
    var _maxRetries = 3;
    var _deadline = Date.now() + 45 * 60 * 1000;
var _fail = function(msg) {
        btn.classList.remove('loading');
        _btnTxt(msg);
        fetchBalance();
        setTimeout(_resetBtn, 3000);
    };

    var _stageMap = {
        'submitting': 'Submitting',
        'generating': 'Generating',
        'polling': 'Processing',
        'downloading': 'Downloading',
        'enhancing': 'Enhancing',
        'complete': 'Complete'
    };
    var _friendlyStage = function(stage) {
        return _stageMap[stage] || (stage ? stage.charAt(0).toUpperCase() + stage.slice(1) : 'Running');
    };

    while (Date.now() < _deadline) {
        var p = await api('/api/progress?run_id=' + runId);
        if (p && p.done === true) {
            if (p.error_type === 'explicit_content') {
                _btnTxt('FAIL: content flagged');
                btn.classList.remove('loading');
                showWarning('Generation blocked \u2014 WaveSpeed flagged content as sensitive. Try different prompts or outfit style.', 8000);
            } else if (p.ok) {
                _btnTxt('OK (' + p.duration_s + 's)');
                btn.classList.remove('loading');
                refreshOutputs(); showSuccess('Generation complete \u2014 ' + p.duration_s + 's');
            } else {
                _btnTxt('FAIL: ' + (p.detail || 'error'));
                btn.classList.remove('loading');
                showError('Generation failed: ' + (p.detail || 'error'));
            }
            fetchBalance();
            setTimeout(_resetBtn, 3000);
            _pendingJobs = null;
            _resetPromptList();
            break;
        }
        if (!p || p.error || typeof p.done !== 'boolean') {
            _fail('FAIL: run not found (server restarted?)');
            _pendingJobs = null;
            _resetPromptList();
            break;
        }
        var stage = p.stage ? _friendlyStage(p.stage) : 'Running';
        var detail = stage + (p.detail ? ': ' + p.detail : '');
        if (p.total > 0) detail += ' (' + p.current + '/' + p.total + ')';
        if (detail !== _lastDetail) {
            _lastDetail = detail;
            _lastChangeTime = Date.now();
        }
        var updatedAt = (typeof p.updated_at === 'number') ? p.updated_at : (_lastChangeTime / 1000);
        var elapsed = Math.floor(Date.now() / 1000 - updatedAt);
        if (elapsed >= 300 && _retryCount < _maxRetries) {
            _retryCount++;
            _btnTxt('Reconnecting\u2026');
            var r3 = await api('/api/run/photo', {prompts: jobs});
            if (r3.ok) {
                runId = r3.run_id;
                _startTs = Date.now();
                _lastDetail = '';
                _lastChangeTime = Date.now();
                continue;
            } else {
                _fail('FAIL: retry ' + _retryCount + ' failed');
                _pendingJobs = null;
                _resetPromptList();
                break;
            }
        }
        if (elapsed >= 300) {
            _fail('FAIL: generation stalled');
            _pendingJobs = null;
            _resetPromptList();
            break;
        }
        _btnTxt(stage + ' ' + (p.total > 0 ? p.current + '/' + p.total + ' \u00b7 ' : '') + Math.floor((Date.now() - _startTs) / 1000) + 's');
        await new Promise(r3 => setTimeout(r3, 1000));
    }
    if (Date.now() >= _deadline) {
        _fail('FAIL: timed out after 45 min');
        _pendingJobs = null;
        _resetPromptList();
    }
}

function toggleEditPrompts() {
    var items = document.querySelectorAll('.prompt-item');
    var btn = document.getElementById('edit-prompts-btn');
    var confirmBtn = document.getElementById('confirm-gen-btn');
    var editing = items.length > 0 && items[0].classList.contains('editing');
    if (editing) {
        for (var i = 0; i < items.length; i++) {
            var pre = items[i].querySelector('pre');
            var ta = items[i].querySelector('textarea');
            if (pre && ta) pre.textContent = ta.value;
        }
    }
    for (var i = 0; i < items.length; i++) {
        items[i].classList.toggle('editing', !editing);
    }
    confirmBtn.disabled = !editing;
    btn.textContent = editing ? 'Edit' : 'Confirm';
}

function cancelGeneration() {
    _resetPromptList();
    _pendingJobs = null;
    _resetBtn();
}

// ── Outputs table ──
var _outputsData = [];

function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

var _preview = null;
var _viewMode = 'table';
try { _viewMode = localStorage.getItem('ofm_view_mode') || 'table'; } catch(e) {}

function setViewMode(mode) {
    _viewMode = (mode === 'grid') ? 'grid' : 'table';
    try { localStorage.setItem('ofm_view_mode', _viewMode); } catch(e) {}
    syncViewToggle();
    var area = document.getElementById('outputs-area');
    if (area) renderOutputs();
}

function syncViewToggle() {
    document.querySelectorAll('.view-toggle button').forEach(function(b) {
        var on = b.dataset.view === _viewMode;
        b.classList.toggle('active', on);
        b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
}

var _cpySvg = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
var _dlSvg = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>';
var _delSvg = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>';

function _batchCount(b) {
    var t = b.items.length + ' item' + (b.items.length !== 1 ? 's' : '');
    var vids = b.items.filter(function(it) { return it.is_video; }).length;
    if (vids) t += ' \u00b7 ' + vids + ' video' + (vids !== 1 ? 's' : '');
    return t;
}

function _captionSpan(item, sid) {
    var txt = item.txt_content;
    var srcEsc = item.src.replace(/'/g, "\\'");
    var txtShort = txt ? txt.replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim() : '';
    if (txtShort.length > 80) txtShort = txtShort.substring(0, 80) + '...';
    var title = txt ? txt : 'Click to add caption';
    if (txt) {
        return '<span class="caption-text" onclick="editCaption(\'' + sid + '\',\'' + srcEsc + '\')" title="' + esc(title) + '\n\nClick to edit caption">' + esc(txtShort) + '</span>';
    }
    return '<span class="caption-text caption-placeholder" onclick="editCaption(\'' + sid + '\',\'' + srcEsc + '\')" title="' + esc(title) + '">Add caption</span>';
}

function _itemMeta(item, sid) {
    var html = '<div class="item-meta">';
    if (item.prompt) html += '<span class="prompt-link" onclick="showPrompt(\'' + sid + '\')">Prompt Used</span>';
    var ext = item.filename ? item.filename.split('.').pop().toUpperCase() : (item.is_video ? 'MP4' : 'PNG');
    html += '<span class="item-meta-right"><span class="fmt">' + ext + '</span><span class="created">' + esc(item.created_at || '') + '</span></span>';
    html += '</div>';
    return html;
}

function renderOutputs() {
    try {
    var batches = _outputsData;
    var area = document.getElementById('outputs-area');
    if (!area) return;
    if (_preview) { _preview.style.display = 'none'; var ov = _preview.querySelector('video'); if (ov) { ov.pause(); ov.currentTime = 0; } }
    if (!batches.length) { area.innerHTML = '<div class="outputs-empty"><span class="empty-illustration">$ ls outputs/</span>No outputs yet.<br>Generate your first images above.</div>'; return; }

    var total = batches.reduce(function(s, b) { return s + b.items.length; }, 0);
    var gs = document.getElementById('global-stats');
    if (gs) gs.textContent = total + ' items \u00b7 ' + batches.length + ' batches';

    var sb = document.getElementById('sidebar-balance');
    if (sb) sb.textContent = '$' + _balance.toFixed(2);
    document.getElementById('sidebar-generated').textContent = total;
    document.getElementById('sidebar-batches').textContent = batches.length;

    var collapsed = {};
    document.querySelectorAll('.b.collapsed').forEach(function(el) {
        collapsed[el.id.replace('batch-', '')] = true;
    });
    if (_viewMode === 'grid') { area.innerHTML = buildGridHtml(batches); }
    else { area.innerHTML = buildTableHtml(batches); }
    Object.keys(collapsed).forEach(function(id) {
        var el = document.getElementById('batch-' + id);
        if (el) el.classList.add('collapsed');
    });
    bindHoverPreview();
} catch(e) {
    var area2 = document.getElementById('outputs-area');
    if (area2) area2.innerHTML = '<div style="color:#f44336;font-size:11px;padding:12px;background:var(--bg3);border-radius:6px;"><b>Render error:</b> ' + esc(e.message) + '</div>';
    var el = document.getElementById('js-error');
    if (el) { el.style.display = 'block'; el.textContent = 'renderOutputs error: ' + e.message; }
}
}

function buildTableHtml(batches) {
    var html = '';
    batches.forEach(function(b, bIdx) {
        var bid = b.id;
        html += '<div class="b ' + (bIdx === 0 ? '' : 'collapsed') + '" id="batch-' + bid + '">';
        html += '<div class="b-header" onclick="toggleBatch(\'' + bid + '\')">';
        html += '<span class="chevron">\u25b8</span>';
        html += '<span class="b-title">' + esc(b.name) + '</span>';
        html += '<span class="b-count">' + _batchCount(b) + '</span>';
        html += '</div>';
        html += '<div class="b-body"><table class="tw"><tbody>';
        b.items.forEach(function(item, iIdx) {
            var sid = bid + '_' + item.stem;
            var txt = item.txt_content;
            var ext = item.filename ? item.filename.split('.').pop().toUpperCase() : '';
            var num = iIdx + 1;
            html += '<tr>';
            html += '<td class="n">' + num + '</td>';
            html += '<td class="m">';
            if (item.is_video) { html += '<span class="thumb" id="' + sid + '_m">'; } else { html += '<span class="thumb" id="' + sid + '_m" onclick="fullscreen(\'' + sid + '_m\',0)">'; }
            if (item.is_video) {
                html += '<video muted loop playsinline preload="metadata"><source src="' + item.src + '" type="video/mp4"></video>';
            } else {
                html += '<img src="' + item.src + '" loading="lazy">';
            }
            html += '</span>';
            if (item.prompt) html += '<pre class="prompt-box" id="pb-' + sid + '" data-negative="' + esc(item.negative_prompt || '') + '">' + esc(item.prompt) + '</pre>';
            if (txt) html += '<div class="txt" id="' + sid + '_t">' + esc(txt) + '</div>';
            html += '</td>';
            html += '<td class="info">';
            html += _captionSpan(item, sid);
            html += _itemMeta(item, sid);
            html += '</td>';
            html += '<td class="bt">';
            html += '<button class="cp" onclick="copyText(\'' + sid + '\')" title="Copy caption">' + _cpySvg + '</button>';
            html += '<a class="dl" href="' + item.src + '" download="' + item.filename + '" title="Download">' + _dlSvg + '</a>';
            html += '<button class="del" onclick="deleteMedia(\'' + item.src.replace(/'/g, "\\'") + '\')" title="Delete">' + _delSvg + '</button>';
            html += '</td>';
            html += '</tr>';
        });
        html += '</tbody></table></div></div>';
    });
    return html;
}

function buildGridHtml(batches) {
    var html = '';
    batches.forEach(function(b, bIdx) {
        var bid = b.id;
        html += '<div class="b ' + (bIdx === 0 ? '' : 'collapsed') + '" id="batch-' + bid + '">';
        html += '<div class="b-header" onclick="toggleBatch(\'' + bid + '\')">';
        html += '<span class="chevron">\u25b8</span>';
        html += '<span class="b-title">' + esc(b.name) + '</span>';
        html += '<span class="b-count">' + _batchCount(b) + '</span>';
        html += '</div>';
        html += '<div class="b-body"><div class="g-grid">';
        b.items.forEach(function(item, iIdx) {
            var sid = bid + '_' + item.stem;
            var srcEsc = item.src.replace(/'/g, "\\'");
            html += '<div class="g-card">';
            html += '<div class="g-thumb" id="' + sid + '_m"' + (item.is_video ? '' : ' onclick="fullscreen(\'' + sid + '_m\',0)"') + '>';
            if (item.is_video) {
                html += '<video muted loop playsinline preload="metadata"><source src="' + item.src + '" type="video/mp4"></video>';
            } else {
                html += '<img src="' + item.src + '" loading="lazy">';
            }
            html += '</div>';
            if (item.prompt) html += '<pre class="prompt-box" id="pb-' + sid + '" data-negative="' + esc(item.negative_prompt || '') + '">' + esc(item.prompt) + '</pre>';
            html += '<div class="g-body">';
            html += _captionSpan(item, sid);
            html += _itemMeta(item, sid);
            html += '<div class="g-actions">';
            if (item.txt_content) html += '<button class="cp" onclick="copyText(\'' + sid + '\')" title="Copy caption">' + _cpySvg + '</button>';
            html += '<a class="dl" href="' + item.src + '" download="' + item.filename + '" title="Download">' + _dlSvg + '</a>';
            html += '<button class="del" onclick="deleteMedia(\'' + srcEsc + '\')" title="Delete">' + _delSvg + '</button>';
            html += '</div>';
            html += '</div></div>';
        });
        html += '</div></div></div>';
    });
    return html;
}

function bindHoverPreview() {
    _preview = document.getElementById('hover-preview');
    if (!_preview) { _preview = document.createElement('div'); _preview.id = 'hover-preview'; document.body.appendChild(_preview); }
    _preview.onmouseleave = function() { _preview.style.display = 'none'; };
    document.querySelectorAll('.tw .thumb').forEach(function(cell) {
        var media = cell.querySelector('video, img');
        if (!media) return;
        var isVid = media.tagName === 'VIDEO';
        cell.addEventListener('mouseenter', function(e) {
            if (fsActive) return;
            _preview.innerHTML = '';
            var clone;
            if (isVid) { clone = document.createElement('video'); clone.src = media.querySelector('source').src; clone.muted = true; clone.loop = true; clone.autoplay = true; clone.playsinline = true; }
            else { clone = document.createElement('img'); clone.src = media.src; }
            _preview.appendChild(clone);
            var rect = cell.getBoundingClientRect();
            var left = rect.right + 10, top = rect.top;
            if (left + 260 > window.innerWidth) left = rect.left - 260 - 10;
            if (top + 360 > window.innerHeight) top = window.innerHeight - 360 - 10;
            if (top < 10) top = 10;
            _preview.style.left = left + 'px'; _preview.style.top = top + 'px'; _preview.style.display = 'flex';
        });
        cell.addEventListener('mouseleave', function(e) {
            if (_preview.contains(e.relatedTarget)) return;
            _preview.style.display = 'none';
        });
        media.addEventListener('mouseenter', function() { if (isVid && !fsActive) media.play(); });
        media.addEventListener('mouseleave', function() { if (isVid && !fsActive) media.pause(); media.currentTime = 0; });
    });
}


function toggleBatch(bid) {
    var b = document.getElementById('batch-' + bid);
    if (!b) return;
    b.classList.toggle('collapsed');
    localStorage.setItem('ofm_collapse_' + bid, b.classList.contains('collapsed') ? '1' : '0');
}

async function refreshOutputs() {
    var btn = document.getElementById('btn-refresh');
    if (btn) btn.classList.add('loading');
    var r = await api('/api/dashboard/refresh');
    if (btn) btn.classList.remove('loading');
    if (r.outputs) {
        _outputsData = r.outputs;
        renderOutputs();
    } else {
        showError(r.output || 'Failed to load outputs');
    }
}

function copyText(sid) {
    var t = document.getElementById(sid + '_t');
    if (!t) return;
    navigator.clipboard.writeText(t.innerText).then(function() {
        var m = document.getElementById(sid + '_msg');
        m.innerText = 'Copied!';
        setTimeout(function() { m.innerText = ''; }, 1500);
    });
}

// Edit caption modal
var _editSid = null, _editSrc = null;
function editCaption(sid, src) {
    _editSid = sid; _editSrc = src;
    var t = document.getElementById(sid + '_t');
    var textarea = document.getElementById('edit-text');
    textarea.value = t ? t.innerText : '';
    document.getElementById('edit-modal').classList.add('show');
    textarea.focus();
    textarea.select();
}
function closeEdit() {
    document.getElementById('edit-modal').classList.remove('show');
    _editSid = null; _editSrc = null;
}
async function saveEdit() {
    if (!_editSid || !_editSrc) return;
    var text = document.getElementById('edit-text').value;
    var btn = document.getElementById('edit-save');
    btn.disabled = true;
    try {
        var r = await api('/api/caption/edit', { src: _editSrc, text: text });
        if (r.ok) {
            var sid = _editSid;
            var tCell = document.getElementById(sid + '_t');
            if (tCell) {
                var flat = text.replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim();
                tCell.innerText = flat;
                tCell.title = flat;
            }
            closeEdit();
            refreshOutputs();
            showSuccess('Caption saved');
        } else {
            showError(r.output || r.error || 'Failed to save');
        }
    } catch (e) {
        showError('Error: ' + e.message);
    }
    btn.disabled = false;
}
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.getElementById('edit-modal').classList.contains('show')) closeEdit();
});

// Prompt Used — modal popup
function showPrompt(sid) {
    var box = document.getElementById('pb-' + sid);
    if (!box) return;
    var full = box.textContent || '';
    var main = full, negative = '', identity = '';
    var i = full.indexOf('negative prompt:');
    if (i >= 0) {
        main = full.substring(0, i).replace(/\n+$/g, '').trim();
        var rest = full.substring(i + 'negative prompt:'.length);
        var j = rest.search(/keep model identity/i);
        if (j >= 0) {
            negative = rest.substring(0, j).trim();
            identity = rest.substring(j).trim();
        } else {
            negative = rest.trim();
        }
    }
    document.getElementById('prompt-main').textContent = main || '(empty)';
    document.getElementById('prompt-negative').textContent = negative || '(empty)';
    document.getElementById('prompt-identity').textContent = identity || 'keep model identity/lip color consistent/accurate/similar';
    document.getElementById('prompt-modal').classList.add('show');
}
function closePrompt() {
    document.getElementById('prompt-modal').classList.remove('show');
}
function copyPrompt() {
    var main = document.getElementById('prompt-main').textContent;
    var neg = document.getElementById('prompt-negative').textContent;
    var id = document.getElementById('prompt-identity').textContent;
    var full = main + '\n\nnegative prompt: ' + neg + '\n\n' + id;
    navigator.clipboard.writeText(full).then(function() {
        var btn = document.getElementById('prompt-copy');
        var orig = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(function() { btn.textContent = orig; }, 1500);
    }).catch(function(e) {
        alert('Copy failed: ' + e.message);
    });
}
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.getElementById('prompt-modal').classList.contains('show')) closePrompt();
});
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('edit-modal').addEventListener('click', function(e) {
        if (e.target === this) closeEdit();
    });
    document.getElementById('prompt-modal').addEventListener('click', function(e) {
        if (e.target === this) closePrompt();
    });
});

function deleteMedia(src) {
    if (!confirm('Delete this media file? This cannot be undone.')) return;
    api('/api/media/delete', {src: src}).then(function(data) {
        if (data.ok) {
            refreshOutputs();
            showSuccess('Deleted');
        } else {
            showError('Delete failed: ' + (data.error || 'unknown error'));
        }
    }).catch(function(e) {
        showError('Delete error: ' + e.message);
    });
}

// Fullscreen zoom/pan with prev/next arrows

var fsActive = false;
var _fsScale = 1, _fsPanX = 0, _fsPanY = 0;
var _fsDragging = false, _fsDragRef = null, _fsMoved = false;
var _fsCleanup = [];
var _fsBatch = [];
var _fsIdx = 0;

function _buildFsList(vid) {
    var sid = vid.replace(/_m$/, '');
    _fsBatch = [];
    _fsIdx = 0;
    for (var b = 0; b < _outputsData.length; b++) {
        var batch = _outputsData[b];
        for (var i = 0; i < batch.items.length; i++) {
            var item = batch.items[i];
            var itVid = batch.id + '_' + item.stem + '_m';
            _fsBatch.push({ vid: itVid, isVideo: item.is_video });
            if (itVid === vid) _fsIdx = _fsBatch.length - 1;
        }
    }
    var part = _fsBatch[_fsIdx].vid.split('_')[0];
    _fsBatch = _fsBatch.filter(function(it) { return it.vid.indexOf(part + '_') === 0; });
    for (var j = 0; j < _fsBatch.length; j++) {
        if (_fsBatch[j].vid === vid) { _fsIdx = j; break; }
    }
}

function _renderFs() {
    var modal = document.getElementById('fs-modal');
    var item = _fsBatch[_fsIdx];
    var srcEl = document.getElementById(item.vid);
    if (!srcEl) return;
    var isV = item.isVideo;
    modal.innerHTML = '';
    for (var ci = 0; ci < _fsCleanup.length; ci++) {
        var h = _fsCleanup[ci];
        window.removeEventListener('mousemove', h);
        window.removeEventListener('mouseup', h);
        window.removeEventListener('keydown', h);
    }
    _fsScale = 1; _fsPanX = 0; _fsPanY = 0;
    _fsDragging = false; _fsDragRef = null; _fsMoved = false;
    _fsCleanup = [];

    var wrap = document.createElement('div');
    wrap.className = 'fs-wrap';

    if (isV) {
        var c = document.createElement('video');
        c.src = srcEl.querySelector('source').src;
        c.muted = false; c.loop = true; c.autoplay = true; c.playsinline = true; c.controls = true;
        wrap.appendChild(c);
        wrap.onclick = function(e) { if (e.target === wrap) closeFS(); };
    } else {
        var img = document.createElement('img');
        img.src = srcEl.querySelector('img').src;
        img.draggable = false;
        wrap.appendChild(img);
        function apply() {
            img.style.transform = 'translate(' + _fsPanX + 'px,' + _fsPanY + 'px) scale(' + _fsScale + ')';
            wrap.classList.toggle('zoomed', _fsScale > 1);
        }
        function _clamp() {
            var r = img.getBoundingClientRect();
            var nw = r.width / _fsScale, nh = r.height / _fsScale;
            var vw = window.innerWidth, vh = window.innerHeight;
            var ox = Math.max(0, (nw * _fsScale - vw) / 2);
            var oy = Math.max(0, (nh * _fsScale - vh) / 2);
            _fsPanX = Math.max(-ox, Math.min(ox, _fsPanX));
            _fsPanY = Math.max(-oy, Math.min(oy, _fsPanY));
        }
        wrap.onmousedown = function(e) {
            e.preventDefault();
            _fsDragging = true; _fsMoved = false;
            _fsDragRef = { x: e.clientX - _fsPanX, y: e.clientY - _fsPanY, target: e.target };
        };
        var mm = function(e) {
            if (!_fsDragging || _fsScale <= 1) return;
            var dx = e.clientX - _fsDragRef.x - _fsPanX;
            var dy = e.clientY - _fsDragRef.y - _fsPanY;
            if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
                if (!_fsMoved) wrap.classList.add('grabbing');
                _fsMoved = true;
            }
            _fsPanX = e.clientX - _fsDragRef.x;
            _fsPanY = e.clientY - _fsDragRef.y;
            _clamp();
            apply();
        };
        var mu = function(e) {
            if (!_fsDragging) return;
            _fsDragging = false;
            wrap.classList.remove('grabbing');
            if (_fsMoved) return;
            if (_fsDragRef.target === img) {
                if (_fsScale > 1) { _fsScale = 1; _fsPanX = 0; _fsPanY = 0; }
                else { _fsScale = 2; _fsPanX = 0; _fsPanY = 0; }
                apply();
            } else { closeFS(); }
        };
        window.addEventListener('mousemove', mm);
        window.addEventListener('mouseup', mu);
        _fsCleanup.push(mm);
        _fsCleanup.push(mu);
        wrap.ondblclick = function() { _fsScale = 1; _fsPanX = 0; _fsPanY = 0; apply(); };
    }

    var kh = function(e) {
        if (e.key === 'Escape') { closeFS(); }
        else if (e.key === 'ArrowLeft') { navigateFs(-1); }
        else if (e.key === 'ArrowRight') { navigateFs(1); }
        else if (e.key === '+' || e.key === '=') {
            var ns = Math.min(10, _fsScale + 0.25);
            _fsPanX = (window.innerWidth / 2) - (window.innerWidth / 2 - _fsPanX) * (ns / _fsScale);
            _fsPanY = (window.innerHeight / 2) - (window.innerHeight / 2 - _fsPanY) * (ns / _fsScale);
            _fsScale = ns; if (_clamp) _clamp(); if (apply) apply();
        } else if (e.key === '-' || e.key === '_') {
            var ns2 = Math.max(0.5, _fsScale - 0.25);
            _fsPanX = (window.innerWidth / 2) - (window.innerWidth / 2 - _fsPanX) * (ns2 / _fsScale);
            _fsPanY = (window.innerHeight / 2) - (window.innerHeight / 2 - _fsPanY) * (ns2 / _fsScale);
            _fsScale = ns2; if (_clamp) _clamp(); if (apply) apply();
        } else if (e.key === '0') { _fsScale = 1; _fsPanX = 0; _fsPanY = 0; if (apply) apply(); }
    };
    window.addEventListener('keydown', kh);
    _fsCleanup.push(kh);

    if (_fsBatch.length > 1) {
        if (_fsIdx > 0) { var pb = document.createElement('button'); pb.className = 'fs-arrow fs-prev'; pb.innerHTML = '\u25c0'; pb.onclick = function() { navigateFs(-1); }; modal.appendChild(pb); }
        if (_fsIdx < _fsBatch.length - 1) { var nb = document.createElement('button'); nb.className = 'fs-arrow fs-next'; nb.innerHTML = '\u25b6'; nb.onclick = function() { navigateFs(1); }; modal.appendChild(nb); }
    }

    modal.appendChild(wrap);
    modal.classList.add('show');
    fsActive = true;
}

function fullscreen(vid, isVideo) {
    if (fsActive) return;
    _buildFsList(vid);
    _renderFs();
}
function navigateFs(dir) {
    var n = _fsIdx + dir;
    if (n < 0 || n >= _fsBatch.length) return;
    _fsIdx = n;
    _renderFs();
}
function closeFS() {
    var modal = document.getElementById('fs-modal');
    modal.classList.remove('show');
    modal.innerHTML = '';
    fsActive = false;
    for (var i = 0; i < _fsCleanup.length; i++) {
        var h = _fsCleanup[i];
        window.removeEventListener('mousemove', h);
        window.removeEventListener('mouseup', h);
        window.removeEventListener('keydown', h);
    }
    _fsCleanup = [];
}

// ── API status badge ──
var _selectedAccount = null;
var _lastIdentity = '';
var _lastApiCount = 0;

function updateApiLabel() {
    var user = document.getElementById('api-user');
    if (!user) return;
    var text = '';
    if (_selectedAccount) {
        text = _selectedAccount;
    } else if (_lastIdentity) {
        text = _lastIdentity;
    } else if (_lastApiCount > 0) {
        text = _lastApiCount + ' API' + (_lastApiCount !== 1 ? 's' : '');
    } else {
        text = 'No API keys';
    }
    if (user.textContent !== text) user.textContent = text;
}

async function checkApiStatus() {
    var dot = document.getElementById('api-dot');
    var user = document.getElementById('api-user');
    var bal = document.getElementById('api-tab-bal');
    if (!dot || !user) {
        requestAnimationFrame(function() { checkApiStatus(); });
        return;
    }
    try {
        var controller = new AbortController();
        var timeoutId = setTimeout(function() { controller.abort(); }, 10000);
        var r = await fetch('/api/settings/key/status', { signal: controller.signal });
        clearTimeout(timeoutId);
        var data = await r.json();
        var accounts = data.wavespeed_accounts || {};
        var active = data.active_wavespeed_account || '';
        var count = Object.keys(accounts).length;
        _lastApiCount = count;
        if (count > 0) {
            dot.className = 'api-tab-dot valid';
            if (_selectedAccount && !accounts[_selectedAccount]) {
                _selectedAccount = null;
            }
            if (!_selectedAccount && active && accounts[active]) {
                _selectedAccount = active;
            }
            updateApiLabel();
            if (active && accounts[active]) {
                try {
                    var br = await fetch('/api/balance/account?account=' + encodeURIComponent(active));
                    var bd = await br.json();
                    if (bd && typeof bd.balance === 'number') {
                        bal.textContent = '$' + bd.balance.toFixed(2);
                    } else {
                        bal.textContent = '$--';
                    }
                } catch(e) {
                    bal.textContent = '$--';
                }
            } else {
                bal.textContent = '$--';
            }
        } else {
            dot.className = 'api-tab-dot invalid';
            _lastApiCount = 0;
            _selectedAccount = null;
            updateApiLabel();
            bal.textContent = '$--';
        }
    } catch(e) {
        if (e.name === 'AbortError') {
            var dot = document.getElementById('api-dot');
            if (dot) dot.className = 'api-tab-dot invalid';
            return;
        }
        var dot = document.getElementById('api-dot');
        var user = document.getElementById('api-user');
        if (dot) dot.className = 'api-tab-dot invalid';
        if (bal) bal.textContent = '$--';
    }
}

// ── ESC key closes API dropdown / prompt modal ──
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        var apiModal = document.getElementById('api-modal');
        if (apiModal && apiModal.classList.contains('show')) {
            closeApiModal();
        }
        var pm = document.getElementById('prompt-modal');
        if (pm && pm.classList.contains('show')) {
            closePrompt();
        }
    }
});

// Outside click closes API modal
document.addEventListener('click', function(e) {
    if (!e.target.closest('#api-modal-box') && !e.target.closest('#api-nav-trigger')) {
        closeApiModal();
    }
});
var _delSvg2 = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';

var _validationCache = null;
var _validationCacheTime = 0;
var _accountsCache = null;
var _accountsCacheTime = 0;

function _invalidateValidation() {
    _validationCache = null;
    _validationCacheTime = 0;
}

async function _getValidationResults() {
    var now = Date.now();
    if (_validationCache && now - _validationCacheTime < 30000) return _validationCache;
    try {
        var r = await fetch('/api/settings/wavespeed/accounts/validate-all');
        var data = await r.json();
        if (data.ok) {
            _validationCache = data.results || {};
            _validationCacheTime = now;
            return _validationCache;
        }
    } catch(e) {}
    return {};
}

async function _fetchValidationForAccount(label) {
    try {
        var r = await fetch('/api/settings/wavespeed/accounts/validate-all');
        var data = await r.json();
        if (data.ok && data.results) {
            // Update validation cache
            if (!_validationCache) _validationCache = {};
            _validationCache[label] = data.results[label];
            _validationCacheTime = Date.now();
            
            // Update just this row's status
            _updateAccountValidationStatus(label, data.results[label]);
        }
    } catch(e) {
        // Silently fail - row stays in "checking..." state
    }
}

function _updateAccountValidationStatus(label, isValid) {
    var statusEl = document.querySelector('.provider-status[data-label="' + label.replace(/"/g, '\\"') + '"]');
    var dotEl = document.querySelector('.provider-row .provider-dot');
    if (!statusEl || !dotEl) return;
    
    // Find the correct row's dot
    var row = statusEl.closest('.provider-row');
    if (!row) return;
    var rowDot = row.querySelector('.provider-dot');
    
    var statusClass = isValid ? 'valid' : 'invalid';
    var statusText = isValid ? 'valid' : 'invalid';
    
    statusEl.className = 'provider-status ' + statusClass;
    statusEl.textContent = statusText;
    if (rowDot) rowDot.className = 'provider-dot ' + statusClass;
}

function _invalidateAccounts() {
    _accountsCache = null;
    _accountsCacheTime = 0;
}

async function preloadAccounts() {
    try {
        var r = await fetch('/api/settings/wavespeed/accounts');
        var data = await r.json();
        if (data.ok && data.accounts) {
            _accountsCache = data;
            _accountsCacheTime = Date.now();
        }
    } catch(e) {}
}

async function preloadValidation() {
    try {
        var r = await fetch('/api/settings/wavespeed/accounts/validate-all');
        var data = await r.json();
        if (data.ok) {
            _validationCache = data.results || {};
            _validationCacheTime = Date.now();
        }
    } catch(e) {}
}

function _renderAccounts(data, validation) {
    var list = document.getElementById('api-provider-list');
    if (!list) return;
    
    if (!data.ok || !data.accounts || Object.keys(data.accounts).length === 0) {
        list.innerHTML = '<div class="provider-summary"><span>No providers configured</span></div>';
        _selectedAccount = null;
        _lastApiCount = 0;
        updateApiLabel();
        return;
    }
    
    var active = data.active || '';
    _selectedAccount = active;
    updateApiLabel();
    
    var count = Object.keys(data.accounts).length;
    var validCount = Object.keys(data.accounts).filter(function(l) { return !!validation[l]; }).length;
    
    var html = '<div class="provider-summary">'
      + '<span class="ps-count">' + count + ' provider' + (count === 1 ? '' : 's') + '</span>'
      + '<span class="ps-sep"></span>'
      + '<span class="ps-valid">' + validCount + ' valid</span>'
      + '<span class="ps-total" id="provider-sum-bal">$--</span>'
      + '</div>';
    
    Object.keys(data.accounts).forEach(function(label) {
        var preview = data.accounts[label];
        var isActive = (label === active);
        var isValid = validation[label];
        var hasValidation = validation.hasOwnProperty(label);
        var statusClass = hasValidation ? (isValid ? 'valid' : 'invalid') : 'checking';
        var statusText = hasValidation ? (isValid ? 'valid' : 'invalid') : 'checking...';
        var maskedKey = '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022' + (preview.length > 4 ? preview.slice(-4) : '');
        
        html += '<div class="provider-row' + (isActive ? ' selected' : '') + '">';
        html += '<span class="provider-dot ' + statusClass + '"></span>';
        html += '<div class="provider-body">';
        html += '<div class="provider-line">';
        html += '<span class="provider-name">' + esc(label) + '</span>';
        html += '<span class="provider-bal" data-account="' + esc(label) + '">$--</span>';
        html += '</div>';
        html += '<div class="provider-line">';
        html += '<span class="provider-key">' + maskedKey + '</span>';
        html += '<span class="provider-status ' + statusClass + '" data-label="' + esc(label) + '">' + statusText + '</span>';
        html += '</div>';
        html += '</div>';
        html += '<div class="provider-actions">';
        // Toggle switch
        html += '<label class="provider-toggle" title="' + (isActive ? 'Active provider' : 'Set as active provider') + '">';
        html += '<input type="checkbox" role="switch" aria-label="Set as active provider" ' + (isActive ? 'checked' : '') + (count === 1 ? ' disabled' : '') + ' onclick="toggleProvider(\'' + esc(label) + '\', this)">';
        html += '<span class="toggle-slider"></span>';
        html += '</label>';
        // Hover-reveal delete
        html += '<button class="provider-delete" onclick="removeApiProvider(\'' + esc(label) + '\')" title="Remove provider" aria-label="Remove provider">' + _delSvg2 + '</button>';
        html += '</div>';
        html += '</div>';
    });
    
    list.innerHTML = html;
    
    // Load balances (accumulate for the summary total)
    var balTotal = 0;
    var balPending = count;
    Object.keys(data.accounts).forEach(function(label) {
        fetch('/api/balance/account?account=' + encodeURIComponent(label))
            .then(function(res) { return res.json(); })
            .then(function(d) {
                var balSpan = document.querySelector('.provider-bal[data-account="' + esc(label).replace(/"/g, '\\"') + '"]');
                if (balSpan && d && typeof d.balance === 'number') {
                    balSpan.textContent = '$' + d.balance.toFixed(2);
                    balTotal += d.balance;
                }
                balPending -= 1;
                if (balPending <= 0) {
                    var totalSpan = document.getElementById('provider-sum-bal');
                    if (totalSpan) totalSpan.textContent = '$' + balTotal.toFixed(2);
                }
            })
            .catch(function() {
                var balSpan = document.querySelector('.provider-bal[data-account="' + esc(label).replace(/"/g, '\\"') + '"]');
                if (balSpan) balSpan.textContent = '$--';
                balPending -= 1;
            });
    });
}

// ── API Modal toggle ──
function _setApiExpanded(open) {
    var t = document.getElementById('api-nav-trigger');
    if (t) {
        t.setAttribute('aria-expanded', open ? 'true' : 'false');
        t.classList.toggle('open', open);
    }
}
function toggleApiModal() {
    var modal = document.getElementById('api-modal');
    if (!modal) return;
    if (modal.classList.contains('show')) {
        closeApiModal();
    } else {
        modal.classList.add('show');
        _setApiExpanded(true);
        loadApiProviderList();
    }
}

function closeApiModal() {
    var modal = document.getElementById('api-modal');
    if (modal) modal.classList.remove('show');
    _setApiExpanded(false);
}

document.addEventListener('keydown', function(e) {
    var trigger = document.getElementById('api-nav-trigger');
    if (trigger && document.activeElement === trigger && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        toggleApiModal();
    }
});

async function loadApiProviderList() {
    var list = document.getElementById('api-provider-list');
    if (!list) return;
    
    // Render immediately from cache if available (no await on validation)
    if (_accountsCache) {
        _renderAccounts(_accountsCache, {});  // empty validation = show "checking..."
    } else {
        list.innerHTML = '<div class="provider-summary"><span class="ps-load">Loading providers\u2026</span></div>';
    }
    
    // Background: fetch fresh accounts + validation, then update
    try {
        var r = await fetch('/api/settings/wavespeed/accounts');
        var data = await r.json();
        if (data.ok && data.accounts) {
            _accountsCache = data;
            _accountsCacheTime = Date.now();
            
            // Fetch validation in background
            var validation = await _getValidationResults();
            _renderAccounts(data, validation);
        }
    } catch(e) {
        // If no cache was available and fetch fails, show error
        if (!_accountsCache) {
            list.innerHTML = '<div class="provider-summary"><span>Error loading accounts</span></div>';
        }
    }
}

async function confirmSwitchApi(label) {
  try {
    var r = await fetch('/api/settings/wavespeed/active', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({label: label})
    });
    var data = await r.json();
    if (data.ok) {
      _selectedAccount = label;
      _lastApiCount = 0;
      _lastIdentity = '';
      updateApiLabel();
      _invalidateValidation();
      checkApiStatus();
      fetchBalance();
      
      // Optimistically update cache and re-render with empty validation (no spinner flash)
      if (_accountsCache && _accountsCache.accounts) {
        _accountsCache.active = label;
        _renderAccounts(_accountsCache, {});
      }
      
      // Background: fetch fresh accounts + validation, then update
      try {
        var rr = await fetch('/api/settings/wavespeed/accounts');
        var fresh = await rr.json();
        if (fresh.ok && fresh.accounts) {
          _accountsCache = fresh;
          _accountsCacheTime = Date.now();
          var validation = await _getValidationResults();
          _renderAccounts(fresh, validation);
        }
      } catch(e) {}
    }
  } catch(e) {
    var result = document.getElementById('api-modal-result');
    if (result) { 
      result.className = 'api-modal-result error'; 
      result.textContent = 'Error switching account'; 
      result.style.display = 'block'; 
      setTimeout(function() { result.style.display = 'none'; }, 3000);
    }
  }
}

function toggleProvider(label, checkbox) {
  // Prevent unchecking the only active provider
  if (!checkbox.checked) {
    checkbox.checked = true;
    return;
  }
  
  // Prevent switching if already active (checkbox would be checked)
  if (_selectedAccount === label && checkbox.checked) {
    return;
  }
  
  confirmSwitchApi(label);
}

async function addApiProvider() {
  var name = document.getElementById('api-new-provider-name').value.trim().toLowerCase();
  var key = document.getElementById('api-new-provider-key').value.trim();
  var result = document.getElementById('api-modal-result');
  result.className = 'api-modal-result';
  result.style.display = 'none';
  if (!name || !key) { 
    result.className = 'api-modal-result error'; 
    result.textContent = 'Enter both account name and key'; 
    result.style.display = 'block'; 
    return; 
  }
  try {
    var r = await fetch('/api/settings/wavespeed/accounts/set', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({label: name, key: key})
    });
    var data = await r.json();
    if (data.ok) {
      document.getElementById('api-new-provider-name').value = '';
      document.getElementById('api-new-provider-key').value = '';
      
      // Optimistically update cache and render immediately (no spinner)
      if (_accountsCache && _accountsCache.accounts) {
        _accountsCache.accounts[name] = key;
        _accountsCache.active = data.active || _accountsCache.active || name;
        _renderAccounts(_accountsCache, {});  // empty validation = new account shows "checking..."
      }
      
      // Fetch validation in background for the new account
      _fetchValidationForAccount(name);
      
      result.className = 'api-modal-result success';
      result.textContent = 'Account saved: ' + name;
      result.style.display = 'block';
      setTimeout(function() { result.style.display = 'none'; }, 2000);
    } else {
      result.className = 'api-modal-result error';
      result.textContent = data.error || 'Failed to save';
      result.style.display = 'block';
      setTimeout(function() { result.style.display = 'none'; }, 3000);
    }
  } catch(e) {
    result.className = 'api-modal-result error';
    result.textContent = 'Error: ' + e.message;
    result.style.display = 'block';
    setTimeout(function() { result.style.display = 'none'; }, 3000);
  }
}

async function removeApiProvider(label) {
  if (!confirm('Remove account "' + label + '"?')) return;
  var result = document.getElementById('api-modal-result');
  result.className = 'api-modal-result';
  result.style.display = 'none';
  try {
    var r = await fetch('/api/settings/wavespeed/accounts/remove', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({label: label})
    });
    var data = await r.json();
    if (data.ok) {
      // Optimistically update cache and render immediately (no spinner)
      if (_accountsCache && _accountsCache.accounts) {
        delete _accountsCache.accounts[label];
        // Update active if we removed the active account
        if (_accountsCache.active === label) {
          _accountsCache.active = Object.keys(_accountsCache.accounts)[0] || '';
        }
        _renderAccounts(_accountsCache, _validationCache || {});
      }
      
      // Invalidate validation cache since accounts changed
      _invalidateValidation();
      
      checkApiStatus();
      result.className = 'api-modal-result success';
      result.textContent = 'Removed ' + label;
      result.style.display = 'block';
      setTimeout(function() { result.style.display = 'none'; }, 2000);
    } else {
      result.className = 'api-modal-result error';
      result.textContent = data.error || 'Failed to remove';
      result.style.display = 'block';
      setTimeout(function() { result.style.display = 'none'; }, 3000);
    }
  } catch(e) {
    result.className = 'api-modal-result error';
    result.textContent = 'Error: ' + e.message;
    result.style.display = 'block';
    setTimeout(function() { result.style.display = 'none'; }, 3000);
  }
}

// ── Init ──
document.addEventListener('DOMContentLoaded', function() {
    try {
        setLive('loading', 'Starting...');
        fetchBalance();
        refreshOutputs();
        syncViewToggle();
        
        checkApiStatus();
        preloadAccounts();
        preloadValidation();
        loadActiveBank();
        setInterval(checkApiStatus, 30000);
        setInterval(fetchBalance, 60000);

        // Close modal on backdrop click
        var apiModal = document.getElementById('api-modal');
        if (apiModal) {
            apiModal.addEventListener('click', function(e) {
                if (e.target === apiModal) {
                    closeApiModal();
                }
            });
        }
        
        // Close modal on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var apiModal = document.getElementById('api-modal');
                if (apiModal && apiModal.classList.contains('show')) {
                    closeApiModal();
                }
            }
        });
    } catch(e) {}
});

// ── Equal-height panels: prompt preview matches generation card ──
var _heightSyncTimer = null;
function syncPanelHeights() {
    var card = document.querySelector('.gen-layout .card');
    var preview = document.querySelector('.gen-preview');
    if (!card || !preview) return;
    if (window.innerWidth < 768) { preview.style.height = 'auto'; return; }
    preview.style.height = card.offsetHeight + 'px';
}
window.addEventListener('load', syncPanelHeights);
window.addEventListener('resize', function() {
    clearTimeout(_heightSyncTimer);
    _heightSyncTimer = setTimeout(syncPanelHeights, 100);
});
if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(syncPanelHeights);
}
syncPanelHeights();