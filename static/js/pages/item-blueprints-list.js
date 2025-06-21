document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.delete-btn');
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const deleteForm = document.getElementById('deleteForm');
    const blueprintName = document.getElementById('blueprintName');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const url = this.dataset.deleteUrl;
            const name = this.dataset.blueprintName;
            blueprintName.textContent = name;
            deleteForm.action = url;
            deleteModal.show();
        });
    });
});
