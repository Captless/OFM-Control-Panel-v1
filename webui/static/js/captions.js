// captions.js — caption generator card.
// ── Caption Generator Controls ──

var _captions = [];

function getSelectedCapPlatform() {
    var radios = document.querySelectorAll('input[name="cap_platform"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "tiktok";
}

function getSelectedCapHook() {
    var radios = document.querySelectorAll('input[name="cap_hook"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "vulnerable";
}

async function generateCaptions() {
    var btn = document.getElementById('btn-caption');
    var txt = btn ? btn.querySelector('.btn-text') : null;
    var countEl = document.getElementById('cap-count');
    var count = countEl ? parseInt(countEl.value, 10) : 5;
    if (isNaN(count) || count < 1) count = 5;
    if (count > 20) count = 20;
    var platform = getSelectedCapPlatform();
    var hook = getSelectedCapHook();
    var body = { count: count, platform: platform };
    if (hook !== 'mixed') body.hook_types = [hook];
    if (btn) btn.disabled = true;
    if (txt) txt.textContent = 'Generating...';
    var r = await api('/api/captions/generate', body);
    if (btn) btn.disabled = false;
    if (txt) txt.textContent = 'Generate Captions';
    if (r && r.ok && Array.isArray(r.captions)) {
        renderCaptions(r.captions);
        var ca = document.getElementById('btn-copy-all');
        var cl = document.getElementById('btn-clear-caps');
        if (ca) ca.style.display = '';
        if (cl) cl.style.display = '';
        showSuccess('Generated ' + r.captions.length + ' captions');
    } else {
        showError((r && r.output) ? r.output : 'Failed to generate captions');
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
            + '<span class="cap-badge">' + esc(c.platform || '') + '</span>'
            + '<span class="cap-badge">' + esc(c.hook_type || '') + '</span>'
            + '</div>'
            + '<pre class="caption-text-raw">' + esc(c.text || '') + '</pre>'
            + '<div class="caption-meta">' + (c.cta ? esc(c.cta) : '') + (tags ? ' ' + tags : '') + '</div>'
            + '<button class="btn btn-sm btn-outline" onclick="copyCaption(' + i + ')">Copy</button>'
            + '</div>';
    }
    list.innerHTML = html;
}

function copyCaption(idx) {
    if (!_captions || !_captions[idx]) return;
    navigator.clipboard.writeText(_captions[idx].text).then(function() {
        showSuccess('Caption copied');
    }).catch(function() {
        showError('Copy failed');
    });
}

async function copyAllCaptions() {
    if (!_captions || !_captions.length) return;
    var all = _captions.map(function(c) { return c.text; }).join('\n\n');
    try {
        await navigator.clipboard.writeText(all);
        showSuccess(_captions.length + ' captions copied');
    } catch (e) {
        showError('Copy failed');
    }
}

function clearCaptions() {
    _captions = [];
    var list = document.getElementById('caption-list');
    if (list) {
        list.innerHTML = '<div class="caption-empty">No captions yet. Pick a platform and hook type, then click Generate Captions.</div>';
    }
    var ca = document.getElementById('btn-copy-all');
    var cl = document.getElementById('btn-clear-caps');
    if (ca) ca.style.display = 'none';
    if (cl) cl.style.display = 'none';
    showToast('Cleared');
}
