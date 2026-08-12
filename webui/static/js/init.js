// init.js — app boot. Load last.
// ── Init ──
document.addEventListener('DOMContentLoaded', function() {
    try {
        setLive('loading', 'Starting...');
        fetchBalance();
        refreshOutputs();
        syncViewToggle();
        
        checkApiStatus();
        preloadAccounts();
        preloadValidation();
        loadActiveBank();
        setInterval(checkApiStatus, 30000);
        setInterval(fetchBalance, 60000);

        // Close modal on backdrop click
        var apiModal = document.getElementById('api-modal');
        if (apiModal) {
            apiModal.addEventListener('click', function(e) {
                if (e.target === apiModal) {
                    closeApiModal();
                }
            });
        }
        
        // Close modal on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                var apiModal = document.getElementById('api-modal');
                if (apiModal && apiModal.classList.contains('show')) {
                    closeApiModal();
                }
            }
        });
    } catch(e) {}
});
