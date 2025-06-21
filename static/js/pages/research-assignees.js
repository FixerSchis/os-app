document.addEventListener('DOMContentLoaded', function() {
    // Initialize Select2
    $('.select2').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Choose a character...',
        allowClear: true
    });

    // Initialize progress bars
    document.querySelectorAll('.progress-bar').forEach(function(bar) {
        var percent = parseInt(bar.getAttribute('data-progress'));
        bar.style.width = percent + '%';
    });
});
