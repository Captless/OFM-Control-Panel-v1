// promptBanks.js — prompt bank tiles, editor modal, export/import.

var _activeBankId = '';
var _savedBanks = {};
var _pendingDeleteId = null;

var _POOL_LABELS = {
  'INDOOR_SCENES': 'Indoor Scenes', 'MIRROR_SCENES': 'Mirror Scenes', 'OUTDOOR_SCENES': 'Outdoor Scenes',
  'FRAMING': 'Framing', 'HAIR': 'Hair', 'POSES': 'Poses', 'HANDHELD_POSES': 'Handheld Poses',
  'QUALITY': 'Quality', 'OUTFIT_TOPS_POOLS': 'Outfit Tops', 'OUTFIT_BOTTOMS_POOLS': 'Outfit Bottoms',
  'LIGHTING_POOLS': 'Lighting', 'DEFAULT_NEGATIVE': 'Default Negative', 'MIRROR_NEGATIVE': 'Mirror Negative',
  'IDENTITY_LOCK': 'Identity Lock'
};
function _poolLabel(name) { return _POOL_LABELS[name] || name; }

var _OVERRIDABLE_POOLS = [
  'INDOOR_SCENES', 'MIRROR_SCENES', 'OUTDOOR_SCENES', 'FRAMING', 'HAIR', 'POSES',
  'HANDHELD_POSES', 'QUALITY', 'OUTFIT_TOPS_POOLS', 'OUTFIT_BOTTOMS_POOLS', 'LIGHTING_POOLS',
  'DEFAULT_NEGATIVE', 'MIRROR_NEGATIVE', 'IDENTITY_LOCK'
];

var _POOL_PURPOSES = {
  'INDOOR_SCENES': 'Indoor photo locations (bedroom, bathroom, living room)',
  'MIRROR_SCENES': 'Mirror selfie locations (bathroom mirror, wardrobe mirror)',
  'OUTDOOR_SCENES': 'Outdoor locations (alley, street, rooftop, graffiti wall)',
  'FRAMING': 'Camera angle & crop',
  'HAIR': 'Hair state (wet, messy, damp, braided)',
  'POSES': 'Body posture (weight shift, hip tilt, candid)',
  'HANDHELD_POSES': 'Handheld-selfie angles & gestures',
  'QUALITY': 'iPhone aesthetic (grain, noise, raw sensor)',
  'OUTFIT_TOPS_POOLS': 'Top clothing by category',
  'OUTFIT_BOTTOMS_POOLS': 'Bottom clothing by category',
  'LIGHTING_POOLS': 'Lighting mood by type (warm, cool, dimlit, flash, screen, mixed)',
  'DEFAULT_NEGATIVE': 'What to avoid in handheld shots',
  'MIRROR_NEGATIVE': 'What to avoid in mirror shots',
  'IDENTITY_LOCK': 'Identity consistency prompt'
};

