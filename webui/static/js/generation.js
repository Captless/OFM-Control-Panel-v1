// generation.js — radial workflow: Configure → Preview → Generate → Results.

function getSelectedVibe() {
  var r = document.querySelector('input[name="vibe"]:checked');
  return r ? r.value : 'indoor';
}
function getSelectedCamera() {
  var r = document.querySelector('input[name="camera_style"]:checked');
  return r ? r.value : 'handheld';
}
function getSelectedLighting() {
  var r = document.querySelector('input[name="lighting"]:checked');
  return r ? r.value : 'warm';
}
function getSelectedTime() {
  var r = document.querySelector('input[name="time_of_day"]:checked');
  return r ? r.value : 'day';
}
function getSelectedTopCategory() {
  var el = document.getElementById('outfit-top');
  return el ? el.value : 'tank';
}
function getSelectedBottomCategory() {
  var el = document.getElementById('outfit-bottom');
  return el ? el.value : 'miniskirt';
}

function onVibeChange() { updateCost(); }

function onCameraChange() {
  var camera = getSelectedCamera();
  var vibe = getSelectedVibe();
  var outdoorPill = document.querySelector('input[name="vibe"][value="outdoor"]');
  if (camera === 'mirror' && vibe === 'outdoor') {
    var indoorPill = document.querySelector('input[name="vibe"][value="indoor"]');
    if (indoorPill) indoorPill.checked = true;
  }
  if (outdoorPill) {
    outdoorPill.disabled = (camera === 'mirror');
    var parent = outdoorPill.closest('.pill');
    if (parent) parent.style.opacity = (camera === 'mirror') ? '0.4' : '1';
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
      bpTotal.textContent = '$' + totalData.total.toFixed(2);
    }
  } catch(e) { console.error('fetchBalance total error:', e); }
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
  try {
    await fetchBalance();
  } finally {
    if (btn) setTimeout(function() { btn.classList.remove('spin'); }, 500);
  }
}

function updateCost() {
  var count = parseInt(document.getElementById('photo-count').value) || 0;
  var total = (count * _perPhoto).toFixed(2);
  var el = document.getElementById('cost-tracker');
  if (el) el.textContent = '$' + total + ' total · ' + _balance.toFixed(2) + ' available';
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
  var prog = document.getElementById('gen-progress-images');
  if (!strip && !prog) return;
  if (!images || !Object.keys(images).length) {
    if (strip) { strip.style.display = 'none'; strip.innerHTML = ''; }
    if (prog) prog.innerHTML = '';
    return;
  }
  var html = '';
  Object.keys(images).forEach(function(k) {
    var im = images[k];
    var cls = 'gs-' + (im.status || 'processing');
    var label = _statusBadge[im.status] || im.status;
    var showDetail = im.status === 'failed' || im.status === 'cancelled' || im.status === 'timeout';
    var detail = (showDetail && im.detail) ? ' <span class="gs-detail">' + esc(im.detail) + '</span>' : '';
    html += '<div class="gs-row ' + cls + '"><span class="gs-badge">' + esc(label) + '</span><span class="gs-elapsed">' + im.elapsed + 's</span>' + detail + '</div>';
  });
  if (strip) { strip.style.display = 'block'; strip.innerHTML = html; }
  if (prog) prog.innerHTML = html;
}

var _genAnimTimer = null;
function _startGenAnim() {
  var dots = 1;
  clearInterval(_genAnimTimer);
  _genAnimTimer = setInterval(function() {
    dots = (dots % 3) + 1;
    _setStepStatus('Generating' + new Array(dots + 1).join('.'));
  }, 500);
  _setStepStatus('Generating.');
}

function _setStepStatus(text) {
  var el = document.getElementById('gen-status-text');
  if (el) el.textContent = text;
}

function _resetBtn() {
  var btn = document.getElementById('btn-photo');
  if (btn) { btn.classList.remove('loading'); btn.disabled = false; }
  _btnTxt('Generate Prompt');
  setControlsLocked(false);
  clearInterval(_genAnimTimer);
  var strip = document.getElementById('gen-status-strip');
  if (strip) { strip.style.display = 'none'; strip.innerHTML = ''; }
}

function setControlsLocked(locked) {
  var config = document.getElementById('panel-configure');
  if (!config) return;
  config.classList.toggle('controls-locked', locked);
  var inputs = config.querySelectorAll('input');
  for (var i = 0; i < inputs.length; i++) inputs[i].disabled = locked;
  var btns = config.querySelectorAll('button');
  for (var b = 0; b < btns.length; b++) btns[b].disabled = locked;
}

