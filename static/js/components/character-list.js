document.addEventListener('DOMContentLoaded', function() {
    const actionButtons = document.querySelectorAll('.action-btn');
    const actionModal = new bootstrap.Modal(document.getElementById('actionModal'));
    const actionForm = document.getElementById('actionForm');
    const actionLabel = document.getElementById('actionLabel');
    const actionWarning = document.getElementById('actionWarning');

    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const url = this.dataset.actionUrl;
            const label = this.dataset.actionLabel;
            const warning = this.dataset.warning;
            actionLabel.textContent = label;
            actionForm.action = url;
            if (warning) {
                actionWarning.textContent = warning;
                actionWarning.classList.remove('d-none');
            } else {
                actionWarning.textContent = '';
                actionWarning.classList.add('d-none');
            }
            actionModal.show();
        });
    });
}); 