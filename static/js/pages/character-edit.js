// Stage details toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(event) {
        var btn = event.target.closest('.stage-details-toggle');
        if (!btn) return;
        var icon = btn.querySelector('i.fas');
        var targetId = btn.getAttribute('data-details-target');
        var target = document.querySelector(targetId);
        console.log('Details button clicked:', btn, 'Target:', target);
        if (!target) return;
        if (target.style.display === 'none' || target.style.display === '') {
            target.style.display = 'block';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
        } else {
            target.style.display = 'none';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    });
});

// Progress bar initialization
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.progress-bar').forEach(function(bar) {
        var percent = parseInt(bar.getAttribute('data-progress'));
        bar.style.width = percent + '%';
    });
});

// Initialize species filter
document.addEventListener('DOMContentLoaded', function() {
    // Get user role information from the script tag
    const jsVariables = document.getElementById('js-variables');
    if (jsVariables) {
        try {
            const userInfo = JSON.parse(jsVariables.textContent);
            const userIsAdmin = userInfo.userIsAdmin || false;
            const userIsNpc = userInfo.userIsNpc || false;

            // Initialize the species filter
            initSpeciesFilter('faction', 'species_id', userIsAdmin, userIsNpc);
        } catch (e) {
            console.error('Error parsing user info:', e);
            // Fallback: initialize without admin privileges
            initSpeciesFilter('faction', 'species_id', false, false);
        }
    } else {
        // Fallback: initialize without admin privileges
        initSpeciesFilter('faction', 'species_id', false, false);
    }
});