var _previewDebounce = null;
var _previewFetching = false;
var _previewStateKey = null;

function _currentPreviewStateKey() {
  return [getSelectedVibe(), getSelectedCamera(), getSelectedLighting(), getSelectedTime(), getSelectedTopCategory(), getSelectedBottomCategory(), document.getElementById('photo-count').value, getSelectedBankId()].join('|');
}

function getSelectedBankId() {
  try {
    return (window.API_BANK_ID && typeof API_BANK_ID === 'function' && API_BANK_ID()) || '';
  } catch(e) { return ''; }
}

async function fetchPromptPreview(silent) {
  var vibe = getSelectedVibe();
  var camera_style = getSelectedCamera();
  var lighting = getSelectedLighting();
  var time_of_day = getSelectedTime();
  var outfit_top = getSelectedTopCategory();
  var outfit_bottom = getSelectedBottomCategory();
  var count = parseInt(document.getElementById('photo-count').value) || 6;
  var r = await api('/api/prompts/generate', {vibe: vibe, camera_style: camera_style, lighting: lighting, time_of_day: time_of_day, top_category: outfit_top, bottom_category: outfit_bottom, count: count, bank_id: getSelectedBankId()});
  if (!r.ok) {
    if (!silent) {
      _btnTxt('FAIL: ' + (r.error || 'error'));
      showError('Prompt build failed: ' + (r.error || 'error'));
      setTimeout(_resetBtn, 3000);
    }
    return null;
  }
  _previewStateKey = _currentPreviewStateKey();
  _pendingJobs = r.jobs;
  var list = document.getElementById('prompt-list');
  var html = '';
  for (var i = 0; i < r.jobs.length; i++) {
    var prompt = r.jobs[i].prompt || '';
    html += '<div class="prompt-item" data-idx="' + i + '">';
    html += '<span class="pnum">PROMPT ' + (i + 1) + '</span>';
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
  return r.jobs;
}

async function startPromptGeneration() {
  if (_previewFetching) return;
  _previewFetching = true;
  _btnTxt('Generating prompt…');
  var jobs = await fetchPromptPreview(false);
  _previewFetching = false;
  if (jobs && jobs.length) {
    _currentStep = 'preview';
    _renderSteps();
    _showPanel('preview');
  }
}

function schedulePreviewRefresh() {
  if (!_pendingJobs) return;
  if (_currentPreviewStateKey() === _previewStateKey) return;
  if (typeof _currentStep === 'string' && _currentStep !== 'configure') return;
  var items = document.querySelectorAll('.prompt-item');
  if (items.length > 0 && items[0].classList.contains('editing')) return;
  clearTimeout(_previewDebounce);
  _previewDebounce = setTimeout(function() { fetchPromptPreview(true); }, 300);
}

function _resetPromptList() {
  document.getElementById('prompt-list').innerHTML = '<div class="empty-state"><p>No prompts yet.</p><p class="empty-hint">Configure your shoot first.</p></div>';
  document.getElementById('confirm-gen-btn').style.display = 'none';
  document.getElementById('cancel-gen-btn').style.display = 'none';
  document.getElementById('edit-prompts-btn').style.display = 'none';
  document.getElementById('edit-prompts-btn').textContent = 'Edit';
  document.getElementById('confirm-gen-btn').disabled = false;
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
  if (!jobs.length) { showError('No prompts to generate'); return; }

  // Enter generate step
  _currentStep = 'generate';
  _renderSteps();
  _showPanel('generate');
  _setStepStatus('Submitting jobs...');
  var ring = _updateProgressRing(0, jobs.length);

  setControlsLocked(true);
  btn.disabled = true;
  btn.classList.add('loading');
  _startGenAnim();

  var r2 = await api('/api/run/photo', {prompts: jobs});
  if (!r2.ok) {
    _setStepStatus('Failed: ' + (r2.output || 'error'));
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
    _setStepStatus(msg);
    fetchBalance();
    setTimeout(function() { _resetBtn(); }, 3000);
  };

  var _stageMap = {
    'submitting': 'Submitting', 'generating': 'Generating', 'polling': 'Processing',
    'downloading': 'Downloading', 'enhancing': 'Enhancing', 'complete': 'Complete'
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
        if (p.images) Object.keys(p.images).forEach(function(k) {
          if (p.images[k].status === 'failed' && p.images[k].detail) flagMsg = p.images[k].detail;
        });
        _setStepStatus('Blocked — content flagged');
        showWarning('Generation blocked — WaveSpeed flagged content as sensitive' + (flagMsg ? ': ' + flagMsg : '') + '. Try different prompts or outfit style.', 8000);
      } else if (p.ok) {
        _setStepStatus('Complete — ' + p.duration_s + 's');
        _updateProgressRing(p.total || 1, p.total || 1, true);
        refreshOutputs();
        showSuccess('Generation complete — ' + p.duration_s + 's');
        // Move to results
        setTimeout(function() {
          _currentStep = 'results';
          _renderSteps();
          _showPanel('results');
        }, 600);
      } else {
        _setStepStatus('Failed: ' + (p.detail || 'error'));
        showError('Generation failed: ' + (p.detail || 'error'));
      }
      clearInterval(_genAnimTimer);
      fetchBalance();
      _pendingJobs = null;
      break;
    }
    if (!p || p.error || typeof p.done !== 'boolean') {
      _fail('FAIL: run not found (server restarted?)');
      _pendingJobs = null;
      break;
    }
    var stage = p.stage ? _friendlyStage(p.stage) : 'Running';
    var detail = stage + (p.detail ? ': ' + p.detail : '');
    if (p.total > 0) detail += ' (' + Math.min(p.current, p.total) + '/' + p.total + ')';
    if (detail !== _lastDetail) { _lastDetail = detail; _lastChangeTime = Date.now(); }
    var updatedAt = (typeof p.updated_at === 'number') ? p.updated_at : (_lastChangeTime / 1000);
    var elapsed = Math.floor(Date.now() / 1000 - updatedAt);
    if (elapsed >= 300 && _retryCount < _maxRetries) {
      _retryCount++;
      _setStepStatus('Reconnecting…');
      var r3 = await api('/api/run/photo', {prompts: jobs});
      if (r3.ok) { runId = r3.run_id; _lastDetail = ''; _lastChangeTime = Date.now(); continue; }
      else { _fail('FAIL: retry ' + _retryCount + ' failed'); _pendingJobs = null; break; }
    }
    if (elapsed >= 300) { _fail('FAIL: generation stalled'); _pendingJobs = null; break; }
    _renderGenStatus(p.images);
    _setStepStatus(detail);
    _updateProgressRing(p.current, p.total);
    await new Promise(rx => setTimeout(rx, 1000));
  }
  if (Date.now() >= _deadline) {
    _fail('FAIL: timed out after 45 min');
    _pendingJobs = null;
  }
}

