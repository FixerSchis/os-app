document.addEventListener('DOMContentLoaded', function() {
    // Auto-submit form when show inactive checkbox changes
    const showInactiveCheckbox = document.getElementById('show_inactive');
    if (showInactiveCheckbox) {
        showInactiveCheckbox.addEventListener('change', function() {
            this.closest('form').submit();
        });
    }

    // Disband modal functionality
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