function _poolValType(val) {
  if (val == null) return 'list';
  if (Array.isArray(val)) return 'list';
  if (typeof val === 'object') return 'dict';
  return 'str';
}
function _poolTypeBadgeOf(val) {
  var t = _poolValType(val);
  if (t === 'dict') return 'styles';
  if (t === 'str') return 'text';
  return 'list';
}
function _poolCopy(val) {
  if (val == null) return [];
  if (Array.isArray(val)) return val.slice();
  if (typeof val === 'object') {
    var o = {};
    Object.keys(val).forEach(function(k) { o[k] = Array.isArray(val[k]) ? val[k].slice() : []; });
    return o;
  }
  return String(val);
}
function _poolToText(val) {
  var t = _poolValType(val);
  if (t === 'str') return String(val == null ? '' : val);
  if (t === 'dict') {
    var lines = [];
    Object.keys(val).forEach(function(k) { lines.push(k + ': ' + ((val[k] || []).join(', '))); });
    return lines.join('\n');
  }
  return (Array.isArray(val) ? val : []).join('\n');
}
function _textToPool(name, text) {
  var lines = text.split('\n').map(function(s) { return s.trim(); }).filter(Boolean);
  var cur = (_bankEditorDraft && _bankEditorDraft.pools) ? _bankEditorDraft.pools[name] : null;
  var t = _poolValType(cur);
  if (t === 'str') return lines.join(' ');
  if (t === 'dict') {
    var out = {};
    lines.forEach(function(line) {
      var idx = line.indexOf(':');
      if (idx === -1) return;
      var key = line.substring(0, idx).trim();
      var items = line.substring(idx + 1).split(',').map(function(s) { return s.trim(); }).filter(Boolean);
      if (!key) return;
      if (!out[key]) out[key] = [];
      items.forEach(function(it) { if (out[key].indexOf(it) === -1) out[key].push(it); });
    });
    return out;
  }
  return lines;
}
function _poolCountText(val) {
  var t = _poolValType(val);
  if (t === 'dict') return Object.keys(val).length + ' styles';
  if (t === 'str') return 'text';
  return (Array.isArray(val) ? val.length : 0) + ' items';
}
function _poolHintText(val) {
  var t = _poolValType(val);
  if (t === 'dict') return 'Format: style: item1, item2 — one style per line.';
  if (t === 'str') return 'Single block of text.';
  return 'One item per line.';
}

async function loadActiveBank() {
  var data = await api('/api/settings/banks/active');
  _activeBankId = (data && data.active) || '';
}
function getSelectedBankId() { return _activeBankId; }

function setActiveBank(id) {
  if (id === _activeBankId) return;
  var prev = _activeBankId;
  _activeBankId = id;
  renderBankList();
  api('/api/settings/banks/active', {id: id}).then(function(r) {
    if (r && r.ok) {
      _activeBankId = (r.active || '');
      showSuccess(id ? 'Active prompt bank set' : 'Using Default prompt bank');
    } else {
      _activeBankId = prev;
      showError((r && (r.error || r.output)) || 'Failed to set active bank');
      renderBankList();
    }
  });
}

async function loadBankEditor() {
  await loadActiveBank();
  await renderBankList();
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
    var id = ids[i];
    var b = banks[id] || {};
    var isBuiltin = (id === 'builtin');
    var isActive = isBuiltin ? (!_activeBankId) : (id === _activeBankId);
    var poolNames = Object.keys(b.pools || {});
    var name = b.name || id;
    html += '<div class="bank-tile' + (isActive ? ' active' : '') + (isBuiltin ? ' is-builtin' : '') + '" role="radio" aria-checked="' + (isActive ? 'true' : 'false') + '" aria-label="' + esc(name) + '">';
    html += '<div class="bank-tile-head">';
    html += '<span class="bank-tile-radio" aria-hidden="true"></span>';
    html += '<span class="bank-tile-name' + (isBuiltin ? ' is-builtin' : '') + '"' + (isBuiltin ? '' : ' onclick="openBankEditor(\'' + esc(id) + '\')" title="Click to edit"') + '>' + esc(name) + '</span>';
    if (isActive) html += '<span class="bank-tile-active-badge">ACTIVE</span>';
    else html += '<button type="button" class="bank-tile-use" onclick="setActiveBank(\'' + esc(id) + '\')" title="Use this bank">Use</button>';
    html += '</div>';
    html += '<div class="bank-tile-pools">';
    if (!poolNames.length) {
      html += '<span class="bank-chip">' + (isBuiltin ? 'Built-in defaults' : 'No overrides yet') + '</span>';
    } else {
      for (var p = 0; p < poolNames.length; p++) {
        html += '<span class="bank-chip">' + esc(_poolLabel(poolNames[p])) + '</span>';
      }
    }
    html += '</div>';
    html += '<div class="bank-tile-foot">';
    html += '<span class="bank-tile-count">' + poolNames.length + ' pool' + (poolNames.length !== 1 ? 's' : '') + '</span>';
    html += '<button type="button" class="btn-sm-outline" onclick="openBankEditor(\'' + esc(id) + '\')">Edit</button>';
    if (!isBuiltin) {
      html += '<button type="button" class="btn-sm-outline danger" onclick="confirmDeleteBank(\'' + esc(id) + '\')">Delete</button>';
    }
    html += '</div>';
    html += '</div>';
  }
  html += '<button type="button" class="bank-tile-new" onclick="openNewBankFromDefault()">+ Create New Bank</button>';
  list.innerHTML = html;
}

