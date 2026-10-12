$(document).ready(function() {
    $('#sample_ids').select2({
        width: '100%',
        placeholder: 'Select samples...'
    });

    $('#character_id, #add_character_id').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Search by character name, user name, or ID'
    }).on('select2:open', function() {
        const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDarkMode) {
            $('.select2-container--bootstrap-5').addClass('select2-dark');
            $('.select2-dropdown').addClass('select2-dark');
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const disbandButtons = document.querySelectorAll('.disband-btn');
    const disbandModal = new bootstrap.Modal(document.getElementById('disbandModal'));
    const disbandForm = document.getElementById('disbandForm');
    disbandButtons.forEach(button => {
        button.addEventListener('click', function() {
            disbandForm.action = this.dataset.disbandUrl;
            disbandModal.show();
        });
    });
});
