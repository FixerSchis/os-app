document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.delete-btn');
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const deleteForm = document.getElementById('deleteForm');
    const itemNameSpan = document.getElementById('itemName');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const deleteUrl = this.dataset.deleteUrl;
            const itemName = this.dataset.itemName;
            deleteForm.action = deleteUrl;
            itemNameSpan.textContent = itemName;
            deleteModal.show();
        });
    });
}); 