// ── Bank Editor Modal ──
var _bankEditorId = '';
var _bankEditorPool = '';
var _bankEditorDraft = null;
var _bankEditorIsNew = false;
var _bankEditorDefaults = null;

function showBankEditor() {
  var modal = document.getElementById('bank-editor-modal');
  if (modal) modal.classList.add('show');
}
function closeBankEditor() {
  var modal = document.getElementById('bank-editor-modal');
  if (modal) modal.classList.remove('show');
  _bankEditorId = ''; _bankEditorPool = ''; _bankEditorDraft = null; _bankEditorIsNew = false;
}

async function openBankEditor(id) {
  var b = (id === 'builtin') ? null : (_savedBanks[id] || null);
  if (id !== 'builtin' && !b) return;
  var def = await api('/api/settings/banks/pools/defaults');
  _bankEditorDefaults = (def && def.pools) ? def.pools : {};
  var pools = (id === 'builtin') ? _bankEditorDefaults : (b.pools || {});
  _bankEditorId = id;
  var draft = {};
  Object.keys(pools).forEach(function(k) { draft[k] = _poolCopy(pools[k]); });
  _bankEditorDraft = { id: id, name: (b ? (b.name || '') : 'Built-in'), pools: draft };
  _bankEditorPool = Object.keys(draft)[0] || '';
  var search = document.getElementById('be-pool-search');
  if (search) search.value = '';
  renderBankEditor();
  showBankEditor();
}

function renderBankEditor() {
  if (!_bankEditorDraft) return;
  var readOnly = (_bankEditorId === 'builtin');
  var isNew = _bankEditorIsNew;
  document.getElementById('bank-editor-title').textContent = readOnly ? 'Built-in Pools' : (isNew ? 'Create Bank' : 'Edit Bank');
  document.getElementById('bank-editor-subtitle').textContent = readOnly ? 'View-only — create a bank to edit pools' : (_bankEditorDraft.name || '');
  var nameInput = document.getElementById('be-name');
  if (nameInput) { nameInput.value = _bankEditorDraft.name; nameInput.disabled = readOnly; }
  var saveBtn = document.getElementById('be-save');
  if (saveBtn) saveBtn.textContent = isNew ? 'Create Bank' : 'Save Bank';
  var list = document.getElementById('be-pool-list');
  var names = Object.keys(_bankEditorDraft.pools);
  var html = '';
  for (var i = 0; i < names.length; i++) {
    var n = names[i];
    var val = _bankEditorDraft.pools[n];
    var selected = (n === _bankEditorPool);
    var isCustom = (_OVERRIDABLE_POOLS.indexOf(n) === -1);
    var purpose = _POOL_PURPOSES[n] || '';
    html += '<div class="be-pool-item' + (selected ? ' active' : '') + '" data-name="' + esc(n) + '" role="option" aria-selected="' + (selected ? 'true' : 'false') + '" tabindex="' + (selected ? '0' : '-1') + '" onclick="selectBankPool(\'' + esc(n) + '\')">';
    html += '<span class="be-pool-item-name" title="' + esc(purpose) + '">' + esc(_poolLabel(n)) + '</span>';
    if (isCustom && !readOnly) html += '<span class="be-pool-item-badge custom">custom</span>';
    html += '<span class="be-pool-item-count">' + _poolCountText(val) + '</span>';
    if (!readOnly) html += '<button type="button" class="be-pool-del" onclick="event.stopPropagation(); deleteBankPool(\'' + esc(n) + '\')" title="Remove pool ' + esc(_poolLabel(n)) + '">&times;</button>';
    html += '</div>';
  }
  if (!readOnly) {
    var avail = [];
    for (var a = 0; a < _OVERRIDABLE_POOLS.length; a++) {
      if (_bankEditorDraft.pools[_OVERRIDABLE_POOLS[a]] === undefined) avail.push(_OVERRIDABLE_POOLS[a]);
    }
    if (avail.length) {
      html += '<div class="be-avail-head">Available built-ins</div>';
      for (var a2 = 0; a2 < avail.length; a2++) {
        var an = avail[a2];
        html += '<div class="be-avail-item"><span class="be-avail-name" title="' + esc(_POOL_PURPOSES[an] || '') + '">' + esc(_poolLabel(an)) + '</span><button type="button" class="be-avail-add" onclick="addBuiltinPool(\'' + esc(an) + '\')">Override</button></div>';
      }
    }
  }
  list.innerHTML = html;
  var resetBtn = document.getElementById('be-reset');
  var addBtns = document.querySelectorAll('.be-add-pool');
  for (var a = 0; a < addBtns.length; a++) addBtns[a].style.display = readOnly ? 'none' : '';
  if (saveBtn) saveBtn.style.display = readOnly ? 'none' : '';
  if (resetBtn) resetBtn.style.display = readOnly ? 'none' : '';
  if (!_bankEditorPool || _bankEditorDraft.pools[_bankEditorPool] === undefined) {
    _bankEditorPool = names[0] || '';
  }
  _syncPoolUi();
}

