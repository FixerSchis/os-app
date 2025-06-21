document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.delete-btn');
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const deleteForm = document.getElementById('deleteForm');
    const itemCode = document.getElementById('itemCode');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const url = this.dataset.deleteUrl;
            const code = this.dataset.itemCode;
            itemCode.textContent = code;
            deleteForm.action = url;
            deleteModal.show();
        });
    });
    // Explicitly hide modal on cancel/close to fix lingering fade
    document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(btn => {
        btn.addEventListener('click', function() {
            deleteModal.hide();
        });
    });
});
