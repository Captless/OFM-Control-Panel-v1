// init.js — app boot. Load last.

document.addEventListener('DOMContentLoaded', function() {
  try {
    initTheme();
    setLive('loading', 'Starting…');
    fetchBalance();
    refreshOutputs();
    syncViewToggle();
    loadSettings();
    loadBankEditor();
    checkApiStatus();
    preloadAccounts();
    preloadValidation();
    _currentStep = 'configure';
    _renderSteps();
    _showPanel('configure');

    setInterval(checkApiStatus, 30000);
    setInterval(fetchBalance, 60000);

    // Close modals on backdrop click
    document.querySelectorAll('.modal').forEach(function(m) {
      m.addEventListener('click', function(e) {
        if (e.target === m) m.classList.remove('show');
      });
    });
  } catch(e) {
    console.error('init error:', e);
  }
});