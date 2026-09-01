// core.js — API helper, toast, error handling, live indicator.

function setLive(state, text) {
  var dot = document.getElementById('live-dot');
  var el = document.getElementById('live-indicator');
  var txt = document.getElementById('live-text');
  if (el) el.className = 'hud-live' + (state === 'error' ? ' error' : state === 'loading' ? ' loading' : '');
  if (txt && text) txt.textContent = text;
}

async function api(url, body) {
  try {
    var opts = { method: body ? 'POST' : 'GET', headers: {} };
    if (body) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    var r = await fetch(url, opts);
    return await r.json();
  } catch (e) {
    console.error('api error:', url, e);
    return null;
  }
}

function esc(s) {
  if (!s) return '';
  var d = document.createElement('div');
  d.appendChild(document.createTextNode(s));
  return d.innerHTML;
}

window.onerror = function(msg, src, line) {
  var el = document.getElementById('js-error');
  if (el) { el.style.display = 'block'; el.textContent = 'JS Error: ' + msg + (line ? ' (line ' + line + ')' : ''); }
  setTimeout(function() { if (el) el.style.display = 'none'; }, 6000);
};
window.addEventListener('unhandledrejection', function(e) {
  console.error('Unhandled rejection:', e.reason);
});

// Toast system
var _toastContainer = null;
function _getToastContainer() {
  if (!_toastContainer) _toastContainer = document.getElementById('toast-container');
  return _toastContainer;
}

function showToast(msg, type) {
  var c = _getToastContainer();
  if (!c) return;
  var t = document.createElement('div');
  t.className = 'toast ' + (type || 'info');
  t.innerHTML = '<span class="toast-msg">' + esc(msg) + '</span><span class="toast-close" onclick="this.parentElement.remove()">&times;</span>';
  c.appendChild(t);
  setTimeout(function() { t.classList.add('out'); setTimeout(function() { t.remove(); }, 250); }, 4000);
}
function showSuccess(msg) { showToast(msg, 'success'); }
function showError(msg) { showToast(msg, 'error'); }
function showInfo(msg) { showToast(msg, 'info'); }
function showWarning(msg) { showToast(msg, 'warning'); }
