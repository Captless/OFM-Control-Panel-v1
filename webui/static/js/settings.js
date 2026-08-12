// settings.js — identity + avatar settings.
var _pendingAvatarUrl = '';

function _setSettingsStatus(msg, type) {
    var el = document.getElementById('settings-status');
    if (!el) return;
    if (!msg) { el.textContent = ''; el.className = 'settings-status'; return; }
    el.textContent = msg;
    el.className = 'settings-status' + (type ? ' ' + type : '');
}

async function loadSettings() {
    var r = await api('/api/settings/identity');
    if (!r || !r.ok) { _setSettingsStatus('Failed to load settings', 'error'); return; }
    var identity = r.identity || {};
    var name = document.getElementById('settings-identity-name');
    if (name) name.textContent = identity.name || 'Unnamed identity';
    var preview = document.getElementById('settings-avatar-preview');
    if (preview) {
        if (identity.avatar_url) {
            preview.src = identity.avatar_url;
            preview.style.display = 'block';
        } else {
            preview.removeAttribute('src');
            preview.style.display = 'none';
        }
    }
    var urlInput = document.getElementById('settings-avatar-url');
    if (urlInput) {
        urlInput.value = identity.avatar_url || '';
        urlInput.placeholder = identity.avatar_url ? '' : 'https://\u2026';
    }
    await loadBankEditor();
}
function loadAvatarUrl() {
    var input = document.getElementById('settings-avatar-url');
    var url = (input.value || '').trim();
    if (!url) { _setSettingsStatus('Enter an image URL first', 'error'); return; }
    if (!/^https?:\/\//i.test(url)) {
        _setSettingsStatus('Must be a public http(s) URL (local paths won\u2019t reach WaveSpeed)', 'error');
        return;
    }
    _pendingAvatarUrl = url;
    var preview = document.getElementById('settings-new-preview');
    preview.onerror = function() {
        _setSettingsStatus('Could not load image from that URL', 'error');
        preview.style.display = 'none';
    };
    preview.onload = function() {
        preview.style.display = 'block';
        _setSettingsStatus('Ready to save', 'ok');
    };
    preview.style.display = 'block';
    _setSettingsStatus('Loading image\u2026', '');
    preview.src = url + (url.indexOf('?') === -1 ? '?' : '&') + '_t=' + Date.now();
}

async function handleAvatarFile(file) {
    if (!file) return;
    if (!file.type || file.type.indexOf('image/') !== 0) {
        _setSettingsStatus('Invalid file type: images only', 'error');
        return;
    }
    if (file.size > 5 * 1024 * 1024) {
        _setSettingsStatus('File too large: max 5MB', 'error');
        return;
    }
    var zone = document.getElementById('settings-upload-zone');
    if (zone) zone.classList.remove('drag-over');
    _setSettingsStatus('Uploading\u2026', '');
    var fd = new FormData();
    fd.append('file', file);
    try {
        var resp = await fetch('/api/settings/identity/upload', { method: 'POST', body: fd });
        var data = await resp.json();
        if (!data.ok) {
            _setSettingsStatus(data.error || 'Upload failed', 'error');
            return;
        }
        _pendingAvatarUrl = data.avatar_url || data.url;
        var preview = document.getElementById('settings-new-preview');
        preview.onerror = null;
        preview.onload = function() { preview.style.display = 'block'; };
        preview.style.display = 'block';
        preview.src = data.url + (data.url.indexOf('?') === -1 ? '?' : '&') + '_t=' + Date.now();
        if (data.uploaded) {
            _setSettingsStatus('Uploaded \u2014 public WaveSpeed URL ready. Save to apply.', 'ok');
        } else {
            _setSettingsStatus('Saved locally. ' + (data.warning || 'Paste a public URL for generation.'), 'error');
        }
    } catch(e) {
        _setSettingsStatus('Upload error: ' + e.message, 'error');
    }
}

async function saveIdentity() {
    if (!_pendingAvatarUrl) { _setSettingsStatus('Load or upload an image first.', 'error'); return; }
    var r = await api('/api/settings/identity', { avatar_url: _pendingAvatarUrl });
    if (r && r.ok) {
        var newPreview = document.getElementById('settings-new-preview');
        if (newPreview) { newPreview.style.display = 'none'; newPreview.removeAttribute('src'); }
        var input = document.getElementById('settings-file-input');
        if (input) input.value = '';
        _pendingAvatarUrl = '';
        showSuccess('Identity saved');
        loadSettings();
    } else {
        _setSettingsStatus((r && (r.error || r.output)) || 'Failed to save identity', 'error');
    }
}


document.addEventListener('DOMContentLoaded', function() {
    var fileInput = document.getElementById('settings-file-input');
    var zone = document.getElementById('settings-upload-zone');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            handleAvatarFile(fileInput.files[0]);
        });
    }
    if (zone) {
        zone.addEventListener('click', function() { if (fileInput) fileInput.click(); });
        zone.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); if (fileInput) fileInput.click(); }
        });
        zone.addEventListener('dragover', function(e) {
            e.preventDefault();
            zone.classList.add('drag-over');
        });
        zone.addEventListener('dragleave', function() {
            zone.classList.remove('drag-over');
        });
        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            zone.classList.remove('drag-over');
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
                handleAvatarFile(e.dataTransfer.files[0]);
            }
        });
    }
});