function _syncPoolUi() {
  var name = _bankEditorPool;
  var val = (_bankEditorDraft && name) ? _bankEditorDraft.pools[name] : undefined;
  var ta = document.getElementById('be-textarea');
  if (ta) ta.value = (name && val !== undefined) ? _poolToText(val) : '';
  document.getElementById('be-pool-name').textContent = name ? _poolLabel(name) : '';
  document.getElementById('be-pool-type').textContent = (val === undefined || val === null) ? '' : _poolTypeBadgeOf(val);
  document.getElementById('be-hint').textContent = (val === undefined || val === null) ? '' : _poolHintText(val);
  var purposeEl = document.getElementById('be-pool-purpose');
  if (purposeEl) purposeEl.textContent = (name && _POOL_PURPOSES[name]) ? _POOL_PURPOSES[name] : '';
  var items = document.querySelectorAll('.be-pool-item');
  for (var i = 0; i < items.length; i++) {
    var isSel = items[i].dataset.name === name;
    items[i].classList.toggle('active', isSel);
    items[i].setAttribute('aria-selected', isSel ? 'true' : 'false');
    items[i].tabIndex = isSel ? 0 : -1;
  }
}

function selectBankPool(name) {
  if (!_bankEditorDraft || _bankEditorDraft.pools[name] === undefined) return;
  if (_bankEditorId !== 'builtin') {
    var cur = _bankEditorPool;
    var ta = document.getElementById('be-textarea');
    if (cur && ta && _bankEditorDraft.pools[cur] !== undefined) {
      _bankEditorDraft.pools[cur] = _textToPool(cur, ta.value);
    }
  }
  _bankEditorPool = name;
  _syncPoolUi();
}

function deleteBankPool(name) {
  if (_bankEditorId === 'builtin') return;
  var names = Object.keys(_bankEditorDraft.pools);
  if (names.length <= 1) { showError('Bank must keep at least one pool'); return; }
  delete _bankEditorDraft.pools[name];
  if (_bankEditorPool === name) _bankEditorPool = Object.keys(_bankEditorDraft.pools)[0];
  renderBankEditor();
}

function addCustomPool(type) {
  if (_bankEditorId === 'builtin') return;
  var name = prompt('New pool name (UPPERCASE, e.g. OCCASIONS):');
  if (!name) return;
  name = name.trim().toUpperCase().replace(/\s+/g, '_');
  if (!name) return;
  if (_bankEditorDraft.pools[name] !== undefined) { showError('Pool "' + name + '" already exists'); return; }
  _bankEditorDraft.pools[name] = (type === 'dict') ? {} : (type === 'str') ? '' : [];
  _bankEditorPool = name;
  renderBankEditor();
}

