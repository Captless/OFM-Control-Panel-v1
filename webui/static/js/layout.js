// layout.js — Mode switching + radial workflow step navigation.

var _activeMode = 'generate';
var _currentStep = 'configure';

function switchMode(mode) {
  _activeMode = mode;
  // Update nav
  document.querySelectorAll('.hud-mode').forEach(function(b) {
    b.classList.toggle('active', b.dataset.mode === mode);
  });
  // Show/hide mode views
  document.querySelectorAll('.mode-view').forEach(function(v) {
    v.hidden = v.id !== 'mode-' + mode;
  });
}

// ── Step navigation ──
var _STEP_ORDER = ['configure', 'preview', 'generate', 'results'];

function goToStep(step) {
  // Only allow jumping to earlier steps (or results)
  var idx = _STEP_ORDER.indexOf(step);
  var curIdx = _STEP_ORDER.indexOf(_currentStep);
  if (idx === -1 || idx > curIdx) return;
  _currentStep = step;
  _renderSteps();
  _showPanel(step);
}

function _renderSteps() {
  var nodes = document.querySelectorAll('.step-node');
  var lines = document.querySelectorAll('.step-line');
  var curIdx = _STEP_ORDER.indexOf(_currentStep);
  nodes.forEach(function(n) {
    var idx = _STEP_ORDER.indexOf(n.dataset.step);
    n.classList.toggle('active', idx === curIdx);
    n.classList.toggle('done', idx < curIdx);
  });
  lines.forEach(function(l) {
    l.classList.toggle('done', true); // simplified: all lines before active done handled below
  });
  // lines done = up to before active
  var lineNodes = document.querySelectorAll('.step-line');
  lineNodes.forEach(function(l, i) {
    l.classList.toggle('done', i <= curIdx - 1);
  });
}

function _showPanel(step) {
  var panels = document.querySelectorAll('.stage-panel');
  panels.forEach(function(p) {
    p.classList.toggle('active', p.id === 'panel-' + step);
  });
  // Scroll stage into view
  var stage = document.getElementById('stage');
  var main = document.getElementById('main-content');
  if (main && window.scrollY > 60) main.scrollIntoView({ behavior: 'smooth' });
}

function resetWorkflow() {
  _currentStep = 'configure';
  _renderSteps();
  _showPanel('configure');
  // Reset generate controls
  try {
    var s = document.getElementById('photo-count');
    if (s) s.value = '1';
    var l = document.getElementById('photo-count-label');
    if (l) l.textContent = '1';
  } catch(e) {}
  cancelGeneration();
}

// ESC/outside-click for modals handled per-module
// Mode persistence not needed for SPA