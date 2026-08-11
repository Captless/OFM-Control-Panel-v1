// generation.js — photo controls, balance/cost, prompt preview, run pipeline.
// ── Photo Generation Controls ──

function getSelectedVibe() {
    var radios = document.querySelectorAll('input[name="vibe"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "indoor";
}

function getSelectedCamera() {
    var radios = document.querySelectorAll('input[name="camera_style"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "handheld";
}

function getSelectedLighting() {
    var radios = document.querySelectorAll('input[name="lighting"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "warm";
}

function getSelectedTime() {
    var radios = document.querySelectorAll('input[name="time_of_day"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "day";
}

function getSelectedOutfitStyle() {
    var radios = document.querySelectorAll('input[name="outfit_style"]');
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) return radios[i].value;
    }
    return "any";
}
function onVibeChange() {
    updateCost();
}

function onCameraChange() {
    var camera = getSelectedCamera();
    var vibe = getSelectedVibe();
    var outdoorPill = document.querySelector('input[name="vibe"][value="outdoor"]');
    if (camera === "mirror" && vibe === "outdoor") {
        // Auto-switch to "indoor" when mirror + outdoor conflict
        var indoorPill = document.querySelector('input[name="vibe"][value="indoor"]');
        if (indoorPill) indoorPill.checked = true;
    }
    // Grey out/outdoor pill when mirror is selected
    if (outdoorPill) {
        outdoorPill.disabled = (camera === "mirror");
        if (camera === "mirror") {
            outdoorPill.parentElement.style.opacity = "0.4";
            outdoorPill.parentElement.style.pointerEvents = "none";
        } else {
            outdoorPill.parentElement.style.opacity = "1";
            outdoorPill.parentElement.style.pointerEvents = "auto";
        }
    }
    updateCost();
}
var _balance = 0;
var _perPhoto = 0.07;
var _pendingJobs = null;

async function fetchBalance() {
    var data = await api('/api/balance');
    if (data && typeof data.balance === 'number') {
        _balance = data.balance;
        _perPhoto = data.per_photo || 0.07;
    }
    var bpActive = document.getElementById('bp-active');
    if (bpActive) bpActive.textContent = '$' + _balance.toFixed(2);
    try {
        var r = await fetch('/api/balance/total');
        var totalData = await r.json();
        var bpTotal = document.getElementById('bp-total');
        if (bpTotal && typeof totalData.total === 'number') {
            bpTotal.textContent = '$' + totalData.total.toFixed(2) + ' total';
        }
    } catch(e) {
        console.error('fetchBalance total error:', e);
    }
    var slider = document.getElementById('photo-count');
    var label = document.getElementById('photo-count-label');
    if (slider && _perPhoto > 0) {
        var maxCount = Math.min(Math.floor(_balance / _perPhoto), 30);
        slider.max = Math.max(maxCount, 1);
        if (parseInt(slider.value) > maxCount) {
            slider.value = maxCount;
            if (label) label.textContent = maxCount;
        }
    }
    updateCost();
}

async function refreshBalance() {
    var btn = document.getElementById('bp-refresh');
    if (btn) btn.classList.add('spin');
    await fetchBalance();
    if (btn) setTimeout(function() { btn.classList.remove('spin'); }, 500);
}

function updateCost() {
    var count = parseInt(document.getElementById('photo-count').value) || 0;
    var total = (count * _perPhoto).toFixed(2);
    var el = document.getElementById('cost-tracker');
    if (!el) return;
    el.textContent = '$' + total + ' · $' + _balance.toFixed(2);
    schedulePreviewRefresh();
}

function _btnTxt(t) { var e = document.querySelector('#btn-photo .btn-text'); if (e) e.textContent = t; }
var _statusBadge = {
    'submitting': 'Queued', 'created': 'Queued', 'queued': 'Queued',
    'processing': 'Processing', 'completed': 'Done', 'saved': 'Saved',
    'enhancing': 'Enhancing', 'failed': 'Error', 'cancelled': 'Cancelled',
    'timeout': 'Timed out'
};
function _renderGenStatus(images) {
    var strip = document.getElementById('gen-status-strip');
    if (!strip) return;
    if (!images || !Object.keys(images).length) { strip.style.display = 'none'; strip.innerHTML = ''; return; }
    strip.style.display = 'block';
    var html = '';
    Object.keys(images).forEach(function(k) {
        var im = images[k];
        var cls = 'gs-' + (im.status || 'processing');
        var label = _statusBadge[im.status] || im.status;
        var showDetail = im.status === 'failed' || im.status === 'cancelled' || im.status === 'timeout';
        var detail = (showDetail && im.detail) ? ' <span class="gs-detail">' + esc(im.detail) + '</span>' : '';
        html += '<div class="gs-row ' + cls + '"><span class="gs-badge">' + esc(label) + '</span><span class="gs-elapsed">' + im.elapsed + 's</span>' + detail + '</div>';
    });
    strip.innerHTML = html;
}
function _startGenAnim() {
    var dots = 1;
    clearInterval(_genAnimTimer);
    _genAnimTimer = setInterval(function() {
        dots = (dots % 3) + 1;
        _btnTxt('Generating' + new Array(dots + 1).join('.'));
    }, 500);
    _btnTxt('Generating.');
}

function _resetBtn() { var btn = document.getElementById('btn-photo'); if (btn) { btn.classList.remove('loading'); btn.disabled = false; } _btnTxt('Generate'); setControlsLocked(false); clearInterval(_genAnimTimer); var strip = document.getElementById('gen-status-strip'); if (strip) { strip.style.display = 'none'; strip.innerHTML = ''; } }

function setControlsLocked(locked) {
    var card = document.querySelector('.gen-layout .card');
    if (!card) return;
    card.classList.toggle('controls-locked', locked);
    var inputs = card.querySelectorAll('input');
    for (var i = 0; i < inputs.length; i++) {
        inputs[i].disabled = locked;
    }
}
var _previewDebounce = null;
var _genAnimTimer = null;
var _previewFetching = false;

async function fetchPromptPreview(silent) {
    var vibe = getSelectedVibe();
    var camera_style = getSelectedCamera();
    var lighting = getSelectedLighting();
    var time_of_day = getSelectedTime();
    var outfit_style = getSelectedOutfitStyle();
    var count = parseInt(document.getElementById('photo-count').value) || 6;
    var r = await api('/api/prompts/generate', {vibe: vibe, camera_style: camera_style, lighting: lighting, time_of_day: time_of_day, outfit_style: outfit_style, count: count, bank_id: getSelectedBankId()});
    if (!r.ok) {
        if (!silent) {
            _btnTxt('FAIL: ' + (r.error || 'error'));
            showError('Prompt build failed: ' + (r.error || 'error'));
            setTimeout(_resetBtn, 3000);
        }
        return null;
    }
    _pendingJobs = r.jobs;
    var list = document.getElementById('prompt-list');
    var html = '';
    for (var i = 0; i < r.jobs.length; i++) {
        var prompt = r.jobs[i].prompt || '';
        html += '<div class="prompt-item" data-idx="' + i + '">';
        html += '<span class="pnum">PROMPT</span>';
        html += '<pre>' + esc(prompt) + '</pre>';
        html += '<textarea>' + prompt + '</textarea>';
        html += '</div>';
    }
    list.innerHTML = html;
    document.getElementById('confirm-gen-btn').style.display = 'inline-block';
    document.getElementById('confirm-gen-btn').disabled = false;
    document.getElementById('cancel-gen-btn').style.display = 'inline-block';
    document.getElementById('edit-prompts-btn').style.display = 'inline-block';
    _btnTxt('Update Preview');
    syncPanelHeights();
    return r.jobs;
}

async function startPromptGeneration() {
    if (_previewFetching) return;
    _previewFetching = true;
    _btnTxt('Generating prompts\u2026');
    await fetchPromptPreview(false);
    _previewFetching = false;
}

function schedulePreviewRefresh() {
    if (!_pendingJobs) return;
    var items = document.querySelectorAll('.prompt-item');
    if (items.length > 0 && items[0].classList.contains('editing')) return;
    clearTimeout(_previewDebounce);
    _previewDebounce = setTimeout(function() { fetchPromptPreview(true); }, 300);
}

function _resetPromptList() {
    document.getElementById('prompt-list').innerHTML = '<div class="prompt-empty">' +
        '<span class="prompt-empty-icon"><svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V4z"/><line x1="2" y1="10" x2="6" y2="10"/><line x1="2" y1="7" x2="5" y2="7"/></svg></span>' +
        '<p>No prompts yet</p>' +
        '<p class="prompt-empty-sub">Select options and click Generate to build prompts for review and editing before confirming generation.</p>' +
        '</div>';
    document.getElementById('confirm-gen-btn').style.display = 'none';
    document.getElementById('cancel-gen-btn').style.display = 'none';
    document.getElementById('edit-prompts-btn').style.display = 'none';
    document.getElementById('edit-prompts-btn').textContent = 'Edit';
    document.getElementById('confirm-gen-btn').disabled = false;
    syncPanelHeights();
}

async function confirmGeneration() {
    var btn = document.getElementById('btn-photo');
    var items = document.querySelectorAll('.prompt-item');
    var jobs = [];
    for (var i = 0; i < items.length; i++) {
        var ta = items[i].querySelector('textarea');
        var prompt = ta ? ta.value : '';
        if (prompt.trim()) {
            var orig = _pendingJobs && _pendingJobs[i] ? _pendingJobs[i] : {};
            jobs.push({
                prompt: prompt,
                filename: orig.filename || String(i + 1).padStart(3, '0') + '_' + Date.now().toString(36) + '.png'
            });
        }
    }
    if (!jobs.length) return;
    _resetPromptList();
    setControlsLocked(true);
    btn.disabled = true;
    btn.classList.add('loading'); _startGenAnim();
    var r2 = await api('/api/run/photo', {prompts: jobs});
    if (!r2.ok) {
        _btnTxt('FAIL: ' + (r2.output || 'error'));
        clearInterval(_genAnimTimer);
        showError('Failed to start generation: ' + (r2.output || 'error'));
        fetchBalance();
        setTimeout(_resetBtn, 3000);
        return;
    }
    var runId = r2.run_id;
    var _lastDetail = '';
    var _lastChangeTime = Date.now();
    var _retryCount = 0;
    var _maxRetries = 3;
    var _deadline = Date.now() + 45 * 60 * 1000;
var _fail = function(msg) {
        btn.classList.remove('loading');
        clearInterval(_genAnimTimer);
        _btnTxt(msg);
        fetchBalance();
        setTimeout(_resetBtn, 3000);
    };

    var _stageMap = {
        'submitting': 'Submitting',
        'generating': 'Generating',
        'polling': 'Processing',
        'downloading': 'Downloading',
        'enhancing': 'Enhancing',
        'complete': 'Complete'
    };
    var _friendlyStage = function(stage) {
        return _stageMap[stage] || (stage ? stage.charAt(0).toUpperCase() + stage.slice(1) : 'Running');
    };

    while (Date.now() < _deadline) {
        var p = await api('/api/progress?run_id=' + runId);
        if (p && p.done === true) {
            _renderGenStatus(p.images);
            if (p.error_type === 'explicit_content') {
                var flagMsg = '';
                if (p.images) {
                    Object.keys(p.images).forEach(function(k) {
                        var im = p.images[k];
                        if (im.status === 'failed' && im.detail) { flagMsg = im.detail; }
                    });
                }
                _btnTxt('FAIL: content flagged');
                showWarning('Generation blocked \u2014 WaveSpeed flagged content as sensitive' + (flagMsg ? ': ' + flagMsg : '') + '. Try different prompts or outfit style.', 8000);
            } else if (p.ok) {
                _btnTxt('OK (' + p.duration_s + 's)');
                refreshOutputs(); showSuccess('Generation complete \u2014 ' + p.duration_s + 's');
            } else {
                _btnTxt('FAIL: ' + (p.detail || 'error'));
                showError('Generation failed: ' + (p.detail || 'error'));
            }
            clearInterval(_genAnimTimer);
            fetchBalance();
            setTimeout(_resetBtn, 3000);
            _pendingJobs = null;
            _resetPromptList();
            break;        }
        if (!p || p.error || typeof p.done !== 'boolean') {
            _fail('FAIL: run not found (server restarted?)');
            _pendingJobs = null;
            _resetPromptList();
            break;
        }
        var stage = p.stage ? _friendlyStage(p.stage) : 'Running';
        var detail = stage + (p.detail ? ': ' + p.detail : '');
        if (p.total > 0) detail += ' (' + p.current + '/' + p.total + ')';
        if (detail !== _lastDetail) {
            _lastDetail = detail;
            _lastChangeTime = Date.now();
        }
        var updatedAt = (typeof p.updated_at === 'number') ? p.updated_at : (_lastChangeTime / 1000);
        var elapsed = Math.floor(Date.now() / 1000 - updatedAt);
        if (elapsed >= 300 && _retryCount < _maxRetries) {
            _retryCount++;
            _btnTxt('Reconnecting\u2026');
            var r3 = await api('/api/run/photo', {prompts: jobs});
            if (r3.ok) {
                runId = r3.run_id;
                _lastDetail = '';
                _lastChangeTime = Date.now();
                continue;
            } else {
                _fail('FAIL: retry ' + _retryCount + ' failed');
                _pendingJobs = null;
                _resetPromptList();
                break;
            }
        }
        if (elapsed >= 300) {
            _fail('FAIL: generation stalled');
            _pendingJobs = null;
            _resetPromptList();
            break;
        }
        _renderGenStatus(p.images);
        var btnText = 'Generating...';
        if (p.total > 0) btnText = 'Generating ' + p.current + '/' + p.total;
        _btnTxt(btnText);
        await new Promise(r3 => setTimeout(r3, 1000));
    }
    if (Date.now() >= _deadline) {
        _fail('FAIL: timed out after 45 min');
        _pendingJobs = null;
        _resetPromptList();
    }
}

function toggleEditPrompts() {
    var items = document.querySelectorAll('.prompt-item');
    var btn = document.getElementById('edit-prompts-btn');
    var confirmBtn = document.getElementById('confirm-gen-btn');
    var editing = items.length > 0 && items[0].classList.contains('editing');
    if (editing) {
        for (var i = 0; i < items.length; i++) {
            var pre = items[i].querySelector('pre');
            var ta = items[i].querySelector('textarea');
            if (pre && ta) pre.textContent = ta.value;
        }
    }
    for (var i = 0; i < items.length; i++) {
        items[i].classList.toggle('editing', !editing);
    }
    confirmBtn.disabled = !editing;
    btn.textContent = editing ? 'Edit' : 'Confirm';
}

function cancelGeneration() {
    _resetPromptList();
    _pendingJobs = null;
    _btnTxt('Generate');
}
