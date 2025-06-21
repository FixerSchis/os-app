$(document).ready(function() {
    $('#sample_ids').select2({
        width: '100%',
        placeholder: 'Select samples...'
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
