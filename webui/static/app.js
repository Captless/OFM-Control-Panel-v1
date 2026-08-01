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
var _moonSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
var _sunSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
function setThemeIcon(isLight) {
    var btn = document.getElementById('theme-btn');
    if (!btn) return;
    btn.innerHTML = isLight ? _sunSvg : _moonSvg;
}
function toggleTheme() {
    document.body.classList.toggle('light');
    var isLight = document.body.classList.contains('light');
    var btn = document.getElementById('theme-btn');
    if (btn) { btn.classList.add('rotate'); setTimeout(function() { btn.classList.remove('rotate'); }, 300); }
    setThemeIcon(isLight);
    localStorage.setItem('ofm_theme', isLight ? 'light' : 'dark');
}
var savedTheme = localStorage.getItem('ofm_theme');
if (savedTheme === 'light') { document.body.classList.add('light'); setThemeIcon(true); } else { setThemeIcon(false); }

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
    var r = await api('/api/prompts/generate', {vibe: vibe, camera_style: camera_style, lighting: lighting, time_of_day: time_of_day, outfit_style: outfit_style, count: count});
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
    btn.classList.add('loading'); _btnTxt(jobs.length + ' prompts \u2192 starting\u2026');
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
    while (Date.now() < _deadline) {
        var p = await api('/api/progress?run_id=' + runId);
        if (p && p.done === true) {
            _btnTxt(p.ok ? 'OK (' + p.duration_s + 's)' : 'FAIL: ' + (p.detail || 'error'));
            btn.classList.remove('loading');
            if (p.ok) { refreshOutputs(); showSuccess('Generation complete \u2014 ' + p.duration_s + 's'); }
            else { showError('Generation failed: ' + (p.detail || 'error')); }
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
        var stage = p.stage ? p.stage.charAt(0).toUpperCase() + p.stage.slice(1) : 'Running';
        var detail = stage + (p.detail ? ': ' + p.detail : '') + ((p.total > 0) ? ' (' + p.current + '/' + p.total + ')' : '');
        if (detail !== _lastDetail) {
            _lastDetail = detail;
            _lastChangeTime = Date.now();
        }
        var updatedAt = (typeof p.updated_at === 'number') ? p.updated_at : (_lastChangeTime / 1000);
        var elapsed = Math.floor(Date.now() / 1000 - updatedAt);
        if (elapsed >= 300 && _retryCount < _maxRetries) {
            _retryCount++;
            _btnTxt('Stalled \u2014 retry ' + _retryCount + '/' + _maxRetries + '\u2026');
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
        _btnTxt(detail + ' \u00b7 ' + Math.floor((Date.now() - _startTs) / 1000) + 's');
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

    var cpySvg = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
    var dlSvg = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>';
    var delSvg = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>';

    var html = '';
    batches.forEach(function(b, bIdx) {
        var bid = b.id;
        html += '<div class="b ' + (bIdx === 0 ? '' : 'collapsed') + '" id="batch-' + bid + '">';
        html += '<div class="b-header" onclick="toggleBatch(\'' + bid + '\')">';
        html += '<span class="chevron">\u25b8</span>';
        html += '<span class="b-title">' + esc(b.name) + '</span>';
        html += '<span class="b-count">' + b.items.length + ' item' + (b.items.length !== 1 ? 's' : '') + '</span>';
        html += '</div>';
        html += '<div class="b-body"><table class="tw"><tbody>';
        b.items.forEach(function(item, iIdx) {
            var sid = bid + '_' + item.stem;
            var txt = item.txt_content;
            var ext = item.filename ? item.filename.split('.').pop().toUpperCase() : '';
            var display = item.name || item.filename || item.stem;
            var num = iIdx + 1;
            html += '<tr>';
            html += '<td class="n">' + num + '</td>';
            html += '<td class="m">';
            if (item.is_video) { html += '<span class="thumb" id="' + sid + '_m">'; } else { html += '<span class="thumb" id="' + sid + '_m" onclick="fullscreen(\'' + sid + '_m\',0)">'; }
            if (item.is_video) {
                html += '<video muted loop playsinline preload="metadata"><source src="' + item.src + '" type="video/mp4"></video><span class="vid-badge">VID</span>';
            } else {
                html += '<img src="' + item.src + '" loading="lazy">';
            }
            html += '</span>';
            if (item.prompt) html += '<pre class="prompt-box" id="pb-' + sid + '" data-negative="' + esc(item.negative_prompt || '') + '">' + esc(item.prompt) + '</pre>';
            if (txt) html += '<div class="txt" id="' + sid + '_t">' + esc(txt) + '</div>';
            html += '</td>';
            html += '<td class="info">';
            var txtShort = txt ? txt.replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim() : '';
            if (txtShort.length > 80) txtShort = txtShort.substring(0, 80) + '...';
            if (txt) {
                html += '<span class="caption-text" onclick="editCaption(\'' + sid + '\',\'' + item.src.replace(/'/g, "\\'") + '\')" title="' + esc(txt) + '\n\nClick to edit caption">' + esc(txtShort) + '</span>';
            } else {
                html += '<span class="caption-placeholder" onclick="editCaption(\'' + sid + '\',\'' + item.src.replace(/'/g, "\\'") + '\')" title="Click to add caption">Add caption</span>';
            }
            html += '<div class="info-meta">';
            if (item.prompt) html += '<span class="prompt-link" onclick="showPrompt(\'' + sid + '\')" title="View full prompt">Prompt Used</span><span class="info-sep">&middot;</span>';
            html += '<span class="fmt">' + (ext || (item.is_video ? 'MP4' : 'PNG')) + '</span>';
            html += '</div>';
            html += '</td>';
            html += '<td class="bt">';
            html += '<button class="cp" onclick="copyText(\'' + sid + '\')" title="Copy caption">' + cpySvg + '</button>';
            html += '<a class="dl" href="' + item.src + '" download="' + item.filename + '" title="Download">' + dlSvg + '</a>';
            html += '<button class="del" onclick="deleteMedia(\'' + item.src.replace(/'/g, "\\'") + '\')" title="Delete">' + delSvg + '</button>';
            html += '</td>';
            html += '</tr>';
        });
        html += '</tbody></table></div></div>';
    });
    var collapsed = {};
    document.querySelectorAll('.b.collapsed').forEach(function(el) {
        collapsed[el.id.replace('batch-', '')] = true;
    });
    area.innerHTML = html;
    Object.keys(collapsed).forEach(function(id) {
        var el = document.getElementById('batch-' + id);
        if (el) el.classList.add('collapsed');
    });

    // Hover preview
    var _preview = document.getElementById('hover-preview');
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
} catch(e) {
    if (area) area.innerHTML = '<div style="color:#f44336;font-size:11px;padding:12px;background:var(--bg3);border-radius:6px;"><b>Render error:</b> ' + esc(e.message) + '</div>';
    var el = document.getElementById('js-error');
    if (el) { el.style.display = 'block'; el.textContent = 'renderOutputs error: ' + e.message; }
}
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
    document.getElementById('prompt-main').textContent = box.textContent || '(empty)';
    document.getElementById('prompt-negative').textContent = box.getAttribute('data-negative') || '(empty)';
    document.getElementById('prompt-identity').textContent = 'keep model identity/lip color consistent/accurate/similar';
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
        var identity = data.identity_name || '';
        var count = Object.keys(accounts).length;
        _lastIdentity = identity;
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
            var provCount = data.providers ? Object.keys(data.providers).length : 0;
            if (provCount > 0) {
                dot.className = 'api-tab-dot valid';
                _lastApiCount = provCount;
                _selectedAccount = null;
                updateApiLabel();
                bal.textContent = '$--';
            } else {
                dot.className = 'api-tab-dot invalid';
                _lastApiCount = 0;
                _selectedAccount = null;
                updateApiLabel();
                bal.textContent = '$--';
            }
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
    if (!e.target.closest('#api-modal') && !e.target.closest('#api-nav-trigger')) {
        closeApiModal();
    }
});
var _delSvg2 = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
var _checkSvg = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

async function loadProviderList() {
    var list = document.getElementById('provider-list');
    try {
        var r = await fetch('/api/settings/wavespeed/accounts');
        var data = await r.json();
        var validation = await _getValidationResults();
        var headerHtml = '<div class="provider-header"><span style="min-width:100px;flex:1">Account</span><span style="width:80px;text-align:right">Bal</span><span style="flex:1">API Key</span><span style="width:60px">Status</span><span style="width:70px"></span></div>';
        if (!data.ok || !data.accounts || Object.keys(data.accounts).length === 0) {
            list.innerHTML = headerHtml + '<div class="settings-empty">No accounts configured</div>';
            return;
        }
        var html = headerHtml;
        var active = data.active || '';
        Object.keys(data.accounts).forEach(function(label) {
            var preview = data.accounts[label];
            var isActive = (label === active);
            var isValid = validation[label];
            var statusClass = isValid ? 'valid' : 'invalid';
            var statusText = isValid ? 'Valid' : 'Invalid';
            html += '<div class="provider-row">';
            html += '<span class="provider-name" onclick="startRename(this, \'' + esc(label) + '\')" title="Click to rename">' + esc(label) + '</span>';
            html += '<span class="provider-bal" data-account="' + esc(label) + '">--</span>';
            html += '<span class="provider-key">' + esc(preview) + '</span>';
            html += '<span class="provider-status ' + statusClass + '">' + statusText + '</span>';
            if (isActive) {
                html += '<span class="provider-active-badge">Active</span>';
            } else {
                html += '<button class="use-btn" onclick="confirmSwitchAccount(\'' + esc(label) + '\')">Use</button>';
            }
            html += '<button class="provider-remove" onclick="removeProvider(\'' + esc(label) + '\')" title="Remove account">' + _delSvg2 + '</button>';
            html += '</div>';
        });
        list.innerHTML = html;
        Object.keys(data.accounts).forEach(function(label) {
            fetch('/api/balance/account?account=' + encodeURIComponent(label))
                .then(function(r) { return r.json(); })
                .then(function(d) {
                    var balSpan = document.querySelector('.provider-bal[data-account="' + label.replace(/"/g, '\\"') + '"]');
                    if (balSpan && d && typeof d.balance === 'number') {
                        balSpan.textContent = '$' + d.balance.toFixed(2);
                    }
                })
                .catch(function() {
                    var balSpan = document.querySelector('.provider-bal[data-account="' + label.replace(/"/g, '\\"') + '"]');
                    if (balSpan) balSpan.textContent = '$--';
                });
        });
    } catch(e) {
    list.innerHTML = '<div class="provider-header"><span style="min-width:100px;flex:1">Account</span><span style="width:80px;text-align:right">Bal</span><span style="flex:1">API Key</span><span style="width:60px">Status</span><span style="width:70px"></span></div><div class="settings-empty">Error loading accounts</div>';
    }
}

function startRename(el, oldLabel) {
    var input = document.createElement('input');
    input.type = 'text';
    input.value = oldLabel;
    input.className = 'provider-name-input';
    input.style.width = el.offsetWidth + 'px';
    el.parentNode.replaceChild(input, el);
    input.focus();
    input.select();

    function cancel() {
        var span = document.createElement('span');
        span.className = 'provider-name';
        span.onclick = function() { startRename(span, oldLabel); };
        span.title = 'Click to rename';
        span.textContent = oldLabel;
        input.parentNode.replaceChild(span, input);
    }

    async function save() {
        var newLabel = input.value.trim();
        if (!newLabel || newLabel === oldLabel) { cancel(); return; }
        try {
            var r = await fetch('/api/settings/wavespeed/accounts/rename', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({old_label: oldLabel, new_label: newLabel})
            });
            var data = await r.json();
            if (data.ok) {
                loadProviderList();
                checkApiStatus();
                _invalidateAccounts();
            } else {
                alert(data.error || 'Rename failed');
                cancel();
            }
        } catch(e) {
            alert('Error: ' + e.message);
            cancel();
        }
    }

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') save();
        else if (e.key === 'Escape') cancel();
    });
    input.addEventListener('blur', save);
}

async function confirmSwitchAccount(label) {
    if (!confirm('Switch active API to "' + label + '"? This will use this key for all new generations.')) return;
    try {
        var r = await fetch('/api/settings/wavespeed/active', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({label: label})
        });
        var data = await r.json();
        if (data.ok) {
            loadProviderList();
            checkApiStatus();
            fetchBalance();
            showSuccess('Active API switched to ' + label);
        }
    } catch(e) {
        showError('Error switching account: ' + e.message);
        var result = document.getElementById('settings-result');
        if (result) { result.className = 'settings-result error'; result.textContent = 'Error switching account'; result.style.display = 'block'; }
    }
}

async function addProvider() {
    var name = document.getElementById('new-provider-name').value.trim().toLowerCase();
    var key = document.getElementById('new-provider-key').value.trim();
    var result = document.getElementById('settings-result');
    result.className = 'settings-result';
    result.style.display = 'none';
    if (!name || !key) { result.className = 'settings-result error'; result.textContent = 'Enter both account name and key'; result.style.display = 'block'; return; }
    try {
        var r = await fetch('/api/settings/wavespeed/accounts/set', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({label: name, key: key})
        });
        var data = await r.json();
        if (data.ok) {
            document.getElementById('new-provider-name').value = '';
            document.getElementById('new-provider-key').value = '';
            loadProviderList();
            checkApiStatus();
            result.className = 'settings-result success';
            result.textContent = 'Account saved: ' + name;
            result.style.display = 'block';
            setTimeout(function() { result.style.display = 'none'; }, 2000);
        } else {
            result.className = 'settings-result error';
            result.textContent = data.error || 'Failed to save';
            result.style.display = 'block';
        }
    } catch(e) {
        result.className = 'settings-result error';
        result.textContent = 'Error: ' + e.message;
        result.style.display = 'block';
    }
}
async function removeProvider(label) {
    if (!confirm('Remove account "' + label + '"?')) return;
    var result = document.getElementById('settings-result');
    result.className = 'settings-result';
    result.style.display = 'none';
    try {
        var r = await fetch('/api/settings/wavespeed/accounts/remove', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({label: label})
        });
        var data = await r.json();
        if (data.ok) {
            loadProviderList();
            checkApiStatus();
            result.className = 'settings-result success';
            result.textContent = 'Removed ' + label;
            result.style.display = 'block';
            setTimeout(function() { result.style.display = 'none'; }, 2000);
        } else {
            result.className = 'settings-result error';
            result.textContent = data.error || 'Failed to remove';
            result.style.display = 'block';
        }
    } catch(e) {
        result.className = 'settings-result error';
        result.textContent = 'Error: ' + e.message;
        result.style.display = 'block';
    }
}

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
        if (isActive) {
            html += '<button class="provider-check active" title="Active provider" disabled>' + _checkSvg + '</button>';
        } else {
            html += '<button class="provider-check" onclick="confirmSwitchApi(\'' + esc(label) + '\')" title="Set as default">' + _checkSvg + '</button>';
        }
        html += '<button class="provider-remove" onclick="removeApiProvider(\'' + esc(label) + '\')" title="Remove provider">' + _delSvg2 + '</button>';
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
  if (!confirm('Switch active API to "' + label + '"? This will use this key for all new generations.')) return;
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
        
        checkApiStatus();
        preloadAccounts();
        preloadValidation();
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