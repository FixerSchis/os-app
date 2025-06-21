$(document).ready(function() {
    $('.select2').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: 'Select a character...'
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const leaveBtn = document.querySelector('.leave-btn');
    const disbandBtn = document.querySelector('.disband-btn');
    const groupActionModal = new bootstrap.Modal(document.getElementById('groupActionModal'));
    const groupActionForm = document.getElementById('groupActionForm');
    const groupActionWarning = document.getElementById('groupActionWarning');
    if (leaveBtn) {
        leaveBtn.addEventListener('click', function() {
            groupActionForm.action = this.dataset.leaveUrl;
            groupActionWarning.textContent = this.dataset.warning;
            groupActionModal.show();
        });
    }
    if (disbandBtn) {
        disbandBtn.addEventListener('click', function() {
            groupActionForm.action = this.dataset.disbandUrl;
            groupActionWarning.textContent = this.dataset.warning;
            groupActionModal.show();
        });
    }
}); 