function _updateProgressRing(current, total, complete) {
  var ring = document.getElementById('progress-ring-fg');
  var label = document.getElementById('progress-ring-label');
  if (!ring) return;
  var circ = 2 * Math.PI * 52; // r=52
  var pct = 0;
  if (total > 0) pct = Math.min((current / total) * 100, 100);
  if (complete) pct = 100;
  ring.style.strokeDashoffset = circ - (circ * pct / 100);
  if (label) label.textContent = Math.round(pct) + '%';
}

function toggleEditPrompts() {
  var items = document.querySelectorAll('.prompt-item');
  var btn = document.getElementById('edit-prompts-btn');
  var confirmBtn = document.getElementById('confirm-gen-btn');
  var editing = items.length > 0 && items[0].classList.contains('editing');
  for (var i = 0; i < items.length; i++) {
    var pre = items[i].querySelector('pre');
    var ta = items[i].querySelector('textarea');
    if (editing) {
      // leaving edit: commit edits back to preview
      if (pre && ta) pre.textContent = ta.value;
      if (ta) ta.style.height = '';
    } else {
      // entering edit: make textarea exactly match preview box height/content
      if (pre && ta) {
        ta.value = pre.textContent;
        ta.style.height = pre.offsetHeight + 'px';
        ta.style.minHeight = pre.offsetHeight + 'px';
      }
    }
  }
  for (var i = 0; i < items.length; i++) items[i].classList.toggle('editing', !editing);
  confirmBtn.disabled = !editing;
  btn.textContent = editing ? 'Edit' : 'Done Editing';
}

function cancelGeneration() {
  _resetPromptList();
  _pendingJobs = null;
  _btnTxt('Generate Prompt');
  if (_currentStep === 'preview') {
    _currentStep = 'configure';
    _renderSteps();
    _showPanel('configure');
  }
}

// Initialize progress ring to 0
try {
  _updateProgressRing(0, 1);
} catch(e) {}