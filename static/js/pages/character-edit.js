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