// captions.js — content-aware caption generator.

var _captions = [];
var _captionBanks = {};
var _activeCaptionBankId = '';

function getSelectedCapHook() {
  var r = document.querySelector('input[name="cap_hook"]:checked');
  return r ? r.value : 'vulnerable';
}

function getSelectedCaptionBankId() {
  var r = document.querySelector('input[name="cap_bank"]:checked');
  return r ? r.value : '';
}

async function loadCaptionBanks() {
  var data = await api('/api/caption-banks');
  _captionBanks = (data && data.banks) ? data.banks : {};
  var act = await api('/api/caption-banks/active');
  _activeCaptionBankId = (act && act.active) || '';
  renderCaptionBanks();
}

function renderCaptionBanks() {
  var row = document.getElementById('caption-bank-row');
  if (!row) return;
  var ids = Object.keys(_captionBanks);
  var html = '<label class="pill' + (_activeCaptionBankId === '' ? ' active' : '') + '"><input type="radio" name="cap_bank" value="" ' + (_activeCaptionBankId === '' ? 'checked' : '') + '><span class="pill-body">Default</span></label>';
  for (var i = 0; i < ids.length; i++) {
    var id = ids[i];
    var b = _captionBanks[id] || {};
    var isActive = (id === _activeCaptionBankId);
    html += '<label class="pill' + (isActive ? ' active' : '') + '"><input type="radio" name="cap_bank" value="' + esc(id) + '" ' + (isActive ? 'checked' : '') + '><span class="pill-body">' + esc(b.name || id) + '</span></label>';
  }
  row.innerHTML = html;
}

function setActiveCaptionBank(id) {
  api('/api/caption-banks/active', { id: id }).then(function(r) {
    if (r && r.ok) {
      _activeCaptionBankId = (r.active || '');
      renderCaptionBanks();
      showSuccess(id ? 'Active caption bank set' : 'Using Default caption bank');
    } else {
      showError((r && (r.error || r.output)) || 'Failed to set active caption bank');
    }
  });
}

function exportCaptionBank() {
  var id = getSelectedCaptionBankId() || _activeCaptionBankId || '';
  if (!id) id = 'default';
  fetch('/api/caption-banks/export?id=' + encodeURIComponent(id)).then(function(res) {
    if (!res.ok) return res.json().then(function(j) { throw new Error((j && j.error) || 'Export failed'); });
    var disposition = res.headers.get('Content-Disposition') || '';
    var m = /filename="?([^"]+)"?/.exec(disposition);
    var filename = m ? m[1] : 'caption_bank.py';
    return res.blob().then(function(blob) {
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showSuccess('Caption bank exported');
    });
  }).catch(function(err) {
    showError(err.message || 'Export failed');
  });
}

function importCaptionBank(file) {
  if (!file) return;
  var reader = new FileReader();
  reader.onload = function(e) {
    var name = file.name.replace(/\.py$/i, '').replace(/[_-]+/g, ' ').trim() || 'Imported Bank';
    api('/api/caption-banks/import', { name: name, content: e.target.result }).then(function(r) {
      if (r && r.ok) {
        _activeCaptionBankId = r.bank.id;
        showSuccess('Imported caption bank "' + r.bank.name + '"');
        loadCaptionBanks();
      } else {
        showError((r && (r.error || r.output)) || 'Import failed');
      }
    }).catch(function(err) { showError('Import failed: ' + err.message); });
  };
  reader.onerror = function() { showError('Import failed: could not read file'); };
  reader.readAsText(file);
}

document.addEventListener('DOMContentLoaded', function() {
  var change = function(e) {
    if (e.target && e.target.name === 'cap_bank') {
      setActiveCaptionBank(e.target.value);
    }
  };
  document.addEventListener('change', change);
});

async function generateCaptions() {
  var btn = document.getElementById('btn-caption');
  var txt = btn ? btn.querySelector('.btn-text') : null;
  var countEl = document.getElementById('cap-count');
  var count = countEl ? parseInt(countEl.value, 10) : 5;
  if (isNaN(count) || count < 1) count = 5;
  if (count > 20) count = 20;
  var hook = getSelectedCapHook();
  var body = { count: count };
  if (hook !== 'mixed') body.hook_types = [hook];
  if (btn) btn.disabled = true;
  if (txt) txt.textContent = 'Generating...';
  var r = await api('/api/captions/generate', body);
  if (btn) btn.disabled = false;
  if (txt) txt.textContent = 'Generate Captions';
  if (r && r.ok && Array.isArray(r.captions)) {
    renderCaptions(r.captions);
    var ca = document.getElementById('caption-actions');
    if (ca) ca.style.display = '';
    showSuccess('Generated ' + r.captions.length + ' captions');
  } else {
    showError((r && r.error) ? r.error : 'Failed to generate captions');
  }
}

function renderCaptions(caps) {
  _captions = caps || [];
  var list = document.getElementById('caption-list');
  if (!list) return;
  var html = '';
  for (var i = 0; i < _captions.length; i++) {
    var c = _captions[i];
    var tags = (c.hashtags || []).map(function(h) { return esc(h); }).join(' ');
    html += '<div class="caption-item">'
      + '<div class="caption-item-head">'
      + '<span class="cap-badge">' + esc(c.hook_type || '') + '</span>'
      + '</div>'
      + '<pre class="caption-text-raw">' + esc(c.on_screen || '') + '</pre>'
      + '<div class="caption-meta">' + (c.cta ? esc(c.cta) : '') + (tags ? ' ' + tags : '') + '</div>'
      + '<button class="btn-sm-outline" onclick="copyCaption(' + i + ')">Copy</button>'
      + '</div>';
  }
  list.innerHTML = html;
}

function copyCaption(idx) {
  if (!_captions || !_captions[idx]) return;
  var c = _captions[idx];
  var text = c.on_screen || '';
  navigator.clipboard.writeText(text).then(function() {
    showSuccess('On-screen caption copied');
  }).catch(function() {
    showError('Copy failed');
  });
}

async function copyAllCaptions() {
  if (!_captions.length) return;
  var text = _captions.map(function(c) { return c.on_screen || ''; }).join('\n\n');
  navigator.clipboard.writeText(text).then(function() {
    showSuccess('All on-screen captions copied');
  }).catch(function() {
    showError('Copy failed');
  });
}

function clearCaptions() {
  _captions = [];
  var list = document.getElementById('caption-list');
  if (list) list.innerHTML = '<div class="empty-state"><p>No captions yet.</p><p class="empty-hint">Describe your content, pick a hook type, then generate.</p></div>';
  var ca = document.getElementById('caption-actions');
  if (ca) ca.style.display = 'none';
}