function addBuiltinPool(name) {
  if (_bankEditorId === 'builtin') return;
  if (_bankEditorDraft.pools[name] !== undefined) return;
  var val = (_bankEditorDefaults && _bankEditorDefaults[name] !== undefined) ? _bankEditorDefaults[name] : [];
  _bankEditorDraft.pools[name] = _poolCopy(val);
  _bankEditorPool = name;
  renderBankEditor();
}

async function resetCurrentPool() {
  if (_bankEditorId === 'builtin') return;
  var name = _bankEditorPool;
  if (!name || _bankEditorDraft.pools[name] === undefined) return;
  var def = await api('/api/settings/banks/pools/defaults');
  var defaults = (def && def.pools) ? def.pools : {};
  _bankEditorDraft.pools[name] = (defaults[name] !== undefined) ? _poolCopy(defaults[name]) : [];
  _syncPoolUi();
  showInfo('Pool reset — press Save Bank to keep');
}

async function saveBankFromModal() {
  if (_bankEditorId === 'builtin') return;
  var name = _bankEditorPool;
  var text = document.getElementById('be-textarea').value;
  if (name && _bankEditorDraft.pools[name] !== undefined) {
    _bankEditorDraft.pools[name] = _textToPool(name, text);
  }
  var nameInput = document.getElementById('be-name');
  var newName = (nameInput ? nameInput.value : '').trim();
  if (!newName) newName = _bankEditorDraft.name;
  var btn = document.getElementById('be-save');
  var btnTxt = btn ? btn.textContent : '';
  if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }
  if (_bankEditorIsNew) {
    var r = await api('/api/settings/banks/create', {name: newName, pools: _bankEditorDraft.pools});
    if (btn) { btn.disabled = false; btn.textContent = btnTxt; }
    if (r && r.ok) {
      _activeBankId = r.bank.id; _savedBanks[r.bank.id] = r.bank;
      showSuccess('Bank created');
      closeBankEditor(); renderBankList();
    } else { showError((r && (r.error || r.output)) || 'Create failed'); }
    return;
  }
  var body = {id: _bankEditorId, pools: _bankEditorDraft.pools};
  if (newName) body.name = newName;
  var r2 = await api('/api/settings/banks/update', body);
  if (btn) { btn.disabled = false; btn.textContent = btnTxt; }
  if (r2 && r2.ok) {
    showSuccess('Bank saved');
    if (newName) _bankEditorDraft.name = newName;
    closeBankEditor(); renderBankList();
  } else { showError((r2 && (r2.error || r2.output)) || 'Save failed'); }
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    var be = document.getElementById('bank-editor-modal');
    if (be && be.classList.contains('show')) { closeBankEditor(); return; }
    var db = document.getElementById('delete-bank-modal');
    if (db && db.classList.contains('show')) { closeDeleteBankModal(); return; }
  }
});
document.addEventListener('click', function(e) {
  var be = document.getElementById('bank-editor-modal');
  if (be && be.classList.contains('show') && !e.target.closest('.modal-box')) { closeBankEditor(); return; }
  var db = document.getElementById('delete-bank-modal');
  if (db && db.classList.contains('show') && !e.target.closest('.modal-box')) { closeDeleteBankModal(); }
});

