// outputs.js — outputs rendering, actions, fullscreen viewer.

var _outputsData = [];
var _preview = null;
var _viewMode = 'table';
try { _viewMode = localStorage.getItem('ofm_view_mode') || 'table'; } catch(e) {}
var _showAll = false;
try { _showAll = localStorage.getItem('ofm_show_all') === '1'; } catch(e) {}

var _cpySvg = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
var _dlSvg = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>';
var _delSvg = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>';

function setShowAll() {
  _showAll = !_showAll;
  try { localStorage.setItem('ofm_show_all', _showAll ? '1' : '0'); } catch(e) {}
  renderOutputs();
}

function setViewMode(mode) {
  _viewMode = (mode === 'grid') ? 'grid' : 'table';
  try { localStorage.setItem('ofm_view_mode', _viewMode); } catch(e) {}
  syncViewToggle();
  renderOutputs();
}

function syncViewToggle() {
  document.querySelectorAll('.view-toggle button[data-view]').forEach(function(b) {
    var on = b.dataset.view === _viewMode;
    b.classList.toggle('active', on);
    b.setAttribute('aria-selected', on ? 'true' : 'false');
  });
}

function _batchCount(b) {
  var t = b.items.length + ' item' + (b.items.length !== 1 ? 's' : '');
  var vids = b.items.filter(function(it) { return it.is_video; }).length;
  if (vids) t += ' · ' + vids + ' video' + (vids !== 1 ? 's' : '');
  return t;
}

