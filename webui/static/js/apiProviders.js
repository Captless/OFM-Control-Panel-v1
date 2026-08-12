// apiProviders.js — API provider status, modal, account management.
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