document.addEventListener('DOMContentLoaded', function() {
  var poolList = document.getElementById('be-pool-list');
  var search = document.getElementById('be-pool-search');
  if (poolList) {
    if (search) {
      search.addEventListener('input', function() {
        var q = search.value.trim().toLowerCase();
        var items = poolList.querySelectorAll('.be-pool-item');
        for (var i = 0; i < items.length; i++) {
          var label = items[i].dataset.name || '';
          items[i].classList.toggle('hidden', !!q && label.toLowerCase().indexOf(q) === -1);
        }
      });
    }
    poolList.addEventListener('keydown', function(e) {
      var all = Array.prototype.slice.call(poolList.querySelectorAll('.be-pool-item'));
      var items = all.filter(function(el) { return !el.classList.contains('hidden'); });
      if (!items.length) return;
      var idx = items.indexOf(document.activeElement);
      if (idx === -1) {
        var cur = poolList.querySelector('.be-pool-item.active');
        idx = cur ? items.indexOf(cur) : 0;
      }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        var n = (e.key === 'ArrowDown') ? (idx + 1) % items.length : (idx - 1 + items.length) % items.length;
        items[n].focus(); selectBankPool(items[n].dataset.name);
      } else if (e.key === 'Home') { e.preventDefault(); items[0].focus(); selectBankPool(items[0].dataset.name); }
      else if (e.key === 'End') { e.preventDefault(); items[items.length - 1].focus(); selectBankPool(items[items.length - 1].dataset.name); }
      else if (e.key === 'Enter' || e.key === ' ') {
        var active = document.activeElement;
        if (active && active.classList && active.classList.contains('be-pool-item')) { e.preventDefault(); selectBankPool(active.dataset.name); }
      }
    });
  }
});

function generateNextBankName() {
  var max = 0;
  Object.keys(_savedBanks).forEach(function(id) {
    if (id === 'builtin') return;
    var name = _savedBanks[id].name || '';
    var m = /^Bank (\d+)$/i.exec(name);
    if (m) max = Math.max(max, parseInt(m[1], 10));
  });
  return 'Bank ' + (max + 1);
}

async function openNewBankFromDefault() {
  var name = generateNextBankName();
  var def = await api('/api/settings/banks/pools/defaults');
  var pools = (def && def.pools) ? def.pools : {};
  _bankEditorDefaults = pools;
  _bankEditorId = 'new';
  var draft = {};
  Object.keys(pools).forEach(function(k) { draft[k] = _poolCopy(pools[k]); });
  _bankEditorDraft = { id: '', name: name, pools: draft };
  _bankEditorPool = Object.keys(draft)[0] || '';
  _bankEditorIsNew = true;
  var search = document.getElementById('be-pool-search');
  if (search) search.value = '';
  renderBankEditor();
  showBankEditor();
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
  var delBtn = document.querySelector('#delete-bank-modal-box .btn-danger');
  var delTxt = delBtn ? delBtn.textContent : '';
  if (delBtn) { delBtn.disabled = true; delBtn.textContent = 'Deleting…'; }
  var r = await api('/api/settings/banks/delete', {id: id});
  if (delBtn) { delBtn.disabled = false; delBtn.textContent = delTxt; }
  closeDeleteBankModal();
  if (r && r.ok) {
    if (_activeBankId === id) _activeBankId = '';
    showSuccess('Bank deleted');
    await loadActiveBank();
    renderBankList();
  } else { showError((r && (r.error || r.output)) || 'Delete failed'); }
}

function exportBanks() {
  api('/api/settings/banks/export').then(function(data) {
    var blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'prompt_banks_' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Exported ' + Object.keys(data.banks || {}).length + ' banks', 'success');
  }).catch(function(e) { showToast('Export failed: ' + e.message, 'error'); });
}

function importBanks(file) {
  if (!file) return;
  var reader = new FileReader();
  reader.onload = function(e) {
    var parsed;
    try { parsed = JSON.parse(e.target.result); }
    catch (err) { showToast('Import failed: invalid JSON', 'error'); return; }
    if (!parsed || typeof parsed !== 'object') { showToast('Import failed: invalid format', 'error'); return; }
    api('/api/settings/banks/import', {data: parsed}).then(function(data) {
      if (data && data.ok) {
        var msg = 'Imported ' + data.imported + ' bank' + (data.imported !== 1 ? 's' : '');
        if (data.skipped) msg += ', skipped ' + data.skipped;
        showToast(msg, 'success');
        renderBankList();
      } else { showToast('Import failed: ' + ((data && (data.error || data.output)) || 'unknown'), 'error'); }
    }).catch(function(e) { showToast('Import failed: ' + e.message, 'error'); });
  };
  reader.onerror = function() { showToast('Import failed: could not read file', 'error'); };
  reader.readAsText(file);
}