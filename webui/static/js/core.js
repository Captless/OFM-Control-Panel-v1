// core.js — errors, api() helper, setLive, toast, esc(). Load first.
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
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