function _captionSpan(item, sid) {
  var txt = item.txt_content;
  var srcEsc = item.src.replace(/'/g, "\\'");
  var txtShort = txt ? txt.replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim() : '';
  if (txtShort.length > 80) txtShort = txtShort.substring(0, 80) + '...';
  var title = txt ? txt : 'Click to add caption';
  if (txt) {
    return '<span class="table-caption" onclick="editCaption(\'' + sid + '\',\'' + srcEsc + '\')" title="' + esc(title) + '\n\nClick to edit caption">' + esc(txtShort) + '</span>';
  }
  return '<span class="table-caption-placeholder" onclick="editCaption(\'' + sid + '\',\'' + srcEsc + '\')" title="' + esc(title) + '">Add caption</span>';
}

function _itemMeta(item, sid) {
  var srcEsc = item.src.replace(/'/g, "\\'");
  var html = '<div class="table-meta">';
  if (item.prompt) html += '<span class="table-prompt-link" onclick="showPrompt(\'' + srcEsc + '\')">Prompt</span>';
  var ext = item.filename ? item.filename.split('.').pop().toUpperCase() : (item.is_video ? 'MP4' : 'PNG');
  html += '<span class="table-ext">' + ext + '</span>';
  html += '<span class="table-time">' + esc(item.created_at || '') + '</span>';
  html += '</div>';
  return html;
}

function renderOutputs() {
  try {
  var batches = _outputsData;
  var area = document.getElementById('outputs-area');
  if (!area) return;
  if (_preview) { _preview.style.display = 'none'; var ov = _preview.querySelector('video'); if (ov) { ov.pause(); ov.currentTime = 0; } }
  if (!batches.length) { area.innerHTML = '<div class="outputs-empty">No outputs yet.<br>Generate your first images above.</div>'; return; }

  var total = batches.reduce(function(s, b) { return s + b.items.length; }, 0);
  var meta = document.getElementById('results-meta');
  if (meta) meta.textContent = total + (total !== 1 ? ' items' : ' item');
  var gs = document.getElementById('global-stats');
  if (gs) gs.textContent = total + (total !== 1 ? ' items' : ' item');

  var collapsed = {};
  document.querySelectorAll('.batch.collapsed').forEach(function(el) {
    collapsed[el.id.replace('batch-', '')] = true;
  });
  if (_viewMode === 'grid') { area.innerHTML = _showAll ? buildFlatGridHtml(batches) : buildGridHtml(batches); }
  else { area.innerHTML = _showAll ? buildFlatHtml(batches) : buildTableHtml(batches); }
  Object.keys(collapsed).forEach(function(id) {
    var el = document.getElementById('batch-' + id);
    if (el) el.classList.add('collapsed');
  });
  bindHoverPreview();
  var area2 = document.getElementById('outputs-area');
  if (area2) { area2.dataset.total = total; area2.dataset.batches = batches.length; }
  } catch(e) { console.error('renderOutputs error:', e); }
}

function _rowHtml(it, startIdx, isVideo) {
  var srcEsc = it.src.replace(/'/g, "\\'");
  var media = it.is_video
    ? '<video muted preload="metadata" src="/' + srcEsc + '"></video>'
    : '<img src="/' + srcEsc + '" alt="">';
  var hov = 'onmouseenter="showHover(this)" onmouseleave="hideHover()"';
  return '<div class="out-row">'
    + '<span class="out-index">' + (startIdx + 1) + '</span>'
    + '<span class="out-thumb' + (isVideo ? ' is-video' : '') + '" onclick="openFS(' + startIdx + ', true)" ' + hov + '>' + media + '</span>'
    + '<div class="out-info">'
    + _captionSpan(it, srcEsc)
    + _itemMeta(it, srcEsc)
    + '</div>'
    + '<div class="out-actions">'
    + '<button class="cp" onclick="copyCaptionText(\'' + srcEsc + '\')" title="Copy caption">' + _cpySvg + '</button>'
    + '<button class="dl" onclick="downloadMedia(\'' + srcEsc + '\')" title="Download">' + _dlSvg + '</button>'
    + '<button class="del" onclick="deleteMedia(\'' + srcEsc + '\', event)" title="Delete">' + _delSvg + '</button>'
    + '</div>'
    + '</div>';
}

function buildTableHtml(batches) {
  var html = '';
  var gi = 0;
  if (_showAll) {
    var items = [];
    batches.forEach(function(b) { items = items.concat(b.items); });
    for (var i = 0; i < items.length; i++) html += _rowHtml(items[i], i, items[i].is_video);
    return html;
  }
  batches.forEach(function(b) {
    var cid = b.id;
    html += '<div class="batch" id="batch-' + cid + '">'
      + '<div class="batch-head" onclick="toggleBatch(\'' + cid + '\')">'
      + '<span class="batch-chevron">▶</span>'
      + '<span class="batch-title">' + esc(b.name) + '</span>'
      + '<span class="batch-count">' + _batchCount(b) + '</span>'
      + '</div>'
      + '<div class="batch-body">';
    b.items.forEach(function(it) { html += _rowHtml(it, gi++, it.is_video); });
    html += '</div></div>';
  });
  return html;
}

function buildFlatHtml(batches) {
  var items = [];
  batches.forEach(function(b) { items = items.concat(b.items); });
  var html = '<div class="batch flat"><div class="batch-body">';
  for (var i = 0; i < items.length; i++) html += _rowHtml(items[i], i, items[i].is_video);
  html += '</div></div>';
  return html;
}

function buildGridHtml(batches) {
  var html = '';
  var gi = 0;
  batches.forEach(function(b) {
    html += '<div class="batch" id="batch-' + b.id + '">'
      + '<div class="batch-head" onclick="toggleBatch(\'' + b.id + '\')">'
      + '<span class="batch-chevron">▶</span>'
      + '<span class="batch-title">' + esc(b.name) + '</span>'
      + '<span class="batch-count">' + _batchCount(b) + '</span>'
      + '</div>'
      + '<div class="batch-body">' + _gridShell(b.items, gi) + '</div>'
      + '</div>';
    gi += b.items.length;
  });
  return html;
}

function buildFlatGridHtml(batches) {
  var items = [];
  batches.forEach(function(b) { items = items.concat(b.items); });
  return '<div class="batch flat"><div class="batch-body">' + _gridShell(items, 0) + '</div></div>';
}

function _gridShell(items, startIdx) {
  if (!items || !items.length) return '<div class="outputs-empty">No items</div>';
  startIdx = startIdx || 0;
  var html = '<div class="grid-view">';
  for (var i = 0; i < items.length; i++) {
    var it = items[i];
    var srcEsc = it.src.replace(/'/g, "\\'");
    var media = it.is_video ? '<video muted preload="metadata" src="/' + srcEsc + '"></video>' : '<img src="/' + srcEsc + '" alt="">';
    html += '<div class="grid-card">'
      + '<div class="grid-thumb" onclick="openFS(' + (startIdx + i) + ', true)">' + media + '</div>'
      + '<div class="grid-body">'
      + _captionSpan(it, srcEsc)
      + _itemMeta(it, srcEsc)
      + '</div>'
      + '<div class="grid-actions">'
      + '<button onclick="copyCaptionText(\'' + srcEsc + '\')" title="Copy caption">' + _cpySvg + '</button>'
      + '<button onclick="downloadMedia(\'' + srcEsc + '\')" title="Download">' + _dlSvg + '</button>'
      + '<button class="del" onclick="deleteMedia(\'' + srcEsc + '\', event)" title="Delete">' + _delSvg + '</button>'
      + '</div>'
      + '</div>';
  }
  html += '</div>';
  return html;
}

function toggleBatch(id) {
  var el = document.getElementById('batch-' + id);
  if (el) el.classList.toggle('collapsed');
}

// Store all items for fullscreen navigation
var _allItems = [];
function _cacheItems(batches) {
  _allItems = [];
  batches.forEach(function(b) { _allItems = _allItems.concat(b.items); });
}
function refreshOutputs() {
  return refreshOutputsFromServer();
}

async function refreshOutputsFromServer() {
  var r = await api('/api/outputs');
  if (r && Array.isArray(r)) {
    _outputsData = r;
    _cacheItems(r);
    renderOutputs();
  }
}

// Fullscreen
var _fsIndex = 0;
var _fsScale = 1;
var _fsTx = 0;
var _fsTy = 0;
function openFS(idx, cache) {
  if (cache) {
    _allItems = [];
    _outputsData.forEach(function(b) { _allItems = _allItems.concat(b.items); });
  }
  if (!_allItems.length) return;
  _fsIndex = idx;
  _fsScale = 1; _fsTx = 0; _fsTy = 0;
  _renderFS();
}

function _renderFS() {
  var m = document.getElementById('fs-modal');
  if (!m) return;
  if (_allItems.length === 0) return;
  var it = _allItems[_fsIndex];
  var srcEsc = it.src.replace(/'/g, "\\'");
  var media = it.is_video
    ? '<video src="/' + srcEsc + '" controls autoplay loop></video>'
    : '<img src="/' + srcEsc + '" alt="" draggable="false">';
  var arrows = _allItems.length > 1
    ? '<button class="fs-arrow fs-prev" onclick="fsNav(-1)" aria-label="Previous">‹</button><button class="fs-arrow fs-next" onclick="fsNav(1)" aria-label="Next">›</button>'
    : '';
  m.innerHTML = '<div class="fs-wrap">' + media + '</div>' + arrows;
  m.classList.add('show');
  _fsScale = 1; _fsTx = 0; _fsTy = 0;
  _bindFSControls();
}

function _bindFSControls() {
  var wrap = document.querySelector('#fs-modal .fs-wrap');
  var img = wrap ? wrap.querySelector('img') : null;
  if (!wrap) return;
  var dragState = null;
  var moved = false;
  var baseW = img ? img.offsetWidth || window.innerWidth : window.innerWidth;
  var baseH = img ? img.offsetHeight || window.innerHeight : window.innerHeight;

  function _clamp() {
    var vw = window.innerWidth;
    var vh = window.innerHeight;
    var maxX = Math.max(0, (baseW * _fsScale - vw) / 2);
    var maxY = Math.max(0, (baseH * _fsScale - vh) / 2);
    _fsTx = Math.max(-maxX, Math.min(maxX, _fsTx));
    _fsTy = Math.max(-maxY, Math.min(maxY, _fsTy));
  }

  wrap.addEventListener('mousedown', function(e) {
    if (e.target.tagName === 'VIDEO' || e.button !== 0) return;
    if (_fsScale > 1) {
      dragState = { x: e.clientX, y: e.clientY, tx: _fsTx, ty: _fsTy };
      moved = false;
      wrap.classList.add('grabbing');
      if (img) img.style.transition = 'none';
      e.preventDefault();
    }
  });
  window.addEventListener('mousemove', function(e) {
    if (!dragState) return;
    var dx = e.clientX - dragState.x;
    var dy = e.clientY - dragState.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) moved = true;
    _fsTx = dragState.tx + dx;
    _fsTy = dragState.ty + dy;
    _clamp();
    _applyFSView(false);
  });
  window.addEventListener('mouseup', function() {
    if (dragState) {
      wrap.classList.remove('grabbing');
      if (_fsScale > 1 && img) img.style.transition = 'transform 160ms cubic-bezier(0.32,0.72,0,1)';
      dragState = null;
    }
  });

  // click: instant zoom toggle on image, close on blank backdrop (no delay)
  wrap.addEventListener('click', function(e) {
    if (e.target.tagName === 'VIDEO') return;
    if (dragState || moved) return;
    if (e.target === img) {
      if (_fsScale > 1) _setFSZoom(1);
      else _setFSZoom(2.5);
    } else {
      closeFS();
    }
  });

  if (img) {
    img.addEventListener('wheel', function(e) {
      e.preventDefault();
      var prev = _fsScale;
      var factor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
      var next = Math.max(1, Math.min(10, prev * factor));
      if (next > 1) {
        var rect = wrap.getBoundingClientRect();
        var px = (e.clientX - rect.left) / rect.width;
        var py = (e.clientY - rect.top) / rect.height;
        var k = next / prev;
        _fsTx = px * rect.width - k * (px * rect.width - _fsTx);
        _fsTy = py * rect.height - k * (py * rect.height - _fsTy);
        _fsScale = next;
        _clamp();
        _applyFSView(true);
      } else {
        _setFSZoom(1);
      }
      e.stopPropagation();
    }, { passive: false });
  }
  [...document.querySelectorAll('.fs-arrow')].forEach(function(b) {
    b.addEventListener('click', function(e) { e.stopPropagation(); });
  });
  // keyboard: Esc closes, arrows navigate
  document.addEventListener('keydown', _fsKeyHandler);
}

function _setFSZoom(scale) {
  _fsScale = (scale > 1) ? scale : 1;
  var img = document.querySelector('#fs-modal .fs-wrap img');
  if (_fsScale <= 1) { _fsTx = 0; _fsTy = 0; }
  else if (img) {
    var baseW = img.offsetWidth || window.innerWidth;
    var baseH = img.offsetHeight || window.innerHeight;
    var maxX = Math.max(0, (baseW * _fsScale - window.innerWidth) / 2);
    var maxY = Math.max(0, (baseH * _fsScale - window.innerHeight) / 2);
    _fsTx = Math.max(-maxX, Math.min(maxX, _fsTx));
    _fsTy = Math.max(-maxY, Math.min(maxY, _fsTy));
  }
  _applyFSView(true);
  var wrap = document.querySelector('#fs-modal .fs-wrap');
  if (wrap) wrap.classList.toggle('zoomed', _fsScale > 1);
}

var _fsDragged = false;
function _applyFSView(animate) {
  var img = document.querySelector('#fs-modal .fs-wrap img');
  if (!img) return;
  img.style.transform = 'translate(' + _fsTx + 'px,' + _fsTy + 'px) scale(' + _fsScale + ')';
}

function _fsKeyHandler(e) {
  var m = document.getElementById('fs-modal');
  if (!m || !m.classList.contains('show')) return;
  if (e.key === 'Escape') { closeFS(); }
  else if (e.key === 'ArrowRight') { fsNav(1); }
  else if (e.key === 'ArrowLeft') { fsNav(-1); }
}

function fsNav(dir) {
  var n = _allItems.length;
  if (!n) return;
  _fsIndex = (_fsIndex + dir + n) % n;
  _renderFS();
}

function closeFS() {
  var m = document.getElementById('fs-modal');
  if (m) { m.classList.remove('show'); m.innerHTML = ''; }
  document.removeEventListener('keydown', _fsKeyHandler);
}

// Hover preview (table + grid mode)
function bindHoverPreview() {
  // delegated via inline handlers (showHover/moveHover/hideHover)
}
function _getHover() {
  var hp = document.getElementById('hover-preview');
  if (!hp) {
    hp = document.createElement('div');
    hp.id = 'hover-preview';
    document.body.appendChild(hp);
  }
  return hp;
}
function showHover(el) {
  var media = el.querySelector('img, video');
  if (!media) return;
  var hp = _getHover();
  var src = media.getAttribute('src');
  var isVideo = media.tagName === 'VIDEO';
  var out = isVideo
    ? '<video src="' + src + '" muted autoplay loop preload="auto"></video>'
    : '<img src="' + src + '" alt="">';
  hp.innerHTML = out;
  hp.style.display = 'block';
  // position directly beside the media thumbnail (right side, vertically centered)
  var r = el.getBoundingClientRect();
  var w = hp.offsetWidth || 220;
  var h = hp.offsetHeight || 392;
  var x = r.right + 12;
  var y = r.top + r.height / 2 - h / 2;
  if (x + w > window.innerWidth - 8) x = Math.max(8, r.left - w - 12);
  x = Math.max(8, x);
  y = Math.max(8, Math.min(y, window.innerHeight - h - 8));
  hp.style.left = x + 'px';
  hp.style.top = y + 'px';
  hp.dataset.video = isVideo ? '1' : '0';
}
function hideHover() {
  var hp = _getHover();
  hp.style.display = 'none';
  var v = hp.querySelector('video');
  if (v) { v.pause(); v.currentTime = 0; }
  hp.innerHTML = '';
}

// Actions
function copyCaptionText(src) {
  editCaption('', src);
}

function downloadMedia(src) {
  var a = document.createElement('a');
  a.href = '/' + src;
  a.download = src.split('/').pop();
  a.click();
}

async function deleteMedia(src, event) {
  if (event) event.stopPropagation();
  if (!confirm('Delete this media file?')) return;
  var r = await api('/api/media/delete', {src: src});
  if (r && r.ok) {
    showSuccess('Deleted');
    refreshOutputs();
  } else {
    showError((r && r.error) || 'Delete failed');
  }
}

// Edit caption modal
var _editSrc = null;
var _editSid = null;
function _findItemBySrc(src) {
  var found = null;
  _outputsData.forEach(function(b) {
    if (found) return;
    b.items.forEach(function(x) { if (x.src === src) found = x; });
  });
  return found;
}
async function editCaption(sid, src) {
  _editSrc = src;
  _editSid = sid;
  var txt = document.getElementById('edit-text');
  if (txt) {
    var it = _findItemBySrc(src);
    txt.value = (it && it.txt_content) ? it.txt_content : '';
  }
  var m = document.getElementById('edit-modal');
  if (m) m.classList.add('show');
  if (txt) setTimeout(function() { txt.focus(); }, 50);
}

function closeEdit() {
  var m = document.getElementById('edit-modal');
  if (m) m.classList.remove('show');
}

async function saveEdit() {
  var txt = document.getElementById('edit-text');
  if (!_editSrc) { closeEdit(); return; }
  var text = txt ? txt.value : '';
  var r = await api('/api/caption/edit', {src: _editSrc, text: text});
  if (r && r.ok) {
    showSuccess('Caption saved');
    closeEdit();
    refreshOutputs();
  } else {
    showError((r && r.error) || 'Save failed');
  }
}

// Prompt modal
var _promptSrc = null;
function _parsePromptSections(it) {
  var full = it.prompt || '';
  var neg = it.negative_prompt || '';
  var identity = '';
  var main = full;
  var marker = '\nnegative prompt: ';
  var idx = full.indexOf(marker);
  if (idx !== -1) {
    main = full.slice(0, idx);
    var rest = full.slice(idx + marker.length);
    var nl = rest.indexOf('\n');
    if (nl !== -1) {
      var embeddedNeg = rest.slice(0, nl);
      identity = rest.slice(nl + 1);
      if (!neg) neg = embeddedNeg;
    } else {
      if (!neg) neg = rest;
    }
    main = main.replace(/\s+$/, '');
  } else if (!neg) {
    // single-line fallback: some prompts inline "negative prompt: ..."
    var m2 = /(?:^|\n)\s*negative prompt:\s*(.*)$/i.exec(full);
    if (m2 && m2[1]) { neg = m2[1]; main = full.slice(0, m2.index).replace(/\s+$/, ''); }
  }
  return { main: main, neg: neg, identity: identity };
}
function showPrompt(src) {
  var it = _findItemBySrc(src);
  if (!it) { showError('Prompt not found'); return; }
  var m = document.getElementById('prompt-modal');
  if (!m) return;
  var s = _parsePromptSections(it);
  document.getElementById('prompt-main').textContent = s.main || '(none)';
  document.getElementById('prompt-negative').textContent = s.neg || '(none)';
  document.getElementById('prompt-identity').textContent = s.identity || '(none)';
  m.classList.add('show');
}
function closePrompt() {
  var m = document.getElementById('prompt-modal');
  if (m) m.classList.remove('show');
}
async function copyPrompt() {
  var t = document.getElementById('prompt-main');
  if (t) navigator.clipboard.writeText(t.textContent).then(function() { showSuccess('Prompt copied'); });
}

// ESC handlers for modals
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    closeFS();
    var m = document.getElementById('edit-modal');
    if (m && m.classList.contains('show')) closeEdit();
    var pm = document.getElementById('prompt-modal');
    if (pm && pm.classList.contains('show')) closePrompt();
  }
});
