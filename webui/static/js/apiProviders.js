// apiProviders.js — API provider status, modal, account management.

var _selectedAccount = null;
var _lastIdentity = '';
var _lastApiCount = 0;

function updateApiLabel() {
  var user = document.getElementById('api-user');
  if (!user) return;
  var text = _selectedAccount || (_lastApiCount > 0 ? _lastApiCount + ' API' + (_lastApiCount !== 1 ? 's' : '') : 'No API keys');
  if (user.textContent !== text) user.textContent = text;
}

async function checkApiStatus() {
  var dot = document.getElementById('api-dot');
  var user = document.getElementById('api-user');
  if (!dot || !user) { requestAnimationFrame(function() { checkApiStatus(); }); return; }
  try {
    var controller = new AbortController();
    var timeoutId = setTimeout(function() { controller.abort(); }, 10000);
    var r = await fetch('/api/settings/key/status', { signal: controller.signal });
    clearTimeout(timeoutId);
    var data = await r.json();
    setLive('', 'Live');
    var accounts = data.wavespeed_accounts || {};
    var active = data.active_wavespeed_account || '';
    var count = Object.keys(accounts).length;
    _lastApiCount = count;
    if (count > 0) {
      dot.className = 'trigger-dot valid';
      _selectedAccount = (active && accounts[active]) ? active : _selectedAccount;
      updateApiLabel();
    } else {
      dot.className = 'trigger-dot invalid';
      _lastApiCount = 0;
      _selectedAccount = null;
      updateApiLabel();
    }
  } catch(e) {
    if (e.name === 'AbortError') {
      var d = document.getElementById('api-dot');
      if (d) d.className = 'trigger-dot invalid';
      setLive('error', 'Offline');
      return;
    }
    var d2 = document.getElementById('api-dot');
    if (d2) d2.className = 'trigger-dot invalid';
    setLive('error', 'Offline');
  }
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    var apiModal = document.getElementById('api-modal');
    if (apiModal && apiModal.classList.contains('show')) closeApiModal();
  }
});
document.addEventListener('click', function(e) {
  if (!e.target.closest('.modal-box') && !e.target.closest('#api-nav-trigger')) closeApiModal();
});

var _delSvg2 = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';

var _validationCache = null;
var _validationCacheTime = 0;
var _accountsCache = null;
var _accountsCacheTime = 0;

function _invalidateValidation() { _validationCache = null; _validationCacheTime = 0; }
function _invalidateAccounts() { _accountsCache = null; _accountsCacheTime = 0; }

async function _getValidationResults() {
  var now = Date.now();
  if (_validationCache && now - _validationCacheTime < 30000) return _validationCache;
  try {
    var r = await fetch('/api/settings/wavespeed/accounts/validate-all');
    var data = await r.json();
    if (data.ok) { _validationCache = data.results || {}; _validationCacheTime = now; return _validationCache; }
  } catch(e) {}
  return {};
}

async function preloadAccounts() {
  try {
    var r = await fetch('/api/settings/wavespeed/accounts');
    var data = await r.json();
    if (data.ok && data.accounts) { _accountsCache = data; _accountsCacheTime = Date.now(); }
  } catch(e) {}
}
async function preloadValidation() {
  try {
    var r = await fetch('/api/settings/wavespeed/accounts/validate-all');
    var data = await r.json();
    if (data.ok) { _validationCache = data.results || {}; _validationCacheTime = Date.now(); }
  } catch(e) {}
}

