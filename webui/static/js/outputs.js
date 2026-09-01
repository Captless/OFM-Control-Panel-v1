// outputs.js — outputs rendering, actions, fullscreen viewer.
// ── Outputs table ──
var _outputsData = [];


var _preview = null;
var _viewMode = 'table';
try { _viewMode = localStorage.getItem('ofm_view_mode') || 'table'; } catch(e) {}
var _showAll = false;
try { _showAll = localStorage.getItem('ofm_show_all') === '1'; } catch(e) {}

function setShowAll() {
    _showAll = !_showAll;
    try { localStorage.setItem('ofm_show_all', _showAll ? '1' : '0'); } catch(e) {}
    syncViewToggle();
    var area = document.getElementById('outputs-area');
    if (area) renderOutputs();
}

function setViewMode(mode) {
    _viewMode = (mode === 'grid') ? 'grid' : 'table';
    try { localStorage.setItem('ofm_view_mode', _viewMode); } catch(e) {}
    syncViewToggle();
    var area = document.getElementById('outputs-area');
    if (area) renderOutputs();
}

function syncViewToggle() {
    document.querySelectorAll('.view-toggle button[data-view]').forEach(function(b) {
        var on = b.dataset.view === _viewMode;
        b.classList.toggle('active', on);
        b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    var sa = document.getElementById('btn-show-all');
    if (sa) {
        sa.classList.toggle('active', _showAll);
        sa.setAttribute('aria-checked', _showAll ? 'true' : 'false');
    }
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
    if (_viewMode === 'grid') { area.innerHTML = _showAll ? buildFlatGridHtml(batches) : buildGridHtml(batches); }
    else { area.innerHTML = _showAll ? buildFlatHtml(batches) : buildTableHtml(batches); }
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

function buildFlatHtml(batches) {
    var html = '';
    var num = 0;
    batches.forEach(function(b, bIdx) {
        var bid = b.id;
        b.items.forEach(function(item, iIdx) {
            var sid = bid + '_' + item.stem;
            num++;
            html += '<tr class="flat-row">';
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
            if (item.txt_content) html += '<div class="txt" id="' + sid + '_t">' + esc(item.txt_content) + '</div>';
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
    });
    if (html) return '<div class="b flat"><div class="b-body"><table class="tw"><tbody>' + html + '</tbody></table></div></div>';
    return '';
}

function buildFlatGridHtml(batches) {
    var html = '';
    batches.forEach(function(b) {
        var bid = b.id;
        b.items.forEach(function(item) {
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
    });
    if (html) return '<div class="b flat"><div class="b-body"><div class="g-grid">' + html + '</div></div></div>';
    return '';
}

async function refreshOutputs() {
    var r = await api('/api/dashboard/refresh');
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
    if (!_showAll) {
        var part = _fsBatch[_fsIdx].vid.split('_')[0];
        _fsBatch = _fsBatch.filter(function(it) { return it.vid.indexOf(part + '_') === 0; });
        for (var j = 0; j < _fsBatch.length; j++) {
            if (_fsBatch[j].vid === vid) { _fsIdx = j; break; }
        }
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