function _renderAccounts(data, validation) {
  var list = document.getElementById('api-provider-list');
  if (!list) return;
  if (!data.ok || !data.accounts || Object.keys(data.accounts).length === 0) {
    list.innerHTML = '<div class="empty-state"><p>No providers configured.</p><p class="empty-hint">Add one below.</p></div>';
    _selectedAccount = null; _lastApiCount = 0; updateApiLabel(); return;
  }
  var active = data.active || '';
  _selectedAccount = active; updateApiLabel();
  var html = '';
  Object.keys(data.accounts).forEach(function(label) {
    var preview = data.accounts[label];
    var isActive = (label === active);
    var isValid = validation[label];
    var hasValidation = validation.hasOwnProperty(label);
    var statusClass = hasValidation ? (isValid ? 'valid' : 'invalid') : 'checking';
    var statusText = hasValidation ? (isValid ? 'valid' : 'invalid') : 'checking...';
    var maskedKey = '••••••••' + (preview.length > 4 ? preview.slice(-4) : '');
    html += '<div class="provider-row' + (isActive ? ' selected' : '') + '">';
    html += '<span class="provider-dot ' + statusClass + '"></span>';
    html += '<div class="provider-body">';
    html += '<span class="provider-name">' + esc(label) + '</span>';
    html += '<span class="provider-key">' + maskedKey + '</span>';
    html += '</div>';
    html += '<span class="provider-bal" data-account="' + esc(label) + '">$--</span>';
    html += '<span class="provider-status ' + statusClass + '">' + statusText + '</span>';
    html += '<div class="provider-actions">';
    html += '<label class="provider-toggle" title="' + (isActive ? 'Active provider' : 'Set as active provider') + '">';
    html += '<input type="checkbox" role="switch" aria-label="Set as active provider" ' + (isActive ? 'checked' : '') + (Object.keys(data.accounts).length === 1 ? ' disabled' : '') + ' onclick="toggleProvider(\'' + esc(label) + '\', this)">';
    html += '<span class="toggle-slider"></span></label>';
    html += '<button class="btn-sm-outline" onclick="removeApiProvider(\'' + esc(label) + '\')" title="Remove provider">' + _delSvg2 + '</button>';
    html += '</div></div>';
  });
  list.innerHTML = html;
  Object.keys(data.accounts).forEach(function(label) {
    fetch('/api/balance/account?account=' + encodeURIComponent(label)).then(function(res) { return res.json(); }).then(function(d) {
      var balSpan = document.querySelector('.provider-bal[data-account="' + esc(label).replace(/"/g, '\\"') + '"]');
      if (balSpan && d && typeof d.balance === 'number') balSpan.textContent = '$' + d.balance.toFixed(2);
    }).catch(function(){});
  });
}

function _setApiExpanded(open) {
  var t = document.getElementById('api-nav-trigger');
  if (t) { t.setAttribute('aria-expanded', open ? 'true' : 'false'); t.classList.toggle('open', open); }
}

function toggleApiModal() {
  var modal = document.getElementById('api-modal');
  if (!modal) return;
  if (modal.classList.contains('show')) { closeApiModal(); }
  else { modal.classList.add('show'); _setApiExpanded(true); loadApiProviderList(); }
}
function closeApiModal() {
  var modal = document.getElementById('api-modal');
  if (modal) modal.classList.remove('show');
  _setApiExpanded(false);
}

async function loadApiProviderList() {
  var list = document.getElementById('api-provider-list');
  if (!list) return;
  if (_accountsCache) {
    _renderAccounts(_accountsCache, {});
  } else {
    list.innerHTML = '<div class="empty-state"><p>Loading providers…</p></div>';
  }
  try {
    var r = await fetch('/api/settings/wavespeed/accounts');
    var data = await r.json();
    if (data.ok && data.accounts) {
      _accountsCache = data; _accountsCacheTime = Date.now();
      var validation = await _getValidationResults();
      _renderAccounts(data, validation);
    }
  } catch(e) {
    if (!_accountsCache) list.innerHTML = '<div class="empty-state"><p>Error loading accounts</p></div>';
  }
}

async function confirmSwitchApi(label) {
  try {
    var r = await fetch('/api/settings/wavespeed/active', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({label: label}) });
    var data = await r.json();
    if (data.ok) {
      _selectedAccount = label; _lastApiCount = 0; updateApiLabel();
      _invalidateValidation(); checkApiStatus(); fetchBalance();
      if (_accountsCache && _accountsCache.accounts) { _accountsCache.active = label; _renderAccounts(_accountsCache, {}); }
      try {
        var rr = await fetch('/api/settings/wavespeed/accounts');
        var fresh = await rr.json();
        if (fresh.ok && fresh.accounts) { _accountsCache = fresh; _accountsCacheTime = Date.now(); var v = await _getValidationResults(); _renderAccounts(fresh, v); }
      } catch(e) {}
    }
  } catch(e) {
    var result = document.getElementById('api-modal-result');
    if (result) { result.className = 'api-result error'; result.textContent = 'Error switching account'; result.style.display = 'block'; setTimeout(function() { result.style.display = 'none'; }, 3000); }
  }
}

function toggleProvider(label, checkbox) {
  if (!checkbox.checked) { checkbox.checked = true; return; }
  if (_selectedAccount === label && checkbox.checked) return;
  confirmSwitchApi(label);
}

async function addApiProvider() {
  var name = document.getElementById('api-new-provider-name').value.trim().toLowerCase();
  var key = document.getElementById('api-new-provider-key').value.trim();
  var result = document.getElementById('api-modal-result');
  result.className = 'api-result'; result.style.display = 'none';
  if (!name || !key) { result.className = 'api-result error'; result.textContent = 'Enter both account name and key'; result.style.display = 'block'; return; }
  try {
    var r = await fetch('/api/settings/wavespeed/accounts/set', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({label: name, key: key}) });
    var data = await r.json();
    if (data.ok) {
      document.getElementById('api-new-provider-name').value = '';
      document.getElementById('api-new-provider-key').value = '';
      if (_accountsCache && _accountsCache.accounts) {
        _accountsCache.accounts[name] = key;
        _accountsCache.active = data.active || _accountsCache.active || name;
        _renderAccounts(_accountsCache, {});
      }
      result.className = 'api-result success'; result.textContent = 'Account saved: ' + name; result.style.display = 'block';
      setTimeout(function() { result.style.display = 'none'; }, 2000);
    } else {
      result.className = 'api-result error'; result.textContent = data.error || 'Failed to save'; result.style.display = 'block';
      setTimeout(function() { result.style.display = 'none'; }, 3000);
    }
  } catch(e) {
    result.className = 'api-result error'; result.textContent = 'Error: ' + e.message; result.style.display = 'block';
    setTimeout(function() { result.style.display = 'none'; }, 3000);
  }
}

async function removeApiProvider(label) {
  if (!confirm('Remove account "' + label + '"?')) return;
  var result = document.getElementById('api-modal-result');
  result.className = 'api-result'; result.style.display = 'none';
  try {
    var r = await fetch('/api/settings/wavespeed/accounts/remove', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({label: label}) });
    var data = await r.json();
    if (data.ok) {
      if (_accountsCache && _accountsCache.accounts) {
        delete _accountsCache.accounts[label];
        if (_accountsCache.active === label) _accountsCache.active = Object.keys(_accountsCache.accounts)[0] || '';
        _renderAccounts(_accountsCache, _validationCache || {});
      }
      _invalidateValidation(); checkApiStatus();
      result.className = 'api-result success'; result.textContent = 'Removed ' + label; result.style.display = 'block';
      setTimeout(function() { result.style.display = 'none'; }, 2000);
    } else {
      result.className = 'api-result error'; result.textContent = data.error || 'Failed to remove'; result.style.display = 'block';
      setTimeout(function() { result.style.display = 'none'; }, 3000);
    }
  } catch(e) {
    result.className = 'api-result error'; result.textContent = 'Error: ' + e.message; result.style.display = 'block';
    setTimeout(function() { result.style.display = 'none'; }, 3000);
  }
}